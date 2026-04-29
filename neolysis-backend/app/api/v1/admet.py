"""
Neolysis — ADMET Router
=========================
ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) prediction endpoint.

Endpoints:
    POST /api/v1/admet — Predict ADMET properties from a SMILES string

Pipeline:
    1. Validate SMILES via RDKit
    2. Run TDC pretrained models (Caco-2, hERG, DILI, BBB, Lipophilicity)
    3. Normalise each value to risk_level (low/medium/high)
    4. Return structured scorecard

Rate limit: 20/minute per IP (ADMET models are compute-intensive).

Example response:
    {
      "smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "caco2": {"value": -5.2, "risk_level": "low", "unit": "log Papp (cm/s)", ...},
      "herg": {"value": 8.3, "risk_level": "low", "unit": "IC50 (µM)", ...},
      "dili": {"value": 0.18, "risk_level": "low", ...},
      "bbb": {"value": 0.45, "risk_level": "medium", ...},
      "lipophilicity": {"value": 1.24, "risk_level": "low", ...},
      "drug_likeness": {"mw": 180.16, "logp": 1.24, "lipinski_pass": true, ...}
    }
"""

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from loguru import logger

from app.services.admet_service import admet_service
from app.core.rate_limit import limiter

router = APIRouter()


class ADMETRequest(BaseModel):
    """Input schema for ADMET prediction."""
    smiles: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Valid SMILES string for the compound to evaluate",
        examples=["CC(=O)Oc1ccccc1C(=O)O"],  # Aspirin
    )


@router.post(
    "/",
    summary="Predict ADMET properties",
    response_description="ADMET scorecard with risk levels per property",
)
@limiter.limit("20/minute")
async def predict_admet(
    request: Request,
    body: ADMETRequest,
) -> dict:
    """
    Predict ADMET safety and pharmacokinetic properties for a given compound SMILES.

    Returns a structured scorecard with:
    - **caco2**: Intestinal permeability (Caco-2 log Papp)
    - **herg**: Cardiac ion channel toxicity (hERG IC50)
    - **dili**: Drug-induced liver injury probability
    - **bbb**: Blood-brain barrier penetration probability
    - **lipophilicity**: Lipophilicity (logD)
    - **drug_likeness**: RDKit Lipinski Rule-of-5 properties

    Each property includes a `risk_level` of `low`, `medium`, or `high`.

    Rate limited to 20 requests/minute per IP.
    """
    smiles = body.smiles.strip()
    logger.info(f"ADMET request for SMILES (len={len(smiles)})")

    try:
        result = await admet_service.predict(smiles)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid SMILES string: {str(e)}",
        )
    except Exception as e:
        logger.error(f"ADMET prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMET prediction service error. Please try again.",
        )

    return {"smiles": smiles, **result}
