"""
Neolysis — Proteins Router
============================
CRUD endpoints for drug target proteins.

Endpoints:
    GET  /api/v1/proteins           — List all proteins (filterable by disease_id)
    GET  /api/v1/proteins/{id}      — Protein detail
    POST /api/v1/proteins           — Create a new protein record (admin)

Design notes:
    - Filterable by `disease_id` query param (UUID)
    - Pagination: limit/offset
    - Public read access; write requires future auth middleware
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.db.session import get_db
from app.models.protein import Protein
from app.schemas.protein import ProteinOut, ProteinCreate

router = APIRouter()


@router.get("/", response_model=List[ProteinOut], summary="List proteins, filterable by disease")
async def list_proteins(
    disease_id: Optional[uuid.UUID] = Query(None, description="Filter by disease UUID"),
    limit: int = Query(50, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> List[ProteinOut]:
    """
    List drug target proteins.

    Filter by `disease_id` to get all proteins associated with a specific NTD.
    Example: GET /api/v1/proteins?disease_id=<uuid>
    """
    query = select(Protein)
    if disease_id:
        query = query.where(Protein.disease_id == disease_id)
    query = query.order_by(Protein.name).offset(offset).limit(limit)

    result = await db.execute(query)
    proteins = result.scalars().all()
    logger.debug(f"Fetched {len(proteins)} proteins (disease_id={disease_id})")
    return [ProteinOut.model_validate(p) for p in proteins]


@router.get("/{protein_id}", response_model=ProteinOut, summary="Get protein detail")
async def get_protein(
    protein_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProteinOut:
    """
    Return a single protein by UUID.

    Includes structure_url (direct PDB link) and amino acid sequence for viewer integration.
    """
    protein = await db.get(Protein, protein_id)
    if not protein:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protein {protein_id} not found",
        )
    return ProteinOut.model_validate(protein)


@router.post(
    "/",
    response_model=ProteinOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new protein target",
)
async def create_protein(
    protein_in: ProteinCreate,
    db: AsyncSession = Depends(get_db),
) -> ProteinOut:
    """
    Add a new drug target protein.

    Intended for admin/seed use. Links to an existing Disease via disease_id.
    """
    protein = Protein(**protein_in.model_dump())
    db.add(protein)
    await db.commit()
    await db.refresh(protein)
    logger.info(f"Created protein: {protein.name} (id={protein.id})")
    return ProteinOut.model_validate(protein)
