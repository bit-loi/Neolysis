from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Tuple, Optional
from app.models.target import Target
from app.models.compound import Compound
from app.models.docking import DockingResult
from fastapi import HTTPException
from loguru import logger


class NarrativeService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def prepare_narrative_context(
        self,
        target_id: int,
        top_compound_ids: Optional[List[int]] = None,
        limit: int = 5
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Fetches and prepares the target and compound context required for the LLM prompt.

        If top_compound_ids is None or empty, auto-selects the top `limit` compounds
        by binding affinity (most negative vina_score_kcal_mol first).
        """
        target = await self.db.get(Target, target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        # Build compound query
        if top_compound_ids:
            query = (
                select(Compound, DockingResult.vina_score_kcal_mol)
                .join(DockingResult, DockingResult.compound_id == Compound.id)
                .where(
                    Compound.id.in_(top_compound_ids),
                    DockingResult.target_id == target_id
                )
                .order_by(DockingResult.vina_score_kcal_mol.asc())
            )
        else:
            # Auto-select top N by affinity
            query = (
                select(Compound, DockingResult.vina_score_kcal_mol)
                .join(DockingResult, DockingResult.compound_id == Compound.id)
                .where(DockingResult.target_id == target_id)
                .order_by(DockingResult.vina_score_kcal_mol.asc())
                .limit(limit)
            )

        result = await self.db.execute(query)
        rows = result.all()

        compounds_data = []
        for compound, score in rows:
            compounds_data.append({
                "name": compound.name or f"CID {compound.pubchem_cid}",
                "pubchem_cid": compound.pubchem_cid,
                "vina_score": score,
                "qed": compound.qed_score,
                "lipinski": compound.lipinski_pass,
                "mw": getattr(compound, 'molecular_weight', 'N/A'),
                "logp": getattr(compound, 'logp', 'N/A')
            })

        if not compounds_data:
            logger.warning(f"No docking results found for target {target_id} — narrative will be context-limited")

        target_dict = {
            "name": target.name,
            "organism": target.organism,
            "disease": target.disease,
            "description": target.description,
            "asean_prevalence_note": target.asean_prevalence_note
        }

        return target_dict, compounds_data
