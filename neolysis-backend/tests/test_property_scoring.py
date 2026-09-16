from app.schemas.property import TargetConditions
from app.services.property_models import ph_fit_estimator, solubility_estimator, thermostability_estimator
from app.services.property_scoring import property_scoring_service


SAMPLE_SEQUENCE = (
    "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH"
    "VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL"
)


def test_score_returns_backward_compatible_top_level_fields():
    """
    industrial_fit_score, method, model_version, and limitations must keep working
    exactly as before this milestone's additive changes.
    """
    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))

    assert 0 <= result.industrial_fit_score <= 1
    assert result.method == "baseline_sequence_property_scaffold"
    assert result.uncertainty.calibration_status == "uncalibrated"


def test_each_indicator_reports_heuristic_status_and_method():
    """
    No trained thermostability/solubility model is installed in this milestone.
    Every indicator must say so explicitly rather than looking like a trained
    model result.
    """
    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))

    for indicator in (result.thermostability, result.ph_fit, result.solubility, result.condition_fit):
        assert indicator.status == "heuristic"
        assert indicator.calibration_status == "uncalibrated"
        assert indicator.method == "heuristic_v1"


def test_thermostability_estimator_adapter_contract():
    estimate = thermostability_estimator.predict(
        charged_fraction=0.2, proline_fraction=0.05, glycine_fraction=0.05, temp_pressure=0.5
    )

    assert estimate.status == "heuristic"
    assert estimate.calibration_status == "uncalibrated"
    assert 0 <= estimate.score <= 1


def test_solubility_estimator_adapter_contract():
    estimate = solubility_estimator.predict(hydrophobicity=-0.2, charged_fraction=0.25, cysteine_fraction=0.01)

    assert estimate.status == "heuristic"
    assert 0 <= estimate.score <= 1


def test_ph_fit_estimator_uses_isoelectric_point_when_available():
    estimate = ph_fit_estimator.predict_from_isoelectric_point(target_ph=7.0, isoelectric_point=7.0)

    assert estimate.score == 1.0
    assert "isoelectric point" in estimate.explanation


def test_ph_fit_estimator_falls_back_to_charge_balance_when_pi_unavailable():
    estimate = ph_fit_estimator.predict_from_charge_balance(acid_basic_balance=0.0)

    assert estimate.status == "heuristic"
    assert "charged residue balance" in estimate.explanation


def test_property_scoring_is_deterministic_for_identical_input():
    conditions = TargetConditions(temperature_c=60, ph=10, use_case="detergent")

    first = property_scoring_service.score(SAMPLE_SEQUENCE, conditions)
    second = property_scoring_service.score(SAMPLE_SEQUENCE, conditions)

    assert first.industrial_fit_score == second.industrial_fit_score
    assert first.thermostability.score == second.thermostability.score
