from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.target import Target
from app.models.compound import Compound
from app.models.docking import DockingResult
from app.models.paper import Paper
from app.schemas.target import TargetOut
from app.schemas.docking import DockingWithCompound
from app.schemas.paper import PaperOut
from app.services.alphafold import alphafold_service

router = APIRouter()


@router.get("/", response_model=List[TargetOut])
async def list_targets(db: AsyncSession = Depends(get_db)):
    """Return all protein targets with their pdb_url for the frontend viewer."""
    result = await db.execute(select(Target))
    return result.scalars().all()


@router.get("/{target_id}", response_model=TargetOut)
async def get_target(target_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single protein target with metadata and pdb_url."""
    target = await db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.get("/{target_id}/structure")
async def get_target_structure(target_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns a URL to the PDB file for 3D viewing.
    Priority: R2-stored URL (pdb_url) → AlphaFold → RCSB.
    The backend never proxies the PDB file — only the URL is returned.
    """
    target = await db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Use stored pdb_url first (R2 or pre-resolved AlphaFold/RCSB)
    if target.pdb_url:
        return {"pdb_url": target.pdb_url, "source": target.source or "stored"}

    # Fallback: dynamically resolve from AlphaFold or RCSB
    url = await alphafold_service.get_structure_url(
        uniprot_id=target.uniprot_id,
        pdb_id=target.pdb_id
    )

    if not url:
        raise HTTPException(status_code=404, detail="No structure found for this target")

    return {"pdb_url": url, "source": "dynamic"}


@router.get("/{target_id}/compounds", response_model=List[DockingWithCompound])
async def get_compounds_for_target(target_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return all drug candidate compounds for a target, ranked by binding affinity.
    Joins Compound + DockingResult to return a flat, aggregated response.
    Per spec: GET /proteins/:id/compounds
    """
    target = await db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

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
        .order_by(DockingResult.vina_score_kcal_mol.asc())  # most negative = best
    )
    result = await db.execute(query)
    rows = result.mappings().all()

    return [DockingWithCompound(**dict(row)) for row in rows]


@router.get("/{target_id}/papers", response_model=List[PaperOut])
async def get_papers_for_target(target_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return research papers linked to this target (RAG context layer).
    Per spec: papers table with protein_id FK.
    """
    target = await db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    result = await db.execute(
        select(Paper).where(Paper.target_id == target_id)
    )
    return result.scalars().all()
