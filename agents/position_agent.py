from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.position_schema import PositionAgentOutput
from schemas.external_schema import ExternalAgentOutput
from schemas.internal_schema import InternalAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

POSITION_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in strategic positioning.
Using inputs from external and internal analyses, apply:
1. SWOT → TOWS Matrix — generate SO, ST, WO, WT strategies
2. BCG Matrix — classify business units by market share vs growth
3. Ansoff Matrix — evaluate growth vector options with risk levels

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "strengths": [{"item": "string", "impact_score": 5}],
  "weaknesses": [{"item": "string", "impact_score": 5}],
  "opportunities": [{"item": "string", "impact_score": 5}],
  "threats": [{"item": "string", "impact_score": 5}],
  "tows_strategies": [{"type": "SO|ST|WO|WT", "strategy": "string", "rationale": "string"}],
  "bcg_positions": [{"unit": "string", "market_share": 0.0, "market_growth": 0.0, "quadrant": "star|cash cow|question mark|dog", "recommendation": "string"}],
  "ansoff_options": [{"quadrant": "market penetration|market development|product development|diversification", "initiative": "string", "risk_level": "low|medium|high", "rationale": "string"}],
  "strategic_position_score": 50
}

impact_score is an integer 1-10. strategic_position_score is an integer 0-100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_position_agent(
    company: str,
    industry: str,
    strategic_question: str,
    external_output: ExternalAgentOutput,
    internal_output: InternalAgentOutput
) -> PositionAgentOutput:

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

External Analysis Summary:
- Key Opportunities: {external_output.key_external_opportunities}
- Key Threats: {external_output.key_external_threats}
- Industry Attractiveness Score: {external_output.overall_attractiveness_score}
- Industry Stage: {external_output.industry_lifecycle.stage}

Internal Analysis Summary:
- Key Strengths: {internal_output.key_strengths}
- Key Weaknesses: {internal_output.key_weaknesses}
- Core Competencies: {internal_output.core_competencies}
- Internal Strength Score: {internal_output.internal_strength_score}

Conduct full strategic positioning analysis. Return structured JSON only.
"""
    response = await client.chat.completions.create(
        model=AGENT_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": POSITION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    raw = json.loads(response.choices[0].message.content)
    try:
        return PositionAgentOutput(**raw)
    except Exception as e:
        print("PositionAgent raw JSON:", json.dumps(raw, indent=2))
        raise