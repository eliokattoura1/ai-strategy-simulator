import asyncio
from schemas.external_schema import ExternalAgentOutput
from schemas.internal_schema import InternalAgentOutput
from schemas.position_schema import PositionAgentOutput
from schemas.competitive_schema import CompetitiveAgentOutput
from schemas.formulation_schema import FormulationAgentOutput
from schemas.risk_schema import RiskAgentOutput
from schemas.execution_schema import ExecutionAgentOutput
from agents.external_agent import run_external_agent
from agents.internal_agent import run_internal_agent
from agents.position_agent import run_position_agent
from agents.competitive_agent import run_competitive_agent
from agents.formulation_agent import run_formulation_agent
from agents.risk_agent import run_risk_agent
from agents.execution_agent import run_execution_agent
from schemas.finance_schema import FinanceAgentOutput
from agents.finance_agent import run_finance_agent
from schemas.ethics_schema import EthicsAgentOutput
from agents.ethics_agent import run_ethics_agent
from dataclasses import dataclass

@dataclass
class SimulatorState:
    company: str
    industry: str
    strategic_question: str
    external: ExternalAgentOutput = None
    internal: InternalAgentOutput = None
    position: PositionAgentOutput = None
    competitive: CompetitiveAgentOutput = None
    formulation: FormulationAgentOutput = None
    risk: RiskAgentOutput = None
    ethics: EthicsAgentOutput = None
    execution: ExecutionAgentOutput = None
    finance: FinanceAgentOutput = None
    market_data: dict = None

def _build_rag_fetcher(company_name: str):
    """Return a context-fetching function if RAG is available, else a no-op."""
    try:
        from rag.document_processor import query_context
        def fetch(query: str) -> str:
            return query_context(company_name, query) or None
        return fetch
    except Exception:
        return lambda query: None


async def run_orchestrator(
    company: str,
    industry: str,
    strategic_question: str,
    company_name: str = None,
    ticker: str = None,
    country_code: str = None,
) -> SimulatorState:
    state = SimulatorState(
        company=company,
        industry=industry,
        strategic_question=strategic_question
    )

    market_data_str = ""
    if ticker or country_code:
        try:
            from data_layer.market_data import get_all_market_data, format_for_agent_prompt
            print(f"📡 Fetching market data: ticker={ticker} country={country_code}...")
            md = get_all_market_data(ticker or "", country_code or "")
            state.market_data = md
            market_data_str = format_for_agent_prompt(md)
            quality = md.get("data_quality", {}).get("overall", "None")
            print(f"📡 Market data quality: {quality}")
        except Exception as e:
            print(f"📡 Market data fetch failed: {e}")

    fetch = _build_rag_fetcher(company_name) if company_name else (lambda q: None)

    print("🔍 Running External + Internal agents in parallel...")
    state.external, state.internal = await asyncio.gather(
        run_external_agent(
            company, industry, strategic_question,
            context=fetch("external environment PESTEL market trends competition regulatory political economic"),
            market_data=market_data_str,
        ),
        run_internal_agent(
            company, industry, strategic_question,
            context=fetch("internal capabilities resources operations technology staff financial performance"),
        ),
    )

    print("📍 Running Position agent...")
    state.position = await run_position_agent(
        company, industry, strategic_question,
        state.external, state.internal,
        context=fetch("strategic position market share growth competitive advantages SWOT"),
    )

    print("⚔️ Running Competitive agent...")
    state.competitive = await run_competitive_agent(
        company, industry, strategic_question,
        state.external, state.position,
        context=fetch("competitors competitive strategy market dynamics pricing rivalry"),
    )

    print("🎯 Running Formulation agent...")
    state.formulation = await run_formulation_agent(
        company, industry, strategic_question,
        state.internal, state.position, state.competitive,
        context=fetch("strategy direction value proposition differentiation cost structure"),
    )

    print("⚠️ Running Risk agent...")
    state.risk = await run_risk_agent(
        company, industry, strategic_question,
        state.external, state.formulation,
        context=fetch("risks challenges threats uncertainties regulatory compliance"),
    )

    print("⚖️  Running Ethics agent...")
    state.ethics = await run_ethics_agent(
        company, industry, strategic_question,
        state.risk, state.formulation,
        context=fetch("ethics ESG stakeholder impact governance social responsibility"),
    )

    print("🚀 Running Execution agent...")
    state.execution = await run_execution_agent(
        company, industry, strategic_question,
        state.formulation, state.risk,
        context=fetch("implementation operations milestones KPIs execution roadmap initiatives"),
    )

    # Re-run execution with actual risk output
    print("🔄 Re-running Execution agent with risk data...")
    state.execution = await run_execution_agent(
        company, industry, strategic_question,
        state.formulation, state.risk,
        context=fetch("implementation operations milestones KPIs execution roadmap initiatives"),
    )

    print("💰 Running Finance agent...")
    state.finance = await run_finance_agent(
        company, industry, strategic_question,
        state.formulation, state.execution,
        context=fetch("financial performance revenue EBITDA cash flow valuation cap table funding burn rate"),
        market_data=market_data_str,
    )

    print("✅ All agents complete.")
    return state