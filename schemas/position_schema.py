from pydantic import BaseModel, Field
from typing import List, Dict

class SWOTItem(BaseModel):
    item: str
    impact_score: int = Field(..., ge=1, le=10)

class TOWSStrategy(BaseModel):
    type: str  # SO / ST / WO / WT
    strategy: str
    rationale: str

class BCGPosition(BaseModel):
    unit: str
    market_share: float
    market_growth: float
    quadrant: str  # star / cash cow / question mark / dog
    recommendation: str

class AnsoffOption(BaseModel):
    quadrant: str  # market penetration / market development / product development / diversification
    initiative: str
    risk_level: str  # low / medium / high
    rationale: str

class PositionAgentOutput(BaseModel):
    strengths: List[SWOTItem]
    weaknesses: List[SWOTItem]
    opportunities: List[SWOTItem]
    threats: List[SWOTItem]
    tows_strategies: List[TOWSStrategy]
    bcg_positions: List[BCGPosition]
    ansoff_options: List[AnsoffOption]
    strategic_position_score: int = Field(..., ge=0, le=100)

PositionAgentOutput.model_rebuild()