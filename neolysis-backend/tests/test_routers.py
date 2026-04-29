"""
TDD Tests — API Router Endpoints
===================================
Integration tests for the REST API endpoints using the AsyncClient fixture.

Coverage:
    Compounds:
      ✓ GET /compounds → 200
      ✓ POST /compounds/validate → 200 with valid SMILES (Aspirin)
      ✓ POST /compounds/validate → 422 with invalid SMILES
      ✓ POST /compounds/validate → includes mw, logp, tpsa, lipinski_pass

    ADMET:
      ✓ POST /admet → 200 with valid SMILES
      ✓ POST /admet → 422 with invalid SMILES
      ✓ POST /admet → response contains caco2, herg, dili, bbb, lipophilicity

    Knowledge Graph:
      ✓ GET /knowledge-graph → 422 without any filter
      ✓ GET /knowledge-graph?subject=NS5 → 200
      ✓ POST /knowledge-graph → 201 with valid triple

    Diseases:
      ✓ GET /diseases → 200 with list
      ✓ GET /diseases/{invalid_id} → 404

    Health:
      ✓ GET /health → 200 with status: healthy
      ✓ GET /health/full → 200 with subsystems

    Insight:
      ✓ POST /insight without params → 422
      ✓ POST /insight with query → 200 (mocked RAG+LLM)
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock

PREFIX = "/api/v1"


# ── Compounds ──────────────────────────────────────────────────────────────

class TestCompoundsRouter:
    @pytest.mark.asyncio
    async def test_list_compounds_returns_200(self, client):
        response = await client.get(f"{PREFIX}/compounds/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_validate_aspirin_returns_200(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/compounds/validate",
            json={"smiles": sample_smiles["aspirin"]},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_returns_required_fields(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/compounds/validate",
            json={"smiles": sample_smiles["aspirin"]},
        )
        data = response.json()
        for field in ("mw", "logp", "hbd", "hba", "tpsa", "lipinski_pass", "violations"):
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_validate_invalid_smiles_returns_422(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/compounds/validate",
            json={"smiles": sample_smiles["invalid"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_aspirin_lipinski_pass(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/compounds/validate",
            json={"smiles": sample_smiles["aspirin"]},
        )
        assert response.json()["lipinski_pass"] is True

    @pytest.mark.asyncio
    async def test_validate_requires_smiles_field(self, client):
        response = await client.post(f"{PREFIX}/compounds/validate", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_compound_not_found_returns_404(self, client):
        response = await client.get(f"{PREFIX}/compounds/999999")
        assert response.status_code == 404


# ── ADMET ──────────────────────────────────────────────────────────────────

class TestAdmetRouter:
    @pytest.mark.asyncio
    async def test_valid_smiles_returns_200(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/admet/",
            json={"smiles": sample_smiles["aspirin"]},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_five_admet_properties(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/admet/",
            json={"smiles": sample_smiles["aspirin"]},
        )
        data = response.json()
        for prop in ("caco2", "herg", "dili", "bbb", "lipophilicity"):
            assert prop in data

    @pytest.mark.asyncio
    async def test_invalid_smiles_returns_422(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/admet/",
            json={"smiles": sample_smiles["invalid"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_response_has_drug_likeness(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/admet/",
            json={"smiles": sample_smiles["aspirin"]},
        )
        assert "drug_likeness" in response.json()

    @pytest.mark.asyncio
    async def test_response_risk_levels_valid(self, client, sample_smiles):
        response = await client.post(
            f"{PREFIX}/admet/",
            json={"smiles": sample_smiles["caffeine"]},
        )
        data = response.json()
        for prop in ("caco2", "herg", "dili", "bbb", "lipophilicity"):
            assert data[prop]["risk_level"] in ("low", "medium", "high")


# ── Knowledge Graph ────────────────────────────────────────────────────────

class TestKnowledgeGraphRouter:
    @pytest.mark.asyncio
    async def test_query_without_filters_returns_422(self, client):
        response = await client.get(f"{PREFIX}/knowledge-graph/")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_with_subject_returns_200(self, client):
        response = await client.get(f"{PREFIX}/knowledge-graph/?subject=Dengue+NS5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_query_with_relation_returns_200(self, client):
        response = await client.get(f"{PREFIX}/knowledge-graph/?relation=inhibited_by")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_relations_returns_200(self, client):
        response = await client.get(f"{PREFIX}/knowledge-graph/relations")
        assert response.status_code == 200
        assert "relations" in response.json()

    @pytest.mark.asyncio
    async def test_create_triple_returns_201(self, client):
        response = await client.post(
            f"{PREFIX}/knowledge-graph/",
            json={
                "subject": "Dengue NS5",
                "relation": "inhibited_by",
                "object": "Quercetin",
                "source": "Test",
                "confidence": 0.9,
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_created_triple_has_id(self, client):
        response = await client.post(
            f"{PREFIX}/knowledge-graph/",
            json={"subject": "NS3", "relation": "targets", "object": "ATP"},
        )
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_triple_invalid_confidence_returns_422(self, client):
        response = await client.post(
            f"{PREFIX}/knowledge-graph/",
            json={"subject": "X", "relation": "Y", "object": "Z", "confidence": 2.0},  # > 1.0
        )
        assert response.status_code == 422


# ── Diseases ───────────────────────────────────────────────────────────────

class TestDiseasesRouter:
    @pytest.mark.asyncio
    async def test_list_returns_200(self, client):
        response = await client.get(f"{PREFIX}/diseases/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_404_or_422(self, client):
        response = await client.get(f"{PREFIX}/diseases/{uuid.uuid4()}")
        assert response.status_code in (404, 422)

    @pytest.mark.asyncio
    async def test_create_disease_returns_201(self, client):
        response = await client.post(
            f"{PREFIX}/diseases/",
            json={"name": "Dengue Fever", "description": "Mosquito-borne", "region": "ASEAN"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_created_disease_has_uuid(self, client):
        response = await client.post(
            f"{PREFIX}/diseases/",
            json={"name": "Test Disease", "region": "ASEAN"},
        )
        data = response.json()
        assert "id" in data
        # Validate it's a UUID
        uuid.UUID(data["id"])


# ── Health ─────────────────────────────────────────────────────────────────

class TestHealthRouter:
    @pytest.mark.asyncio
    async def test_liveness_returns_200(self, client):
        response = await client.get(f"{PREFIX}/health/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_liveness_has_status_field(self, client):
        response = await client.get(f"{PREFIX}/health/")
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_full_health_returns_200(self, client):
        with patch("app.services.rag_service.RAGService.health_check", AsyncMock(return_value=True)):
            response = await client.get(f"{PREFIX}/health/full")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_full_health_has_subsystems(self, client):
        with patch("app.services.rag_service.RAGService.health_check", AsyncMock(return_value=True)):
            response = await client.get(f"{PREFIX}/health/full")
        data = response.json()
        assert "subsystems" in data
        assert "postgresql" in data["subsystems"]


# ── Insight ────────────────────────────────────────────────────────────────

class TestInsightRouter:
    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, client):
        response = await client.post(f"{PREFIX}/insight/", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_with_query_returns_200(self, client):
        fallback = {
            "summary": "No papers found.", "drug_assessment": "N/A",
            "next_steps": "Run pubmed_crawler.py", "citations": [],
            "kg_context": [], "rag_papers_used": 0, "fallback": True,
        }
        with patch("app.services.insight_service.InsightService.generate_insight", AsyncMock(return_value=fallback)):
            response = await client.post(
                f"{PREFIX}/insight/",
                json={"query": "dengue NS5 inhibitor quercetin"},
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_required_keys(self, client):
        mock_result = {
            "summary": "test", "drug_assessment": "test", "next_steps": "test",
            "citations": [], "kg_context": [], "rag_papers_used": 0, "fallback": True,
        }
        with patch("app.services.insight_service.InsightService.generate_insight", AsyncMock(return_value=mock_result)):
            response = await client.post(f"{PREFIX}/insight/", json={"query": "test query"})
        for key in ("summary", "drug_assessment", "next_steps", "citations"):
            assert key in response.json()
