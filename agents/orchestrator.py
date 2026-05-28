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
    execution: ExecutionAgentOutput = None

async def run_orchestrator(company: str, industry: str, strategic_question: str) -> SimulatorState:
    state = SimulatorState(
        company=company,
        industry=industry,
        strategic_question=strategic_question
    )

    print("🔍 Running External + Internal agents in parallel...")
    state.external, state.internal = await asyncio.gather(
        run_external_agent(company, industry, strategic_question),
        run_internal_agent(company, industry, strategic_question)
    )

    print("📍 Running Position agent...")
    state.position = await run_position_agent(
        company, industry, strategic_question,
        state.external, state.internal
    )

    print("⚔️ Running Competitive agent...")
    state.competitive = await run_competitive_agent(
        company, industry, strategic_question,
        state.external, state.position
    )

    print("🎯 Running Formulation agent...")
    state.formulation = await run_formulation_agent(
        company, industry, strategic_question,
        state.internal, state.position, state.competitive
    )

    print("⚠️ Running Risk agent...")
    state.risk = await run_risk_agent(
        company, industry, strategic_question,
        state.external, state.formulation
    )

    print("🚀 Running Execution agent...")
    state.execution = await run_execution_agent(
        company, industry, strategic_question,
        state.formulation, state.risk
    )

    # Re-run execution with actual risk output
    print("🔄 Re-running Execution agent with risk data...")
    state.execution = await run_execution_agent(
        company, industry, strategic_question,
        state.formulation, state.risk
    )

    print("✅ All agents complete.")
    return state