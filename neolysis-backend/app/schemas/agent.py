from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.property import TargetConditions
from app.schemas.variant import VariantCandidate


class AgentAnalysisRequest(BaseModel):
    sequence: str = Field(..., min_length=1)
    target_conditions: TargetConditions = Field(default_factory=TargetConditions)
    variants: List[VariantCandidate] = Field(default_factory=list)
    user_question: Optional[str] = None
    enzyme_class_hint: Optional[str] = None


class AgentToolCall(BaseModel):
    name: str
    status: str
    summary: str


class AgentAnalysisResponse(BaseModel):
    agent_plan: List[str]
    tool_calls: List[AgentToolCall]
    structured_analysis: Dict[str, Any]
    final_report: str
    limitations: List[str] = Field(default_factory=list)
