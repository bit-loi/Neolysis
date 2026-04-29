"""
Neolysis — Health Check Router (Enhanced)
==========================================
Extended health check reporting DB + Qdrant status and platform-level stats.

Endpoints:
    GET /api/v1/health/     — Liveness probe (simple)
    GET /api/v1/health/full — Detailed status: DB, Qdrant, record counts
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.db.session import get_db
from app.models.compound import Compound
from app.models.target import Target
from app.models.knowledge_graph import KnowledgeGraph

router = APIRouter()


@router.get("/", summary="Liveness probe")
async def health_check():
    """Simple liveness probe — returns immediately without DB access."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Neolysis API",
    }


@router.get("/full", summary="Full health check with subsystem status")
async def full_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Comprehensive health check that tests:
    - PostgreSQL (Supabase) connectivity
    - Qdrant vector store connectivity
    - Record counts for key tables

    Returns overall status + per-subsystem breakdown.
    """
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Neolysis API",
        "overall": "healthy",
        "subsystems": {},
    }

    # ── PostgreSQL ──────────────────────────────────────────────────────────
    try:
        compound_count = (await db.execute(select(func.count()).select_from(Compound))).scalar()
        target_count = (await db.execute(select(func.count()).select_from(Target))).scalar()
        kg_count = (await db.execute(select(func.count()).select_from(KnowledgeGraph))).scalar()

        report["subsystems"]["postgresql"] = {
            "status": "healthy",
            "compounds": compound_count,
            "targets": target_count,
            "knowledge_graph_triples": kg_count,
        }
    except Exception as e:
        logger.error(f"Health check: DB error: {e}")
        report["subsystems"]["postgresql"] = {"status": "unhealthy", "error": "DB unavailable"}
        report["overall"] = "degraded"

    # ── Qdrant ──────────────────────────────────────────────────────────────
    try:
        from app.services.rag_service import rag_service
        qdrant_healthy = await rag_service.health_check()
        report["subsystems"]["qdrant"] = {
            "status": "healthy" if qdrant_healthy else "unhealthy",
            "collection": "pubmed_ntd",
        }
        if not qdrant_healthy:
            report["overall"] = "degraded"
    except Exception as e:
        logger.error(f"Health check: Qdrant error: {e}")
        report["subsystems"]["qdrant"] = {"status": "unhealthy", "error": "Qdrant unavailable"}
        report["overall"] = "degraded"

    return report
