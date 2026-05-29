"""
test_finance_math.py
Run: python tests/test_finance_math.py
Tests all deterministic financial functions — no API key required.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.finance_math import (
    compute_npv, compute_irr, compute_payback, compute_enterprise_value,
    compute_dilution, compute_price_per_share, compute_new_shares_issued,
    compute_ltv, compute_ltv_cac_ratio, compute_cac_payback_months,
    compute_runway, compute_burn_multiple, build_pnl, compute_implied_ev,
)


def test_dcf():
    fcfs = [200_000, 300_000, 400_000, 500_000, 600_000]
    invest = 1_000_000

    npv = compute_npv(fcfs, 10.0, invest)
    assert npv > 0, f"NPV should be positive: {npv}"

    irr = compute_irr(fcfs, invest)
    assert 20 < irr < 40, f"IRR out of range: {irr}"

    pb = compute_payback(fcfs, invest)
    assert 2 < pb < 4, f"Payback out of range: {pb}"

    ev = compute_enterprise_value(fcfs, 10.0, 2.0, invest)
    assert ev["enterprise_value"] > invest
    assert ev["terminal_value"] > 0

    print(f"  DCF: NPV=${npv:,.0f}  IRR={irr:.1f}%  Payback={pb:.1f}yr  EV=${ev['enterprise_value']:,.0f}")


def test_dcf_negative_npv():
    fcfs = [50_000] * 5
    npv = compute_npv(fcfs, 10.0, 1_000_000)
    assert npv < 0
    print(f"  DCF negative NPV: {npv:,.0f} ✓")


def test_cap_table():
    total_pre = 10_000_000
    founder_shares = 6_000_000
    pre_money = 5_000_000
    amount = 2_000_000

    pps = compute_price_per_share(pre_money, total_pre)
    assert abs(pps - 0.5) < 0.01, f"PPS wrong: {pps}"

    new_shares = compute_new_shares_issued(amount, pps)
    assert new_shares == 4_000_000

    dil = compute_dilution(total_pre, new_shares, founder_shares)
    assert dil["founder_pre_pct"] == 60.0
    assert dil["founder_post_pct"] < 60.0
    assert dil["founder_dilution_pct"] > 0

    print(f"  Cap Table: PPS=${pps:.2f}  New shares={new_shares:,}  Founder dilution={dil['founder_dilution_pct']:.1f}%")


def test_unit_economics():
    # SaaS example: $500 ARPU/mo, 70% GM, 2% monthly churn
    ltv = compute_ltv(arpu=500, gross_margin_pct=70, monthly_churn_pct=2.0)
    assert ltv == 17_500.0, f"LTV wrong: {ltv}"

    cac = 3_000
    ratio = compute_ltv_cac_ratio(ltv, cac)
    assert abs(ratio - 5.83) < 0.05, f"LTV/CAC wrong: {ratio}"

    payback = compute_cac_payback_months(cac, 500, 70)
    assert abs(payback - 8.6) < 0.2, f"Payback months wrong: {payback}"

    runway = compute_runway(cash_on_hand=500_000, net_burn_monthly=25_000)
    assert runway == 20.0

    bm = compute_burn_multiple(net_burn=100_000, net_new_arr=200_000)
    assert bm == 0.5

    print(f"  Unit Econ: LTV=${ltv:,.0f}  LTV/CAC={ratio:.1f}x  Payback={payback:.1f}mo  Runway={runway:.0f}mo  BM={bm:.1f}x")


def test_pnl():
    pnl = build_pnl(
        revenue=1_000_000,
        cogs_pct=35.0,
        opex=300_000,
        depreciation=50_000,
        interest_expense=20_000,
        tax_rate_pct=25.0,
        year=1,
    )
    assert pnl["gross_margin_pct"] == 65.0
    assert pnl["ebitda"] == 350_000
    assert pnl["ebit"] == 300_000
    # EBT = EBIT - interest = 300k - 20k = 280k; NI = 280k * 0.75 = 210k
    assert pnl["net_income"] == 210_000
    assert abs(pnl["net_margin_pct"] - 21.0) < 0.01

    print(f"  P&L: GM={pnl['gross_margin_pct']}%  EBITDA=${pnl['ebitda']:,.0f}  NI=${pnl['net_income']:,.0f}  NM={pnl['net_margin_pct']:.2f}%")


def test_valuation_multiples():
    # EV/EBITDA comps: 12x, 15x, 18x — subject EBITDA = $5M
    ebitda = 5_000_000
    multiples = [12.0, 15.0, 18.0]
    implied = compute_implied_ev(ebitda, multiples)

    assert implied["low"]  == 60_000_000
    assert implied["mid"]  == 75_000_000
    assert implied["high"] == 90_000_000

    print(f"  Valuation: Low=${implied['low']/1e6:.0f}M  Mid=${implied['mid']/1e6:.0f}M  High=${implied['high']/1e6:.0f}M")


if __name__ == "__main__":
    tests = [test_dcf, test_dcf_negative_npv, test_cap_table, test_unit_economics, test_pnl, test_valuation_multiples]
    passed = 0
    for t in tests:
        name = t.__name__.replace("test_", "").upper()
        try:
            print(f"\n[{name}]")
            t()
            print(f"  ✓ passed")
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")

    print(f"\n{'─'*40}")
    print(f"Results: {passed}/{len(tests)} passed")
