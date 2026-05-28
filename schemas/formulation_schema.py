from pydantic import BaseModel, Field
from typing import List

class StrategyClockPosition(BaseModel):
    position: int = Field(..., ge=1, le=8)
    label: str
    price_point: str
    perceived_value: str
    viability: str

class GenericStrategy(BaseModel):
    strategy: str  # cost leadership / differentiation / focus-cost / focus-differentiation
    rationale: str
    fit_score: int = Field(..., ge=0, le=100)
    risks: List[str]

class FormulationAgentOutput(BaseModel):
    strategy_clock_positions: List[StrategyClockPosition]
    generic_strategies: List[GenericStrategy]
    recommended_strategy: str
    strategic_logic: str
    formulation_confidence_score: int = Field(..., ge=0, le=100)

FormulationAgentOutput.model_rebuild()