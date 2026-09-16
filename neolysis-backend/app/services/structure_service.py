"""
Neolysis — NVIDIA Structure Service
=======================================
Coordinates structure prediction jobs (AlphaFold2, AlphaFold2 Multimer,
OpenFold3, Boltz-2), standalone MSA search (ColabFold), and ProteinMPNN
backbone-conditioned sequence design.

Job orchestration
------------------
Brief-recommended architecture uses the existing Celery infrastructure for
background jobs. That is NOT done here: `app/core/worker.py` references
`app.core.tasks`, a module that does not exist in this repository (confirmed
during discovery), so Celery is currently broken, and fixing it was explicitly
out of scope for this milestone. Jobs are instead tracked in an in-memory
store and executed via `asyncio.create_task`, mirroring the existing
`project_workflow.py` pattern (already in-memory, not persisted to Postgres).
This is a deliberate, documented compromise — not a silent shortcut — and
should be revisited when Celery is fixed and/or project persistence is
hardened (both tracked separately per the agreed milestone order).

Caching
-------
Structure cache key includes provider + model + parameter_hash + sequence
hashes, NOT just the sequence hash, because different models/parameters can
legitimately produce different structures:

    structure:{provider}:{model}:{parameter_hash}:{sequence_sha256_joined}

MSA cache key includes sequence hash + database selection + search params.

Both caches are best-effort via the existing Redis `Cache` singleton and are
safe no-ops if Redis is unreachable (same pattern as the M2 embedding cache).

Storage
-------
The brief recommends storing large PDB/mmCIF artifacts in durable object/file
storage, with PostgreSQL holding only metadata/references. No object storage
integration exists in this repository yet, and adding one is out of scope for
this milestone. `StructureResult.artifact_text` therefore holds the structure
text directly (same pattern PDB text already uses elsewhere in this codebase,
e.g. project_workflow's raw_pdb_text) — flagged here as a limitation to
revisit, not a hidden design decision.

Model selection strategy
-------------------------
This service does NOT call every model for every request:
    - protein monomer            -> requested model (openfold3 or alphafold2)
    - known protein complex      -> alphafold2_multimer or openfold3
    - protein-ligand hypothesis  -> boltz2 (never run by default; caller opts in)
    - standalone MSA             -> ColabFold MSA Search only

Failure handling
-----------------
No automatic fallback to a different scientific model. If the requested model
cannot run (e.g. NVIDIA_API_KEY not configured), the job fails with an
explicit error_code/error_message rather than silently substituting another
model and presenting the result as equivalent.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from loguru import logger

from app.config import settings
from app.core.cache import cache
from app.schemas.structure import (
    MsaSearchRequest,
    MsaSearchResult,
    ProteinMpnnDesign,
    ProteinMpnnRequest,
    ProteinMpnnResult,
    StructureJobRecord,
    StructureJobRequest,
    StructureResult,
)
from app.services.nvidia.client import NvidiaNimClient
from app.services.nvidia.errors import ProviderError
from app.services.nvidia.providers import (
    NvidiaAlphaFold2MultimerProvider,
    NvidiaAlphaFold2Provider,
    NvidiaBoltz2Provider,
    NvidiaColabFoldMsaProvider,
    NvidiaOpenFold3Provider,
    NvidiaProteinMpnnProvider,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parameter_hash(**params) -> str:
    canonical = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class NvidiaNotConfiguredError(ProviderError):
    pass


class StructureService:
    def __init__(self):
        self._jobs: Dict[str, StructureJobRecord] = {}
        self._results: Dict[str, StructureResult] = {}
        self._client: Optional[NvidiaNimClient] = None

    # ── Client construction ────────────────────────────────────────────────

    def _require_client(self) -> NvidiaNimClient:
        if not settings.NVIDIA_API_KEY or not settings.NVIDIA_HEALTH_API_BASE_URL:
            raise NvidiaNotConfiguredError(
                "NVIDIA_API_KEY and NVIDIA_HEALTH_API_BASE_URL must both be configured "
                "to run structure prediction, MSA search, or ProteinMPNN. Neither is set "
                "in this environment."
            )
        if self._client is None:
            self._client = NvidiaNimClient(
                base_url=settings.NVIDIA_HEALTH_API_BASE_URL,
                api_key=settings.NVIDIA_API_KEY,
                timeout_seconds=settings.NVIDIA_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.NVIDIA_MAX_RETRIES,
            )
        return self._client

    # ── Structure prediction jobs ──────────────────────────────────────────

    def submit_job(self, request: StructureJobRequest) -> StructureJobRecord:
        job_id = str(uuid4())
        sequence_hashes = [_sha256(seq.upper()) for seq in request.sequences]
        parameter_hash = _parameter_hash(
            algorithm=request.algorithm,
            relax_prediction=request.relax_prediction,
            predict_affinity=request.predict_affinity,
            ligand_ids=[ligand.id for ligand in request.ligands],
        )
        cache_key = f"structure:nvidia:{request.model}:{parameter_hash}:{':'.join(sequence_hashes)}"

        record = StructureJobRecord(
            job_id=job_id,
            model=request.model,
            status="queued",
            parameter_hash=parameter_hash,
            sequence_sha256=sequence_hashes,
            cache_key=cache_key,
            created_at=_utc_now_iso(),
        )
        self._jobs[job_id] = record

        # Fire-and-track via asyncio, not Celery (see module docstring). This
        # keeps job state observable through get_job() without blocking the
        # request that submitted it.
        asyncio.create_task(self._run_job(job_id, request))
        return record

    def get_job(self, job_id: str) -> StructureJobRecord:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]

    def get_result(self, job_id: str) -> Optional[StructureResult]:
        return self._results.get(job_id)

    async def _run_job(self, job_id: str, request: StructureJobRequest) -> None:
        record = self._jobs[job_id]
        record.status = "running"
        record.started_at = _utc_now_iso()

        cached = await self._read_structure_cache(record.cache_key)
        if cached is not None:
            self._results[job_id] = cached
            record.status = "completed"
            record.completed_at = _utc_now_iso()
            return

        try:
            client = self._require_client()
            provider = self._select_provider(request.model, client)
            raw_response = await provider.predict(
                request.sequences,
                algorithm=request.algorithm,
                relax_prediction=request.relax_prediction,
                ligands=[ligand.model_dump() for ligand in request.ligands] or None,
            )
        except NotImplementedError as exc:
            record.status = "failed"
            record.error_code = "not_implemented"
            record.error_message = str(exc)
            record.completed_at = _utc_now_iso()
            return
        except ProviderError as exc:
            record.status = "failed"
            record.error_code = type(exc).__name__
            record.error_message = exc.message
            record.completed_at = _utc_now_iso()
            logger.warning(f"structure job {job_id} failed: {exc.message}")
            return
        except Exception as exc:  # pragma: no cover - defensive catch-all
            record.status = "failed"
            record.error_code = "unexpected_error"
            record.error_message = f"{type(exc).__name__}: {exc}"
            record.completed_at = _utc_now_iso()
            logger.error(f"structure job {job_id} raised unexpectedly: {exc}")
            return

        result = StructureResult(
            structure_id=str(uuid4()),
            model=request.model,
            artifact_text=self._extract_artifact_text(raw_response),
            confidence_summary=self._extract_confidence_summary(raw_response),
            raw_provider_response_keys=list(raw_response.keys()),
        )
        self._results[job_id] = result
        await self._write_structure_cache(record.cache_key, result)
        record.status = "completed"
        record.completed_at = _utc_now_iso()

    def _select_provider(self, model: str, client: NvidiaNimClient):
        if model == "alphafold2":
            return NvidiaAlphaFold2Provider(client)
        if model == "alphafold2_multimer":
            return NvidiaAlphaFold2MultimerProvider(client)
        if model == "openfold3":
            return NvidiaOpenFold3Provider(client)
        if model == "boltz2":
            return NvidiaBoltz2Provider(client)
        raise ValueError(f"Unsupported structure model '{model}'.")

    @staticmethod
    def _extract_artifact_text(raw_response: dict) -> Optional[str]:
        for key in ("pdb", "structure", "output_pdb", "mmcif"):
            value = raw_response.get(key)
            if isinstance(value, str):
                return value
        return None

    @staticmethod
    def _extract_confidence_summary(raw_response: dict) -> Optional[dict]:
        for key in ("confidence", "plddt", "metrics"):
            value = raw_response.get(key)
            if value is not None:
                return {key: value}
        return None

    async def _read_structure_cache(self, cache_key: str) -> Optional[StructureResult]:
        try:
            await cache.ensure_connected()
            cached = await cache.get(cache_key)
        except Exception as exc:
            logger.warning(f"Structure cache read skipped ({type(exc).__name__}: {exc})")
            return None
        if not cached:
            return None
        try:
            return StructureResult.model_validate_json(cached) if isinstance(cached, str) else StructureResult.model_validate(cached)
        except Exception:
            return None

    async def _write_structure_cache(self, cache_key: str, result: StructureResult) -> None:
        try:
            await cache.ensure_connected()
            await cache.set(cache_key, result.model_dump_json(), ttl=60 * 60 * 24 * 30)
        except Exception as exc:
            logger.warning(f"Structure cache write skipped ({type(exc).__name__}: {exc})")

    # ── Standalone MSA search (ColabFold) ──────────────────────────────────

    async def search_msa(self, request: MsaSearchRequest) -> MsaSearchResult:
        sequence_hash = _sha256(request.sequence.upper())
        param_hash = _parameter_hash(
            databases=sorted(request.databases), formats=sorted(request.output_alignment_formats)
        )
        cache_key = f"msa:colabfold:{param_hash}:{sequence_hash}"

        cached = await self._read_generic_cache(cache_key)
        if cached is not None:
            return MsaSearchResult(
                sequence_sha256=sequence_hash,
                databases=request.databases,
                cache_key=cache_key,
                cache_hit=True,
                alignment_formats=request.output_alignment_formats,
                raw_provider_response_keys=cached.get("keys", []),
            )

        client = self._require_client()
        provider = NvidiaColabFoldMsaProvider(client)
        raw_response = await provider.search(
            request.sequence, request.databases, request.output_alignment_formats
        )
        await self._write_generic_cache(cache_key, {"keys": list(raw_response.keys())})

        return MsaSearchResult(
            sequence_sha256=sequence_hash,
            databases=request.databases,
            cache_key=cache_key,
            cache_hit=False,
            alignment_formats=request.output_alignment_formats,
            raw_provider_response_keys=list(raw_response.keys()),
        )

    # ── ProteinMPNN ─────────────────────────────────────────────────────────

    async def design_with_proteinmpnn(self, request: ProteinMpnnRequest) -> ProteinMpnnResult:
        structure_hash = _sha256(request.input_pdb)
        param_hash = _parameter_hash(
            ca_only=request.ca_only,
            use_soluble_model=request.use_soluble_model,
            num_seq_per_target=request.num_seq_per_target,
            sampling_temp=request.sampling_temp,
        )
        cache_key = f"proteinmpnn:{param_hash}:{structure_hash}"

        cached = await self._read_generic_cache(cache_key)
        if cached is not None:
            return ProteinMpnnResult(
                designs=[ProteinMpnnDesign(**design) for design in cached.get("designs", [])],
                cache_key=cache_key,
                cache_hit=True,
            )

        client = self._require_client()
        provider = NvidiaProteinMpnnProvider(client)
        raw_response = await provider.design(
            request.input_pdb,
            request.ca_only,
            request.use_soluble_model,
            request.num_seq_per_target,
            request.sampling_temp,
        )

        designs = self._parse_proteinmpnn_designs(raw_response)
        await self._write_generic_cache(cache_key, {"designs": [d.model_dump() for d in designs]})

        return ProteinMpnnResult(designs=designs, cache_key=cache_key, cache_hit=False)

    @staticmethod
    def _parse_proteinmpnn_designs(raw_response: dict) -> list[ProteinMpnnDesign]:
        raw_designs = raw_response.get("sequences") or raw_response.get("designs") or []
        designs = []
        for item in raw_designs:
            if isinstance(item, str):
                designs.append(ProteinMpnnDesign(sequence=item))
            elif isinstance(item, dict):
                designs.append(
                    ProteinMpnnDesign(
                        sequence=item.get("sequence", ""),
                        # Deliberately read a compatibility/score field, never a "ddg" field.
                        backbone_sequence_compatibility=item.get("score") or item.get("compatibility"),
                    )
                )
        return designs

    async def _read_generic_cache(self, cache_key: str) -> Optional[dict]:
        try:
            await cache.ensure_connected()
            cached = await cache.get(cache_key)
        except Exception as exc:
            logger.warning(f"Cache read skipped for {cache_key} ({type(exc).__name__}: {exc})")
            return None
        if not cached:
            return None
        try:
            return json.loads(cached) if isinstance(cached, str) else cached
        except (TypeError, ValueError):
            return None

    async def _write_generic_cache(self, cache_key: str, value: dict) -> None:
        try:
            await cache.ensure_connected()
            await cache.set(cache_key, json.dumps(value), ttl=60 * 60 * 24 * 7)
        except Exception as exc:
            logger.warning(f"Cache write skipped for {cache_key} ({type(exc).__name__}: {exc})")


structure_service = StructureService()
