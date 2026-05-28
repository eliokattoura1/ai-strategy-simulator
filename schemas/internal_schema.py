from pydantic import BaseModel, Field
from typing import List, Optional

class VRIOResource(BaseModel):
    resource: str
    valuable: bool
    rare: bool
    inimitable: bool
    organized: bool
    competitive_implication: str

class McKinsey7SElement(BaseModel):
    element: str
    assessment: str
    alignment_score: float = Field(ge=0, le=100)

class ValueChainActivity(BaseModel):
    activity: str
    type: str
    strength: str
    cost_driver: bool
    value_driver: bool

class InternalAgentOutput(BaseModel):
    company: str
    vrio_resources: List[VRIOResource]
    mckinsey_7s: List[McKinsey7SElement]
    value_chain: List[ValueChainActivity]
    core_competencies: List[str]
    internal_strength_score: float = Field(ge=0, le=100)
    key_strengths: List[str]
    key_weaknesses: List[str]

InternalAgentOutput.model_rebuild()