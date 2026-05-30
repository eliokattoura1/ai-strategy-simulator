import requests
from config import ALPHA_VANTAGE_API_KEY


def get_yahoo_finance(ticker: str) -> dict:
    base = {
        "market_cap": None, "pe_ratio": None, "price_to_book": None,
        "ev_to_ebitda": None, "revenue_ttm": None, "net_income_ttm": None,
        "gross_margin": None, "profit_margin": None, "52_week_high": None,
        "52_week_low": None, "current_price": None, "beta": None,
        "dividend_yield": None,
    }
    if not ticker:
        base["error"] = "Yahoo Finance: no ticker provided"
        return base
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            base["error"] = f"Yahoo Finance: ticker '{ticker}' not found"
            return base
        base["market_cap"]     = info.get("marketCap")
        base["pe_ratio"]       = info.get("trailingPE")
        base["price_to_book"]  = info.get("priceToBook")
        base["ev_to_ebitda"]   = info.get("enterpriseToEbitda")
        base["revenue_ttm"]    = info.get("totalRevenue")
        base["net_income_ttm"] = info.get("netIncomeToCommon")
        base["gross_margin"]   = info.get("grossMargins")
        base["profit_margin"]  = info.get("profitMargins")
        base["52_week_high"]   = info.get("fiftyTwoWeekHigh")
        base["52_week_low"]    = info.get("fiftyTwoWeekLow")
        base["current_price"]  = info.get("currentPrice") or info.get("regularMarketPrice")
        base["beta"]           = info.get("beta")
        base["dividend_yield"] = info.get("dividendYield")
    except Exception as exc:
        base["error"] = f"Yahoo Finance: {exc}"
    return base


def get_world_bank(country_code: str, year: int = 2024) -> dict:
    import time
    import requests
    from collections import Counter

    indicators = {
        "NY.GDP.MKTP.KD.ZG":    "gdp_growth_pct",
        "FP.CPI.TOTL.ZG":       "inflation_pct",
        "SL.UEM.TOTL.ZS":       "unemployment_pct",
        "NY.GDP.PCAP.CD":       "gdp_per_capita_usd",
        "GC.DOD.TOTL.GD.ZS":   "govt_debt_pct_gdp",
        "BX.KLT.DINV.WD.GD.ZS":"fdi_pct_gdp",
    }

    result = {v: None for v in indicators.values()}
    field_years: dict[str, int] = {}

    try:
        for indicator, field in indicators.items():
            for yr in (year, year - 1, year - 2):
                url = (
                    f"https://api.worldbank.org/v2/country/{country_code}"
                    f"/indicator/{indicator}"
                    f"?format=json&date={yr}&per_page=1"
                )
                try:
                    r = requests.get(url, timeout=15)
                except requests.Timeout:
                    time.sleep(2)
                    r = requests.get(url, timeout=15)
                data = r.json()
                if (isinstance(data, list) and len(data) > 1
                        and data[1] and data[1][0].get("value") is not None):
                    result[field] = round(float(data[1][0]["value"]), 2)
                    field_years[field] = yr
                    break
    except Exception as e:
        result["error"] = f"World Bank: {e}"

    data_year = Counter(field_years.values()).most_common(1)[0][0] if field_years else None
    result["data_year"] = data_year
    result["_field_years"] = field_years
    return result


def get_alpha_vantage_fundamentals(ticker: str) -> dict:
    fields = [
        "Description", "Sector", "Industry",
        "MarketCapitalization", "EBITDA", "PERatio", "PEGRatio",
        "EPS", "RevenuePerShareTTM", "ProfitMargin",
        "OperatingMarginTTM", "ReturnOnAssetsTTM", "ReturnOnEquityTTM",
        "RevenueTTM", "GrossProfitTTM", "DilutedEPSTTM",
        "QuarterlyEarningsGrowthYOY", "QuarterlyRevenueGrowthYOY",
        "AnalystTargetPrice", "ForwardPE",
    ]
    key_map = {
        "Description": "description", "Sector": "sector", "Industry": "industry",
        "MarketCapitalization": "market_capitalization", "EBITDA": "ebitda",
        "PERatio": "pe_ratio", "PEGRatio": "peg_ratio", "EPS": "eps",
        "RevenuePerShareTTM": "revenue_per_share_ttm", "ProfitMargin": "profit_margin",
        "OperatingMarginTTM": "operating_margin_ttm",
        "ReturnOnAssetsTTM": "return_on_assets_ttm",
        "ReturnOnEquityTTM": "return_on_equity_ttm",
        "RevenueTTM": "revenue_ttm", "GrossProfitTTM": "gross_profit_ttm",
        "DilutedEPSTTM": "diluted_eps_ttm",
        "QuarterlyEarningsGrowthYOY": "quarterly_earnings_growth_yoy",
        "QuarterlyRevenueGrowthYOY": "quarterly_revenue_growth_yoy",
        "AnalystTargetPrice": "analyst_target_price", "ForwardPE": "forward_pe",
    }
    if not ticker:
        return {"error": "Alpha Vantage: no ticker provided"}
    if not ALPHA_VANTAGE_API_KEY:
        return {"error": "Alpha Vantage: no API key configured"}
    try:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
        note = raw.get("Note") or raw.get("Information") or ""
        if "Thank you for using Alpha Vantage" in note or "higher API call frequency" in note:
            result = {key_map[k]: None for k in fields}
            result["error"] = "Alpha Vantage: rate limit reached — upgrade to premium or wait"
            return result
        if not raw or "Symbol" not in raw:
            return {"error": f"Alpha Vantage: {note or 'empty response'}"}
        return {key_map[k]: raw.get(k) for k in fields}
    except Exception as exc:
        return {"error": f"Alpha Vantage: {exc}"}


def get_all_market_data(ticker: str, country_code: str) -> dict:
    if ticker:
        yahoo = get_yahoo_finance(ticker)
        alpha_vantage = get_alpha_vantage_fundamentals(ticker)
    else:
        yahoo = {"error": "no ticker provided"}
        alpha_vantage = {"error": "no ticker provided"}

    world_bank = get_world_bank(country_code)

    yahoo_ok = "error" not in yahoo
    wb_ok = "error" not in world_bank
    av_ok = "error" not in alpha_vantage

    available = sum([yahoo_ok, wb_ok, av_ok])
    if available == 3:
        overall = "Full"
    elif available >= 1:
        overall = "Partial"
    else:
        overall = "None"

    return {
        "ticker": ticker,
        "country_code": country_code,
        "yahoo": yahoo,
        "world_bank": world_bank,
        "alpha_vantage": alpha_vantage,
        "data_quality": {
            "yahoo_available": yahoo_ok,
            "world_bank_available": wb_ok,
            "alpha_vantage_available": av_ok,
            "overall": overall,
        },
    }


def _safe(v):
    if v is None:
        return None
    try:
        f = float(v)
        return f"{f:.2f}" if f != int(f) else str(int(f))
    except (TypeError, ValueError):
        return str(v) if v else None


def _fmt_money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if abs(v) >= 1e12:
        return f"${v/1e12:.1f}T"
    if abs(v) >= 1e9:
        return f"${v/1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"


def _fmt_pct(v):
    try:
        v = float(v)
        return f"{v*100:.1f}%" if abs(v) <= 1 else f"{v:.1f}%"
    except (TypeError, ValueError):
        return None


def _fmt_wb(v, suffix="%"):
    try:
        return f"{float(v):.1f}{suffix}"
    except (TypeError, ValueError):
        return None


def format_for_agent_prompt(market_data: dict) -> str:
    if not market_data:
        return ""

    quality = market_data.get("data_quality", {}).get("overall", "None")
    if quality == "None":
        return ""

    yahoo = market_data.get("yahoo", {}) or {}
    av = market_data.get("alpha_vantage", {}) or {}
    wb = market_data.get("world_bank", {}) or {}
    country_code = market_data.get("country_code", "")

    lines = ["=== REAL MARKET DATA (verified external sources) ===", ""]

    yahoo_ok = market_data.get("data_quality", {}).get("yahoo_available", False)
    av_ok = market_data.get("data_quality", {}).get("alpha_vantage_available", False)
    if yahoo_ok or av_ok:
        lines.append("COMPANY FINANCIALS (Yahoo Finance / Alpha Vantage):")
        fields = [
            ("Market Cap",       _fmt_money(yahoo.get("market_cap") or av.get("market_capitalization"))),
            ("P/E Ratio",        _safe(yahoo.get("pe_ratio") or av.get("pe_ratio"))),
            ("Revenue (TTM)",    _fmt_money(yahoo.get("revenue_ttm") or av.get("revenue_ttm"))),
            ("Net Income (TTM)", _fmt_money(yahoo.get("net_income_ttm"))),
            ("Gross Margin",     _fmt_pct(yahoo.get("gross_margin"))),
            ("EPS",              _safe(av.get("eps"))),
            ("ROE",              _fmt_pct(av.get("return_on_equity_ttm"))),
            ("Beta",             _safe(yahoo.get("beta"))),
        ]
        for label, val in fields:
            if val is not None:
                lines.append(f"- {label}: {val}")
        lines.append("")

    wb_ok = market_data.get("data_quality", {}).get("world_bank_available", False)
    if wb_ok:
        wb_year = wb.get("data_year", "N/A")
        field_years = wb.get("_field_years", {})
        lines.append(f"MACRO ENVIRONMENT (World Bank — {country_code}):")
        wb_fields = [
            ("GDP Growth",              "gdp_growth_pct",       _fmt_wb(wb.get("gdp_growth_pct"))),
            ("Inflation",               "inflation_pct",        _fmt_wb(wb.get("inflation_pct"))),
            ("Unemployment",            "unemployment_pct",     _fmt_wb(wb.get("unemployment_pct"))),
            ("GDP per Capita",          "gdp_per_capita_usd",   _fmt_money(wb.get("gdp_per_capita_usd")) if wb.get("gdp_per_capita_usd") else None),
            ("Government Debt (% GDP)", "govt_debt_pct_gdp",    _fmt_wb(wb.get("govt_debt_pct_gdp"))),
            ("FDI (% GDP)",             "fdi_pct_gdp",          _fmt_wb(wb.get("fdi_pct_gdp"))),
        ]
        for label, field_key, val in wb_fields:
            if val is not None:
                yr = field_years.get(field_key, wb_year)
                lines.append(f"- {label}: {val} ({yr})")
        lines.append("")

    lines.append(f"DATA QUALITY: {quality}")
    lines.append("================================================")
    return "\n".join(lines)
