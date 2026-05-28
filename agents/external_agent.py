from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.external_schema import ExternalAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

EXTERNAL_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in external environment analysis.

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "company": "string",
  "industry": "string",
  "pestel": [{"factor": "string", "description": "string", "impact": "high|medium|low", "direction": "opportunity|threat"}],
  "porter_forces": [{"force": "string", "intensity": "high|medium|low", "score": 0.0, "rationale": "string"}],
  "industry_lifecycle": {"stage": "embryonic|growth|shakeout|mature|decline", "rationale": "string", "strategic_implication": "string"},
  "overall_attractiveness_score": 0.0,
  "key_external_threats": ["string"],
  "key_external_opportunities": ["string"]
}

Porter's forces must include all 5: Competitive Rivalry, Supplier Power, Buyer Power, Threat of Substitutes, Threat of New Entrants.
PESTEL must include all 6 factors.
Scores are floats between 0 and 100 for attractiveness, 0-10 for porter forces.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_external_agent(company: str, industry: str, strategic_question: str, context: str = None) -> ExternalAgentOutput:
    if context:
        print(f"[ExternalAgent] RAG context received ({len(context)} chars): {context[:200]!r}")
    else:
        print("[ExternalAgent] No RAG context provided")
    system_content = EXTERNAL_SYSTEM_PROMPT
    if context:
        system_content = f"REAL COMPANY DATA (use this in your analysis):\n{context}\n\n---\n\nPrioritize this data over general knowledge.\n\n{system_content}"
    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Conduct a full external environment analysis. Return structured JSON only.
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
        return ExternalAgentOutput(**raw)
    except Exception as e:
        print("ExternalAgent raw JSON:", json.dumps(raw, indent=2))
        raise