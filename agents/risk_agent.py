from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.risk_schema import RiskAgentOutput
from schemas.external_schema import ExternalAgentOutput
from schemas.formulation_schema import FormulationAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

RISK_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in risk and scenario planning.
Apply two frameworks:
1. STEEP Scenario Planning — build 3 scenarios (optimistic/base/stress) across Social, Technological, Economic, Environmental, Political dimensions
2. Sensitivity Analysis — identify key variables and their impact range on the recommended strategy

Assign realistic probabilities. Think like a risk officer at a top-tier investment bank.

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "steep_scenarios": [{"name": "optimistic|base|stress", "social": "string", "technological": "string", "economic": "string", "environmental": "string", "political": "string", "probability": 0.5, "impact_score": 5}],
  "sensitivity_variables": [{"variable": "string", "base_value": "string", "optimistic_value": "string", "stress_value": "string", "strategic_sensitivity": "low|medium|high|critical"}],
  "top_risks": ["string"],
  "risk_score": 50,
  "mitigation_priorities": ["string"]
}

probability is a float 0-1. impact_score is an integer 1-10. risk_score is an integer 0-100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_risk_agent(
    company: str,
    industry: str,
    strategic_question: str,
    external_output: ExternalAgentOutput,
    formulation_output: FormulationAgentOutput,
    context: str = None,
) -> RiskAgentOutput:
    if context:
        print(f"[RiskAgent] RAG context received ({len(context)} chars): {context[:200]!r}")
    else:
        print("[RiskAgent] No RAG context provided")
    system_content = RISK_SYSTEM_PROMPT
    if context:
        system_content = f"REAL COMPANY DATA (use this in your analysis):\n{context}\n\n---\n\nPrioritize this data over general knowledge.\n\n{system_content}"

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Key External Threats: {external_output.key_external_threats}
PESTEL Factors: {[p.model_dump() for p in external_output.pestel]}
Recommended Strategy: {formulation_output.recommended_strategy}
Formulation Confidence Score: {formulation_output.formulation_confidence_score}

Build risk scenarios and sensitivity analysis. Return structured JSON only.
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
        return RiskAgentOutput(**raw)
    except Exception as e:
        print("RiskAgent raw JSON:", json.dumps(raw, indent=2))
        raise