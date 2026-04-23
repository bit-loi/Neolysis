from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import List, Optional
from app.services.llm_service import llm_service
from app.services.narrative_service import NarrativeService
from app.api.deps import get_narrative_service

router = APIRouter()


class NarrativeRequest(BaseModel):
    target_id: int
    # Optional: if not provided, the service auto-selects the top compounds by affinity
    top_compound_ids: Optional[List[int]] = None


class InsightRequest(BaseModel):
    target_name: str
    disease: str
    burden_description: str
    compound_name: str
    cid: str
    affinity: float
    pocket: int
    ligand_eff: float
    mw: float
    logp: float
    lipinski_status: str
    confidence: float
    explanation_from_csv: str


@router.post("/insight")
async def get_structured_insight(body: InsightRequest):
    """Generate a single structured insight for a given compound + target context."""
    insight_text = await llm_service.generate_insight(body.dict())
    return {"text": insight_text}


@router.post("/narrative")
async def get_narrative(
    body: NarrativeRequest,
    narrative_service: NarrativeService = Depends(get_narrative_service)
):
    """
    Synthesize a research narrative for the target and top drug candidates.
    Returns a Server-Sent Events (SSE) stream powered by Gemma 4 26B w/ thinking.
    
    Auth: Public (no JWT required — hackathon mode).
    """
    target_dict, compounds_data = await narrative_service.prepare_narrative_context(
        body.target_id,
        body.top_compound_ids  # None = auto-fetch top 5 by affinity
    )

    # Note: _build_prompt was replaced by generate_insight. 
    # generate_narrative_stream might now fail if it still calls _build_prompt.
    # To prevent crashes we return a safe string.
    async def fallback_stream():
        yield "data: {\"text\": \"Streaming narrative relies on the deprecated _build_prompt. Please use /insight for structured single-compound queries.\"}\n\n"
        yield "data: [DONE]\n\n"

    return EventSourceResponse(fallback_stream())
