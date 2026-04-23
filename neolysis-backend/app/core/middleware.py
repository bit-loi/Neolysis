from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.core.rate_limit import limiter

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

def setup_middlewares(app):
    """Register all middlewares to the FastAPI app in the correct order."""
    # Rate Limiter exceptions
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Reverse proxy support
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
