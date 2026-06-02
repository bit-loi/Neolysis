from fastapi import APIRouter, HTTPException, status

from app.schemas.variant import MutationRiskRequest, MutationRiskResult, VariantRankRequest, VariantRankResponse
from app.services.mutation_risk import mutation_risk_service
from app.services.sequence_validation import sequence_validation_service
from app.services.variant_ranking import variant_ranking_service

router = APIRouter()


@router.post("/rank", response_model=VariantRankResponse)
async def rank_variants(payload: VariantRankRequest) -> VariantRankResponse:
    validation = sequence_validation_service.validate(payload.wild_type_sequence)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Variant ranking requires a valid wild-type protein sequence.",
                "validation": validation.model_dump(),
            },
        )
    return variant_ranking_service.rank(
        wild_type_sequence=validation.cleaned_sequence,
        variants=payload.variants,
        target_conditions=payload.target_conditions,
    )


@router.post("/risk", response_model=MutationRiskResult)
async def analyze_mutation_risk(payload: MutationRiskRequest) -> MutationRiskResult:
    validation = sequence_validation_service.validate(payload.wild_type_sequence)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Mutation risk analysis requires a valid wild-type protein sequence.",
                "validation": validation.model_dump(),
            },
        )
    return mutation_risk_service.analyze(
        wild_type=validation.cleaned_sequence,
        variant_sequence=payload.variant_sequence,
        mutations=payload.mutations,
        active_site_positions=payload.active_site_positions,
        conserved_regions=payload.conserved_regions,
    )
