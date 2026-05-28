from pydantic import BaseModel, Field
from typing import List

class STEEPScenario(BaseModel):
    name: str  # optimistic / base / stress
    social: str
    technological: str
    economic: str
    environmental: str
    political: str
    probability: float = Field(..., ge=0, le=1)
    impact_score: int = Field(..., ge=1, le=10)

class SensitivityVariable(BaseModel):
    variable: str
    base_value: str
    optimistic_value: str
    stress_value: str
    strategic_sensitivity: str  # low / medium / high / critical

class RiskAgentOutput(BaseModel):
    steep_scenarios: List[STEEPScenario]
    sensitivity_variables: List[SensitivityVariable]
    top_risks: List[str]
    risk_score: int = Field(..., ge=0, le=100)
    mitigation_priorities: List[str]

RiskAgentOutput.model_rebuild()