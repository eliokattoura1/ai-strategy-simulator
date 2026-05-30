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

If any agent section is marked as unavailable, explicitly note the missing analytical dimension
in both executive_summary and board_narrative. Lower your confidence scores for affected areas
and flag the gap so the board can commission follow-up analysis.

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
    _NA = "[agent failed — data unavailable]"

    ext_section = (
        f"- Attractiveness Score: {state.external.overall_attractiveness_score}\n"
        f"- Opportunities: {state.external.key_external_opportunities}\n"
        f"- Threats: {state.external.key_external_threats}\n"
        f"- Industry Stage: {state.external.industry_lifecycle.stage}"
    ) if state.external else f"⚠️  {_NA}"

    int_section = (
        f"- Strength Score: {state.internal.internal_strength_score}\n"
        f"- Core Competencies: {state.internal.core_competencies}\n"
        f"- Key Strengths: {state.internal.key_strengths}\n"
        f"- Key Weaknesses: {state.internal.key_weaknesses}"
    ) if state.internal else f"⚠️  {_NA}"

    pos_section = (
        f"- Strategic Position Score: {state.position.strategic_position_score}\n"
        f"- TOWS Strategies: {[t.model_dump() for t in state.position.tows_strategies]}\n"
        f"- Ansoff Options: {[a.model_dump() for a in state.position.ansoff_options]}"
    ) if state.position else f"⚠️  {_NA}"

    comp_section = (
        f"- Recommended Posture: {state.competitive.recommended_competitive_posture}\n"
        f"- Competitive Intensity Score: {state.competitive.competitive_intensity_score}\n"
        f"- Blue Ocean Opportunity: {state.competitive.blue_ocean_opportunity}"
    ) if state.competitive else f"⚠️  {_NA}"

    form_section = (
        f"- Recommended Strategy: {state.formulation.recommended_strategy}\n"
        f"- Formulation Confidence Score: {state.formulation.formulation_confidence_score}\n"
        f"- Strategy Clock Positions: {[s.model_dump() for s in state.formulation.strategy_clock_positions]}"
    ) if state.formulation else f"⚠️  {_NA}"

    risk_section = (
        f"- Risk Score: {state.risk.risk_score}\n"
        f"- Top Risks: {state.risk.top_risks}\n"
        f"- Scenarios: {[s.model_dump() for s in state.risk.steep_scenarios]}"
    ) if state.risk else f"⚠️  {_NA}"

    exec_section = (
        f"- Execution Readiness Score: {state.execution.execution_readiness_score}\n"
        f"- Critical Success Factors: {state.execution.critical_success_factors}\n"
        f"- OKRs: {[o.model_dump() for o in state.execution.okrs]}"
    ) if state.execution else f"⚠️  {_NA}"

    failed_notice = (
        f"\n⚠️  FAILED AGENTS — analysis missing for: {', '.join(state.failed_agents)}\n"
        "Caveat your synthesis and board narrative to flag these analytical gaps.\n"
    ) if state.failed_agents else ""

    prompt = f"""
Company: {state.company}
Industry: {state.industry}
Strategic Question: {state.strategic_question}
{failed_notice}
=== AGENT OUTPUTS SUMMARY ===

EXTERNAL:
{ext_section}

INTERNAL:
{int_section}

POSITION:
{pos_section}

COMPETITIVE:
{comp_section}

FORMULATION:
{form_section}

RISK:
{risk_section}

EXECUTION:
{exec_section}

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