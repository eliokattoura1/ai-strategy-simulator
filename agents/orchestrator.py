import asyncio
import operator
from dataclasses import dataclass, field
from typing import TypedDict, Optional, Any, Annotated

from langgraph.graph import StateGraph, START, END
from utils.logger import get_logger

logger = get_logger(__name__)

from schemas.external_schema import ExternalAgentOutput
from schemas.internal_schema import InternalAgentOutput
from schemas.position_schema import PositionAgentOutput
from schemas.competitive_schema import CompetitiveAgentOutput
from schemas.formulation_schema import FormulationAgentOutput
from schemas.risk_schema import RiskAgentOutput
from schemas.execution_schema import ExecutionAgentOutput
from schemas.finance_schema import FinanceAgentOutput
from schemas.ethics_schema import EthicsAgentOutput
from schemas.synthesis_schema import SynthesisOutput
from agents.external_agent import run_external_agent
from agents.internal_agent import run_internal_agent
from agents.position_agent import run_position_agent
from agents.competitive_agent import run_competitive_agent
from agents.formulation_agent import run_formulation_agent
from agents.risk_agent import run_risk_agent
from agents.execution_agent import run_execution_agent
from agents.finance_agent import run_finance_agent
from agents.ethics_agent import run_ethics_agent


# ── SimulatorState — kept for backward compat (synthesis.py + main.py import it)
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
    synthesis: SynthesisOutput = None
    market_data: dict = None
    failed_agents: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0


# ── Typed LangGraph state ──────────────────────────────────────────────────────
class PipelineState(TypedDict):
    # Inputs
    company: str
    industry: str
    strategic_question: str
    company_name: Optional[str]
    ticker: Optional[str]
    country_code: Optional[str]
    on_step: Optional[Any]
    # Infrastructure (populated by node_market_data)
    market_data: Optional[dict]
    market_data_str: str
    rag_fetch: Optional[Any]
    # Agent outputs
    external: Optional[Any]
    internal: Optional[Any]
    position: Optional[Any]
    competitive: Optional[Any]
    formulation: Optional[Any]
    risk: Optional[Any]
    ethics: Optional[Any]
    execution: Optional[Any]
    finance: Optional[Any]
    synthesis: Optional[Any]
    # operator.add reducer: safe for concurrent writes from parallel ext+int nodes
    failed_agents: Annotated[list[str], operator.add]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _emit(state: PipelineState, key: str, status: str) -> None:
    cb = state.get("on_step")
    if cb:
        cb(key, status)


async def _run_with_retry(name: str, coro_factory) -> tuple[Any, list[str]]:
    """Run coro_factory(); retry once after 3 s on failure. Returns (result, failed_names)."""
    for attempt in range(2):
        try:
            return await asyncio.wait_for(coro_factory(), timeout=60.0), []
        except Exception as exc:
            if attempt == 0:
                logger.warning("[%s] failed (attempt 1): %s — retrying in 3s...", name, exc)
                await asyncio.sleep(3)
            else:
                logger.error("[%s] failed after retry: %s", name, exc)
                return None, [name]


def _build_rag_fetcher(company_name: str):
    try:
        from rag.document_processor import query_context
        def fetch(query: str) -> str:
            return query_context(company_name, query) or None
        return fetch
    except Exception:
        return lambda query: None


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def node_market_data(state: PipelineState) -> dict:
    _emit(state, "market_data", "running")
    market_data = None
    market_data_str = ""
    ticker = state.get("ticker")
    country_code = state.get("country_code")

    if ticker or country_code:
        try:
            from data_layer.market_data import get_all_market_data, format_for_agent_prompt
            logger.info("Fetching market data: ticker=%s country=%s", ticker, country_code)
            md = get_all_market_data(ticker or "", country_code or "")
            market_data = md
            market_data_str = format_for_agent_prompt(md)
            quality = md.get("data_quality", {}).get("overall", "None")
            logger.info("Market data quality: %s", quality)
        except Exception as e:
            logger.warning("Market data fetch failed: %s", e)

    company_name = state.get("company_name")
    rag_fetch = _build_rag_fetcher(company_name) if company_name else (lambda q: None)

    _emit(state, "market_data", "done")
    logger.info("Running External + Internal agents in parallel...")
    _emit(state, "ext_int", "running")
    return {
        "market_data": market_data,
        "market_data_str": market_data_str,
        "rag_fetch": rag_fetch,
    }


async def node_external(state: PipelineState) -> dict:
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("external", lambda: run_external_agent(
        state["company"], state["industry"], state["strategic_question"],
        context=fetch("external environment PESTEL market trends competition regulatory political economic"),
        market_data=state.get("market_data_str", ""),
    ))
    return {"external": result, "failed_agents": failures}


async def node_internal(state: PipelineState) -> dict:
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("internal", lambda: run_internal_agent(
        state["company"], state["industry"], state["strategic_question"],
        context=fetch("internal capabilities resources operations technology staff financial performance"),
    ))
    return {"internal": result, "failed_agents": failures}


async def node_position(state: PipelineState) -> dict:
    _emit(state, "ext_int", "done")
    _emit(state, "position", "running")
    logger.info("Running Position agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("position", lambda: run_position_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("external"), state.get("internal"),
        context=fetch("strategic position market share growth competitive advantages SWOT"),
    ))
    _emit(state, "position", "done")
    return {"position": result, "failed_agents": failures}


async def node_competitive(state: PipelineState) -> dict:
    _emit(state, "competitive", "running")
    logger.info("Running Competitive agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("competitive", lambda: run_competitive_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("external"), state.get("position"),
        context=fetch("competitors competitive strategy market dynamics pricing rivalry"),
    ))
    _emit(state, "competitive", "done")
    return {"competitive": result, "failed_agents": failures}


async def node_formulation(state: PipelineState) -> dict:
    _emit(state, "formulation", "running")
    logger.info("Running Formulation agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("formulation", lambda: run_formulation_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("internal"), state.get("position"), state.get("competitive"),
        context=fetch("strategy direction value proposition differentiation cost structure"),
    ))
    _emit(state, "formulation", "done")
    return {"formulation": result, "failed_agents": failures}


async def node_risk(state: PipelineState) -> dict:
    _emit(state, "risk", "running")
    logger.info("Running Risk agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("risk", lambda: run_risk_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("external"), state.get("formulation"),
        context=fetch("risks challenges threats uncertainties regulatory compliance"),
    ))
    _emit(state, "risk", "done")
    return {"risk": result, "failed_agents": failures}


async def node_ethics(state: PipelineState) -> dict:
    _emit(state, "ethics", "running")
    logger.info("Running Ethics agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("ethics", lambda: run_ethics_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("risk"), state.get("formulation"),
        context=fetch("ethics ESG stakeholder impact governance social responsibility"),
    ))
    _emit(state, "ethics", "done")
    return {"ethics": result, "failed_agents": failures}


async def node_execution(state: PipelineState) -> dict:
    _emit(state, "execution", "running")
    logger.info("Running Execution agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("execution", lambda: run_execution_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("formulation"), state.get("risk"),
        context=fetch("implementation operations milestones KPIs execution roadmap initiatives"),
    ))
    _emit(state, "execution", "done")
    return {"execution": result, "failed_agents": failures}


async def node_finance(state: PipelineState) -> dict:
    _emit(state, "finance", "running")
    logger.info("Running Finance agent...")
    fetch = state.get("rag_fetch") or (lambda q: None)
    result, failures = await _run_with_retry("finance", lambda: run_finance_agent(
        state["company"], state["industry"], state["strategic_question"],
        state.get("formulation"), state.get("execution"),
        context=fetch("financial performance revenue EBITDA cash flow valuation cap table funding burn rate"),
        market_data=state.get("market_data_str", ""),
    ))
    _emit(state, "finance", "done")
    return {"finance": result, "failed_agents": failures}


async def node_synthesis(state: PipelineState) -> dict:
    from agents.synthesis import run_synthesis as _run_synthesis
    _emit(state, "synthesis", "running")
    logger.info("Running Synthesis Layer...")
    sim = SimulatorState(
        company=state["company"],
        industry=state["industry"],
        strategic_question=state["strategic_question"],
        external=state.get("external"),
        internal=state.get("internal"),
        position=state.get("position"),
        competitive=state.get("competitive"),
        formulation=state.get("formulation"),
        risk=state.get("risk"),
        ethics=state.get("ethics"),
        execution=state.get("execution"),
        finance=state.get("finance"),
        market_data=state.get("market_data"),
        failed_agents=state.get("failed_agents", []),
    )
    result, failures = await _run_with_retry("synthesis", lambda: _run_synthesis(sim))
    _emit(state, "synthesis", "done")
    return {"synthesis": result, "failed_agents": failures}


# ── Conditional edge: skip Finance when no market data is available ────────────

def _route_after_execution(state: PipelineState) -> str:
    if state.get("market_data") is not None:
        return "node_finance"
    return "node_synthesis"


# ── Graph construction (compiled once at import time) ─────────────────────────

def _build_graph():
    g = StateGraph(PipelineState)

    g.add_node("node_market_data", node_market_data)
    g.add_node("node_external",    node_external)
    g.add_node("node_internal",    node_internal)
    g.add_node("node_position",    node_position)
    g.add_node("node_competitive", node_competitive)
    g.add_node("node_formulation", node_formulation)
    g.add_node("node_risk",        node_risk)
    g.add_node("node_ethics",      node_ethics)
    g.add_node("node_execution",   node_execution)
    g.add_node("node_finance",     node_finance)
    g.add_node("node_synthesis",   node_synthesis)

    # Entry
    g.add_edge(START, "node_market_data")

    # Fan-out: market_data → external + internal run in parallel
    g.add_edge("node_market_data", "node_external")
    g.add_edge("node_market_data", "node_internal")

    # Fan-in: position waits for both external and internal
    g.add_edge("node_external", "node_position")
    g.add_edge("node_internal", "node_position")

    # Sequential chain
    g.add_edge("node_position",    "node_competitive")
    g.add_edge("node_competitive", "node_formulation")
    g.add_edge("node_formulation", "node_risk")
    g.add_edge("node_risk",        "node_ethics")
    g.add_edge("node_ethics",      "node_execution")

    # Conditional: run Finance only when market data is present
    g.add_conditional_edges(
        "node_execution",
        _route_after_execution,
        {"node_finance": "node_finance", "node_synthesis": "node_synthesis"},
    )

    g.add_edge("node_finance",   "node_synthesis")
    g.add_edge("node_synthesis", END)

    return g.compile()


_GRAPH = _build_graph()


# ── Public API ─────────────────────────────────────────────────────────────────

async def run_orchestrator(
    company: str,
    industry: str,
    strategic_question: str,
    company_name: str = None,
    ticker: str = None,
    country_code: str = None,
    on_step=None,
) -> SimulatorState:
    initial: PipelineState = {
        "company": company,
        "industry": industry,
        "strategic_question": strategic_question,
        "company_name": company_name,
        "ticker": ticker,
        "country_code": country_code,
        "on_step": on_step,
        "market_data": None,
        "market_data_str": "",
        "rag_fetch": None,
        "external": None,
        "internal": None,
        "position": None,
        "competitive": None,
        "formulation": None,
        "risk": None,
        "ethics": None,
        "execution": None,
        "finance": None,
        "synthesis": None,
        "failed_agents": [],
    }

    final = await _GRAPH.ainvoke(initial)

    failed = final.get("failed_agents", [])
    if failed:
        logger.warning("Pipeline complete with %d failed agent(s): %s", len(failed), ", ".join(failed))
    else:
        logger.info("All agents complete.")

    return SimulatorState(
        company=company,
        industry=industry,
        strategic_question=strategic_question,
        external=final.get("external"),
        internal=final.get("internal"),
        position=final.get("position"),
        competitive=final.get("competitive"),
        formulation=final.get("formulation"),
        risk=final.get("risk"),
        ethics=final.get("ethics"),
        execution=final.get("execution"),
        finance=final.get("finance"),
        synthesis=final.get("synthesis"),
        market_data=final.get("market_data"),
        failed_agents=failed,
    )
