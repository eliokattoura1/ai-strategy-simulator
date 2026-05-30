"""
reports/data_quality.py
Annotate simulation output with per-field data provenance flags.

Three provenance categories
  verified / computed  — deterministically derived by finance_math.py
  verified / <source>  — value matches a real market data feed within tolerance
  unverified / AI est  — LLM assumption with no external data backing
"""
from __future__ import annotations
import copy


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _within_pct(a, b, pct: float = 15.0) -> bool:
    """True when a and b agree within pct% of each other."""
    fa, fb = _safe_float(a), _safe_float(b)
    if fa is None or fb is None:
        return False
    if fb == 0:
        return fa == 0
    return abs(fa - fb) / abs(fb) <= pct / 100


def _tag(verified: bool, source: str) -> dict:
    return {"verified": verified, "source": source}


_COMPUTED = _tag(True,  "computed")
_AI       = _tag(False, "AI estimate")

def _market(source_name: str) -> dict:
    return _tag(True, source_name)


# ── Main annotator ────────────────────────────────────────────────────────────

def annotate_output(output: dict, market_data: dict | None) -> dict:
    """
    Return a shallow copy of *output* with a '_data_quality' key added.

    '_data_quality' shape:
      fields:  dict[str, {verified: bool, source: str}]
      summary: {total_fields, verified_count, estimated_count}
    """
    output = dict(output)
    md    = market_data or {}
    yahoo = md.get("yahoo") or {}
    av    = md.get("alpha_vantage") or {}
    wb    = md.get("world_bank") or {}

    # Real-world reference values pulled from market feeds
    rev_real    = _safe_float(yahoo.get("revenue_ttm") or av.get("revenue_ttm"))
    gm_real     = _safe_float(yahoo.get("gross_margin"))           # 0–1 fraction
    pe_real     = _safe_float(yahoo.get("pe_ratio") or av.get("pe_ratio"))
    mc_real     = _safe_float(yahoo.get("market_cap") or av.get("market_capitalization"))
    yahoo_src   = "Yahoo Finance" if yahoo.get("revenue_ttm") else "Alpha Vantage"

    fin  = output.get("finance") or {}
    dcf  = fin.get("dcf") or {}
    cap  = fin.get("cap_table") or {}
    rnd  = cap.get("funding_round") or {}
    burn = fin.get("burn") or {}
    ue   = burn.get("unit_economics") or {}
    val  = fin.get("valuation") or {}
    bm   = fin.get("banking_metrics")

    fields: dict[str, dict] = {}

    # ── DCF — computed outputs ─────────────────────────────────────────────────
    fields["finance.dcf.npv"]                  = _COMPUTED
    fields["finance.dcf.irr"]                  = _COMPUTED
    fields["finance.dcf.payback_period_years"] = _COMPUTED
    fields["finance.dcf.terminal_value"]       = _COMPUTED
    fields["finance.dcf.enterprise_value"]     = _COMPUTED

    # DCF — LLM assumptions
    fields["finance.dcf.wacc"]                 = _AI
    fields["finance.dcf.terminal_growth_rate"] = _AI

    # Cash-flow assumptions — year-1 revenue checked against real TTM
    for i, cf in enumerate(dcf.get("cash_flows") or []):
        pre = f"finance.dcf.cash_flows[{i}]"
        if i == 0 and rev_real is not None and _within_pct(cf.get("revenue"), rev_real):
            fields[f"{pre}.revenue"] = _market(yahoo_src)
        else:
            fields[f"{pre}.revenue"] = _AI
        fields[f"{pre}.cogs"]  = _AI
        fields[f"{pre}.opex"]  = _AI
        fields[f"{pre}.capex"] = _AI

    # ── Cap Table — computed derivations ───────────────────────────────────────
    fields["finance.cap_table.total_shares_post"]                    = _COMPUTED
    fields["finance.cap_table.founder_dilution_pct"]                 = _COMPUTED
    fields["finance.cap_table.funding_round.price_per_share"]        = _COMPUTED
    fields["finance.cap_table.funding_round.new_shares_issued"]      = _COMPUTED
    fields["finance.cap_table.funding_round.post_money_valuation"]   = _COMPUTED
    fields["finance.cap_table.funding_round.investor_ownership_pct"] = _COMPUTED

    # Pre-money valuation may match real market cap
    pre_money = _safe_float(rnd.get("pre_money_valuation"))
    if mc_real is not None and pre_money is not None and _within_pct(pre_money, mc_real):
        mc_src = "Yahoo Finance" if yahoo.get("market_cap") else "Alpha Vantage"
        fields["finance.cap_table.funding_round.pre_money_valuation"] = _market(mc_src)
    else:
        fields["finance.cap_table.funding_round.pre_money_valuation"] = _AI

    fields["finance.cap_table.funding_round.amount_raised"] = _AI
    fields["finance.cap_table.total_shares_pre"]            = _AI

    # ── Burn & Unit Economics ─────────────────────────────────────────────────
    fields["finance.burn.net_burn"]                         = _COMPUTED
    fields["finance.burn.runway_months"]                    = _COMPUTED
    fields["finance.burn.burn_multiple"]                    = _COMPUTED
    fields["finance.burn.unit_economics.ltv"]               = _COMPUTED
    fields["finance.burn.unit_economics.ltv_cac_ratio"]     = _COMPUTED
    fields["finance.burn.unit_economics.payback_months"]    = _COMPUTED

    # Gross margin — check against Yahoo Finance (stored as 0–1 fraction)
    gm_llm = _safe_float(ue.get("gross_margin_pct"))
    if gm_real is not None and gm_llm is not None and _within_pct(gm_llm, gm_real * 100):
        fields["finance.burn.unit_economics.gross_margin_pct"] = _market("Yahoo Finance")
    else:
        fields["finance.burn.unit_economics.gross_margin_pct"] = _AI

    # Monthly revenue — annualise and compare to real TTM
    monthly_rev = _safe_float(burn.get("monthly_revenue"))
    if rev_real is not None and monthly_rev is not None and _within_pct(monthly_rev * 12, rev_real):
        fields["finance.burn.monthly_revenue"] = _market(yahoo_src)
    else:
        fields["finance.burn.monthly_revenue"] = _AI

    fields["finance.burn.monthly_burn"]                     = _AI
    fields["finance.burn.cash_on_hand"]                     = _AI
    fields["finance.burn.unit_economics.cac"]               = _AI
    fields["finance.burn.unit_economics.arpu"]              = _AI
    fields["finance.burn.unit_economics.churn_rate_pct"]    = _AI

    # ── Valuation ─────────────────────────────────────────────────────────────
    fields["finance.valuation.implied_valuation_low"]  = _COMPUTED
    fields["finance.valuation.implied_valuation_mid"]  = _COMPUTED
    fields["finance.valuation.implied_valuation_high"] = _COMPUTED
    fields["finance.valuation.subject_ev_ebitda"]      = _COMPUTED
    fields["finance.valuation.subject_ev_revenue"]     = _COMPUTED

    # Subject P/E — computed from DCF EV, but cross-check against real P/E
    subj_pe = _safe_float(val.get("subject_pe"))
    if pe_real is not None and subj_pe is not None and _within_pct(subj_pe, pe_real):
        pe_src = "Yahoo Finance" if yahoo.get("pe_ratio") else "Alpha Vantage"
        fields["finance.valuation.subject_pe"] = _market(pe_src)
    else:
        fields["finance.valuation.subject_pe"] = _COMPUTED

    fields["finance.valuation.comparable_companies"] = _AI
    fields["finance.valuation.valuation_commentary"]  = _AI

    # ── Banking metrics — all LLM-generated assumptions ───────────────────────
    if bm:
        for metric in ("nim_pct", "roa_pct", "roe_pct", "npl_ratio_pct",
                       "car_pct", "cost_to_income_pct"):
            fields[f"finance.banking_metrics.{metric}"] = _AI

    # ── Top-level LLM outputs ─────────────────────────────────────────────────
    fields["finance.financial_fit_score"] = _AI
    fields["finance.go_signal"]           = _AI
    fields["finance.cfo_summary"]         = _AI

    # ── World Bank macro — mark real figures where data was returned ───────────
    wb_indicator_map = {
        "gdp_growth_pct":    "World Bank",
        "inflation_pct":     "World Bank",
        "unemployment_pct":  "World Bank",
        "gdp_per_capita_usd":"World Bank",
        "govt_debt_pct_gdp": "World Bank",
        "fdi_pct_gdp":       "World Bank",
    }
    for k, src in wb_indicator_map.items():
        if wb.get(k) is not None:
            fields[f"market_data.world_bank.{k}"] = _market(src)

    # ── Summary ───────────────────────────────────────────────────────────────
    total     = len(fields)
    verified  = sum(1 for v in fields.values() if v["verified"])
    estimated = total - verified

    output["_data_quality"] = {
        "fields":  fields,
        "summary": {
            "total_fields":    total,
            "verified_count":  verified,
            "estimated_count": estimated,
        },
    }
    return output
