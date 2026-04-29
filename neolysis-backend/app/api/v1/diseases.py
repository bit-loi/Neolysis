"""
Neolysis — Diseases Router
============================
CRUD endpoints for Neglected Tropical Diseases (NTDs).

Endpoints:
    GET  /api/v1/diseases          — List all diseases
    GET  /api/v1/diseases/{id}     — Disease detail with related proteins
    POST /api/v1/diseases          — Create a new disease record (admin)

Design notes:
    - Disease detail includes nested protein list (eager join, no N+1)
    - UUID primary keys throughout
    - Public read access; writes intended for admin/seed use
"""

import uuid
from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger

from app.db.session import get_db
from app.models.disease import Disease
from app.schemas.disease import DiseaseOut, DiseaseCreate, DiseaseWithProteins
from app.schemas.protein import ProteinOut

router = APIRouter()


@router.get("/", response_model=List[DiseaseOut], summary="List all NTDs")
async def list_diseases(db: AsyncSession = Depends(get_db)) -> List[DiseaseOut]:
    """
    Return all neglected tropical diseases in the platform.

    Currently covers: Dengue, Leptospirosis, Melioidosis, Scrub Typhus (ASEAN focus).
    """
    result = await db.execute(select(Disease).order_by(Disease.name))
    diseases = result.scalars().all()
    logger.debug(f"Fetched {len(diseases)} diseases")
    return [DiseaseOut.model_validate(d) for d in diseases]


@router.get("/{disease_id}", summary="Disease detail with related proteins")
async def get_disease(
    disease_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Return a single disease with all its associated drug target proteins.

    Uses a single optimised JOIN (selectinload) to avoid N+1 queries.
    """
    result = await db.execute(
        select(Disease)
        .options(selectinload(Disease.proteins))
        .where(Disease.id == disease_id)
    )
    disease = result.scalar_one_or_none()
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease {disease_id} not found",
        )

    disease_data = DiseaseOut.model_validate(disease).model_dump()
    disease_data["proteins"] = [
        ProteinOut.model_validate(p).model_dump() for p in disease.proteins
    ]
    return disease_data


@router.post(
    "/",
    response_model=DiseaseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new disease record",
)
async def create_disease(
    disease_in: DiseaseCreate,
    db: AsyncSession = Depends(get_db),
) -> DiseaseOut:
    """
    Create a new NTD disease record.

    Intended for admin/seed use. A future version will require an elevated JWT scope.
    """
    disease = Disease(**disease_in.model_dump())
    db.add(disease)
    await db.commit()
    await db.refresh(disease)
    logger.info(f"Created disease: {disease.name} (id={disease.id})")
    return DiseaseOut.model_validate(disease)
