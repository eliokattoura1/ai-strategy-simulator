"""
AI Strategy Simulator — Boardroom PDF Report Generator
Entry point: generate_report(json_path, output_path)
"""

import json
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether, HRFlowable,
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY  = colors.HexColor("#1B2A4A")
GOLD  = colors.HexColor("#C9A84C")
WHITE = colors.white
LGRAY = colors.HexColor("#F4F5F7")
MGRAY = colors.HexColor("#D0D3DA")
DGRAY = colors.HexColor("#6B7280")

ROW_ALT = colors.HexColor("#EEF0F5")

# VRIO colours
SCA_COLOR = colors.HexColor("#1A7A4A")   # green
TCA_COLOR = colors.HexColor("#B8860B")   # dark gold / yellow
CP_COLOR  = colors.HexColor("#C15B1E")   # orange
CD_COLOR  = colors.HexColor("#B22222")   # red

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

# ── Styles ────────────────────────────────────────────────────────────────────

def build_styles():
    base = getSampleStyleSheet()
    s = {}

    def ps(name, **kw):
        s[name] = ParagraphStyle(name, **kw)

    ps("cover_company",  fontName="Helvetica-Bold", fontSize=28,
       textColor=WHITE, alignment=TA_CENTER, spaceAfter=6)
    ps("cover_industry", fontName="Helvetica", fontSize=14,
       textColor=GOLD, alignment=TA_CENTER, spaceAfter=4)
    ps("cover_question", fontName="Helvetica", fontSize=11,
       textColor=LGRAY, alignment=TA_CENTER, spaceAfter=4, leading=16)
    ps("cover_date",     fontName="Helvetica", fontSize=10,
       textColor=MGRAY, alignment=TA_CENTER)
    ps("cover_conf",     fontName="Helvetica-Bold", fontSize=9,
       textColor=GOLD, alignment=TA_CENTER, spaceAfter=0)

    ps("section_header", fontName="Helvetica-Bold", fontSize=13,
       textColor=GOLD, alignment=TA_LEFT, spaceAfter=6, spaceBefore=4)
    ps("subsection",     fontName="Helvetica-Bold", fontSize=10,
       textColor=NAVY, alignment=TA_LEFT, spaceAfter=4, spaceBefore=6)
    ps("body",           fontName="Helvetica", fontSize=9,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_JUSTIFY,
       leading=13, spaceAfter=4)
    ps("body_center",    fontName="Helvetica", fontSize=9,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_CENTER, leading=13)
    ps("body_bold",      fontName="Helvetica-Bold", fontSize=9,
       textColor=NAVY, alignment=TA_LEFT, leading=13)
    ps("small",          fontName="Helvetica", fontSize=7.5,
       textColor=DGRAY, alignment=TA_LEFT, leading=10)
    ps("small_center",   fontName="Helvetica", fontSize=7.5,
       textColor=DGRAY, alignment=TA_CENTER, leading=10)
    ps("table_header",   fontName="Helvetica-Bold", fontSize=8.5,
       textColor=WHITE, alignment=TA_CENTER, leading=11)
    ps("table_cell",     fontName="Helvetica", fontSize=8,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_LEFT, leading=11)
    ps("table_cell_c",   fontName="Helvetica", fontSize=8,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_CENTER, leading=11)
    ps("score_label",    fontName="Helvetica-Bold", fontSize=22,
       textColor=WHITE, alignment=TA_CENTER)
    ps("score_sub",      fontName="Helvetica", fontSize=9,
       textColor=GOLD, alignment=TA_CENTER)
    ps("narrative",      fontName="Helvetica", fontSize=9.5,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_JUSTIFY,
       leading=15, spaceAfter=6)
    ps("toc_entry",      fontName="Helvetica", fontSize=9,
       textColor=NAVY, alignment=TA_LEFT, leading=13)
    ps("page_num",       fontName="Helvetica", fontSize=8,
       textColor=DGRAY, alignment=TA_CENTER)
    return s


# ── Custom Flowables ──────────────────────────────────────────────────────────

class SectionHeader(Flowable):
    """Navy banner with gold text for section titles."""
    def __init__(self, text, width=None):
        super().__init__()
        self.text = text
        self._width = width or (PAGE_W - 2 * MARGIN)
        self.height = 22

    def draw(self):
        self.canv.setFillColor(NAVY)
        self.canv.rect(0, 0, self._width, self.height, fill=1, stroke=0)
        self.canv.setFillColor(GOLD)
        self.canv.setFont("Helvetica-Bold", 11)
        self.canv.drawString(8, 6, self.text.upper())

    def wrap(self, availW, availH):
        self._width = availW
        return availW, self.height


class ScoreBadge(Flowable):
    """Circular badge showing a numeric score."""
    def __init__(self, score, label="Strategic Fit Score", size=90):
        super().__init__()
        self.score = score
        self.label = label
        self.size = size
        self.width = size
        self.height = size + 16

    def draw(self):
        r = self.size / 2
        cx, cy = r, r + 8
        # Shadow
        self.canv.setFillColor(colors.HexColor("#C0C4CC"))
        self.canv.circle(cx + 2, cy - 2, r, fill=1, stroke=0)
        # Main circle
        self.canv.setFillColor(NAVY)
        self.canv.circle(cx, cy, r, fill=1, stroke=0)
        # Gold ring
        self.canv.setStrokeColor(GOLD)
        self.canv.setLineWidth(3)
        self.canv.circle(cx, cy, r - 3, fill=0, stroke=1)
        # Score text
        self.canv.setFillColor(WHITE)
        self.canv.setFont("Helvetica-Bold", 24)
        txt = str(int(self.score))
        self.canv.drawCentredString(cx, cy - 8, txt)
        # Sub-label
        self.canv.setFillColor(GOLD)
        self.canv.setFont("Helvetica", 6.5)
        self.canv.drawCentredString(cx, cy - 20, self.label)

    def wrap(self, availW, availH):
        return self.width, self.height


class BarChart(Flowable):
    """Horizontal bar chart using pure ReportLab shapes."""
    def __init__(self, data, title="", width=380, height=None, max_val=10.0):
        super().__init__()
        self.data = data          # list of (label, value)
        self.title = title
        self._w = width
        self.max_val = max_val
        bar_h = 18
        gap = 6
        self._h = height or (len(data) * (bar_h + gap) + 40)
        self.bar_h = bar_h
        self.gap = gap

    def wrap(self, availW, availH):
        self._w = availW
        return availW, self._h

    def draw(self):
        c = self.canv
        label_w = 140
        bar_area = self._w - label_w - 30
        y = self._h - 30

        if self.title:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(NAVY)
            c.drawString(0, self._h - 12, self.title)

        for label, val in self.data:
            pct = min(float(val) / self.max_val, 1.0)
            bw = pct * bar_area

            # Label
            c.setFont("Helvetica", 8)
            c.setFillColor(NAVY)
            # truncate label
            lbl = label if len(label) <= 22 else label[:21] + "…"
            c.drawRightString(label_w - 4, y + 4, lbl)

            # Background track
            c.setFillColor(LGRAY)
            c.rect(label_w, y, bar_area, self.bar_h, fill=1, stroke=0)

            # Bar
            c.setFillColor(NAVY)
            if bw > 0:
                c.rect(label_w, y, bw, self.bar_h, fill=1, stroke=0)
            # Gold accent end-cap
            if bw >= 4:
                c.setFillColor(GOLD)
                c.rect(label_w + bw - 4, y, 4, self.bar_h, fill=1, stroke=0)

            # Value label
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(NAVY)
            c.drawString(label_w + bw + 5, y + 4, str(val))

            y -= (self.bar_h + self.gap)


class AnsoffMatrix(Flowable):
    """2×2 Ansoff matrix visual."""
    def __init__(self, options, width=380, height=200):
        super().__init__()
        self.options = options
        self._w = width
        self._h = height

    def wrap(self, availW, availH):
        self._w = min(availW, self._w)
        return self._w, self._h

    def _quadrant_data(self):
        mapping = {
            "market penetration": (0, 0),
            "market development": (1, 0),
            "product development": (0, 1),
            "diversification": (1, 1),
        }
        grid = {(c, r): ("", "") for c in range(2) for r in range(2)}
        for o in self.options:
            key = o.get("quadrant", "").lower()
            pos = mapping.get(key)
            if pos:
                grid[pos] = (o.get("initiative", ""), o.get("risk_level", ""))
        return grid

    def draw(self):
        c = self.canv
        w, h = self._w, self._h
        cw = (w - 60) / 2
        ch = (h - 40) / 2
        ox, oy = 60, 20

        titles = {(0,0):"Market Penetration", (1,0):"Market Development",
                  (0,1):"Product Development", (1,1):"Diversification"}
        risk_colors = {"low": colors.HexColor("#1A7A4A"),
                       "medium": colors.HexColor("#B8860B"),
                       "high": colors.HexColor("#B22222")}
        bg_colors = {(0,0): colors.HexColor("#E8F4EC"),
                     (1,0): colors.HexColor("#FFF8E8"),
                     (0,1): colors.HexColor("#FFF0E8"),
                     (1,1): colors.HexColor("#F8E8E8")}

        grid = self._quadrant_data()

        # Axis labels
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(NAVY)
        c.drawCentredString(ox + cw/2, h - 12, "Existing Products")
        c.drawCentredString(ox + cw + cw/2, h - 12, "New Products")
        # Y axis labels (rotated)
        c.saveState()
        c.translate(12, oy + ch/2)
        c.rotate(90)
        c.drawCentredString(0, 0, "Existing Markets")
        c.restoreState()
        c.saveState()
        c.translate(12, oy + ch + ch/2)
        c.rotate(90)
        c.drawCentredString(0, 0, "New Markets")
        c.restoreState()

        for col in range(2):
            for row in range(2):
                x = ox + col * cw
                y = oy + row * ch
                # Background
                c.setFillColor(bg_colors[(col, row)])
                c.rect(x, y, cw, ch, fill=1, stroke=0)
                # Border
                c.setStrokeColor(NAVY)
                c.setLineWidth(0.5)
                c.rect(x, y, cw, ch, fill=0, stroke=1)
                # Title
                c.setFont("Helvetica-Bold", 7.5)
                c.setFillColor(NAVY)
                c.drawCentredString(x + cw/2, y + ch - 12, titles[(col, row)])
                # Initiative text
                init, risk = grid[(col, row)]
                if init:
                    c.setFont("Helvetica", 6.5)
                    c.setFillColor(colors.HexColor("#333333"))
                    words = init.split()
                    lines, line = [], []
                    for w in words:
                        line.append(w)
                        if len(" ".join(line)) > 22:
                            lines.append(" ".join(line[:-1]))
                            line = [w]
                    if line:
                        lines.append(" ".join(line))
                    ty = y + ch - 26
                    for ln in lines[:3]:
                        c.drawCentredString(x + cw/2, ty, ln)
                        ty -= 9
                    if risk:
                        c.setFont("Helvetica-Bold", 6.5)
                        c.setFillColor(risk_colors.get(risk, DGRAY))
                        c.drawCentredString(x + cw/2, y + 6, f"Risk: {risk.upper()}")


class StrategyClockFlowable(Flowable):
    """Simple Strategy Clock circle diagram."""
    def __init__(self, positions, width=200, height=200):
        super().__init__()
        self.positions = positions
        self._w = width
        self._h = height

    def wrap(self, availW, availH):
        return self._w, self._h

    def draw(self):
        import math
        c = self.canv
        cx, cy = self._w / 2, self._h / 2
        r = min(cx, cy) - 20

        # Outer circle
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.5)
        c.setFillColor(LGRAY)
        c.circle(cx, cy, r, fill=1, stroke=1)

        # 8 position labels around clock
        clock_labels = {
            1: "No Frills", 2: "Low Price", 3: "Hybrid",
            4: "Differentiation", 5: "Focused Diff.",
            6: "Risky High", 7: "Monopoly", 8: "Loss of Share"
        }
        for pos_num, label in clock_labels.items():
            angle = math.radians(90 - (pos_num - 1) * 45)
            lx = cx + (r + 12) * math.cos(angle)
            ly = cy + (r + 12) * math.sin(angle)
            c.setFont("Helvetica", 5.5)
            c.setFillColor(DGRAY)
            c.drawCentredString(lx, ly - 3, f"{pos_num}. {label}")

        # Highlight active positions
        for p in self.positions:
            pos_num = p.get("position", 4)
            angle = math.radians(90 - (pos_num - 1) * 45)
            px = cx + (r * 0.7) * math.cos(angle)
            py = cy + (r * 0.7) * math.sin(angle)
            c.setFillColor(GOLD)
            c.circle(px, py, 7, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(NAVY)
            c.drawCentredString(px, py - 3, str(pos_num))

        # Center label
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(NAVY)
        c.drawCentredString(cx, cy - 3, "Strategy\nClock")


# ── Page decorators ───────────────────────────────────────────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()
    pw, ph = A4

    # Top line
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, ph - 1.4 * cm, pw - MARGIN, ph - 1.4 * cm)

    # Logo placeholder (top-right)
    logo_w, logo_h = 2.8 * cm, 0.9 * cm
    lx = pw - MARGIN - logo_w
    ly = ph - MARGIN * 0.55 - logo_h
    canvas.setFillColor(LGRAY)
    canvas.setStrokeColor(MGRAY)
    canvas.setLineWidth(0.5)
    canvas.rect(lx, ly, logo_w, logo_h, fill=1, stroke=1)
    canvas.setFont("Helvetica", 6)
    canvas.setFillColor(DGRAY)
    canvas.drawCentredString(lx + logo_w / 2, ly + logo_h / 2 - 2, "COMPANY LOGO")

    # Bottom line + page number
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN, 1.5 * cm, pw - MARGIN, 1.5 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(DGRAY)
    canvas.drawCentredString(pw / 2, 0.8 * cm, f"— {doc.page} —")

    # Confidential footer text
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MGRAY)
    canvas.drawString(MARGIN, 0.8 * cm, "CONFIDENTIAL")
    canvas.drawRightString(pw - MARGIN, 0.8 * cm, "AI Strategy Simulator")

    canvas.restoreState()


def _cover_page(canvas, doc):
    """Full-bleed navy cover — no header/footer chrome."""
    canvas.saveState()
    pw, ph = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)

    # Gold accent bar
    canvas.setFillColor(GOLD)
    canvas.rect(0, ph * 0.42, pw, 3, fill=1, stroke=0)
    canvas.rect(0, ph * 0.42 - 6, pw, 1.5, fill=1, stroke=0)

    # Watermark
    canvas.saveState()
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.04))
    canvas.setFont("Helvetica-Bold", 72)
    canvas.translate(pw / 2, ph / 2)
    canvas.rotate(35)
    canvas.drawCentredString(0, 0, "CONFIDENTIAL")
    canvas.restoreState()

    # Logo placeholder
    lx = pw - 3.5 * cm - MARGIN
    ly = ph - 2.0 * cm
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.1))
    canvas.rect(lx, ly, 3.5 * cm, 1.1 * cm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.5))
    canvas.drawCentredString(lx + 1.75 * cm, ly + 0.4 * cm, "COMPANY LOGO")

    canvas.restoreState()


# ── Table helpers ─────────────────────────────────────────────────────────────

def std_table_style(header_rows=1, col_widths=None):
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, header_rows - 1), NAVY),
        ("TEXTCOLOR",   (0, 0), (-1, header_rows - 1), WHITE),
        ("FONTNAME",    (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, header_rows - 1), 8.5),
        ("ALIGN",       (0, 0), (-1, header_rows - 1), "CENTER"),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [WHITE, ROW_ALT]),
        ("FONTNAME",    (0, header_rows), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, header_rows), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID",        (0, 0), (-1, -1), 0.4, MGRAY),
        ("LINEBELOW",   (0, header_rows - 1), (-1, header_rows - 1), 1.2, GOLD),
    ])


def P(text, style_name, styles):
    return Paragraph(str(text), styles[style_name])


# ── Section builders ──────────────────────────────────────────────────────────

def build_cover(data, styles):
    story = []
    company = data.get("company", "Company Name")
    industry = data.get("industry", "")
    question = data.get("strategic_question", "")
    date_str = datetime.now().strftime("%B %Y")

    # Vertical spacers to push content to vertical center of navy page
    story.append(Spacer(1, 7.5 * cm))
    story.append(Paragraph("AI STRATEGY SIMULATOR", ParagraphStyle(
        "cov_tag", fontName="Helvetica", fontSize=10,
        textColor=GOLD, alignment=TA_CENTER, spaceAfter=8,
        letterSpacing=4
    )))
    story.append(Paragraph("STRATEGIC INTELLIGENCE REPORT", ParagraphStyle(
        "cov_sub", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.Color(1, 1, 1, 0.5), alignment=TA_CENTER, spaceAfter=20
    )))
    story.append(Paragraph(company.upper(), styles["cover_company"]))
    story.append(Paragraph(industry, styles["cover_industry"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f'"{question}"', styles["cover_question"]))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(date_str, styles["cover_date"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("CONFIDENTIAL", styles["cover_conf"]))
    story.append(PageBreak())
    return story


def build_executive_summary(data, styles):
    syn = data.get("synthesis", {})
    summary = syn.get("executive_summary", "")
    score = syn.get("overall_strategic_fit_score", 0)

    story = [SectionHeader("Executive Summary"), Spacer(1, 0.3 * cm)]

    # Score badge + summary side-by-side via a table
    badge = ScoreBadge(score, "Overall Strategic Fit", size=100)
    summary_para = Paragraph(summary, styles["narrative"])

    layout = Table(
        [[badge, summary_para]],
        colWidths=[3.5 * cm, PAGE_W - 2 * MARGIN - 3.5 * cm - 0.5 * cm],
        hAlign="LEFT"
    )
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(layout)

    # Conflicts & resolutions
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Key Strategic Tensions & Resolutions", styles["subsection"]))
    conflicts = syn.get("inter_agent_conflicts", [])
    resolutions = syn.get("conflict_resolutions", [])
    rows = [["Tension", "Resolution"]]
    for c, r in zip(conflicts, resolutions):
        rows.append([Paragraph(c, styles["table_cell"]),
                     Paragraph(r, styles["table_cell"])])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[aw * 0.45, aw * 0.55])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(PageBreak())
    return story


def build_external(data, styles):
    ext = data.get("external", {})
    story = [SectionHeader("External Environment Analysis"), Spacer(1, 0.3 * cm)]

    # PESTEL table
    story.append(Paragraph("PESTEL Analysis", styles["subsection"]))
    pestel = ext.get("pestel", [])
    impact_colors = {"high": colors.HexColor("#B22222"),
                     "medium": colors.HexColor("#B8860B"),
                     "low": colors.HexColor("#1A7A4A")}
    rows = [["Factor", "Description", "Impact", "Direction"]]
    for p in pestel:
        rows.append([
            Paragraph(f"<b>{p['factor']}</b>", styles["table_cell"]),
            Paragraph(p["description"], styles["table_cell"]),
            Paragraph(p["impact"].upper(), styles["table_cell_c"]),
            Paragraph(p["direction"].upper(), styles["table_cell_c"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[2.2*cm, aw-2.2-2.2-2.5, 2.2*cm, 2.5*cm])
    ts = std_table_style()
    # Colour-code impact cells
    for i, p in enumerate(pestel, start=1):
        col = impact_colors.get(p["impact"], DGRAY)
        ts.add("TEXTCOLOR", (2, i), (2, i), col)
        ts.add("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")
        dir_col = colors.HexColor("#1A7A4A") if p["direction"] == "opportunity" else colors.HexColor("#B22222")
        ts.add("TEXTCOLOR", (3, i), (3, i), dir_col)
        ts.add("FONTNAME",  (3, i), (3, i), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Porter's 5 Forces bar chart
    story.append(Paragraph("Porter's Five Forces", styles["subsection"]))
    forces = ext.get("porter_forces", [])
    bar_data = [(f["force"], f["score"]) for f in forces]
    story.append(BarChart(bar_data, width=PAGE_W - 2 * MARGIN, max_val=10.0))

    # Rationale table
    story.append(Spacer(1, 0.3 * cm))
    rows2 = [["Force", "Intensity", "Score", "Rationale"]]
    for f in forces:
        rows2.append([
            Paragraph(f["force"], styles["table_cell"]),
            Paragraph(f["intensity"].upper(), styles["table_cell_c"]),
            Paragraph(str(f["score"]), styles["table_cell_c"]),
            Paragraph(f["rationale"], styles["table_cell"]),
        ])
    t2 = Table(rows2, colWidths=[3.5*cm, 2*cm, 1.5*cm, aw-3.5-2-1.5])
    t2.setStyle(std_table_style())
    story.append(t2)

    # Industry lifecycle
    lc = ext.get("industry_lifecycle", {})
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"<b>Industry Lifecycle Stage:</b> {lc.get('stage','').upper()} — {lc.get('strategic_implication','')}",
        styles["body"]))
    story.append(PageBreak())
    return story


def build_internal(data, styles):
    internal = data.get("internal", {})
    story = [SectionHeader("Internal Audit"), Spacer(1, 0.3 * cm)]

    # VRIO table
    story.append(Paragraph("VRIO Resource Analysis", styles["subsection"]))
    vrio_color_map = {"SCA": SCA_COLOR, "TCA": TCA_COLOR, "CP": CP_COLOR, "CD": CD_COLOR}
    vrio_label = {"SCA": "Sustained CA", "TCA": "Temporary CA",
                  "CP": "Competitive Parity", "CD": "Competitive Disadvantage"}
    rows = [["Resource", "Valuable", "Rare", "Inimitable", "Organized", "Implication"]]
    for r in internal.get("vrio_resources", []):
        ci = r.get("competitive_implication", "CP")
        impl_color = vrio_color_map.get(ci, DGRAY)
        rows.append([
            Paragraph(r["resource"], styles["table_cell"]),
            Paragraph("✓" if r["valuable"] else "✗", styles["table_cell_c"]),
            Paragraph("✓" if r["rare"] else "✗", styles["table_cell_c"]),
            Paragraph("✓" if r["inimitable"] else "✗", styles["table_cell_c"]),
            Paragraph("✓" if r["organized"] else "✗", styles["table_cell_c"]),
            Paragraph(vrio_label.get(ci, ci), styles["table_cell_c"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    cw = [3.8*cm, 1.6*cm, 1.4*cm, 1.8*cm, 1.8*cm, aw-3.8-1.6-1.4-1.8-1.8]
    t = Table(rows, colWidths=cw)
    ts = std_table_style()
    for i, r in enumerate(internal.get("vrio_resources", []), start=1):
        ci = r.get("competitive_implication", "CP")
        col = vrio_color_map.get(ci, DGRAY)
        ts.add("BACKGROUND", (5, i), (5, i), col)
        ts.add("TEXTCOLOR",  (5, i), (5, i), WHITE)
        ts.add("FONTNAME",   (5, i), (5, i), "Helvetica-Bold")
        # Checkmark colours
        for j in range(1, 5):
            val = [r["valuable"], r["rare"], r["inimitable"], r["organized"]][j-1]
            ts.add("TEXTCOLOR", (j, i), (j, i),
                   colors.HexColor("#1A7A4A") if val else colors.HexColor("#B22222"))
    t.setStyle(ts)
    story.append(t)

    # VRIO Legend
    legend_items = [("SCA", SCA_COLOR), ("TCA", TCA_COLOR), ("CP", CP_COLOR), ("CD", CD_COLOR)]
    leg_data = [[Paragraph(f"<b>{k}</b>: {vrio_label[k]}", ParagraphStyle(
        f"leg_{k}", fontName="Helvetica", fontSize=7.5,
        textColor=WHITE, backColor=v)) for k, v in legend_items]]
    leg_t = Table(leg_data, colWidths=[aw/4]*4)
    leg_t.setStyle(TableStyle([
        ("BACKGROUND", (i, 0), (i, 0), legend_items[i][1]) for i in range(4)
    ] + [
        ("TEXTCOLOR",  (0, 0), (-1, -1), WHITE),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(leg_t)

    # McKinsey 7S
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("McKinsey 7S Framework", styles["subsection"]))
    s7 = internal.get("mckinsey_7s", [])
    rows7 = [["Element", "Assessment", "Alignment Score"]]
    for el in s7:
        score = el.get("alignment_score", 0)
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        rows7.append([
            Paragraph(f"<b>{el['element']}</b>", styles["table_cell"]),
            Paragraph(el["assessment"], styles["table_cell"]),
            Paragraph(f"{bar}  {score:.0f}", ParagraphStyle(
                "mono", fontName="Courier", fontSize=7.5,
                textColor=NAVY, alignment=TA_LEFT)),
        ])
    t7 = Table(rows7, colWidths=[2.5*cm, aw-2.5-4.5, 4.5*cm])
    t7.setStyle(std_table_style())
    story.append(t7)
    story.append(PageBreak())
    return story


def build_position(data, styles):
    pos = data.get("position", {})
    story = [SectionHeader("Strategic Position"), Spacer(1, 0.3 * cm)]

    # SWOT 2×2
    story.append(Paragraph("SWOT Analysis", styles["subsection"]))
    aw = PAGE_W - 2 * MARGIN

    def swot_cell(items, bg, header, hdr_text_color=WHITE):
        content = [Paragraph(f"<b>{header}</b>", ParagraphStyle(
            "swot_h", fontName="Helvetica-Bold", fontSize=9,
            textColor=hdr_text_color, alignment=TA_CENTER))]
        for it in items:
            content.append(Paragraph(
                f"• {it['item']} ({it['impact_score']})",
                ParagraphStyle("swot_b", fontName="Helvetica", fontSize=8,
                               textColor=colors.HexColor("#1C1C1C"), leading=11)))
        return content

    s_cell = swot_cell(pos.get("strengths", []),     colors.HexColor("#E8F4EC"), "STRENGTHS")
    w_cell = swot_cell(pos.get("weaknesses", []),     colors.HexColor("#FFF0E8"), "WEAKNESSES")
    o_cell = swot_cell(pos.get("opportunities", []), colors.HexColor("#EEF4FF"), "OPPORTUNITIES")
    t_cell = swot_cell(pos.get("threats", []),        colors.HexColor("#FEF0F0"), "THREATS")

    def wrap_cell(items, bg):
        return Table([[it] for it in items],
                     style=TableStyle([
                         ("BACKGROUND", (0, 0), (-1, -1), bg),
                         ("TOPPADDING", (0, 0), (-1, -1), 3),
                         ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                         ("LEFTPADDING", (0, 0), (-1, -1), 6),
                         ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                     ]))

    sw_bg = colors.HexColor("#E8F4EC")
    wk_bg = colors.HexColor("#FFF0E8")
    op_bg = colors.HexColor("#EEF4FF")
    th_bg = colors.HexColor("#FEF0F0")

    swot_table = Table(
        [[wrap_cell(s_cell, sw_bg), wrap_cell(w_cell, wk_bg)],
         [wrap_cell(o_cell, op_bg), wrap_cell(t_cell, th_bg)]],
        colWidths=[aw / 2, aw / 2]
    )
    swot_table.setStyle(TableStyle([
        ("GRID",     (0, 0), (-1, -1), 1.5, NAVY),
        ("VALIGN",   (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(swot_table)

    # TOWS strategies
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("TOWS Strategic Directions", styles["subsection"]))
    tows = pos.get("tows_strategies", [])
    type_colors = {"SO": colors.HexColor("#1A7A4A"), "ST": colors.HexColor("#1B2A4A"),
                   "WO": colors.HexColor("#B8860B"), "WT": colors.HexColor("#B22222")}
    rows_t = [["Type", "Strategy", "Rationale"]]
    for t in tows:
        rows_t.append([
            Paragraph(f"<b>{t['type']}</b>", styles["table_cell_c"]),
            Paragraph(t["strategy"], styles["table_cell"]),
            Paragraph(t["rationale"], styles["table_cell"]),
        ])
    tt = Table(rows_t, colWidths=[1.2*cm, aw*0.42, aw-1.2-aw*0.42])
    ts_t = std_table_style()
    for i, t in enumerate(tows, start=1):
        c = type_colors.get(t["type"], NAVY)
        ts_t.add("BACKGROUND", (0, i), (0, i), c)
        ts_t.add("TEXTCOLOR",  (0, i), (0, i), WHITE)
    tt.setStyle(ts_t)
    story.append(tt)

    # Ansoff matrix
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Ansoff Growth Matrix", styles["subsection"]))
    ansoff = pos.get("ansoff_options", [])
    story.append(AnsoffMatrix(ansoff, width=PAGE_W - 2 * MARGIN, height=180))
    story.append(PageBreak())
    return story


def build_competitive(data, styles):
    comp = data.get("competitive", {})
    story = [SectionHeader("Competitive Dynamics"), Spacer(1, 0.3 * cm)]

    # Game Theory
    story.append(Paragraph("Game Theory Scenarios", styles["subsection"]))
    gt = comp.get("game_theory_scenarios", [])
    rows = [["Scenario", "Our Move", "Competitor Response",
             "Payoff Us", "Payoff Comp.", "Nash Eq.", "Recommended"]]
    for s in gt:
        rows.append([
            Paragraph(s.get("scenario", ""), styles["table_cell"]),
            Paragraph(s.get("our_move", ""), styles["table_cell"]),
            Paragraph(s.get("competitor_response", ""), styles["table_cell"]),
            Paragraph(str(s.get("payoff_us", "")), styles["table_cell_c"]),
            Paragraph(str(s.get("payoff_competitor", "")), styles["table_cell_c"]),
            Paragraph("Yes" if s.get("nash_equilibrium") else "No", styles["table_cell_c"]),
            Paragraph("✓" if s.get("recommended") else "", styles["table_cell_c"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[3.2*cm, 3*cm, 3*cm, 1.3*cm, 1.5*cm, 1.4*cm, aw-3.2-3-3-1.3-1.5-1.4])
    ts = std_table_style()
    for i, s in enumerate(gt, start=1):
        if s.get("recommended"):
            ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#E8F4EC"))
        if s.get("nash_equilibrium"):
            ts.add("FONTNAME", (5, i), (5, i), "Helvetica-Bold")
            ts.add("TEXTCOLOR", (5, i), (5, i), colors.HexColor("#1A7A4A"))
    t.setStyle(ts)
    story.append(t)

    # ERRC Grid
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Blue Ocean ERRC Grid", styles["subsection"]))
    errc = comp.get("errc_grid", [])
    action_colors = {"eliminate": colors.HexColor("#B22222"),
                     "reduce":    colors.HexColor("#C15B1E"),
                     "raise":     colors.HexColor("#1A7A4A"),
                     "create":    colors.HexColor("#1B2A4A")}
    rows2 = [["Factor", "Action", "Rationale", "Impact"]]
    for e in errc:
        rows2.append([
            Paragraph(e.get("factor", ""), styles["table_cell"]),
            Paragraph(e.get("action", "").upper(), styles["table_cell_c"]),
            Paragraph(e.get("rationale", ""), styles["table_cell"]),
            Paragraph(str(e.get("impact", "")), styles["table_cell_c"]),
        ])
    t2 = Table(rows2, colWidths=[3.5*cm, 2*cm, aw-3.5-2-1.5, 1.5*cm])
    ts2 = std_table_style()
    for i, e in enumerate(errc, start=1):
        col = action_colors.get(e.get("action", ""), DGRAY)
        ts2.add("BACKGROUND", (1, i), (1, i), col)
        ts2.add("TEXTCOLOR",  (1, i), (1, i), WHITE)
        ts2.add("FONTNAME",   (1, i), (1, i), "Helvetica-Bold")
    t2.setStyle(ts2)
    story.append(t2)

    # Blue Ocean statement
    bo = comp.get("blue_ocean_opportunity", "")
    if bo:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"<b>Blue Ocean Opportunity:</b> {bo}", styles["body"]))

    story.append(PageBreak())
    return story


def build_formulation(data, styles):
    form = data.get("formulation", {})
    story = [SectionHeader("Strategy Formulation"), Spacer(1, 0.3 * cm)]

    # Generic strategy
    story.append(Paragraph("Generic Strategy Recommendation", styles["subsection"]))
    generic = form.get("generic_strategies", [{}])[0]
    rec = form.get("recommended_strategy", "").upper()
    logic = form.get("strategic_logic", "")
    conf = form.get("formulation_confidence_score", 0)

    aw = PAGE_W - 2 * MARGIN
    badge = ScoreBadge(conf, "Confidence", size=80)
    detail = [
        Paragraph(f"<b>Recommended Strategy:</b> {rec}", styles["body_bold"]),
        Spacer(1, 4),
        Paragraph(logic, styles["body"]),
        Spacer(1, 4),
        Paragraph(f"<b>Fit Score:</b> {generic.get('fit_score', '')}  |  "
                  f"<b>Risks:</b> {', '.join(generic.get('risks', []))}", styles["small"]),
    ]
    lt = Table([[badge, detail]],
               colWidths=[2.8*cm, aw - 2.8*cm])
    lt.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(lt)

    # Strategy Clock
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Strategy Clock Position", styles["subsection"]))
    positions = form.get("strategy_clock_positions", [])
    clock = StrategyClockFlowable(positions, width=200, height=190)
    pos_detail = []
    for p in positions:
        pos_detail.append(Paragraph(
            f"<b>Position {p['position']}: {p['label']}</b>", styles["body_bold"]))
        pos_detail.append(Paragraph(
            f"Price: {p.get('price_point','')}  |  Perceived Value: {p.get('perceived_value','')}",
            styles["small"]))
        pos_detail.append(Paragraph(p.get("viability",""), styles["body"]))
    cl_t = Table([[clock, pos_detail]],
                 colWidths=[6.8*cm, aw - 6.8*cm])
    cl_t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(cl_t)
    story.append(PageBreak())
    return story


def build_risk(data, styles):
    risk = data.get("risk", {})
    story = [SectionHeader("Risk & Scenarios"), Spacer(1, 0.3 * cm)]

    # STEEP scenarios
    story.append(Paragraph("STEEP Scenario Analysis", styles["subsection"]))
    steep = risk.get("steep_scenarios", [])
    scenario_names = [s["name"].upper() for s in steep]
    dimensions = ["social", "technological", "economic", "environmental", "political"]
    rows = [["Dimension"] + [
        f"{n}\n(p={next((s['probability'] for s in steep if s['name']==n.lower()), '')})"
        for n in scenario_names
    ]]
    for dim in dimensions:
        row = [Paragraph(dim.capitalize(), styles["table_cell"])]
        for s in steep:
            row.append(Paragraph(s.get(dim, ""), styles["table_cell"]))
        rows.append(row)
    aw = PAGE_W - 2 * MARGIN
    ncols = len(steep) + 1
    cw = [2.5*cm] + [(aw - 2.5*cm) / len(steep)] * len(steep)
    t = Table(rows, colWidths=cw)
    ts = std_table_style()
    col_bgs = [colors.HexColor("#E8F4EC"), colors.HexColor("#EEF4FF"), colors.HexColor("#FEF0F0")]
    for j, s in enumerate(steep):
        for i in range(1, len(dimensions)+1):
            ts.add("BACKGROUND", (j+1, i), (j+1, i),
                   col_bgs[j % len(col_bgs)] if i % 2 == 0 else WHITE)
    t.setStyle(ts)
    story.append(t)

    # Top risks
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Top Strategic Risks", styles["subsection"]))
    top_risks = risk.get("top_risks", [])
    rows2 = [["#", "Risk", "Mitigation Priority"]]
    mitigations = risk.get("mitigation_priorities", [])
    for i, (r, m) in enumerate(zip(top_risks, mitigations + [""]*10), start=1):
        rows2.append([
            Paragraph(str(i), styles["table_cell_c"]),
            Paragraph(r, styles["table_cell"]),
            Paragraph(m, styles["table_cell"]),
        ])
    t2 = Table(rows2, colWidths=[0.8*cm, aw*0.42, aw-0.8-aw*0.42])
    t2.setStyle(std_table_style())
    story.append(t2)

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"<b>Overall Risk Score:</b> {risk.get('risk_score', '')} / 100",
        styles["body_bold"]))
    story.append(PageBreak())
    return story


def build_execution(data, styles):
    exec_data = data.get("execution", {})
    story = [SectionHeader("Execution Roadmap"), Spacer(1, 0.3 * cm)]

    # Balanced Scorecard
    story.append(Paragraph("Balanced Scorecard", styles["subsection"]))
    bsc = exec_data.get("balanced_scorecard", [])
    persp_colors = {
        "financial": colors.HexColor("#1B2A4A"),
        "customer":  colors.HexColor("#1A7A4A"),
        "internal":  colors.HexColor("#C15B1E"),
        "learning":  colors.HexColor("#B8860B"),
    }
    rows = [["Perspective", "Objective", "KPI", "Target", "Initiative"]]
    for b in bsc:
        p = b.get("perspective", "")
        rows.append([
            Paragraph(p.upper(), styles["table_cell_c"]),
            Paragraph(b.get("objective",""), styles["table_cell"]),
            Paragraph(b.get("kpi",""), styles["table_cell"]),
            Paragraph(b.get("target",""), styles["table_cell"]),
            Paragraph(b.get("initiative",""), styles["table_cell"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[2.2*cm, aw*0.22, aw*0.20, aw*0.20, aw-2.2-aw*0.22-aw*0.20-aw*0.20])
    ts = std_table_style()
    for i, b in enumerate(bsc, start=1):
        col = persp_colors.get(b.get("perspective",""), NAVY)
        ts.add("BACKGROUND", (0, i), (0, i), col)
        ts.add("TEXTCOLOR",  (0, i), (0, i), WHITE)
        ts.add("FONTNAME",   (0, i), (0, i), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)

    # OKRs
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Objectives & Key Results (OKRs)", styles["subsection"]))
    okrs = exec_data.get("okrs", [])
    rows2 = [["Objective", "Key Results", "Timeframe", "Owner"]]
    for o in okrs:
        kr_text = "\n".join([f"• {kr}" for kr in o.get("key_results", [])])
        rows2.append([
            Paragraph(o.get("objective",""), styles["table_cell"]),
            Paragraph(kr_text.replace("\n","<br/>"), styles["table_cell"]),
            Paragraph(o.get("timeframe",""), styles["table_cell_c"]),
            Paragraph(o.get("owner",""), styles["table_cell"]),
        ])
    t2 = Table(rows2, colWidths=[3.5*cm, aw*0.4, 2*cm, aw-3.5-aw*0.4-2])
    t2.setStyle(std_table_style())
    story.append(t2)

    story.append(Spacer(1, 0.2*cm))
    csf = exec_data.get("critical_success_factors", [])
    if csf:
        story.append(Paragraph(
            "<b>Critical Success Factors:</b> " + " | ".join(csf), styles["small"]))
    story.append(PageBreak())
    return story


def build_options_ranking(data, styles):
    syn = data.get("synthesis", {})
    story = [SectionHeader("Strategic Options Ranking"), Spacer(1, 0.3 * cm)]

    options = syn.get("strategic_options", [])
    aw = PAGE_W - 2 * MARGIN

    rows = [["Rank", "Option", "Strategic Fit", "Risk", "Feasibility", "Overall Score", "Supporting Frameworks"]]
    for i, opt in enumerate(sorted(options, key=lambda x: -x.get("overall_score", 0)), start=1):
        score = opt.get("overall_score", 0)
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        frameworks = ", ".join(opt.get("supporting_frameworks", []))
        rows.append([
            Paragraph(f"#{i}", styles["table_cell_c"]),
            Paragraph(f"<b>{opt.get('option','')}</b>", styles["table_cell"]),
            Paragraph(str(opt.get("strategic_fit_score","")), styles["table_cell_c"]),
            Paragraph(str(opt.get("risk_score","")), styles["table_cell_c"]),
            Paragraph(str(opt.get("feasibility_score","")), styles["table_cell_c"]),
            Paragraph(f"{bar}\n{score}", ParagraphStyle(
                "score_bar", fontName="Courier", fontSize=7,
                textColor=NAVY, alignment=TA_CENTER)),
            Paragraph(frameworks, styles["small"]),
        ])
    t = Table(rows, colWidths=[1*cm, 3.5*cm, 1.8*cm, 1.3*cm, 1.8*cm, 3.5*cm, aw-1-3.5-1.8-1.3-1.8-3.5])
    ts = std_table_style()
    for i, opt in enumerate(sorted(options, key=lambda x: -x.get("overall_score", 0)), start=1):
        if i == 1:
            ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#E8F4EC"))
            ts.add("FONTNAME",   (0, i), (-1, i), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)

    # Rationale bullets
    story.append(Spacer(1, 0.4*cm))
    for opt in options:
        story.append(Paragraph(
            f"<b>{opt.get('option','')}</b> — {opt.get('rationale','')}",
            styles["body"]))
        if opt.get("conflicting_signals"):
            story.append(Paragraph(
                f"<i>Conflicting signals: {', '.join(opt['conflicting_signals'])}</i>",
                styles["small"]))

    story.append(PageBreak())
    return story


def build_board_narrative(data, styles):
    syn = data.get("synthesis", {})
    story = [SectionHeader("Board Narrative"), Spacer(1, 0.4 * cm)]

    narrative = syn.get("board_narrative", "")
    # Split into paragraphs
    paras = [p.strip() for p in narrative.split(". ") if p.strip()]
    # Reconstruct as sentences grouped into 2
    groups = []
    for i in range(0, len(paras), 2):
        chunk = ". ".join(paras[i:i+2])
        if not chunk.endswith("."):
            chunk += "."
        groups.append(chunk)

    for g in groups:
        story.append(Paragraph(g, styles["narrative"]))
        story.append(Spacer(1, 0.15*cm))

    # Scenario branches
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Scenario-Based Recommendations", styles["subsection"]))
    branches = syn.get("scenario_branches", [])
    aw = PAGE_W - 2 * MARGIN
    rows = [["Scenario", "Recommended Option", "Expected Outcome", "Key Assumptions"]]
    for b in branches:
        rows.append([
            Paragraph(b.get("scenario","").upper(), styles["table_cell_c"]),
            Paragraph(b.get("recommended_option",""), styles["table_cell"]),
            Paragraph(b.get("expected_outcome",""), styles["table_cell"]),
            Paragraph(" | ".join(b.get("key_assumptions",[])), styles["small"]),
        ])
    t = Table(rows, colWidths=[2*cm, 3.5*cm, aw*0.35, aw-2-3.5-aw*0.35])
    t.setStyle(std_table_style())
    story.append(t)
    story.append(PageBreak())
    return story


def build_appendix(data, styles):
    story = [SectionHeader("Appendix — Raw Scores Summary"), Spacer(1, 0.3 * cm)]
    story.append(Paragraph(
        "Aggregate scores across all analytical agents used in this report.",
        styles["body"]))
    story.append(Spacer(1, 0.3*cm))

    ext = data.get("external", {})
    internal = data.get("internal", {})
    pos = data.get("position", {})
    comp = data.get("competitive", {})
    form = data.get("formulation", {})
    risk = data.get("risk", {})
    exec_d = data.get("execution", {})
    syn = data.get("synthesis", {})

    rows = [["Agent / Framework", "Score / Value", "Notes"]]
    score_rows = [
        ("External Environment",  f"{ext.get('overall_attractiveness_score','')} / 100",
         "Industry attractiveness"),
        ("Internal Audit",        f"{internal.get('internal_strength_score','')} / 100",
         "Resource strength"),
        ("Strategic Position",    f"{pos.get('strategic_position_score','')} / 100",
         "SWOT positioning"),
        ("Competitive Intensity", f"{comp.get('competitive_intensity_score','')} / 100",
         "Rivalry & dynamics"),
        ("Strategy Formulation",  f"{form.get('formulation_confidence_score','')} / 100",
         "Confidence in generic strategy"),
        ("Risk Assessment",       f"{risk.get('risk_score','')} / 100",
         "Composite risk level"),
        ("Execution Readiness",   f"{exec_d.get('execution_readiness_score','')} / 100",
         "Capability & readiness"),
        ("Overall Strategic Fit", f"{syn.get('overall_strategic_fit_score','')} / 100",
         "Synthesis score"),
    ]

    for name, score, note in score_rows:
        rows.append([
            Paragraph(name, styles["table_cell"]),
            Paragraph(f"<b>{score}</b>", styles["table_cell_c"]),
            Paragraph(note, styles["small"]),
        ])

    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[5*cm, 3*cm, aw-5-3])
    ts = std_table_style()
    # Highlight overall
    ts.add("BACKGROUND", (0, len(score_rows)), (-1, len(score_rows)), colors.HexColor("#E8EDF5"))
    ts.add("FONTNAME",   (0, len(score_rows)), (-1, len(score_rows)), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)

    # Porter scores
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Porter's Five Forces — Detailed Scores", styles["subsection"]))
    forces = ext.get("porter_forces", [])
    rows2 = [["Force", "Score / 10", "Intensity"]]
    for f in forces:
        rows2.append([
            Paragraph(f["force"], styles["table_cell"]),
            Paragraph(str(f["score"]), styles["table_cell_c"]),
            Paragraph(f["intensity"].upper(), styles["table_cell_c"]),
        ])
    t2 = Table(rows2, colWidths=[6*cm, 2.5*cm, aw-6-2.5])
    t2.setStyle(std_table_style())
    story.append(t2)

    # McKinsey 7S scores
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("McKinsey 7S — Alignment Scores", styles["subsection"]))
    s7 = internal.get("mckinsey_7s", [])
    rows3 = [["Element", "Alignment Score", "Assessment"]]
    for el in s7:
        rows3.append([
            Paragraph(el["element"], styles["table_cell"]),
            Paragraph(str(el.get("alignment_score","")), styles["table_cell_c"]),
            Paragraph(el.get("assessment",""), styles["table_cell"]),
        ])
    t3 = Table(rows3, colWidths=[2.5*cm, 2.5*cm, aw-2.5-2.5])
    t3.setStyle(std_table_style())
    story.append(t3)

    return story


# ── Main generator ────────────────────────────────────────────────────────────

def generate_report(json_path: str, output_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    styles = build_styles()

    # Page templates
    frame_normal = Frame(MARGIN, MARGIN + 1*cm, PAGE_W - 2*MARGIN,
                         PAGE_H - 2*MARGIN - 2.5*cm, id="normal")
    frame_cover  = Frame(0, 0, PAGE_W, PAGE_H, id="cover")

    def cover_tpl():
        return PageTemplate(id="Cover", frames=[frame_cover],
                            onPage=_cover_page)

    def normal_tpl():
        return PageTemplate(id="Normal", frames=[frame_normal],
                            onPage=_header_footer)

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        pageTemplates=[cover_tpl(), normal_tpl()],
        title=f"Strategic Report — {data.get('company','')}",
        author="AI Strategy Simulator",
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 1.8*cm, bottomMargin=MARGIN + 1*cm,
    )

    story = []

    # 1. Cover
    story += build_cover(data, styles)

    # Switch to normal template after cover
    from reportlab.platypus import NextPageTemplate
    story.append(NextPageTemplate("Normal"))

    # 2. Executive Summary
    story += build_executive_summary(data, styles)

    # 3. External Environment
    story += build_external(data, styles)

    # 4. Internal Audit
    story += build_internal(data, styles)

    # 5. Strategic Position
    story += build_position(data, styles)

    # 6. Competitive Dynamics
    story += build_competitive(data, styles)

    # 7. Strategy Formulation
    story += build_formulation(data, styles)

    # 8. Risk & Scenarios
    story += build_risk(data, styles)

    # 9. Execution Roadmap
    story += build_execution(data, styles)

    # 10. Strategic Options Ranking
    story += build_options_ranking(data, styles)

    # 11. Board Narrative
    story += build_board_narrative(data, styles)

    # 12. Appendix
    story += build_appendix(data, styles)

    doc.build(story)
    print(f"Report saved: {output_path}")


# ── CLI entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    json_path   = os.path.join(base, "output.json")
    output_path = os.path.join(base, "strategy_report.pdf")
    generate_report(json_path, output_path)
