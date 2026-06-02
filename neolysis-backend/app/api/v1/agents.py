from fastapi import APIRouter

from app.schemas.agent import AgentAnalysisRequest, AgentAnalysisResponse
from app.services.agent_orchestrator import agent_orchestrator

router = APIRouter()


@router.post("/analyze", response_model=AgentAnalysisResponse)
async def analyze_with_agent(payload: AgentAnalysisRequest) -> AgentAnalysisResponse:
    return agent_orchestrator.analyze(payload)
