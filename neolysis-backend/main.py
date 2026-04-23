from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.core.cache import cache
from app.core.middleware import setup_middlewares
from app.api.v1 import targets, compounds, docking, narrative, health, auth, projects, papers, docking_csv
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting up Neolysis API...")
    await cache.connect()
    yield
    # Shutdown logic
    logger.info("Shutting down Neolysis API...")
    await cache.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Setup Middlewares
setup_middlewares(app)

# API Routes
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(targets.router, prefix=f"{settings.API_V1_STR}/targets", tags=["targets"])
app.include_router(compounds.router, prefix=f"{settings.API_V1_STR}/compounds", tags=["compounds"])
app.include_router(docking.router, prefix=f"{settings.API_V1_STR}/docking", tags=["docking"])
app.include_router(docking_csv.router, prefix=f"{settings.API_V1_STR}/docking-csv", tags=["docking-csv"])
app.include_router(narrative.router, prefix=f"{settings.API_V1_STR}/narrative", tags=["narrative"])
app.include_router(papers.router, prefix=f"{settings.API_V1_STR}/papers", tags=["papers"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
