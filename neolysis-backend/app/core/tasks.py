"""
Neolysis Background Tasks
=========================
Celery task definitions. These tasks are reserved for future async operations.

Planned:
  - compute_docking_score: Run AutoDock Vina in the background for a given target/compound pair
  - fetch_pubchem_data: Asynchronously enrich compound metadata from PubChem
  - upload_pdb_to_r2: Upload a PDB file to Cloudflare R2 and return the public URL
"""
from app.core.worker import celery_app
from loguru import logger


@celery_app.task(name="tasks.health_check")
def health_check():
    """Simple health check task to verify the worker is running."""
    logger.info("Celery worker health check: OK")
    return {"status": "ok"}


@celery_app.task(name="tasks.compute_docking_score", bind=True, max_retries=2)
def compute_docking_score(self, target_id: int, compound_id: int):
    """
    [RESERVED] Compute an AutoDock Vina docking score for a target-compound pair.
    Will write the result to the docking_results table upon completion.
    
    Currently a placeholder — implement when AutoDock Vina is integrated.
    """
    logger.info(f"[PLACEHOLDER] Docking task queued: target={target_id}, compound={compound_id}")
    raise NotImplementedError(
        "Live docking not yet implemented. Use precomputed scores from docking_results table."
    )


@celery_app.task(name="tasks.upload_pdb_to_r2")
def upload_pdb_to_r2(target_id: int, pdb_content: str):
    """
    [RESERVED] Upload a PDB file to Cloudflare R2 and update the target's pdb_url.
    """
    logger.info(f"[PLACEHOLDER] R2 upload task queued: target={target_id}")
    raise NotImplementedError("R2 upload not yet implemented.")
