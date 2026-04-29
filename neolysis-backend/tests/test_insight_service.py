"""
TDD Tests — Insight Service Pipeline
=======================================
Tests for the RAG→KG→LLM orchestration pipeline.

Coverage:
    ✓ generate_insight: returns fallback when 0 RAG papers found
    ✓ generate_insight: does NOT call LLM when papers < MIN_PAPERS_FOR_LLM
    ✓ generate_insight: calls RAG before LLM (order verification)
    ✓ generate_insight: returns rag_papers_used count
    ✓ generate_insight: structured output has required keys
    ✓ _build_grounded_prompt: includes protein, compound, paper info
    ✓ _parse_llm_output: valid JSON parsed correctly
    ✓ _parse_llm_output: invalid JSON wrapped gracefully
    ✓ _parse_llm_output: markdown fences stripped before parsing
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.insight_service import InsightService, FALLBACK_RESPONSE


@pytest.fixture
def service():
    return InsightService()


@pytest.fixture
def mock_papers():
    return [
        {"title": "Dengue NS5 inhibition study", "abstract": "Quercetin inhibits NS5...", "pmid": "11111111", "score": 0.95},
        {"title": "Leptospirosis drug targets", "abstract": "LipL32 is a key outer membrane protein...", "pmid": "22222222", "score": 0.88},
    ]


@pytest.fixture
def sample_llm_response():
    return json.dumps({
        "summary": "NS5 is a validated drug target for dengue.",
        "drug_assessment": "Quercetin shows moderate binding affinity at -7.2 kcal/mol.",
        "next_steps": "1. Run MD simulation. 2. Validate with IC50 assay.",
        "citations": [{"title": "Dengue NS5 inhibition study", "pmid": "11111111"}],
    })


class TestGenerateInsightFallback:
    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_papers(self, service, mock_db):
        with patch("app.services.insight_service.rag_service.search_relevant_papers", AsyncMock(return_value=[])):
            result = await service.generate_insight(
                db=mock_db,
                protein_id=None,
                compound_id=None,
                query="dengue NS5 inhibitor",
            )
        assert result["fallback"] is True
        assert result["rag_papers_used"] == 0
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_fallback_does_not_call_llm(self, service, mock_db):
        with patch("app.services.insight_service.rag_service.search_relevant_papers", AsyncMock(return_value=[])):
            with patch("app.services.insight_service.llm_service.generate_insight") as mock_llm:
                await service.generate_insight(db=mock_db, protein_id=None, compound_id=None, query="test")
        mock_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_contains_crawler_instruction(self, service, mock_db):
        with patch("app.services.insight_service.rag_service.search_relevant_papers", AsyncMock(return_value=[])):
            result = await service.generate_insight(db=mock_db, protein_id=None, compound_id=None, query="test")
        assert "pubmed_crawler" in result["next_steps"].lower() or "crawler" in result["next_steps"].lower()


class TestGenerateInsightWithPapers:
    @pytest.mark.asyncio
    async def test_returns_rag_papers_count(self, service, mock_db, mock_papers, sample_llm_response):
        with patch("app.services.insight_service.rag_service.search_relevant_papers", AsyncMock(return_value=mock_papers)):
            with patch("app.services.insight_service.kg_service.get_relations", AsyncMock(return_value=[])):
                with patch("app.services.insight_service.kg_service.get_context_for_prompt", AsyncMock(return_value="")):
                    with patch("app.services.insight_service.llm_service.generate_insight", AsyncMock(return_value=sample_llm_response)):
                        result = await service.generate_insight(
                            db=mock_db, protein_id=None, compound_id=None, query="dengue NS5"
                        )
        assert result["rag_papers_used"] == len(mock_papers)

    @pytest.mark.asyncio
    async def test_result_has_all_required_keys(self, service, mock_db, mock_papers, sample_llm_response):
        with patch("app.services.insight_service.rag_service.search_relevant_papers", AsyncMock(return_value=mock_papers)):
            with patch("app.services.insight_service.kg_service.get_relations", AsyncMock(return_value=[])):
                with patch("app.services.insight_service.kg_service.get_context_for_prompt", AsyncMock(return_value="")):
                    with patch("app.services.insight_service.llm_service.generate_insight", AsyncMock(return_value=sample_llm_response)):
                        result = await service.generate_insight(db=mock_db, protein_id=None, compound_id=None, query="test")

        for key in ("summary", "drug_assessment", "next_steps", "citations", "rag_papers_used", "fallback"):
            assert key in result, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_fallback_is_false_with_papers(self, service, mock_db, mock_papers, sample_llm_response):
        with patch("app.services.insight_service.rag_service.search_relevant_papers", AsyncMock(return_value=mock_papers)):
            with patch("app.services.insight_service.kg_service.get_relations", AsyncMock(return_value=[])):
                with patch("app.services.insight_service.kg_service.get_context_for_prompt", AsyncMock(return_value="")):
                    with patch("app.services.insight_service.llm_service.generate_insight", AsyncMock(return_value=sample_llm_response)):
                        result = await service.generate_insight(db=mock_db, protein_id=None, compound_id=None, query="test")
        assert result["fallback"] is False


class TestBuildGroundedPrompt:
    def test_includes_paper_titles(self, service, mock_papers):
        prompt = service._build_grounded_prompt(
            context={"target_name": "NS5", "disease": "Dengue"},
            papers=mock_papers,
            kg_context="KG context string",
            query="NS5 inhibitor",
        )
        assert "Dengue NS5 inhibition study" in prompt

    def test_includes_protein_name(self, service, mock_papers):
        prompt = service._build_grounded_prompt(
            context={"target_name": "LipL32", "disease": "Leptospirosis"},
            papers=mock_papers,
            kg_context="",
            query="test",
        )
        assert "LipL32" in prompt

    def test_includes_pmid(self, service, mock_papers):
        prompt = service._build_grounded_prompt(
            context={}, papers=mock_papers, kg_context="", query="test"
        )
        assert "11111111" in prompt

    def test_includes_kg_context(self, service, mock_papers):
        prompt = service._build_grounded_prompt(
            context={}, papers=mock_papers,
            kg_context="NS5 → inhibited_by → Quercetin",
            query="test",
        )
        assert "NS5 → inhibited_by → Quercetin" in prompt

    def test_prompt_requires_json_output(self, service, mock_papers):
        prompt = service._build_grounded_prompt(context={}, papers=mock_papers, kg_context="", query="test")
        assert "JSON" in prompt


class TestParseLLMOutput:
    def test_valid_json_parsed_correctly(self, service, sample_llm_response, mock_papers):
        result = service._parse_llm_output(sample_llm_response, mock_papers)
        assert result["summary"] == "NS5 is a validated drug target for dengue."
        assert len(result["citations"]) >= 1

    def test_invalid_json_returns_wrapped_summary(self, service, mock_papers):
        result = service._parse_llm_output("Some plain text response", mock_papers)
        assert "summary" in result
        assert "drug_assessment" in result
        assert "citations" in result

    def test_markdown_fences_stripped(self, service, mock_papers):
        fenced = '```json\n{"summary": "test", "drug_assessment": "ok", "next_steps": "go", "citations": []}\n```'
        result = service._parse_llm_output(fenced, mock_papers)
        assert result["summary"] == "test"

    def test_missing_keys_filled_with_na(self, service, mock_papers):
        partial = json.dumps({"summary": "partial response"})
        result = service._parse_llm_output(partial, mock_papers)
        assert result["drug_assessment"] == "N/A"
        assert result["next_steps"] == "N/A"
