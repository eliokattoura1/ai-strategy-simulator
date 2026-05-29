"""
finance_dashboard.py  —  drop into reports/charts_generator.py or call standalone
Generates a 5-panel Plotly HTML dashboard from FinanceAgentOutput.
"""
import plotly.graph_objects as go
import plotly.subplots as sp
from schemas.finance_schema import FinanceAgentOutput


def build_finance_dashboard(output: FinanceAgentOutput) -> go.Figure:
    fig = sp.make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "DCF — Cumulative FCF vs Investment",
            "Cap Table — Pre vs Post Funding Round",
            "Burn Rate & Runway",
            "P&L — 3-Year Trend",
            "Valuation — EV/EBITDA Comps",
            "",
        ),
        specs=[
            [{"type": "scatter"}, {"type": "pie"}],
            [{"type": "bar"},     {"type": "scatter"}],
            [{"type": "bar"},     {"type": "table"}],
        ],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    BLUE   = "#4F46E5"
    GREEN  = "#10B981"
    AMBER  = "#F59E0B"
    RED    = "#EF4444"
    GRAY   = "#6B7280"

    # ── Panel 1: DCF cumulative FCF waterfall ─────────────────────────────────
    invest = output.dcf.cash_flows[0].revenue * 0  # placeholder
    # Rebuild from initial investment implied by NPV
    initial = output.dcf.enterprise_value - output.dcf.npv
    cumulative, running = [-initial / 1e6], -initial / 1e6
    years = [0]
    for cf in output.dcf.cash_flows:
        running += cf.fcf / 1e6
        cumulative.append(running)
        years.append(cf.year)

    fig.add_trace(go.Scatter(
        x=years, y=cumulative,
        mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=8, color=[RED if v < 0 else GREEN for v in cumulative]),
        name="Cumulative FCF",
        hovertemplate="Year %{x}: $%{y:.2f}M<extra></extra>",
    ), row=1, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color=GRAY, opacity=0.5, row=1, col=1)
    fig.add_annotation(
        x=output.dcf.payback_period_years, y=0,
        text=f"Payback {output.dcf.payback_period_years:.1f}yr",
        showarrow=True, arrowhead=2, arrowcolor=AMBER,
        font=dict(size=10, color=AMBER), row=1, col=1,
    )

    # ── Panel 2: Cap Table donut pre vs post ──────────────────────────────────
    labels = [s.name for s in output.cap_table.shareholders] + ["New Investors"]
    post_pcts = [s.ownership_post_pct for s in output.cap_table.shareholders]
    post_pcts.append(output.cap_table.funding_round.investor_ownership_pct)

    fig.add_trace(go.Pie(
        labels=labels,
        values=post_pcts,
        hole=0.45,
        textinfo="label+percent",
        textfont=dict(size=10),
        marker=dict(colors=[BLUE, GREEN, AMBER, RED, GRAY]),
        name="Post-Round Ownership",
    ), row=1, col=2)

    # ── Panel 3: Burn rate bar — burn vs revenue ──────────────────────────────
    months = list(range(1, 13))
    # Simulate monthly burn declining as revenue grows
    burns   = [output.burn.monthly_burn / 1e3] * 12
    revenue = [output.burn.monthly_revenue * (1.05 ** m) / 1e3 for m in range(12)]

    fig.add_trace(go.Bar(x=months, y=burns,   name="Monthly Burn ($K)",    marker_color=RED,   opacity=0.7), row=2, col=1)
    fig.add_trace(go.Bar(x=months, y=revenue, name="Monthly Revenue ($K)", marker_color=GREEN, opacity=0.7), row=2, col=1)
    fig.add_annotation(
        x=6, y=max(burns),
        text=f"Runway: {output.burn.runway_months:.0f} mo | LTV/CAC: {output.burn.unit_economics.ltv_cac_ratio:.1f}x",
        showarrow=False, font=dict(size=10, color=BLUE), row=2, col=1,
    )

    # ── Panel 4: P&L 3-year trend ─────────────────────────────────────────────
    yrs      = [p.year for p in output.statements.pnl]
    revenues = [p.revenue / 1e6 for p in output.statements.pnl]
    ebitdas  = [p.ebitda / 1e6 for p in output.statements.pnl]
    nets     = [p.net_income / 1e6 for p in output.statements.pnl]

    fig.add_trace(go.Scatter(x=yrs, y=revenues, mode="lines+markers", name="Revenue",    line=dict(color=BLUE,  width=2)), row=2, col=2)
    fig.add_trace(go.Scatter(x=yrs, y=ebitdas,  mode="lines+markers", name="EBITDA",     line=dict(color=GREEN, width=2)), row=2, col=2)
    fig.add_trace(go.Scatter(x=yrs, y=nets,     mode="lines+markers", name="Net Income", line=dict(color=AMBER, width=2, dash="dot")), row=2, col=2)

    # ── Panel 5: Valuation comps bar ──────────────────────────────────────────
    comp_names = [c.company for c in output.valuation.comparable_companies] + ["Subject Co."]
    ev_ebitdas = [c.ev_ebitda for c in output.valuation.comparable_companies] + [output.valuation.subject_ev_ebitda]
    bar_colors = [GRAY] * len(output.valuation.comparable_companies) + [BLUE]

    fig.add_trace(go.Bar(
        x=comp_names, y=ev_ebitdas,
        marker_color=bar_colors,
        name="EV/EBITDA",
        hovertemplate="%{x}: %{y:.1f}x<extra></extra>",
    ), row=3, col=1)

    # Implied valuation range annotation
    fig.add_annotation(
        x=comp_names[-1], y=output.valuation.subject_ev_ebitda,
        text=(
            f"Implied EV<br>"
            f"Low: ${output.valuation.implied_valuation_low/1e6:.1f}M<br>"
            f"Mid: ${output.valuation.implied_valuation_mid/1e6:.1f}M<br>"
            f"High: ${output.valuation.implied_valuation_high/1e6:.1f}M"
        ),
        showarrow=True, arrowhead=2,
        font=dict(size=9), bgcolor="white", bordercolor=BLUE,
        row=3, col=1,
    )

    # ── Panel 6: KPI scorecard table ──────────────────────────────────────────
    ue = output.burn.unit_economics
    metrics = ["NPV", "IRR", "Payback", "LTV/CAC", "Gross Margin", "Runway", "Fit Score", "Signal"]
    values  = [
        f"${output.dcf.npv/1e6:.2f}M",
        f"{output.dcf.irr:.1f}%",
        f"{output.dcf.payback_period_years:.1f} yr",
        f"{ue.ltv_cac_ratio:.1f}x",
        f"{ue.gross_margin_pct:.1f}%",
        f"{output.burn.runway_months:.0f} mo",
        f"{output.financial_fit_score}/100",
        output.go_signal,
    ]
    signal_colors = {
        "Go": "#D1FAE5",
        "Conditional Go": "#FEF3C7",
        "No Go": "#FEE2E2",
    }
    cell_colors = ["#F9FAFB"] * 7 + [signal_colors.get(output.go_signal, "#F9FAFB")]

    fig.add_trace(go.Table(
        header=dict(
            values=["Metric", "Value"],
            fill_color=BLUE,
            font=dict(color="white", size=11),
            align="left",
        ),
        cells=dict(
            values=[metrics, values],
            fill_color=[["#F9FAFB"] * len(metrics), cell_colors],
            align="left",
            font=dict(size=11),
        ),
    ), row=3, col=2)

    fig.update_layout(
        title=dict(
            text=f"Financial Viability Dashboard  ·  {output.go_signal}  ·  Fit Score {output.financial_fit_score}/100",
            font=dict(size=15),
        ),
        height=950,
        template="plotly_white",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.05, x=0),
        showlegend=True,
    )

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative FCF ($M)", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_yaxes(title_text="USD (thousands)", row=2, col=1)
    fig.update_xaxes(title_text="Year", row=2, col=2)
    fig.update_yaxes(title_text="USD ($M)", row=2, col=2)
    fig.update_yaxes(title_text="EV/EBITDA (x)", row=3, col=1)

    return fig


def save_finance_dashboard(output: FinanceAgentOutput, path: str = "reports/finance_dashboard.html") -> str:
    fig = build_finance_dashboard(output)
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"[FinanceDashboard] Saved → {path}")
    return path
