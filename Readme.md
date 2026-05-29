# 🧠 AI Strategy Simulator

> A multi-agent AI system that replicates a full C-suite strategy process — from environmental scanning to boardroom-ready recommendations, with a built-in financial viability engine.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![ReportLab](https://img.shields.io/badge/Reports-ReportLab-navy)

---

## 🎯 What It Does

Input a company, industry, and strategic question. The system deploys 10 specialized AI agents — each running a different strategic management or finance framework — then synthesizes their outputs into a ranked, scored, boardroom-ready PDF strategy report.

**Example:**
> *"Should Bank Audi expand into fintech or defend its core banking position?"*

The system returns a 22-page investment-bank-style report with scored recommendations, financial viability analysis, ethics & ESG assessment, conflict resolutions, and 3 scenario branches — in under 2 minutes.

---

## 🏛️ Strategic Frameworks Covered

| Layer | Frameworks |
|-------|-----------|
| External Environment | PESTEL, Porter's Five Forces, Industry Life Cycle |
| Internal Audit | VRIO, McKinsey 7S, Value Chain Analysis |
| Strategic Position | SWOT → TOWS Matrix, BCG Matrix, Ansoff Matrix |
| Competitive Dynamics | Game Theory (payoff matrices), Blue Ocean ERRC Grid |
| Strategy Formulation | Bowman's Strategy Clock, Generic Strategies |
| Risk & Scenarios | STEEP Scenario Planning, Sensitivity Analysis |
| Execution | Balanced Scorecard, OKRs |
| **Financial Viability** | **DCF / NPV / IRR, Cap Table & Dilution, Burn Rate & Unit Economics, 3-Statement Model, Valuation Multiples** |
| **Ethics & Stakeholder** | **Stakeholder Theory, ESG Scoring, 3 Ethical Frameworks (Utilitarian, Deontological, Virtue Ethics)** |
| Synthesis | Conflict Resolution, Strategic Fit Scoring |

---

## 🤖 Multi-Agent Architecture

**Pipeline flow:**

0. **Market Data Layer** — fetches live market data (Yahoo Finance · Alpha Vantage · World Bank) before agents run; injects real numbers into every agent prompt
1. **Orchestrator** — receives input, routes to agents, manages state
2. **External Agent** — PESTEL + Porter's Five Forces + Industry Life Cycle
3. **Internal Agent** — VRIO + McKinsey 7S + Value Chain
4. **Position Agent** — SWOT/TOWS + BCG + Ansoff
5. **Competitive Agent** — Game Theory + Blue Ocean ERRC
6. **Formulation Agent** — Strategy Clock + Generic Strategies
7. **Risk Agent** — STEEP Scenarios + Sensitivity Analysis
8. **Execution Agent** — Balanced Scorecard + OKRs
9. **Finance Agent** — DCF · Cap Table · Burn Rate · 3-Statement Model · Valuation Comps
10. **Ethics Agent** — Stakeholder Theory · ESG Scoring · 3 Ethical Frameworks
11. **Synthesis Layer** — Conflict resolution + strategic fit scoring + board narrative

**Output:** 22-page PDF report + 8 Plotly charts

---

## 💰 Finance Agent — 5 Domains

The Finance Agent runs a deterministic Python math engine (no LLM hallucination on numbers) alongside an LLM that interprets the results in strategic context.

| Domain | What It Computes |
|--------|-----------------|
| **DCF / Valuation** | NPV, IRR, payback period, terminal value, enterprise value (WACC-discounted) |
| **Cap Table & Equity Dilution** | Pre/post-money ownership, dilution %, new shares issued, price per share |
| **Burn Rate & Unit Economics** | Monthly burn, runway, LTV/CAC ratio, payback months, ARPU, churn, gross margin |
| **3-Statement Model** | Projected P&L, balance sheet, and cash flow statement |
| **Valuation Multiples** | EV/EBITDA, EV/Revenue, P/E vs. comparable companies; Bear / Base / Bull range |

Outputs a **go / conditional go / no-go signal** and a CFO-style summary paragraph.

---

## 📊 Output Per Run

- ✅ Structured JSON per agent (all 10 agents + synthesis)
- ✅ Strategic fit score (0–100)
- ✅ Financial fit score (0–100) with go-signal
- ✅ ESG & ethics assessment with stakeholder impact matrix
- ✅ 3 scenario branches (optimistic / base / stress)
- ✅ 22-page investment-bank-style PDF boardroom report
- ✅ 8 Plotly charts (5 strategic + 3 financial)

### Charts Generated

| Chart | Description |
|-------|-------------|
| Strategic Capability Radar | Scores across all 8 analytical dimensions |
| Porter's Five Forces Bar | Industry competitive intensity (0–10) |
| BCG Matrix | Business unit portfolio positioning |
| STEEP Scenario Comparison | Scenario severity across dimensions |
| Strategic Options Ranking | Overall score, fit, risk & feasibility |
| **DCF Waterfall** | From revenue to NPV via WACC discounting |
| **Cumulative Free Cash Flow** | Projected FCF accumulation over 5 years |
| **Valuation Comps** | Subject multiples vs. comparable companies |

---

## 🌐 Data Sources

Real market data is fetched before agents run and injected into every agent prompt via `data_layer/market_data.py` (`get_all_market_data()` · `format_for_agent_prompt()`).

| Source | Data Points | Key Required? |
|--------|------------|---------------|
| **Yahoo Finance** | Market cap, P/E ratio, revenue, gross/operating/net margins, beta, 52-week range | No — free |
| **Alpha Vantage** | EPS, ROE, revenue growth (YoY), analyst price targets, earnings estimates | Yes — free tier at alphavantage.co |
| **World Bank** | GDP growth, inflation rate, unemployment rate, GDP per capita, government debt (% GDP), FDI inflows | No — free |

> Yahoo Finance and World Bank require no API key. Alpha Vantage requires a free key (set `ALPHA_VANTAGE_API_KEY` in your `.env`).

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Agents | OpenAI GPT-4o |
| Orchestration & Synthesis | OpenAI GPT-4o |
| Financial Math Engine | Pure Python (deterministic — no LLM for numbers) |
| Market Data | Yahoo Finance · Alpha Vantage · World Bank APIs |
| Agent State Management | Python async + dataclasses |
| Data Validation | Pydantic v2 |
| UI | Streamlit (Playfair Display + Inter — investment bank aesthetic) |
| PDF Report | ReportLab (22-page, investment bank layout) |
| Charts | Plotly (8 charts — strategic + financial) |
| Vector Database | ChromaDB (RAG — document upload & context injection) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

```bash
git clone https://github.com/eliokattoura1/ai-strategy-simulator.git
cd ai-strategy-simulator
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuration

Set your API keys as environment variables (or in a `.env` file):

```powershell
# Windows
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_key_here", "User")
[System.Environment]::SetEnvironmentVariable("ALPHA_VANTAGE_API_KEY", "your_key_here", "User")
```

```bash
# Mac/Linux
export OPENAI_API_KEY=your_key_here
export ALPHA_VANTAGE_API_KEY=your_key_here  # free at alphavantage.co
```

> Yahoo Finance and World Bank are free with no key required.

### Run

**Streamlit UI (recommended):**
```bash
streamlit run ui/app.py
```

**Command line:**
```bash
python main.py
```

---

## 📁 Project Structure

```
ai-strategy-simulator/
├── agents/
│   ├── orchestrator.py        # Routes and manages agent state
│   ├── external_agent.py      # PESTEL + Porter's Five Forces
│   ├── internal_agent.py      # VRIO + McKinsey 7S
│   ├── position_agent.py      # SWOT/TOWS + BCG + Ansoff
│   ├── competitive_agent.py   # Game Theory + Blue Ocean
│   ├── formulation_agent.py   # Strategy Clock + Generic Strategies
│   ├── risk_agent.py          # STEEP Scenarios
│   ├── execution_agent.py     # Balanced Scorecard + OKRs
│   ├── finance_agent.py       # DCF + Cap Table + Burn + Statements + Valuation
│   ├── ethics_agent.py        # Stakeholder Theory + ESG + 3 ethical frameworks
│   └── synthesis.py           # Conflict resolution + scoring
├── schemas/
│   ├── external_schema.py
│   ├── internal_schema.py
│   ├── position_schema.py
│   ├── competitive_schema.py
│   ├── formulation_schema.py
│   ├── risk_schema.py
│   ├── execution_schema.py
│   ├── finance_schema.py      # Pydantic models for all 5 finance domains
│   ├── ethics_schema.py       # Pydantic models for ethics & ESG output
│   └── synthesis_schema.py
├── data_layer/
│   └── market_data.py         # get_all_market_data(), format_for_agent_prompt()
├── tools/
│   └── finance_math.py        # Deterministic NPV, IRR, LTV/CAC, dilution, burn
├── reports/
│   ├── pdf_generator.py       # 22-page ReportLab PDF (investment bank layout)
│   ├── charts_generator.py    # 5 strategic Plotly charts
│   ├── finance_dashboard.py   # 3 financial Plotly charts (DCF, FCF, comps)
│   └── output.json            # Raw agent outputs (all 10 agents + synthesis)
├── rag/
│   └── document_processor.py  # ChromaDB document upload + context injection
├── ui/
│   └── app.py                 # Streamlit UI (premium investment bank design)
├── config.py                  # API keys + model config
├── main.py                    # CLI entry point
└── requirements.txt
```

---

## 📄 Report Structure (22 Pages)

The system generates a 22-page investment-bank-style PDF:

1. Cover Page
2. Executive Summary + Strategic Fit Score
3. External Environment (PESTEL + Porter's)
4. Internal Audit (VRIO + McKinsey 7S)
5. Strategic Position (SWOT + TOWS + Ansoff)
6. Competitive Dynamics (Game Theory + Blue Ocean)
7. Strategy Formulation (Strategy Clock + Generic)
8. Risk & Scenarios (STEEP + Sensitivity)
9. Execution Roadmap (BSC + OKRs)
10. Financial Viability (DCF + Valuation + Unit Economics)
11. Ethics & Stakeholder Analysis (ESG + 3 Frameworks)
12. Strategic Options Ranking
13. Board Narrative
14–22. Appendix — Raw scores, Porter forces, McKinsey 7S, Finance detail, Ethics detail

---

## 🎓 Course Showcase

This project was built as part of an MBA in AI & Data Science. Each module maps directly to coursework:

| Module | Course(s) |
|--------|-----------|
| External, Internal, Position, Competitive, Formulation, Risk, Execution, Synthesis agents | Strategic Management |
| Finance Agent — DCF, cap table, burn rate, unit economics, valuation multiples | Entrepreneurial Finance + Managerial Accounting |
| Ethics Agent — Stakeholder Theory, ESG scoring, 3 ethical frameworks | Business Ethics |
| Market Data Layer — Yahoo Finance, Alpha Vantage, World Bank APIs; ChromaDB RAG | Management Information Systems + Data Science |
| *(Coming soon)* LangGraph orchestration + memory | AI & Machine Learning |

---

## 🗺️ Roadmap

- [x] Multi-agent strategy pipeline (10 agents)
- [x] PDF boardroom report
- [x] Plotly strategic dashboards
- [x] Streamlit UI
- [x] **Finance Agent** — DCF, cap table, burn rate, 3-statement model, valuation comps
- [x] **3 financial Plotly charts** — DCF waterfall, cumulative FCF, valuation comps
- [x] **UI redesign** — Playfair Display + Inter, investment bank aesthetic
- [x] **PDF redesign** — 22-page investment bank layout with finance + ethics pages
- [x] **ChromaDB RAG** — upload company documents for context injection
- [x] **Ethics Agent** — Stakeholder Theory, ESG scoring, 3 ethical frameworks
- [x] **Market Data APIs** — Yahoo Finance, Alpha Vantage, World Bank live data injection
- [ ] PowerPoint export
- [ ] Company comparison mode
- [ ] Historical run storage
- [ ] LangGraph orchestration + memory

---

## 👨‍💼 About

Built as part of an MBA in AI & Data Science portfolio. Demonstrates multi-agent AI architecture, strategic management frameworks, financial modeling, and full-stack AI product development.

---

## ⚠️ API Keys Required

This project requires the following API keys:

| Key | Required | Where to get it |
|-----|----------|----------------|
| `OPENAI_API_KEY` | Yes | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ALPHA_VANTAGE_API_KEY` | Optional | [alphavantage.co](https://www.alphavantage.co/support/#api-key) — free tier |

- Yahoo Finance and World Bank data are free with no key
- New OpenAI accounts receive free credits to get started
- A full simulation costs approximately **$0.50–2.00** in API calls

> A demo video walkthrough is available here: *(coming soon)*

*Powered by OpenAI GPT-4o*
