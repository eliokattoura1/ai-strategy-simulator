import asyncio
import json
from agents import synthesis
from agents.orchestrator import run_orchestrator
from agents.synthesis import run_synthesis

async def run_simulation(company: str, industry: str, strategic_question: str, company_name: str = None):
    print(f"\n{'='*60}")
    print(f"AI STRATEGY SIMULATOR")
    print(f"Company: {company}")
    print(f"Industry: {industry}")
    print(f"Question: {strategic_question}")
    print(f"{'='*60}\n")

    # Run all agents
    state = await run_orchestrator(company, industry, strategic_question, company_name=company_name)

    # Synthesize
    print("🧠 Running Synthesis Layer...")
    synthesis = await run_synthesis(state)

    print(f"\n{'='*60}")
    print(f"✅ SIMULATION COMPLETE")
    print(f"Overall Strategic Fit Score: {synthesis.overall_strategic_fit_score}/100")
    print(f"Recommended Strategy: {synthesis.ranked_recommendation}")
    print(f"{'='*60}\n")

    # Save raw JSON output
    output = {
        "company": company,
        "industry": industry,
        "strategic_question": strategic_question,
        "external": state.external.model_dump(),
        "internal": state.internal.model_dump(),
        "position": state.position.model_dump(),
        "competitive": state.competitive.model_dump(),
        "formulation": state.formulation.model_dump(),
        "risk": state.risk.model_dump(),
        "execution": state.execution.model_dump(),
        "finance": state.finance.model_dump() if state.finance else None,
        "synthesis": synthesis.model_dump()
    }
    if state.ethics:
        output["ethics"] = state.ethics.model_dump()

    with open("reports/output.json", "w") as f:
        json.dump(output, f, indent=2)

    print("📄 Raw output saved to reports/output.json")
    return state, synthesis

if __name__ == "__main__":
    asyncio.run(run_simulation(
        company="Bank Audi",
        industry="Lebanese Banking & Financial Services",
        strategic_question="Should Bank Audi expand into fintech or defend its core banking position?"
    ))