from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.docking import DockingResult
from typing import Optional, Dict, Any

class DockingStore:
    async def get_score(self, db: AsyncSession, target_id: int, compound_id: int) -> Dict[str, Any]:
        """
        Retrieves pre-computed Vina score from the database.
        """
        query = select(DockingResult).where(
            DockingResult.target_id == target_id,
            DockingResult.compound_id == compound_id
        )
        result = await db.execute(query)
        docking = result.scalar_one_or_none()
        
        if docking:
            return {
                "score": docking.vina_score_kcal_mol,
                "pose": docking.binding_pose_json,
                "status": "precomputed"
            }
        
        return {
            "score": None,
            "pose": None,
            "status": "not_precomputed"
        }

docking_store = DockingStore()
