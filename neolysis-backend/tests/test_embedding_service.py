from app.services.embeddings import ProteinEmbeddingService


def test_baseline_embedding_is_explicitly_labeled():
    result = ProteinEmbeddingService(mode="baseline").generate_embedding("ACDEFGHIK")

    assert result.mode == "baseline"
    assert result.status == "completed"
    assert result.provider == "neolysis"
    assert result.dimensions == 25


def test_esm2_failure_returns_observable_baseline_fallback(monkeypatch):
    service = ProteinEmbeddingService(mode="esm2")

    def fail(_sequence):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(service, "_generate_esm2", fail)
    result = service.generate_embedding("ACDEFGHIK")

    assert result.mode == "baseline"
    assert result.status == "fallback"
    assert "model unavailable" in result.fallback_reason
