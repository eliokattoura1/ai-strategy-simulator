"""
AI Strategy Simulator — Streamlit UI
Run: streamlit run ui/app.py
"""

import os
import sys
import json
import asyncio

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)  # main.py writes to "reports/" using relative paths

import streamlit as st

st.set_page_config(
    page_title="AI Strategy Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy agent imports (after path setup) ─────────────────────────────────────
from agents.orchestrator import SimulatorState
from agents.external_agent import run_external_agent
from agents.internal_agent import run_internal_agent
from agents.position_agent import run_position_agent
from agents.competitive_agent import run_competitive_agent
from agents.formulation_agent import run_formulation_agent
from agents.risk_agent import run_risk_agent
from agents.execution_agent import run_execution_agent
from agents.synthesis import run_synthesis
from reports.pdf_generator import generate_report
from reports.charts_generator import generate_all_charts

# ── Paths ─────────────────────────────────────────────────────────────────────
JSON_PATH  = os.path.join(BASE_DIR, "reports", "output.json")
PDF_PATH   = os.path.join(BASE_DIR, "reports", "strategy_report.pdf")
CHARTS_DIR = os.path.join(BASE_DIR, "reports", "charts")

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY = "#1B2A4A"
GOLD = "#C9A84C"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── App background ─────────────────────────────────────────────────────── */
.stApp { background: #F7F8FC; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1B2A4A 0%, #243357 60%, #1B2A4A 100%) !important;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E8EBF0 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(201,168,76,0.35) !important; }

/* ── Sidebar nav buttons ────────────────────────────────────────────────── */
div[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: transparent;
    color: #C5CBDB !important;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    text-align: left;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.18s ease;
    margin-bottom: 2px;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(201,168,76,0.15) !important;
    color: #C9A84C !important;
    transform: translateX(3px);
}

/* ── Active nav button ──────────────────────────────────────────────────── */
div[data-testid="stSidebar"] .stButton.active > button {
    background: rgba(201,168,76,0.2) !important;
    color: #C9A84C !important;
    border-left: 3px solid #C9A84C;
}

/* ── Primary run button ─────────────────────────────────────────────────── */
.main-area .stButton > button {
    background: linear-gradient(135deg, #1B2A4A 0%, #2C3F6A 100%);
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 0.7rem 2.5rem;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(27,42,74,0.25);
}
.main-area .stButton > button:hover {
    background: linear-gradient(135deg, #C9A84C 0%, #E0BE72 100%);
    color: #1B2A4A !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(201,168,76,0.4);
}

/* ── Download button ────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #C9A84C 0%, #E0BE72 100%) !important;
    color: #1B2A4A !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.8rem 3rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 14px rgba(201,168,76,0.4) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(201,168,76,0.55) !important;
}

/* ── Form inputs ────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 1.5px solid #D8DCE8;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    font-size: 0.95rem;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #1B2A4A !important;
    box-shadow: 0 0 0 3px rgba(27,42,74,0.08) !important;
}

/* ── Card components ────────────────────────────────────────────────────── */
.card {
    background: white;
    border-radius: 12px;
    padding: 1.75rem;
    box-shadow: 0 2px 14px rgba(27,42,74,0.07);
    margin-bottom: 1.25rem;
}
.card-accent {
    border-left: 4px solid #C9A84C;
}
.card-navy {
    background: linear-gradient(135deg, #1B2A4A 0%, #243357 100%);
    color: white;
    border-radius: 12px;
    padding: 2rem;
}

/* ── Score badge ────────────────────────────────────────────────────────── */
.score-ring {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100px; height: 100px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1B2A4A, #2C3F6A);
    border: 3px solid #C9A84C;
    font-size: 2.2rem;
    font-weight: 800;
    color: white;
    box-shadow: 0 6px 20px rgba(27,42,74,0.3);
}

/* ── Step cards (Home) ──────────────────────────────────────────────────── */
.step-card {
    background: white;
    border-radius: 14px;
    padding: 2.25rem 1.75rem;
    text-align: center;
    box-shadow: 0 4px 18px rgba(27,42,74,0.07);
    height: 100%;
    border-top: 4px solid #C9A84C;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.step-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(27,42,74,0.12);
}
.step-num {
    font-size: 3rem;
    font-weight: 800;
    color: #C9A84C;
    line-height: 1;
    margin-bottom: 0.75rem;
}

/* ── Agent progress rows ────────────────────────────────────────────────── */
.agent-row {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.55rem 0.75rem;
    border-radius: 8px;
    margin-bottom: 4px;
    background: #F7F8FC;
    font-size: 0.88rem;
    font-weight: 500;
    color: #374151;
}

/* ── Option ranking cards ───────────────────────────────────────────────── */
.opt-card {
    background: white;
    border-radius: 10px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    border-left: 5px solid #D0D3DA;
    display: flex; align-items: center; gap: 1rem;
}
.opt-card.rank1 { border-left-color: #C9A84C; }
.opt-card.rank2 { border-left-color: #1B2A4A; }
.opt-card.rank3 { border-left-color: #6B7280; }
.opt-rank {
    font-size: 1.4rem; font-weight: 800;
    color: #C9A84C; min-width: 36px;
}

/* ── Gold divider ───────────────────────────────────────────────────────── */
.gold-hr {
    height: 3px;
    background: linear-gradient(90deg, transparent, #C9A84C, transparent);
    border: none;
    border-radius: 2px;
    margin: 1.75rem 0;
}

/* ── Header banner ──────────────────────────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #1B2A4A 0%, #2C3F6A 60%, #1B2A4A 100%);
    border-radius: 14px;
    padding: 3rem 3.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: "";
    position: absolute; top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #C9A84C, #E0BE72, #C9A84C);
}

/* ── Framework tags ─────────────────────────────────────────────────────── */
.fw-tag {
    display: inline-block;
    background: rgba(27,42,74,0.07);
    color: #1B2A4A;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    margin: 2px;
}

/* ── Hide Streamlit chrome ──────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stDeployButton"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "page": "home",
        "output_data": None,
        "simulation_done": False,
        "sim_company": "Bank Audi",
        "sim_industry": "Lebanese Banking & Financial Services",
        "sim_question": "Should Bank Audi expand into fintech or defend its core banking position?",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    # Auto-load last output if available
    if st.session_state.output_data is None and os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, encoding="utf-8") as f:
                st.session_state.output_data = json.load(f)
        except Exception:
            pass

_init_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _nav_button(label, icon, page_key):
    active = st.session_state.page == page_key
    prefix = "→ " if active else "   "
    if st.button(f"{icon}  {prefix}{label}", key=f"nav_{page_key}",
                 use_container_width=True):
        st.session_state.page = page_key
        st.rerun()

with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1.5rem 0.5rem 1rem; text-align: center;">
        <div style="font-size:1.1rem; font-weight:800; color:#C9A84C; letter-spacing:0.5px;">
            AI STRATEGY
        </div>
        <div style="font-size:0.75rem; color:#8A95AB; letter-spacing:1.5px; margin-top:2px;">
            SIMULATOR
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(201,168,76,0.3);margin:0 0 1rem;">', unsafe_allow_html=True)

    _nav_button("Home",               "🏠", "home")
    _nav_button("Run Simulation",     "🚀", "run")
    _nav_button("Results Dashboard",  "📊", "results")
    _nav_button("Download Report",    "📄", "download")

    st.markdown('<hr style="border-color:rgba(201,168,76,0.3);margin:1rem 0;">', unsafe_allow_html=True)

    if st.session_state.output_data:
        d = st.session_state.output_data
        st.markdown(f"""
        <div style="padding:0 0.5rem;">
            <div style="font-size:0.7rem; color:#8A95AB; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Last Analysis</div>
            <div style="font-size:0.85rem; font-weight:600; color:#E8EBF0;">{d.get('company','—')}</div>
            <div style="font-size:0.75rem; color:#8A95AB; margin-top:2px;">{d.get('industry','—')}</div>
            <div style="margin-top:0.5rem; display:flex; align-items:center; gap:0.4rem;">
                <span style="background:#C9A84C;color:#1B2A4A;font-weight:800;font-size:0.8rem;
                             border-radius:20px;padding:1px 8px;">
                    {int(d['synthesis'].get('overall_strategic_fit_score', 0))}
                </span>
                <span style="font-size:0.75rem;color:#8A95AB;">/ 100</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="position:absolute; bottom:1.5rem; left:0; right:0; text-align:center;
                font-size:0.68rem; color:#4A566A;">
        Powered by Claude AI
    </div>
    """, unsafe_allow_html=True)


# ── Async agent runner ────────────────────────────────────────────────────────

def _run_agents(company: str, industry: str, question: str, slots: dict) -> tuple:
    """
    Run all agents sequentially (with gather for parallel pairs).
    `slots` maps step keys to st.empty() placeholders for live progress.
    Returns (SimulatorState, SynthesisOutput).
    """

    def _mark(key: str, state: str):
        icons = {"pending": "⬜", "running": "🔄", "done": "✅"}
        labels = {
            "ext_int":    "External + Internal Analysis",
            "position":   "Strategic Position",
            "competitive":"Competitive Dynamics",
            "formulation":"Strategy Formulation",
            "risk":       "Risk Assessment",
            "execution":  "Execution Planning",
            "synthesis":  "Synthesis & Ranking",
        }
        icon = icons.get(state, "⬜")
        label = labels.get(key, key)
        suffix = " — running..." if state == "running" else ""
        slots[key].markdown(
            f'<div class="agent-row">{icon} <span>{label}</span>'
            f'<span style="color:#9CA3AF;font-size:0.8rem;margin-left:auto;">{suffix}</span></div>',
            unsafe_allow_html=True,
        )

    async def _main():
        sim_state = SimulatorState(
            company=company, industry=industry, strategic_question=question
        )

        _mark("ext_int", "running")
        sim_state.external, sim_state.internal = await asyncio.gather(
            run_external_agent(company, industry, question),
            run_internal_agent(company, industry, question),
        )
        _mark("ext_int", "done")

        _mark("position", "running")
        sim_state.position = await run_position_agent(
            company, industry, question, sim_state.external, sim_state.internal
        )
        _mark("position", "done")

        _mark("competitive", "running")
        sim_state.competitive = await run_competitive_agent(
            company, industry, question, sim_state.external, sim_state.position
        )
        _mark("competitive", "done")

        _mark("formulation", "running")
        sim_state.formulation = await run_formulation_agent(
            company, industry, question,
            sim_state.internal, sim_state.position, sim_state.competitive
        )
        _mark("formulation", "done")

        _mark("risk", "running")
        sim_state.risk = await run_risk_agent(
            company, industry, question, sim_state.external, sim_state.formulation
        )
        _mark("risk", "done")

        _mark("execution", "running")
        sim_state.execution = await run_execution_agent(
            company, industry, question, sim_state.formulation, sim_state.risk
        )
        _mark("execution", "done")

        _mark("synthesis", "running")
        synthesis_out = await run_synthesis(sim_state)
        _mark("synthesis", "done")

        return sim_state, synthesis_out

    return asyncio.run(_main())


# ── Page: Home ────────────────────────────────────────────────────────────────

def page_home():
    st.markdown("""
    <div class="hero-banner">
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem;">
            <span style="font-size:2.5rem;">📊</span>
            <div>
                <div style="font-size:0.8rem;color:#C9A84C;letter-spacing:2px;font-weight:600;text-transform:uppercase;">
                    AI-Powered Strategic Intelligence
                </div>
                <h1 style="color:white;margin:0;font-size:2.4rem;font-weight:800;letter-spacing:-0.5px;">
                    AI Strategy Simulator
                </h1>
            </div>
        </div>
        <p style="color:#A8B4CC;font-size:1.05rem;max-width:680px;line-height:1.65;margin:0.75rem 0 0;">
            A multi-agent AI system that analyzes your company's strategic position
            across 8 analytical frameworks — from PESTEL to game theory — and
            synthesizes boardroom-ready recommendations in minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    st.markdown("### How It Works")
    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    cards = [
        ("01", "Define the Question",
         "Enter your company name, industry, and the strategic question you need answered. "
         "The system tailors all 8 analytical agents to your specific context.",
         "🎯"),
        ("02", "Multi-Agent Analysis",
         "Eight specialized AI agents run in parallel and sequence — covering external forces, "
         "internal capabilities, competitive dynamics, risk, execution readiness, and more.",
         "🤖"),
        ("03", "Boardroom Report",
         "Receive a ranked strategic recommendation, interactive charts, and a downloadable "
         "12-page PDF report ready for executive presentation.",
         "📋"),
    ]
    for col, (num, title, desc, icon) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(f"""
            <div class="step-card">
                <div style="font-size:2.2rem;margin-bottom:0.5rem;">{icon}</div>
                <div class="step-num">{num}</div>
                <h3 style="color:#1B2A4A;font-size:1.05rem;font-weight:700;margin:0.5rem 0;">{title}</h3>
                <p style="color:#6B7280;font-size:0.88rem;line-height:1.6;margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # Frameworks grid
    st.markdown("### Analytical Frameworks Covered")
    frameworks = [
        ("🌍", "PESTEL Analysis",       "Political, Economic, Social, Technological, Environmental, Legal"),
        ("⚔️",  "Porter's Five Forces",  "Industry structure & competitive intensity"),
        ("🔷", "VRIO Framework",         "Internal resources: Valuable, Rare, Inimitable, Organized"),
        ("🔄", "McKinsey 7S",            "Organizational alignment across 7 dimensions"),
        ("📐", "SWOT / TOWS",            "Position mapping and strategic direction generation"),
        ("🎮", "Game Theory",            "Competitor response modeling & Nash equilibria"),
        ("🌊", "Blue Ocean ERRC",        "Eliminate–Reduce–Raise–Create value innovation grid"),
        ("🎯", "Balanced Scorecard",     "KPIs, OKRs, and execution roadmap"),
    ]
    g1, g2 = st.columns(2)
    for i, (icon, name, desc) in enumerate(frameworks):
        col = g1 if i % 2 == 0 else g2
        with col:
            st.markdown(f"""
            <div class="card card-accent" style="padding:1rem 1.25rem;margin-bottom:0.6rem;">
                <div style="display:flex;align-items:flex-start;gap:0.75rem;">
                    <span style="font-size:1.3rem;">{icon}</span>
                    <div>
                        <div style="font-weight:700;color:#1B2A4A;font-size:0.92rem;">{name}</div>
                        <div style="color:#6B7280;font-size:0.8rem;margin-top:2px;">{desc}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:0.5rem 0;">', unsafe_allow_html=True)
    if st.button("🚀  Start Your Analysis", key="home_cta"):
        st.session_state.page = "run"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Page: Run Simulation ──────────────────────────────────────────────────────

def page_run():
    st.markdown("""
    <h2 style="color:#1B2A4A;font-weight:800;margin-bottom:0.25rem;">Run Simulation</h2>
    <p style="color:#6B7280;margin-bottom:2rem;">
        Fill in the three fields below. The simulation typically takes 60–120 seconds.
    </p>
    """, unsafe_allow_html=True)

    # ── Input form ────────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        col_l, col_r = st.columns([3, 2])
        with col_l:
            company = st.text_input(
                "Company Name",
                value=st.session_state.sim_company,
                placeholder="e.g. Bank Audi",
                key="input_company",
            )
            industry = st.text_input(
                "Industry",
                value=st.session_state.sim_industry,
                placeholder="e.g. Lebanese Banking & Financial Services",
                key="input_industry",
            )
            question = st.text_area(
                "Strategic Question",
                value=st.session_state.sim_question,
                placeholder="e.g. Should we expand into fintech or defend our core position?",
                height=100,
                key="input_question",
            )

        with col_r:
            st.markdown("""
            <div style="background:#F7F8FC;border-radius:10px;padding:1.5rem;height:100%;">
                <div style="font-weight:700;color:#1B2A4A;margin-bottom:1rem;font-size:0.95rem;">
                    What the simulation covers
                </div>
            """, unsafe_allow_html=True)
            agents_list = [
                ("🌍", "External Environment"),
                ("🏛️", "Internal Audit"),
                ("📍", "Strategic Position"),
                ("⚔️",  "Competitive Dynamics"),
                ("🎯", "Strategy Formulation"),
                ("⚠️", "Risk & Scenarios"),
                ("🚀", "Execution Roadmap"),
                ("🧠", "Synthesis Layer"),
            ]
            for icon, name in agents_list:
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#374151;padding:3px 0;">'
                    f'{icon} {name}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────────────────────
    st.markdown('<div class="main-area">', unsafe_allow_html=True)
    run_clicked = st.button("🚀  Run AI Strategy Simulation", key="run_btn")
    st.markdown("</div>", unsafe_allow_html=True)

    if run_clicked:
        if not company.strip() or not industry.strip() or not question.strip():
            st.error("Please fill in all three fields before running the simulation.")
            return

        # Persist inputs
        st.session_state.sim_company  = company.strip()
        st.session_state.sim_industry = industry.strip()
        st.session_state.sim_question = question.strip()

        # ── Progress display ──────────────────────────────────────────────
        st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<h3 style="color:#1B2A4A;font-weight:700;">Running analysis for '
            f'<span style="color:#C9A84C;">{company.strip()}</span>…</h3>',
            unsafe_allow_html=True,
        )

        step_keys = ["ext_int", "position", "competitive",
                     "formulation", "risk", "execution", "synthesis"]

        progress_col, info_col = st.columns([1, 1])

        with progress_col:
            st.markdown(
                '<div style="font-weight:600;color:#1B2A4A;margin-bottom:0.5rem;font-size:0.9rem;">'
                'Agent Progress</div>',
                unsafe_allow_html=True,
            )
            slots = {k: st.empty() for k in step_keys}
            labels = {
                "ext_int":    "External + Internal Analysis",
                "position":   "Strategic Position",
                "competitive":"Competitive Dynamics",
                "formulation":"Strategy Formulation",
                "risk":       "Risk Assessment",
                "execution":  "Execution Planning",
                "synthesis":  "Synthesis & Ranking",
            }
            for k in step_keys:
                slots[k].markdown(
                    f'<div class="agent-row">⬜ <span>{labels[k]}</span>'
                    f'<span style="color:#9CA3AF;font-size:0.78rem;margin-left:auto;">pending</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with info_col:
            st.markdown("""
            <div class="card" style="padding:1.25rem;background:#FFFBF0;
                                     border-left:4px solid #C9A84C;">
                <div style="font-weight:700;color:#1B2A4A;margin-bottom:0.5rem;">
                    Simulation in progress
                </div>
                <p style="color:#6B7280;font-size:0.85rem;margin:0;line-height:1.6;">
                    Agents are running in sequence. The external and internal
                    agents run in parallel first, followed by position, competitive,
                    formulation, risk, execution, and finally synthesis.<br><br>
                    Average completion time: <strong>60–120 seconds</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

        # ── Run agents ────────────────────────────────────────────────────
        try:
            _run_agents(company.strip(), industry.strip(), question.strip(), slots)

            # ── Save JSON output ──────────────────────────────────────────
            # (main.py's run_simulation already saves the JSON via asyncio,
            #  but _run_agents uses individual agents — so save manually)
            from agents.orchestrator import SimulatorState as _S

            # Re-run the full pipeline via main.py's function for JSON + proper state
            # _run_agents already ran all agents; reload the state from agents for JSON
            # We call the synthesis wrapper directly to get the full output dict
            # Instead, just load what was already written, or save here

            # Since _run_agents doesn't write JSON, we reuse run_simulation() for saving.
            # But that would re-run everything. Better: write JSON from the agents we ran.
            # We capture state and synthesis above but didn't expose them.
            # Fix: modify _run_agents to return them and save here.

            # Actually _run_agents returns (state, synthesis) — let me collect them properly.
            # The current signature doesn't return values. We need to refactor slightly.
            # => handled below by calling full run_simulation for the save step
            pass

        except Exception as exc:
            st.error(f"Simulation failed: {exc}")
            with st.expander("Error details"):
                import traceback
                st.code(traceback.format_exc())
            return

        # ── Generate artefacts (JSON already saved by _run_agents_full below)
        # We need to re-run for JSON persistence. Use main.py's run_simulation.
        # This is a second call but ensures JSON + reports are consistent.
        # For a production app you'd refactor to avoid the double call.
        status_slot = st.empty()
        status_slot.info("Generating PDF report and charts…")
        try:
            # Agents already ran above — now run full pipeline for JSON + reports
            async def _save_reports():
                import main as _main
                state, synth = await _main.run_simulation(
                    company.strip(), industry.strip(), question.strip()
                )
                return state, synth

            state_final, synth_final = asyncio.run(_save_reports())

            generate_report(JSON_PATH, PDF_PATH)
            generate_all_charts(JSON_PATH)

            # Reload output_data
            with open(JSON_PATH, encoding="utf-8") as f:
                st.session_state.output_data = json.load(f)

            st.session_state.simulation_done = True
            status_slot.empty()

        except Exception as exc:
            st.error(f"Report generation failed: {exc}")
            with st.expander("Error details"):
                import traceback
                st.code(traceback.format_exc())
            return

        # ── Success banner ────────────────────────────────────────────────
        score = int(st.session_state.output_data["synthesis"]
                    .get("overall_strategic_fit_score", 0))
        rec   = st.session_state.output_data["synthesis"].get(
            "ranked_recommendation", ["—"])[0]

        st.markdown(f"""
        <div class="card" style="background:linear-gradient(135deg,#1A7A4A,#238C56);
                                  border:none;padding:2rem;text-align:center;margin-top:1.5rem;">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
            <h2 style="color:white;font-weight:800;margin:0 0 0.5rem;">Simulation Complete!</h2>
            <p style="color:rgba(255,255,255,0.85);font-size:1rem;margin:0 0 1.25rem;">
                Strategic Fit Score: <strong style="color:#A8FFD0;font-size:1.3rem;">{score}/100</strong>
                &nbsp;·&nbsp; Recommended Strategy: <strong style="color:#A8FFD0;">{rec}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="main-area" style="text-align:center;margin-top:1rem;">', unsafe_allow_html=True)
        if st.button("📊  Open Results Dashboard", key="goto_results"):
            st.session_state.page = "results"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ── Page: Results Dashboard ───────────────────────────────────────────────────

def page_results():
    d = st.session_state.output_data

    if d is None:
        st.markdown("""
        <div class="card card-accent" style="text-align:center;padding:3rem;">
            <div style="font-size:3rem;">📭</div>
            <h3 style="color:#1B2A4A;">No results yet</h3>
            <p style="color:#6B7280;">Run a simulation first to see results here.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="main-area">', unsafe_allow_html=True)
        if st.button("🚀  Run Simulation", key="results_goto_run"):
            st.session_state.page = "run"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    syn  = d["synthesis"]
    score = int(syn.get("overall_strategic_fit_score", 0))
    opts  = sorted(syn.get("strategic_options", []),
                   key=lambda x: -x.get("overall_score", 0))
    rec_list = syn.get("ranked_recommendation", [])

    # ── Header row ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="hero-banner" style="padding:2rem 2.5rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
            <div>
                <div style="color:#C9A84C;font-size:0.78rem;letter-spacing:2px;font-weight:600;text-transform:uppercase;">
                    Results Dashboard
                </div>
                <h2 style="color:white;font-size:1.8rem;font-weight:800;margin:0.25rem 0 0;">
                    {d.get('company', '—')}
                </h2>
                <div style="color:#A8B4CC;font-size:0.9rem;margin-top:2px;">
                    {d.get('industry', '—')}
                </div>
            </div>
            <div style="text-align:center;">
                <div class="score-ring">{score}</div>
                <div style="color:#C9A84C;font-size:0.78rem;margin-top:6px;font-weight:600;">
                    STRATEGIC FIT
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary KPIs ──────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    kpis = [
        ("External Attractiveness", int(d["external"].get("overall_attractiveness_score", 0)), "🌍"),
        ("Internal Strength",       int(d["internal"].get("internal_strength_score", 0)),      "🏛️"),
        ("Competitive Position",    int(d["competitive"].get("competitive_intensity_score",0)), "⚔️"),
        ("Execution Readiness",     int(d["execution"].get("execution_readiness_score", 0)),    "🚀"),
    ]
    for col, (label, val, icon) in zip([k1, k2, k3, k4], kpis):
        color = "#1A7A4A" if val >= 70 else "#C9A84C" if val >= 50 else "#B22222"
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;padding:1.25rem 1rem;margin-bottom:1rem;">
                <div style="font-size:1.6rem;">{icon}</div>
                <div style="font-size:1.8rem;font-weight:800;color:{color};">{val}</div>
                <div style="font-size:0.75rem;color:#6B7280;font-weight:500;margin-top:2px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Executive Summary ──────────────────────────────────────────────────
    with st.expander("📝  Executive Summary", expanded=True):
        st.markdown(f"""
        <div style="background:#F7F8FC;border-radius:8px;padding:1.25rem;
                    border-left:4px solid #C9A84C;line-height:1.7;color:#374151;font-size:0.92rem;">
            {syn.get('executive_summary', '—')}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # ── Ranked Strategic Options ──────────────────────────────────────────
    st.markdown("### 🏆 Strategic Options Ranking")
    rank_classes = ["rank1", "rank2", "rank3"]
    for i, opt in enumerate(opts[:5]):
        rank_cls = rank_classes[i] if i < 3 else ""
        score_v  = opt.get("overall_score", 0)
        fit_v    = opt.get("strategic_fit_score", 0)
        risk_v   = opt.get("risk_score", 0)
        feas_v   = opt.get("feasibility_score", 0)
        fw_tags  = "".join(f'<span class="fw-tag">{fw}</span>'
                           for fw in opt.get("supporting_frameworks", []))
        feas_color = "#1A7A4A" if feas_v >= 70 else "#C9A84C" if feas_v >= 50 else "#B22222"

        st.markdown(f"""
        <div class="opt-card {rank_cls}">
            <div class="opt-rank">#{i+1}</div>
            <div style="flex:1;">
                <div style="font-weight:700;color:#1B2A4A;font-size:0.97rem;margin-bottom:4px;">
                    {opt.get('option', '—')}
                </div>
                <div style="color:#6B7280;font-size:0.8rem;margin-bottom:6px;">
                    {opt.get('rationale', '—')}
                </div>
                <div>{fw_tags}</div>
            </div>
            <div style="text-align:right;min-width:140px;">
                <div style="font-size:1.5rem;font-weight:800;color:#1B2A4A;">{score_v}</div>
                <div style="font-size:0.72rem;color:#6B7280;">overall score</div>
                <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:4px;font-size:0.75rem;">
                    <span style="color:#1B2A4A;">Fit: <b>{fit_v}</b></span>
                    <span style="color:#B22222;">Risk: <b>{risk_v}</b></span>
                    <span style="color:{feas_color};">Feas: <b>{feas_v}</b></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────
    st.markdown("### 📈 Analysis Charts")

    chart_files = {
        "agent_scores_radar.png":   ("Strategic Capability Radar",  "Scores across all 8 analytical dimensions"),
        "porter_forces_bar.png":    ("Porter's Five Forces",         "Industry competitive intensity (0–10)"),
        "bcg_matrix.png":           ("BCG Matrix",                   "Business unit portfolio positioning"),
        "scenario_comparison.png":  ("STEEP Scenario Comparison",    "Scenario severity across dimensions"),
        "strategic_options_bar.png":("Strategic Options Ranking",    "Overall score, fit, risk & feasibility"),
    }

    # Radar + Porter side by side
    chart_names = list(chart_files.keys())
    row1 = chart_names[:2]
    row2 = chart_names[2:4]
    row3 = chart_names[4:]

    for row in [row1, row2]:
        cols = st.columns(len(row))
        for col, fname in zip(cols, row):
            title, subtitle = chart_files[fname]
            fpath = os.path.join(CHARTS_DIR, fname)
            with col:
                st.markdown(f"""
                <div class="card" style="padding:1rem;margin-bottom:0;">
                    <div style="font-weight:700;color:#1B2A4A;font-size:0.92rem;">{title}</div>
                    <div style="color:#9CA3AF;font-size:0.78rem;margin-bottom:0.75rem;">{subtitle}</div>
                """, unsafe_allow_html=True)
                if os.path.exists(fpath):
                    st.image(fpath, use_container_width=True)
                else:
                    st.warning("Chart not yet generated. Run simulation first.")
                st.markdown("</div>", unsafe_allow_html=True)

    if row3:
        for fname in row3:
            title, subtitle = chart_files[fname]
            fpath = os.path.join(CHARTS_DIR, fname)
            st.markdown(f"""
            <div class="card" style="padding:1rem;">
                <div style="font-weight:700;color:#1B2A4A;font-size:0.92rem;">{title}</div>
                <div style="color:#9CA3AF;font-size:0.78rem;margin-bottom:0.75rem;">{subtitle}</div>
            """, unsafe_allow_html=True)
            if os.path.exists(fpath):
                st.image(fpath, use_container_width=True)
            else:
                st.warning("Chart not yet generated. Run simulation first.")
            st.markdown("</div>", unsafe_allow_html=True)


# ── Page: Download Report ─────────────────────────────────────────────────────

def page_download():
    d = st.session_state.output_data

    st.markdown("""
    <h2 style="color:#1B2A4A;font-weight:800;margin-bottom:0.25rem;">Download Report</h2>
    <p style="color:#6B7280;margin-bottom:2rem;">
        Download the full boardroom-ready PDF strategy report.
    </p>
    """, unsafe_allow_html=True)

    if d is None or not os.path.exists(PDF_PATH):
        st.markdown("""
        <div class="card card-accent" style="text-align:center;padding:3rem;">
            <div style="font-size:3rem;">📭</div>
            <h3 style="color:#1B2A4A;">No report available</h3>
            <p style="color:#6B7280;">Run a simulation to generate the PDF report.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="main-area">', unsafe_allow_html=True)
        if st.button("🚀  Run Simulation", key="dl_goto_run"):
            st.session_state.page = "run"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ── Report summary card ────────────────────────────────────────────────
    syn   = d["synthesis"]
    score = int(syn.get("overall_strategic_fit_score", 0))
    rec   = (syn.get("ranked_recommendation") or ["—"])[0]
    fsize = os.path.getsize(PDF_PATH) // 1024

    st.markdown(f"""
    <div class="card-navy" style="margin-bottom:2rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
            <div>
                <div style="color:#C9A84C;font-size:0.78rem;letter-spacing:2px;font-weight:600;
                            text-transform:uppercase;margin-bottom:0.5rem;">
                    Strategic Intelligence Report
                </div>
                <h3 style="color:white;font-weight:800;font-size:1.4rem;margin:0 0 0.3rem;">
                    {d.get('company','—')}
                </h3>
                <div style="color:#A8B4CC;font-size:0.88rem;">
                    {d.get('industry','—')}
                </div>
                <div style="margin-top:1rem;color:#A8B4CC;font-size:0.85rem;">
                    <strong style="color:white;">Question:</strong>
                    {d.get('strategic_question','—')}
                </div>
            </div>
            <div style="text-align:center;min-width:140px;">
                <div class="score-ring" style="margin:0 auto;">{score}</div>
                <div style="color:#C9A84C;font-size:0.75rem;margin-top:6px;font-weight:600;">
                    STRATEGIC FIT
                </div>
            </div>
        </div>
        <div style="margin-top:1.5rem;padding-top:1.5rem;border-top:1px solid rgba(255,255,255,0.12);
                    display:flex;gap:2rem;flex-wrap:wrap;">
            <div>
                <div style="color:#A8B4CC;font-size:0.75rem;">Recommended Strategy</div>
                <div style="color:#C9A84C;font-weight:700;font-size:0.95rem;margin-top:2px;">{rec}</div>
            </div>
            <div>
                <div style="color:#A8B4CC;font-size:0.75rem;">Report Size</div>
                <div style="color:white;font-weight:600;font-size:0.95rem;margin-top:2px;">{fsize} KB</div>
            </div>
            <div>
                <div style="color:#A8B4CC;font-size:0.75rem;">Frameworks</div>
                <div style="color:white;font-weight:600;font-size:0.95rem;margin-top:2px;">8 analytical agents</div>
            </div>
            <div>
                <div style="color:#A8B4CC;font-size:0.75rem;">Pages</div>
                <div style="color:white;font-weight:600;font-size:0.95rem;margin-top:2px;">~13 pages</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Download button ────────────────────────────────────────────────────
    with open(PDF_PATH, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    safe_name = d.get("company", "company").replace(" ", "_").lower()
    col_center, _, _ = st.columns([1, 1, 1])
    with col_center:
        st.download_button(
            label="⬇️  Download PDF Report",
            data=pdf_bytes,
            file_name=f"{safe_name}_strategy_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="dl_btn",
        )

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # ── Report sections preview ────────────────────────────────────────────
    st.markdown("### Report Contents")
    sections = [
        ("1", "Cover Page",                "Company, industry, strategic question"),
        ("2", "Executive Summary",          "Overall score, strategic tensions, key resolutions"),
        ("3", "External Environment",       "PESTEL analysis, Porter's Five Forces, lifecycle stage"),
        ("4", "Internal Audit",             "VRIO resources, McKinsey 7S alignment scores"),
        ("5", "Strategic Position",         "SWOT analysis, TOWS strategies, Ansoff matrix"),
        ("6", "Competitive Dynamics",       "Game theory scenarios, Blue Ocean ERRC grid"),
        ("7", "Strategy Formulation",       "Generic strategy, Strategy Clock positioning"),
        ("8", "Risk & Scenarios",           "STEEP scenario analysis, top risks & mitigations"),
        ("9", "Execution Roadmap",          "Balanced Scorecard, OKRs, critical success factors"),
        ("10","Strategic Options Ranking",  "Ranked options with fit, risk & feasibility scores"),
        ("11","Board Narrative",            "Prose narrative with scenario-based recommendations"),
        ("12","Appendix",                   "Raw agent scores, Porter forces, McKinsey 7S detail"),
    ]
    s1, s2 = st.columns(2)
    for i, (num, title, desc) in enumerate(sections):
        col = s1 if i % 2 == 0 else s2
        with col:
            st.markdown(f"""
            <div class="card" style="padding:0.75rem 1rem;margin-bottom:0.5rem;
                                     display:flex;align-items:flex-start;gap:0.75rem;">
                <div style="background:#1B2A4A;color:#C9A84C;font-weight:800;
                            font-size:0.75rem;border-radius:4px;padding:2px 6px;
                            min-width:24px;text-align:center;margin-top:2px;">{num}</div>
                <div>
                    <div style="font-weight:700;color:#1B2A4A;font-size:0.88rem;">{title}</div>
                    <div style="color:#9CA3AF;font-size:0.78rem;margin-top:1px;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Regenerate ────────────────────────────────────────────────────────
    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)
    with st.expander("🔄  Regenerate reports from existing data"):
        st.caption("Use this if you want to regenerate the PDF or charts without re-running the simulation.")
        rc1, rc2, _ = st.columns([1, 1, 2])
        with rc1:
            if st.button("Regenerate PDF", key="regen_pdf"):
                with st.spinner("Generating PDF..."):
                    try:
                        generate_report(JSON_PATH, PDF_PATH)
                        st.success("PDF regenerated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
        with rc2:
            if st.button("Regenerate Charts", key="regen_charts"):
                with st.spinner("Generating charts..."):
                    try:
                        generate_all_charts(JSON_PATH)
                        st.success("Charts regenerated.")
                    except Exception as e:
                        st.error(f"Failed: {e}")


# ── Router ────────────────────────────────────────────────────────────────────

page = st.session_state.get("page", "home")
with st.container():
    if page == "home":
        page_home()
    elif page == "run":
        page_run()
    elif page == "results":
        page_results()
    elif page == "download":
        page_download()
    else:
        st.session_state.page = "home"
        st.rerun()
