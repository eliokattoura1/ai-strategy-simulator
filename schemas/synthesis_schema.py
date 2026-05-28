from pydantic import BaseModel, Field
from typing import List, Dict

class StrategicOption(BaseModel):
    option: str
    rationale: str
    strategic_fit_score: int = Field(..., ge=0, le=100)
    risk_score: int = Field(..., ge=0, le=100)
    feasibility_score: int = Field(..., ge=0, le=100)
    overall_score: int = Field(..., ge=0, le=100)
    supporting_frameworks: List[str]
    conflicting_signals: List[str]

class ScenarioBranch(BaseModel):
    scenario: str  # optimistic / base / stress
    recommended_option: str
    expected_outcome: str
    key_assumptions: List[str]

class SynthesisOutput(BaseModel):
    strategic_options: List[StrategicOption]
    ranked_recommendation: List[str]
    scenario_branches: List[ScenarioBranch]
    inter_agent_conflicts: List[str]
    conflict_resolutions: List[str]
    overall_strategic_fit_score: int = Field(..., ge=0, le=100)
    executive_summary: str
    board_narrative: str

SynthesisOutput.model_rebuild()