"""
Neolysis — NVIDIA NIM Provider Errors
========================================
Structured, provider-specific error types so callers can distinguish rate
limiting from a hard failure without parsing strings.
"""
from typing import Optional


class ProviderError(Exception):
    """Base class for all NVIDIA NIM provider failures."""

    def __init__(self, message: str, *, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProviderRateLimited(ProviderError):
    def __init__(self, message: str, *, retry_after_seconds: Optional[float] = None):
        super().__init__(message, status_code=429)
        self.retry_after_seconds = retry_after_seconds


class ProviderTimeout(ProviderError):
    pass


class ProviderUnavailable(ProviderError):
    """Non-2xx, non-429 response, or the provider could not be reached at all."""
