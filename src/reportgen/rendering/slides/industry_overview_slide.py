from __future__ import annotations

from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import BulletBlock, TextBlock
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


def _clip(text: str, limit: int) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + "..."


def render_industry_overview_slide(
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
        "Industry Overview — Indian Financial Services Landscape",
        page_number,
        theme,
        runtime,
    )

    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    
    text_block = next((b for b in slide_spec.blocks if isinstance(b, TextBlock)), None)
    
    left_x = 0.32
    mid_x = 4.60
    right_x = 8.88
    col_w = 4.10
    top = 1.20
    
    # Header Lines
    for x in [left_x, mid_x, right_x]:
        _add_rect(slide, runtime, x, top, col_w, 0.02, theme.palette.primary)
        _add_rect(slide, runtime, x, top + 0.35, col_w, 0.015, theme.palette.accent)

    # Subtitles
    _add_text(slide, runtime, left_x, top + 0.08, col_w, 0.25, "INDIA WEALTH MANAGEMENT SECTOR", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_text(slide, runtime, mid_x, top + 0.08, col_w, 0.25, "INDIA CAPITAL MARKETS SECTOR", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_text(slide, runtime, right_x, top + 0.08, col_w, 0.25, "INDIA WEALTH MARKET SIZE & GROWTH", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)

    paragraphs = []
    if text_block and text_block.content:
        paragraphs = [p for p in text_block.content.split("\n") if p.strip()]

    p1 = paragraphs[0] if len(paragraphs) > 0 else "India's financial services sector is positioned at the centre of the growth-resilience trade-off."
    p2 = paragraphs[1] if len(paragraphs) > 1 else "India's mutual fund industry penetration stands at just 5-6% of GDP."
    p3 = paragraphs[2] if len(paragraphs) > 2 else "F&O Regulatory Headwinds – Transient, Not Structural. SEBI's tightening of F&O trading norms in late 2025 created a meaningful but transient headwind."
    p4 = paragraphs[3] if len(paragraphs) > 3 else "India's capital markets are at the cusp of a structural deepening phase."

    # Column 1 Text
    _add_text(slide, runtime, left_x, top + 0.45, col_w, 1.0, _clip(p1, 550), font=theme.body_font.family, size=8, color=theme.palette.text)
    _add_text(slide, runtime, left_x, top + 1.50, col_w, 0.7, _clip(p2, 450), font=theme.body_font.family, size=8, color=theme.palette.text)

    # Column 2 Text
    _add_text(slide, runtime, mid_x, top + 0.45, col_w, 0.9, _clip(p3, 500), font=theme.body_font.family, size=8, color=theme.palette.text)
    _add_text(slide, runtime, mid_x, top + 1.40, col_w, 0.7, _clip(p4, 350), font=theme.body_font.family, size=8, color=theme.palette.text)

    # Column 1 Tailwinds
    tw_top = top + 2.4
    _add_text(slide, runtime, left_x, tw_top, col_w, 0.2, "KEY INDUSTRY TAILWINDS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, tw_top + 0.22, col_w, 0.015, theme.palette.secondary)
    
    tw_y = tw_top + 0.35
    tailwinds = model.industry_tailwinds if model.industry_tailwinds else [
        "Mutual Fund Penetration Under-development: India's MF penetration at 5-6% vs global average 20%+",
        "India's Demographic Dividend: Large working-age population entering peak earning years.",
        "Policy Support & Open Banking: FDI in insurance revised to 100%."
    ]
    for tw in tailwinds[:3]:
        _add_rect(slide, runtime, left_x, tw_y, 0.4, 0.18, "#E6F4EA", radius=True)
        _add_text(slide, runtime, left_x, tw_y + 0.02, 0.4, 0.15, "BULL", font=theme.header_font.family, size=6, color="#137333", bold=True, align=runtime.PP_ALIGN.CENTER)
        
        tw_body = tw
        _add_text(slide, runtime, left_x + 0.5, tw_y, col_w - 0.5, 0.6, _clip(tw_body, 220), font=theme.body_font.family, size=7.5, color=theme.palette.text)
        tw_y += 0.70

    # Column 2 Middle section (AI & DIGITAL TRANSFORMATION)
    mid_ai_top = top + 2.3
    _add_text(slide, runtime, mid_x, mid_ai_top, col_w, 0.2, "AI & DIGITAL TRANSFORMATION", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, mid_x, mid_ai_top + 0.22, col_w, 0.015, theme.palette.secondary)

    kpi_w = 1.95
    kpi_h = 0.65
    gap_x = 0.20
    gap_y = 0.15
    kpi_y = mid_ai_top + 0.35
    
    kpis = [
        ("OPERATIONAL EFFICIENCY", "60%", "Reduction in operational timelines via AI"),
        ("GENAI BANKING POTENTIAL", "46%", "RBI estimated enhancement potential"),
        ("FINTECH STARTUPS (2022)", "14,000", "Up from 733 in 2016-17"),
        ("PRIVATE CREDIT (H1 2025)", "$9B", "+53% YoY - record high"),
    ]
    
    for i, (k_title, k_val, k_sub) in enumerate(kpis):
        cx = mid_x + (i % 2) * (kpi_w + gap_x)
        cy = kpi_y + (i // 2) * (kpi_h + gap_y)
        _add_rect(slide, runtime, cx, cy, kpi_w, kpi_h, "#FFFFFF", line="#C8D2E3", radius=True)
        _add_text(slide, runtime, cx + 0.08, cy + 0.06, kpi_w - 0.16, 0.15, k_title, font=theme.header_font.family, size=6, color=theme.palette.muted_text, bold=True)
        _add_text(slide, runtime, cx + 0.08, cy + 0.22, kpi_w - 0.16, 0.25, k_val, font=theme.title_font.family, size=14, color=theme.palette.primary, bold=True)
        _add_text(slide, runtime, cx + 0.08, cy + 0.48, kpi_w - 0.16, 0.15, k_sub, font=theme.body_font.family, size=6, color=theme.palette.text)

    # Technology Moat Card
    moat_y = kpi_y + 2 * kpi_h + 2 * gap_y
    _add_rect(slide, runtime, mid_x, moat_y, col_w, 1.10, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, mid_x, moat_y, 0.04, 1.10, theme.palette.primary)
    _add_text(slide, runtime, mid_x + 0.10, moat_y + 0.05, col_w - 0.20, 0.20, "Technology Moat: Research Platform", font=theme.body_font.family, size=8.5, color=theme.palette.primary, bold=True)
    moat_text = "MOFSL's research franchise covering 300+ companies is the enduring competitive moat attracting institutional clients. AI is being deployed to enhance research productivity. The 'Buy Right, Sit Tight' philosophy is digitally codified in their investment process platform."
    _add_text(slide, runtime, mid_x + 0.10, moat_y + 0.25, col_w - 0.20, 0.80, moat_text, font=theme.body_font.family, size=7.5, color=theme.palette.text)

    # Column 3 Wealth Market Size KPIs
    right_kpi_y = top + 0.45
    r_kpis = [
        ("HNWI COUNT (JUN 2025)", "8.56L", "India's HNWIs - 4th globally by 2028"),
        ("HNWI BY 2027", "16.57L", "Projected - 94% growth from today"),
        ("UHNWI GROWTH BY 2028", "58.4%", "Fastest growing ultra-HNI pool globally"),
        ("NBFC PROFIT GROWTH", "16%", "Annual - sector profit doubling by FY30"),
    ]
    for i, (k_title, k_val, k_sub) in enumerate(r_kpis):
        cx = right_x + (i % 2) * (kpi_w + gap_x)
        cy = right_kpi_y + (i // 2) * (kpi_h + gap_y)
        _add_rect(slide, runtime, cx, cy, kpi_w, kpi_h, "#FFFFFF", line="#C8D2E3", radius=True)
        _add_text(slide, runtime, cx + 0.08, cy + 0.06, kpi_w - 0.16, 0.15, k_title, font=theme.header_font.family, size=6, color=theme.palette.muted_text, bold=True)
        _add_text(slide, runtime, cx + 0.08, cy + 0.22, kpi_w - 0.16, 0.25, k_val, font=theme.title_font.family, size=14, color=theme.palette.primary, bold=True)
        _add_text(slide, runtime, cx + 0.08, cy + 0.48, kpi_w - 0.16, 0.15, k_sub, font=theme.body_font.family, size=6, color=theme.palette.text)

    # Column 3 Risks
    risk_top = right_kpi_y + 2 * kpi_h + 2 * gap_y + 0.1
    _add_text(slide, runtime, right_x, risk_top, col_w, 0.2, "KEY INDUSTRY RISKS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_x, risk_top + 0.22, col_w, 0.015, theme.palette.secondary)
    
    risk_y = risk_top + 0.35
    risks = model.industry_risks if model.industry_risks else [
        "Regulatory Uncertainty: SEBI's evolving capital adequacy frameworks.",
        "Market Volatility & Revenue Cyclicality: Capital markets volatility.",
        "Fintech Disruption: 14,000+ fintech startups competing for the same base.",
        "India External Sector Vulnerability: India's reliance on foreign capital."
    ]
    for i, risk in enumerate(risks[:4]):
        tag = "HIGH" if i < 2 else "MED"
        color = "#C5221F" if tag == "HIGH" else "#E37400"
        bg = "#FCE8E6" if tag == "HIGH" else "#FEF7E0"
        _add_rect(slide, runtime, right_x, risk_y, 0.4, 0.18, bg, radius=True)
        _add_text(slide, runtime, right_x, risk_y + 0.02, 0.4, 0.15, tag, font=theme.header_font.family, size=6, color=color, bold=True, align=runtime.PP_ALIGN.CENTER)
        
        _add_text(slide, runtime, right_x + 0.5, risk_y, col_w - 0.5, 0.6, _clip(risk, 220), font=theme.body_font.family, size=7.5, color=theme.palette.text)
        risk_y += 0.70
