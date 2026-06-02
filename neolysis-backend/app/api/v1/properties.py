from fastapi import APIRouter, HTTPException, status

from app.schemas.property import PropertyScoreRequest, PropertyScoreResult
from app.services.property_scoring import property_scoring_service
from app.services.sequence_validation import sequence_validation_service

router = APIRouter()


@router.post("/score", response_model=PropertyScoreResult)
async def score_properties(payload: PropertyScoreRequest) -> PropertyScoreResult:
    validation = sequence_validation_service.validate(payload.sequence, name=payload.name)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Property scoring requires a valid canonical protein sequence.",
                "validation": validation.model_dump(),
            },
        )
    return property_scoring_service.score(validation.cleaned_sequence, payload.target_conditions)
