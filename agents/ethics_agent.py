from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.ethics_schema import EthicsAgentOutput
from schemas.risk_schema import RiskAgentOutput
from schemas.formulation_schema import FormulationAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

ETHICS_SYSTEM_PROMPT = """You are a Chief Ethics Officer evaluating a strategic recommendation through three lenses.

1. Stakeholder Theory (Freeman) — identify all stakeholders affected by the strategy:
   employees, customers, shareholders, community, regulators, environment.
   For each: impact_type (Positive/Negative/Mixed/Neutral), severity (High/Medium/Low),
   description of the impact, and ethical_concern if any.

2. Three Ethical Frameworks applied to the strategy:
   - Utilitarian: does it maximize overall welfare?
   - Deontological: does it respect rights and duties regardless of outcome?
   - Virtue Ethics: does it reflect good character and organizational values?
   Each returns verdict (Supports/Neutral/Opposes) and reasoning.

3. ESG Scoring (0-10 each pillar):
   - Environmental: carbon footprint, resource use, sustainability
   - Social: employee welfare, community impact, diversity
   - Governance: transparency, board accountability, ethical leadership
   Include red_flags per pillar (empty list if none).

4. ethical_red_flags: specific concerns about the strategy (list of strings)
5. recommended_safeguards: concrete actions to address each red flag (list of strings)
6. overall_ethical_risk: High / Medium / Low
7. composite_esg_score: weighted average of E/S/G scores (0-10)
8. ethics_score: 0-100 (0=highly unethical, 100=exemplary)

Return ONLY valid JSON matching this schema exactly:
{
  "stakeholder_impacts": [{"stakeholder": "string", "impact_type": "Positive|Negative|Mixed|Neutral", "severity": "High|Medium|Low", "description": "string", "ethical_concern": "string or null"}],
  "ethical_frameworks": [{"framework": "Utilitarian|Deontological|Virtue Ethics", "verdict": "Supports|Neutral|Opposes", "reasoning": "string"}],
  "esg_scores": [{"pillar": "Environmental|Social|Governance", "score": 7.5, "rationale": "string", "red_flags": ["string"]}],
  "composite_esg_score": 7.0,
  "ethical_red_flags": ["string"],
  "recommended_safeguards": ["string"],
  "overall_ethical_risk": "High|Medium|Low",
  "ethics_score": 75
}

No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_ethics_agent(
    company: str,
    industry: str,
    strategic_question: str,
    risk_output: RiskAgentOutput,
    formulation_output: FormulationAgentOutput,
    context: str = None,
) -> EthicsAgentOutput:
    if context:
        print(f"[EthicsAgent] RAG context received ({len(context)} chars): {context[:200]!r}")
    else:
        print("[EthicsAgent] No RAG context provided")
    system_content = ETHICS_SYSTEM_PROMPT
    if context:
        system_content = f"REAL COMPANY DATA (use this in your analysis):\n{context}\n\n---\n\nPrioritize this data over general knowledge.\n\n{system_content}"

    steep_summary = "; ".join(
        f"{s.name} (p={s.probability}): social={s.social[:60]}, economic={s.economic[:60]}"
        for s in risk_output.steep_scenarios
    )

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Recommended Strategy: {formulation_output.recommended_strategy}

Top Risks: {risk_output.top_risks}

STEEP Scenarios Summary: {steep_summary}

Evaluate the ethical dimensions of this strategy. Return structured JSON only.
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
        return EthicsAgentOutput(**raw)
    except Exception as e:
        print("EthicsAgent raw JSON:", json.dumps(raw, indent=2))
        raise
