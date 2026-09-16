"""
Neolysis — Protein Embedding Client
=====================================
Domain-facing entry point for protein embeddings. Callers (enzyme function
prediction, property scoring, variant ranking, the agent orchestrator) depend
only on `protein_embedding_service.generate_embedding(sequence)` — they never
import torch/transformers and never talk to Redis or the PLM microservice
directly.

Architecture
------------
    ProteinEmbeddingService (facade, backward-compatible entry point)
        └── ProteinEmbeddingClient
                ├── BaselineEmbeddingProvider          (in-process, always available)
                ├── RemotePLMProvider                  (HTTP call to a self-hosted PLM microservice)
                └── HuggingFaceSpaceEmbeddingProvider   (gradio_client call to a hosted HF Space)
                        └── Redis cache (best-effort; disabled if unreachable)

A large protein language model is NEVER loaded inside this process. Provider
selection is controlled by PLM_PROVIDER:
    - "hf_space" -> HuggingFaceSpaceEmbeddingProvider (Milestone 2A)
    - "http"     -> RemotePLMProvider (Milestone 2, self-hosted microservice)
    - unset      -> legacy behavior: PROTEIN_EMBEDDING_MODE=esm2 + PLM_SERVICE_URL
                     activates RemotePLMProvider, for backward compatibility with
                     deployments configured before PLM_PROVIDER existed.

If the configured provider is unreachable, times out, or returns an error, or
the response metadata does not match what was requested, this client falls
back to the deterministic baseline embedding and marks the result
status="fallback" with an explicit fallback_reason — it never silently
pretends to be a pretrained embedding.

Cache key
---------
Cache identity includes more than the sequence hash, so a 35M embedding can
never be silently reused as though it came from a 150M or 650M model:

    plm:{model_id}:{pooling}:{sequence_sha256}
"""
import hashlib
import json
from typing import Any, Optional

import httpx
from loguru import logger

from app.config import settings
from app.core.cache import cache
from app.schemas.enzyme import EmbeddingResult
from app.services.protein_features import AMINO_ACIDS


def _sequence_sha256(sequence: str) -> str:
    return hashlib.sha256(sequence.encode("utf-8")).hexdigest()


def _cache_key(model_id: str, pooling: str, sequence_sha256: str) -> str:
    return f"plm:{model_id}:{pooling}:{sequence_sha256}"


async def _read_embedding_cache(cache_key: str) -> Optional[list[float]]:
    try:
        await cache.ensure_connected()
        cached = await cache.get(cache_key)
    except Exception as exc:
        logger.warning(f"Embedding cache read skipped ({type(exc).__name__}: {exc})")
        return None
    if cached is None:
        return None
    try:
        return json.loads(cached) if isinstance(cached, str) else cached
    except (TypeError, ValueError):
        return None


async def _write_embedding_cache(cache_key: str, vector: list[float]) -> None:
    try:
        await cache.ensure_connected()
        await cache.set(cache_key, json.dumps(vector), ttl=60 * 60 * 24 * 30)
    except Exception as exc:
        # Caching is strictly best-effort. A cache outage must never break
        # embedding generation or make the request appear to fail.
        logger.warning(f"Embedding cache write skipped ({type(exc).__name__}: {exc})")


class BaselineEmbeddingProvider:
    """Training-free composition embedding. Always available, no dependencies."""

    def generate(self, sequence: str) -> EmbeddingResult:
        length = max(len(sequence), 1)
        composition_vector = [round(sequence.count(aa) / length, 6) for aa in AMINO_ACIDS]
        grouped = [
            sum(sequence.count(aa) for aa in "AVLIMFWY") / length,
            sum(sequence.count(aa) for aa in "DE") / length,
            sum(sequence.count(aa) for aa in "KRH") / length,
            sum(sequence.count(aa) for aa in "STNQ") / length,
            sum(sequence.count(aa) for aa in "CGP") / length,
        ]
        vector = composition_vector + [round(value, 6) for value in grouped]
        return EmbeddingResult(
            vector=vector,
            dimensions=len(vector),
            mode="baseline",
            model_version="baseline-composition-v0.1",
            provider="neolysis",
            status="completed",
            fallback_reason=None,
            limitations=[
                "This is a lightweight baseline embedding, not a trained protein language model embedding."
            ],
        )


class RemotePLMProvider:
    """
    Calls the dedicated PLM inference microservice (services/plm-inference) over
    HTTP. This is the ONLY provider allowed to produce a pretrained protein
    language model embedding — it never loads a model in this process.
    """

    def __init__(self, base_url: str, model_id: str, max_residues: int, pooling: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.max_residues = max_residues
        self.pooling = pooling
        self.timeout = timeout

    async def generate(self, sequence: str) -> EmbeddingResult:
        if len(sequence) > self.max_residues:
            # Never silently truncate. The caller (ProteinEmbeddingClient) treats
            # this as a fallback trigger, not a value to sneak past validation.
            raise ValueError(
                f"Sequence length {len(sequence)} exceeds PLM_MAX_RESIDUES={self.max_residues}; "
                "refusing to truncate. Configure explicit chunking upstream if longer "
                "sequences must be supported."
            )

        sequence_sha256 = _sequence_sha256(sequence)
        cache_key = _cache_key(self.model_id, self.pooling, sequence_sha256)

        cached_vector = await self._read_cache(cache_key)
        if cached_vector is not None:
            return EmbeddingResult(
                vector=cached_vector,
                dimensions=len(cached_vector),
                mode="pretrained",
                model_version=self.model_id,
                provider="neolysis-plm-service (cache hit)",
                status="completed",
                limitations=[
                    "A pretrained representation is not itself a calibrated enzyme-function classifier.",
                    "Downstream conclusions still require database, structural, and wet-lab validation.",
                ],
            )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embed",
                json={"sequence": sequence, "pooling": self.pooling},
            )
        response.raise_for_status()
        payload = response.json()

        vector = [round(float(value), 6) for value in payload["embedding"]]
        await self._write_cache(cache_key, vector)

        return EmbeddingResult(
            vector=vector,
            dimensions=payload.get("embedding_dimension", len(vector)),
            mode="pretrained",
            model_version=payload.get("model", self.model_id),
            provider="neolysis-plm-service",
            status="completed",
            limitations=[
                "A pretrained representation is not itself a calibrated enzyme-function classifier.",
                "Downstream conclusions still require database, structural, and wet-lab validation.",
            ],
        )

    @staticmethod
    async def _read_cache(cache_key: str) -> Optional[list[float]]:
        return await _read_embedding_cache(cache_key)

    @staticmethod
    async def _write_cache(cache_key: str, vector: list[float]) -> None:
        await _write_embedding_cache(cache_key, vector)


class HuggingFaceSpaceResponseError(ValueError):
    """Raised when a Hugging Face Space returns metadata that doesn't match the request."""


class HuggingFaceSpaceEmbeddingProvider:
    """
    Calls a hosted Hugging Face Space (via gradio_client) instead of a
    self-hosted PLM microservice. Like RemotePLMProvider, this is the ONLY
    place a pretrained embedding is produced for this provider path — the
    model itself runs on the Space's infrastructure, never in this process.

    gradio_client is imported lazily (inside generate(), not at module import
    time) so that importing this module — and running the rest of the test
    suite — never requires gradio_client to be installed. Tests mock
    generate()'s HTTP-equivalent call directly and never need the real
    package.
    """

    def __init__(
        self,
        space_id: str,
        model_id: str,
        max_residues: int,
        pooling: str,
        hf_token: Optional[str] = None,
        api_name: str = "/embed",
    ):
        self.space_id = space_id
        self.model_id = model_id
        self.max_residues = max_residues
        self.pooling = pooling
        self.hf_token = hf_token
        self.api_name = api_name

    async def generate(self, sequence: str) -> EmbeddingResult:
        if len(sequence) > self.max_residues:
            # Never silently truncate — same contract as RemotePLMProvider.
            raise ValueError(
                f"Sequence length {len(sequence)} exceeds PLM_MAX_RESIDUES={self.max_residues}; "
                "refusing to truncate. Configure explicit chunking upstream if longer "
                "sequences must be supported."
            )

        sequence_sha256 = _sequence_sha256(sequence)
        cache_key = _cache_key(self.model_id, self.pooling, sequence_sha256)

        cached_vector = await _read_embedding_cache(cache_key)
        if cached_vector is not None:
            return EmbeddingResult(
                vector=cached_vector,
                dimensions=len(cached_vector),
                mode="pretrained",
                model_version=self.model_id,
                provider=f"huggingface-space:{self.space_id} (cache hit)",
                status="completed",
                limitations=[
                    "A pretrained representation is not itself a calibrated enzyme-function classifier.",
                    "Downstream conclusions still require database, structural, and wet-lab validation.",
                ],
            )

        payload = await self._call_space(sequence)
        self._validate_response_metadata(payload, sequence_sha256)

        vector = [round(float(value), 6) for value in payload["embedding"]]
        await _write_embedding_cache(cache_key, vector)

        return EmbeddingResult(
            vector=vector,
            dimensions=payload.get("embedding_dimension", len(vector)),
            mode="pretrained",
            model_version=payload.get("model", self.model_id),
            provider=f"huggingface-space:{self.space_id}",
            status="completed",
            limitations=[
                "A pretrained representation is not itself a calibrated enzyme-function classifier.",
                "Downstream conclusions still require database, structural, and wet-lab validation.",
            ],
        )

    async def _call_space(self, sequence: str) -> dict:
        """
        Calls the Space's /embed endpoint via gradio_client. gradio_client's
        Client.predict() is synchronous, so it runs in a worker thread via
        asyncio.to_thread to avoid blocking the FastAPI event loop.

        Signature verified live against the actual Space on 2026-09-16 via
        client.view_api():

            predict(sequence, api_name="/embed") -> esm2_embedding
            Parameters:
             - sequence: str (required)

        The Space exposes exactly one positional parameter (sequence) and has
        no separate `pooling` argument — pooling is hardcoded to "mean" inside
        the Space itself. Do not add a pooling kwarg here without re-checking
        view_api() again if the Space's interface changes.

        The Hugging Face token is passed only as the `token` constructor
        argument to gradio_client.Client (NOT `hf_token` — that keyword does
        not exist on this gradio_client version and raises TypeError). The
        token is never logged, never printed, and never included in any
        exception message raised from this method.
        """
        import asyncio

        def _predict() -> Any:
            from gradio_client import Client

            client = Client(self.space_id, token=self.hf_token, verbose=False)
            return client.predict(sequence, api_name=self.api_name)

        try:
            result = await asyncio.to_thread(_predict)
        except Exception as exc:
            # Re-raise as a plain RuntimeError with a message that cannot
            # possibly contain the token (self.hf_token is never interpolated
            # here), regardless of what the underlying gradio_client exception says.
            raise RuntimeError(f"Hugging Face Space call failed: {type(exc).__name__}: {exc}") from exc

        if isinstance(result, dict):
            return result
        raise HuggingFaceSpaceResponseError(
            f"Unexpected response type from Hugging Face Space '{self.space_id}': {type(result).__name__}"
        )

    def _validate_response_metadata(self, payload: dict, expected_sequence_sha256: str) -> None:
        """
        Defends against a misconfigured or mismatched Space silently producing
        an embedding that looks valid but was computed by the wrong model,
        pooling strategy, or for the wrong sequence.
        """
        required_keys = {"model", "pooling", "embedding_dimension", "sequence_sha256", "embedding"}
        missing = required_keys - payload.keys()
        if missing:
            raise HuggingFaceSpaceResponseError(
                f"Hugging Face Space response is missing required metadata: {sorted(missing)}"
            )
        if payload["model"] != self.model_id:
            raise HuggingFaceSpaceResponseError(
                f"Space returned model '{payload['model']}' but PLM_MODEL is configured as '{self.model_id}'."
            )
        if payload["pooling"] != self.pooling:
            raise HuggingFaceSpaceResponseError(
                f"Space returned pooling '{payload['pooling']}' but PLM_POOLING is configured as '{self.pooling}'."
            )
        if payload["sequence_sha256"] != expected_sequence_sha256:
            raise HuggingFaceSpaceResponseError(
                "Space response sequence_sha256 does not match the request; refusing to cache or "
                "return a result that may belong to a different sequence."
            )
        if payload["embedding_dimension"] != len(payload["embedding"]):
            raise HuggingFaceSpaceResponseError(
                f"Space reported embedding_dimension={payload['embedding_dimension']} but returned "
                f"{len(payload['embedding'])} values."
            )


class ProteinEmbeddingClient:
    """
    Resolves a sequence to an embedding using the configured provider, with an
    explicit, observable fallback path. This is the seam future providers
    (e.g. a different self-hosted PLM, another hosted inference API) plug
    into without changing any caller's code.

    Provider resolution order:
      1. PLM_PROVIDER="hf_space" -> HuggingFaceSpaceEmbeddingProvider
      2. PLM_PROVIDER="http"     -> RemotePLMProvider
      3. PLM_PROVIDER unset      -> legacy: PROTEIN_EMBEDDING_MODE=="esm2" and
                                     PLM_SERVICE_URL set -> RemotePLMProvider
      4. otherwise               -> BaselineEmbeddingProvider
    """

    def __init__(self, mode: Optional[str] = None, provider: Optional[str] = None):
        self.mode = (mode or settings.PROTEIN_EMBEDDING_MODE).lower()
        self.provider_name = (provider or settings.PLM_PROVIDER or "").lower() or None
        self.baseline = BaselineEmbeddingProvider()
        self._remote: Optional[RemotePLMProvider] = None
        self._hf_space: Optional[HuggingFaceSpaceEmbeddingProvider] = None

    def _get_remote(self) -> Optional[RemotePLMProvider]:
        if not settings.PLM_SERVICE_URL:
            return None
        if self._remote is None:
            self._remote = RemotePLMProvider(
                base_url=settings.PLM_SERVICE_URL,
                model_id=settings.PROTEIN_EMBEDDING_MODEL,
                max_residues=settings.PROTEIN_EMBEDDING_MAX_RESIDUES,
                pooling=settings.PLM_POOLING,
            )
        return self._remote

    def _get_hf_space(self) -> Optional[HuggingFaceSpaceEmbeddingProvider]:
        if not settings.HF_SPACE_ID:
            return None
        if self._hf_space is None:
            self._hf_space = HuggingFaceSpaceEmbeddingProvider(
                space_id=settings.HF_SPACE_ID,
                model_id=settings.PLM_MODEL,
                max_residues=settings.PLM_MAX_RESIDUES,
                pooling=settings.PLM_POOLING,
                hf_token=settings.HF_TOKEN,
            )
        return self._hf_space

    async def embed(self, sequence: str) -> EmbeddingResult:
        if self.provider_name == "hf_space":
            space = self._get_hf_space()
            if space is None:
                return self._fallback(sequence, "HF_SPACE_ID is not configured; no Hugging Face Space to call.")
            try:
                return await space.generate(sequence)
            except Exception as exc:
                return self._fallback(sequence, f"Hugging Face Space call failed: {type(exc).__name__}: {exc}")

        if self.provider_name == "http":
            remote = self._get_remote()
            if remote is None:
                return self._fallback(sequence, "PLM_SERVICE_URL is not configured; no PLM microservice to call.")
            try:
                return await remote.generate(sequence)
            except Exception as exc:
                return self._fallback(sequence, f"PLM microservice call failed: {type(exc).__name__}: {exc}")

        if self.provider_name is None and self.mode == "esm2":
            # Legacy path: PLM_PROVIDER was never set, but the older
            # PROTEIN_EMBEDDING_MODE=esm2 + PLM_SERVICE_URL combination is.
            remote = self._get_remote()
            if remote is None:
                return self._fallback(sequence, "PLM_SERVICE_URL is not configured; no PLM microservice to call.")
            try:
                return await remote.generate(sequence)
            except Exception as exc:
                return self._fallback(sequence, f"PLM microservice call failed: {type(exc).__name__}: {exc}")

        return self.baseline.generate(sequence)

    def _fallback(self, sequence: str, reason: str) -> EmbeddingResult:
        return self.baseline.generate(sequence).model_copy(
            update={"status": "fallback", "fallback_reason": reason}
        )


protein_embedding_client = ProteinEmbeddingClient()


class ProteinEmbeddingService:
    """
    Backward-compatible facade over ProteinEmbeddingClient.

    Kept because existing callers (enzymes.py, agent_orchestrator.py, and their
    tests) use the synchronous `generate_embedding(sequence)` method. Baseline
    mode is fully synchronous and returns immediately. esm2 mode requires the
    async `embed()` path on ProteinEmbeddingClient; callers that need esm2 must
    migrate to `await protein_embedding_client.embed(sequence)` (done for
    enzymes.py and agent_orchestrator.py in this milestone). Calling
    generate_embedding() directly in esm2 mode still works for backward
    compatibility, but runs the remote call synchronously via asyncio and is not
    the preferred path for new code.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or settings.PROTEIN_EMBEDDING_MODE).lower()
        self._client = ProteinEmbeddingClient(mode=self.mode)

    def generate_embedding(self, sequence: str) -> EmbeddingResult:
        if self.mode != "esm2":
            return self._client.baseline.generate(sequence)
        import asyncio

        try:
            return asyncio.run(self._client.embed(sequence))
        except RuntimeError:
            # Already inside an event loop (e.g. called from async test code) —
            # this synchronous facade cannot nest event loops. Fall back to
            # baseline rather than deadlocking, and say so explicitly.
            return self._client.baseline.generate(sequence).model_copy(
                update={
                    "status": "fallback",
                    "fallback_reason": (
                        "generate_embedding() was called from within a running event loop; "
                        "use 'await protein_embedding_client.embed(sequence)' instead."
                    ),
                }
            )


protein_embedding_service = ProteinEmbeddingService()
