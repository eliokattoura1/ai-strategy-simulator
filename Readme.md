# 🧠 AI Strategy Simulator

> A multi-agent AI system that replicates a full C-suite strategy process — from environmental scanning to boardroom-ready recommendations.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![ReportLab](https://img.shields.io/badge/Reports-ReportLab-navy)

---

## 🎯 What It Does

Input a company, industry, and strategic question. The system deploys 8 specialized AI agents — each running a different strategic management framework — then synthesizes their outputs into a ranked, scored, boardroom-ready PDF strategy report.

**Example:**
> *"Should Bank Audi expand into fintech or defend its core banking position?"*

The system returns a 13-page strategy report with scored recommendations, conflict resolutions, and 3 scenario branches in under 2 minutes.

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
| Synthesis | Conflict Resolution, Strategic Fit Scoring |

---

## 🤖 Multi-Agent Architecture

**Pipeline flow:**

1. **Orchestrator** — receives input, routes to agents, manages state
2. **External Agent** — PESTEL + Porter's Five Forces + Industry Life Cycle
3. **Internal Agent** — VRIO + McKinsey 7S + Value Chain
4. **Position Agent** — SWOT/TOWS + BCG + Ansoff
5. **Competitive Agent** — Game Theory + Blue Ocean ERRC
6. **Formulation Agent** — Strategy Clock + Generic Strategies
7. **Risk Agent** — STEEP Scenarios + Sensitivity Analysis
8. **Execution Agent** — Balanced Scorecard + OKRs
9. **Synthesis Layer** — Conflict resolution + strategic fit scoring + board narrative

**Output:** 13-page PDF report + 5 Plotly dashboards

---

## 📊 Output Per Run

- ✅ Structured JSON per agent
- ✅ Strategic fit score (0–100)
- ✅ 3 scenario branches (optimistic / base / stress)
- ✅ 13-page PDF boardroom report
- ✅ 5 Plotly strategic dashboards

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Agents | OpenAI GPT-4o |
| Orchestration & Synthesis | OpenAI GPT-4o |
| Agent State Management | Python async + dataclasses |
| Data Validation | Pydantic v2 |
| UI | Streamlit |
| PDF Report | ReportLab |
| Charts | Plotly |
| Vector Database | ChromaDB (RAG — coming soon) |

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

Set your OpenAI API key as an environment variable:

```powershell
# Windows
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_key_here", "User")
```

```bash
# Mac/Linux
export OPENAI_API_KEY=your_key_here
```

### Run

**Streamlit UI:**
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
│   └── synthesis.py           # Conflict resolution + scoring
├── schemas/                   # Pydantic output schemas per agent
├── reports/
│   ├── pdf_generator.py       # 13-page ReportLab PDF generator
│   ├── charts_generator.py    # 5 Plotly strategic charts
│   └── output.json            # Raw agent outputs
├── ui/
│   └── app.py                 # Streamlit application
├── config.py                  # API keys + model config
├── main.py                    # CLI entry point
└── requirements.txt
```

---

## 📄 Sample Report

The system generates a 13-page boardroom PDF including:

1. Cover Page
2. Executive Summary + Strategic Fit Score
3. External Environment (PESTEL + Porter's)
4. Internal Audit (VRIO + McKinsey 7S)
5. Strategic Position (SWOT + TOWS + Ansoff)
6. Competitive Dynamics (Game Theory + Blue Ocean)
7. Strategy Formulation (Strategy Clock + Generic)
8. Risk & Scenarios (STEEP + Sensitivity)
9. Execution Roadmap (BSC + OKRs)
10. Strategic Options Ranking
11. Board Narrative
12. Appendix — Raw Scores

---

## 🗺️ Roadmap

- [x] Multi-agent pipeline
- [x] PDF boardroom report
- [x] Plotly dashboards
- [x] Streamlit UI
- [ ] ChromaDB RAG — upload company documents
- [ ] PowerPoint export
- [ ] Company comparison mode
- [ ] Historical run storage

---

## 👨‍💼 About

Built as part of an MBA in AI & Data Science portfolio. Demonstrates multi-agent AI architecture, strategic management frameworks, and full-stack AI product development.

---

*Powered by OpenAI GPT-4o*
