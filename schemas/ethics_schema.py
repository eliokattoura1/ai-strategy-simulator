from pydantic import BaseModel, Field
from typing import List, Literal


class StakeholderImpact(BaseModel):
    stakeholder: str
    impact_type: Literal["Positive", "Negative", "Mixed", "Neutral"]
    severity: Literal["High", "Medium", "Low"]
    description: str
    ethical_concern: str | None = None


class ESGScore(BaseModel):
    pillar: Literal["Environmental", "Social", "Governance"]
    score: float = Field(..., ge=0.0, le=10.0)
    rationale: str
    evidence_basis: str                  # specific metrics/facts that ground the score
    red_flags: List[str] = Field(default_factory=list)


class EthicalFrameworkAssessment(BaseModel):
    framework: Literal["Utilitarian", "Deontological", "Virtue Ethics"]
    verdict: Literal["Supports", "Neutral", "Opposes"]
    reasoning: str


class EthicsAgentOutput(BaseModel):
    stakeholder_impacts: List[StakeholderImpact]
    ethical_frameworks: List[EthicalFrameworkAssessment]
    esg_scores: List[ESGScore]
    composite_esg_score: float = Field(..., ge=0.0, le=10.0)
    ethical_red_flags: List[str]
    recommended_safeguards: List[str]
    overall_ethical_risk: Literal["High", "Medium", "Low"]
    ethics_score: int = Field(..., ge=0, le=100)

EthicsAgentOutput.model_rebuild()
