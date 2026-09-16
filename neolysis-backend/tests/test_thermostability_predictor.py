"""
Milestone 3A — Property Predictor Architecture / Heuristic Baseline.

This is NOT Milestone 3B (trained Tm model). These tests verify that:
  - the thermostability heuristic is explicitly labeled as such
  - its output is deterministic and bounded
  - it never calls the ESM2 Hugging Face Space, the self-hosted PLM
    microservice, or any other network endpoint

No dataset, model artifact, or training occurs here.
"""
import httpx
import pytest

from app.schemas.property import TargetConditions
from app.services.property_models import (
    HeuristicThermostabilityPredictor,
    PropertyEstimate,
    thermostability_estimator,
)
from app.services.property_scoring import property_scoring_service

SAMPLE_SEQUENCE = (
    "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH"
    "VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL"
)


def test_thermostability_indicator_method_is_heuristic_v1():
    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))
    assert result.thermostability.method == "heuristic_v1"


def test_thermostability_indicator_status_is_heuristic():
    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))
    assert result.thermostability.status == "heuristic"


def test_thermostability_indicator_calibration_status_is_uncalibrated():
    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))
    assert result.thermostability.calibration_status == "uncalibrated"


def test_thermostability_indicator_has_no_model_provenance():
    """
    No trained model artifact exists. model_name/model_version must be null,
    and experimental_validation_required must be true, for every heuristic result.
    """
    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))

    assert result.thermostability.model_name is None
    assert result.thermostability.model_version is None
    assert result.thermostability.experimental_validation_required is True


def test_thermostability_output_is_deterministic():
    conditions = TargetConditions(temperature_c=60, ph=10)

    first = property_scoring_service.score(SAMPLE_SEQUENCE, conditions)
    second = property_scoring_service.score(SAMPLE_SEQUENCE, conditions)

    assert first.thermostability.score == second.thermostability.score


def test_thermostability_score_is_bounded_zero_to_one():
    # Sweep a range of target temperatures to check the clamp holds at both extremes.
    for temp_c in (-20, 0, 37, 60, 90, 130):
        result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=temp_c))
        assert 0.0 <= result.thermostability.score <= 1.0


def test_predictor_satisfies_protocol_contract_directly():
    predictor = HeuristicThermostabilityPredictor()
    estimate = predictor.predict(
        charged_fraction=0.2, proline_fraction=0.05, glycine_fraction=0.05, temp_pressure=0.5
    )

    assert isinstance(estimate, PropertyEstimate)
    assert estimate.method == "heuristic_v1"
    assert estimate.status == "heuristic"
    assert estimate.calibration_status == "uncalibrated"
    assert estimate.model_name is None
    assert estimate.model_version is None


def test_thermostability_estimator_singleton_is_the_heuristic_predictor():
    """Backward-compatible singleton name must still resolve to the heuristic implementation."""
    assert isinstance(thermostability_estimator, HeuristicThermostabilityPredictor)


def test_heuristic_predictor_never_calls_httpx(monkeypatch):
    """
    The heuristic formula does not consume an embedding and must never make
    any outbound HTTP request (ESM2 Space, PLM microservice, or otherwise).
    """
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Thermostability heuristic must not make any HTTP request")

    monkeypatch.setattr(httpx.AsyncClient, "post", fail_if_called)
    monkeypatch.setattr(httpx.AsyncClient, "get", fail_if_called)

    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))
    assert result.thermostability.score is not None


def test_heuristic_predictor_never_imports_gradio_client(monkeypatch):
    """
    Guard against a future regression where thermostability scoring is
    accidentally wired to call the Hugging Face Space. If gradio_client's
    Client is ever constructed during property_scoring_service.score(), this
    fails loudly rather than silently adding network latency.
    """
    import sys

    class _FailingClient:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("Thermostability heuristic must not construct a gradio_client.Client")

    fake_module = type(sys)("gradio_client")
    fake_module.Client = _FailingClient
    monkeypatch.setitem(sys.modules, "gradio_client", fake_module)

    result = property_scoring_service.score(SAMPLE_SEQUENCE, TargetConditions(temperature_c=60, ph=10))
    assert result.thermostability.score is not None


def test_heuristic_formula_output_matches_pre_refactor_value():
    """
    Milestone 3A must not change the formula. This locks in a known score for
    a fixed set of composition inputs, computed from the pre-refactor formula:
        score = 0.42 + charged*1.2 + proline*0.9 - glycine*0.45 - temp_pressure*0.18
    """
    predictor = HeuristicThermostabilityPredictor()
    estimate = predictor.predict(
        charged_fraction=0.2, proline_fraction=0.05, glycine_fraction=0.05, temp_pressure=0.5
    )
    expected = 0.42 + 0.2 * 1.2 + 0.05 * 0.9 - 0.05 * 0.45 - 0.5 * 0.18
    assert estimate.score == round(max(0.0, min(1.0, expected)), 3)
