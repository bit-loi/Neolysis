from fastapi import APIRouter, HTTPException, status

from app.schemas.enzyme import EnzymeFunctionRequest, EnzymeFunctionResponse
from app.services.embeddings import protein_embedding_client
from app.services.enzyme_function import enzyme_function_service
from app.services.sequence_validation import sequence_validation_service

router = APIRouter()


@router.post("/predict-function", response_model=EnzymeFunctionResponse)
async def predict_enzyme_function(payload: EnzymeFunctionRequest) -> EnzymeFunctionResponse:
    validation = sequence_validation_service.validate(payload.sequence, name=payload.name)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Function prediction requires a valid canonical protein sequence.",
                "validation": validation.model_dump(),
            },
        )
    embedding = await protein_embedding_client.embed(validation.cleaned_sequence)
    prediction = enzyme_function_service.predict(
        validation.cleaned_sequence,
        embedding=embedding,
        enzyme_class_hint=payload.enzyme_class_hint,
    )
    return EnzymeFunctionResponse(embedding=embedding, prediction=prediction)
