"""
Unit tests for NvidiaNimClient. All HTTP calls are mocked — no network access
to NVIDIA happens in this suite, consistent with NVIDIA_API_KEY being unset
in this environment.
"""
import httpx
import pytest

from app.services.nvidia.client import NvidiaNimClient
from app.services.nvidia.errors import ProviderRateLimited, ProviderTimeout, ProviderUnavailable


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict, headers: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_body = json_body
        self.headers = headers or {}
        self.text = text or str(json_body)

    def json(self):
        return self._json_body


@pytest.mark.asyncio
async def test_successful_post_returns_json(monkeypatch):
    client = NvidiaNimClient(base_url="https://fake.nvidia", api_key="test-key")

    async def fake_post(_self, _url, headers=None, json=None):
        assert headers["Authorization"] == "Bearer test-key"
        return _FakeResponse(200, {"pdb": "ATOM ..."})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.post("/v1/fake", {"sequence": "MKT"}, provider_label="nvidia", model_label="openfold3")
    assert result == {"pdb": "ATOM ..."}


@pytest.mark.asyncio
async def test_client_error_is_not_retried(monkeypatch):
    client = NvidiaNimClient(base_url="https://fake.nvidia", api_key="test-key", max_retries=3)
    call_count = 0

    async def fake_post(_self, _url, headers=None, json=None):
        nonlocal call_count
        call_count += 1
        return _FakeResponse(422, {}, text="bad request")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(ProviderUnavailable):
        await client.post("/v1/fake", {}, provider_label="nvidia", model_label="openfold3")

    assert call_count == 1  # no retry for 4xx


@pytest.mark.asyncio
async def test_rate_limit_raises_after_exhausting_retries(monkeypatch):
    client = NvidiaNimClient(base_url="https://fake.nvidia", api_key="test-key", max_retries=1, base_backoff_seconds=0.001)
    call_count = 0

    async def fake_post(_self, _url, headers=None, json=None):
        nonlocal call_count
        call_count += 1
        return _FakeResponse(429, {}, headers={"Retry-After": "0.001"})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(ProviderRateLimited) as exc_info:
        await client.post("/v1/fake", {}, provider_label="nvidia", model_label="openfold3")

    assert call_count == 2  # initial attempt + 1 retry
    assert exc_info.value.retry_after_seconds == 0.001


@pytest.mark.asyncio
async def test_timeout_raises_provider_timeout_after_exhausting_retries(monkeypatch):
    client = NvidiaNimClient(base_url="https://fake.nvidia", api_key="test-key", max_retries=1, base_backoff_seconds=0.001)

    async def fake_post(_self, _url, headers=None, json=None):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(ProviderTimeout):
        await client.post("/v1/fake", {}, provider_label="nvidia", model_label="openfold3")


@pytest.mark.asyncio
async def test_server_error_is_retried_then_raises(monkeypatch):
    client = NvidiaNimClient(base_url="https://fake.nvidia", api_key="test-key", max_retries=2, base_backoff_seconds=0.001)
    call_count = 0

    async def fake_post(_self, _url, headers=None, json=None):
        nonlocal call_count
        call_count += 1
        return _FakeResponse(503, {}, text="upstream unavailable")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(ProviderUnavailable):
        await client.post("/v1/fake", {}, provider_label="nvidia", model_label="openfold3")

    assert call_count == 3  # initial + 2 retries


def test_fingerprint_never_includes_raw_sequence():
    fingerprint = NvidiaNimClient._fingerprint_payload({"sequence": "MKTPROPRIETARYSEQUENCE"})
    assert "MKTPROPRIETARYSEQUENCE" not in fingerprint
    assert "sha256:" in fingerprint
    assert "len:" in fingerprint
