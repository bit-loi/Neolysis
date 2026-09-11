from app.schemas.scientific import UncertaintyEstimate


def uncertainty_estimate(confidence: float, *basis: str) -> UncertaintyEstimate:
    """Expose honest heuristic uncertainty without claiming statistical calibration."""

    confidence = round(max(0.0, min(1.0, confidence)), 3)
    uncertainty = round(1.0 - confidence, 3)
    if uncertainty >= 0.6:
        level = "high"
    elif uncertainty >= 0.3:
        level = "medium"
    else:
        level = "low"
    return UncertaintyEstimate(
        confidence=confidence,
        uncertainty=uncertainty,
        level=level,
        basis=list(basis),
        calibration_status="uncalibrated",
    )
