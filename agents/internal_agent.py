from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.internal_schema import InternalAgentOutput
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

INTERNAL_SYSTEM_PROMPT = """You are a senior strategy consultant specializing in internal capability analysis.

Return ONLY a valid JSON object with EXACTLY these field names:
{
  "company": "string",
  "vrio_resources": [{"resource": "string", "valuable": true, "rare": true, "inimitable": true, "organized": true, "competitive_implication": "SCA|TCA|CP|CD"}],
  "mckinsey_7s": [{"element": "string", "assessment": "string", "alignment_score": 0.0}],
  "value_chain": [{"activity": "string", "type": "primary|support", "strength": "strong|average|weak", "cost_driver": true, "value_driver": true}],
  "core_competencies": ["string"],
  "internal_strength_score": 0.0,
  "key_strengths": ["string"],
  "key_weaknesses": ["string"]
}

McKinsey 7S must include all 7 elements: Strategy, Structure, Systems, Shared Values, Skills, Style, Staff.
VRIO must include at least 5 key resources/capabilities.
Value chain must include at least 4 primary and 3 support activities.
Scores are floats between 0 and 100.
No markdown, no explanation, no extra fields. Return raw JSON only."""

async def run_internal_agent(company: str, industry: str, strategic_question: str, context: str = None) -> InternalAgentOutput:
    if context:
        print(f"[InternalAgent] RAG context received ({len(context)} chars): {context[:200]!r}")
    else:
        print("[InternalAgent] No RAG context provided")
    system_content = INTERNAL_SYSTEM_PROMPT
    if context:
        system_content = f"REAL COMPANY DATA (use this in your analysis):\n{context}\n\n---\n\nPrioritize this data over general knowledge.\n\n{system_content}"
    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Conduct a full internal capability audit. Return structured JSON only.
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
        return InternalAgentOutput(**raw)
    except Exception as e:
        print("InternalAgent raw JSON:", json.dumps(raw, indent=2))
        raise