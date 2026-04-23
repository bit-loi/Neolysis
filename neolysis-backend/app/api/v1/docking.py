from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.compound import Compound
from app.models.docking import DockingResult
from app.schemas.docking import DockingOut, DockingWithCompound
from app.services.docking_store import docking_store

router = APIRouter()


@router.get("/{target_id}", response_model=List[DockingWithCompound])
async def list_docking_for_target(target_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return all precomputed docking results for a target, with inline compound metadata.
    Sorted by binding affinity (most negative = best).
    Per spec: GET /docking/:protein_id
    """
    query = (
        select(
            Compound.id.label("compound_id"),
            Compound.pubchem_cid,
            Compound.name,
            Compound.canonical_smiles.label("smiles"),
            Compound.molecular_weight,
            Compound.logp,
            Compound.hbd,
            Compound.hba,
            Compound.qed_score,
            Compound.lipinski_pass,
            DockingResult.vina_score_kcal_mol,
            DockingResult.source,
        )
        .join(DockingResult, DockingResult.compound_id == Compound.id)
        .where(DockingResult.target_id == target_id)
        .order_by(DockingResult.vina_score_kcal_mol.asc())
    )
    result = await db.execute(query)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No docking results found for target {target_id}")

    return [DockingWithCompound(**dict(row)) for row in rows]


@router.get("/{target_id}/{compound_id}")
async def get_docking_score(
    target_id: int,
    compound_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve pre-computed Vina score for a specific target-compound pair.
    """
    result = await docking_store.get_score(db, target_id, compound_id)
    if not result["score"]:
        return {
            "target_id": target_id,
            "compound_id": compound_id,
            "vina_score": None,
            "status": "not_precomputed"
        }

    return {
        "target_id": target_id,
        "compound_id": compound_id,
        "vina_score": result["score"],
        "pose": result["pose"],
        "status": "precomputed"
    }
