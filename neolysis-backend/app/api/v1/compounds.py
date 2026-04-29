"""
Neolysis — Compounds Router (Enhanced)
========================================
Endpoints for drug compound management and molecular property validation.

Endpoints:
    GET  /api/v1/compounds              — List compounds (with pagination)
    GET  /api/v1/compounds/cid/{cid}    — Get by PubChem CID
    GET  /api/v1/compounds/{id}         — Get by internal ID
    POST /api/v1/compounds/validate     — Validate SMILES + calculate RDKit properties

Design notes:
    - /validate uses RDKit (WASM-safe thread pool) to compute:
        MW, LogP, HBD, HBA, TPSA, QED, Lipinski pass/fail
    - Rate limited: 30/minute for validate (CPU-intensive)
    - All inputs sanitized via Pydantic and RDKit validation
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.compound import Compound
from app.models.docking import DockingResult
from app.schemas.compound import CompoundOut
from app.services.rdkit_service import rdkit_service
from app.core.rate_limit import limiter

router = APIRouter()


class SMILESValidationRequest(BaseModel):
    """Input schema for SMILES property calculation."""
    smiles: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Valid SMILES string to calculate properties for",
        examples=["CC(=O)Oc1ccccc1C(=O)O"],  # Aspirin
    )


@router.get("/", response_model=List[CompoundOut], summary="List all compounds")
async def list_compounds(
    target_id: Optional[int] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List compounds with pagination, optionally filtered by target docking results.

    For ranked compound lists by binding affinity, use GET /api/v1/targets/{id}/compounds instead.
    """
    if target_id:
        query = (
            select(Compound)
            .join(DockingResult, DockingResult.compound_id == Compound.id)
            .where(DockingResult.target_id == target_id)
            .offset(offset)
            .limit(limit)
        )
    else:
        query = select(Compound).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/validate",
    summary="Validate SMILES and calculate molecular properties",
)
@limiter.limit("30/minute")
async def validate_smiles(
    request: Request,
    body: SMILESValidationRequest,
) -> dict:
    """
    Validate a SMILES string and compute RDKit molecular properties.

    Returns:
    - **mw**: Molecular weight (Da)
    - **logp**: Wildman-Crippen LogP
    - **hbd**: H-bond donor count
    - **hba**: H-bond acceptor count
    - **tpsa**: Topological polar surface area (Å²)
    - **qed**: Quantitative estimate of drug-likeness (0–1)
    - **lipinski_pass**: Boolean (True if ≤1 Lipinski violation)
    - **violations**: List of violated Lipinski rules
    - **valid**: Boolean indicating SMILES validity

    Rate limited to 30/minute per IP.
    """
    smiles = body.smiles.strip()
    props = await rdkit_service.get_drug_likeness(smiles)

    if "Calculation Error" in props.get("violations", []):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid SMILES string: '{smiles[:100]}'. Could not parse with RDKit.",
        )

    return {
        "smiles": smiles,
        "valid": True,
        **props,
    }


@router.get("/cid/{pubchem_cid}", response_model=CompoundOut, summary="Get compound by PubChem CID")
async def get_compound_by_cid(pubchem_cid: int, db: AsyncSession = Depends(get_db)):
    """
    Get compound by PubChem CID.
    """
    result = await db.execute(
        select(Compound).where(Compound.pubchem_cid == pubchem_cid)
    )
    compound = result.scalar_one_or_none()
    if not compound:
        raise HTTPException(status_code=404, detail=f"Compound with CID {pubchem_cid} not found")
    return compound


@router.get("/{compound_id}", response_model=CompoundOut, summary="Get compound by internal ID")
async def get_compound(compound_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get compound by internal database ID.
    """
    compound = await db.get(Compound, compound_id)
    if not compound:
        raise HTTPException(status_code=404, detail="Compound not found")
    return compound
