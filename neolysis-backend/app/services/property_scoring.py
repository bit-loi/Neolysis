from app.schemas.property import PropertyIndicator, PropertyScoreResult, TargetConditions
from app.services.protein_features import protein_feature_service


class PropertyScoringService:
    def score(self, sequence: str, conditions: TargetConditions) -> PropertyScoreResult:
        features = protein_feature_service.extract(sequence)
        composition = features.amino_acid_composition
        length = max(features.sequence_length, 1)

        charged_fraction = (composition["D"] + composition["E"] + composition["K"] + composition["R"]) / length
        proline_fraction = composition["P"] / length
        glycine_fraction = composition["G"] / length
        cysteine_fraction = composition["C"] / length
        hydrophobicity = features.gravy or 0.0

        target_temp = conditions.temperature_c if conditions.temperature_c is not None else 37.0
        temp_pressure = min(max((target_temp - 35.0) / 55.0, 0.0), 1.0)
        thermostability_score = 0.42 + charged_fraction * 1.2 + proline_fraction * 0.9 - glycine_fraction * 0.45
        thermostability_score -= temp_pressure * 0.18
        thermostability_score = self._clamp(thermostability_score)

        target_ph = conditions.ph if conditions.ph is not None else 7.0
        pi = features.isoelectric_point
        if pi is not None:
            ph_distance = abs(target_ph - pi)
            ph_score = self._clamp(1.0 - ph_distance / 7.0)
            ph_explanation = "pH fit uses the estimated isoelectric point as a rough process compatibility proxy."
        else:
            acid_basic_balance = abs((composition["D"] + composition["E"]) - (composition["K"] + composition["R"])) / length
            ph_score = self._clamp(0.62 - acid_basic_balance)
            ph_explanation = "pH fit uses charged residue balance because isoelectric point was unavailable."

        solubility_score = self._clamp(0.72 - max(hydrophobicity, 0) * 0.12 + charged_fraction * 0.8 - cysteine_fraction * 0.3)

        solvent_penalty = {
            "none": 0.0,
            "low": 0.04,
            "moderate": 0.10,
            "high": 0.18,
        }.get((conditions.solvent_exposure or "none").lower(), 0.08)
        salinity_penalty = min((conditions.salinity_m_m or 0.0) / 5000.0, 1.0) * 0.08
        condition_fit = self._clamp((thermostability_score + ph_score + solubility_score) / 3 - solvent_penalty - salinity_penalty)

        risk_flags = []
        if target_temp >= 60 and thermostability_score < 0.55:
            risk_flags.append("High-temperature process conditions may exceed the baseline thermostability proxy.")
        if conditions.ph is not None and (conditions.ph <= 4 or conditions.ph >= 10) and ph_score < 0.55:
            risk_flags.append("Extreme pH conditions should be validated experimentally.")
        if hydrophobicity > 0.6:
            risk_flags.append("Hydrophobicity proxy suggests possible solubility risk.")
        if cysteine_fraction > 0.04:
            risk_flags.append("Elevated cysteine content may require checking disulfide state and expression conditions.")
        if (conditions.solvent_exposure or "none").lower() in {"moderate", "high"}:
            risk_flags.append("Solvent exposure scoring is a low-confidence staging proxy.")

        return PropertyScoreResult(
            thermostability=PropertyIndicator(
                score=round(thermostability_score, 3),
                label=self._label(thermostability_score),
                explanation="Estimated from charged residue, proline, glycine, and target-temperature proxies.",
            ),
            ph_fit=PropertyIndicator(
                score=round(ph_score, 3),
                label=self._label(ph_score),
                explanation=ph_explanation,
            ),
            solubility=PropertyIndicator(
                score=round(solubility_score, 3),
                label=self._label(solubility_score),
                explanation="Estimated from hydrophobicity, charged residue fraction, and cysteine content.",
            ),
            condition_fit=PropertyIndicator(
                score=round(condition_fit, 3),
                label=self._label(condition_fit),
                explanation="Combined industrial condition fit with penalties for solvent exposure and high salinity.",
            ),
            industrial_fit_score=round(condition_fit, 3),
            risk_flags=risk_flags,
            confidence=0.38,
            method="baseline_sequence_property_scaffold",
            model_version="industrial-fit-baseline-v0.1",
            limitations=[
                "Scores are computational proxies for prioritization only.",
                "No activity assay, kinetic model, or process-stability measurement is included.",
                "Experimental wet-lab validation is required before industrial use.",
            ],
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _label(score: float) -> str:
        if score >= 0.72:
            return "favorable"
        if score >= 0.45:
            return "moderate"
        return "needs review"


property_scoring_service = PropertyScoringService()
