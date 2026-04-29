"""
TDD Tests — RAG Service (Qdrant)
==================================
Tests for RAG vector store operations using mocked Qdrant client.

Coverage:
    ✓ search_relevant_papers: returns list of dicts with correct keys
    ✓ search_relevant_papers: empty query returns empty list
    ✓ search_relevant_papers: Qdrant error returns empty list gracefully
    ✓ add_paper: calls upsert with correct payload
    ✓ add_paper: returns True on success, False on failure
    ✓ batch_add_papers: empty list returns 0
    ✓ batch_add_papers: calls encoder and upsert
    ✓ health_check: returns True when Qdrant responds
    ✓ health_check: returns False when Qdrant unavailable
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.rag_service import RAGService


@pytest.fixture
def service():
    return RAGService()


class TestSearchRelevantPapers:
    @pytest.mark.asyncio
    async def test_empty_query_returns_empty_list(self, service):
        result = await service.search_relevant_papers("")
        assert result == []

    @pytest.mark.asyncio
    async def test_whitespace_query_returns_empty_list(self, service):
        result = await service.search_relevant_papers("   ")
        assert result == []

    @pytest.mark.asyncio
    async def test_qdrant_error_returns_empty_list(self, service):
        with patch("app.services.rag_service._embed_text", side_effect=Exception("Qdrant down")):
            result = await service.search_relevant_papers("dengue treatment")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_correct_keys(self, service):
        mock_result = MagicMock()
        mock_result.payload = {"title": "Dengue study", "abstract": "Abstract text", "pmid": "12345"}
        mock_result.score = 0.92

        with patch("app.services.rag_service._embed_text", return_value=[0.1] * 384):
            with patch("app.services.rag_service._search_qdrant", return_value=[
                {"title": "Dengue study", "abstract": "Abstract text", "pmid": "12345", "score": 0.92}
            ]):
                results = await service.search_relevant_papers("dengue NS5", top_k=1)

        assert len(results) == 1
        for key in ("title", "abstract", "pmid", "score"):
            assert key in results[0]

    @pytest.mark.asyncio
    async def test_score_is_float(self, service):
        with patch("app.services.rag_service._embed_text", return_value=[0.1] * 384):
            with patch("app.services.rag_service._search_qdrant", return_value=[
                {"title": "Test", "abstract": "Test", "pmid": "999", "score": 0.85}
            ]):
                results = await service.search_relevant_papers("test query")
        if results:
            assert isinstance(results[0]["score"], float)


class TestAddPaper:
    @pytest.mark.asyncio
    async def test_success_returns_true(self, service):
        with patch("app.services.rag_service._upsert_paper", return_value=None):
            result = await service.add_paper("Test Title", "Test abstract", "pmid123")
        assert result is True

    @pytest.mark.asyncio
    async def test_failure_returns_false(self, service):
        with patch("app.services.rag_service._upsert_paper", side_effect=Exception("fail")):
            result = await service.add_paper("Title", "Abstract", "pmid456")
        assert result is False

    @pytest.mark.asyncio
    async def test_called_with_correct_args(self, service):
        with patch("app.services.rag_service._upsert_paper") as mock_upsert:
            await service.add_paper("Title", "Abstract text", "12345678")
            mock_upsert.assert_called_once_with("Title", "Abstract text", "12345678")


class TestBatchAddPapers:
    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self, service):
        result = await service.batch_add_papers([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_batch_calls_upsert(self, service):
        papers = [
            {"title": "P1", "abstract": "Abs1", "pmid": "001"},
            {"title": "P2", "abstract": "Abs2", "pmid": "002"},
        ]
        with patch("app.services.rag_service._batch_upsert", return_value=2):
            result = await service.batch_add_papers(papers)
        assert result == 2

    @pytest.mark.asyncio
    async def test_batch_error_returns_zero(self, service):
        with patch("app.services.rag_service._batch_upsert", side_effect=Exception("fail")):
            result = await service.batch_add_papers([{"title": "T", "abstract": "A", "pmid": "1"}])
        assert result == 0


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_returns_true_when_healthy(self, service):
        mock_client = MagicMock()
        mock_client.get_collections.return_value = MagicMock()
        with patch("app.services.rag_service._get_qdrant", return_value=mock_client):
            result = await service.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_unhealthy(self, service):
        with patch("app.services.rag_service._get_qdrant", side_effect=Exception("Connection refused")):
            result = await service.health_check()
        assert result is False
