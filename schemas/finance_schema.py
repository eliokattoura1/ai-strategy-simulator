from pydantic import BaseModel
from typing import Literal, Optional


# ── 1. DCF / NPV / IRR ────────────────────────────────────────────────────────

class CashFlowYear(BaseModel):
    year: int
    revenue: float
    cogs: float
    opex: float
    capex: float = 0.0

    @property
    def gross_profit(self) -> float:
        return self.revenue - self.cogs

    @property
    def ebitda(self) -> float:
        return self.gross_profit - self.opex

    @property
    def fcf(self) -> float:
        return self.ebitda - self.capex


class DCFAnalysis(BaseModel):
    wacc: float                        # %
    terminal_growth_rate: float        # %
    npv: float                         # USD — computed, not from LLM
    irr: float                         # % — computed
    payback_period_years: float        # computed
    terminal_value: float              # USD — computed
    enterprise_value: float            # NPV + terminal value
    cash_flows: list[CashFlowYear]     # 5 years from LLM


# ── 2. Cap Table + Equity Dilution ────────────────────────────────────────────

class ShareholderRow(BaseModel):
    name: str
    role: Literal["Founder", "Investor", "ESOP", "Advisor", "Other"]
    shares: int
    ownership_pct: float               # pre-money
    ownership_post_pct: float          # post-money after new round


class FundingRound(BaseModel):
    round_name: Literal["Pre-Seed", "Seed", "Series A", "Series B", "Series C", "Bridge"]
    amount_raised: float               # USD
    pre_money_valuation: float
    post_money_valuation: float
    new_shares_issued: int
    price_per_share: float
    investor_ownership_pct: float


class CapTableAnalysis(BaseModel):
    total_shares_pre: int
    total_shares_post: int
    shareholders: list[ShareholderRow]
    funding_round: FundingRound
    founder_dilution_pct: float        # how much founders lost
    dilution_summary: str


# ── 3. Burn Rate + Unit Economics ─────────────────────────────────────────────

class UnitEconomics(BaseModel):
    cac: float                         # Customer Acquisition Cost USD
    ltv: float                         # Lifetime Value USD
    ltv_cac_ratio: float               # computed
    payback_months: float              # CAC / monthly gross margin per customer
    arpu: float                        # Average Revenue Per User/month
    churn_rate_pct: float              # monthly %
    gross_margin_pct: float


class BankingMetrics(BaseModel):
    nim_pct: Optional[float] = None            # Net Interest Margin %
    roa_pct: Optional[float] = None            # Return on Assets %
    roe_pct: Optional[float] = None            # Return on Equity %
    npl_ratio_pct: Optional[float] = None      # Non-Performing Loans %
    car_pct: Optional[float] = None            # Capital Adequacy Ratio %
    cost_to_income_pct: Optional[float] = None # Cost-to-Income ratio %


class BurnAnalysis(BaseModel):
    monthly_burn: float                # USD
    monthly_revenue: float
    net_burn: float                    # burn - revenue
    cash_on_hand: float
    runway_months: float               # computed
    break_even_month: int              # month number when net_burn = 0
    burn_multiple: float               # net_burn / net_new_arr — efficiency metric
    unit_economics: Optional[UnitEconomics] = None


# ── 4. Financial Statements (3-statement model) ───────────────────────────────

class PnLStatement(BaseModel):
    year: int
    revenue: float
    cogs: float
    gross_profit: float
    gross_margin_pct: float
    opex: float
    ebitda: float
    depreciation: float
    ebit: float
    interest_expense: float
    ebt: float
    tax_rate_pct: float
    net_income: float
    net_margin_pct: float


class BalanceSheet(BaseModel):
    year: int
    cash: float
    accounts_receivable: float
    inventory: float
    total_current_assets: float
    ppe_net: float
    total_assets: float
    accounts_payable: float
    short_term_debt: float
    total_current_liabilities: float
    long_term_debt: float
    total_liabilities: float
    equity: float


class CashFlowStatement(BaseModel):
    year: int
    cfo: float                         # Cash from Operations
    cfi: float                         # Cash from Investing (capex negative)
    cff: float                         # Cash from Financing
    net_change_in_cash: float
    ending_cash: float


class FinancialStatements(BaseModel):
    pnl: list[PnLStatement]            # 3 years
    balance_sheet: list[BalanceSheet]  # 3 years
    cash_flow: list[CashFlowStatement] # 3 years


# ── 5. Valuation Multiples ────────────────────────────────────────────────────

class CompComp(BaseModel):
    company: str
    ev_ebitda: float
    ev_revenue: float
    pe_ratio: float
    price_to_book: float


class ValuationMultiples(BaseModel):
    subject_ev_ebitda: float
    subject_ev_revenue: float
    subject_pe: float
    comparable_companies: list[CompComp]
    implied_valuation_low: float       # USD — from lowest multiple
    implied_valuation_mid: float       # USD — median
    implied_valuation_high: float      # USD — highest
    valuation_method_used: Literal["EV/EBITDA", "EV/Revenue", "P/E", "Blended"]
    valuation_commentary: str


# ── Combined Agent Output ──────────────────────────────────────────────────────

class FinanceAgentOutput(BaseModel):
    dcf: DCFAnalysis
    cap_table: CapTableAnalysis
    burn: BurnAnalysis
    statements: FinancialStatements
    valuation: ValuationMultiples
    banking_metrics: Optional[BankingMetrics] = None
    financial_fit_score: int           # 0-100, used by synthesis layer
    go_signal: Literal["Go", "Conditional Go", "No Go"]
    cfo_summary: str                   # 80-word board narrative
    data_warnings: list[str] = []      # sanity-bound violations flagged during computation
