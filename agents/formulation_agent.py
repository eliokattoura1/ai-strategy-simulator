from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.formulation_schema import FormulationAgentOutput
from schemas.position_schema import PositionAgentOutput
from schemas.competitive_schema import CompetitiveAgentOutput
from schemas.internal_schema import InternalAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

FORMULATION_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in strategy formulation.
Apply two frameworks:
1. Bowman's Strategy Clock — identify optimal price/value positioning (8 positions)
2. Porter's Generic Strategies — recommend cost leadership, differentiation, or focus with fit score

Strategy Clock positions:
1. Low price/low value, 2. Low price, 3. Hybrid, 4. Differentiation,
5. Focused differentiation, 6-8. Failure zone (high price/low value variants)

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "strategy_clock_positions": [{"position": 4, "label": "string", "price_point": "string", "perceived_value": "string", "viability": "string"}],
  "generic_strategies": [{"strategy": "cost leadership|differentiation|focus-cost|focus-differentiation", "rationale": "string", "fit_score": 50, "risks": ["string"]}],
  "recommended_strategy": "string",
  "strategic_logic": "string",
  "formulation_confidence_score": 50
}

position is an integer 1-8. fit_score is an integer 0-100. formulation_confidence_score is an integer 0-100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_formulation_agent(
    company: str,
    industry: str,
    strategic_question: str,
    internal_output: InternalAgentOutput,
    position_output: PositionAgentOutput,
    competitive_output: CompetitiveAgentOutput
) -> FormulationAgentOutput:

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Core Competencies: {internal_output.core_competencies}
Internal Strength Score: {internal_output.internal_strength_score}
Strategic Position Score: {position_output.strategic_position_score}
Dominant Competitive Strategy: {competitive_output.recommended_competitive_posture}
Blue Ocean Opportunity: {competitive_output.blue_ocean_opportunity}

Formulate optimal strategy. Return structured JSON only.
"""
    response = await client.chat.completions.create(
        model=AGENT_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FORMULATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    raw = json.loads(response.choices[0].message.content)
    try:
        return FormulationAgentOutput(**raw)
    except Exception as e:
        print("FormulationAgent raw JSON:", json.dumps(raw, indent=2))
        raise