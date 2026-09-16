from fastapi import FastAPI

from app.config import settings
from app.core.middleware import setup_middlewares
from app.api.v1 import agents, docking, enzymes, health, projects, properties, reports, sequences, structures, variants


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Neolysis is a computational enzyme intelligence API for industrial biotechnology. "
        "It validates protein sequences, extracts protein features, estimates industrial "
        "property fit, ranks variants with baseline scaffolds, and generates wet-lab "
        "validation planning reports. Outputs are computational estimates and require "
        "experimental validation."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

setup_middlewares(app)

PREFIX = settings.API_V1_STR

app.include_router(health.router, prefix=f"{PREFIX}/health", tags=["Health"])
app.include_router(sequences.router, prefix=f"{PREFIX}/sequences", tags=["Sequences"])
app.include_router(enzymes.router, prefix=f"{PREFIX}/enzymes", tags=["Enzymes"])
app.include_router(properties.router, prefix=f"{PREFIX}/properties", tags=["Properties"])
app.include_router(variants.router, prefix=f"{PREFIX}/variants", tags=["Variants"])
app.include_router(reports.router, prefix=f"{PREFIX}/reports", tags=["Reports"])
app.include_router(agents.router, prefix=f"{PREFIX}/agents", tags=["Agentic Analysis"])
app.include_router(projects.router, prefix=f"{PREFIX}/projects", tags=["Structure-Aware Projects"])
app.include_router(docking.router, prefix=f"{PREFIX}/docking", tags=["Molecular Docking"])
app.include_router(structures.router, prefix=f"{PREFIX}/structures", tags=["NVIDIA NIM Structure Prediction"])


@app.get("/health", include_in_schema=False)
async def root_health():
    return await health.health_check()


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_prefix": PREFIX,
        "positioning": "computational enzyme candidate prioritization for industrial biotechnology",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
