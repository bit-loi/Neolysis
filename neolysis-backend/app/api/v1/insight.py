"""
Neolysis — Insight Router
==========================
AI-powered drug discovery insight generation endpoint.

Pipeline (strict order):
    1. Fetch protein + compound + docking context from Supabase
    2. RAG: Query Qdrant for top 5 relevant PubMed papers [MANDATORY FIRST]
    3. KG: Query KnowledgeGraph for related biomedical triples
    4. LLM: Call Gemma 4 with fully grounded context prompt
    5. Return structured JSON with citations

Constraint enforcement:
    - LLM is NEVER called without RAG context
    - If no papers are found → fallback message returned, no LLM call
    - All citations must be grounded in the returned paper list

Rate limit: 5/minute per IP (Gemma 4 inference is expensive).

Example response:
    {
      "summary": "NS5 RNA polymerase is a key drug target...",
      "drug_assessment": "Quercetin shows moderate binding affinity...",
      "next_steps": "1. Run MD simulation... 2. Validate with IC50 assay...",
      "citations": [{"title": "...", "pmid": "12345678"}],
      "kg_context": [{"subject": "NS5", "relation": "inhibited_by", "object": "Quercetin"}],
      "rag_papers_used": 5,
      "fallback": false
    }
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.session import get_db
from app.services.insight_service import insight_service
from app.core.rate_limit import limiter

router = APIRouter()


class InsightRequest(BaseModel):
    """Input schema for the insight generation pipeline."""
    protein_id: Optional[int] = Field(
        None,
        description="Integer ID of the target protein (from /api/v1/targets)"
    )
    compound_id: Optional[int] = Field(
        None,
        description="Integer ID of the compound (from /api/v1/compounds)"
    )
    protein_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Protein/target name override for RAG (used when protein_id is None)"
    )
    compound_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Compound name override for RAG (used when compound_id is None)"
    )
    query: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional free-text query to guide the RAG search",
        examples=["dengue NS5 polymerase quercetin inhibitor mechanism"]
    )


@router.post(
    "/",
    summary="Generate AI-powered drug discovery insight",
    response_description="Structured insight with citations and knowledge graph context",
)
@limiter.limit("5/minute")
async def generate_insight(
    request: Request,
    body: InsightRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate a research-grade AI insight for a protein-compound pair.

    The pipeline enforces RAG-before-LLM: Gemma 4 is **never** called without
    first retrieving relevant PubMed literature from the Qdrant vector store.

    If no relevant papers are found, a fallback message is returned explaining
    how to populate the RAG corpus (run `scripts/pubmed_crawler.py`).

    Rate limited to 5 requests/minute per IP.
    """
    # Validate that at least one identifier is provided
    if not any([
        body.protein_id,
        body.compound_id,
        body.protein_name,
        body.compound_name,
        body.query,
    ]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Provide at least one of: protein_id, compound_id, "
                "protein_name, compound_name, or query."
            ),
        )

    query = (body.query or "").strip()
    logger.info(
        f"Insight request: protein_id={body.protein_id}, "
        f"compound_id={body.compound_id}, query='{query[:60]}'"
    )

    try:
        result = await insight_service.generate_insight(
            db=db,
            protein_id=body.protein_id,
            compound_id=body.compound_id,
            query=query,
            protein_name=body.protein_name,
            compound_name=body.compound_name,
        )
    except Exception as e:
        logger.error(f"Insight service error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Insight generation failed. Please try again.",
        )

    return result
