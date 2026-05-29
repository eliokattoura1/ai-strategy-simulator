"""
AI Strategy Simulator — Streamlit UI
Run: streamlit run ui/app.py
"""

import os
import sys
import json
import math
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
NAVY      = "#1B2A4A"
NAVY_DARK = "#0F1E35"
GOLD      = "#C9A84C"
GOLD_LT   = "#E0BE72"

GREEN = "#1A8A53"
AMBER = "#C9A84C"
RED   = "#C0392B"


# ── Formatting helpers ────────────────────────────────────────────────────────
def _score_color(val: float) -> str:
    """Green / amber / red color coding for a 0–100 score."""
    return GREEN if val >= 70 else AMBER if val >= 50 else RED


def _glow_for_score(val: float) -> str:
    """Box-shadow glow color depending on score band (for score rings)."""
    if val >= 75:
        return "0 0 28px rgba(26,138,83,0.55)"
    if val >= 50:
        return "0 0 28px rgba(201,168,76,0.55)"
    return "0 0 28px rgba(192,57,43,0.55)"


def _fmt_money(v) -> str:
    """Compact currency formatting: $72.8M, $1.2B, $450K."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if math.isinf(v) or math.isnan(v):
        return "—"
    av = abs(v)
    if av >= 1e9:
        return f"${v/1e9:.1f}B"
    if av >= 1e6:
        return f"${v/1e6:.1f}M"
    if av >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:,.0f}"


def _fmt_payback(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if math.isinf(v) or math.isnan(v):
        return "∞"
    return f"{v:.1f} yr"


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;1,500;1,600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── App background ─────────────────────────────────────────────────────── */
.stApp { background: #F0F2F8; }

/* ── Strip Streamlit default padding artifacts ──────────────────────────── */
.block-container { padding-top: 1.6rem !important; padding-bottom: 3rem !important; max-width: 1280px; }
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, [data-testid="stDeployButton"], [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stVerticalBlock"] { gap: 0.6rem; }

/* All interactive elements get a smooth transition */
button, a, .stButton > button, [data-testid="stDownloadButton"] > button,
.step-card, .fw-card, .opt-card, .sec-card, .agent-row {
    transition: all 0.2s ease !important;
}

.serif { font-family: 'Playfair Display', Georgia, serif !important; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0F1E35 !important;
    border-right: none;
    min-width: 232px !important;
}
[data-testid="stSidebar"] * { color: #E8EBF0; }
[data-testid="stSidebar"] hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(201,168,76,0.45), transparent) !important;
    margin: 1rem 0 !important;
}

/* Sidebar radio nav → pill items */
[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 4px !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent !important;
    border-radius: 10px !important;
    border-left: 3px solid transparent !important;
    padding: 0.5rem 0.8rem !important;
    cursor: pointer !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(201,168,76,0.15) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label span {
    color: #C4CCDA !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}
/* Active nav item */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]) {
    background: rgba(201,168,76,0.15) !important;
    border-left: 3px solid #C9A84C !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]) p,
[data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]) span {
    color: #C9A84C !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] [role="radio"] {
    accent-color: #C9A84C !important;
    border-color: #C9A84C !important;
}

/* ── Generic / nav buttons (navy → gold hover) ──────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1B2A4A 0%, #2C3F6A 100%);
    color: #fff !important;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 2rem;
    font-weight: 700;
    font-size: 0.96rem;
    letter-spacing: 0.2px;
    box-shadow: 0 4px 14px rgba(27,42,74,0.22);
}
.stButton > button:hover {
    background: linear-gradient(135deg, #C9A84C 0%, #E0BE72 100%);
    color: #0F1E35 !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(201,168,76,0.42);
}

/* Full-width CTA pill (Home) */
.cta-zone .stButton > button {
    width: 100%;
    height: 56px;
    border-radius: 28px;
    font-weight: 800;
    font-size: 1.05rem;
    background: linear-gradient(90deg, #0F1E35 0%, #1B2A4A 35%, #C9A84C 130%);
    color: #fff !important;
    box-shadow: 0 8px 26px rgba(15,30,53,0.35);
}
.cta-zone .stButton > button:hover {
    background: linear-gradient(90deg, #C9A84C 0%, #E0BE72 100%);
    color: #0F1E35 !important;
    transform: translateY(-2px);
}

/* Gold run button */
.gold-run .stButton > button {
    width: 100%;
    height: 60px;
    border-radius: 14px;
    background: linear-gradient(135deg, #C9A84C 0%, #E0BE72 100%);
    color: #0F1E35 !important;
    font-weight: 800;
    font-size: 1.12rem;
    box-shadow: 0 8px 24px rgba(201,168,76,0.42);
}
.gold-run .stButton > button:hover {
    background: #0F1E35;
    color: #C9A84C !important;
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(15,30,53,0.4);
}

/* ── Download button ────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    width: 100%;
    height: 64px;
    background: linear-gradient(135deg, #C9A84C 0%, #E0BE72 100%) !important;
    color: #0F1E35 !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 800 !important;
    font-size: 1.12rem !important;
    box-shadow: 0 8px 24px rgba(201,168,76,0.42) !important;
    background-size: 200% auto !important;
}
[data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 30px rgba(201,168,76,0.6) !important;
    background-position: right center !important;
    animation: shimmer 1.4s linear infinite;
}
@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

/* ── Form inputs ────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 2px solid #E0E4EE !important;
    border-radius: 10px !important;
    padding: 0.65rem 0.9rem !important;
    font-size: 0.95rem !important;
    background: #FCFCFE !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #C9A84C !important;
    box-shadow: 0 0 0 4px rgba(201,168,76,0.18) !important;
}
.stTextArea > div > div > textarea { min-height: 120px !important; }

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed rgba(201,168,76,0.55) !important;
    border-radius: 12px !important;
    background: #FBF8EF !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    background: #0F1E35 !important;
    border-color: #C9A84C !important;
}
[data-testid="stFileUploaderDropzone"]:hover * { color: #E8EBF0 !important; }

/* ── Card components ────────────────────────────────────────────────────── */
.card {
    background: #fff;
    border-radius: 16px;
    padding: 1.6rem 1.75rem;
    box-shadow: 0 4px 24px rgba(27,42,74,0.08);
    margin-bottom: 1.1rem;
}
.card-accent { border-left: 4px solid #C9A84C; }
.card-navy {
    background: #0F1E35;
    color: #fff;
    border-radius: 16px;
    padding: 1.9rem;
    box-shadow: 0 4px 24px rgba(15,30,53,0.25);
}

/* Section label above inputs */
.field-label {
    font-size: 0.7rem; font-weight: 700; color: #1B2A4A;
    text-transform: uppercase; letter-spacing: 1px;
    margin: 0.35rem 0 0.2rem;
}

/* ── Score rings ────────────────────────────────────────────────────────── */
.score-ring {
    display: inline-flex; flex-direction: column;
    align-items: center; justify-content: center;
    width: 120px; height: 120px;
    border-radius: 50%;
    background: radial-gradient(circle at 50% 40%, #1B2A4A, #0F1E35);
    border: 4px solid #C9A84C;
    color: #fff;
}
.score-ring .sr-num { font-size: 2.6rem; font-weight: 900; line-height: 1; }
.score-ring .sr-lbl { font-size: 0.55rem; letter-spacing: 1.5px; color: #C9A84C;
                      font-weight: 700; margin-top: 3px; text-transform: uppercase; }

/* ── Hero banners ───────────────────────────────────────────────────────── */
.hero {
    background: linear-gradient(120deg, #0F1E35 0%, #1B2A4A 50%, #0F1E35 100%);
    border-radius: 18px;
    padding: 2.6rem 3rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 30px rgba(15,30,53,0.25);
}
.hero::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #C9A84C, #E0BE72, #C9A84C);
}
.hero-sm { padding: 1.4rem 2.2rem; min-height: 80px; }
.eyebrow {
    color: #C9A84C; font-size: 0.62rem; letter-spacing: 3px;
    font-weight: 700; text-transform: uppercase;
}

/* Stat pills */
.stat-pill {
    display: inline-flex; flex-direction: column; align-items: center;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(201,168,76,0.3);
    border-radius: 12px; padding: 0.6rem 1.4rem; margin-right: 0.7rem;
}
.stat-pill .sp-num { color: #C9A84C; font-weight: 800; font-size: 1.3rem; line-height: 1; }
.stat-pill .sp-lbl { color: #A8B4CC; font-size: 0.68rem; letter-spacing: 0.5px; margin-top: 3px; }

/* ── Step cards (Home) ──────────────────────────────────────────────────── */
.step-card {
    background: #fff; border-radius: 16px; padding: 2rem 1.6rem;
    box-shadow: 0 4px 24px rgba(27,42,74,0.08);
    height: 100%; border-top: 4px solid #C9A84C;
}
.step-card:hover { transform: translateY(-6px); box-shadow: 0 14px 34px rgba(27,42,74,0.16); }
.step-num { font-family: 'Playfair Display', serif; font-size: 3rem; font-weight: 800;
            color: #C9A84C; line-height: 1; margin-bottom: 0.4rem; }

/* ── Framework cards ────────────────────────────────────────────────────── */
.fw-card {
    background: #fff; border-radius: 12px; padding: 0.95rem 1.2rem;
    margin-bottom: 0.7rem; box-shadow: 0 4px 24px rgba(27,42,74,0.06);
    border-left: 3px solid #C9A84C;
}
.fw-card:hover { background: #FFFBF0; border-left-color: #E0BE72; transform: translateX(3px); }

/* ── Agent progress rows ────────────────────────────────────────────────── */
.agent-row {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.6rem 0.85rem; border-radius: 10px; margin-bottom: 6px;
    font-size: 0.9rem; font-weight: 600;
}
.agent-row.pending { background: rgba(255,255,255,0.04); color: #7C8AA5; }
.agent-row.running { background: rgba(201,168,76,0.12); color: #E0BE72; }
.agent-row.done    { background: rgba(26,138,83,0.12);  color: #DCE5EF; }
.dot { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
.dot.gray  { background: #5A6B86; }
.dot.gold  { background: #E0BE72; box-shadow: 0 0 0 0 rgba(224,190,114,0.7); animation: pulse 1.3s infinite; }
.dot.green { background: #2ECC71; }
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(224,190,114,0.6); }
    70%  { box-shadow: 0 0 0 8px rgba(224,190,114,0); }
    100% { box-shadow: 0 0 0 0 rgba(224,190,114,0); }
}
.row-suffix { margin-left: auto; font-size: 0.74rem; font-weight: 600; }
.badge-done { background: rgba(46,204,113,0.18); color: #2ECC71; padding: 1px 9px;
              border-radius: 20px; font-size: 0.7rem; font-weight: 700; }

/* Coverage panel agent rows */
.cov-row { display: flex; align-items: center; gap: 0.6rem; padding: 0.45rem 0; }
.cov-name { color: #E8EBF0; font-weight: 600; font-size: 0.84rem; min-width: 96px; }
.cov-tags { color: #8895AE; font-size: 0.72rem; }

/* ── Progress bar ───────────────────────────────────────────────────────── */
.pbar-track { height: 8px; background: rgba(255,255,255,0.08); border-radius: 20px; overflow: hidden; }
.pbar-fill { height: 100%; border-radius: 20px;
             background: linear-gradient(90deg, #C9A84C, #E0BE72);
             transition: width 0.4s ease; }

/* ── Option ranking cards ───────────────────────────────────────────────── */
.opt-card {
    background: #fff; border-radius: 14px; padding: 1.25rem 1.6rem;
    margin-bottom: 0.85rem; box-shadow: 0 4px 24px rgba(27,42,74,0.08);
    border-left: 5px solid #D0D3DA; display: flex; align-items: center; gap: 1.2rem;
}
.opt-card.rank1 { border-left-color: #C9A84C; background: #FFFBF0; }
.opt-card.rank2 { border-left-color: #1B2A4A; }
.opt-card.rank3 { border-left-color: #6B7280; }
.opt-rank { font-family: 'Playfair Display', serif; font-size: 3rem; font-weight: 800;
            color: #C9A84C; min-width: 56px; text-align: center; line-height: 1; }

/* Pill badges */
.pill {
    display: inline-block; font-size: 0.72rem; font-weight: 700;
    padding: 3px 11px; border-radius: 20px; margin: 2px 3px 2px 0;
}
.pill-fit  { background: rgba(27,42,74,0.1);  color: #1B2A4A; }
.pill-risk { background: rgba(192,57,43,0.12); color: #C0392B; }
.pill-feas { background: rgba(26,138,83,0.12); color: #1A8A53; }
.fw-tag {
    display: inline-block; background: rgba(27,42,74,0.07); color: #1B2A4A;
    font-size: 0.7rem; font-weight: 600; padding: 2px 9px; border-radius: 20px; margin: 2px;
}

/* ── Gold divider ───────────────────────────────────────────────────────── */
.gold-hr {
    height: 2px; border: none; border-radius: 2px; margin: 1.6rem 0;
    background: linear-gradient(90deg, transparent, #C9A84C, transparent);
}

/* Section heading */
.sec-h { font-weight: 800; color: #1B2A4A; font-size: 1.25rem; margin: 0.5rem 0 0.4rem; }

/* Report contents section cards */
.sec-card {
    background: #fff; border-radius: 12px; padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem; box-shadow: 0 4px 24px rgba(27,42,74,0.06);
    border-left: 3px solid transparent; display: flex; align-items: flex-start; gap: 0.8rem;
}
.sec-card:hover { border-left-color: #C9A84C; transform: translateX(3px); }
.sec-badge { background: #0F1E35; color: #C9A84C; font-weight: 800; font-size: 0.78rem;
             border-radius: 8px; padding: 3px 9px; min-width: 28px; text-align: center; }
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
_NAV_OPTIONS = {
    "🏠  Home":               "home",
    "🚀  Run Simulation":     "run",
    "📊  Results Dashboard":  "results",
    "📄  Download Report":    "download",
}
_NAV_LABELS = list(_NAV_OPTIONS.keys())

with st.sidebar:
    st.markdown("""
    <div style="padding: 1.4rem 0.5rem 0.4rem; text-align: center;">
        <div class="serif" style="font-style:italic; font-size:1.25rem; font-weight:700;
                                   color:#C9A84C; line-height:1;">
            AI Strategy
        </div>
        <div style="font-size:0.5rem; color:#8A95AB; letter-spacing:3px;
                    margin-top:5px; font-weight:600;">
            SIMULATOR
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    _current_label = next(
        (k for k, v in _NAV_OPTIONS.items() if v == st.session_state.page),
        _NAV_LABELS[0],
    )
    _selected = st.radio(
        "Navigation",
        _NAV_LABELS,
        index=_NAV_LABELS.index(_current_label),
        key="nav_radio",
        label_visibility="collapsed",
    )
    if _NAV_OPTIONS[_selected] != st.session_state.page:
        st.session_state.page = _NAV_OPTIONS[_selected]
        st.rerun()

    st.markdown('<hr>', unsafe_allow_html=True)

    if st.session_state.output_data:
        d = st.session_state.output_data
        _sb_score = int(d['synthesis'].get('overall_strategic_fit_score', 0))
        st.markdown(f"""
        <div style="background:#162030; border-radius:12px; padding:1rem 1.1rem; margin:0 0.25rem;">
            <div style="font-size:0.6rem; color:#8A95AB; text-transform:uppercase;
                        letter-spacing:1.5px; margin-bottom:0.55rem;">Last Analysis</div>
            <div style="font-size:0.92rem; font-weight:700; color:#FFFFFF;">{d.get('company','—')}</div>
            <div style="font-size:0.72rem; color:#8A95AB; margin-top:2px;">{d.get('industry','—')}</div>
            <div style="margin-top:0.65rem; display:flex; align-items:center; gap:0.45rem;">
                <span style="background:#C9A84C; color:#0F1E35; font-weight:800; font-size:0.8rem;
                             border-radius:20px; padding:2px 10px;">{_sb_score}</span>
                <span style="font-size:0.72rem; color:#8A95AB;">/ 100 fit</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-top:1.4rem;">
        <div style="font-size:0.64rem; color:#5A6B86; letter-spacing:1px; font-weight:600;">
            v2.0 · FINANCE EDITION
        </div>
        <div style="font-size:0.58rem; color:#4A566A; margin-top:4px;">
            Powered by Claude AI
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Progress row markup helper (visual only) ──────────────────────────────────
def _progress_row_html(label: str, state: str) -> str:
    if state == "running":
        dot, cls = '<span class="dot gold"></span>', "running"
        suffix = '<span class="row-suffix" style="color:#E0BE72;">analyzing…</span>'
    elif state == "done":
        dot, cls = '<span class="dot green"></span>', "done"
        suffix = '<span class="row-suffix"><span class="badge-done">complete</span></span>'
    else:
        dot, cls = '<span class="dot gray"></span>', "pending"
        suffix = '<span class="row-suffix" style="color:#7C8AA5;">pending</span>'
    return (f'<div class="agent-row {cls}">{dot}<span>{label}</span>{suffix}</div>')


# ── Async agent runner ────────────────────────────────────────────────────────

def _run_agents(company: str, industry: str, question: str, slots: dict, company_name: str = None) -> tuple:
    """
    Run all agents sequentially (with gather for parallel pairs).
    `slots` maps step keys to st.empty() placeholders for live progress.
    Returns (SimulatorState, SynthesisOutput).
    """

    labels = {
        "ext_int":    "External + Internal Analysis",
        "position":   "Strategic Position",
        "competitive":"Competitive Dynamics",
        "formulation":"Strategy Formulation",
        "risk":       "Risk Assessment",
        "execution":  "Execution Planning",
        "synthesis":  "Synthesis & Ranking",
    }

    def _mark(key: str, state: str):
        slots[key].markdown(_progress_row_html(labels.get(key, key), state),
                            unsafe_allow_html=True)

    async def _main():
        sim_state = SimulatorState(
            company=company, industry=industry, strategic_question=question
        )

        # Build RAG context fetcher for progress-display run
        _rag_fetch = lambda q: None
        if company_name:
            print(f"[RAG] _run_agents: RAG enabled for company='{company_name}'")
            try:
                from rag.document_processor import query_context
                def _rag_fetch(q):
                    result = query_context(company_name, q)
                    return result if result else None
            except Exception as e:
                print(f"[RAG] _run_agents: failed to import query_context: {e}")
        else:
            print("[RAG] _run_agents: no company_name — RAG disabled")

        _mark("ext_int", "running")
        sim_state.external, sim_state.internal = await asyncio.gather(
            run_external_agent(company, industry, question,
                context=_rag_fetch("external environment PESTEL market trends competition regulatory political economic")),
            run_internal_agent(company, industry, question,
                context=_rag_fetch("internal capabilities resources operations technology staff financial performance")),
        )
        _mark("ext_int", "done")

        _mark("position", "running")
        sim_state.position = await run_position_agent(
            company, industry, question, sim_state.external, sim_state.internal,
            context=_rag_fetch("strategic position market share growth competitive advantages SWOT"),
        )
        _mark("position", "done")

        _mark("competitive", "running")
        sim_state.competitive = await run_competitive_agent(
            company, industry, question, sim_state.external, sim_state.position,
            context=_rag_fetch("competitors competitive strategy market dynamics pricing rivalry"),
        )
        _mark("competitive", "done")

        _mark("formulation", "running")
        sim_state.formulation = await run_formulation_agent(
            company, industry, question,
            sim_state.internal, sim_state.position, sim_state.competitive,
            context=_rag_fetch("strategy direction value proposition differentiation cost structure"),
        )
        _mark("formulation", "done")

        _mark("risk", "running")
        sim_state.risk = await run_risk_agent(
            company, industry, question, sim_state.external, sim_state.formulation,
            context=_rag_fetch("risks challenges threats uncertainties regulatory compliance"),
        )
        _mark("risk", "done")

        _mark("execution", "running")
        sim_state.execution = await run_execution_agent(
            company, industry, question, sim_state.formulation, sim_state.risk,
            context=_rag_fetch("implementation operations milestones KPIs execution roadmap initiatives"),
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
    <div class="hero">
        <div style="display:flex; align-items:center; justify-content:space-between;
                    flex-wrap:wrap; gap:2rem;">
            <div style="flex:1; min-width:320px;">
                <div class="eyebrow">Multi-Agent AI Platform</div>
                <h1 class="serif" style="color:#fff; font-size:3rem; font-weight:800;
                                         margin:0.6rem 0 0.5rem; line-height:1.05;">
                    AI Strategy Simulator
                </h1>
                <p style="color:#A8B4CC; font-size:1.05rem; line-height:1.6; margin:0; max-width:520px;">
                    From strategic question to boardroom report in 90 seconds.
                </p>
                <div style="margin-top:1.6rem;">
                    <span class="stat-pill"><span class="sp-num">8</span><span class="sp-lbl">AGENTS</span></span>
                    <span class="stat-pill"><span class="sp-num">15</span><span class="sp-lbl">FRAMEWORKS</span></span>
                    <span class="stat-pill"><span class="sp-num">90</span><span class="sp-lbl">SECONDS</span></span>
                </div>
            </div>
            <div style="text-align:center;">
                <div class="score-ring" style="width:148px; height:148px;
                     box-shadow:0 0 34px rgba(201,168,76,0.45);">
                    <span class="sr-num" style="font-size:3.4rem;">77</span>
                    <span class="sr-lbl">Strategic Fit</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    st.markdown('<div class="sec-h">How It Works</div>', unsafe_allow_html=True)
    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    cards = [
        ("01", "Define the Question",
         "Enter your company name, industry, and the strategic question you need answered. "
         "The system tailors all 8 analytical agents to your specific context.",
         "🎯"),
        ("02", "Multi-Agent Analysis",
         "Eight specialized AI agents run in parallel and sequence — covering external forces, "
         "internal capabilities, competitive dynamics, risk, execution, and finance.",
         "🤖"),
        ("03", "Boardroom Report",
         "Receive a ranked strategic recommendation, interactive charts, and a downloadable "
         "PDF report ready for executive presentation.",
         "📋"),
    ]
    for col, (num, title, desc, icon) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(f"""
            <div class="step-card">
                <div style="font-size:2rem; margin-bottom:0.3rem;">{icon}</div>
                <div class="step-num">{num}</div>
                <h3 style="color:#1B2A4A; font-size:1rem; font-weight:700; margin:0.4rem 0;">{title}</h3>
                <p style="color:#6B7280; font-size:0.86rem; line-height:1.6; margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # Frameworks grid
    st.markdown('<div class="sec-h">Analytical Frameworks Covered</div>', unsafe_allow_html=True)
    frameworks = [
        ("🌍", "PESTEL Analysis",       "Political, Economic, Social, Technological, Environmental, Legal"),
        ("⚔️",  "Porter's Five Forces",  "Industry structure & competitive intensity"),
        ("🔷", "VRIO Framework",         "Valuable, Rare, Inimitable, Organized resources"),
        ("🔄", "McKinsey 7S",            "Organizational alignment across 7 dimensions"),
        ("📐", "SWOT / TOWS",            "Position mapping & strategic direction generation"),
        ("🎮", "Game Theory",            "Competitor response modeling & Nash equilibria"),
        ("🌊", "Blue Ocean ERRC",        "Eliminate–Reduce–Raise–Create value innovation"),
        ("🎯", "Balanced Scorecard",     "KPIs, OKRs & execution roadmap"),
        ("💰", "DCF Valuation",          "NPV, IRR, terminal value & enterprise value"),
        ("📈", "Unit Economics",         "LTV/CAC, burn rate, runway & payback"),
    ]
    g1, g2 = st.columns(2)
    for i, (icon, name, desc) in enumerate(frameworks):
        col = g1 if i % 2 == 0 else g2
        with col:
            st.markdown(f"""
            <div class="fw-card">
                <div style="display:flex; align-items:flex-start; gap:0.8rem;">
                    <span style="font-size:1.3rem; line-height:1.2;">{icon}</span>
                    <div>
                        <div style="font-weight:700; color:#1B2A4A; font-size:0.9rem;">{name}</div>
                        <div style="color:#6B7280; font-size:0.78rem; margin-top:2px;">{desc}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="cta-zone">', unsafe_allow_html=True)
    if st.button("Launch Strategy Analysis  →", key="home_cta"):
        st.session_state.page = "run"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Page: Run Simulation ──────────────────────────────────────────────────────

def page_run():
    st.markdown("""
    <div class="hero hero-sm">
        <div class="eyebrow">Configure</div>
        <h2 class="serif" style="color:#fff; font-size:1.75rem; font-weight:700; margin:0.3rem 0 0;">
            Run Simulation
        </h2>
        <div style="color:#C9A84C; font-size:0.9rem; margin-top:2px; font-weight:600;">
            Configure your strategic analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Document uploader ─────────────────────────────────────────────────────
    st.markdown('<div class="field-label">📎 Company Documents (optional)</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload annual reports, news, or financials — indexed for RAG context",
        type=["pdf", "txt", "csv"],
        accept_multiple_files=True,
        key="doc_uploader",
        label_visibility="collapsed",
    )

    # ── Input form + coverage panel ───────────────────────────────────────────
    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        cc, ci = st.columns(2)
        with cc:
            st.markdown('<div class="field-label">Company Name</div>', unsafe_allow_html=True)
            company = st.text_input(
                "Company Name", value=st.session_state.sim_company,
                placeholder="e.g. Bank Audi", key="input_company",
                label_visibility="collapsed",
            )
        with ci:
            st.markdown('<div class="field-label">Industry</div>', unsafe_allow_html=True)
            industry = st.text_input(
                "Industry", value=st.session_state.sim_industry,
                placeholder="e.g. Lebanese Banking & Financial Services", key="input_industry",
                label_visibility="collapsed",
            )
        st.markdown('<div class="field-label">Strategic Question</div>', unsafe_allow_html=True)
        question = st.text_area(
            "Strategic Question", value=st.session_state.sim_question,
            placeholder="e.g. Should we expand into fintech or defend our core position?",
            height=120, key="input_question", label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        coverage = [
            ("#2ECC71", "External",    "PESTEL · Porter's · ILC"),
            ("#4DA3FF", "Internal",    "VRIO · McKinsey 7S · Value Chain"),
            ("#A06CFF", "Position",    "SWOT · BCG · Ansoff"),
            ("#FF8C42", "Competitive", "Game Theory · Blue Ocean"),
            ("#2BC4B8", "Formulation", "Bowman · Generic Strategy"),
            ("#E74C3C", "Risk",        "STEEP · Sensitivity"),
            ("#F1C40F", "Execution",   "BSC · OKRs"),
            ("#C9A84C", "Finance",     "DCF · LTV/CAC · Valuation"),
            ("#FFFFFF", "Synthesis",   "Conflict Resolution · Fit Score"),
        ]
        rows = "".join(
            f'<div class="cov-row"><span class="dot" style="background:{c};"></span>'
            f'<span class="cov-name">{n}</span><span class="cov-tags">{t}</span></div>'
            for c, n, t in coverage
        )
        st.markdown(f"""
        <div class="card-navy" style="padding:1.5rem 1.6rem;">
            <div style="color:#C9A84C; font-size:0.7rem; letter-spacing:2px; font-weight:700;
                        text-transform:uppercase; margin-bottom:0.9rem;">
                What Gets Analyzed
            </div>
            {rows}
            <div style="margin-top:1.1rem; padding-top:1rem;
                        border-top:1px solid rgba(255,255,255,0.1);
                        display:flex; justify-content:space-between;">
                <div>
                    <div style="color:#8895AE; font-size:0.66rem; text-transform:uppercase;
                                letter-spacing:1px;">Est. Cost</div>
                    <div style="color:#C9A84C; font-weight:800; font-size:1rem;">$0.50–2.00</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#8895AE; font-size:0.66rem; text-transform:uppercase;
                                letter-spacing:1px;">Est. Time</div>
                    <div style="color:#E8EBF0; font-weight:800; font-size:1rem;">60–120 sec</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:0.6rem;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="gold-run">', unsafe_allow_html=True)
    run_clicked = st.button("Run AI Strategy Simulation  →", key="run_btn")
    st.markdown("</div>", unsafe_allow_html=True)

    if run_clicked:
        if not company.strip() or not industry.strip() or not question.strip():
            st.error("Please fill in all three fields before running the simulation.")
            return

        # Persist inputs
        st.session_state.sim_company  = company.strip()
        st.session_state.sim_industry = industry.strip()
        st.session_state.sim_question = question.strip()

        # ── Process uploaded documents ────────────────────────────────────
        rag_company = None
        if uploaded_files:
            try:
                from rag.document_processor import process_documents
                with st.spinner("Indexing documents…"):
                    rag_chunks = process_documents(uploaded_files, company.strip())
                st.success(f"📚 {rag_chunks} document chunks indexed")
                rag_company = company.strip()
            except Exception as rag_exc:
                st.warning(f"Document indexing failed — simulation will continue without RAG context. ({rag_exc})")

        # ── Progress display ──────────────────────────────────────────────
        step_keys = ["ext_int", "position", "competitive",
                     "formulation", "risk", "execution", "synthesis"]
        labels = {
            "ext_int":    "External + Internal Analysis",
            "position":   "Strategic Position",
            "competitive":"Competitive Dynamics",
            "formulation":"Strategy Formulation",
            "risk":       "Risk Assessment",
            "execution":  "Execution Planning",
            "synthesis":  "Synthesis & Ranking",
        }

        st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

        prog_col, stat_col = st.columns([3, 1], gap="large")

        with prog_col:
            st.markdown(f"""
            <div class="card-navy" style="padding:1.4rem 1.6rem; margin-bottom:0;">
                <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem;">
                    <span class="dot gold"></span>
                    <span style="color:#fff; font-weight:700; font-size:1.05rem;">Analysis in Progress</span>
                    <span style="color:#8895AE; font-size:0.82rem; margin-left:auto;">{company.strip()}</span>
                </div>
            """, unsafe_allow_html=True)
            slots = {k: st.empty() for k in step_keys}
            for k in step_keys:
                slots[k].markdown(_progress_row_html(labels[k], "pending"), unsafe_allow_html=True)
            st.markdown("""
                <div style="margin-top:1rem;" class="pbar-track">
                    <div class="pbar-fill" style="width:100%; opacity:0.85;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with stat_col:
            st.markdown("""
            <div class="card-navy" style="padding:1.4rem 1.3rem; margin-bottom:0; text-align:center;">
                <div style="color:#8895AE; font-size:0.66rem; text-transform:uppercase;
                            letter-spacing:1.5px;">Live Status</div>
                <div style="font-size:2rem; margin:0.6rem 0;">⏱️</div>
                <div style="color:#C9A84C; font-weight:800; font-size:0.95rem;">Running…</div>
                <div style="color:#8895AE; font-size:0.74rem; margin-top:0.5rem;">
                    Avg 60–120 sec
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Run agents ────────────────────────────────────────────────────
        try:
            _run_agents(company.strip(), industry.strip(), question.strip(), slots, company_name=rag_company)
        except Exception as exc:
            st.error(f"Simulation failed: {exc}")
            with st.expander("Error details"):
                import traceback
                st.code(traceback.format_exc())
            return

        # ── Generate artefacts (JSON persisted via main.run_simulation) ────
        status_slot = st.empty()
        status_slot.info("Generating PDF report and charts…")
        try:
            # Agents already ran above — now run full pipeline for JSON + reports
            async def _save_reports():
                import main as _main
                state, synth = await _main.run_simulation(
                    company.strip(), industry.strip(), question.strip(),
                    company_name=rag_company,
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
        <div class="card" style="background:linear-gradient(135deg,#0F1E35,#1B2A4A);
                                  border:none; border-top:4px solid #C9A84C;
                                  padding:2rem; text-align:center; margin-top:1.5rem;">
            <div style="font-size:2.4rem; margin-bottom:0.4rem;">✅</div>
            <h2 class="serif" style="color:#fff; font-weight:700; margin:0 0 0.5rem;">Simulation Complete</h2>
            <p style="color:#A8B4CC; font-size:1rem; margin:0;">
                Strategic Fit: <strong style="color:#C9A84C; font-size:1.25rem;">{score}/100</strong>
                &nbsp;·&nbsp; Recommended: <strong style="color:#C9A84C;">{rec}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📊  Open Results Dashboard", key="goto_results"):
            st.session_state.page = "results"
            st.rerun()


# ── Page: Results Dashboard ───────────────────────────────────────────────────

def page_results():
    d = st.session_state.output_data

    if d is None:
        st.markdown("""
        <div class="card card-accent" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem;">📭</div>
            <h3 style="color:#1B2A4A;">No results yet</h3>
            <p style="color:#6B7280;">Run a simulation first to see results here.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀  Run Simulation", key="results_goto_run"):
            st.session_state.page = "run"
            st.rerun()
        return

    syn  = d["synthesis"]
    score = int(syn.get("overall_strategic_fit_score", 0))
    opts  = sorted(syn.get("strategic_options", []),
                   key=lambda x: -x.get("overall_score", 0))

    # ── Header / hero ──────────────────────────────────────────────────────
    glow = _glow_for_score(score)
    st.markdown(f"""
    <div class="hero hero-sm" style="padding:1.8rem 2.5rem;">
        <div style="display:flex; align-items:center; justify-content:space-between;
                    flex-wrap:wrap; gap:1rem;">
            <div>
                <div class="eyebrow">Results Dashboard</div>
                <h2 class="serif" style="color:#fff; font-size:2rem; font-weight:700; margin:0.3rem 0 0;">
                    {d.get('company', '—')}
                </h2>
                <div style="color:#A8B4CC; font-size:0.9rem; margin-top:2px;">{d.get('industry', '—')}</div>
            </div>
            <div class="score-ring" style="box-shadow:{glow};">
                <span class="sr-num">{score}</span>
                <span class="sr-lbl">Strategic Fit</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row (4 core + Finance Fit) ─────────────────────────────────────
    fin = d.get("finance") or {}
    kpis = [
        ("External Attractiveness", int(d["external"].get("overall_attractiveness_score", 0)), "🌍", None),
        ("Internal Strength",       int(d["internal"].get("internal_strength_score", 0)),      "🏛️", None),
        ("Competitive Position",    int(d["competitive"].get("competitive_intensity_score",0)), "⚔️", None),
        ("Execution Readiness",     int(d["execution"].get("execution_readiness_score", 0)),    "🚀", None),
    ]
    if fin:
        kpis.append(("Financial Fit", int(fin.get("financial_fit_score", 0)), "💰", GOLD))

    kcols = st.columns(len(kpis))
    for col, (label, val, icon, force_border) in zip(kcols, kpis):
        color = force_border or _score_color(val)
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center; padding:1.2rem 0.8rem; margin-bottom:0.6rem;
                                     border-bottom:4px solid {color};">
                <div style="font-size:1.5rem;">{icon}</div>
                <div style="font-size:2.6rem; font-weight:800; color:{color}; line-height:1.1;">{val}</div>
                <div style="font-size:0.66rem; color:#6B7280; font-weight:700; text-transform:uppercase;
                            letter-spacing:0.5px; margin-top:2px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Executive Summary ──────────────────────────────────────────────────
    with st.expander("📝  Executive Summary", expanded=True):
        st.markdown(f"""
        <div class="card-accent serif" style="background:#FFFBF0; border-radius:10px; padding:1.4rem 1.6rem;
                    font-style:italic; line-height:1.75; color:#374151; font-size:1.02rem;">
            {syn.get('executive_summary', '—')}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # ── Ranked Strategic Options ──────────────────────────────────────────
    st.markdown('<div class="sec-h">🏆 Strategic Options Ranking</div>', unsafe_allow_html=True)
    rank_classes = ["rank1", "rank2", "rank3"]
    for i, opt in enumerate(opts[:5]):
        rank_cls = rank_classes[i] if i < 3 else ""
        score_v  = opt.get("overall_score", 0)
        fit_v    = opt.get("strategic_fit_score", 0)
        risk_v   = opt.get("risk_score", 0)
        feas_v   = opt.get("feasibility_score", 0)
        fw_tags  = "".join(f'<span class="fw-tag">{fw}</span>'
                           for fw in opt.get("supporting_frameworks", []))
        sc_color = _score_color(score_v)

        st.markdown(f"""
        <div class="opt-card {rank_cls}">
            <div class="opt-rank">{i+1}</div>
            <div style="flex:1;">
                <div style="font-weight:700; color:#1B2A4A; font-size:1rem; margin-bottom:4px;">
                    {opt.get('option', '—')}
                </div>
                <div style="color:#6B7280; font-size:0.84rem; margin-bottom:8px; line-height:1.5;">
                    {opt.get('rationale', '—')}
                </div>
                <div>
                    <span class="pill pill-fit">Fit {fit_v}</span>
                    <span class="pill pill-risk">Risk {risk_v}</span>
                    <span class="pill pill-feas">Feasibility {feas_v}</span>
                </div>
                <div style="margin-top:6px;">{fw_tags}</div>
            </div>
            <div style="text-align:center; min-width:90px;">
                <div style="width:74px; height:74px; border-radius:50%; margin:0 auto;
                            display:flex; flex-direction:column; align-items:center; justify-content:center;
                            border:4px solid {sc_color}; color:{sc_color};">
                    <span style="font-size:1.5rem; font-weight:800; line-height:1;">{score_v}</span>
                </div>
                <div style="font-size:0.64rem; color:#9CA3AF; margin-top:5px; text-transform:uppercase;
                            letter-spacing:0.5px;">Overall</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Finance Section ────────────────────────────────────────────────────
    if d.get("finance"):
        st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

        dcf = fin.get("dcf", {})
        ue  = (fin.get("burn", {}) or {}).get("unit_economics", {})
        val = fin.get("valuation", {})
        go_signal = fin.get("go_signal", "—")
        go_lc = go_signal.lower()
        go_color = GREEN if "go" in go_lc and "no" not in go_lc and "conditional" not in go_lc \
                   else AMBER if "conditional" in go_lc else RED

        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
                    flex-wrap:wrap; gap:0.6rem; margin-bottom:0.3rem;">
            <div class="sec-h" style="margin:0;">💰 Financial Viability</div>
            <span style="background:{go_color}; color:#fff; font-weight:800; font-size:0.82rem;
                         padding:5px 16px; border-radius:20px; letter-spacing:0.5px;">{go_signal}</span>
        </div>
        """, unsafe_allow_html=True)

        # Finance KPI strip — NPV | IRR | Payback | LTV/CAC
        npv = dcf.get("npv", 0)
        irr = dcf.get("irr", 0)
        payback = dcf.get("payback_period_years", float("inf"))
        ltv_cac = ue.get("ltv_cac_ratio", 0)

        npv_color = GREEN if (isinstance(npv, (int, float)) and npv > 0) else RED
        irr_color = GREEN if (isinstance(irr, (int, float)) and irr >= 10) else \
                    AMBER if (isinstance(irr, (int, float)) and irr >= 0) else RED
        pb_color  = RED if (isinstance(payback, float) and math.isinf(payback)) else \
                    GREEN if (isinstance(payback, (int, float)) and payback <= 3) else AMBER
        lc_color  = GREEN if (isinstance(ltv_cac, (int, float)) and ltv_cac >= 3) else \
                    AMBER if (isinstance(ltv_cac, (int, float)) and ltv_cac >= 1) else RED

        fin_kpis = [
            ("NPV", _fmt_money(npv), npv_color),
            ("IRR", f"{irr:.1f}%" if isinstance(irr, (int, float)) else "—", irr_color),
            ("Payback", _fmt_payback(payback), pb_color),
            ("LTV / CAC", f"{ltv_cac:.1f}x" if isinstance(ltv_cac, (int, float)) else "—", lc_color),
        ]
        fcols = st.columns(4)
        for col, (label, value, color) in zip(fcols, fin_kpis):
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center; padding:1.2rem 0.7rem; margin-bottom:0.7rem;">
                    <div style="font-size:0.66rem; color:#6B7280; font-weight:700; text-transform:uppercase;
                                letter-spacing:1px;">{label}</div>
                    <div style="font-size:1.9rem; font-weight:800; color:{color}; margin-top:4px;">{value}</div>
                </div>
                """, unsafe_allow_html=True)

        # Valuation range — Bear / Base / Bull
        low  = val.get("implied_valuation_low")
        mid  = val.get("implied_valuation_mid")
        high = val.get("implied_valuation_high")
        if low is not None or mid is not None or high is not None:
            st.markdown('<div style="font-weight:700; color:#1B2A4A; font-size:0.9rem; margin:0.4rem 0 0.5rem;">Implied Valuation Range</div>', unsafe_allow_html=True)
            vcols = st.columns(3)
            valuation_rows = [
                ("Bear", low, RED),
                ("Base", mid, NAVY),
                ("Bull", high, GREEN),
            ]
            for col, (label, value, color) in zip(vcols, valuation_rows):
                with col:
                    st.markdown(f"""
                    <div class="card" style="text-align:center; padding:1.1rem 0.7rem; margin-bottom:0.7rem;">
                        <div style="font-size:0.66rem; color:#6B7280; font-weight:700; text-transform:uppercase;
                                    letter-spacing:1px;">{label}</div>
                        <div style="font-size:1.7rem; font-weight:800; color:{color}; margin-top:4px;">
                            {_fmt_money(value)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # CFO summary
        cfo = fin.get("cfo_summary")
        if cfo:
            st.markdown(f"""
            <div class="card-accent serif" style="background:#FFFBF0; border-radius:10px;
                        padding:1.3rem 1.5rem; font-style:italic; line-height:1.7;
                        color:#374151; font-size:0.98rem;">
                <span style="font-style:normal; font-weight:700; color:#C9A84C; font-family:Inter;
                             font-size:0.72rem; letter-spacing:1px; text-transform:uppercase;">CFO Summary</span><br>
                {cfo}
            </div>
            """, unsafe_allow_html=True)

        # Finance charts
        finance_charts = {
            "fcf_cumulative.png":  ("Cumulative Free Cash Flow", "Projected FCF accumulation over the forecast horizon"),
            "valuation_comps.png": ("Valuation Comparables",     "Subject multiples vs. comparable companies"),
            "dcf_waterfall.png":   ("DCF Waterfall",             "From enterprise value to net present value"),
        }
        for fname, (title, subtitle) in finance_charts.items():
            fpath = os.path.join(CHARTS_DIR, fname)
            if os.path.exists(fpath):
                st.markdown(f"""
                <div class="card" style="padding:1.2rem 1.4rem;">
                    <div style="font-weight:700; color:#1B2A4A; font-size:0.92rem;">{title}</div>
                    <div style="color:#9CA3AF; font-size:0.78rem; margin-bottom:0.75rem;">{subtitle}</div>
                """, unsafe_allow_html=True)
                st.image(fpath, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-h">📈 Analysis Charts</div>', unsafe_allow_html=True)

    chart_files = {
        "agent_scores_radar.png":   ("Strategic Capability Radar",  "Scores across all analytical dimensions"),
        "porter_forces_bar.png":    ("Porter's Five Forces",         "Industry competitive intensity (0–10)"),
        "bcg_matrix.png":           ("BCG Matrix",                   "Business unit portfolio positioning"),
        "scenario_comparison.png":  ("STEEP Scenario Comparison",    "Scenario severity across dimensions"),
        "strategic_options_bar.png":("Strategic Options Ranking",    "Overall score, fit, risk & feasibility"),
    }
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
                <div class="card" style="padding:1.1rem 1.2rem; margin-bottom:0;">
                    <div style="font-weight:700; color:#1B2A4A; font-size:0.9rem;">{title}</div>
                    <div style="color:#9CA3AF; font-size:0.78rem; margin-bottom:0.75rem;">{subtitle}</div>
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
            <div class="card" style="padding:1.1rem 1.2rem;">
                <div style="font-weight:700; color:#1B2A4A; font-size:0.9rem;">{title}</div>
                <div style="color:#9CA3AF; font-size:0.78rem; margin-bottom:0.75rem;">{subtitle}</div>
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
    <div class="hero hero-sm">
        <div class="eyebrow">Export</div>
        <h2 class="serif" style="color:#fff; font-size:1.75rem; font-weight:700; margin:0.3rem 0 0;">
            Download Report
        </h2>
        <div style="color:#C9A84C; font-size:0.9rem; margin-top:2px; font-weight:600;">
            Boardroom-ready PDF strategy report
        </div>
    </div>
    """, unsafe_allow_html=True)

    if d is None or not os.path.exists(PDF_PATH):
        st.markdown("""
        <div class="card card-accent" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem;">📭</div>
            <h3 style="color:#1B2A4A;">No report available</h3>
            <p style="color:#6B7280;">Run a simulation to generate the PDF report.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀  Run Simulation", key="dl_goto_run"):
            st.session_state.page = "run"
            st.rerun()
        return

    # ── Report summary card ────────────────────────────────────────────────
    syn   = d["synthesis"]
    score = int(syn.get("overall_strategic_fit_score", 0))
    rec   = (syn.get("ranked_recommendation") or ["—"])[0]
    fsize = os.path.getsize(PDF_PATH) // 1024
    glow  = _glow_for_score(score)

    st.markdown(f"""
    <div class="card-navy" style="margin-bottom:1.6rem;">
        <div style="display:flex; align-items:center; justify-content:space-between;
                    flex-wrap:wrap; gap:1rem;">
            <div style="flex:1; min-width:260px;">
                <div class="eyebrow">Strategic Intelligence Report</div>
                <h3 class="serif" style="color:#fff; font-weight:700; font-size:1.8rem; margin:0.5rem 0 0.3rem;">
                    {d.get('company','—')}
                </h3>
                <div style="color:#A8B4CC; font-size:0.88rem;">{d.get('industry','—')}</div>
                <div style="margin-top:1rem; color:#A8B4CC; font-size:0.85rem; line-height:1.5;">
                    <strong style="color:#fff;">Question:</strong> {d.get('strategic_question','—')}
                </div>
            </div>
            <div class="score-ring" style="width:100px; height:100px; box-shadow:{glow};">
                <span class="sr-num" style="font-size:2.2rem;">{score}</span>
                <span class="sr-lbl">Fit</span>
            </div>
        </div>
        <div style="margin-top:1.5rem; padding-top:1.4rem; border-top:1px solid rgba(255,255,255,0.12);
                    display:flex; gap:1.2rem; flex-wrap:wrap;">
            <div style="background:#162030; border-radius:10px; padding:0.7rem 1.1rem; min-width:120px;">
                <div style="color:#8895AE; font-size:0.62rem; text-transform:uppercase; letter-spacing:1px;">Score</div>
                <div style="color:#C9A84C; font-weight:800; font-size:1.05rem; margin-top:3px;">{score}/100</div>
            </div>
            <div style="background:#162030; border-radius:10px; padding:0.7rem 1.1rem; min-width:160px;">
                <div style="color:#8895AE; font-size:0.62rem; text-transform:uppercase; letter-spacing:1px;">Recommendation</div>
                <div style="color:#fff; font-weight:700; font-size:0.95rem; margin-top:3px;">{rec}</div>
            </div>
            <div style="background:#162030; border-radius:10px; padding:0.7rem 1.1rem; min-width:90px;">
                <div style="color:#8895AE; font-size:0.62rem; text-transform:uppercase; letter-spacing:1px;">Pages</div>
                <div style="color:#fff; font-weight:700; font-size:0.95rem; margin-top:3px;">~13</div>
            </div>
            <div style="background:#162030; border-radius:10px; padding:0.7rem 1.1rem; min-width:110px;">
                <div style="color:#8895AE; font-size:0.62rem; text-transform:uppercase; letter-spacing:1px;">File Size</div>
                <div style="color:#fff; font-weight:700; font-size:0.95rem; margin-top:3px;">{fsize} KB</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Download button ────────────────────────────────────────────────────
    with open(PDF_PATH, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    safe_name = d.get("company", "company").replace(" ", "_").lower()
    st.download_button(
        label="⬇  Download Board Report — PDF",
        data=pdf_bytes,
        file_name=f"{safe_name}_strategy_report.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="dl_btn",
    )

    st.markdown('<div class="gold-hr"></div>', unsafe_allow_html=True)

    # ── Report sections preview ────────────────────────────────────────────
    st.markdown('<div class="sec-h">Report Contents</div>', unsafe_allow_html=True)
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
        ("10","Financial Viability",        "DCF, valuation comps, unit economics & CFO summary"),
        ("11","Strategic Options Ranking",  "Ranked options with fit, risk & feasibility scores"),
        ("12","Board Narrative",            "Prose narrative with scenario-based recommendations"),
    ]
    s1, s2 = st.columns(2)
    for i, (num, title, desc) in enumerate(sections):
        col = s1 if i % 2 == 0 else s2
        with col:
            st.markdown(f"""
            <div class="sec-card">
                <div class="sec-badge">{num}</div>
                <div>
                    <div style="font-weight:700; color:#1B2A4A; font-size:0.88rem;">{title}</div>
                    <div style="color:#9CA3AF; font-size:0.78rem; margin-top:1px;">{desc}</div>
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
