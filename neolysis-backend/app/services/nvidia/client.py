"""
Neolysis — NVIDIA NIM HTTP Client
====================================
One reusable, auditable client for all NVIDIA Healthcare NIM calls (AlphaFold2,
AlphaFold2 Multimer, OpenFold3, Boltz-2, ColabFold MSA Search, ProteinMPNN).

Security:
    - NVIDIA_API_KEY is read only from settings (never logged, never returned
      to the frontend).
    - Bearer authentication only.
    - Every call is explicit and auditable (structured logging includes
      provider/model/path/latency/status, never the Authorization header or
      raw protein sequence — only its sha256 prefix and length).

Failure handling:
    - Configurable timeout (NVIDIA_REQUEST_TIMEOUT_SECONDS; structure inference
      can legitimately take minutes).
    - HTTP 429 raises ProviderRateLimited, honoring a numeric Retry-After header
      when the provider supplies one.
    - Bounded exponential backoff retries on 429 and transient network/timeout
      errors only. Never retries indefinitely, and never retries a 4xx that
      indicates a bad request (e.g. 400/404/422).
    - No automatic fallback to a different scientific model. If a caller
      chooses to fall back, it must record requested_model / actual_model /
      fallback_reason itself (see StructureService).
"""
import asyncio
import hashlib
import time
from typing import Any, Optional

import httpx
from loguru import logger

from app.services.nvidia.errors import ProviderRateLimited, ProviderTimeout, ProviderUnavailable


class NvidiaNimClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 900.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 2.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds

    async def post(self, path: str, payload: dict, *, provider_label: str, model_label: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        # Never log the raw payload (it may contain a proprietary customer sequence).
        # Log only a hash prefix/length so provider calls remain auditable without
        # exposing customer IP.
        sequence_fingerprint = self._fingerprint_payload(payload)

        attempt = 0
        while True:
            attempt += 1
            start = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout_seconds)) as client:
                    response = await client.post(f"{self.base_url}{path}", headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
                logger.warning(
                    f"nvidia_nim provider={provider_label} model={model_label} path={path} "
                    f"attempt={attempt} status=timeout latency_ms={elapsed_ms} input={sequence_fingerprint}"
                )
                if attempt > self.max_retries:
                    raise ProviderTimeout(f"NVIDIA NIM request to {path} timed out after {attempt} attempts.") from exc
                await self._sleep_backoff(attempt)
                continue
            except httpx.HTTPError as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
                logger.warning(
                    f"nvidia_nim provider={provider_label} model={model_label} path={path} "
                    f"attempt={attempt} status=network_error latency_ms={elapsed_ms} input={sequence_fingerprint}"
                )
                if attempt > self.max_retries:
                    raise ProviderUnavailable(f"NVIDIA NIM request to {path} failed: {exc}") from exc
                await self._sleep_backoff(attempt)
                continue

            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info(
                f"nvidia_nim provider={provider_label} model={model_label} path={path} "
                f"attempt={attempt} status={response.status_code} latency_ms={elapsed_ms} input={sequence_fingerprint}"
            )

            if response.status_code == 429:
                retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
                if attempt > self.max_retries:
                    raise ProviderRateLimited(
                        f"NVIDIA NIM rate-limited {path} after {attempt} attempts.",
                        retry_after_seconds=retry_after,
                    )
                await self._sleep_backoff(attempt, retry_after_override=retry_after)
                continue

            if response.status_code >= 500:
                if attempt > self.max_retries:
                    raise ProviderUnavailable(
                        f"NVIDIA NIM returned {response.status_code} for {path} after {attempt} attempts."
                    )
                await self._sleep_backoff(attempt)
                continue

            if response.status_code >= 400:
                # Client errors (400/404/422/...) are not retried — retrying a
                # malformed request will not succeed and would just waste quota.
                raise ProviderUnavailable(
                    f"NVIDIA NIM returned {response.status_code} for {path}: {response.text[:500]}"
                )

            return response.json()

    async def _sleep_backoff(self, attempt: int, retry_after_override: Optional[float] = None) -> None:
        if retry_after_override is not None:
            delay = retry_after_override
        else:
            delay = self.base_backoff_seconds * (2 ** (attempt - 1))
        await asyncio.sleep(delay)

    @staticmethod
    def _parse_retry_after(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _fingerprint_payload(payload: dict) -> str:
        sequence = payload.get("sequence") or ""
        if not sequence and payload.get("sequences"):
            sequence = "".join(payload["sequences"])
        if not sequence and payload.get("polymers"):
            sequence = "".join(p.get("sequence", "") for p in payload["polymers"])
        digest = hashlib.sha256(sequence.encode("utf-8")).hexdigest()[:12] if sequence else "n/a"
        return f"sha256:{digest} len:{len(sequence)}"
