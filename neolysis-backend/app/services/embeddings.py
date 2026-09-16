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
                ├── BaselineEmbeddingProvider   (in-process, always available)
                └── RemotePLMProvider           (HTTP call to services/plm-inference)
                        └── Redis cache (best-effort; disabled if unreachable)

A large protein language model is NEVER loaded inside this process. When
PROTEIN_EMBEDDING_MODE=esm2, embeddings are requested from the dedicated PLM
microservice over HTTP. If that service is unset, unreachable, times out, or
returns an error, this client falls back to the deterministic baseline
embedding and marks the result status="fallback" with an explicit
fallback_reason — it never silently pretends to be a pretrained embedding.

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

    @staticmethod
    async def _write_cache(cache_key: str, vector: list[float]) -> None:
        try:
            await cache.ensure_connected()
            await cache.set(cache_key, json.dumps(vector), ttl=60 * 60 * 24 * 30)
        except Exception as exc:
            # Caching is strictly best-effort. A cache outage must never break
            # embedding generation or make the request appear to fail.
            logger.warning(f"Embedding cache write skipped ({type(exc).__name__}: {exc})")


class ProteinEmbeddingClient:
    """
    Resolves a sequence to an embedding using the configured mode, with an
    explicit, observable fallback path. This is the seam future providers
    (e.g. a different self-hosted PLM, a hosted inference API) plug into
    without changing any caller's code.
    """

    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or settings.PROTEIN_EMBEDDING_MODE).lower()
        self.baseline = BaselineEmbeddingProvider()
        self._remote: Optional[RemotePLMProvider] = None

    def _get_remote(self) -> Optional[RemotePLMProvider]:
        if self.mode != "esm2":
            return None
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

    async def embed(self, sequence: str) -> EmbeddingResult:
        if self.mode == "esm2":
            remote = self._get_remote()
            if remote is None:
                return self.baseline.generate(
                    sequence
                ).model_copy(
                    update={
                        "status": "fallback",
                        "fallback_reason": "PLM_SERVICE_URL is not configured; no PLM microservice to call.",
                    }
                )
            try:
                return await remote.generate(sequence)
            except Exception as exc:
                return self.baseline.generate(sequence).model_copy(
                    update={
                        "status": "fallback",
                        "fallback_reason": f"PLM microservice call failed: {type(exc).__name__}: {exc}",
                    }
                )
        return self.baseline.generate(sequence)


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
