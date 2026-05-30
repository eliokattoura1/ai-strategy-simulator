import asyncio
import json
from agents import synthesis
from agents.orchestrator import run_orchestrator
from agents.synthesis import run_synthesis

async def run_simulation(
    company: str,
    industry: str,
    strategic_question: str,
    company_name: str = None,
    ticker: str = None,
    country_code: str = None,
    on_step=None,
):
    print(f"\n{'='*60}")
    print(f"AI STRATEGY SIMULATOR")
    print(f"Company: {company}")
    print(f"Industry: {industry}")
    print(f"Question: {strategic_question}")
    print(f"{'='*60}\n")

    # Run all agents
    state = await run_orchestrator(
        company, industry, strategic_question,
        company_name=company_name,
        ticker=ticker,
        country_code=country_code,
        on_step=on_step,
    )

    # Synthesize
    print("🧠 Running Synthesis Layer...")
    if on_step:
        on_step("synthesis", "running")
    synthesis = await run_synthesis(state)
    if on_step:
        on_step("synthesis", "done")

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
        "failed_agents": state.failed_agents,
        "external":     state.external.model_dump()     if state.external     else None,
        "internal":     state.internal.model_dump()     if state.internal     else None,
        "position":     state.position.model_dump()     if state.position     else None,
        "competitive":  state.competitive.model_dump()  if state.competitive  else None,
        "formulation":  state.formulation.model_dump()  if state.formulation  else None,
        "risk":         state.risk.model_dump()          if state.risk         else None,
        "execution":    state.execution.model_dump()    if state.execution    else None,
        "finance":      state.finance.model_dump()      if state.finance      else None,
        "synthesis":    synthesis.model_dump(),
    }
    if state.ethics:
        output["ethics"] = state.ethics.model_dump()
    if state.market_data:
        output["market_data"] = state.market_data

    # Annotate financial figures with data provenance flags
    try:
        from reports.data_quality import annotate_output
        output = annotate_output(output, state.market_data)
        dq = output["_data_quality"]["summary"]
        print(f"🔍 Data quality: {dq['verified_count']} verified, {dq['estimated_count']} AI estimates")
    except Exception as _dq_exc:
        print(f"⚠️  Data quality annotation skipped: {_dq_exc}")

    with open("reports/output.json", "w") as f:
        json.dump(output, f, indent=2)

    print("📄 Raw output saved to reports/output.json")
    return state, synthesis

if __name__ == "__main__":
    asyncio.run(run_simulation(
        company='Bank Audi',
        industry='Lebanese Banking & Financial Services',
        strategic_question='Should Bank Audi expand into fintech or defend its core banking position?',
        company_name='Bank Audi',
        ticker='',
        country_code='LB',
    ))