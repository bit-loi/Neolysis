from fastapi import APIRouter

from app.schemas.project_workflow import (
    ActiveSiteRecord,
    ActiveSiteRequest,
    AnalysisReportRecord,
    DockingJobRecord,
    DockingJobRequest,
    EnzymeSequenceRecord,
    EnzymeSequenceRequest,
    EnzymeStructureRecord,
    EnzymeStructureRequest,
    EnzymeVariantRecord,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectRecord,
    SubstrateRecord,
    SubstrateRequest,
    VariantGenerateRequest,
)
from app.schemas.docking import DockingJobCreate, DockingJobWithResult
from app.services.docking import docking_service
from app.services.project_workflow import project_workflow_service

router = APIRouter()


@router.post("", response_model=ProjectRecord)
async def create_project(payload: ProjectCreateRequest) -> ProjectRecord:
    return project_workflow_service.create_project(payload)


@router.get("", response_model=list[ProjectRecord])
async def list_projects() -> list[ProjectRecord]:
    return project_workflow_service.list_projects()


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str) -> ProjectDetailResponse:
    return project_workflow_service.get_detail(project_id)


@router.post("/{project_id}/sequence", response_model=EnzymeSequenceRecord)
async def set_project_sequence(project_id: str, payload: EnzymeSequenceRequest) -> EnzymeSequenceRecord:
    return project_workflow_service.set_sequence(project_id, payload)


@router.post("/{project_id}/structure", response_model=EnzymeStructureRecord)
async def set_project_structure(project_id: str, payload: EnzymeStructureRequest) -> EnzymeStructureRecord:
    return project_workflow_service.set_structure(project_id, payload)


@router.get("/{project_id}/structure", response_model=list[EnzymeStructureRecord])
async def list_project_structures(project_id: str) -> list[EnzymeStructureRecord]:
    return project_workflow_service.get_detail(project_id).structures


@router.post("/{project_id}/substrates", response_model=SubstrateRecord)
async def add_project_substrate(project_id: str, payload: SubstrateRequest) -> SubstrateRecord:
    return project_workflow_service.add_substrate(project_id, payload)


@router.get("/{project_id}/substrates", response_model=list[SubstrateRecord])
async def list_project_substrates(project_id: str) -> list[SubstrateRecord]:
    return project_workflow_service.get_detail(project_id).substrates


@router.post("/{project_id}/active-site", response_model=ActiveSiteRecord)
async def add_project_active_site(project_id: str, payload: ActiveSiteRequest) -> ActiveSiteRecord:
    return project_workflow_service.add_active_site(project_id, payload)


@router.get("/{project_id}/active-site", response_model=list[ActiveSiteRecord])
async def list_project_active_sites(project_id: str) -> list[ActiveSiteRecord]:
    return project_workflow_service.get_detail(project_id).active_sites


@router.post("/{project_id}/variants/generate", response_model=list[EnzymeVariantRecord])
async def generate_project_variants(project_id: str, payload: VariantGenerateRequest) -> list[EnzymeVariantRecord]:
    return project_workflow_service.generate_variants(project_id, payload)


@router.get("/{project_id}/variants", response_model=list[EnzymeVariantRecord])
async def list_project_variants(project_id: str) -> list[EnzymeVariantRecord]:
    return project_workflow_service.get_detail(project_id).variants


@router.post("/{project_id}/docking-jobs", response_model=DockingJobRecord)
async def add_project_docking_job(project_id: str, payload: DockingJobRequest) -> DockingJobRecord:
    return project_workflow_service.add_docking_job(project_id, payload)


@router.get("/{project_id}/docking-jobs", response_model=list[DockingJobRecord])
async def list_project_docking_jobs(project_id: str) -> list[DockingJobRecord]:
    return project_workflow_service.get_detail(project_id).docking_jobs


@router.post("/{project_id}/docking/jobs", response_model=DockingJobWithResult)
async def create_project_docking_job_v2(project_id: str, payload: DockingJobCreate) -> DockingJobWithResult:
    job = docking_service.create_job(project_id, payload)
    return docking_service.get_job(job.id)


@router.get("/{project_id}/docking/jobs", response_model=list[DockingJobWithResult])
async def list_project_docking_jobs_v2(project_id: str) -> list[DockingJobWithResult]:
    return docking_service.list_project_jobs(project_id)


@router.post("/{project_id}/reports/generate", response_model=AnalysisReportRecord)
async def generate_project_report(project_id: str) -> AnalysisReportRecord:
    return project_workflow_service.generate_report(project_id)


@router.get("/{project_id}/reports", response_model=list[AnalysisReportRecord])
async def list_project_reports(project_id: str) -> list[AnalysisReportRecord]:
    return project_workflow_service.get_detail(project_id).reports
