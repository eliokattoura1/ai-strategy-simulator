from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.competitive_schema import CompetitiveAgentOutput
from schemas.external_schema import ExternalAgentOutput
from schemas.position_schema import PositionAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

COMPETITIVE_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in competitive dynamics.
Apply two frameworks:
1. Game Theory — model competitor responses as payoff scenarios, identify dominant strategy
2. Blue Ocean ERRC Grid — Eliminate, Reduce, Raise, Create factors to unlock uncontested space

Think like a chess grandmaster. Anticipate 2nd and 3rd order competitor moves.

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "game_theory_scenarios": [{"scenario": "string", "our_move": "string", "competitor_response": "string", "payoff_us": 5, "payoff_competitor": 5, "nash_equilibrium": true, "recommended": true}],
  "errc_grid": [{"factor": "string", "action": "eliminate|reduce|raise|create", "rationale": "string", "impact": 5}],
  "blue_ocean_opportunity": "string",
  "competitive_intensity_score": 50,
  "recommended_competitive_posture": "string"
}

payoff_us and payoff_competitor are integers 1-10. impact is an integer 1-10. competitive_intensity_score is an integer 0-100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_competitive_agent(
    company: str,
    industry: str,
    strategic_question: str,
    external_output: ExternalAgentOutput,
    position_output: PositionAgentOutput
) -> CompetitiveAgentOutput:

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Porter's Forces Context:
{[f.model_dump() for f in external_output.porter_forces]}

TOWS Strategies:
{[s.model_dump() for s in position_output.tows_strategies]}

Ansoff Options:
{[a.model_dump() for a in position_output.ansoff_options]}

Model competitive dynamics and blue ocean opportunities. Return structured JSON only.
"""
    response = await client.chat.completions.create(
        model=AGENT_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": COMPETITIVE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    raw = json.loads(response.choices[0].message.content)
    try:
        return CompetitiveAgentOutput(**raw)
    except Exception as e:
        print("CompetitiveAgent raw JSON:", json.dumps(raw, indent=2))
        raise