from app.schemas.property import TargetConditions
from app.schemas.variant import RankedVariant, VariantCandidate, VariantRankResponse
from app.services.mutation_risk import mutation_risk_service
from app.services.property_scoring import property_scoring_service


class VariantRankingService:
    def rank(
        self,
        wild_type_sequence: str,
        variants: list[VariantCandidate],
        target_conditions: TargetConditions,
    ) -> VariantRankResponse:
        ranked: list[RankedVariant] = []
        wild_type = wild_type_sequence.upper()

        for candidate in variants:
            if candidate.sequence:
                variant_sequence = candidate.sequence.upper()
                mutation_warnings: list[str] = []
            else:
                variant_sequence, mutation_warnings = mutation_risk_service.apply_mutations(
                    wild_type,
                    candidate.mutations,
                )

            score = property_scoring_service.score(variant_sequence, target_conditions)
            risk = mutation_risk_service.analyze(
                wild_type,
                variant_sequence=variant_sequence,
                mutations=candidate.mutations,
            )
            adjusted_fit = max(0.0, score.industrial_fit_score - risk.risk_score * 0.18)
            mutation_summary = mutation_risk_service.summarize_mutations(wild_type, variant_sequence)
            risk_flags = (
                score.risk_flags
                + risk.potential_stability_risk
                + risk.potential_function_risk
                + mutation_warnings
            )

            ranked.append(
                RankedVariant(
                    rank=0,
                    variant_id=candidate.variant_id,
                    name=candidate.name,
                    mutation_summary=mutation_summary,
                    predicted_fit_score=round(adjusted_fit, 3),
                    risk_score=risk.risk_score,
                    confidence=round(min(score.confidence, risk.confidence), 3),
                    wet_lab_priority=self._priority(adjusted_fit, risk.risk_score),
                    explanation=(
                        "Ranked by baseline industrial fit score adjusted for sequence-level mutation risk. "
                        "This is a prioritization scaffold and requires experimental validation."
                    ),
                    risk_flags=risk_flags,
                )
            )

        ranked.sort(key=lambda item: (item.predicted_fit_score, -item.risk_score), reverse=True)
        for index, item in enumerate(ranked, start=1):
            item.rank = index

        return VariantRankResponse(
            ranked_variants=ranked,
            limitations=[
                "Variant ranking uses baseline sequence proxies only.",
                "Predicted benefits are not experimental activity or stability measurements.",
            ],
        )

    @staticmethod
    def _priority(fit_score: float, risk_score: float) -> str:
        if fit_score >= 0.68 and risk_score <= 0.35:
            return "high"
        if fit_score >= 0.45 and risk_score <= 0.65:
            return "medium"
        return "low"


variant_ranking_service = VariantRankingService()
