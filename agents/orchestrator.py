import asyncio
from dataclasses import dataclass, field
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
    failed_agents: list = field(default_factory=list)


def _build_rag_fetcher(company_name: str):
    """Return a context-fetching function if RAG is available, else a no-op."""
    try:
        from rag.document_processor import query_context
        def fetch(query: str) -> str:
            return query_context(company_name, query) or None
        return fetch
    except Exception:
        return lambda query: None


async def _run_with_retry(name: str, coro_factory, failed_agents: list):
    """Call coro_factory(); retry once after 3 s on failure; return None and record name on second failure."""
    for attempt in range(2):
        try:
            return await coro_factory()
        except Exception as exc:
            if attempt == 0:
                print(f"⚠️  [{name}] failed (attempt 1): {exc} — retrying in 3s...")
                await asyncio.sleep(3)
            else:
                print(f"❌ [{name}] failed after retry: {exc} — continuing without it.")
                failed_agents.append(name)
                return None


async def run_orchestrator(
    company: str,
    industry: str,
    strategic_question: str,
    company_name: str = None,
    ticker: str = None,
    country_code: str = None,
    on_step=None,
) -> SimulatorState:
    def _step(key: str, state: str):
        if on_step:
            on_step(key, state)
    state = SimulatorState(
        company=company,
        industry=industry,
        strategic_question=strategic_question
    )

    market_data_str = ""
    _step("market_data", "running")
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
    _step("market_data", "done")

    fetch = _build_rag_fetcher(company_name) if company_name else (lambda q: None)

    print("🔍 Running External + Internal agents in parallel...")
    _step("ext_int", "running")
    state.external, state.internal = await asyncio.gather(
        _run_with_retry("external", lambda: run_external_agent(
            company, industry, strategic_question,
            context=fetch("external environment PESTEL market trends competition regulatory political economic"),
            market_data=market_data_str,
        ), state.failed_agents),
        _run_with_retry("internal", lambda: run_internal_agent(
            company, industry, strategic_question,
            context=fetch("internal capabilities resources operations technology staff financial performance"),
        ), state.failed_agents),
    )
    _step("ext_int", "done")

    print("📍 Running Position agent...")
    _step("position", "running")
    state.position = await _run_with_retry("position", lambda: run_position_agent(
        company, industry, strategic_question,
        state.external, state.internal,
        context=fetch("strategic position market share growth competitive advantages SWOT"),
    ), state.failed_agents)
    _step("position", "done")

    print("⚔️ Running Competitive agent...")
    _step("competitive", "running")
    state.competitive = await _run_with_retry("competitive", lambda: run_competitive_agent(
        company, industry, strategic_question,
        state.external, state.position,
        context=fetch("competitors competitive strategy market dynamics pricing rivalry"),
    ), state.failed_agents)
    _step("competitive", "done")

    print("🎯 Running Formulation agent...")
    _step("formulation", "running")
    state.formulation = await _run_with_retry("formulation", lambda: run_formulation_agent(
        company, industry, strategic_question,
        state.internal, state.position, state.competitive,
        context=fetch("strategy direction value proposition differentiation cost structure"),
    ), state.failed_agents)
    _step("formulation", "done")

    print("⚠️ Running Risk agent...")
    _step("risk", "running")
    state.risk = await _run_with_retry("risk", lambda: run_risk_agent(
        company, industry, strategic_question,
        state.external, state.formulation,
        context=fetch("risks challenges threats uncertainties regulatory compliance"),
    ), state.failed_agents)
    _step("risk", "done")

    print("⚖️  Running Ethics agent...")
    _step("ethics", "running")
    state.ethics = await _run_with_retry("ethics", lambda: run_ethics_agent(
        company, industry, strategic_question,
        state.risk, state.formulation,
        context=fetch("ethics ESG stakeholder impact governance social responsibility"),
    ), state.failed_agents)
    _step("ethics", "done")

    print("🚀 Running Execution agent...")
    _step("execution", "running")
    state.execution = await _run_with_retry("execution", lambda: run_execution_agent(
        company, industry, strategic_question,
        state.formulation, state.risk,
        context=fetch("implementation operations milestones KPIs execution roadmap initiatives"),
    ), state.failed_agents)
    _step("execution", "done")

    print("💰 Running Finance agent...")
    _step("finance", "running")
    state.finance = await _run_with_retry("finance", lambda: run_finance_agent(
        company, industry, strategic_question,
        state.formulation, state.execution,
        context=fetch("financial performance revenue EBITDA cash flow valuation cap table funding burn rate"),
        market_data=market_data_str,
    ), state.failed_agents)
    _step("finance", "done")

    if state.failed_agents:
        print(f"⚠️  Pipeline complete with {len(state.failed_agents)} failed agent(s): {', '.join(state.failed_agents)}")
    else:
        print("✅ All agents complete.")
    return state
