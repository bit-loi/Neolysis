from fastapi import APIRouter

from app.schemas.report import ReportGenerationRequest, ReportResponse
from app.services.report_generation import report_generation_service

router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(payload: ReportGenerationRequest) -> ReportResponse:
    return report_generation_service.generate(payload)
