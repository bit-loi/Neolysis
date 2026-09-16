from app.schemas.property import PropertyIndicator, PropertyScoreResult, TargetConditions
from app.services.property_models import ph_fit_estimator, solubility_estimator, thermostability_estimator
from app.services.protein_features import protein_feature_service
from app.services.uncertainty import uncertainty_estimate


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
        thermostability_estimate = thermostability_estimator.predict(
            charged_fraction, proline_fraction, glycine_fraction, temp_pressure
        )

        target_ph = conditions.ph if conditions.ph is not None else 7.0
        pi = features.isoelectric_point
        if pi is not None:
            ph_estimate = ph_fit_estimator.predict_from_isoelectric_point(target_ph, pi)
        else:
            acid_basic_balance = abs((composition["D"] + composition["E"]) - (composition["K"] + composition["R"])) / length
            ph_estimate = ph_fit_estimator.predict_from_charge_balance(acid_basic_balance)

        solubility_estimate = solubility_estimator.predict(hydrophobicity, charged_fraction, cysteine_fraction)

        thermostability_score = thermostability_estimate.score
        ph_score = ph_estimate.score
        solubility_score = solubility_estimate.score

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
            risk_flags.append("Solvent exposure scoring is a low-confidence baseline indicator.")

        confidence = 0.38
        return PropertyScoreResult(
            thermostability=PropertyIndicator(
                score=thermostability_estimate.score,
                label=thermostability_estimate.label,
                explanation=thermostability_estimate.explanation,
                method=thermostability_estimate.method,
                calibration_status=thermostability_estimate.calibration_status,
                status=thermostability_estimate.status,
                model_name=thermostability_estimate.model_name,
                model_version=thermostability_estimate.model_version,
                experimental_validation_required=thermostability_estimate.experimental_validation_required,
            ),
            ph_fit=PropertyIndicator(
                score=ph_estimate.score,
                label=ph_estimate.label,
                explanation=ph_estimate.explanation,
                method=ph_estimate.method,
                calibration_status=ph_estimate.calibration_status,
                status=ph_estimate.status,
            ),
            solubility=PropertyIndicator(
                score=solubility_estimate.score,
                label=solubility_estimate.label,
                explanation=solubility_estimate.explanation,
                method=solubility_estimate.method,
                calibration_status=solubility_estimate.calibration_status,
                status=solubility_estimate.status,
            ),
            condition_fit=PropertyIndicator(
                score=round(condition_fit, 3),
                label=self._label(condition_fit),
                explanation="Combined industrial condition fit with penalties for solvent exposure and high salinity.",
                method="heuristic_v1",
                calibration_status="uncalibrated",
                status="heuristic",
            ),
            industrial_fit_score=round(condition_fit, 3),
            risk_flags=risk_flags,
            confidence=confidence,
            uncertainty=uncertainty_estimate(
                confidence,
                "The score uses transparent sequence-composition proxies.",
                "No assay-specific calibration or experimental measurements are included.",
            ),
            method="baseline_sequence_property_scaffold",
            model_version="industrial-fit-baseline-v0.1",
            limitations=[
                "Scores are computational proxies for prioritization only.",
                "No activity assay, kinetic model, or process-stability measurement is included.",
                "No trained thermostability or solubility model is installed yet; these remain transparent heuristics.",
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
