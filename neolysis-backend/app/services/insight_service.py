"""
Neolysis — Insight Service (RAG + KG + Gemma 4 LLM Pipeline)
==============================================================
Orchestrates the full research-grade insight pipeline:

    1. Fetch protein + compound + docking data from Supabase
    2. Query Qdrant RAG → top 5 relevant PubMed papers  [MANDATORY FIRST]
    3. Query KnowledgeGraph → related biomedical triples
    4. Build a grounded prompt injecting all context
    5. Call Gemma 4 via Google GenAI → structured JSON output

Enforced constraint: LLM is NEVER called without RAG context.
If no papers are found, a fallback message is returned without LLM call.

Output format:
    {
        "summary":         str,
        "drug_assessment": str,
        "next_steps":      str,
        "citations":       [{"title": str, "pmid": str}],
        "kg_context":      [{"subject", "relation", "object"}],
        "rag_papers_used": int,
        "fallback":        bool
    }

TODO (BioLLM): Replace Gemma 4 call with a fine-tuned BioMedLM or
               MedPaLM2 endpoint for higher factual accuracy.
"""

import json
from typing import Dict, Any, List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.services.rag_service import rag_service
from app.services.kg_service import kg_service
from app.services.llm_service import llm_service
from app.models.target import Target
from app.models.compound import Compound
from app.models.docking import DockingResult


# Minimum papers required before LLM call is permitted
MIN_PAPERS_FOR_LLM = 1

FALLBACK_RESPONSE = {
    "summary": (
        "Insufficient literature context was found to generate a grounded insight. "
        "The RAG pipeline returned no relevant PubMed papers for this query. "
        "Please run the PubMed crawler script (scripts/pubmed_crawler.py) to populate "
        "the Qdrant vector store before requesting AI insights."
    ),
    "drug_assessment": "N/A — no literature context available.",
    "next_steps": (
        "1. Run: python scripts/pubmed_crawler.py\n"
        "2. Retry this endpoint after the crawler completes.\n"
        "3. Manually add papers via POST /api/v1/papers if needed."
    ),
    "citations": [],
    "kg_context": [],
    "rag_papers_used": 0,
    "fallback": True,
}


class InsightService:
    """
    End-to-end RAG + KG + LLM insight pipeline for drug discovery queries.

    All database operations use the injected AsyncSession.
    External service calls (Qdrant, Gemma) are delegated to their respective singletons.
    """

    async def generate_insight(
        self,
        db: AsyncSession,
        protein_id: Optional[int],
        compound_id: Optional[int],
        query: str,
        protein_name: Optional[str] = None,
        compound_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the full insight pipeline for a protein-compound pair.

        Args:
            db:            AsyncSession (injected)
            protein_id:    Integer ID of the target protein (existing model)
            compound_id:   Integer ID of the compound (existing model)
            query:         Free-text research query to ground the RAG search
            protein_name:  Override name for RAG query (used if protein_id is None)
            compound_name: Override name for RAG query (used if compound_id is None)

        Returns:
            Structured insight dict with citations.
        """

        # ── Step 1: Fetch biomedical context from DB ───────────────────────
        context = await self._fetch_biomedical_context(
            db, protein_id, compound_id
        )

        # Build the search query for RAG
        target_name = protein_name or context.get("target_name", "")
        cmpd_name = compound_name or context.get("compound_name", "")
        disease = context.get("disease", "")

        rag_query = (
            query
            or f"{target_name} {cmpd_name} {disease} drug discovery inhibitor"
        ).strip()

        # ── Step 2: RAG FIRST — always before LLM ─────────────────────────
        logger.info(f"[Insight] RAG query: '{rag_query[:80]}'")
        papers = await rag_service.search_relevant_papers(rag_query, top_k=5)

        if len(papers) < MIN_PAPERS_FOR_LLM:
            logger.warning(
                f"[Insight] Insufficient RAG context ({len(papers)} papers). "
                "Returning fallback response."
            )
            return {**FALLBACK_RESPONSE, "query": rag_query}

        # ── Step 3: Knowledge Graph context ───────────────────────────────
        kg_triples = []
        if target_name:
            kg_triples = await kg_service.get_relations(db, target_name, limit=8)
            if not kg_triples and cmpd_name:
                kg_triples = await kg_service.get_relations(db, cmpd_name, limit=8)

        kg_context_str = await kg_service.get_context_for_prompt(
            db, target_name or cmpd_name, max_triples=8
        )

        # ── Step 4: Build grounded prompt ─────────────────────────────────
        prompt = self._build_grounded_prompt(
            context=context,
            papers=papers,
            kg_context=kg_context_str,
            query=rag_query,
        )

        # ── Step 5: Call Gemma 4 with structured output requirement ───────
        logger.info(f"[Insight] Calling Gemma 4 with {len(papers)} RAG papers")
        raw_output = await llm_service.generate_insight(
            {
                "prompt": prompt,
                "target_name": target_name,
                "explanation_from_csv": context.get("docking_summary", ""),
                "lipinski_status": context.get("lipinski_pass", "N/A"),
                "ligand_eff": context.get("ligand_efficiency", "N/A"),
                "burden_description": f"{disease} — ASEAN NTD",
            }
        )

        # ── Step 6: Parse and validate structured output ──────────────────
        structured = self._parse_llm_output(raw_output, papers)

        return {
            **structured,
            "rag_papers_used": len(papers),
            "kg_context": [
                {
                    "subject": t.subject,
                    "relation": t.relation,
                    "object": t.object,
                }
                for t in kg_triples
            ],
            "fallback": False,
            "query": rag_query,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_biomedical_context(
        self,
        db: AsyncSession,
        protein_id: Optional[int],
        compound_id: Optional[int],
    ) -> Dict[str, Any]:
        """Fetch protein, compound, and docking data from Supabase."""
        ctx: Dict[str, Any] = {}

        if protein_id:
            target = await db.get(Target, protein_id)
            if target:
                ctx["target_name"] = target.name
                ctx["disease"] = getattr(target, "disease", "")
                ctx["organism"] = getattr(target, "organism", "")
                ctx["target_description"] = getattr(target, "description", "")
                ctx["asean_note"] = getattr(target, "asean_prevalence_note", "")

        if compound_id:
            compound = await db.get(Compound, compound_id)
            if compound:
                ctx["compound_name"] = getattr(compound, "name", f"CID {compound.pubchem_cid}")
                ctx["smiles"] = getattr(compound, "canonical_smiles", "")
                ctx["mw"] = getattr(compound, "molecular_weight", None)
                ctx["logp"] = getattr(compound, "logp", None)
                ctx["lipinski_pass"] = "Pass" if compound.lipinski_pass else "Fail"
                ctx["qed"] = getattr(compound, "qed_score", None)

        if protein_id and compound_id:
            result = await db.execute(
                select(DockingResult).where(
                    DockingResult.target_id == protein_id,
                    DockingResult.compound_id == compound_id,
                )
            )
            docking = result.scalar_one_or_none()
            if docking:
                score = docking.vina_score_kcal_mol
                ctx["vina_score"] = score
                # Ligand efficiency = vina_score / heavy atom count (rough)
                if ctx.get("smiles") and score:
                    try:
                        from rdkit import Chem
                        mol = Chem.MolFromSmiles(ctx["smiles"])
                        ha = mol.GetNumHeavyAtoms() if mol else 1
                        ctx["ligand_efficiency"] = round(abs(score) / ha, 3)
                    except Exception:
                        ctx["ligand_efficiency"] = None
                ctx["docking_summary"] = (
                    f"AutoDock Vina score: {score} kcal/mol. "
                    f"Ligand efficiency: {ctx.get('ligand_efficiency', 'N/A')} kcal/mol/heavy atom."
                )

        return ctx

    def _build_grounded_prompt(
        self,
        context: Dict[str, Any],
        papers: List[Dict[str, Any]],
        kg_context: str,
        query: str,
    ) -> str:
        """
        Build a RAG-grounded prompt for Gemma 4.

        The prompt structure enforces citation grounding and structured output.
        LLM is explicitly instructed not to invent facts beyond what is provided.
        """
        # Format PubMed papers
        paper_block = "\n".join(
            f"[{i+1}] PMID {p['pmid']} — {p['title']}\n    Abstract: {p['abstract'][:400]}..."
            for i, p in enumerate(papers)
        )

        # Format biomedical context
        protein_block = (
            f"Target: {context.get('target_name', 'Unknown')}\n"
            f"Disease: {context.get('disease', 'Unknown')}\n"
            f"Organism: {context.get('organism', 'Unknown')}\n"
            f"ASEAN context: {context.get('asean_note', 'N/A')}"
        )

        compound_block = (
            f"Compound: {context.get('compound_name', 'Unknown')}\n"
            f"MW: {context.get('mw', 'N/A')} Da | LogP: {context.get('logp', 'N/A')}\n"
            f"Lipinski: {context.get('lipinski_pass', 'N/A')} | QED: {context.get('qed', 'N/A')}\n"
            f"Docking: {context.get('docking_summary', 'No docking data available')}"
        )

        return f"""You are a computational drug discovery assistant specializing in ASEAN Neglected Tropical Diseases.

RESEARCH QUERY: {query}

=== BIOMEDICAL CONTEXT ===
{protein_block}

{compound_block}

=== KNOWLEDGE GRAPH ===
{kg_context}

=== PUBMED LITERATURE (use ONLY these sources for citations) ===
{paper_block}

=== INSTRUCTIONS ===
Using ONLY the information provided above, generate a structured JSON response.
Do NOT invent any facts. Do NOT add citations not listed above.
If information is insufficient, say so explicitly.

Respond with valid JSON in this exact format:
{{
  "summary": "<2-3 paragraph scientific summary for a graduate researcher>",
  "drug_assessment": "<assessment of this compound's potential as a drug candidate for this target>",
  "next_steps": "<3-5 specific, actionable next steps for wet-lab or computational follow-up>",
  "citations": [
    {{"title": "<exact title from literature above>", "pmid": "<PMID>"}}
  ]
}}"""

    def _parse_llm_output(
        self,
        raw: str,
        papers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Parse the LLM's raw text output into a structured dict.

        Falls back gracefully if JSON parsing fails.
        """
        # Try to extract JSON block
        try:
            # Strip markdown code fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                # Remove first and last fence lines
                clean = "\n".join(
                    l for l in lines
                    if not l.strip().startswith("```")
                )
            parsed = json.loads(clean)
            # Validate required keys
            for key in ("summary", "drug_assessment", "next_steps", "citations"):
                if key not in parsed:
                    parsed[key] = "N/A"
            return parsed
        except json.JSONDecodeError:
            logger.warning("[Insight] LLM output was not valid JSON — wrapping as summary")
            # Fallback: wrap raw text in the expected structure
            return {
                "summary": raw[:2000] if raw else "No response generated.",
                "drug_assessment": "See summary above.",
                "next_steps": "Review the summary and consult the cited literature.",
                "citations": [
                    {"title": p["title"], "pmid": p["pmid"]}
                    for p in papers[:3]
                ],
            }


insight_service = InsightService()
