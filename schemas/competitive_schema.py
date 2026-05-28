from pydantic import BaseModel, Field
from typing import List, Dict

class GameTheoryScenario(BaseModel):
    scenario: str
    our_move: str
    competitor_response: str
    payoff_us: int = Field(..., ge=1, le=10)
    payoff_competitor: int = Field(..., ge=1, le=10)
    nash_equilibrium: bool
    recommended: bool

class ERRCItem(BaseModel):
    factor: str
    action: str  # eliminate / reduce / raise / create
    rationale: str
    impact: int = Field(..., ge=1, le=10)

class CompetitiveAgentOutput(BaseModel):
    game_theory_scenarios: List[GameTheoryScenario]
    errc_grid: List[ERRCItem]
    blue_ocean_opportunity: str
    competitive_intensity_score: int = Field(..., ge=0, le=100)
    recommended_competitive_posture: str

CompetitiveAgentOutput.model_rebuild()