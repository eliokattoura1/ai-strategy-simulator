from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.execution_schema import ExecutionAgentOutput
from schemas.formulation_schema import FormulationAgentOutput
from schemas.risk_schema import RiskAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

EXECUTION_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in strategy execution.
Apply two frameworks:
1. Balanced Scorecard — define objectives, KPIs, targets, and initiatives across 4 perspectives
2. OKRs — define ambitious objectives with measurable key results per quarter

Make KPIs specific and measurable. OKRs should be ambitious but achievable.

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "balanced_scorecard": [{"perspective": "financial|customer|internal|learning", "objective": "string", "kpi": "string", "target": "string", "initiative": "string"}],
  "okrs": [{"objective": "string", "key_results": ["string"], "timeframe": "Q1|Q2|H1|annual", "owner": "string"}],
  "critical_success_factors": ["string"],
  "execution_readiness_score": 50,
  "quick_wins": ["string"]
}

execution_readiness_score is an integer 0-100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_execution_agent(
    company: str,
    industry: str,
    strategic_question: str,
    formulation_output: FormulationAgentOutput,
    risk_output: RiskAgentOutput,
    context: str = None,
) -> ExecutionAgentOutput:
    if context:
        print(f"[ExecutionAgent] RAG context received ({len(context)} chars): {context[:200]!r}")
    else:
        print("[ExecutionAgent] No RAG context provided")
    system_content = EXECUTION_SYSTEM_PROMPT
    if context:
        system_content = f"REAL COMPANY DATA (use this in your analysis):\n{context}\n\n---\n\nPrioritize this data over general knowledge.\n\n{system_content}"

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Recommended Strategy: {formulation_output.recommended_strategy}
Formulation Confidence Score: {formulation_output.formulation_confidence_score}
Top Risks: {risk_output.top_risks}
Base Scenario: {[s.model_dump() for s in risk_output.steep_scenarios if s.name == "base"]}

Build execution roadmap. Return structured JSON only.
"""
    response = await client.chat.completions.create(
        model=AGENT_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
    )

    raw = json.loads(response.choices[0].message.content)
    try:
        return ExecutionAgentOutput(**raw)
    except Exception as e:
        print("ExecutionAgent raw JSON:", json.dumps(raw, indent=2))
        raise