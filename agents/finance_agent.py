from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AGENT_MODEL, MAX_TOKENS, TEMPERATURE
from schemas.finance_schema import (
    FinanceAgentOutput, DCFAnalysis, CashFlowYear,
    CapTableAnalysis, ShareholderRow, FundingRound,
    BurnAnalysis, UnitEconomics,
    FinancialStatements, PnLStatement, BalanceSheet, CashFlowStatement,
    ValuationMultiples, CompComp,
)
from schemas.formulation_schema import FormulationAgentOutput
from schemas.execution_schema import ExecutionAgentOutput
from tools.finance_math import (
    compute_npv, compute_irr, compute_payback, compute_enterprise_value,
    compute_dilution, compute_price_per_share, compute_new_shares_issued,
    compute_ltv, compute_ltv_cac_ratio, compute_cac_payback_months,
    compute_runway, compute_burn_multiple, build_pnl, compute_implied_ev,
)
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ── System Prompt ──────────────────────────────────────────────────────────────

FINANCE_SYSTEM_PROMPT = """You are a CFO-level financial analyst embedded in a multi-agent strategy simulator.

Given a company, industry, and recommended strategy, you produce raw financial assumptions across 5 domains.
The system will compute all derived metrics (NPV, IRR, LTV/CAC, etc.) from your assumptions — do NOT compute them yourself.

Return ONLY a valid JSON object with EXACTLY this structure:

{
  "dcf": {
    "wacc": <float %>,
    "terminal_growth_rate": <float %>,
    "initial_investment": <float USD>,
    "cash_flows": [
      {"year":1,"revenue":<float>,"cogs":<float>,"opex":<float>,"capex":<float>},
      {"year":2,"revenue":<float>,"cogs":<float>,"opex":<float>,"capex":<float>},
      {"year":3,"revenue":<float>,"cogs":<float>,"opex":<float>,"capex":<float>},
      {"year":4,"revenue":<float>,"cogs":<float>,"opex":<float>,"capex":<float>},
      {"year":5,"revenue":<float>,"cogs":<float>,"opex":<float>,"capex":<float>}
    ]
  },
  "cap_table": {
    "total_shares_pre": <int>,
    "shareholders": [
      {"name":"Founders","role":"Founder","shares":<int>},
      {"name":"Seed Investors","role":"Investor","shares":<int>},
      {"name":"ESOP","role":"ESOP","shares":<int>}
    ],
    "funding_round": {
      "round_name": "Series A|Series B|...",
      "amount_raised": <float USD>,
      "pre_money_valuation": <float USD>
    }
  },
  "burn": {
    "monthly_burn": <float USD>,
    "monthly_revenue": <float USD>,
    "cash_on_hand": <float USD>,
    "unit_economics": {
      "cac": <float USD>,
      "arpu": <float USD/month>,
      "churn_rate_pct": <float monthly %>,
      "gross_margin_pct": <float %>
    }
  },
  "statements": {
    "years": [
      {
        "year": <int>,
        "revenue": <float>,
        "cogs_pct": <float %>,
        "opex": <float>,
        "depreciation": <float>,
        "interest_expense": <float>,
        "tax_rate_pct": <float %>,
        "cash": <float>,
        "accounts_receivable": <float>,
        "inventory": <float>,
        "ppe_net": <float>,
        "accounts_payable": <float>,
        "short_term_debt": <float>,
        "long_term_debt": <float>,
        "equity": <float>,
        "cfo": <float>,
        "cfi": <float>,
        "cff": <float>
      }
    ]
  },
  "valuation": {
    "comparable_companies": [
      {"company":"<name>","ev_ebitda":<float>,"ev_revenue":<float>,"pe_ratio":<float>,"price_to_book":<float>},
      {"company":"<name>","ev_ebitda":<float>,"ev_revenue":<float>,"pe_ratio":<float>,"price_to_book":<float>},
      {"company":"<name>","ev_ebitda":<float>,"ev_revenue":<float>,"pe_ratio":<float>,"price_to_book":<float>}
    ],
    "valuation_method_used": "EV/EBITDA|EV/Revenue|P/E|Blended",
    "valuation_commentary": "<string max 60 words>"
  },
  "financial_fit_score": <int 0-100>,
  "go_signal": "Go|Conditional Go|No Go",
  "cfo_summary": "<string 80 words max — CFO board voice>"
}

Scoring guide for financial_fit_score:
80-100: Strong positive NPV, IRR > WACC, LTV/CAC > 3, runway > 18mo
50-79:  Moderate returns, viable with conditions
20-49:  Weak returns, significant financial risk
0-19:   Negative NPV, no recovery path visible

No markdown. No explanation. Raw JSON only."""


# ── Main Agent Function (matches execution_agent.py pattern exactly) ──────────

async def run_finance_agent(
    company: str,
    industry: str,
    strategic_question: str,
    formulation_output: FormulationAgentOutput,
    execution_output: ExecutionAgentOutput,
    context: str = None,
    market_data: str = None,
) -> FinanceAgentOutput:

    if context:
        print(f"[FinanceAgent] RAG context received ({len(context)} chars): {context[:200]!r}")
    else:
        print("[FinanceAgent] No RAG context provided")

    system_content = FINANCE_SYSTEM_PROMPT
    if context:
        system_content = (
            f"REAL COMPANY DATA (use this in your analysis):\n{context}\n\n---\n\n"
            f"Prioritize this data over general knowledge.\n\n{system_content}"
        )
    if market_data:
        system_content = (
            f"VERIFIED FINANCIAL DATA FROM YAHOO FINANCE & "
            f"ALPHA VANTAGE (use these exact figures — do NOT "
            f"invent alternative numbers):\n{market_data}"
            f"\n\n---\n\n{system_content}"
        )

    prompt = f"""
Company: {company}
Industry: {industry}
Strategic Question: {strategic_question}

Recommended Strategy: {formulation_output.recommended_strategy}
Formulation Confidence Score: {formulation_output.formulation_confidence_score}
Critical Success Factors: {execution_output.critical_success_factors}
Execution Readiness Score: {execution_output.execution_readiness_score}

Produce financial assumptions for all 5 domains. Return structured JSON only.
"""

    response = await client.chat.completions.create(
        model=AGENT_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user",   "content": prompt},
        ],
    )

    raw = json.loads(response.choices[0].message.content)

    try:
        return _build_output(raw)
    except Exception as e:
        print("FinanceAgent raw JSON:", json.dumps(raw, indent=2))
        raise


# ── Output Builder — LLM assumptions + deterministic math ────────────────────

def _build_output(raw: dict) -> FinanceAgentOutput:
    # ── DCF ──────────────────────────────────────────────────────────────────
    d = raw["dcf"]
    cf_objects = [CashFlowYear(**y) for y in d["cash_flows"]]
    fcfs = [y.fcf for y in cf_objects]
    invest = d["initial_investment"]
    ev_data = compute_enterprise_value(fcfs, d["wacc"], d["terminal_growth_rate"], invest)

    dcf = DCFAnalysis(
        wacc=d["wacc"],
        terminal_growth_rate=d["terminal_growth_rate"],
        npv=ev_data["npv"],
        irr=compute_irr(fcfs, invest),
        payback_period_years=compute_payback(fcfs, invest),
        terminal_value=ev_data["terminal_value"],
        enterprise_value=ev_data["enterprise_value"],
        cash_flows=cf_objects,
    )

    # ── Cap Table ─────────────────────────────────────────────────────────────
    ct = raw["cap_table"]
    fr_raw = ct["funding_round"]
    total_pre = ct["total_shares_pre"]
    pps = compute_price_per_share(fr_raw["pre_money_valuation"], total_pre)
    new_shares = compute_new_shares_issued(fr_raw["amount_raised"], pps)
    total_post = total_pre + new_shares
    post_money = fr_raw["pre_money_valuation"] + fr_raw["amount_raised"]

    founder_shares = next(
        (s["shares"] for s in ct["shareholders"] if s["role"] == "Founder"), 0
    )
    dil = compute_dilution(total_pre, new_shares, founder_shares)

    shareholders = [
        ShareholderRow(
            name=s["name"],
            role=s["role"],
            shares=s["shares"],
            ownership_pct=round(s["shares"] / total_pre * 100, 2),
            ownership_post_pct=round(s["shares"] / total_post * 100, 2),
        )
        for s in ct["shareholders"]
    ]

    cap_table = CapTableAnalysis(
        total_shares_pre=total_pre,
        total_shares_post=total_post,
        shareholders=shareholders,
        funding_round=FundingRound(
            round_name=fr_raw["round_name"],
            amount_raised=fr_raw["amount_raised"],
            pre_money_valuation=fr_raw["pre_money_valuation"],
            post_money_valuation=post_money,
            new_shares_issued=new_shares,
            price_per_share=pps,
            investor_ownership_pct=round(new_shares / total_post * 100, 2),
        ),
        founder_dilution_pct=dil["founder_dilution_pct"],
        dilution_summary=(
            f"Founders diluted from {dil['founder_pre_pct']}% to "
            f"{dil['founder_post_pct']}% post {fr_raw['round_name']}. "
            f"New investors own {dil['new_investor_pct']}%."
        ),
    )

    # ── Burn + Unit Economics ─────────────────────────────────────────────────
    b = raw["burn"]
    ue_raw = b["unit_economics"]
    ltv = compute_ltv(ue_raw["arpu"], ue_raw["gross_margin_pct"], ue_raw["churn_rate_pct"])
    net_burn = max(b["monthly_burn"] - b["monthly_revenue"], 0)
    # Estimate net new ARR from monthly revenue growth (simple proxy: 10% MoM)
    net_new_arr = b["monthly_revenue"] * 0.10 * 12

    burn = BurnAnalysis(
        monthly_burn=b["monthly_burn"],
        monthly_revenue=b["monthly_revenue"],
        net_burn=net_burn,
        cash_on_hand=b["cash_on_hand"],
        runway_months=compute_runway(b["cash_on_hand"], net_burn),
        break_even_month=int(b["cash_on_hand"] / max(net_burn, 1)),
        burn_multiple=compute_burn_multiple(net_burn, net_new_arr),
        unit_economics=UnitEconomics(
            cac=ue_raw["cac"],
            ltv=ltv,
            ltv_cac_ratio=compute_ltv_cac_ratio(ltv, ue_raw["cac"]),
            payback_months=compute_cac_payback_months(
                ue_raw["cac"], ue_raw["arpu"], ue_raw["gross_margin_pct"]
            ),
            arpu=ue_raw["arpu"],
            churn_rate_pct=ue_raw["churn_rate_pct"],
            gross_margin_pct=ue_raw["gross_margin_pct"],
        ),
    )

    # ── 3-Statement Model ─────────────────────────────────────────────────────
    pnl_list, bs_list, cf_list = [], [], []
    for yr in raw["statements"]["years"]:
        pnl_dict = build_pnl(
            yr["revenue"], yr["cogs_pct"], yr["opex"],
            yr["depreciation"], yr["interest_expense"], yr["tax_rate_pct"], yr["year"],
        )
        pnl_list.append(PnLStatement(**pnl_dict))

        total_current = yr["cash"] + yr["accounts_receivable"] + yr["inventory"]
        total_assets = total_current + yr["ppe_net"]
        total_current_liab = yr["accounts_payable"] + yr["short_term_debt"]
        total_liab = total_current_liab + yr["long_term_debt"]

        bs_list.append(BalanceSheet(
            year=yr["year"],
            cash=yr["cash"],
            accounts_receivable=yr["accounts_receivable"],
            inventory=yr["inventory"],
            total_current_assets=total_current,
            ppe_net=yr["ppe_net"],
            total_assets=total_assets,
            accounts_payable=yr["accounts_payable"],
            short_term_debt=yr["short_term_debt"],
            total_current_liabilities=total_current_liab,
            long_term_debt=yr["long_term_debt"],
            total_liabilities=total_liab,
            equity=yr["equity"],
        ))

        net_change = yr["cfo"] + yr["cfi"] + yr["cff"]
        cf_list.append(CashFlowStatement(
            year=yr["year"],
            cfo=yr["cfo"],
            cfi=yr["cfi"],
            cff=yr["cff"],
            net_change_in_cash=net_change,
            ending_cash=yr["cash"],
        ))

    statements = FinancialStatements(pnl=pnl_list, balance_sheet=bs_list, cash_flow=cf_list)

    # ── Valuation Multiples ───────────────────────────────────────────────────
    v = raw["valuation"]
    comps = [CompComp(**c) for c in v["comparable_companies"]]
    ebitda_year3 = pnl_list[2].ebitda if len(pnl_list) >= 3 else pnl_list[-1].ebitda
    ev_multiples = [c.ev_ebitda for c in comps]
    implied = compute_implied_ev(ebitda_year3, ev_multiples)

    # Subject company multiples from its own DCF-derived EV
    subj_ev = dcf.enterprise_value
    subj_revenue_y3 = cf_objects[2].revenue if len(cf_objects) >= 3 else cf_objects[-1].revenue
    subj_ebitda_y3 = ebitda_year3

    valuation = ValuationMultiples(
        subject_ev_ebitda=round(subj_ev / subj_ebitda_y3, 2) if subj_ebitda_y3 else 0,
        subject_ev_revenue=round(subj_ev / subj_revenue_y3, 2) if subj_revenue_y3 else 0,
        subject_pe=round(subj_ev / max(pnl_list[2].net_income, 1), 2) if len(pnl_list) >= 3 else 0,
        comparable_companies=comps,
        implied_valuation_low=implied["low"],
        implied_valuation_mid=implied["mid"],
        implied_valuation_high=implied["high"],
        valuation_method_used=v["valuation_method_used"],
        valuation_commentary=v["valuation_commentary"],
    )

    return FinanceAgentOutput(
        dcf=dcf,
        cap_table=cap_table,
        burn=burn,
        statements=statements,
        valuation=valuation,
        financial_fit_score=raw["financial_fit_score"],
        go_signal=raw["go_signal"],
        cfo_summary=raw["cfo_summary"],
    )
