import pytest
from unittest.mock import AsyncMock, patch


SAMPLE_SEQUENCE = (
    "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH"
    "VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL"
    "SHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYYANKYNGVFQECC"
)


@pytest.mark.asyncio
async def test_sequence_validate_endpoint(client):
    response = await client.post(
        "/api/v1/sequences/validate",
        json={"sequence": f">candidate\n{SAMPLE_SEQUENCE}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["sequence_length"] == len(SAMPLE_SEQUENCE)


@pytest.mark.asyncio
async def test_sequence_features_endpoint(client):
    response = await client.post(
        "/api/v1/sequences/features",
        json={"sequence": SAMPLE_SEQUENCE},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["features"]["molecular_weight"] > 0
    assert data["features"]["sequence_length"] == len(SAMPLE_SEQUENCE)


@pytest.mark.asyncio
async def test_property_scoring_endpoint(client):
    response = await client.post(
        "/api/v1/properties/score",
        json={
            "sequence": SAMPLE_SEQUENCE,
            "target_conditions": {
                "temperature_c": 65,
                "ph": 10.5,
                "salinity_m_m": 250,
                "solvent_exposure": "moderate",
                "use_case": "detergent",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["industrial_fit_score"] <= 1
    assert data["method"] == "baseline_sequence_property_scaffold"
    assert data["uncertainty"]["calibration_status"] == "uncalibrated"
    assert data["uncertainty"]["uncertainty"] == pytest.approx(1 - data["confidence"])
    assert "Experimental wet-lab validation is required before industrial use." in data["limitations"]


@pytest.mark.asyncio
async def test_agent_analyze_endpoint_returns_plan_and_report(client):
    response = await client.post(
        "/api/v1/agents/analyze",
        json={
            "sequence": SAMPLE_SEQUENCE,
            "user_question": "Which candidate should be prioritized for alkaline detergent validation?",
            "target_conditions": {
                "temperature_c": 60,
                "ph": 10,
                "solvent_exposure": "moderate",
                "use_case": "detergent",
            },
            "variants": [
                {"variant_id": "V1", "mutations": ["M1A"]},
                {"variant_id": "V2", "sequence": SAMPLE_SEQUENCE[:-1] + "A"},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "validate_fasta" in data["agent_plan"]
    assert data["tool_calls"]
    assert "wet-lab validation" in data["final_report"]
    assert data["structured_analysis"]["variant_ranking"]["ranked_variants"]
    assert len(data["provenance"]["input_sha256"]) == 64
    assert data["provenance"]["llm_used"] is False
    assert data["structured_analysis"]["enzyme_function"]["prediction"]["uncertainty"]["level"] == "high"


@pytest.mark.asyncio
async def test_llm_narrative_mode_falls_back_without_api_key(client):
    response = await client.post(
        "/api/v1/agents/analyze",
        json={
            "sequence": SAMPLE_SEQUENCE,
            "narrative_mode": "llm",
            "target_conditions": {"temperature_c": 50, "ph": 8},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provenance"]["llm_used"] is False
    narrative_call = next(
        call for call in data["tool_calls"] if call["name"] == "narrate_report_with_llm"
    )
    assert narrative_call["status"] == "fallback"


@pytest.mark.asyncio
async def test_llm_is_only_a_narrative_layer(client):
    with patch(
        "app.services.agent_orchestrator.llm_service.generate_enzyme_report",
        AsyncMock(return_value=("Grounded narrative", True, "test-model")),
    ):
        response = await client.post(
            "/api/v1/agents/analyze",
            json={
                "sequence": SAMPLE_SEQUENCE,
                "narrative_mode": "llm",
                "target_conditions": {"temperature_c": 50, "ph": 8},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["final_report"] == "Grounded narrative"
    assert data["provenance"]["llm_used"] is True
    assert data["provenance"]["llm_model"] == "test-model"
    assert data["structured_analysis"]["property_scoring"]["method"] == "baseline_sequence_property_scaffold"
