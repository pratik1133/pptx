from __future__ import annotations

from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _rgb(runtime: Any, color: str) -> Any:
    return runtime.RGBColor.from_string(color.removeprefix("#"))


def _add_rect(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    fill: str,
    *,
    line: str | None = None,
    radius: bool = False,
) -> Any:
    shape_type = runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(runtime, fill)
    if line:
        shape.line.color.rgb = _rgb(runtime, line)
        shape.line.width = runtime.Pt(0.7)
    else:
        shape.line.fill.background()
    return shape


def _add_text(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    text: str,
    *,
    font: str,
    size: float,
    color: str,
    bold: bool = False,
    align: Any | None = None,
    valign: Any | None = None,
) -> Any:
    box = slide.shapes.add_textbox(
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    if valign:
        frame.vertical_anchor = valign
    frame.margin_left = runtime.Inches(0.04)
    frame.margin_right = runtime.Inches(0.04)
    frame.margin_top = runtime.Inches(0.01)
    frame.margin_bottom = runtime.Inches(0.01)
    paragraph = frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = runtime.Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(runtime, color)
    return box

def _add_rich_text(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    runs: list[tuple[str, str, float, str, bool]],
    *,
    align: Any | None = None,
    valign: Any | None = None,
) -> Any:
    box = slide.shapes.add_textbox(
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    if valign:
        frame.vertical_anchor = valign
    frame.margin_left = runtime.Inches(0.04)
    frame.margin_right = runtime.Inches(0.04)
    frame.margin_top = runtime.Inches(0.01)
    frame.margin_bottom = runtime.Inches(0.01)
    paragraph = frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    
    for text, font, size, color, bold in runs:
        run = paragraph.add_run()
        run.text = text
        run.font.name = font
        run.font.size = runtime.Pt(size)
        run.font.bold = bold
        run.font.color.rgb = _rgb(runtime, color)
    return box

def _add_risk_item(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    tag: str,
    title: str,
    description: str,
    theme: BrandTheme,
    height_estimate: float = 0.6
):
    if tag == "HIGH":
        tag_bg = "#FEE2E2"
        tag_fg = "#DC2626"
    elif tag == "MED":
        tag_bg = "#FEF3C7"
        tag_fg = "#D97706"
    else: # LOW
        tag_bg = "#DCFCE7"
        tag_fg = "#166534"
        
    tag_width = 0.45
    tag_height = 0.15
    tag_top = top + 0.03
    
    _add_rect(slide, runtime, left, tag_top, tag_width, tag_height, tag_bg, radius=True)
    _add_text(slide, runtime, left, tag_top, tag_width, tag_height, tag, font=theme.body_font.family, size=6.5, color=tag_fg, bold=True, align=runtime.PP_ALIGN.CENTER, valign=runtime.MSO_ANCHOR.MIDDLE)
    
    text_left = left + tag_width + 0.1
    text_width = width - tag_width - 0.1
    
    runs = [
        (title + " ", theme.header_font.family, 8.5, theme.palette.primary, True),
        (description, theme.body_font.family, 8.5, theme.palette.text, False)
    ]
    
    _add_rich_text(slide, runtime, text_left, top, text_width, height_estimate, runs)

def render_forensic_assessment_slide(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
    *,
    page_number: int,
) -> None:
    render_section_header(
        slide,
        Box(left=0.5, top=0.6, width=12.333, height=0.55),
        "Risk Register & Forensic Assessment — Governance Monitoring",
        page_number,
        theme,
        runtime,
    )

    left_col_x = 0.5
    right_col_x = 6.8
    col_width = 6.0
    top_y = 1.3

    # LEFT COLUMN: INVESTMENT RISKS
    _add_text(slide, runtime, left_col_x, top_y, col_width, 0.25, "INVESTMENT RISKS", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_col_x, top_y + 0.25, col_width, 0.015, theme.palette.secondary)
    
    y_offset = top_y + 0.35
    
    desc = "SEBI's repeated interventions on F&O trading norms compressing cyclical broking revenues — Q2FY26 brokerage revenue declined 24%. Primary risk to near-term earnings: if SEBI imposes further restrictions, broking revenues could decline an additional 15-25%. Monitoring trigger: track quarterly SEBI circulars on derivatives framework and F&O volume data."
    _add_risk_item(slide, runtime, left_col_x, y_offset, col_width, "HIGH", "SEBI Regulatory Headwinds on F&O", desc, theme, 0.7)
    y_offset += 0.8
    _add_rect(slide, runtime, left_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")

    desc = "A sharp equity market correction (Nifty -20%+ scenario) would compress AUM valuations and therefore management fee income. 46% YoY AUM growth is partly market appreciation — in a bear market, this reverses to AUM compression. H1FY26 operating PAT growth of 11% is partly protected by new flows, but an extended bear market reduces both valuations and new investment appetite simultaneously."
    _add_risk_item(slide, runtime, left_col_x, y_offset, col_width, "HIGH", "Market Volatility — AUM Valuation Risk", desc, theme, 0.7)
    y_offset += 0.95
    _add_rect(slide, runtime, left_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")

    desc = "Zerodha, Groww, and other discount fintech brokers continue to capture retail broking market share. MOFSL's differentiation in research and HNI advisory limits the impact in premium segments, but the mass-market broking business faces structural margin compression. Fintech startups grew from 733 (FY16-17) to 14,000+ (FY21-22) — competitive intensity is at an all-time high."
    _add_risk_item(slide, runtime, left_col_x, y_offset, col_width, "HIGH", "Fintech Disruption — Discount Broker Competition", desc, theme, 0.7)
    y_offset += 0.8
    _add_rect(slide, runtime, left_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")

    desc = "If ARR contribution drops below 55% for two consecutive quarters (currently 65%), the re-rating thesis is challenged. This could occur if regulatory headwinds become severe enough to compress fee income disproportionately, or if management makes an ill-timed acquisition that increases revenue volatility. Monitor ARR % every quarter against the 55% floor threshold."
    _add_risk_item(slide, runtime, left_col_x, y_offset, col_width, "MED", "ARR Trajectory Risk — Thesis-Breaking Condition", desc, theme, 0.7)
    y_offset += 0.8
    _add_rect(slide, runtime, left_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")

    desc = "91% of AUM outperforming benchmarks over 3 years is exceptional — but it creates a high baseline. Any meaningful performance reversion (especially in MOFSL's flagship multicap and emerging bluechip funds) would trigger client redemptions and hurt both AUM levels and the brand premium that justifies higher management fees."
    _add_risk_item(slide, runtime, left_col_x, y_offset, col_width, "MED", "AUM Performance Reversion Risk", desc, theme, 0.7)
    y_offset += 0.65
    _add_rect(slide, runtime, left_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")

    desc = "Raamdeo Agrawal's QGLP philosophy and research reputation are deeply embedded in the MOFSL brand and AUM outperformance. Any leadership transition risk (health, retirement) could create client confidence uncertainty, particularly for the QGLP-branded funds. Institutional process documentation and second-tier research leadership development would mitigate this long-term structural risk."
    _add_risk_item(slide, runtime, left_col_x, y_offset, col_width, "LOW", "Key Person Risk — Raamdeo Agrawal", desc, theme, 0.7)


    # RIGHT COLUMN: FORENSIC ASSESSMENT
    _add_text(slide, runtime, right_col_x, top_y, col_width, 0.25, "⚠ FORENSIC ASSESSMENT - MONITOR CLOSELY", font=theme.header_font.family, size=9, color="#DC2626", bold=True)
    _add_rect(slide, runtime, right_col_x, top_y + 0.25, col_width, 0.015, theme.palette.secondary)
    
    y_offset = top_y + 0.35
    
    box_h = 0.95
    _add_rect(slide, runtime, right_col_x, y_offset, col_width, box_h, "#F7F9FC", line="#DDE5F0")
    _add_rect(slide, runtime, right_col_x, y_offset, 0.04, box_h, "#E53E3E")
    
    runs = [
        ("Overall Forensic Verdict: Monitor Closely\n", theme.header_font.family, 9, theme.palette.primary, True),
        ("MOFSL faces recurring regulatory violations that are operational rather than fraudulent in nature. Despite SEBI's repeated interventions, these structural lapses suggest deeper governance issues within the risk management systems. The pattern warrants close monitoring but does not fundamentally impair the business model or thesis. We classify MOFSL in the \"Monitor Closely\" forensic category — not disqualifying, but requiring active quarterly tracking of compliance developments.", theme.body_font.family, 8.5, theme.palette.text, False)
    ]
    _add_rich_text(slide, runtime, right_col_x + 0.1, y_offset + 0.05, col_width - 0.2, box_h - 0.1, runs)
    
    y_offset += box_h + 0.15
    
    desc = "SEBI imposed ₹7 lakh penalty for multiple violations of securities laws stemming from margin reporting issues, collection violations, and other regulatory lapses discovered during an inspection. While small in monetary terms, the pattern suggests systemic compliance weaknesses in the back-office and reporting infrastructure. Severity: Low monetary, Medium reputational."
    _add_risk_item(slide, runtime, right_col_x, y_offset, col_width, "MED", "SEBI Penalty — Margin Reporting Violations (2021)", desc, theme, 0.7)
    y_offset += 0.8
    _add_rect(slide, runtime, right_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")
    
    desc = "In May 2022, SEBI penalized Motilal Oswal with ₹25 lakh fine for misutilization of client funds and inaccurate margin reporting. The combination of client fund misuse and reporting inaccuracies indicates gaps in internal controls and oversight — a more substantive governance concern than the 2021 margin reporting violation alone. Severity: Medium — second offense of financial reporting nature."
    _add_risk_item(slide, runtime, right_col_x, y_offset, col_width, "MED", "SEBI Penalty — Client Fund Misutilization (May 2022)", desc, theme, 0.7)
    y_offset += 0.85
    _add_rect(slide, runtime, right_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")
    
    desc = "SFIO and EOW-Mumbai found MOFSL guilty of misselling NSEL contracts, KYC manipulation, client code modification, and illegal transactions. SEBI declared MOFSL \"not fit and proper\" as commodity derivative broker in February 2019. While historical, the severity of these findings — including regulatory disqualification in a product category — demands ongoing monitoring. Severity: High (historical) — still affects regulatory relationship quality."
    _add_risk_item(slide, runtime, right_col_x, y_offset, col_width, "HIGH", "NSEL Case — Misselling & 'Not Fit & Proper' (Historical)", desc, theme, 0.8)
    y_offset += 0.85
    _add_rect(slide, runtime, right_col_x, y_offset - 0.05, col_width, 0.01, "#E2E8F0")

    desc = "SEBI concluded MOFSL failed to exercise sufficient control over APs with 13 NSE + 9 BSE terminals operating from locations not declared to the regulator, including an unreported branch in Delhi. This is an operational governance and reporting failure — suggesting the compliance infrastructure has not scaled commensurately with business growth. Severity: Medium — structural control weakness."
    _add_risk_item(slide, runtime, right_col_x, y_offset, col_width, "MED", "Unauthorized Terminal Operations", desc, theme, 0.7)
    y_offset += 0.7
    
    box2_h = 0.85
    _add_rect(slide, runtime, right_col_x, y_offset, col_width, box2_h, "#F7F9FC", line="#DDE5F0")
    _add_rect(slide, runtime, right_col_x, y_offset, 0.04, box2_h, theme.palette.secondary)
    
    runs = [
        ("Forensic Monitoring Triggers\n", theme.header_font.family, 9, theme.palette.primary, True),
        ("1. Any fresh SEBI enforcement actions or penalties (monitor every quarter) | 2. Client complaint escalation trends on SCORES portal | 3. Auditor commentary on internal controls in quarterly results | 4. Management's progress on compliance infrastructure investments | 5. Any investigation by SFIO, EOW, or other enforcement agencies expanding scope from historical NSEL case.", theme.body_font.family, 8.5, theme.palette.text, False)
    ]
    _add_rich_text(slide, runtime, right_col_x + 0.1, y_offset + 0.05, col_width - 0.2, box2_h - 0.1, runs)

