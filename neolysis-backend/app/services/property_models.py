"""
Neolysis — Property Model Adapters
=====================================
Clean adapter boundary between the property-scoring endpoint and whatever is
actually computing each indicator today (a transparent heuristic) versus what
may compute it in the future (a trained model on cached pLM embeddings).

Every adapter reports its own `status`:
    "trained"     — a validated Neolysis model artifact produced this value
    "heuristic"   — a transparent, explainable formula produced this value
    "unavailable" — no validated model exists yet; do not fabricate a score

This milestone intentionally keeps the existing thermostability/pH-fit/
solubility heuristics unchanged (same formulas, same numbers) so no existing
behavior regresses. What changes is that each result now carries an honest,
inspectable `method` and `calibration_status` instead of an implicit shared
label, and a future trained model can be swapped in behind the same
`predict()` contract without touching the property-scoring endpoint.

None of these heuristics consume a protein embedding today — they operate on
deterministic sequence-composition features (via protein_feature_service),
which is scientifically appropriate for what they estimate. Wiring these
adapters to consume a pLM embedding is deferred to a future milestone and
tracked as a limitation, not silently implemented without a validated benefit.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PropertyEstimate:
    score: Optional[float]
    label: str
    explanation: str
    method: str
    calibration_status: str
    status: str  # "trained" | "heuristic" | "unavailable"


class ThermostabilityEstimator:
    """
    No trained Tm predictor is installed. Design references for a future
    trained model (NOT copied, used only as scientific context): ESMStabP,
    TemStaPro, Meltome Atlas. Until a validated model artifact with reported
    MAE/RMSE/R² exists, this remains an explicit sequence-composition heuristic.
    """

    METHOD = "heuristic_v1"

    def predict(self, charged_fraction: float, proline_fraction: float, glycine_fraction: float, temp_pressure: float) -> PropertyEstimate:
        score = 0.42 + charged_fraction * 1.2 + proline_fraction * 0.9 - glycine_fraction * 0.45
        score -= temp_pressure * 0.18
        score = _clamp(score)
        return PropertyEstimate(
            score=round(score, 3),
            label=_label(score),
            explanation="Estimated from charged residue, proline, glycine, and target-temperature proxies.",
            method=self.METHOD,
            calibration_status="uncalibrated",
            status="heuristic",
        )


class PhFitEstimator:
    """
    Transparent heuristic only, as intended for a first pH-fit implementation.
    pI alone does not determine an enzyme's activity optimum; this is a
    prioritization signal, not a claim about catalytic pH optimum.
    """

    METHOD = "heuristic_v1"

    def predict_from_isoelectric_point(self, target_ph: float, isoelectric_point: float) -> PropertyEstimate:
        ph_distance = abs(target_ph - isoelectric_point)
        score = _clamp(1.0 - ph_distance / 7.0)
        return PropertyEstimate(
            score=round(score, 3),
            label=_label(score),
            explanation="pH fit uses the estimated isoelectric point as a rough process compatibility proxy.",
            method=self.METHOD,
            calibration_status="uncalibrated",
            status="heuristic",
        )

    def predict_from_charge_balance(self, acid_basic_balance: float) -> PropertyEstimate:
        score = _clamp(0.62 - acid_basic_balance)
        return PropertyEstimate(
            score=round(score, 3),
            label=_label(score),
            explanation="pH fit uses charged residue balance because isoelectric point was unavailable.",
            method=self.METHOD,
            calibration_status="uncalibrated",
            status="heuristic",
        )


class SolubilityEstimator:
    """
    No validated Neolysis solubility model artifact (e.g. trained on eSOL with
    pLM embeddings + sequence features) is installed yet. This remains an
    explicit sequence-composition heuristic rather than a fabricated model
    score. When a validated artifact exists, swap the body of predict() to
    call it and change status/method/calibration_status accordingly — callers
    do not need to change.
    """

    METHOD = "heuristic_v1"

    def predict(self, hydrophobicity: float, charged_fraction: float, cysteine_fraction: float) -> PropertyEstimate:
        score = _clamp(0.72 - max(hydrophobicity, 0) * 0.12 + charged_fraction * 0.8 - cysteine_fraction * 0.3)
        return PropertyEstimate(
            score=round(score, 3),
            label=_label(score),
            explanation="Estimated from hydrophobicity, charged residue fraction, and cysteine content.",
            method=self.METHOD,
            calibration_status="uncalibrated",
            status="heuristic",
        )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _label(score: float) -> str:
    if score >= 0.72:
        return "favorable"
    if score >= 0.45:
        return "moderate"
    return "needs review"


thermostability_estimator = ThermostabilityEstimator()
ph_fit_estimator = PhFitEstimator()
solubility_estimator = SolubilityEstimator()
