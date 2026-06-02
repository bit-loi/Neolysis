from fastapi import APIRouter, HTTPException, status

from app.schemas.sequence import SequenceFeatureResponse, SequenceInput, SequenceValidationResult
from app.services.protein_features import protein_feature_service
from app.services.sequence_validation import sequence_validation_service

router = APIRouter()


@router.post("/validate", response_model=SequenceValidationResult)
async def validate_sequence(payload: SequenceInput) -> SequenceValidationResult:
    return sequence_validation_service.validate(payload.sequence, name=payload.name)


@router.post("/features", response_model=SequenceFeatureResponse)
async def extract_sequence_features(payload: SequenceInput) -> SequenceFeatureResponse:
    validation = sequence_validation_service.validate(payload.sequence, name=payload.name)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Protein sequence contains invalid residues or could not be parsed.",
                "validation": validation.model_dump(),
            },
        )
    features = protein_feature_service.extract(validation.cleaned_sequence)
    return SequenceFeatureResponse(validation=validation, features=features)
