"""
finance_math.py
Pure deterministic financial computations — no LLM.
All functions take raw numbers, return raw numbers.
"""
from __future__ import annotations


# ── DCF ───────────────────────────────────────────────────────────────────────

def compute_npv(fcfs: list[float], wacc_pct: float, initial_investment: float) -> float:
    """NPV = Σ FCF_t/(1+r)^t - I₀"""
    r = wacc_pct / 100
    pv = sum(cf / (1 + r) ** (t + 1) for t, cf in enumerate(fcfs))
    return round(pv - initial_investment, 2)


def compute_irr(fcfs: list[float], initial_investment: float, max_iter: int = 1000) -> float:
    """Newton-Raphson IRR. Returns % or -999.0 if no convergence."""
    flows = [-initial_investment] + fcfs
    r = 0.15
    for _ in range(max_iter):
        npv   = sum(cf / (1 + r) ** t for t, cf in enumerate(flows))
        d_npv = sum(-t * cf / (1 + r) ** (t + 1) for t, cf in enumerate(flows))
        if abs(d_npv) < 1e-12:
            break
        r -= npv / d_npv
        if r <= -1:
            return -999.0
    return round(r * 100, 2)


def compute_payback(fcfs: list[float], initial_investment: float) -> float:
    """Payback period in years with linear interpolation within the recovery year."""
    cumulative = 0.0
    for i, cf in enumerate(fcfs):
        prev = cumulative
        cumulative += cf
        if cumulative >= initial_investment:
            fraction = (initial_investment - prev) / cf
            return round(i + fraction, 2)
    return float("inf")


def compute_terminal_value(final_fcf: float, wacc_pct: float, growth_pct: float) -> float:
    """Gordon Growth Model terminal value."""
    r, g = wacc_pct / 100, growth_pct / 100
    if r <= g:
        return float("inf")
    return round(final_fcf * (1 + g) / (r - g), 2)


def compute_enterprise_value(fcfs: list[float], wacc_pct: float,
                              growth_pct: float, initial_investment: float) -> dict:
    r = wacc_pct / 100
    pv_fcfs = sum(cf / (1 + r) ** (t + 1) for t, cf in enumerate(fcfs))
    tv = compute_terminal_value(fcfs[-1], wacc_pct, growth_pct)
    pv_tv = tv / (1 + r) ** len(fcfs)
    ev = pv_fcfs + pv_tv
    npv = ev - initial_investment
    return {
        "npv": round(npv, 2),
        "terminal_value": round(tv, 2),
        "enterprise_value": round(ev, 2),
    }


# ── Cap Table ─────────────────────────────────────────────────────────────────

def compute_dilution(
    existing_shares: int,
    new_shares: int,
    founder_pre_shares: int,
) -> dict:
    """Returns post-money ownership percentages."""
    total_post = existing_shares + new_shares
    founder_pre_pct  = founder_pre_shares / existing_shares * 100
    founder_post_pct = founder_pre_shares / total_post * 100
    dilution = founder_pre_pct - founder_post_pct
    return {
        "total_shares_post": total_post,
        "founder_pre_pct": round(founder_pre_pct, 2),
        "founder_post_pct": round(founder_post_pct, 2),
        "founder_dilution_pct": round(dilution, 2),
        "new_investor_pct": round(new_shares / total_post * 100, 2),
    }


def compute_price_per_share(pre_money_valuation: float, total_shares_pre: int) -> float:
    return round(pre_money_valuation / total_shares_pre, 4)


def compute_new_shares_issued(amount_raised: float, price_per_share: float) -> int:
    return int(amount_raised / price_per_share)


# ── Unit Economics ────────────────────────────────────────────────────────────

def compute_ltv(arpu: float, gross_margin_pct: float, monthly_churn_pct: float) -> float:
    """LTV = (ARPU × GM%) / Monthly Churn"""
    if monthly_churn_pct <= 0:
        return float("inf")
    return round((arpu * gross_margin_pct / 100) / (monthly_churn_pct / 100), 2)


def compute_ltv_cac_ratio(ltv: float, cac: float) -> float:
    if cac <= 0:
        return 0.0
    return round(ltv / cac, 2)


def compute_cac_payback_months(cac: float, arpu: float, gross_margin_pct: float) -> float:
    monthly_gm = arpu * gross_margin_pct / 100
    if monthly_gm <= 0:
        return float("inf")
    return round(cac / monthly_gm, 1)


def compute_runway(cash_on_hand: float, net_burn_monthly: float) -> float:
    if net_burn_monthly <= 0:
        return 999  # profitable; float('inf') breaks JSON serialization
    return round(cash_on_hand / net_burn_monthly, 1)


def compute_burn_multiple(net_burn: float, net_new_arr: float) -> float:
    """Burn multiple = net burn / net new ARR. <1 = efficient, >2 = concerning."""
    if net_new_arr <= 0:
        return float("inf")
    return round(net_burn / net_new_arr, 2)


# ── Financial Statements ──────────────────────────────────────────────────────

def build_pnl(
    revenue: float,
    cogs_pct: float,
    opex: float,
    depreciation: float,
    interest_expense: float,
    tax_rate_pct: float,
    year: int,
) -> dict:
    cogs          = revenue * cogs_pct / 100
    gross_profit  = revenue - cogs
    gross_margin  = gross_profit / revenue * 100 if revenue else 0
    ebitda        = gross_profit - opex
    ebit          = ebitda - depreciation
    ebt           = ebit - interest_expense
    net_income    = ebt * (1 - tax_rate_pct / 100)
    net_margin    = net_income / revenue * 100 if revenue else 0
    return {
        "year": year, "revenue": round(revenue, 2), "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2), "gross_margin_pct": round(gross_margin, 2),
        "opex": round(opex, 2), "ebitda": round(ebitda, 2),
        "depreciation": round(depreciation, 2), "ebit": round(ebit, 2),
        "interest_expense": round(interest_expense, 2), "ebt": round(ebt, 2),
        "tax_rate_pct": tax_rate_pct, "net_income": round(net_income, 2),
        "net_margin_pct": round(net_margin, 2),
    }


# ── Valuation Multiples ───────────────────────────────────────────────────────

def compute_implied_ev(ebitda: float, multiples: list[float]) -> dict:
    evs = [ebitda * m for m in multiples]
    return {
        "low":  round(min(evs), 2),
        "mid":  round(sum(evs) / len(evs), 2),
        "high": round(max(evs), 2),
    }
