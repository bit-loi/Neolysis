from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.models.compound import Compound
from app.models.docking import DockingResult
from app.schemas.compound import CompoundOut

router = APIRouter()


@router.get("/", response_model=List[CompoundOut])
async def list_compounds(
    target_id: Optional[int] = None,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List compounds, optionally filtered by target docking results.
    For a ranked compound list use GET /targets/{id}/compounds instead.
    """
    if target_id:
        query = (
            select(Compound)
            .join(DockingResult, DockingResult.compound_id == Compound.id)
            .where(DockingResult.target_id == target_id)
            .limit(limit)
        )
    else:
        query = select(Compound).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/cid/{pubchem_cid}", response_model=CompoundOut)
async def get_compound_by_cid(pubchem_cid: int, db: AsyncSession = Depends(get_db)):
    """
    Get compound by PubChem CID.
    Per spec: GET /compounds/:cid
    """
    result = await db.execute(
        select(Compound).where(Compound.pubchem_cid == pubchem_cid)
    )
    compound = result.scalar_one_or_none()
    if not compound:
        raise HTTPException(status_code=404, detail=f"Compound with CID {pubchem_cid} not found")
    return compound


@router.get("/{compound_id}", response_model=CompoundOut)
async def get_compound(compound_id: int, db: AsyncSession = Depends(get_db)):
    """Get compound by internal DB id."""
    compound = await db.get(Compound, compound_id)
    if not compound:
        raise HTTPException(status_code=404, detail="Compound not found")
    return compound
