from __future__ import annotations

from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
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


def render_business_segments_slide(
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
        "Business Segments — Growth Drivers & Investment Thesis",
        page_number,
        theme,
        runtime,
    )

    left_x = 0.32
    left_w = 6.20
    right_x = 6.64
    right_w = 6.38
    top = 1.25

    # Helper to render a group of tags
    def _render_tags(x, y, tags, accent="#E37400"):
        cx = x
        cy = y
        for tag in tags:
            # estimate width: ~0.08 inch per character + padding
            w = len(tag) * 0.05 + 0.15
            if cx + w > (left_x + left_w if x < right_x else right_x + right_w):
                cx = x
                cy += 0.22
            _add_rect(slide, runtime, cx, cy, w, 0.18, "#FFFFFF", line=accent, radius=True)
            _add_text(slide, runtime, cx, cy + 0.015, w, 0.15, tag, font=theme.header_font.family, size=6, color=accent, bold=True, align=runtime.PP_ALIGN.CENTER)
            cx += w + 0.08
        return cy + 0.25

    # =========================================================
    # LEFT COLUMN
    # =========================================================
    
    # 1. AMC Card
    amc_h = 3.30
    _add_rect(slide, runtime, left_x, top, left_w, amc_h, "#FFFFFF", line="#C8D2E3")
    
    _add_text(slide, runtime, left_x + 0.10, top + 0.10, 3.0, 0.20, "Asset Management (AMC)", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    
    # Subtitle bar
    sub_w = 3.20
    _add_rect(slide, runtime, left_x + left_w - sub_w - 0.10, top + 0.10, sub_w, 0.20, theme.palette.primary, radius=True)
    _add_text(slide, runtime, left_x + left_w - sub_w - 0.10, top + 0.12, sub_w, 0.18, "AUM ₹1.89L Cr | +33% YoY | Fee-Based ARR Engine", font=theme.header_font.family, size=6.5, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
    
    amc_tags = ['₹1.89L Cr AUM', '+33% YoY Growth', '₹11,610 Cr Net Flows', '91% Outperforming Benchmarks', 'EBITDA Margin 57%+']
    tag_y = _render_tags(left_x + 0.10, top + 0.40, amc_tags)
    
    amc_text = "The AMC business is the crown jewel of MOFSL's transformation - a capital-light, fee-generating machine that requires minimal incremental investment as AUM grows, creating significant operating leverage. Revenue is generated through management fees (AUM × fee rate), creating a recurring income stream that grows automatically as the AUM compounds. The 91% benchmark outperformance over 3 years is the critical differentiator: it enables MOFSL to charge premium fees (1-2% AUM) versus discount managers (0.1-0.5%) and attract sticky, quality clients who rarely leave when performance persists. Net flows of ₹11,610 crore demonstrate the market's trust in MOFSL's investment process despite overall industry volatility. SIP culture expanding into Tier 2-3 cities is the secular tailwind driving systematic inflows."
    _add_text(slide, runtime, left_x + 0.10, tag_y + 0.05, left_w - 0.20, 1.20, _clip(amc_text, 1000), font=theme.body_font.family, size=7.5, color=theme.palette.text)
    
    # AMC Table
    amc_tbl_y = top + 2.45
    _add_text(slide, runtime, left_x + 0.10, amc_tbl_y - 0.20, left_w - 0.20, 0.20, "AMC — GROWTH ENGINE BREAKDOWN", font=theme.header_font.family, size=7.5, color=theme.palette.primary, bold=True)
    
    amc_rows = [
        ("AUM (Lakh Crore)", "₹1.89L Cr", "₹3.0L+ Cr", "Market appreciation + net flows"),
        ("Management Fee Income", "Growing", "+25% CAGR", "AUM compounding effect"),
        ("Benchmark Outperformance", "91%", "Maintain 85%+", "QGLP process discipline"),
        ("Net Inflows/Quarter", "₹11,610 Cr (H1)", "₹15,000 Cr+", "Tier 2/3 SIP expansion")
    ]
    
    shape = slide.shapes.add_table(len(amc_rows) + 1, 4, runtime.Inches(left_x + 0.10), runtime.Inches(amc_tbl_y), runtime.Inches(left_w - 0.20), runtime.Inches(0.70))
    table = shape.table
    table.columns[0].width = runtime.Inches((left_w - 0.20) * 0.35)
    table.columns[1].width = runtime.Inches((left_w - 0.20) * 0.15)
    table.columns[2].width = runtime.Inches((left_w - 0.20) * 0.15)
    table.columns[3].width = runtime.Inches((left_w - 0.20) * 0.35)
    
    amc_hds = ["Metric", "Current", "FY27E Target", "Growth Lever"]
    for i, header in enumerate(amc_hds):
        _set_cell(table.cell(0, i), runtime, header, font=theme.header_font.family, size=6.5, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if i else runtime.PP_ALIGN.LEFT)
        
    for i, row in enumerate(amc_rows, start=1):
        row_fill = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
        for j, val in enumerate(row):
            color = theme.palette.green if j == 2 and "+" in val else theme.palette.text if j == 3 else theme.palette.text
            bold = True if j in (1, 2) else False
            _set_cell(table.cell(i, j), runtime, val, font=theme.body_font.family, size=6.5, color=color, fill=row_fill, bold=bold, align=runtime.PP_ALIGN.RIGHT if j in (1, 2) else runtime.PP_ALIGN.RIGHT if j == 3 else runtime.PP_ALIGN.LEFT)

    # 2. Wealth Card
    wealth_top = top + amc_h + 0.15
    wealth_h = 2.45
    _add_rect(slide, runtime, left_x, wealth_top, left_w, wealth_h, "#FFFFFF", line="#C8D2E3")
    
    _add_text(slide, runtime, left_x + 0.10, wealth_top + 0.10, 3.0, 0.20, "Private Wealth Management", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    
    w_sub_w = 3.40
    _add_rect(slide, runtime, left_x + left_w - w_sub_w - 0.10, wealth_top + 0.10, w_sub_w, 0.20, theme.palette.primary, radius=True)
    _add_text(slide, runtime, left_x + left_w - w_sub_w - 0.10, wealth_top + 0.12, w_sub_w, 0.18, "AUM ₹1.96L Cr | +31% YoY | HNI/UHNI Premium Franchise", font=theme.header_font.family, size=6.5, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
    
    wealth_tags = ['₹1.96L Cr AUM', '+41% Family Count YoY', 'PAT +14% (9M)', 'Distribution Book ₹42,775 Cr', '+34% Distribution YoY']
    tag_y = _render_tags(left_x + 0.10, wealth_top + 0.40, wealth_tags)
    
    wealth_text = "Private Wealth Management targets HNI and UHNI families with tailored financial advisory and wealth solutions. This is the segment that will benefit most from India's wealth creation super-cycle: 8.56 lakh HNWIs in June 2025, growing to 16.57 lakh by 2027. MOFSL's competitive advantage here is its 38-year research reputation - HNI families trust MOFSL's QGLP process and 'Buy Right, Sit Tight' philosophy. Family count growing 41% YoY demonstrates that MOFSL's HNI advisor network is acquiring new clients at an accelerating pace. Advisory fees charged as a percentage of AUM create a pure ARR income stream with zero capital at risk and zero cycle sensitivity."
    _add_text(slide, runtime, left_x + 0.10, tag_y + 0.05, left_w - 0.20, 1.30, _clip(wealth_text, 1000), font=theme.body_font.family, size=7.5, color=theme.palette.text)

    # =========================================================
    # RIGHT COLUMN
    # =========================================================

    # 1. Capital Markets
    cm_h = 2.65
    _add_rect(slide, runtime, right_x, top, right_w, cm_h, "#FFFFFF", line="#C8D2E3")
    
    _add_text(slide, runtime, right_x + 0.10, top + 0.10, 3.0, 0.20, "Capital Markets & Broking", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    
    cm_sub_w = 3.20
    _add_rect(slide, runtime, right_x + right_w - cm_sub_w - 0.10, top + 0.10, cm_sub_w, 0.20, theme.palette.primary, radius=True)
    _add_text(slide, runtime, right_x + right_w - cm_sub_w - 0.10, top + 0.12, cm_sub_w, 0.18, "30% Revenue | Deliberate Decline | Distribution Network", font=theme.header_font.family, size=6.5, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
    
    cm_tags = ['30% of Revenues', 'Research: 300+ Companies', 'SEBI F&O Headwind', 'Brokerage -24% Q2FY26']
    tag_y = _render_tags(right_x + 0.10, top + 0.40, cm_tags)
    
    cm_text = "The legacy broking business (equity, derivatives, commodity, currency, institutional services, and M&A advisory) now contributes only 30% of total revenue - down from historical highs - reflecting MOFSL's deliberate diversification into annuity businesses. This is by design, not distress. While SEBI's F&O regulatory changes caused a 24% decline in brokerage revenue in Q2FY26, this segment's declining revenue share is actually evidence of the thesis working: the annuity businesses (AMC, wealth) are growing faster. The institutional equity distribution through research-led approach remains the brand anchor that drives HNI and institutional credibility across all other business lines."
    _add_text(slide, runtime, right_x + 0.10, tag_y + 0.05, right_w - 0.20, 1.10, _clip(cm_text, 1000), font=theme.body_font.family, size=7.5, color=theme.palette.text)
    
    # Broking Table
    cm_tbl_y = top + 1.95
    _add_text(slide, runtime, right_x + 0.10, cm_tbl_y - 0.20, right_w - 0.20, 0.20, "BROKING — REGULATORY IMPACT & OUTLOOK", font=theme.header_font.family, size=7.5, color=theme.palette.primary, bold=True)
    
    cm_rows = [
        ("F&O Volume Impact", "Peak levels", "-24% brokerage", "Stabilization by Q3FY26"),
        ("Market Share", "Gaining", "Holding", "Maintain 3-5%"),
        ("Broking % of Revenue", "~40%", "30%", "Target <25% by FY28")
    ]
    
    shape = slide.shapes.add_table(len(cm_rows) + 1, 4, runtime.Inches(right_x + 0.10), runtime.Inches(cm_tbl_y), runtime.Inches(right_w - 0.20), runtime.Inches(0.55))
    table = shape.table
    table.columns[0].width = runtime.Inches((right_w - 0.20) * 0.30)
    table.columns[1].width = runtime.Inches((right_w - 0.20) * 0.20)
    table.columns[2].width = runtime.Inches((right_w - 0.20) * 0.20)
    table.columns[3].width = runtime.Inches((right_w - 0.20) * 0.30)
    
    cm_hds = ["Parameter", "Before SEBI", "Post-SEBI (Q2FY26)", "Recovery Path"]
    for i, header in enumerate(cm_hds):
        _set_cell(table.cell(0, i), runtime, header, font=theme.header_font.family, size=6.5, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if i else runtime.PP_ALIGN.LEFT)
        
    for i, row in enumerate(cm_rows, start=1):
        row_fill = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
        for j, val in enumerate(row):
            color = theme.palette.red if "-24%" in val else theme.palette.green if "Target" in val else theme.palette.text
            bold = True if j in (1, 2) or "Target" in val else False
            _set_cell(table.cell(i, j), runtime, val, font=theme.body_font.family, size=6.5, color=color, fill=row_fill, bold=bold, align=runtime.PP_ALIGN.CENTER if j in (1, 2) else runtime.PP_ALIGN.RIGHT if j == 3 else runtime.PP_ALIGN.LEFT)

    # 2. Housing Finance
    hf_top = top + cm_h + 0.15
    hf_h = 1.45
    _add_rect(slide, runtime, right_x, hf_top, right_w, hf_h, "#FFFFFF", line="#C8D2E3")
    
    _add_text(slide, runtime, right_x + 0.10, hf_top + 0.10, 3.0, 0.20, "Housing Finance", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    
    hf_sub_w = 3.20
    _add_rect(slide, runtime, right_x + right_w - hf_sub_w - 0.10, hf_top + 0.10, hf_sub_w, 0.20, theme.palette.primary, radius=True)
    _add_text(slide, runtime, right_x + right_w - hf_sub_w - 0.10, hf_top + 0.12, hf_sub_w, 0.18, "Loan Book ₹6,630 Cr | +25% YoY | NII Income Stream", font=theme.header_font.family, size=6.5, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
    
    hf_tags = ['₹6,630 Cr Loan Book', '+25% YoY Growth', '₹42,775 Cr Distribution Book', 'Distribution +34% YoY']
    tag_y = _render_tags(right_x + 0.10, hf_top + 0.40, hf_tags)
    
    hf_text = "The Housing Finance segment provides retail mortgage lending focused on affordable and mid-segment housing loans, generating NII (Net Interest Income) - another recurring, cycle-resistant income stream. The loan book growing 25% YoY to ₹6,630 crore and the distribution book growing 34% to ₹42,775 crore demonstrate healthy momentum. Urbanization, rising disposable incomes, and government affordable housing schemes are secular tailwinds. The housing finance unit adds balance sheet depth and geographic diversification to MOFSL's increasingly asset-light wealth management core - providing a secured income stream to complement the fee revenues from AMC and wealth management."
    _add_text(slide, runtime, right_x + 0.10, tag_y + 0.05, right_w - 0.20, 0.85, _clip(hf_text, 1000), font=theme.body_font.family, size=7.5, color=theme.palette.text)

    # 3. Alternative Investments
    alt_top = hf_top + hf_h + 0.15
    alt_h = 1.35
    _add_rect(slide, runtime, right_x, alt_top, right_w, alt_h, "#FFFFFF", line="#C8D2E3")
    
    _add_text(slide, runtime, right_x + 0.10, alt_top + 0.10, 3.0, 0.20, "Alternative Investments", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    
    alt_sub_w = 3.00
    _add_rect(slide, runtime, right_x + right_w - alt_sub_w - 0.10, alt_top + 0.10, alt_sub_w, 0.20, theme.palette.primary, radius=True)
    _add_text(slide, runtime, right_x + right_w - alt_sub_w - 0.10, alt_top + 0.12, alt_sub_w, 0.18, "Carry: ₹58 Cr p.a. | Private Credit | Growing Rapidly", font=theme.header_font.family, size=6.5, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
    
    alt_tags = ['₹58 Cr Recurring Carry', 'New Private Credit Fund', 'India Pvt Credit $9B (H1 2025)', '+53% YoY Market Growth']
    tag_y = _render_tags(right_x + 0.10, alt_top + 0.40, alt_tags)
    
    alt_text = "The Alternatives segment (private credit, real estate, other alternative strategies) is MOFSL's fastest-growing and highest-margin business on a per-unit basis. India private credit investments hit a record US$9 billion in H1 2025 (+53% YoY jump), validating the market opportunity. The ₹58 crore recurring carry income represents a baseline that should grow significantly as the fund matures and new fund launches generate additional carry. This segment positions MOFSL as a full-spectrum investment platform - able to serve family offices and institutionals across liquid and illiquid asset classes."
    _add_text(slide, runtime, right_x + 0.10, tag_y + 0.05, right_w - 0.20, 0.75, _clip(alt_text, 1000), font=theme.body_font.family, size=7.5, color=theme.palette.text)

