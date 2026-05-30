"""
AI Strategy Simulator — Boardroom PDF Report Generator
Entry point: generate_report(json_path, output_path)
"""

import json
import math
import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether, HRFlowable, NextPageTemplate, Image,
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY  = colors.HexColor("#1B2A4A")
GOLD  = colors.HexColor("#C9A84C")
WHITE = colors.white
LGRAY = colors.HexColor("#F4F5F7")
MGRAY = colors.HexColor("#D0D3DA")
DGRAY = colors.HexColor("#6B7280")

# Slightly blue-tinted alternating row colour
BLUEGRAY = colors.HexColor("#F0F3F8")
ROW_ALT  = BLUEGRAY

# Semantic colours
GREEN = colors.HexColor("#1A7A4A")
AMBER = colors.HexColor("#B8860B")
RED   = colors.HexColor("#B22222")

# VRIO colours
SCA_COLOR = GREEN
TCA_COLOR = AMBER
CP_COLOR  = colors.HexColor("#C15B1E")   # orange
CD_COLOR  = RED

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

# ── Unicode arrow support (Windows Arial fall-back to ASCII) ────────────────────
ARROW_FONT = "Helvetica"
for _fp in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\Arial.ttf"):
    try:
        pdfmetrics.registerFont(TTFont("ArialU", _fp))
        ARROW_FONT = "ArialU"
        break
    except Exception:
        continue

UP_ARROW   = "▲" if ARROW_FONT != "Helvetica" else "+"
DOWN_ARROW = "▼" if ARROW_FONT != "Helvetica" else "-"


# ── Styles ────────────────────────────────────────────────────────────────────

def build_styles():
    base = getSampleStyleSheet()
    s = {}

    def ps(name, **kw):
        s[name] = ParagraphStyle(name, **kw)

    ps("cover_company",  fontName="Helvetica-Bold", fontSize=28,
       textColor=WHITE, alignment=TA_CENTER, spaceAfter=6, leading=32)
    ps("cover_industry", fontName="Helvetica", fontSize=14,
       textColor=GOLD, alignment=TA_CENTER, spaceAfter=4, leading=18)
    ps("cover_question", fontName="Helvetica", fontSize=12,
       textColor=WHITE, alignment=TA_CENTER, spaceAfter=4, leading=17)
    ps("cover_date",     fontName="Helvetica", fontSize=10,
       textColor=MGRAY, alignment=TA_CENTER)
    ps("cover_conf",     fontName="Helvetica-Bold", fontSize=9,
       textColor=GOLD, alignment=TA_CENTER, spaceAfter=0)

    ps("section_header", fontName="Helvetica-Bold", fontSize=13,
       textColor=GOLD, alignment=TA_LEFT, spaceAfter=6, spaceBefore=4)
    ps("subsection",     fontName="Helvetica-Bold", fontSize=11,
       textColor=NAVY, alignment=TA_LEFT, spaceAfter=4, spaceBefore=6)
    ps("body",           fontName="Helvetica", fontSize=9.5,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_JUSTIFY,
       leading=14, spaceAfter=4)
    ps("body_center",    fontName="Helvetica", fontSize=9.5,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_CENTER, leading=14)
    ps("body_bold",      fontName="Helvetica-Bold", fontSize=9.5,
       textColor=NAVY, alignment=TA_LEFT, leading=14)
    ps("small",          fontName="Helvetica", fontSize=8,
       textColor=DGRAY, alignment=TA_LEFT, leading=11)
    ps("small_center",   fontName="Helvetica", fontSize=8,
       textColor=DGRAY, alignment=TA_CENTER, leading=11)
    ps("table_header",   fontName="Helvetica-Bold", fontSize=8.5,
       textColor=WHITE, alignment=TA_CENTER, leading=11)
    ps("table_cell",     fontName="Helvetica", fontSize=8.5,
       textColor=colors.black, alignment=TA_LEFT, leading=12)
    ps("table_cell_c",   fontName="Helvetica", fontSize=8.5,
       textColor=colors.black, alignment=TA_CENTER, leading=12)
    # White category-label cells for navy first columns
    ps("cell_label",     fontName="Helvetica-Bold", fontSize=8.5,
       textColor=WHITE, alignment=TA_LEFT, leading=12)
    ps("cell_label_c",   fontName="Helvetica-Bold", fontSize=8.5,
       textColor=WHITE, alignment=TA_CENTER, leading=12)
    ps("kpi_head",       fontName="Helvetica-Bold", fontSize=11,
       textColor=WHITE, alignment=TA_CENTER, leading=13)
    ps("score_label",    fontName="Helvetica-Bold", fontSize=22,
       textColor=WHITE, alignment=TA_CENTER)
    ps("score_sub",      fontName="Helvetica", fontSize=9,
       textColor=GOLD, alignment=TA_CENTER)
    ps("narrative",      fontName="Helvetica", fontSize=9.5,
       textColor=colors.HexColor("#1C1C1C"), alignment=TA_JUSTIFY,
       leading=15, spaceAfter=6)
    ps("toc_name",       fontName="Helvetica-Bold", fontSize=10.5,
       textColor=NAVY, alignment=TA_LEFT, leading=16)
    ps("toc_desc",       fontName="Helvetica", fontSize=9,
       textColor=DGRAY, alignment=TA_RIGHT, leading=16)
    ps("toc_name_hl",    fontName="Helvetica-Bold", fontSize=10.5,
       textColor=GOLD, alignment=TA_LEFT, leading=16)
    ps("toc_desc_hl",    fontName="Helvetica-Oblique", fontSize=9,
       textColor=GOLD, alignment=TA_RIGHT, leading=16)
    ps("page_num",       fontName="Helvetica", fontSize=8,
       textColor=DGRAY, alignment=TA_CENTER)
    return s


def _kpi_val_style(color):
    return ParagraphStyle("kpi_val", fontName="Helvetica-Bold", fontSize=13,
                          textColor=color, alignment=TA_CENTER, leading=15)


# ── Custom Flowables ──────────────────────────────────────────────────────────

class SectionHeader(Flowable):
    """Navy banner with gold left accent bar, white title and optional score badge."""
    def __init__(self, text, score=None, width=None):
        super().__init__()
        self.text = text
        self.score = score
        self._width = width or (PAGE_W - 2 * MARGIN)
        self.height = 28

    def wrap(self, availW, availH):
        self._width = availW
        return availW, self.height

    def _score_val(self):
        try:
            if self.score is None or self.score == "":
                return None
            return int(round(float(self.score)))
        except (TypeError, ValueError):
            return None

    def draw(self):
        c = self.canv
        w, h = self._width, self.height
        # Navy banner
        c.setFillColor(NAVY)
        c.rect(0, 0, w, h, fill=1, stroke=0)
        # Gold left accent bar (4pt, full height)
        c.setFillColor(GOLD)
        c.rect(0, 0, 4, h, fill=1, stroke=0)
        # Title
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(14, h / 2 - 4, self.text.upper())
        # Inline score badge on the right
        sv = self._score_val()
        if sv is not None:
            r = 11
            cx, cy = w - r - 10, h / 2
            c.setStrokeColor(GOLD)
            c.setLineWidth(2)
            c.circle(cx, cy, r, fill=0, stroke=1)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(cx, cy - 3.5, str(sv))


class ScoreBadge(Flowable):
    """Circular gauge-style badge showing a numeric score with colour coding."""
    def __init__(self, score, label="Strategic Fit Score", size=90):
        super().__init__()
        self.score = score
        self.label = label
        self.size = size
        self.width = size
        self.height = size + 18

    def wrap(self, availW, availH):
        return self.width, self.height

    def draw(self):
        c = self.canv
        try:
            val = float(self.score)
        except (TypeError, ValueError):
            val = 0
        r = self.size / 2 - 2
        cx = self.size / 2
        cy = self.height - self.size / 2 - 2

        hint = GREEN if val >= 75 else AMBER if val >= 50 else RED

        # Shadow
        c.setFillColor(colors.HexColor("#C0C4CC"))
        c.circle(cx + 2, cy - 2, r, fill=1, stroke=0)
        # Main navy disc
        c.setFillColor(NAVY)
        c.circle(cx, cy, r, fill=1, stroke=0)
        # Inner colour-coded glow hint
        c.saveState()
        c.setFillAlpha(0.30)
        c.setFillColor(hint)
        c.circle(cx, cy, r * 0.62, fill=1, stroke=0)
        c.restoreState()
        # Gauge tick marks
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        for i in range(12):
            a = math.radians(i * 30)
            ca, sa = math.cos(a), math.sin(a)
            c.line(cx + (r - 1) * ca, cy + (r - 1) * sa,
                   cx + (r - 5) * ca, cy + (r - 5) * sa)
        # Gold ring
        c.setStrokeColor(GOLD)
        c.setLineWidth(3)
        c.circle(cx, cy, r - 1, fill=0, stroke=1)
        # Score number
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(cx, cy - 9, str(int(val)))
        # Label below
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx, cy - r - 11, self.label.upper())


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
        risk_colors = {"low": GREEN, "medium": AMBER, "high": RED}
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
                c.setFillColor(bg_colors[(col, row)])
                c.rect(x, y, cw, ch, fill=1, stroke=0)
                c.setStrokeColor(NAVY)
                c.setLineWidth(0.5)
                c.rect(x, y, cw, ch, fill=0, stroke=1)
                c.setFont("Helvetica-Bold", 7.5)
                c.setFillColor(NAVY)
                c.drawCentredString(x + cw/2, y + ch - 12, titles[(col, row)])
                init, risk = grid[(col, row)]
                if init:
                    c.setFont("Helvetica", 6.5)
                    c.setFillColor(colors.HexColor("#333333"))
                    words = init.split()
                    lines, line = [], []
                    for wd in words:
                        line.append(wd)
                        if len(" ".join(line)) > 22:
                            lines.append(" ".join(line[:-1]))
                            line = [wd]
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
        c = self.canv
        cx, cy = self._w / 2, self._h / 2
        r = min(cx, cy) - 20

        c.setStrokeColor(NAVY)
        c.setLineWidth(1.5)
        c.setFillColor(LGRAY)
        c.circle(cx, cy, r, fill=1, stroke=1)

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

        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(NAVY)
        c.drawCentredString(cx, cy - 3, "Strategy")


# ── Page decorators ───────────────────────────────────────────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()
    pw, ph = A4
    company  = getattr(doc, "_company", "")
    date_str = getattr(doc, "_date", "")
    section  = getattr(doc, "_section", "")

    # Logo placeholder (top-right): navy box with gold caption
    lw, lh = 2.6 * cm, 0.75 * cm
    lx = pw - MARGIN - lw
    ly = ph - 0.7 * cm - lh
    canvas.setFillColor(NAVY)
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.8)
    canvas.rect(lx, ly, lw, lh, fill=1, stroke=1)
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 6.5)
    canvas.drawCentredString(lx + lw / 2, ly + lh / 2 - 2.5, "COMPANY LOGO")

    # Header text row
    ty = ph - 1.95 * cm
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(GOLD)
    canvas.drawString(MARGIN, ty, "CONFIDENTIAL")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DGRAY)
    canvas.drawCentredString(pw / 2, ty, "AI Strategy Simulator")
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(NAVY)
    canvas.drawRightString(pw - MARGIN, ty, company)

    # Gold header line
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.line(MARGIN, ph - 2.15 * cm, pw - MARGIN, ph - 2.15 * cm)

    # Navy footer line
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN, 1.5 * cm, pw - MARGIN, 1.5 * cm)

    # Footer: date left, page centre, section right
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DGRAY)
    canvas.drawString(MARGIN, 0.95 * cm, date_str)
    canvas.drawRightString(pw - MARGIN, 0.95 * cm, section)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(pw / 2, 0.95 * cm, f"— {doc.page} —")

    canvas.restoreState()


def _cover_page(canvas, doc):
    """Full navy cover background with gold rules and confidential marks."""
    canvas.saveState()
    pw, ph = A4
    # Full navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, pw, ph, fill=1, stroke=0)
    # Gold top & bottom rules (3pt)
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(3)
    canvas.line(MARGIN, ph - 0.9 * cm, pw - MARGIN, ph - 0.9 * cm)
    canvas.line(MARGIN, 1.0 * cm, pw - MARGIN, 1.0 * cm)
    # CONFIDENTIAL top-right
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawRightString(pw - MARGIN, ph - 1.35 * cm, "CONFIDENTIAL")
    # POWERED BY bottom-centre
    canvas.drawCentredString(pw / 2, 0.6 * cm, "POWERED BY MULTI-AGENT AI")
    canvas.restoreState()


# ── Table helpers ─────────────────────────────────────────────────────────────

def std_table_style(header_rows=1, col_widths=None, first_col=True):
    ts = TableStyle([
        # Header
        ("BACKGROUND",  (0, 0), (-1, header_rows - 1), NAVY),
        ("TEXTCOLOR",   (0, 0), (-1, header_rows - 1), WHITE),
        ("FONTNAME",    (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, header_rows - 1), 9),
        ("ALIGN",       (0, 0), (-1, header_rows - 1), "CENTER"),
        ("LINEBELOW",   (0, header_rows - 1), (-1, header_rows - 1), 1.5, GOLD),
        # Body
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [WHITE, BLUEGRAY]),
        ("TEXTCOLOR",   (0, header_rows), (-1, -1), colors.black),
        ("FONTNAME",    (0, header_rows), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, header_rows), (-1, -1), 8.5),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, header_rows - 1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, header_rows - 1), 8),
        ("TOPPADDING",    (0, header_rows), (-1, -1), 5),
        ("BOTTOMPADDING", (0, header_rows), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID",        (0, 0), (-1, -1), 0.4, MGRAY),
        # Subtle box-shadow effect (outer box + thicker bottom/right edge)
        ("BOX",         (0, 0), (-1, -1), 0.75, MGRAY),
        ("LINEBELOW",   (0, -1), (-1, -1), 1.5, DGRAY),
        ("LINEAFTER",   (-1, 0), (-1, -1), 1.5, DGRAY),
    ])
    # First column = navy category-label column
    if first_col:
        ts.add("BACKGROUND", (0, header_rows), (0, -1), NAVY)
        ts.add("TEXTCOLOR",  (0, header_rows), (0, -1), WHITE)
        ts.add("FONTNAME",   (0, header_rows), (0, -1), "Helvetica-Bold")
    return ts


def P(text, style_name, styles):
    return Paragraph(str(text), styles[style_name])


def make_score_bar(score, width=90, height=10):
    """Return a Drawing with a navy filled bar representing score/100."""
    total_h = height + 16
    d = Drawing(width, total_h)
    d.add(Rect(0, 16, width, height,
               fillColor=LGRAY, strokeColor=None, strokeWidth=0))
    filled_w = max(1, float(score) / 100.0 * width)
    d.add(Rect(0, 16, filled_w, height,
               fillColor=NAVY, strokeColor=None, strokeWidth=0))
    if filled_w >= 4:
        d.add(Rect(filled_w - 4, 16, 4, height,
                   fillColor=GOLD, strokeColor=None, strokeWidth=0))
    d.add(String(width / 2, 2, str(int(score)),
                 fontName="Helvetica-Bold", fontSize=8,
                 textAnchor="middle", fillColor=NAVY))
    return d


def _chart_image(charts_dir, filename, max_w=480):
    """Return a scaled ReportLab Image, or None if the file does not exist."""
    if not charts_dir:
        return None
    path = os.path.join(charts_dir, filename)
    if not os.path.exists(path):
        return None
    img = Image(path)
    ratio = img.drawHeight / img.drawWidth
    w = min(max_w, img.drawWidth)
    img.drawWidth = w
    img.drawHeight = w * ratio
    img.hAlign = "CENTER"
    return img


# ── Section builders ──────────────────────────────────────────────────────────

def build_cover(data, styles):
    """Cover page — light flowables on the navy background drawn by _cover_page."""
    story = []
    company = data.get("company", "Company Name")
    industry = data.get("industry", "")
    question = data.get("strategic_question", "")
    date_str = datetime.now().strftime("%B %Y")
    aw = PAGE_W - 2 * MARGIN

    story.append(Spacer(1, 3.0 * cm))
    story.append(Paragraph("AI STRATEGY SIMULATOR", ParagraphStyle(
        "cov_title", fontName="Helvetica-Bold", fontSize=32,
        textColor=WHITE, alignment=TA_CENTER, leading=36)))
    story.append(Spacer(1, 0.45 * cm))
    story.append(Paragraph("STRATEGIC INTELLIGENCE REPORT", ParagraphStyle(
        "cov_subtitle", fontName="Helvetica", fontSize=14,
        textColor=GOLD, alignment=TA_CENTER, leading=18)))

    story.append(Spacer(1, 0.7 * cm))
    story.append(HRFlowable(width="55%", thickness=3, color=GOLD,
                            spaceBefore=4, spaceAfter=4, hAlign="CENTER"))

    story.append(Spacer(1, 1.6 * cm))
    story.append(Paragraph(company.upper(), styles["cover_company"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(industry, ParagraphStyle(
        "cov_ind", fontName="Helvetica-Oblique", fontSize=13,
        textColor=GOLD, alignment=TA_CENTER, leading=16)))

    story.append(Spacer(1, 1.1 * cm))
    q_tbl = Table(
        [[Paragraph(f'"{question}"', ParagraphStyle(
            "cov_q", fontName="Helvetica-Oblique", fontSize=12,
            textColor=WHITE, alignment=TA_CENTER, leading=17))]],
        colWidths=[aw * 0.72], hAlign="CENTER",
    )
    q_tbl.setStyle(TableStyle([
        ("LINEBEFORE",    (0, 0), (0, -1), 3, GOLD),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(q_tbl)

    story.append(Spacer(1, 1.4 * cm))
    story.append(Paragraph(date_str, ParagraphStyle(
        "cov_dt", fontName="Helvetica", fontSize=10,
        textColor=MGRAY, alignment=TA_CENTER)))

    # Switch template BEFORE PageBreak so page 2 gets the Normal header.
    story.append(NextPageTemplate("Normal"))
    story.append(PageBreak())
    return story


def build_toc(data, styles):
    """Table of contents with dot leaders, descriptions, and right-aligned page numbers."""
    aw = PAGE_W - 2 * MARGIN
    story = [SectionHeader("Table of Contents"), Spacer(1, 0.5 * cm)]

    entries = [
        ("Executive Summary",         "Overall strategic fit & key tensions",           3),
        ("External Environment",      "PESTEL · Porter's · Lifecycle · Market Data",   4),
        ("Internal Audit",            "VRIO resources & McKinsey 7S",                   6),
        ("Strategic Position",        "SWOT · TOWS · Ansoff growth matrix",             7),
        ("Competitive Dynamics",      "Game theory & Blue Ocean ERRC",                  8),
        ("Strategy Formulation",      "Generic strategy & Strategy Clock",              9),
        ("Risk & Scenarios",          "STEEP scenarios & top strategic risks",         10),
        ("Ethics & ESG",              "Stakeholder impact · ESG scoring",              11),
        ("Execution Roadmap",         "Balanced Scorecard & OKRs",                    12),
        ("Financial Viability",       "DCF · unit economics · valuation · go signal",  13),
        ("Strategic Options Ranking", "Weighted scoring of strategic options",         16),
        ("Board Narrative",           "Recommendation & scenario branches",            17),
        ("Appendix",                  "Aggregate scores summary",                      18),
    ]

    pg_style = ParagraphStyle(
        "toc_pg", fontName="Helvetica-Bold", fontSize=11,
        textColor=GOLD, alignment=TA_RIGHT, leading=16,
    )
    pg_style_hl = ParagraphStyle(
        "toc_pg_hl", fontName="Helvetica-Bold", fontSize=11,
        textColor=WHITE, alignment=TA_RIGHT, leading=16,
    )

    rows = []
    hl_idx = None
    for i, (name, desc, pg) in enumerate(entries):
        if name == "Financial Viability":
            hl_idx = i
            rows.append([
                Paragraph(name, styles["toc_name_hl"]),
                Paragraph(desc, styles["toc_desc_hl"]),
                Paragraph(str(pg), pg_style_hl),
            ])
        else:
            rows.append([
                Paragraph(name, styles["toc_name"]),
                Paragraph(desc, styles["toc_desc"]),
                Paragraph(str(pg), pg_style),
            ])

    t = Table(rows, colWidths=[aw * 0.38, aw * 0.50, aw * 0.12])
    style_cmds = [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LGRAY]),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",            (0, 0), (-1, -1), 0.75, MGRAY),
    ]
    # Gold dotted leaders spanning the full row width (name → description → page number)
    for i in range(len(rows)):
        style_cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, GOLD, None, (1, 2)))
    # Highlight Financial Viability row
    if hl_idx is not None:
        style_cmds.append(("BACKGROUND", (0, hl_idx), (-1, hl_idx), NAVY))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(PageBreak())
    return story


def build_executive_summary(data, styles, charts_dir=None):
    syn = data.get("synthesis", {})
    summary = syn.get("executive_summary", "")
    score = syn.get("overall_strategic_fit_score", 0)
    aw = PAGE_W - 2 * MARGIN

    story = [SectionHeader("Executive Summary", score=score), Spacer(1, 0.3 * cm)]

    # Large badge (left) + radar chart (right)
    # Badge column narrowed to 130 pt so radar gets the remaining ~340 pt of column width.
    # rowHeights=240 guarantees the chart has enough vertical room to be legible.
    BADGE_COL = 130
    RADAR_ROW_H = 240
    badge = ScoreBadge(score, "Overall Strategic Fit", size=120)
    radar_img = _chart_image(charts_dir, "agent_scores_radar.png",
                             max_w=aw - BADGE_COL)
    top = Table(
        [[badge, radar_img or Spacer(1, RADAR_ROW_H)]],
        colWidths=[BADGE_COL, aw - BADGE_COL],
        rowHeights=[RADAR_ROW_H],
    )
    top.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(top)

    # Summary text in two columns
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("Executive Overview", styles["subsection"]))
    sents = [s.strip() for s in summary.replace("\n", " ").split(". ") if s.strip()]
    mid = (len(sents) + 1) // 2
    left_txt = ". ".join(sents[:mid])
    right_txt = ". ".join(sents[mid:])
    if left_txt and not left_txt.endswith("."):
        left_txt += "."
    if right_txt and not right_txt.endswith("."):
        right_txt += "."
    two_col = Table(
        [[Paragraph(left_txt, styles["narrative"]),
          Paragraph(right_txt, styles["narrative"])]],
        colWidths=[aw / 2 - 6, aw / 2 - 6],
    )
    two_col.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 12),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(two_col)

    # Conflicts & resolutions (colour-coded columns)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Key Strategic Tensions & Resolutions", styles["subsection"]))
    conflicts = syn.get("inter_agent_conflicts", [])
    resolutions = syn.get("conflict_resolutions", [])
    rows = [["Tension", "Resolution"]]
    for c, r in zip(conflicts, resolutions):
        rows.append([Paragraph(c, styles["table_cell"]),
                     Paragraph(r, styles["table_cell"])])
    t = Table(rows, colWidths=[aw * 0.45, aw * 0.55])
    ts = std_table_style(first_col=False)
    ts.add("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#FBEAEA"))
    ts.add("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#EAF3EC"))
    t.setStyle(ts)
    story.append(t)
    story.append(PageBreak())
    return story


def build_external(data, styles, charts_dir=None):
    ext = data.get("external", {})
    story = [SectionHeader("External Environment Analysis",
                           score=ext.get("overall_attractiveness_score")),
             Spacer(1, 0.3 * cm)]

    # PESTEL table
    story.append(Paragraph("PESTEL Analysis", styles["subsection"]))
    pestel = ext.get("pestel", [])
    impact_colors = {"high": RED, "medium": AMBER, "low": GREEN}
    rows = [["Factor", "Description", "Impact", "Direction"]]
    for p in pestel:
        rows.append([
            Paragraph(p["factor"], styles["cell_label"]),
            Paragraph(p["description"], styles["table_cell"]),
            Paragraph(p["impact"].upper(), styles["table_cell_c"]),
            Paragraph(p["direction"].upper(), styles["table_cell_c"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[2.8*cm, aw-2.8*cm-2.2*cm-3*cm, 2.2*cm, 3*cm])
    ts = std_table_style()
    for i, p in enumerate(pestel, start=1):
        col = impact_colors.get(p["impact"], DGRAY)
        ts.add("TEXTCOLOR", (2, i), (2, i), col)
        ts.add("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")
        dir_col = GREEN if p["direction"] == "opportunity" else RED
        ts.add("TEXTCOLOR", (3, i), (3, i), dir_col)
        ts.add("FONTNAME",  (3, i), (3, i), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Porter's 5 Forces
    forces = ext.get("porter_forces", [])
    bar_data = [(f["force"], f["score"]) for f in forces]
    rows2 = [["Force", "Intensity", "Score", "Rationale"]]
    for f in forces:
        rows2.append([
            Paragraph(f["force"], styles["cell_label"]),
            Paragraph(f["intensity"].upper(), styles["table_cell_c"]),
            Paragraph(str(f["score"]), styles["table_cell_c"]),
            Paragraph(f["rationale"], styles["table_cell"]),
        ])
    t2 = Table(rows2, colWidths=[3.5*cm, 2*cm, 1.5*cm, aw-3.5*cm-2*cm-1.5*cm],
               splitByRow=0)
    t2.setStyle(std_table_style())
    story.append(KeepTogether([
        Paragraph("Porter's Five Forces", styles["subsection"]),
        BarChart(bar_data, width=PAGE_W - 2 * MARGIN, max_val=10.0),
        Spacer(1, 0.3 * cm),
        t2,
    ]))

    porter_img = _chart_image(charts_dir, "porter_forces_bar.png")
    if porter_img:
        story.append(Spacer(1, 0.3 * cm))
        story.append(porter_img)

    # Industry Lifecycle — plain flowable so it flows with the content that follows
    # (market data), ensuring it is never orphaned on a mostly-empty page.
    lc = ext.get("industry_lifecycle", {})
    story.append(Spacer(1, 0.3 * cm))
    story.append(KeepTogether([
        Paragraph("Industry Lifecycle", styles["subsection"]),
        Paragraph(
            f"<b>{lc.get('stage', '').upper()}</b> — {lc.get('strategic_implication', '')}",
            styles["body"]),
    ]))

    # Market Data — merged as subsection after PESTEL / Porter's / Lifecycle
    md_content = _build_market_data_content(data, styles)
    if md_content:
        story.append(Spacer(1, 0.4 * cm))
        story.extend(md_content)

    story.append(PageBreak())
    return story


def _build_market_data_content(data, styles):
    """Market data flowables — no SectionHeader or PageBreak; embedded as subsection."""
    md = data.get("market_data")
    if not md:
        return []
    quality = md.get("data_quality", {}).get("overall", "None")
    if quality == "None":
        return []

    aw = PAGE_W - 2 * MARGIN
    story = [
        Paragraph("Market Data & Macro Indicators", styles["subsection"]),
        Paragraph(
            f"Source: Yahoo Finance · Alpha Vantage · World Bank  |  Data Quality: {quality}",
            styles["small"],
        ),
        Spacer(1, 0.25 * cm),
    ]

    def _num(v, mult=1):
        try:
            return float(v) * mult
        except (TypeError, ValueError):
            return None

    def _fmt_money(v):
        if v is None:
            return "—"
        try:
            v = float(v)
        except (TypeError, ValueError):
            return "—"
        if abs(v) >= 1e12:
            return f"${v/1e12:.1f}T"
        if abs(v) >= 1e9:
            return f"${v/1e9:.1f}B"
        if abs(v) >= 1e6:
            return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"

    def _fmt_pct(v):
        if v is None:
            return "—"
        try:
            f = float(v)
            return f"{f*100:.1f}%" if abs(f) <= 1 else f"{f:.1f}%"
        except (TypeError, ValueError):
            return "—"

    def _fmt_num(v, decimals=2):
        if v is None:
            return "—"
        try:
            return f"{float(v):.{decimals}f}"
        except (TypeError, ValueError):
            return "—"

    yahoo_ok = md.get("data_quality", {}).get("yahoo_available", False)
    av_ok    = md.get("data_quality", {}).get("alpha_vantage_available", False)
    wb_ok    = md.get("data_quality", {}).get("world_bank_available", False)

    yahoo = md.get("yahoo", {}) or {}
    av    = md.get("alpha_vantage", {}) or {}
    wb    = md.get("world_bank", {}) or {}

    # ── Company Financials strip ──────────────────────────────────────────────
    if yahoo_ok or av_ok:
        story.append(Paragraph("Company Financials", styles["subsection"]))

        mc_raw    = yahoo.get("market_cap") or av.get("market_capitalization")
        pe_raw    = yahoo.get("pe_ratio") or av.get("pe_ratio")
        rev_raw   = yahoo.get("revenue_ttm") or av.get("revenue_ttm")
        ni_raw    = yahoo.get("net_income_ttm")
        eps_raw   = av.get("eps")
        roe_raw   = av.get("return_on_equity_ttm")
        gm_raw    = yahoo.get("gross_margin")
        beta_raw  = yahoo.get("beta")

        mc_v   = _fmt_money(mc_raw)
        pe_v   = _fmt_num(pe_raw, 1)
        rev_v  = _fmt_money(rev_raw)
        ni_v   = _fmt_money(ni_raw)
        eps_v  = _fmt_num(eps_raw, 2)
        roe_v  = _fmt_pct(roe_raw)
        gm_v   = _fmt_pct(gm_raw)
        beta_v = _fmt_num(beta_raw, 2)

        def _kpi_color(label, val_str):
            if val_str == "—":
                return NAVY
            if label in ("Market Cap", "Revenue TTM", "Net Income TTM", "EPS", "Gross Margin", "ROE"):
                return GREEN
            if label == "Beta":
                try:
                    b = float(val_str)
                    return AMBER if b > 1.5 else NAVY
                except ValueError:
                    return NAVY
            return NAVY

        headers = ["Market Cap", "P/E Ratio", "Revenue TTM", "Net Income TTM",
                   "EPS", "ROE", "Gross Margin", "Beta"]
        values  = [mc_v, pe_v, rev_v, ni_v, eps_v, roe_v, gm_v, beta_v]
        colors_list = [_kpi_color(h, v) for h, v in zip(headers, values)]

        hdr_cells = [Paragraph(h, styles["kpi_head"]) for h in headers]
        val_cells = [Paragraph(v, _kpi_val_style(c)) for v, c in zip(values, colors_list)]
        kpi_ts = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
            ("LINEBELOW",     (0, 0), (-1, 0), 1.5, GOLD),
            ("BACKGROUND",    (0, 1), (-1, 1), BLUEGRAY),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
            ("BOX",           (0, 0), (-1, -1), 0.75, MGRAY),
            ("LINEBELOW",     (0, -1), (-1, -1), 1.5, DGRAY),
            ("LINEAFTER",     (-1, 0), (-1, -1), 1.5, DGRAY),
        ])
        kpi_tbl = Table([hdr_cells, val_cells], colWidths=[aw / 8] * 8)
        kpi_tbl.setStyle(kpi_ts)
        story.append(kpi_tbl)
        story.append(Spacer(1, 0.4 * cm))

    # ── Macro Environment strip ───────────────────────────────────────────────
    if wb_ok:
        country_code = md.get("country_code", "")
        wb_year      = wb.get("data_year", "N/A")
        story.append(Paragraph(
            f"Macro Environment (World Bank — {country_code} {wb_year})",
            styles["subsection"],
        ))

        gdp_g  = wb.get("gdp_growth_pct")
        infl   = wb.get("inflation_pct")
        unemp  = wb.get("unemployment_pct")
        gdp_pc = wb.get("gdp_per_capita_usd")
        debt   = wb.get("govt_debt_pct_gdp")
        fdi    = wb.get("fdi_pct_gdp")

        def _wb_pct(v):
            if v is None:
                return "—"
            try:
                return f"{float(v):.1f}%"
            except (TypeError, ValueError):
                return "—"

        def _gdp_color(v):
            if v is None:
                return NAVY
            try:
                f = float(v)
                return GREEN if f > 2 else RED if f < 0 else AMBER
            except (TypeError, ValueError):
                return NAVY

        def _infl_color(v):
            if v is None:
                return NAVY
            try:
                f = float(v)
                return RED if f > 5 else GREEN if f < 3 else AMBER
            except (TypeError, ValueError):
                return NAVY

        wb_headers = ["GDP Growth %", "Inflation %", "Unemployment %",
                      "GDP per Capita", "Govt Debt % GDP", "FDI % GDP"]
        wb_values  = [_wb_pct(gdp_g), _wb_pct(infl), _wb_pct(unemp),
                      _fmt_money(gdp_pc), _wb_pct(debt), _wb_pct(fdi)]
        wb_colors  = [
            _gdp_color(gdp_g), _infl_color(infl), NAVY,
            NAVY, NAVY, NAVY,
        ]

        wb_hdr_cells = [Paragraph(h, styles["kpi_head"]) for h in wb_headers]
        wb_val_cells = [Paragraph(v, _kpi_val_style(c)) for v, c in zip(wb_values, wb_colors)]
        wb_kpi_ts = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
            ("LINEBELOW",     (0, 0), (-1, 0), 1.5, GOLD),
            ("BACKGROUND",    (0, 1), (-1, 1), BLUEGRAY),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
            ("BOX",           (0, 0), (-1, -1), 0.75, MGRAY),
            ("LINEBELOW",     (0, -1), (-1, -1), 1.5, DGRAY),
            ("LINEAFTER",     (-1, 0), (-1, -1), 1.5, DGRAY),
        ])
        wb_tbl = Table([wb_hdr_cells, wb_val_cells], colWidths=[aw / 6] * 6)
        wb_tbl.setStyle(wb_kpi_ts)
        story.append(wb_tbl)
        story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "<i>Data sourced from Yahoo Finance, Alpha Vantage, and World Bank Open Data. "
        "Figures represent most recently available data. All financial figures in USD.</i>",
        styles["small"],
    ))
    return story


def build_internal(data, styles):
    internal = data.get("internal", {})
    story = [SectionHeader("Internal Audit",
                           score=internal.get("internal_strength_score")),
             Spacer(1, 0.3 * cm)]

    # VRIO table
    story.append(Paragraph("VRIO Resource Analysis", styles["subsection"]))
    vrio_color_map = {"SCA": SCA_COLOR, "TCA": TCA_COLOR, "CP": CP_COLOR, "CD": CD_COLOR}
    vrio_label = {"SCA": "Sustained CA", "TCA": "Temporary CA",
                  "CP": "Competitive Parity", "CD": "Competitive Disadvantage"}
    rows = [["Resource", "Valuable", "Rare", "Inimitable", "Organized", "Implication"]]
    for r in internal.get("vrio_resources", []):
        ci = r.get("competitive_implication", "CP")
        rows.append([
            Paragraph(r["resource"], styles["cell_label"]),
            Paragraph("✓" if r["valuable"] else "✗", styles["table_cell_c"]),
            Paragraph("✓" if r["rare"] else "✗", styles["table_cell_c"]),
            Paragraph("✓" if r["inimitable"] else "✗", styles["table_cell_c"]),
            Paragraph("✓" if r["organized"] else "✗", styles["table_cell_c"]),
            Paragraph(vrio_label.get(ci, ci), styles["table_cell_c"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    cw = [4.5*cm, 1.5*cm, 1.4*cm, 1.8*cm, 1.8*cm, aw-4.5*cm-1.5*cm-1.4*cm-1.8*cm-1.8*cm]
    t = Table(rows, colWidths=cw)
    ts = std_table_style()
    for i, r in enumerate(internal.get("vrio_resources", []), start=1):
        ci = r.get("competitive_implication", "CP")
        col = vrio_color_map.get(ci, DGRAY)
        ts.add("BACKGROUND", (5, i), (5, i), col)
        ts.add("TEXTCOLOR",  (5, i), (5, i), WHITE)
        ts.add("FONTNAME",   (5, i), (5, i), "Helvetica-Bold")
        for j in range(1, 5):
            val = [r["valuable"], r["rare"], r["inimitable"], r["organized"]][j-1]
            ts.add("TEXTCOLOR", (j, i), (j, i), GREEN if val else RED)
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

    # McKinsey 7S — kept together to prevent heading/table split across pages
    s7 = internal.get("mckinsey_7s", [])
    rows7 = [["Element", "Assessment", "Alignment Score"]]
    for el in s7:
        score = el.get("alignment_score", 0)
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        rows7.append([
            Paragraph(el['element'], styles["cell_label"]),
            Paragraph(el["assessment"], styles["table_cell"]),
            Paragraph(f"{bar}  {score:.0f}", ParagraphStyle(
                "mono", fontName="Courier", fontSize=7.5,
                textColor=NAVY, alignment=TA_LEFT)),
        ])
    t7 = Table(rows7, colWidths=[3.5*cm, aw-3.5*cm-4.5*cm, 4.5*cm], splitByRow=0)
    t7.setStyle(std_table_style())
    story.append(KeepTogether([
        Spacer(1, 0.5*cm),
        Paragraph("McKinsey 7S Framework", styles["subsection"]),
        t7,
    ]))
    story.append(PageBreak())
    return story


def build_position(data, styles):
    pos = data.get("position", {})
    story = [SectionHeader("Strategic Position",
                           score=pos.get("strategic_position_score")),
             Spacer(1, 0.3 * cm)]

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
    type_colors = {"SO": GREEN, "ST": NAVY, "WO": AMBER, "WT": RED}
    rows_t = [["Type", "Strategy", "Rationale"]]
    for t in tows:
        rows_t.append([
            Paragraph(t['type'], styles["cell_label_c"]),
            Paragraph(t["strategy"], styles["table_cell"]),
            Paragraph(t["rationale"], styles["table_cell"]),
        ])
    tt = Table(rows_t, colWidths=[1.2*cm, aw*0.42, aw-1.2*cm-aw*0.42])
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
    story = [SectionHeader("Competitive Dynamics",
                           score=comp.get("competitive_intensity_score")),
             Spacer(1, 0.3 * cm)]

    # Game Theory
    story.append(Paragraph("Game Theory Scenarios", styles["subsection"]))
    gt = comp.get("game_theory_scenarios", [])
    rows = [["Scenario", "Our Move", "Competitor Response",
             "Payoff Us", "Payoff Comp.", "Nash Eq.", "Recommended"]]
    for s in gt:
        rows.append([
            Paragraph(s.get("scenario", ""), styles["cell_label"]),
            Paragraph(s.get("our_move", ""), styles["table_cell"]),
            Paragraph(s.get("competitor_response", ""), styles["table_cell"]),
            Paragraph(str(s.get("payoff_us", "")), styles["table_cell_c"]),
            Paragraph(str(s.get("payoff_competitor", "")), styles["table_cell_c"]),
            Paragraph("Yes" if s.get("nash_equilibrium") else "No", styles["table_cell_c"]),
            Paragraph("✓" if s.get("recommended") else "", styles["table_cell_c"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[3.2*cm, 3*cm, 3*cm, 1.3*cm, 1.5*cm, 1.4*cm, aw-3.2*cm-3*cm-3*cm-1.3*cm-1.5*cm-1.4*cm])
    ts = std_table_style()
    for i, s in enumerate(gt, start=1):
        if s.get("recommended"):
            ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#E8F4EC"))
        if s.get("nash_equilibrium"):
            ts.add("FONTNAME", (5, i), (5, i), "Helvetica-Bold")
            ts.add("TEXTCOLOR", (5, i), (5, i), GREEN)
    t.setStyle(ts)
    story.append(t)

    # ERRC Grid
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Blue Ocean ERRC Grid", styles["subsection"]))
    errc = comp.get("errc_grid", [])
    action_colors = {"eliminate": RED, "reduce": CP_COLOR, "raise": GREEN, "create": NAVY}
    rows2 = [["Factor", "Action", "Rationale", "Impact"]]
    for e in errc:
        rows2.append([
            Paragraph(e.get("factor", ""), styles["cell_label"]),
            Paragraph(e.get("action", "").upper(), styles["table_cell_c"]),
            Paragraph(e.get("rationale", ""), styles["table_cell"]),
            Paragraph(str(e.get("impact", "")), styles["table_cell_c"]),
        ])
    t2 = Table(rows2, colWidths=[3.5*cm, 2*cm, aw-3.5*cm-2*cm-1.5*cm, 1.5*cm])
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
    story = [SectionHeader("Strategy Formulation",
                           score=form.get("formulation_confidence_score")),
             Spacer(1, 0.3 * cm)]

    # Generic strategy
    story.append(Paragraph("Generic Strategy Recommendation", styles["subsection"]))
    generic = form.get("generic_strategies", [{}])[0]
    rec = form.get("recommended_strategy", "").upper()
    logic = form.get("strategic_logic", "")
    conf = form.get("formulation_confidence_score", 0)

    aw = PAGE_W - 2 * MARGIN
    badge = ScoreBadge(conf, "Confidence", size=90)
    detail = [
        Paragraph(f"<b>Recommended Strategy:</b> {rec}", styles["body_bold"]),
        Spacer(1, 4),
        Paragraph(logic, styles["body"]),
        Spacer(1, 4),
        Paragraph(f"<b>Fit Score:</b> {generic.get('fit_score', '')}  |  "
                  f"<b>Risks:</b> {', '.join(generic.get('risks', []))}", styles["small"]),
    ]
    lt = Table([[badge, detail]],
               colWidths=[3.0*cm, aw - 3.0*cm])
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
    story = [SectionHeader("Risk & Scenarios", score=risk.get("risk_score")),
             Spacer(1, 0.3 * cm)]

    # STEEP scenarios
    story.append(Paragraph("STEEP Scenario Analysis", styles["subsection"]))
    steep = risk.get("steep_scenarios", [])
    scenario_names = [s["name"].upper() for s in steep]
    dimensions = ["social", "technological", "economic", "environmental", "political"]
    _sh = ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=8,
                         textColor=WHITE, alignment=TA_CENTER,
                         wordWrap='CJK', splitLongWords=False)
    def _scenario_cell(name, prob):
        return Paragraph(
            f'{name}<br/><font face="Helvetica" size="7" color="#DDDDDD">p={prob}</font>',
            _sh,
        )
    rows = [[Paragraph("Dimension", _sh)] + [
        _scenario_cell(
            n,
            next((s['probability'] for s in steep if s['name'] == n.lower()), ''),
        )
        for n in scenario_names
    ]]
    for dim in dimensions:
        row = [Paragraph(dim.capitalize(), styles["cell_label"])]
        for s in steep:
            row.append(Paragraph(s.get(dim, ""), styles["table_cell"]))
        rows.append(row)
    aw = PAGE_W - 2 * MARGIN
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
            Paragraph(str(i), styles["cell_label_c"]),
            Paragraph(r, styles["table_cell"]),
            Paragraph(m, styles["table_cell"]),
        ])
    t2 = Table(rows2, colWidths=[0.8*cm, aw*0.42, aw-0.8*cm-aw*0.42])
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
    story = [SectionHeader("Execution Roadmap",
                           score=exec_data.get("execution_readiness_score")),
             Spacer(1, 0.3 * cm)]

    # Balanced Scorecard
    story.append(Paragraph("Balanced Scorecard", styles["subsection"]))
    bsc = exec_data.get("balanced_scorecard", [])
    persp_colors = {
        "financial": NAVY,
        "customer":  GREEN,
        "internal":  CP_COLOR,
        "learning":  AMBER,
    }
    rows = [["Perspective", "Objective", "KPI", "Target", "Initiative"]]
    for b in bsc:
        p = b.get("perspective", "")
        rows.append([
            Paragraph(p.upper(), styles["cell_label_c"]),
            Paragraph(b.get("objective",""), styles["table_cell"]),
            Paragraph(b.get("kpi",""), styles["table_cell"]),
            Paragraph(b.get("target",""), styles["table_cell"]),
            Paragraph(b.get("initiative",""), styles["table_cell"]),
        ])
    aw = PAGE_W - 2 * MARGIN
    t = Table(rows, colWidths=[2.2*cm, aw*0.22, aw*0.20, aw*0.20, aw-2.2*cm-aw*0.22-aw*0.20-aw*0.20])
    ts = std_table_style()
    for i, b in enumerate(bsc, start=1):
        col = persp_colors.get(b.get("perspective",""), NAVY)
        ts.add("BACKGROUND", (0, i), (0, i), col)
        ts.add("TEXTCOLOR",  (0, i), (0, i), WHITE)
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
            Paragraph(o.get("objective",""), styles["cell_label"]),
            Paragraph(kr_text.replace("\n","<br/>"), styles["table_cell"]),
            Paragraph(o.get("timeframe",""), styles["table_cell_c"]),
            Paragraph(o.get("owner",""), styles["table_cell"]),
        ])
    t2 = Table(rows2, colWidths=[3.5*cm, aw*0.4, 2*cm, aw-3.5*cm-aw*0.4-2*cm])
    t2.setStyle(std_table_style())
    story.append(t2)

    story.append(Spacer(1, 0.2*cm))
    csf = exec_data.get("critical_success_factors", [])
    if csf:
        story.append(Paragraph(
            "<b>Critical Success Factors:</b> " + " | ".join(csf), styles["small"]))
    story.append(PageBreak())
    return story


def build_financial_viability(data, styles, charts_dir=None):
    fin = data.get("finance")
    if not fin:
        return []

    aw    = PAGE_W - 2 * MARGIN
    story = [SectionHeader("Financial Viability Analysis",
                           score=fin.get("financial_fit_score")),
             Spacer(1, 0.3 * cm)]

    def fmt_m(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return str(v)
        if abs(v) >= 1e9:
            return f"${v / 1e9:.2f}B"
        if abs(v) >= 1e6:
            return f"${v / 1e6:.1f}M"
        return f"${v:,.0f}"

    def kpi_strip(headers, values, value_colors=None, arrows=None):
        """Navy-header / tinted-value metrics strip, full page width."""
        n = len(headers)
        value_colors = value_colors or [NAVY] * n
        arrows = arrows or [None] * n
        hdr_cells = [Paragraph(h, styles["kpi_head"]) for h in headers]
        val_cells = []
        for i, v in enumerate(values):
            prefix = ""
            if arrows[i] == "up":
                prefix = f'<font face="{ARROW_FONT}" color="#1A7A4A">{UP_ARROW}</font> '
            elif arrows[i] == "down":
                prefix = f'<font face="{ARROW_FONT}" color="#B22222">{DOWN_ARROW}</font> '
            val_cells.append(Paragraph(f"{prefix}{v}", _kpi_val_style(value_colors[i])))
        ts = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
            ("LINEBELOW",     (0, 0), (-1, 0), 1.5, GOLD),
            ("BACKGROUND",    (0, 1), (-1, 1), BLUEGRAY),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
            ("BOX",           (0, 0), (-1, -1), 0.75, MGRAY),
            ("LINEBELOW",     (0, -1), (-1, -1), 1.5, DGRAY),
            ("LINEAFTER",     (-1, 0), (-1, -1), 1.5, DGRAY),
        ])
        tbl = Table([hdr_cells, val_cells], colWidths=[aw / n] * n)
        tbl.setStyle(ts)
        return tbl

    # ── Row 1: DCF metrics ────────────────────────────────────────────────────
    dcf = fin.get("dcf", {})
    npv = dcf.get("npv", 0)
    irr = float(dcf.get("irr", 0) or 0)
    wacc = float(dcf.get("wacc", 0) or 0)
    story.append(KeepTogether([
        Paragraph("Discounted Cash Flow", styles["subsection"]),
        kpi_strip(
            ["NPV", "IRR", "Payback Period", "WACC", "Enterprise Value"],
            [
                fmt_m(npv),
                f"{irr:.1f}%",
                f"{dcf.get('payback_period_years', 0):.1f} yrs",
                f"{wacc:.1f}%",
                fmt_m(dcf.get("enterprise_value", 0)),
            ],
            value_colors=[
                GREEN if float(npv or 0) >= 0 else RED,
                GREEN if irr >= wacc else RED,
                NAVY, NAVY, NAVY,
            ],
            arrows=[
                "up" if float(npv or 0) >= 0 else "down",
                "up" if irr >= wacc else "down",
                None, None, None,
            ],
        ),
    ]))
    story.append(Spacer(1, 0.35 * cm))
    fcf_img = _chart_image(charts_dir, "fcf_cumulative.png")
    if fcf_img:
        story.append(fcf_img)
        story.append(Spacer(1, 0.2 * cm))

    # ── Row 2: Unit Economics or Banking Metrics ──────────────────────────────
    burn = fin.get("burn", {})
    bm   = fin.get("banking_metrics")
    if bm:
        nim = float(bm.get("nim_pct", 0) or 0)
        roa = float(bm.get("roa_pct", 0) or 0)
        roe = float(bm.get("roe_pct", 0) or 0)
        npl = float(bm.get("npl_ratio_pct", 0) or 0)
        car = float(bm.get("car_pct", 0) or 0)
        cti = float(bm.get("cost_to_income_pct", 0) or 0)
        story.append(KeepTogether([
            Paragraph("Banking Metrics", styles["subsection"]),
            kpi_strip(
                ["NIM %", "ROA %", "ROE %", "NPL Ratio %", "CAR %", "Cost / Income %"],
                [f"{nim:.2f}%", f"{roa:.2f}%", f"{roe:.1f}%",
                 f"{npl:.1f}%", f"{car:.1f}%", f"{cti:.1f}%"],
                value_colors=[
                    GREEN if nim >= 3.0 else AMBER if nim >= 2.0 else RED,
                    GREEN if roa >= 1.0 else AMBER if roa >= 0.5 else RED,
                    GREEN if roe >= 12.0 else AMBER if roe >= 8.0 else RED,
                    GREEN if npl <= 2.0 else AMBER if npl <= 5.0 else RED,
                    GREEN if car >= 12.0 else AMBER if car >= 8.0 else RED,
                    GREEN if cti <= 50.0 else AMBER if cti <= 65.0 else RED,
                ],
                arrows=[
                    "up" if nim >= 3.0 else "down",
                    "up" if roa >= 1.0 else "down",
                    "up" if roe >= 12.0 else "down",
                    "up" if npl <= 2.0 else "down",   # lower NPL is better
                    "up" if car >= 12.0 else "down",
                    "up" if cti <= 50.0 else "down",  # lower cost/income is better
                ],
            ),
        ]))
    else:
        ue      = burn.get("unit_economics", {})
        ltv_cac = float(ue.get("ltv_cac_ratio", 0) or 0)
        runway  = burn.get("runway_months", 0)
        ltv_cac_color = GREEN if ltv_cac >= 3.0 else AMBER if ltv_cac >= 1.5 else RED
        runway_color  = GREEN if float(runway or 0) >= 18 else AMBER if float(runway or 0) >= 9 else RED
        story.append(KeepTogether([
            Paragraph("Unit Economics", styles["subsection"]),
            kpi_strip(
                ["LTV", "CAC", "LTV / CAC Ratio", "Gross Margin %", "Runway (months)"],
                [
                    fmt_m(ue.get("ltv", 0)),
                    f"${ue.get('cac', 0):,.0f}",
                    f"{ltv_cac:.1f}x",
                    f"{ue.get('gross_margin_pct', 0):.1f}%",
                    f"{runway:.0f}",
                ],
                value_colors=[NAVY, RED, ltv_cac_color, GREEN, runway_color],
                arrows=[None, None, "up" if ltv_cac >= 3.0 else "down", None,
                        "up" if float(runway or 0) >= 18 else "down"],
            ),
        ]))
    story.append(Spacer(1, 0.35 * cm))

    # ── Row 3: Cap Table & Funding Round ──────────────────────────────────────
    cap = fin.get("cap_table", {})
    rnd = cap.get("funding_round", {})
    story.append(KeepTogether([
        Paragraph("Cap Table & Funding Round", styles["subsection"]),
        kpi_strip(
            ["Funding Round", "Amount Raised", "Pre-Money Val.", "Post-Money Val.", "Founder Dilution"],
            [
                rnd.get("round_name", "—"),
                fmt_m(rnd.get("amount_raised", 0)),
                fmt_m(rnd.get("pre_money_valuation", 0)),
                fmt_m(rnd.get("post_money_valuation", 0)),
                f"{cap.get('founder_dilution_pct', 0):.1f}%",
            ],
            value_colors=[NAVY, GREEN, NAVY, NAVY, RED],
            arrows=[None, None, None, None, "down"],
        ),
    ]))
    story.append(Spacer(1, 0.35 * cm))

    # ── Valuation Range — three large number boxes ────────────────────────────
    val        = fin.get("valuation", {})
    val_low    = val.get("implied_valuation_low", 0)
    val_mid    = val.get("implied_valuation_mid", 0)
    val_high   = val.get("implied_valuation_high", 0)
    method     = val.get("valuation_method_used", "")
    commentary = val.get("valuation_commentary", "")

    val_tbl = Table(
        [["BEAR CASE", "BASE CASE", "BULL CASE"],
         [fmt_m(val_low), fmt_m(val_mid), fmt_m(val_high)]],
        colWidths=[aw / 3] * 3,
    )
    val_tbl.setStyle(TableStyle([
        # Label row — coloured bars
        ("BACKGROUND",    (0, 0), (0, 0), RED),
        ("BACKGROUND",    (1, 0), (1, 0), NAVY),
        ("BACKGROUND",    (2, 0), (2, 0), GREEN),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        # Number row — large colour-coded values
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 20),
        ("TEXTCOLOR",     (0, 1), (0, 1), RED),
        ("TEXTCOLOR",     (1, 1), (1, 1), NAVY),
        ("TEXTCOLOR",     (2, 1), (2, 1), GREEN),
        ("BACKGROUND",    (0, 1), (-1, 1), WHITE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 1), (-1, 1), 16),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 16),
        ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
        ("BOX",           (0, 0), (-1, -1), 0.75, MGRAY),
        ("INNERGRID",     (0, 1), (-1, 1), 2, WHITE),
        ("LINEBELOW",     (0, -1), (-1, -1), 1.5, DGRAY),
        ("LINEAFTER",     (-1, 0), (-1, -1), 1.5, DGRAY),
    ]))
    story.append(KeepTogether([
        Paragraph("Valuation Range", styles["subsection"]),
        val_tbl,
        Spacer(1, 0.15 * cm),
        Paragraph(f"<b>Method:</b> {method} — {commentary}", styles["small"]),
    ]))
    story.append(Spacer(1, 0.35 * cm))
    val_img = _chart_image(charts_dir, "valuation_comps.png")
    if val_img:
        story.append(val_img)
        story.append(Spacer(1, 0.2 * cm))

    # ── Go Signal banner + Financial Fit Score badge ──────────────────────────
    score  = fin.get("financial_fit_score", 0)
    go     = fin.get("go_signal", "")
    go_col = {
        "Go":             GREEN,
        "Conditional Go": AMBER,
        "No Go":          RED,
    }.get(go, NAVY)

    score_badge = ScoreBadge(score, "Financial Fit", size=120)

    go_banner = Table(
        [[Paragraph(go.upper(), ParagraphStyle(
            "fv_go", fontName="Helvetica-Bold", fontSize=20,
            textColor=WHITE, alignment=TA_CENTER, leading=24))]],
        colWidths=[aw - 150],
    )
    go_banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), go_col),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
        ("BOX",           (0, 0), (-1, -1), 1, GOLD),
    ]))

    signal_layout = Table(
        [[score_badge, go_banner]],
        colWidths=[150, aw - 150],
    )
    signal_layout.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether([
        Paragraph("Go Signal & Financial Fit Score", styles["subsection"]),
        signal_layout,
    ]))
    story.append(Spacer(1, 0.35 * cm))

    # ── CFO Summary ───────────────────────────────────────────────────────────
    cfo = fin.get("cfo_summary", "")
    story.append(KeepTogether([
        Paragraph("CFO Summary", styles["subsection"]),
        Paragraph(f"<i>{cfo}</i>", styles["narrative"]),
    ]))
    wf_img = _chart_image(charts_dir, "dcf_waterfall.png")
    if wf_img:
        story.append(Spacer(1, 0.2 * cm))
        story.append(wf_img)

    # ── Data Provenance Footnote ──────────────────────────────────────────────
    dq = data.get("_data_quality", {}).get("summary", {})
    if dq:
        v  = dq.get("verified_count", 0)
        e  = dq.get("estimated_count", 0)
        n  = dq.get("total_fields", 0)
        story.append(HRFlowable(width="100%", thickness=0.5, color=MGRAY,
                                spaceBefore=8, spaceAfter=3))
        story.append(Paragraph(
            f"<b>Data provenance ({n} key figures):</b> "
            f'<font color="#1A7A4A"><b>{v} verified</b></font> '
            f"(market data feeds or deterministic computation) · "
            f'<font color="#B22222"><b>{e} AI estimates</b></font> '
            f"(LLM assumptions — no external data backing)",
            styles["small"],
        ))

    story.append(PageBreak())
    return story


def build_ethics_page(data, styles):
    ethics = data.get("ethics")
    if not ethics:
        return []

    aw = PAGE_W - 2 * MARGIN
    story = [SectionHeader("Ethics & ESG Analysis", score=ethics.get("ethics_score")),
             Spacer(1, 0.3 * cm)]

    # ── KPI strip ─────────────────────────────────────────────────────────────
    frameworks_list = ethics.get("ethical_frameworks", [])
    verdicts = [f.get("verdict", "") for f in frameworks_list]
    supports_count = verdicts.count("Supports")
    neutral_count  = verdicts.count("Neutral")
    opposes_count  = verdicts.count("Opposes")
    fw_parts = []
    if supports_count:
        fw_parts.append(f"{supports_count} Support")
    if neutral_count:
        fw_parts.append(f"{neutral_count} Neutral")
    if opposes_count:
        fw_parts.append(f"{opposes_count} Oppose")
    framework_summary = ", ".join(fw_parts) or "—"

    ethical_risk   = ethics.get("overall_ethical_risk", "")
    composite      = float(ethics.get("composite_esg_score", 0) or 0)
    ethics_score   = int(ethics.get("ethics_score", 0) or 0)

    risk_col      = RED if ethical_risk == "High" else AMBER if ethical_risk == "Medium" else GREEN
    composite_col = GREEN if composite >= 7 else AMBER if composite >= 4 else RED
    score_col     = GREEN if ethics_score >= 70 else AMBER if ethics_score >= 40 else RED
    fw_col        = GREEN if supports_count >= 2 else AMBER if supports_count >= 1 else RED

    hdr_cells = [Paragraph(h, styles["kpi_head"]) for h in
                 ["Ethics Score", "ESG Composite", "Overall Ethical Risk", "Framework Verdicts"]]
    val_cells = [
        Paragraph(f"{ethics_score} / 100",   _kpi_val_style(score_col)),
        Paragraph(f"{composite:.1f} / 10",   _kpi_val_style(composite_col)),
        Paragraph(ethical_risk,               _kpi_val_style(risk_col)),
        Paragraph(framework_summary,          _kpi_val_style(fw_col)),
    ]
    kpi_ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, GOLD),
        ("BACKGROUND",    (0, 1), (-1, 1), BLUEGRAY),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
        ("BOX",           (0, 0), (-1, -1), 0.75, MGRAY),
        ("LINEBELOW",     (0, -1), (-1, -1), 1.5, DGRAY),
        ("LINEAFTER",     (-1, 0), (-1, -1), 1.5, DGRAY),
    ])
    kpi_tbl = Table([hdr_cells, val_cells], colWidths=[aw / 4] * 4)
    kpi_tbl.setStyle(kpi_ts)
    story.append(kpi_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── ESG table ─────────────────────────────────────────────────────────────
    story.append(Paragraph("ESG Scoring", styles["subsection"]))
    esg_scores = ethics.get("esg_scores", [])
    rows_esg = [["Pillar", "Score", "Rationale", "Red Flags"]]
    for e in esg_scores:
        sv = float(e.get("score", 0) or 0)
        sc = GREEN if sv >= 7 else AMBER if sv >= 4 else RED
        flags = e.get("red_flags", [])
        flags_text = "<br/>".join([f"• {f}" for f in flags]) if flags else "None"
        rows_esg.append([
            Paragraph(e.get("pillar", ""), styles["cell_label"]),
            Paragraph(f"{sv:.1f}", _kpi_val_style(sc)),
            Paragraph(e.get("rationale", ""), styles["table_cell"]),
            Paragraph(flags_text, styles["table_cell"]),
        ])
    t_esg = Table(rows_esg, colWidths=[2.5*cm, 1.5*cm, aw * 0.42, aw - 2.5*cm - 1.5*cm - aw * 0.42])
    ts_esg = std_table_style()
    for i, e in enumerate(esg_scores, start=1):
        sv = float(e.get("score", 0) or 0)
        sc = GREEN if sv >= 7 else AMBER if sv >= 4 else RED
        ts_esg.add("TEXTCOLOR", (1, i), (1, i), sc)
        ts_esg.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
        ts_esg.add("ALIGN",     (1, i), (1, i), "CENTER")
    t_esg.setStyle(ts_esg)
    story.append(t_esg)
    story.append(Spacer(1, 0.4 * cm))

    # ── Stakeholder Impact table ───────────────────────────────────────────────
    story.append(Paragraph("Stakeholder Impact Analysis", styles["subsection"]))
    impacts = ethics.get("stakeholder_impacts", [])
    impact_colors   = {"Positive": GREEN, "Negative": RED, "Mixed": AMBER, "Neutral": DGRAY}
    severity_colors = {"High": RED, "Medium": AMBER, "Low": GREEN}
    rows_imp = [["Stakeholder", "Impact Type", "Severity", "Description"]]
    for imp in impacts:
        rows_imp.append([
            Paragraph(imp.get("stakeholder", ""), styles["cell_label"]),
            Paragraph(imp.get("impact_type", "").upper(), styles["table_cell_c"]),
            Paragraph(imp.get("severity", "").upper(), styles["table_cell_c"]),
            Paragraph(imp.get("description", ""), styles["table_cell"]),
        ])
    t_imp = Table(rows_imp, colWidths=[3*cm, 2.5*cm, 2*cm, aw - 3*cm - 2.5*cm - 2*cm])
    ts_imp = std_table_style()
    for i, imp in enumerate(impacts, start=1):
        ic = impact_colors.get(imp.get("impact_type", ""), DGRAY)
        sc = severity_colors.get(imp.get("severity", ""), DGRAY)
        ts_imp.add("TEXTCOLOR", (1, i), (1, i), ic)
        ts_imp.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
        ts_imp.add("TEXTCOLOR", (2, i), (2, i), sc)
        ts_imp.add("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")
    t_imp.setStyle(ts_imp)
    story.append(t_imp)
    story.append(Spacer(1, 0.4 * cm))

    # ── Ethical Frameworks table ───────────────────────────────────────────────
    story.append(Paragraph("Ethical Framework Assessment", styles["subsection"]))
    verdict_colors = {"Supports": GREEN, "Neutral": AMBER, "Opposes": RED}
    rows_fw = [["Framework", "Verdict", "Reasoning"]]
    for fw in frameworks_list:
        rows_fw.append([
            Paragraph(fw.get("framework", ""), styles["cell_label"]),
            Paragraph(fw.get("verdict", "").upper(), styles["table_cell_c"]),
            Paragraph(fw.get("reasoning", ""), styles["table_cell"]),
        ])
    t_fw = Table(rows_fw, colWidths=[3.5*cm, 2.5*cm, aw - 3.5*cm - 2.5*cm])
    ts_fw = std_table_style()
    for i, fw in enumerate(frameworks_list, start=1):
        vc = verdict_colors.get(fw.get("verdict", ""), DGRAY)
        ts_fw.add("BACKGROUND", (1, i), (1, i), vc)
        ts_fw.add("TEXTCOLOR",  (1, i), (1, i), WHITE)
        ts_fw.add("FONTNAME",   (1, i), (1, i), "Helvetica-Bold")
    t_fw.setStyle(ts_fw)
    story.append(t_fw)
    story.append(Spacer(1, 0.4 * cm))

    # ── Ethical Red Flags & Recommended Safeguards — side-by-side ─────────────
    red_flags  = ethics.get("ethical_red_flags", [])
    safeguards = ethics.get("recommended_safeguards", [])

    def _bulleted_items(items, accent_color, bg_color, col_w):
        result = []
        for item in items:
            row_tbl = Table(
                [[Paragraph(f"• {item}", styles["table_cell"])]],
                colWidths=[col_w],
            )
            row_tbl.setStyle(TableStyle([
                ("LINEBEFORE",    (0, 0), (0, -1), 3, accent_color),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS",(0, 0), (-1, -1), [bg_color]),
            ]))
            result.append(row_tbl)
            result.append(Spacer(1, 0.1 * cm))
        return result or [Paragraph("None identified.", styles["small"])]

    col_w = aw / 2 - 0.4 * cm
    rf_col = [Paragraph("Ethical Red Flags",      styles["subsection"])] + \
             _bulleted_items(red_flags,  RED,   colors.HexColor("#FEF0F0"), col_w)
    sg_col = [Paragraph("Recommended Safeguards", styles["subsection"])] + \
             _bulleted_items(safeguards, GREEN, colors.HexColor("#E8F4EC"), col_w)

    two_col = Table([[rf_col, sg_col]], colWidths=[aw / 2, aw / 2])
    two_col.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (0, 0),   0),
        ("RIGHTPADDING",  (0, 0), (0, 0),   8),
        ("LEFTPADDING",   (1, 0), (1, 0),   8),
        ("RIGHTPADDING",  (1, 0), (1, 0),   0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(two_col)
    story.append(PageBreak())
    return story


def build_options_ranking(data, styles, charts_dir=None):
    syn = data.get("synthesis", {})
    story = [SectionHeader("Strategic Options Ranking"), Spacer(1, 0.3 * cm)]

    options = syn.get("strategic_options", [])
    aw = PAGE_W - 2 * MARGIN

    rows = [["Rank", "Option", "Strategic Fit", "Risk", "Feasibility", "Overall Score", "Supporting Frameworks"]]
    for i, opt in enumerate(sorted(options, key=lambda x: -x.get("overall_score", 0)), start=1):
        score = opt.get("overall_score", 0)
        frameworks = ", ".join(opt.get("supporting_frameworks", []))
        rows.append([
            Paragraph(f"#{i}", styles["cell_label_c"]),
            Paragraph(f"<b>{opt.get('option','')}</b>", styles["table_cell"]),
            Paragraph(str(opt.get("strategic_fit_score","")), styles["table_cell_c"]),
            Paragraph(str(opt.get("risk_score","")), styles["table_cell_c"]),
            Paragraph(str(opt.get("feasibility_score","")), styles["table_cell_c"]),
            make_score_bar(score, width=88, height=10),
            Paragraph(frameworks, styles["small"]),
        ])
    t = Table(rows, colWidths=[1*cm, 3.5*cm, 1.8*cm, 1.3*cm, 1.8*cm, 3.5*cm, aw-1*cm-3.5*cm-1.8*cm-1.3*cm-1.8*cm-3.5*cm])
    ts = std_table_style()
    for i, opt in enumerate(sorted(options, key=lambda x: -x.get("overall_score", 0)), start=1):
        if i == 1:
            ts.add("BACKGROUND", (1, i), (-1, i), colors.HexColor("#E8F4EC"))
            ts.add("FONTNAME",   (1, i), (-1, i), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)

    options_img = _chart_image(charts_dir, "strategic_options_bar.png")
    if options_img:
        story.append(Spacer(1, 0.3 * cm))
        story.append(options_img)

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
    paras = [p.strip() for p in narrative.split(". ") if p.strip()]
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
            Paragraph(b.get("scenario","").upper(), styles["cell_label_c"]),
            Paragraph(b.get("recommended_option",""), styles["table_cell"]),
            Paragraph(b.get("expected_outcome",""), styles["table_cell"]),
            Paragraph(" | ".join(b.get("key_assumptions",[])), styles["small"]),
        ])
    t = Table(rows, colWidths=[2*cm, 3.5*cm, aw*0.35, aw-2*cm-3.5*cm-aw*0.35])
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

    ext    = data.get("external", {})
    internal = data.get("internal", {})
    pos    = data.get("position", {})
    comp   = data.get("competitive", {})
    form   = data.get("formulation", {})
    risk   = data.get("risk", {})
    exec_d = data.get("execution", {})
    fin    = data.get("finance") or {}
    syn    = data.get("synthesis", {})

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
        ("Financial Analysis",    f"{fin.get('financial_fit_score','')} / 100",
         "Financial viability"),
    ]
    if data.get("ethics"):
        ethics_d = data["ethics"]
        score_rows.insert(
            score_rows.index(next(r for r in score_rows if r[0] == "Execution Readiness")),
            ("Ethics Assessment", f"{ethics_d.get('ethics_score', '')} / 100",
             "Ethical & ESG scoring"),
        )
    score_rows += [
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
    t = Table(rows, colWidths=[5*cm, 3*cm, aw-5*cm-3*cm])
    ts = std_table_style(first_col=False)
    ts.add("BACKGROUND", (0, len(score_rows)), (-1, len(score_rows)), colors.HexColor("#E8EDF5"))
    ts.add("FONTNAME",   (0, len(score_rows)), (-1, len(score_rows)), "Helvetica-Bold")
    t.setStyle(ts)
    story.append(t)

    # Porter scores — kept together
    forces = ext.get("porter_forces", [])
    rows2 = [["Force", "Score / 10", "Intensity"]]
    for f in forces:
        rows2.append([
            Paragraph(f["force"], styles["cell_label"]),
            Paragraph(str(f["score"]), styles["table_cell_c"]),
            Paragraph(f["intensity"].upper(), styles["table_cell_c"]),
        ])
    t2 = Table(rows2, colWidths=[6*cm, 2.5*cm, aw-6*cm-2.5*cm], splitByRow=0)
    t2.setStyle(std_table_style())
    story.append(KeepTogether([
        Spacer(1, 0.4*cm),
        Paragraph("Porter's Five Forces — Detailed Scores", styles["subsection"]),
        t2,
    ]))

    # McKinsey 7S scores
    s7 = internal.get("mckinsey_7s", [])
    rows3 = [["Element", "Alignment Score", "Assessment"]]
    for el in s7:
        rows3.append([
            Paragraph(el["element"], styles["cell_label"]),
            Paragraph(str(el.get("alignment_score","")), styles["table_cell_c"]),
            Paragraph(el.get("assessment",""), styles["table_cell"]),
        ])
    t3 = Table(rows3, colWidths=[2.5*cm, 2.5*cm, aw-2.5*cm-2.5*cm], splitByRow=0)
    t3.setStyle(std_table_style())
    story.append(KeepTogether([
        Spacer(1, 0.4*cm),
        Paragraph("McKinsey 7S — Alignment Scores", styles["subsection"]),
        t3,
    ]))

    return story


# ── Main generator ────────────────────────────────────────────────────────────

class StrategyDocTemplate(BaseDocTemplate):
    """Doc template that tracks the current section for the page footer."""
    def afterFlowable(self, flowable):
        if isinstance(flowable, SectionHeader):
            self._section = flowable.text


def generate_report(json_path: str, output_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Generate Plotly charts before building the PDF
    charts_dir = None
    try:
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        from charts_generator import generate_all_charts
        generate_all_charts(json_path)
        charts_dir = os.path.join(os.path.dirname(os.path.abspath(json_path)), "charts")
    except Exception as _exc:
        print(f"Warning: chart generation skipped — {_exc}")

    styles = build_styles()

    # Page templates
    frame_normal = Frame(MARGIN, MARGIN + 1*cm, PAGE_W - 2*MARGIN,
                         PAGE_H - 2*MARGIN - 2.5*cm, id="normal")
    frame_cover  = Frame(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN,
                         leftPadding=0, rightPadding=0,
                         topPadding=0, bottomPadding=0, id="cover")

    def cover_tpl():
        return PageTemplate(id="Cover", frames=[frame_cover],
                            onPage=_cover_page)

    def normal_tpl():
        return PageTemplate(id="Normal", frames=[frame_normal],
                            onPageEnd=_header_footer)

    doc = StrategyDocTemplate(
        output_path,
        pagesize=A4,
        pageTemplates=[cover_tpl(), normal_tpl()],
        title=f"Strategic Report — {data.get('company','')}",
        author="AI Strategy Simulator",
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 1.8*cm, bottomMargin=MARGIN + 1*cm,
    )
    # Header/footer context
    doc._company = data.get("company", "")
    doc._date = datetime.now().strftime("%B %d, %Y")
    doc._section = ""

    story = []

    # 1. Cover (NextPageTemplate("Normal") is embedded at the end of build_cover)
    story += build_cover(data, styles)

    # 2. Table of Contents
    story += build_toc(data, styles)

    # 3. Executive Summary
    story += build_executive_summary(data, styles, charts_dir)

    # 4. External Environment (PESTEL · Porter's · Lifecycle · Market Data)
    story += build_external(data, styles, charts_dir)

    # 5. Internal Audit
    story += build_internal(data, styles)

    # 6. Strategic Position
    story += build_position(data, styles)

    # 7. Competitive Dynamics
    story += build_competitive(data, styles)

    # 8. Strategy Formulation
    story += build_formulation(data, styles)

    # 9. Risk & Scenarios
    story += build_risk(data, styles)

    # 10. Ethics & ESG Analysis
    story += build_ethics_page(data, styles)

    # 11. Execution Roadmap
    story += build_execution(data, styles)

    # 12. Financial Viability Analysis
    story += build_financial_viability(data, styles, charts_dir)

    # 13. Strategic Options Ranking
    story += build_options_ranking(data, styles, charts_dir)

    # 14. Board Narrative
    story += build_board_narrative(data, styles)

    # 15. Appendix
    story += build_appendix(data, styles)

    doc.build(story)
    print(f"Report saved: {output_path}")


# ── CLI entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    json_path   = os.path.join(base, "output.json")
    output_path = os.path.join(base, "strategy_report.pdf")
    generate_report(json_path, output_path)
