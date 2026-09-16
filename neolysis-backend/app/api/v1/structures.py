from fastapi import APIRouter, HTTPException, status

from app.schemas.structure import (
    MsaSearchRequest,
    MsaSearchResult,
    ProteinMpnnRequest,
    ProteinMpnnResult,
    StructureJobRecord,
    StructureJobRequest,
    StructureJobStatusResponse,
)
from app.services.nvidia.errors import ProviderError
from app.services.structure_service import NvidiaNotConfiguredError, structure_service

router = APIRouter()


@router.post("/jobs", response_model=StructureJobRecord, status_code=status.HTTP_202_ACCEPTED)
async def submit_structure_job(payload: StructureJobRequest) -> StructureJobRecord:
    if payload.model == "alphafold2_multimer" and len(payload.sequences) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="alphafold2_multimer requires 2 or more chain sequences.",
        )
    if payload.model in {"alphafold2", "openfold3"} and payload.ligands:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ligands are only supported with model=boltz2.",
        )
    return structure_service.submit_job(payload)


@router.get("/jobs/{job_id}", response_model=StructureJobStatusResponse)
async def get_structure_job(job_id: str) -> StructureJobStatusResponse:
    try:
        job = structure_service.get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Structure job {job_id} not found.")
    result = structure_service.get_result(job_id) if job.status == "completed" else None
    return StructureJobStatusResponse(job=job, result=result)


@router.post("/msa-search", response_model=MsaSearchResult)
async def search_msa(payload: MsaSearchRequest) -> MsaSearchResult:
    try:
        return await structure_service.search_msa(payload)
    except NvidiaNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message)


@router.post("/proteinmpnn", response_model=ProteinMpnnResult)
async def design_with_proteinmpnn(payload: ProteinMpnnRequest) -> ProteinMpnnResult:
    try:
        return await structure_service.design_with_proteinmpnn(payload)
    except NvidiaNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message)
