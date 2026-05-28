from pydantic import BaseModel, Field
from typing import List

class PESTELFactor(BaseModel):
    factor: str
    description: str
    impact: str
    direction: str

class PorterForce(BaseModel):
    force: str
    intensity: str
    score: float = Field(ge=0, le=10)
    rationale: str

class IndustryLifeCycle(BaseModel):
    stage: str
    rationale: str
    strategic_implication: str

class ExternalAgentOutput(BaseModel):
    company: str
    industry: str
    pestel: List[PESTELFactor]
    porter_forces: List[PorterForce]
    industry_lifecycle: IndustryLifeCycle
    overall_attractiveness_score: float = Field(ge=0, le=100)
    key_external_threats: List[str]
    key_external_opportunities: List[str]

ExternalAgentOutput.model_rebuild()