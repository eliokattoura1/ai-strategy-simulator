from pydantic import BaseModel, Field
from typing import List

class BSCObjective(BaseModel):
    perspective: str  # financial / customer / internal / learning
    objective: str
    kpi: str
    target: str
    initiative: str

class OKR(BaseModel):
    objective: str
    key_results: List[str]
    timeframe: str  # Q1 / Q2 / H1 / annual
    owner: str

class ExecutionAgentOutput(BaseModel):
    balanced_scorecard: List[BSCObjective]
    okrs: List[OKR]
    critical_success_factors: List[str]
    execution_readiness_score: int = Field(..., ge=0, le=100)
    quick_wins: List[str]

ExecutionAgentOutput.model_rebuild()