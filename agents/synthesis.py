from openai import AsyncOpenAI
from config import OPENAI_API_KEY, SYNTHESIS_MODEL, MAX_TOKENS
from schemas.synthesis_schema import SynthesisOutput
from agents.orchestrator import SimulatorState
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYNTHESIS_SYSTEM_PROMPT = """You are the Chief Strategy Officer synthesizing inputs from 7 specialized strategy agents.
Your role:
1. Identify conflicts between agent recommendations and resolve them
2. Score each strategic option across fit, risk, and feasibility (0-100)
3. Rank options and select the dominant recommendation
4. Write a board-level executive narrative (3-4 paragraphs, C-suite tone)

Conflicts to watch for:
- VRIO says "sustain core" but BCG says "divest"
- Ansoff says "diversify" but Generic Strategy says "focus"
- Game Theory says "aggressive" but Risk says "conservative"

Resolve conflicts by weighing strategic fit score, risk score, and execution readiness.

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "strategic_options": [{"option": "string", "rationale": "string", "strategic_fit_score": 50, "risk_score": 50, "feasibility_score": 50, "overall_score": 50, "supporting_frameworks": ["string"], "conflicting_signals": ["string"]}],
  "ranked_recommendation": ["string"],
  "scenario_branches": [{"scenario": "optimistic|base|stress", "recommended_option": "string", "expected_outcome": "string", "key_assumptions": ["string"]}],
  "inter_agent_conflicts": ["string"],
  "conflict_resolutions": ["string"],
  "overall_strategic_fit_score": 50,
  "executive_summary": "string",
  "board_narrative": "string"
}

All score fields are integers 0-100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_synthesis(state: SimulatorState) -> SynthesisOutput:
    prompt = f"""
Company: {state.company}
Industry: {state.industry}
Strategic Question: {state.strategic_question}

=== AGENT OUTPUTS SUMMARY ===

EXTERNAL:
- Attractiveness Score: {state.external.overall_attractiveness_score}
- Opportunities: {state.external.key_external_opportunities}
- Threats: {state.external.key_external_threats}
- Industry Stage: {state.external.industry_lifecycle.stage}

INTERNAL:
- Strength Score: {state.internal.internal_strength_score}
- Core Competencies: {state.internal.core_competencies}
- Key Strengths: {state.internal.key_strengths}
- Key Weaknesses: {state.internal.key_weaknesses}

POSITION:
- Strategic Position Score: {state.position.strategic_position_score}
- TOWS Strategies: {[t.model_dump() for t in state.position.tows_strategies]}
- Ansoff Options: {[a.model_dump() for a in state.position.ansoff_options]}

COMPETITIVE:
- Recommended Posture: {state.competitive.recommended_competitive_posture}
- Competitive Intensity Score: {state.competitive.competitive_intensity_score}
- Blue Ocean Opportunity: {state.competitive.blue_ocean_opportunity}

FORMULATION:
- Recommended Strategy: {state.formulation.recommended_strategy}
- Formulation Confidence Score: {state.formulation.formulation_confidence_score}
- Strategy Clock Positions: {[s.model_dump() for s in state.formulation.strategy_clock_positions]}

RISK:
- Risk Score: {state.risk.risk_score}
- Top Risks: {state.risk.top_risks}
- Scenarios: {[s.model_dump() for s in state.risk.steep_scenarios]}

EXECUTION:
- Execution Readiness Score: {state.execution.execution_readiness_score}
- Critical Success Factors: {state.execution.critical_success_factors}
- OKRs: {[o.model_dump() for o in state.execution.okrs]}

Synthesize all inputs. Resolve conflicts. Rank strategic options. Write board narrative.
Return structured JSON only.
"""
    response = await client.chat.completions.create(
        model=SYNTHESIS_MODEL,
        max_tokens=4096,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    raw = json.loads(response.choices[0].message.content)
    try:
        return SynthesisOutput(**raw)
    except Exception as e:
        print("Synthesis raw JSON:", json.dumps(raw, indent=2))
        raise