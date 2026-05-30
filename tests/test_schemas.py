"""
test_schemas.py
Validates Pydantic schema construction and field constraints for all 10 agent schemas.
No LLM calls — purely structural.
Run: python tests/test_schemas.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pydantic import ValidationError

from schemas.external_schema import ExternalAgentOutput, PESTELFactor, PorterForce, IndustryLifeCycle
from schemas.internal_schema import InternalAgentOutput, VRIOResource, McKinsey7SElement, ValueChainActivity
from schemas.position_schema import PositionAgentOutput, SWOTItem, TOWSStrategy, BCGPosition, AnsoffOption
from schemas.competitive_schema import CompetitiveAgentOutput, GameTheoryScenario, ERRCItem
from schemas.formulation_schema import FormulationAgentOutput, StrategyClockPosition, GenericStrategy
from schemas.risk_schema import RiskAgentOutput, STEEPScenario, SensitivityVariable
from schemas.execution_schema import ExecutionAgentOutput, BSCObjective, OKR
from schemas.ethics_schema import EthicsAgentOutput, StakeholderImpact, ESGScore, EthicalFrameworkAssessment
from schemas.finance_schema import (
    FinanceAgentOutput, DCFAnalysis, CashFlowYear, CapTableAnalysis,
    ShareholderRow, FundingRound, BurnAnalysis, UnitEconomics,
    FinancialStatements, PnLStatement, BalanceSheet, CashFlowStatement,
    ValuationMultiples, CompComp,
)
from schemas.synthesis_schema import SynthesisOutput, StrategicOption, ScenarioBranch


# ── Helpers ────────────────────────────────────────────────────────────────────

def _raises(model_cls, data: dict) -> bool:
    try:
        model_cls(**data)
        return False
    except (ValidationError, Exception):
        return True


# ── 1. External ───────────────────────────────────────────────────────────────

def test_external_valid():
    obj = ExternalAgentOutput(
        company="Acme",
        industry="Tech",
        pestel=[PESTELFactor(factor="Political", description="Stable", impact="Low", direction="Neutral")],
        porter_forces=[PorterForce(force="Rivalry", intensity="High", score=8.0, rationale="Many players")],
        industry_lifecycle=IndustryLifeCycle(stage="Growth", rationale="Fast growth", strategic_implication="Invest"),
        overall_attractiveness_score=75.0,
        key_external_threats=["Regulation"],
        key_external_opportunities=["Expansion"],
    )
    assert obj.overall_attractiveness_score == 75.0


def test_external_score_out_of_range():
    assert _raises(ExternalAgentOutput, dict(
        company="X", industry="Y",
        pestel=[PESTELFactor(factor="P", description="D", impact="I", direction="N")],
        porter_forces=[PorterForce(force="F", intensity="H", score=5.0, rationale="R")],
        industry_lifecycle=IndustryLifeCycle(stage="S", rationale="R", strategic_implication="I"),
        overall_attractiveness_score=101.0,  # invalid
        key_external_threats=[], key_external_opportunities=[],
    ))


def test_porter_force_score_bounds():
    assert _raises(PorterForce, dict(force="F", intensity="H", score=11.0, rationale="R"))
    assert not _raises(PorterForce, dict(force="F", intensity="H", score=10.0, rationale="R"))
    assert not _raises(PorterForce, dict(force="F", intensity="H", score=0.0, rationale="R"))


# ── 2. Internal ───────────────────────────────────────────────────────────────

def test_internal_valid():
    obj = InternalAgentOutput(
        company="Acme",
        vrio_resources=[VRIOResource(resource="Brand", valuable=True, rare=True, inimitable=True, organized=True, competitive_implication="SCA")],
        mckinsey_7s=[McKinsey7SElement(element="Strategy", assessment="Strong", alignment_score=80.0)],
        value_chain=[ValueChainActivity(activity="Ops", type="Primary", strength="Strong", cost_driver=True, value_driver=True)],
        core_competencies=["Innovation"],
        internal_strength_score=70.0,
        key_strengths=["Brand"],
        key_weaknesses=["Legacy IT"],
    )
    assert obj.internal_strength_score == 70.0


def test_internal_mckinsey_score_bounds():
    assert _raises(McKinsey7SElement, dict(element="E", assessment="A", alignment_score=101.0))
    assert not _raises(McKinsey7SElement, dict(element="E", assessment="A", alignment_score=100.0))


# ── 3. Position ───────────────────────────────────────────────────────────────

def test_position_valid():
    item = SWOTItem(item="Strong brand", impact_score=8)
    tows = TOWSStrategy(type="SO", strategy="Expand", rationale="Use strengths")
    bcg = BCGPosition(unit="Core", market_share=0.3, market_growth=0.15, quadrant="star", recommendation="Invest")
    ansoff = AnsoffOption(quadrant="market penetration", initiative="Discount", risk_level="low", rationale="Safe")
    obj = PositionAgentOutput(
        strengths=[item], weaknesses=[item], opportunities=[item], threats=[item],
        tows_strategies=[tows], bcg_positions=[bcg], ansoff_options=[ansoff],
        strategic_position_score=65,
    )
    assert obj.strategic_position_score == 65


def test_swot_impact_score_bounds():
    assert _raises(SWOTItem, dict(item="X", impact_score=0))   # ge=1
    assert _raises(SWOTItem, dict(item="X", impact_score=11))  # le=10
    assert not _raises(SWOTItem, dict(item="X", impact_score=5))


# ── 4. Competitive ────────────────────────────────────────────────────────────

def test_competitive_valid():
    gt = GameTheoryScenario(
        scenario="Price war", our_move="Hold", competitor_response="Cut",
        payoff_us=6, payoff_competitor=4, nash_equilibrium=False, recommended=True,
    )
    errc = ERRCItem(factor="Cost", action="reduce", rationale="Efficiency", impact=7)
    obj = CompetitiveAgentOutput(
        game_theory_scenarios=[gt],
        errc_grid=[errc],
        blue_ocean_opportunity="Digital advisory",
        competitive_intensity_score=55,
        recommended_competitive_posture="Differentiate",
    )
    assert obj.competitive_intensity_score == 55


def test_game_theory_payoff_bounds():
    assert _raises(GameTheoryScenario, dict(
        scenario="S", our_move="O", competitor_response="C",
        payoff_us=11, payoff_competitor=5, nash_equilibrium=False, recommended=False,
    ))


# ── 5. Formulation ────────────────────────────────────────────────────────────

def test_formulation_valid():
    pos = StrategyClockPosition(position=3, label="Hybrid", price_point="Mid", perceived_value="High", viability="Strong")
    gs = GenericStrategy(strategy="differentiation", rationale="Brand", fit_score=80, risks=["Imitation"])
    obj = FormulationAgentOutput(
        strategy_clock_positions=[pos],
        generic_strategies=[gs],
        recommended_strategy="Differentiation",
        strategic_logic="Leverage brand",
        formulation_confidence_score=75,
    )
    assert obj.formulation_confidence_score == 75


def test_strategy_clock_position_bounds():
    assert _raises(StrategyClockPosition, dict(position=0, label="L", price_point="P", perceived_value="V", viability="S"))
    assert _raises(StrategyClockPosition, dict(position=9, label="L", price_point="P", perceived_value="V", viability="S"))
    assert not _raises(StrategyClockPosition, dict(position=1, label="L", price_point="P", perceived_value="V", viability="S"))


# ── 6. Risk ───────────────────────────────────────────────────────────────────

def test_risk_valid():
    scenario = STEEPScenario(
        name="base", social="Stable", technological="Digital", economic="Growth",
        environmental="Green", political="Calm", probability=0.5, impact_score=6,
    )
    sv = SensitivityVariable(variable="Rate", base_value="5%", optimistic_value="3%", stress_value="9%", strategic_sensitivity="high")
    obj = RiskAgentOutput(
        steep_scenarios=[scenario],
        sensitivity_variables=[sv],
        top_risks=["Regulatory"],
        risk_score=40,
        mitigation_priorities=["Lobby"],
    )
    assert obj.risk_score == 40


def test_steep_probability_bounds():
    assert _raises(STEEPScenario, dict(
        name="X", social="S", technological="T", economic="E",
        environmental="N", political="P", probability=1.1, impact_score=5,
    ))


# ── 7. Execution ──────────────────────────────────────────────────────────────

def test_execution_valid():
    bsc = BSCObjective(perspective="financial", objective="Revenue+10%", kpi="Revenue", target="$10M", initiative="Sales push")
    okr = OKR(objective="Launch product", key_results=["Ship v1", "100 users"], timeframe="Q2", owner="CPO")
    obj = ExecutionAgentOutput(
        balanced_scorecard=[bsc],
        okrs=[okr],
        critical_success_factors=["Talent"],
        execution_readiness_score=68,
        quick_wins=["CRM rollout"],
    )
    assert obj.execution_readiness_score == 68


# ── 8. Ethics ─────────────────────────────────────────────────────────────────

def test_ethics_valid():
    si = StakeholderImpact(stakeholder="Employees", impact_type="Positive", severity="Medium", description="Better tools")
    esg = ESGScore(pillar="Governance", score=7.5, rationale="Strong board", evidence_basis="Annual report")
    efa = EthicalFrameworkAssessment(framework="Utilitarian", verdict="Supports", reasoning="Net positive")
    obj = EthicsAgentOutput(
        stakeholder_impacts=[si],
        ethical_frameworks=[efa],
        esg_scores=[esg],
        composite_esg_score=7.5,
        ethical_red_flags=[],
        recommended_safeguards=["Audit"],
        overall_ethical_risk="Low",
        ethics_score=80,
    )
    assert obj.composite_esg_score == 7.5


def test_esg_score_bounds():
    assert _raises(ESGScore, dict(pillar="Environmental", score=10.1, rationale="R", evidence_basis="E"))
    assert not _raises(ESGScore, dict(pillar="Social", score=10.0, rationale="R", evidence_basis="E"))


# ── 9. Finance ────────────────────────────────────────────────────────────────

def _make_cash_flow_years():
    return [CashFlowYear(year=i, revenue=1e6*i, cogs=3e5*i, opex=2e5*i, capex=1e5) for i in range(1, 6)]


def _make_finance_output():
    cfy = _make_cash_flow_years()
    dcf = DCFAnalysis(
        wacc=10.0, terminal_growth_rate=2.0, npv=500_000, irr=25.0,
        payback_period_years=3.0, terminal_value=8_000_000, enterprise_value=9_000_000,
        cash_flows=cfy,
    )
    fr = FundingRound(
        round_name="Series A", amount_raised=2_000_000, pre_money_valuation=8_000_000,
        post_money_valuation=10_000_000, new_shares_issued=250_000, price_per_share=8.0,
        investor_ownership_pct=20.0,
    )
    shareholders = [ShareholderRow(name="Founders", role="Founder", shares=1_000_000, ownership_pct=80.0, ownership_post_pct=64.0)]
    cap = CapTableAnalysis(
        total_shares_pre=1_000_000, total_shares_post=1_250_000,
        shareholders=shareholders, funding_round=fr,
        founder_dilution_pct=16.0, dilution_summary="Founders diluted 16%",
    )
    ue = UnitEconomics(cac=500, ltv=3000, ltv_cac_ratio=6.0, payback_months=8.0, arpu=100, churn_rate_pct=2.0, gross_margin_pct=70.0)
    burn = BurnAnalysis(monthly_burn=100_000, monthly_revenue=80_000, net_burn=20_000, cash_on_hand=500_000, runway_months=25.0, break_even_month=25, burn_multiple=1.5, unit_economics=ue)
    pnl = [PnLStatement(year=i, revenue=1e6, cogs=3e5, gross_profit=7e5, gross_margin_pct=70.0, opex=2e5, ebitda=5e5, depreciation=5e4, ebit=4.5e5, interest_expense=1e4, ebt=4.4e5, tax_rate_pct=25.0, net_income=3.3e5, net_margin_pct=33.0) for i in range(1, 4)]
    bs = [BalanceSheet(year=i, cash=5e5, accounts_receivable=1e5, inventory=0, total_current_assets=6e5, ppe_net=3e5, total_assets=9e5, accounts_payable=5e4, short_term_debt=1e5, total_current_liabilities=1.5e5, long_term_debt=2e5, total_liabilities=3.5e5, equity=5.5e5) for i in range(1, 4)]
    cf = [CashFlowStatement(year=i, cfo=4e5, cfi=-1e5, cff=-5e4, net_change_in_cash=2.5e5, ending_cash=5e5) for i in range(1, 4)]
    stmts = FinancialStatements(pnl=pnl, balance_sheet=bs, cash_flow=cf)
    comps = [CompComp(company="Peer A", ev_ebitda=12.0, ev_revenue=3.0, pe_ratio=20.0, price_to_book=2.5)]
    val = ValuationMultiples(subject_ev_ebitda=10.0, subject_ev_revenue=2.5, subject_pe=18.0, comparable_companies=comps, implied_valuation_low=5e6, implied_valuation_mid=6e6, implied_valuation_high=7e6, valuation_method_used="EV/EBITDA", valuation_commentary="Fairly valued")
    return FinanceAgentOutput(dcf=dcf, cap_table=cap, burn=burn, statements=stmts, valuation=val, financial_fit_score=72, go_signal="Go", cfo_summary="Strong outlook.")


def test_finance_valid():
    obj = _make_finance_output()
    assert obj.financial_fit_score == 72
    assert obj.go_signal == "Go"
    assert len(obj.dcf.cash_flows) == 5


def test_cash_flow_year_computed_properties():
    cfy = CashFlowYear(year=1, revenue=1_000_000, cogs=300_000, opex=200_000, capex=50_000)
    assert cfy.gross_profit == 700_000
    assert cfy.ebitda == 500_000
    assert cfy.fcf == 450_000


def test_finance_invalid_go_signal():
    assert _raises(FinanceAgentOutput, {**_make_finance_output().model_dump(), "go_signal": "Maybe"})


# ── 10. Synthesis ─────────────────────────────────────────────────────────────

def test_synthesis_valid():
    opt = StrategicOption(
        option="Expand", rationale="Growth opportunity", strategic_fit_score=80,
        risk_score=30, feasibility_score=70, overall_score=75,
        supporting_frameworks=["Ansoff"], conflicting_signals=[],
    )
    branch = ScenarioBranch(scenario="optimistic", recommended_option="Expand", expected_outcome="$10M revenue", key_assumptions=["Market grows"])
    obj = SynthesisOutput(
        strategic_options=[opt],
        ranked_recommendation=["Expand"],
        scenario_branches=[branch],
        inter_agent_conflicts=[],
        conflict_resolutions=[],
        overall_strategic_fit_score=77,
        executive_summary="Strong position.",
        board_narrative="Board should proceed.",
    )
    assert obj.overall_strategic_fit_score == 77


def test_synthesis_score_out_of_range():
    assert _raises(StrategicOption, dict(
        option="X", rationale="Y", strategic_fit_score=101,
        risk_score=50, feasibility_score=50, overall_score=50,
        supporting_frameworks=[], conflicting_signals=[],
    ))


# ── Runner ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_external_valid, test_external_score_out_of_range, test_porter_force_score_bounds,
        test_internal_valid, test_internal_mckinsey_score_bounds,
        test_position_valid, test_swot_impact_score_bounds,
        test_competitive_valid, test_game_theory_payoff_bounds,
        test_formulation_valid, test_strategy_clock_position_bounds,
        test_risk_valid, test_steep_probability_bounds,
        test_execution_valid,
        test_ethics_valid, test_esg_score_bounds,
        test_finance_valid, test_cash_flow_year_computed_properties, test_finance_invalid_go_signal,
        test_synthesis_valid, test_synthesis_score_out_of_range,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {t.__name__}: {e}")
    print(f"\n{'─'*50}")
    print(f"Results: {passed}/{len(tests)} passed")
