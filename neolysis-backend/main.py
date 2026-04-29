"""
Neolysis — FastAPI Application Entry Point
==========================================
Production-ready FastAPI app with:
  - Async lifespan (startup/shutdown) for DB + Qdrant + keepalive
  - CORS middleware (permissive for dev; tighten in prod)
  - Security headers (X-Frame-Options, HSTS, etc.)
  - Rate limiting via slowapi
  - All API routers registered under /api/v1
  - Structured logging via loguru

Run with:
    uvicorn main:app --reload --port 8000

Or from this file:
    python main.py
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from loguru import logger

from app.config import settings
from app.core.cache import cache
from app.core.middleware import setup_middlewares
from app.db.session import AsyncSessionLocal, start_keepalive, stop_keepalive

# ── Routers ────────────────────────────────────────────────────────────────
from app.api.v1 import (
    targets,
    compounds,
    docking,
    narrative,
    health,
    auth,
    projects,
    papers,
    docking_csv,
    diseases,
    proteins,
    admet,
    insight,
    knowledge_graph,
)


# ── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
      - Connect to Redis cache
      - Test PostgreSQL connectivity
      - Start DB keepalive background task
      - Test Qdrant connectivity (non-fatal if offline)

    Shutdown:
      - Stop keepalive task
      - Close Redis connection
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("=" * 60)

    # ── Redis ──────────────────────────────────────────────────────────────
    await cache.connect()

    # ── PostgreSQL ─────────────────────────────────────────────────────────
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✓ PostgreSQL connection: OK")
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection FAILED: {e}")
        logger.warning("API will start but DB-dependent endpoints will fail.")

    # ── DB Keepalive ───────────────────────────────────────────────────────
    start_keepalive()

    # ── Qdrant ─────────────────────────────────────────────────────────────
    try:
        from app.services.rag_service import rag_service
        await rag_service.ensure_collection()
        qdrant_ok = await rag_service.health_check()
        if qdrant_ok:
            logger.info(f"✓ Qdrant connection: OK ({settings.QDRANT_HOST}:{settings.QDRANT_PORT})")
        else:
            logger.warning("⚠ Qdrant connection: OFFLINE — RAG/Insight endpoints will degrade gracefully")
    except Exception as e:
        logger.warning(f"⚠ Qdrant startup check skipped: {e}")

    logger.info(f"✓ {settings.PROJECT_NAME} ready — API prefix: {settings.API_V1_STR}")
    logger.info("=" * 60)

    yield  # ── Application runs here ──────────────────────────────────────

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("Shutting down Neolysis API...")
    stop_keepalive()
    await cache.close()
    logger.info("Shutdown complete.")


# ── App Factory ────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Neolysis — Open-source AI drug discovery platform for ASEAN Neglected Tropical Diseases.\n\n"
        "Targets: Dengue, Leptospirosis, Melioidosis, Scrub Typhus.\n\n"
        "Pipeline: RDKit → ADMET (TDC) → Docking (AutoDock Vina) → RAG (Qdrant) → Insight (Gemma 4)"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middlewares (CORS, security headers, rate limiter, proxy headers)
setup_middlewares(app)

# ── Route Registration ─────────────────────────────────────────────────────
PREFIX = settings.API_V1_STR

# Core research endpoints
app.include_router(diseases.router,        prefix=f"{PREFIX}/diseases",        tags=["Diseases"])
app.include_router(proteins.router,        prefix=f"{PREFIX}/proteins",         tags=["Proteins"])
app.include_router(compounds.router,       prefix=f"{PREFIX}/compounds",        tags=["Compounds"])
app.include_router(docking.router,         prefix=f"{PREFIX}/docking",          tags=["Docking"])
app.include_router(docking_csv.router,     prefix=f"{PREFIX}/docking-csv",      tags=["Docking CSV"])
app.include_router(targets.router,         prefix=f"{PREFIX}/targets",          tags=["Targets"])

# AI pipeline endpoints
app.include_router(admet.router,           prefix=f"{PREFIX}/admet",            tags=["ADMET"])
app.include_router(insight.router,         prefix=f"{PREFIX}/insight",          tags=["Insight"])
app.include_router(knowledge_graph.router, prefix=f"{PREFIX}/knowledge-graph",  tags=["Knowledge Graph"])
app.include_router(narrative.router,       prefix=f"{PREFIX}/narrative",        tags=["Narrative"])

# Literature
app.include_router(papers.router,          prefix=f"{PREFIX}/papers",           tags=["Papers"])

# User & project management
app.include_router(auth.router,            prefix=f"{PREFIX}/auth",             tags=["Auth"])
app.include_router(projects.router,        prefix=f"{PREFIX}/projects",         tags=["Projects"])

# Health
app.include_router(health.router,          prefix=f"{PREFIX}/health",           tags=["Health"])


# ── Root ───────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{PREFIX}/health/full",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
