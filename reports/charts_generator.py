"""
AI Strategy Simulator — Plotly Chart Generator
Entry point: generate_all_charts(json_path)
Saves five PNG charts to reports/charts/.
"""

import json
import math
import os

import plotly.graph_objects as go
import plotly.io as pio

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY   = "#1B2A4A"
GOLD   = "#C9A84C"
LGRAY  = "#F5F5F5"
MGRAY  = "#D0D3DA"
DGRAY  = "#6B7280"
WHITE  = "#FFFFFF"

QUADRANT_COLORS = {
    "star":          "#1A7A4A",
    "cash cow":      "#1B2A4A",
    "question mark": "#C9A84C",
    "dog":           "#B22222",
}

FEASIBILITY_COLORS = {
    "high":   "#1A7A4A",
    "medium": "#C9A84C",
    "low":    "#B22222",
}

W, H = 1200, 800

_LAYOUT_BASE = dict(
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    font=dict(family="Helvetica, Arial, sans-serif", color=NAVY),
    title_font=dict(size=20, color=NAVY, family="Helvetica, Arial, sans-serif"),
    margin=dict(l=80, r=60, t=80, b=60),
)


def _save(fig: go.Figure, path: str) -> None:
    pio.write_image(fig, path, format="png", width=W, height=H, scale=1.5)
    print(f"  saved: {path}")


# ── 1. Porter's Five Forces ───────────────────────────────────────────────────

def _porter_bar(data: dict, out: str) -> None:
    forces = data["external"]["porter_forces"]
    labels = [(f["force"][:28] + "…") if len(f["force"]) > 28 else f["force"] for f in forces]
    scores = [f["score"] for f in forces]
    intensities = [f["intensity"].capitalize() for f in forces]

    bar_colors = [
        "#B22222" if i == "High" else GOLD if i == "Medium" else "#1A7A4A"
        for i in intensities
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scores,
        y=labels,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color=NAVY, width=0.8),
        ),
        text=[f"{s:.1f}  ({i})" for s, i in zip(scores, intensities)],
        textposition="outside",
        textfont=dict(size=11, color=NAVY),
        cliponaxis=False,
    ))

    # Gold vertical line at 5 (neutral midpoint)
    fig.add_vline(x=5, line=dict(color=GOLD, width=1.5, dash="dot"))
    fig.add_annotation(
        x=5, y=len(labels),
        text="Neutral", showarrow=False,
        font=dict(size=9, color=GOLD), xanchor="center",
    )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Porter's Five Forces Analysis", x=0.5, xanchor="center"),
        xaxis=dict(
            title="Score (0 = Low Threat, 10 = High Threat)",
            range=[0, 12],
            showgrid=True,
            gridcolor=MGRAY,
            zeroline=False,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            tickfont=dict(size=12),
        ),
        showlegend=False,
        height=H,
        width=W,
    )
    fig.update_layout(margin=dict(l=160))
    _save(fig, out)


# ── 2. Strategic Capability Radar ─────────────────────────────────────────────

def _radar(data: dict, out: str) -> None:
    ext  = data["external"]
    intn = data["internal"]
    pos  = data["position"]
    comp = data["competitive"]
    form = data["formulation"]
    risk = data["risk"]
    exec_ = data["execution"]
    syn  = data["synthesis"]

    categories = [
        "External\nAttractiveness",
        "Internal\nStrength",
        "Strategic\nPosition",
        "Competitive\nDynamics",
        "Strategy\nFormulation",
        "Risk\nAssessment",
        "Execution\nReadiness",
        "Overall\nFit",
    ]
    categories = [(c[:28] + "…") if len(c) > 28 else c for c in categories]
    values = [
        float(ext.get("overall_attractiveness_score", 0)),
        float(intn.get("internal_strength_score", 0)),
        float(pos.get("strategic_position_score", 0)),
        float(comp.get("competitive_intensity_score", 0)),
        float(form.get("formulation_confidence_score", 0)),
        float(risk.get("risk_score", 0)),
        float(exec_.get("execution_readiness_score", 0)),
        float(syn.get("overall_strategic_fit_score", 0)),
    ]
    # Close the polygon
    cats_closed  = categories + [categories[0]]
    vals_closed  = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor=f"rgba(27,42,74,0.18)",
        line=dict(color=GOLD, width=2.5),
        marker=dict(size=6, color=NAVY),
        name="Score",
    ))

    # Benchmark ring at 70
    benchmark = [70] * (len(categories) + 1)
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=cats_closed,
        fill="none",
        line=dict(color=GOLD, width=1, dash="dot"),
        name="Benchmark (70)",
        mode="lines",
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Strategic Capability Radar", x=0.5, xanchor="center"),
        polar=dict(
            bgcolor=LGRAY,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                tickfont=dict(size=9, color=DGRAY),
                gridcolor=MGRAY,
                linecolor=MGRAY,
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=NAVY),
                gridcolor=MGRAY,
                linecolor=MGRAY,
            ),
        ),
        legend=dict(
            x=1.05, y=0.5,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=H,
        width=W,
    )
    fig.update_layout(margin=dict(l=160))
    _save(fig, out)


# ── 3. BCG Matrix ─────────────────────────────────────────────────────────────

def _bcg(data: dict, out: str) -> None:
    positions = data["position"].get("bcg_positions", [])

    fig = go.Figure()

    # Quadrant background rectangles
    quadrant_bg = [
        dict(name="Star",          x=[0.5, 1], y=[0.05, 1],  color="rgba(26,122,74,0.07)"),
        dict(name="Question Mark", x=[0, 0.5], y=[0.05, 1],  color="rgba(201,168,76,0.07)"),
        dict(name="Cash Cow",      x=[0.5, 1], y=[0, 0.05],  color="rgba(27,42,74,0.07)"),
        dict(name="Dog",           x=[0, 0.5], y=[0, 0.05],  color="rgba(178,34,34,0.07)"),
    ]
    for q in quadrant_bg:
        x0, x1 = q["x"]
        y0, y1 = q["y"]
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=q["color"], line=dict(width=0), layer="below")

    # Quadrant dividers
    fig.add_hline(y=0.05, line=dict(color=MGRAY, width=1.5, dash="dot"))
    fig.add_vline(x=0.5,  line=dict(color=MGRAY, width=1.5, dash="dot"))

    # Quadrant labels
    quadrant_labels = [
        ("STAR",          0.75, 0.90, "#1A7A4A"),
        ("QUESTION MARK", 0.25, 0.90, "#B8860B"),
        ("CASH COW",      0.75, 0.02, NAVY),
        ("DOG",           0.25, 0.02, "#B22222"),
    ]
    for label, lx, ly, lc in quadrant_labels:
        fig.add_annotation(
            x=lx, y=ly, text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=11, color=lc),
            opacity=0.55,
        )

    # Scatter points
    for p in positions:
        share  = float(p.get("market_share", 0.5))
        growth = float(p.get("market_growth", 0.05))
        quad   = p.get("quadrant", "").lower()
        color  = QUADRANT_COLORS.get(quad, NAVY)

        fig.add_trace(go.Scatter(
            x=[share], y=[growth],
            mode="markers+text",
            marker=dict(size=22, color=color,
                        line=dict(color=WHITE, width=2)),
            text=[p.get("unit", "")],
            textposition="top center",
            textfont=dict(size=10, color=NAVY),
            name=p.get("unit", ""),
            hovertemplate=(
                f"<b>{p.get('unit','')}</b><br>"
                f"Market Share: {share:.0%}<br>"
                f"Growth Rate: {growth:.1%}<br>"
                f"Quadrant: {quad.title()}<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="BCG Matrix", x=0.5, xanchor="center"),
        xaxis=dict(
            title="Relative Market Share",
            range=[0, 1],
            tickformat=".0%",
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
        ),
        yaxis=dict(
            title="Market Growth Rate",
            range=[0, max(p.get("market_growth", 0.05) for p in positions) * 1.5 + 0.02]
                  if positions else [0, 0.3],
            tickformat=".0%",
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
        ),
        showlegend=True,
        legend=dict(x=1.02, y=0.5, font=dict(size=10)),
        height=H,
        width=W,
    )
    _save(fig, out)


# ── 4. STEEP Scenario Comparison ──────────────────────────────────────────────

def _scenario_comparison(data: dict, out: str) -> None:
    scenarios = data["risk"].get("steep_scenarios", [])
    dimensions = ["social", "technological", "economic", "environmental", "political"]

    scenario_colors = [NAVY, GOLD, "#C15B1E", "#1A7A4A", "#B22222"]

    fig = go.Figure()

    for idx, s in enumerate(scenarios):
        name  = s.get("name", f"Scenario {idx+1}").capitalize()
        prob  = s.get("probability", 0)
        # Heuristic score per dimension: count words as a proxy for severity
        dim_scores = []
        for dim in dimensions:
            text = s.get(dim, "")
            # Score = capped word count / 10 to get 0-1 range for viz
            raw = min(len(text.split()), 50) / 50 * 10
            dim_scores.append(round(raw, 1))

        color = scenario_colors[idx % len(scenario_colors)]
        fig.add_trace(go.Bar(
            name=f"{name} (p={prob:.0%})",
            x=[d.capitalize() for d in dimensions],
            y=dim_scores,
            marker=dict(color=color, opacity=0.85,
                        line=dict(color=WHITE, width=1)),
            text=[f"{v:.1f}" for v in dim_scores],
            textposition="outside",
            textfont=dict(size=9),
            cliponaxis=False,
        ))

    # Probability annotations on a secondary axis
    prob_trace_x = [s.get("name", "").capitalize() for s in scenarios]
    prob_trace_y = [s.get("probability", 0) * 10 for s in scenarios]  # scale to 0-10

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="STEEP Scenario Comparison", x=0.5, xanchor="center"),
        barmode="group",
        xaxis=dict(
            title="STEEP Dimension",
            showgrid=False,
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            title="Relative Severity Score",
            range=[0, 13],
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
        ),
        legend=dict(
            x=1.02, y=0.98,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=MGRAY, borderwidth=1,
        ),
        height=H,
        width=W,
    )
    _save(fig, out)


# ── 5. Strategic Options Ranking ──────────────────────────────────────────────

def _strategic_options_bar(data: dict, out: str) -> None:
    options = sorted(
        data["synthesis"].get("strategic_options", []),
        key=lambda x: x.get("overall_score", 0),
        reverse=True,
    )

    labels      = [o.get("option", "") for o in options]
    overall     = [o.get("overall_score", 0) for o in options]
    fit_scores  = [o.get("strategic_fit_score", 0) for o in options]
    risk_scores = [o.get("risk_score", 0) for o in options]
    feas_scores = [o.get("feasibility_score", 0) for o in options]

    def _feas_color(score):
        if score >= 70:
            return "#1A7A4A"
        if score >= 50:
            return GOLD
        return "#B22222"

    bar_colors = [_feas_color(f) for f in feas_scores]

    fig = go.Figure()

    # Overall score bars
    fig.add_trace(go.Bar(
        x=overall,
        y=labels,
        orientation="h",
        name="Overall Score",
        marker=dict(color=bar_colors, line=dict(color=NAVY, width=0.8)),
        text=[f"{v}" for v in overall],
        textposition="outside",
        textfont=dict(size=12, color=NAVY),
        cliponaxis=False,
    ))

    # Overlay: Strategic Fit (navy outline)
    fig.add_trace(go.Bar(
        x=fit_scores,
        y=labels,
        orientation="h",
        name="Strategic Fit",
        marker=dict(color="rgba(27,42,74,0.25)", line=dict(color=NAVY, width=1.5)),
        opacity=0.6,
        textposition="none",
    ))

    # Risk line markers
    fig.add_trace(go.Scatter(
        x=risk_scores,
        y=labels,
        mode="markers",
        name="Risk Score",
        marker=dict(symbol="diamond", size=10,
                    color="#B22222", line=dict(color=WHITE, width=1.5)),
    ))

    # Feasibility colour legend annotation
    for color, label in [("#1A7A4A","High Feasibility"), (GOLD,"Medium Feasibility"), ("#B22222","Low Feasibility")]:
        fig.add_trace(go.Bar(
            x=[None], y=[None],
            name=label,
            marker=dict(color=color),
        ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Strategic Options Ranking", x=0.5, xanchor="center"),
        barmode="overlay",
        xaxis=dict(
            title="Score (0–100)",
            range=[0, 115],
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            tickfont=dict(size=12),
        ),
        legend=dict(
            x=1.02, y=0.98,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=MGRAY, borderwidth=1,
        ),
        height=H,
        width=W,
    )
    _save(fig, out)


# ── 6. DCF Waterfall (Year 3) ─────────────────────────────────────────────────

def _dcf_waterfall(data: dict, out: str) -> None:
    dcf = data["finance"]["dcf"]
    cf  = dcf["cash_flows"][2]          # Year 3 (index 2)

    revenue = float(cf["revenue"])
    cogs    = float(cf["cogs"])
    opex    = float(cf["opex"])
    ebitda  = revenue - cogs - opex

    GREEN = "#1A7A4A"
    RED   = "#B22222"

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Revenue", "COGS", "OPEX", "EBITDA"],
        y=[revenue, -cogs, -opex, 0],
        text=[
            f"${revenue / 1e6:.1f}M",
            f"−${cogs / 1e6:.1f}M",
            f"−${opex / 1e6:.1f}M",
            f"${ebitda / 1e6:.1f}M",
        ],
        textposition="outside",
        textfont=dict(size=13, color=NAVY),
        increasing=dict(marker=dict(color=GREEN, line=dict(color=GREEN, width=1))),
        decreasing=dict(marker=dict(color=RED,   line=dict(color=RED,   width=1))),
        totals=dict(   marker=dict(color=NAVY,   line=dict(color=NAVY,  width=1))),
        connector=dict(line=dict(color=MGRAY, width=1, dash="dot")),
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(
            text=f"DCF Waterfall — Year 3  (WACC {dcf['wacc']:.1f}%)",
            x=0.5, xanchor="center",
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title="USD",
            showgrid=True, gridcolor=MGRAY,
            zeroline=True, zerolinecolor=NAVY, zerolinewidth=1.5,
            tickformat="$.2s",
        ),
        showlegend=False,
        height=H,
        width=W,
    )
    _save(fig, out)


# ── 7. Cumulative FCF ─────────────────────────────────────────────────────────

def _fcf_cumulative(data: dict, out: str) -> None:
    dcf     = data["finance"]["dcf"]
    ev      = float(dcf["enterprise_value"])
    npv     = float(dcf["npv"])
    payback = float(dcf["payback_period_years"])

    # Year 0: net investment = portion of EV not recovered by discounted FCFs
    years    = [0]
    cum_fcfs = [-(ev - npv)]

    running = cum_fcfs[0]
    for cf in dcf["cash_flows"]:
        fcf = (float(cf["revenue"]) - float(cf["cogs"])
               - float(cf["opex"])  - float(cf["capex"]))
        running += fcf
        years.append(cf["year"])
        cum_fcfs.append(running)

    fig = go.Figure()

    # Red shading below zero
    y_min = min(cum_fcfs) * 1.15
    fig.add_hrect(
        y0=y_min, y1=0,
        fillcolor="rgba(178,34,34,0.06)",
        line_width=0,
        layer="below",
    )

    # Main cumulative FCF line
    fig.add_trace(go.Scatter(
        x=years,
        y=cum_fcfs,
        mode="lines+markers",
        line=dict(color=NAVY, width=2.5),
        marker=dict(size=8, color=NAVY, line=dict(color=WHITE, width=1.5)),
        name="Cumulative FCF",
        hovertemplate="Year %{x}<br>Cumulative FCF: $%{y:,.0f}<extra></extra>",
    ))

    # Gold dashed break-even line
    fig.add_hline(
        y=0,
        line=dict(color=GOLD, width=1.5, dash="dash"),
        annotation_text="Break-even",
        annotation_position="top right",
        annotation_font=dict(size=10, color=GOLD),
    )

    # Gold star at payback point (payback_period_years, 0)
    fig.add_trace(go.Scatter(
        x=[payback],
        y=[0],
        mode="markers+text",
        marker=dict(size=15, color=GOLD, symbol="star",
                    line=dict(color=NAVY, width=1.5)),
        text=[f"  Payback ({payback:.1f} yrs)"],
        textposition="middle right",
        textfont=dict(size=11, color=GOLD),
        name="Payback Point",
        hovertemplate=f"Payback: {payback:.1f} years<extra></extra>",
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Cumulative Free Cash Flow", x=0.5, xanchor="center"),
        xaxis=dict(
            title="Year",
            tickvals=years,
            tickfont=dict(size=12),
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
        ),
        yaxis=dict(
            title="USD",
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
            tickformat="$.2s",
        ),
        legend=dict(
            x=1.02, y=0.98,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=MGRAY, borderwidth=1,
        ),
        height=H,
        width=W,
    )
    _save(fig, out)


# ── 8. Valuation Comps (EV/EBITDA) ───────────────────────────────────────────

def _valuation_comps(data: dict, out: str) -> None:
    val   = data["finance"]["valuation"]
    comps = val.get("comparable_companies", [])
    if not comps:
        return

    subject_name     = data.get("company", "Subject")
    subject_multiple = float(val.get("subject_ev_ebitda", 0))

    comp_names     = [c["company"]        for c in comps]
    comp_multiples = [float(c["ev_ebitda"]) for c in comps]

    # Median of comparable companies (no statistics import needed)
    sorted_m    = sorted(comp_multiples)
    n           = len(sorted_m)
    median_comp = (sorted_m[n // 2] + sorted_m[(n - 1) // 2]) / 2

    all_names     = comp_names + [subject_name]
    all_multiples = comp_multiples + [subject_multiple]
    bar_colors    = [NAVY] * len(comps) + [GOLD]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=all_names,
        y=all_multiples,
        marker=dict(
            color=bar_colors,
            line=dict(color=NAVY, width=0.8),
        ),
        text=[f"{v:.1f}x" for v in all_multiples],
        textposition="outside",
        textfont=dict(size=11, color=NAVY),
        cliponaxis=False,
        name="EV/EBITDA",
        hovertemplate="%{x}<br>EV/EBITDA: %{y:.1f}x<extra></extra>",
    ))

    # Median comp dashed line
    fig.add_hline(
        y=median_comp,
        line=dict(color=GOLD, width=1.5, dash="dash"),
    )
    fig.add_annotation(
        x=len(all_names) - 1,
        y=median_comp,
        text=f"  Median comp: {median_comp:.1f}x",
        showarrow=False,
        font=dict(size=10, color=GOLD),
        xanchor="left",
        yanchor="bottom",
    )

    # Legend proxies for bar colours
    for color, label in [(NAVY, "Comparable Companies"), (GOLD, "Subject Company")]:
        fig.add_trace(go.Bar(x=[None], y=[None], name=label,
                             marker=dict(color=color)))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(
            text=f"EV/EBITDA Valuation Comps — Method: {val.get('valuation_method_used', '')}",
            x=0.5, xanchor="center",
        ),
        xaxis=dict(
            title="",
            tickfont=dict(size=11),
            showgrid=False,
        ),
        yaxis=dict(
            title="EV / EBITDA Multiple (x)",
            showgrid=True, gridcolor=MGRAY,
            zeroline=False,
            ticksuffix="x",
        ),
        barmode="group",
        legend=dict(
            x=1.02, y=0.98,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=MGRAY, borderwidth=1,
        ),
        height=H,
        width=W,
    )
    _save(fig, out)


# ── Entry point ───────────────────────────────────────────────────────────────

def generate_all_charts(json_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    charts_dir = os.path.join(os.path.dirname(json_path), "charts")
    os.makedirs(charts_dir, exist_ok=True)

    def p(name):
        return os.path.join(charts_dir, name)

    print("Generating charts...")
    _porter_bar(data,            p("porter_forces_bar.png"))
    _radar(data,                 p("agent_scores_radar.png"))
    _bcg(data,                   p("bcg_matrix.png"))
    _scenario_comparison(data,   p("scenario_comparison.png"))
    _strategic_options_bar(data, p("strategic_options_bar.png"))

    try:
        _dcf_waterfall(data,  p("dcf_waterfall.png"))
    except Exception as exc:
        print(f"  dcf_waterfall skipped — {exc}")
    try:
        _fcf_cumulative(data, p("fcf_cumulative.png"))
    except Exception as exc:
        print(f"  fcf_cumulative skipped — {exc}")
    try:
        _valuation_comps(data, p("valuation_comps.png"))
    except Exception as exc:
        print(f"  valuation_comps skipped — {exc}")

    print(f"Done — {charts_dir}")


# ── CLI entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    base = os.path.dirname(os.path.abspath(__file__))
    json_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, "output.json")
    generate_all_charts(json_path)
