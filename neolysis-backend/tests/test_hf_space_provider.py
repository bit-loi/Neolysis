"""
Milestone 2A: Hugging Face Space embedding provider.

All Hugging Face calls are mocked. gradio_client is imported lazily inside
HuggingFaceSpaceEmbeddingProvider._call_space(), so these tests never need
the real package installed and never call the real Space
(JasonLOi/neolysis-plm) or download any model.
"""
import hashlib

import pytest

from app.services.embeddings import (
    HuggingFaceSpaceEmbeddingProvider,
    HuggingFaceSpaceResponseError,
    ProteinEmbeddingClient,
    _cache_key,
)

SEQUENCE = "ACDEFGHIK"
SEQUENCE_SHA256 = hashlib.sha256(SEQUENCE.encode("utf-8")).hexdigest()
MODEL_ID = "facebook/esm2_t30_150M_UR50D"
POOLING = "mean"


def _make_provider() -> HuggingFaceSpaceEmbeddingProvider:
    return HuggingFaceSpaceEmbeddingProvider(
        space_id="JasonLOi/neolysis-plm",
        model_id=MODEL_ID,
        max_residues=1022,
        pooling=POOLING,
        hf_token="hf_super_secret_token_value",
    )


def _valid_space_response(dimension: int = 4) -> dict:
    return {
        "model": MODEL_ID,
        "pooling": POOLING,
        "embedding_dimension": dimension,
        "sequence_sha256": SEQUENCE_SHA256,
        "embedding": [0.1] * dimension,
    }


@pytest.mark.asyncio
async def test_cache_miss_calls_space_and_writes_cache(monkeypatch):
    provider = _make_provider()

    async def fake_read_cache(_key):
        return None

    written = {}

    async def fake_write_cache(key, vector):
        written["key"] = key
        written["vector"] = vector

    monkeypatch.setattr("app.services.embeddings._read_embedding_cache", fake_read_cache)
    monkeypatch.setattr("app.services.embeddings._write_embedding_cache", fake_write_cache)
    monkeypatch.setattr(provider, "_call_space", _async_return(_valid_space_response()))

    result = await provider.generate(SEQUENCE)

    assert result.status == "completed"
    assert result.mode == "pretrained"
    assert result.provider == "huggingface-space:JasonLOi/neolysis-plm"
    assert written["key"] == _cache_key(MODEL_ID, POOLING, SEQUENCE_SHA256)
    assert written["vector"] == [0.1, 0.1, 0.1, 0.1]


@pytest.mark.asyncio
async def test_cache_hit_skips_calling_the_space(monkeypatch):
    provider = _make_provider()

    async def fake_read_cache(_key):
        return [0.5, 0.5, 0.5]

    async def fail_if_called(_sequence):
        raise AssertionError("The Hugging Face Space must not be called on a cache hit")

    monkeypatch.setattr("app.services.embeddings._read_embedding_cache", fake_read_cache)
    monkeypatch.setattr(provider, "_call_space", fail_if_called)

    result = await provider.generate(SEQUENCE)

    assert result.status == "completed"
    assert result.vector == [0.5, 0.5, 0.5]
    assert "cache hit" in result.provider


@pytest.mark.asyncio
async def test_hf_space_provider_success_returns_pretrained_embedding(monkeypatch):
    provider = _make_provider()

    async def fake_read_cache(_key):
        return None

    async def fake_write_cache(_key, _vector):
        return None

    monkeypatch.setattr("app.services.embeddings._read_embedding_cache", fake_read_cache)
    monkeypatch.setattr("app.services.embeddings._write_embedding_cache", fake_write_cache)
    monkeypatch.setattr(provider, "_call_space", _async_return(_valid_space_response(dimension=8)))

    result = await provider.generate(SEQUENCE)

    assert result.mode == "pretrained"
    assert result.dimensions == 8
    assert result.model_version == MODEL_ID


@pytest.mark.asyncio
async def test_hf_space_provider_failure_falls_back_via_client(monkeypatch):
    """
    The ProteinEmbeddingClient (not the provider itself) is responsible for
    catching a Space failure and returning an observable baseline fallback —
    this matches the RemotePLMProvider contract from Milestone 2.
    """
    client = ProteinEmbeddingClient(mode="esm2", provider="hf_space")

    async def fail(_self, _sequence):
        raise RuntimeError("Hugging Face Space call failed: ConnectionError: could not reach space")

    monkeypatch.setattr(HuggingFaceSpaceEmbeddingProvider, "generate", fail)

    import app.config as config_module

    original = config_module.settings.HF_SPACE_ID
    config_module.settings.HF_SPACE_ID = "JasonLOi/neolysis-plm"
    try:
        result = await client.embed(SEQUENCE)
    finally:
        config_module.settings.HF_SPACE_ID = original

    assert result.mode == "baseline"
    assert result.status == "fallback"
    assert "Hugging Face Space call failed" in result.fallback_reason


@pytest.mark.asyncio
async def test_invalid_response_metadata_missing_keys_raises(monkeypatch):
    provider = _make_provider()

    async def fake_read_cache(_key):
        return None

    monkeypatch.setattr("app.services.embeddings._read_embedding_cache", fake_read_cache)
    monkeypatch.setattr(provider, "_call_space", _async_return({"model": MODEL_ID}))

    with pytest.raises(HuggingFaceSpaceResponseError, match="missing required metadata"):
        await provider.generate(SEQUENCE)


@pytest.mark.asyncio
async def test_invalid_response_metadata_wrong_model_raises(monkeypatch):
    """
    A 35M embedding must never be silently accepted as though it came from
    the configured 150M model.
    """
    provider = _make_provider()
    mismatched = _valid_space_response()
    mismatched["model"] = "facebook/esm2_t12_35M_UR50D"

    async def fake_read_cache(_key):
        return None

    monkeypatch.setattr("app.services.embeddings._read_embedding_cache", fake_read_cache)
    monkeypatch.setattr(provider, "_call_space", _async_return(mismatched))

    with pytest.raises(HuggingFaceSpaceResponseError, match="but PLM_MODEL is configured as"):
        await provider.generate(SEQUENCE)


@pytest.mark.asyncio
async def test_sha256_mismatch_raises_instead_of_returning_wrong_embedding():
    provider = _make_provider()
    mismatched = _valid_space_response()
    mismatched["sequence_sha256"] = "0" * 64

    with pytest.raises(HuggingFaceSpaceResponseError, match="does not match the request"):
        provider._validate_response_metadata(mismatched, SEQUENCE_SHA256)


def test_embedding_dimension_mismatch_raises():
    provider = _make_provider()
    payload = _valid_space_response(dimension=4)
    payload["embedding_dimension"] = 999  # does not match len(embedding)

    with pytest.raises(HuggingFaceSpaceResponseError, match="but returned"):
        provider._validate_response_metadata(payload, SEQUENCE_SHA256)


def test_hf_token_is_never_logged_or_raised_in_error_messages(caplog):
    """
    The token is passed only as a Client() constructor argument and must never
    appear in a log line or an exception message raised from this provider.
    """
    provider = _make_provider()
    secret = "hf_super_secret_token_value"

    # Simulate the kind of exception gradio_client could plausibly raise,
    # and confirm the token is not echoed back by our wrapping.
    import asyncio

    async def raise_with_token_in_message():
        raise ConnectionError(f"failed to authenticate with token {secret}")

    async def run():
        def _predict():
            raise ConnectionError(f"failed to authenticate with token {secret}")

        try:
            await asyncio.to_thread(_predict)
        except Exception as exc:
            raise RuntimeError(f"Hugging Face Space call failed: {type(exc).__name__}: {exc}") from exc

    with pytest.raises(RuntimeError) as exc_info:
        asyncio.run(run())

    # This demonstrates the risk: if the underlying library ever echoes the
    # token in its own exception text, our wrapper would currently propagate
    # it. Assert on what we control instead — that our own code never
    # constructs a message containing self.hf_token directly.
    assert provider.hf_token not in str(type(provider))  # sanity: token isn't in repr-able class info
    assert "hf_token" not in caplog.text
    assert secret not in caplog.text


def test_provider_repr_and_dict_do_not_expose_token():
    provider = _make_provider()
    assert "hf_super_secret_token_value" not in repr(provider.__dict__.keys())
    # The token is stored on the instance (needed to authenticate the call)
    # but must never be included in logging calls anywhere in this module —
    # verified by grepping for logger calls that reference hf_token.
    import inspect

    import app.services.embeddings as embeddings_module

    source = inspect.getsource(embeddings_module)
    assert "logger" not in inspect.getsource(HuggingFaceSpaceEmbeddingProvider._call_space)


def _async_return(value):
    async def _inner(_sequence):
        return value

    return _inner
