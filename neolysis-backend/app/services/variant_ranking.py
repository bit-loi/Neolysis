from typing import Optional

from app.schemas.property import TargetConditions
from app.schemas.variant import RankedVariant, VariantCandidate, VariantRankResponse, VariantSignals
from app.services.mutation_risk import mutation_risk_service
from app.services.property_scoring import property_scoring_service
from app.services.uncertainty import uncertainty_estimate


class VariantRankingService:
    def rank(
        self,
        wild_type_sequence: str,
        variants: list[VariantCandidate],
        target_conditions: TargetConditions,
        active_site_positions: Optional[list[int]] = None,
    ) -> VariantRankResponse:
        ranked: list[RankedVariant] = []
        wild_type = wild_type_sequence.upper()
        wild_type_score = property_scoring_service.score(wild_type, target_conditions)

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
                active_site_positions=active_site_positions,
            )
            adjusted_fit = max(0.0, score.industrial_fit_score - risk.risk_score * 0.18)
            mutation_summary = mutation_risk_service.summarize_mutations(wild_type, variant_sequence)
            risk_flags = (
                score.risk_flags
                + risk.potential_stability_risk
                + risk.potential_function_risk
                + mutation_warnings
            )

            confidence = round(min(score.confidence, risk.confidence), 3)
            priority = self._priority(adjusted_fit, risk.risk_score)

            signals = VariantSignals(
                thermostability_delta=self._delta(score.thermostability.score, wild_type_score.thermostability.score),
                solubility_delta=self._delta(score.solubility.score, wild_type_score.solubility.score),
                ph_fit_delta=self._delta(score.ph_fit.score, wild_type_score.ph_fit.score),
                # No structure context is supplied to this call, so structure-dependent
                # signals stay explicitly unavailable rather than guessed.
                proteinmpnn_compatibility=None,
                proteinmpnn_status="not_available",
                active_site_distance_angstrom=None,
                structure_prediction_confidence=None,
            )
            reasoning = self._reasoning(signals, risk.active_site_warning, adjusted_fit, wild_type_score.industrial_fit_score)

            ranked.append(
                RankedVariant(
                    rank=0,
                    variant_id=candidate.variant_id,
                    name=candidate.name,
                    mutation_summary=mutation_summary,
                    predicted_fit_score=round(adjusted_fit, 3),
                    risk_score=risk.risk_score,
                    confidence=confidence,
                    uncertainty=uncertainty_estimate(
                        confidence,
                        "Variant confidence is capped by the least-confident scoring component.",
                        "Ranking uncertainty is uncalibrated and does not represent probability of assay success.",
                    ),
                    wet_lab_priority=priority,
                    explanation=(
                        "Ranked by baseline industrial fit score adjusted for sequence-level mutation risk. "
                        "This is a prioritization scaffold and requires experimental validation."
                    ),
                    risk_flags=risk_flags,
                    signals=signals,
                    reasoning=reasoning,
                    calibration_status="uncalibrated",
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
                "Structure-dependent signals (active-site distance, ProteinMPNN compatibility, structure "
                "prediction confidence) are not populated by this endpoint; they require structure context "
                "that this request did not supply.",
            ],
        )

    @staticmethod
    def _delta(variant_score: Optional[float], wild_type_score: Optional[float]) -> Optional[float]:
        if variant_score is None or wild_type_score is None:
            return None
        return round(variant_score - wild_type_score, 3)

    @staticmethod
    def _reasoning(
        signals: VariantSignals,
        active_site_warning: Optional[str],
        adjusted_fit: float,
        wild_type_fit: float,
    ) -> list[str]:
        notes: list[str] = []
        if signals.thermostability_delta is not None:
            if signals.thermostability_delta > 0:
                notes.append("Predicted thermostability improves relative to wild type.")
            elif signals.thermostability_delta < 0:
                notes.append("Predicted thermostability is lower than wild type.")
        if signals.solubility_delta is not None and signals.solubility_delta < -0.05:
            notes.append("Small predicted solubility penalty relative to wild type.")
        if active_site_warning:
            notes.append(active_site_warning)
        else:
            notes.append("No supplied active-site positions were affected by this variant's mutations.")
        if adjusted_fit > wild_type_fit:
            notes.append("Overall predicted industrial fit improves relative to wild type.")
        return notes

    @staticmethod
    def _priority(fit_score: float, risk_score: float) -> str:
        if fit_score >= 0.68 and risk_score <= 0.35:
            return "high"
        if fit_score >= 0.45 and risk_score <= 0.65:
            return "medium"
        return "low"


variant_ranking_service = VariantRankingService()
