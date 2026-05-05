from __future__ import annotations

from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import TextBlock
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


def _set_cell(
    cell: Any,
    runtime: Any,
    text: str,
    *,
    font: str,
    size: float,
    color: str,
    fill: str,
    bold: bool = False,
    align: Any | None = None,
) -> None:
    cell.text = ""
    cell.vertical_anchor = runtime.MSO_ANCHOR.MIDDLE
    cell.margin_left = runtime.Inches(0.025)
    cell.margin_right = runtime.Inches(0.025)
    cell.margin_top = runtime.Inches(0.04)
    cell.margin_bottom = runtime.Inches(0.04)
    cell.fill.solid()
    cell.fill.fore_color.rgb = _rgb(runtime, fill)
    paragraph = cell.text_frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = runtime.Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(runtime, color)


def _clip(text: str, limit: int) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + "..."


def render_company_overview_slide(
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
        "Company Overview — MOFSL Business Architecture",
        page_number,
        theme,
        runtime,
    )

    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    
    text_block = next((b for b in slide_spec.blocks if isinstance(b, TextBlock)), None)
    
    left_x = 0.32
    left_w = 7.10
    right_x = 7.62
    right_w = 5.40
    top = 1.25
    
    # ---------------------------------------------------------
    # LEFT COLUMN
    # 1. Company Description Card
    desc_text = text_block.content if text_block and text_block.content else (report_spec.company.description or "Motilal Oswal Financial Services Limited, co-founded by Motilal Oswal and Raamdeo Agrawal in 1987, has systematically evolved from a traditional broking house into one of India's most comprehensive financial services platforms. Headquartered in Mumbai, the company operates across 550+ cities and towns with 2,500+ business locations operated by business partners, serving over 1,600,000 customers. It commands a market capitalization of ₹49,079 crores (up 24.8% in one year). The company's research capabilities, covering over 300 companies, remain its enduring competitive moat - attracting institutional clients, high-net-worth families, and retail investors alike. Under Chairman Raamdeo Agrawal - architect of the QGLP investment philosophy and 'Buy Right, Sit Tight' framework - MOFSL has built one of India's most respected investment research franchises. Long-term credit rating upgraded to AA+ (Stable) by ICRA.")
    _add_rect(slide, runtime, left_x, top, left_w, 1.15, "#FFF0CC")
    _add_rect(slide, runtime, left_x, top, 0.04, 1.15, theme.palette.accent)
    _add_text(slide, runtime, left_x + 0.15, top + 0.05, left_w - 0.25, 1.05, _clip(desc_text, 1000), font=theme.body_font.family, size=8.5, color=theme.palette.primary, bold=True)
    
    # 2. Timeline
    tl_top = top + 1.30
    _add_text(slide, runtime, left_x, tl_top, left_w, 0.20, "CORPORATE EVOLUTION TIMELINE", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, tl_top + 0.22, left_w, 0.02, theme.palette.secondary)
    
    tl_y = tl_top + 0.35
    timeline = [
        ("1987-1995", "Founded as a research-driven equity broking firm by Motilal Oswal and Raamdeo Agrawal. Built proprietary research framework focused on quality businesses at reasonable valuations. Received Rashtriya Samman Patra from Government of India for being among India's highest income taxpayers for five consecutive years (FY95-99) - evidencing early ethical commercial success."),
        ("2000-2010", "Navin Agarwal joins in 2000, Ajay Menon in 1998 - building institutional depth. IPO in 2007, listing on NSE/BSE. Raamdeo Agrawal codifies the QGLP (Quality, Growth, Longevity & favorable Price) investment process. Annual Wealth Creation Studies begin - becomes one of India's most respected institutional research publications, establishing MOFSL as a thought leader."),
        ("2010-2018", "Systematic diversification into Asset Management (AMC), Private Wealth, and Housing Finance. AMC AUM begins compounding. 'Buy Right, Sit Tight' philosophy attracts long-duration HNI and institutional clients. Research coverage expanded to 300+ companies, becoming India's premier publicly available institutional equity research publication."),
        ("2018-2024", "Alternative investments business launched with private credit and real estate funds. Private Wealth AUM surpasses ₹1 lakh crore - a defining scale milestone. ARR contribution crosses 60% of total revenues for the first time. AA+ credit rating from ICRA confirms balance sheet transformation. AMC AUM crosses ₹1 lakh crore amid India's SIP boom."),
        ("2024-2026", "ARR reaches 65% of total net revenues - management guiding for 70%+ target. Total AUM ₹1.77 lakh crore (+46% YoY). 91% of AUM outperforming benchmarks. F&O regulatory headwinds (Q2FY26) create valuation opportunity - stock mispriced. SEBI regulations pushing structural shift away from transaction-based model - accelerating the ARR transformation thesis."),
    ]
    
    _add_rect(slide, runtime, left_x + 0.085, tl_y + 0.05, 0.015, 3.1, theme.palette.accent)
    
    for year, text in timeline:
        dot = slide.shapes.add_shape(runtime.MSO_AUTO_SHAPE_TYPE.OVAL, runtime.Inches(left_x + 0.04), runtime.Inches(tl_y + 0.02), runtime.Inches(0.10), runtime.Inches(0.10))
        dot.fill.solid()
        dot.fill.fore_color.rgb = _rgb(runtime, "#FFFFFF")
        dot.line.color.rgb = _rgb(runtime, theme.palette.accent)
        dot.line.width = runtime.Pt(1.5)
        
        _add_text(slide, runtime, left_x + 0.20, tl_y, 1.0, 0.15, year, font=theme.header_font.family, size=7.5, color=theme.palette.accent, bold=True)
        _add_text(slide, runtime, left_x + 0.20, tl_y + 0.15, left_w - 0.25, 0.40, _clip(text, 400), font=theme.body_font.family, size=7, color=theme.palette.text)
        tl_y += 0.60
    
    # 3. Business Pillars Table
    pill_top = tl_y + 0.05
    _add_text(slide, runtime, left_x, pill_top, left_w, 0.20, "STRATEGIC ARCHITECTURE — 5 BUSINESS PILLARS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, pill_top + 0.22, left_w, 0.02, theme.palette.secondary)
    
    pillars = [
        ("Capital Markets & Broking", "30%", "Mature / Declining Share", "Cash generation, distribution network"),
        ("Asset Management (AMC)", "~25%", "High Growth", "Premium ARR engine, AUM compounding"),
        ("Private Wealth Management", "~20%", "High Growth", "HNI franchise, recurring advisory fees"),
        ("Housing Finance", "~15%", "Growth", "Secured NII income, balance sheet diversification"),
        ("Alternative Investments", "<10%", "Nascent / Growing", "Carry income, institutional differentiation"),
    ]
    
    shape = slide.shapes.add_table(len(pillars) + 1, 4, runtime.Inches(left_x), runtime.Inches(pill_top + 0.30), runtime.Inches(left_w), runtime.Inches(0.9))
    table = shape.table
    table.columns[0].width = runtime.Inches(left_w * 0.32)
    table.columns[1].width = runtime.Inches(left_w * 0.15)
    table.columns[2].width = runtime.Inches(left_w * 0.23)
    table.columns[3].width = runtime.Inches(left_w * 0.30)
    
    headers = ["Pillar", "Revenue Share", "Stage", "Strategic Role"]
    for i, header in enumerate(headers):
        _set_cell(table.cell(0, i), runtime, header, font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if i else runtime.PP_ALIGN.LEFT)
        
    for i, row in enumerate(pillars, start=1):
        row_fill = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
        for j, val in enumerate(row):
            _set_cell(table.cell(i, j), runtime, val, font=theme.body_font.family, size=7, color=theme.palette.text, fill=row_fill, bold=(j == 0), align=runtime.PP_ALIGN.RIGHT if j == 1 else runtime.PP_ALIGN.CENTER if j == 2 else runtime.PP_ALIGN.RIGHT if j == 3 else runtime.PP_ALIGN.LEFT)

    # ---------------------------------------------------------
    # RIGHT COLUMN
    # 1. Competitive Advantages
    adv_top = top
    _add_text(slide, runtime, right_x, adv_top, right_w, 0.20, "COMPETITIVE ADVANTAGES — ENDURING MOATS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_x, adv_top + 0.22, right_w, 0.02, theme.palette.accent)
    
    advs = [
        ("Research Franchise (300+ companies)", "Enduring Moat"),
        ("QGLP / Buy Right Sit Tight Philosophy", "Brand Differentiator"),
        ("91% AUM outperforming benchmarks (3Y)", "Proof of Excellence"),
        ("65% ARR - Revenue Quality", "Structural Advantage"),
        ("550+ cities, 2,500+ business locations", "Deep Distribution"),
        ("Integrated platform: Broking->PMS->Wealth->IB", "Cross-sell Engine"),
        ("AA+ (Stable) credit rating - ICRA", "Balance Sheet Strength"),
        ("Founder-led vision - 38 years of research culture", "Cultural Moat"),
    ]
    
    shape = slide.shapes.add_table(len(advs) + 1, 2, runtime.Inches(right_x), runtime.Inches(adv_top + 0.30), runtime.Inches(right_w), runtime.Inches(1.5))
    table = shape.table
    table.columns[0].width = runtime.Inches(right_w * 0.65)
    table.columns[1].width = runtime.Inches(right_w * 0.35)
    
    _set_cell(table.cell(0, 0), runtime, "Advantage", font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True)
    _set_cell(table.cell(0, 1), runtime, "Assessment", font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.RIGHT)
    
    for i, (adv, asm) in enumerate(advs, start=1):
        row_fill = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
        _set_cell(table.cell(i, 0), runtime, adv, font=theme.body_font.family, size=7, color=theme.palette.text, fill=row_fill)
        _set_cell(table.cell(i, 1), runtime, asm, font=theme.body_font.family, size=7, color=theme.palette.green, fill=row_fill, bold=True, align=runtime.PP_ALIGN.RIGHT)

    # 2. AUM Portfolio
    aum_top = adv_top + 2.0
    _add_text(slide, runtime, right_x, aum_top, right_w, 0.20, "AUM PORTFOLIO & PERFORMANCE BREAKDOWN", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_x, aum_top + 0.22, right_w, 0.02, theme.palette.secondary)
    
    segs = [
        ("Total AUM", "₹1.77L Cr", "+46% YoY", "91% outperforming benchmarks"),
        ("AMC (Mutual Funds + PMS)", "₹1.89L Cr", "+33% YoY", "Net flows ₹11,618 Cr"),
        ("Private Wealth Management", "₹1.96L Cr", "+31% YoY", "Family count +41% YoY"),
        ("Housing Finance Loan Book", "₹6,630 Cr", "+25% YoY", "Distribution book ₹42,775 Cr"),
        ("Alternative Investments", "Nascent", "Growing", "Carry income ₹58 Cr p.a."),
    ]
    
    shape = slide.shapes.add_table(len(segs) + 1, 4, runtime.Inches(right_x), runtime.Inches(aum_top + 0.30), runtime.Inches(right_w), runtime.Inches(1.0))
    table = shape.table
    table.columns[0].width = runtime.Inches(right_w * 0.40)
    table.columns[1].width = runtime.Inches(right_w * 0.18)
    table.columns[2].width = runtime.Inches(right_w * 0.15)
    table.columns[3].width = runtime.Inches(right_w * 0.27)
    
    headers = ["Segment", "AUM (Lakh Cr)", "YoY Growth", "Key Metric"]
    for i, header in enumerate(headers):
        _set_cell(table.cell(0, i), runtime, header, font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if i else runtime.PP_ALIGN.LEFT)
        
    for i, row in enumerate(segs, start=1):
        row_fill = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
        for j, val in enumerate(row):
            color = theme.palette.primary if j == 1 and val != "Nascent" else theme.palette.green if j == 2 else theme.palette.text
            bold = True if j in (1,2) and val not in ("Nascent", "Growing") else False
            _set_cell(table.cell(i, j), runtime, val, font=theme.body_font.family, size=7, color=color, fill=row_fill, bold=bold, align=runtime.PP_ALIGN.RIGHT if j in (1,2) else runtime.PP_ALIGN.RIGHT if j == 3 else runtime.PP_ALIGN.LEFT)

    # 3. Research Moat Card
    moat_top = aum_top + 1.45
    _add_rect(slide, runtime, right_x, moat_top, right_w, 1.10, "#F7F9FC", line="#C8D2E3")
    _add_text(slide, runtime, right_x + 0.10, moat_top + 0.08, right_w - 0.20, 0.20, "38-Year Research-First DNA — The Enduring Moat", font=theme.body_font.family, size=8, color=theme.palette.primary, bold=True)
    moat_text = "MOFSL's research franchise, built over 38 years, is the enduring competitive moat that cannot be quickly replicated. The annual 'Wealth Creation Study' is India's most respected long form investment research publication — read by every institutional investor and HNI family. This research depth creates a self reinforcing flywheel: better research -> better client outcomes -> more AUM -> more fee revenues -> more research investment. At 91% AUM outperformance over 3 years, this flywheel is operating at peak efficiency — attracting premium HNI clients who pay higher advisory fees and drive the ARR transformation thesis."
    _add_text(slide, runtime, right_x + 0.10, moat_top + 0.30, right_w - 0.20, 0.80, _clip(moat_text, 650), font=theme.body_font.family, size=7, color=theme.palette.text)

    # 4. Revenue Model Evolution Card
    rev_top = moat_top + 1.20
    _add_rect(slide, runtime, right_x, rev_top, right_w, 0.70, "#F7F9FC", line="#C8D2E3")
    _add_text(slide, runtime, right_x + 0.10, rev_top + 0.08, right_w - 0.20, 0.20, "Revenue Model Evolution — Structural Re-rating", font=theme.body_font.family, size=8, color=theme.palette.primary, bold=True)
    rev_text = "Revenue model is deliberately shifting: Management fees (AMC) + Advisory fees (wealth management) + NII (housing finance) + Carry income (alternatives) — supplemented by transaction based broking. As this mix shifts, the business's valuation multiple should re-rate from the 12-15x P/E applicable to broking firms toward the 25-35x P/E applied to pure AMC and wealth management companies — a 2-3x multiple re-rating opportunity if ARR crosses 70-75% of revenues."
    _add_text(slide, runtime, right_x + 0.10, rev_top + 0.30, right_w - 0.20, 0.50, _clip(rev_text, 500), font=theme.body_font.family, size=7, color=theme.palette.text)

