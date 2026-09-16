import pytest

from app.services.embeddings import (
    BaselineEmbeddingProvider,
    ProteinEmbeddingClient,
    ProteinEmbeddingService,
    RemotePLMProvider,
    _cache_key,
)


def test_baseline_embedding_is_explicitly_labeled():
    result = ProteinEmbeddingService(mode="baseline").generate_embedding("ACDEFGHIK")

    assert result.mode == "baseline"
    assert result.status == "completed"
    assert result.provider == "neolysis"
    assert result.dimensions == 25


def test_baseline_provider_is_deterministic():
    provider = BaselineEmbeddingProvider()

    first = provider.generate("ACDEFGHIK")
    second = provider.generate("ACDEFGHIK")

    assert first.vector == second.vector


# ── Milestone 2: async client, explicit fallback, no in-process model loading ──

@pytest.mark.asyncio
async def test_esm2_mode_without_service_url_falls_back_to_baseline():
    """
    PROTEIN_EMBEDDING_MODE=esm2 with no PLM_SERVICE_URL configured must never
    attempt to load a model in-process. It must fall back to baseline and say why.
    """
    client = ProteinEmbeddingClient(mode="esm2")
    # Simulate PLM_SERVICE_URL being unset regardless of the developer's local .env.
    client.mode = "esm2"
    client._remote = None

    import app.config as config_module

    original = config_module.settings.PLM_SERVICE_URL
    config_module.settings.PLM_SERVICE_URL = None
    try:
        result = await client.embed("ACDEFGHIK")
    finally:
        config_module.settings.PLM_SERVICE_URL = original

    assert result.mode == "baseline"
    assert result.status == "fallback"
    assert "PLM_SERVICE_URL is not configured" in result.fallback_reason


@pytest.mark.asyncio
async def test_esm2_mode_falls_back_when_remote_call_fails(monkeypatch):
    """
    If the PLM microservice is unreachable or errors, the client must return an
    observable baseline fallback instead of raising or silently claiming to be
    a pretrained embedding.
    """
    client = ProteinEmbeddingClient(mode="esm2")

    async def fail(_self, _sequence):
        raise ConnectionError("connection refused")

    monkeypatch.setattr(RemotePLMProvider, "generate", fail)

    import app.config as config_module

    original = config_module.settings.PLM_SERVICE_URL
    config_module.settings.PLM_SERVICE_URL = "http://localhost:8100"
    try:
        result = await client.embed("ACDEFGHIK")
    finally:
        config_module.settings.PLM_SERVICE_URL = original

    assert result.mode == "baseline"
    assert result.status == "fallback"
    assert "PLM microservice call failed" in result.fallback_reason
    assert "connection refused" in result.fallback_reason


@pytest.mark.asyncio
async def test_remote_plm_provider_rejects_oversized_sequence_without_truncating():
    provider = RemotePLMProvider(
        base_url="http://localhost:8100",
        model_id="facebook/esm2_t30_150M_UR50D",
        max_residues=10,
        pooling="mean",
    )

    with pytest.raises(ValueError, match="exceeds PLM_MAX_RESIDUES"):
        await provider.generate("A" * 11)


def test_cache_key_includes_model_and_pooling_not_just_sequence_hash():
    """
    Cache identity must include more than the raw sequence hash, so a 35M
    embedding is never mistaken for a 150M or 650M model's embedding.
    """
    seq_hash = "abc123"
    key_35m = _cache_key("facebook/esm2_t12_35M_UR50D", "mean", seq_hash)
    key_150m = _cache_key("facebook/esm2_t30_150M_UR50D", "mean", seq_hash)

    assert key_35m != key_150m
    assert key_35m == f"plm:facebook/esm2_t12_35M_UR50D:mean:{seq_hash}"


@pytest.mark.asyncio
async def test_remote_plm_provider_uses_cache_hit_and_skips_http_call(monkeypatch):
    """
    A cache hit must be served without making an HTTP call to the PLM service —
    this is the whole point of caching embeddings.
    """
    provider = RemotePLMProvider(
        base_url="http://localhost:8100",
        model_id="facebook/esm2_t30_150M_UR50D",
        max_residues=1022,
        pooling="mean",
    )

    async def fake_read_cache(_cache_key):
        return [0.1, 0.2, 0.3]

    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("HTTP call should not happen on a cache hit")

    monkeypatch.setattr(RemotePLMProvider, "_read_cache", staticmethod(fake_read_cache))

    import httpx

    monkeypatch.setattr(httpx.AsyncClient, "post", fail_if_called)

    result = await provider.generate("ACDEFGHIK")

    assert result.status == "completed"
    assert result.vector == [0.1, 0.2, 0.3]
    assert "cache hit" in result.provider
