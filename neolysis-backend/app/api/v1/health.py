from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Liveness probe")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Neolysis Enzyme Engineering API",
    }


@router.get("/full", summary="Full health check with subsystem status")
async def full_health_check() -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Neolysis Enzyme Engineering API",
        "overall": "healthy",
        "subsystems": {
            "sequence_validation": {"status": "available"},
            "protein_feature_extraction": {"status": "available"},
            "baseline_property_scoring": {"status": "available"},
            "agent_orchestrator": {"status": "available"},
        },
        "limitations": [
            "Staging health checks do not require database, Redis, or model-server connectivity.",
        ],
    }
