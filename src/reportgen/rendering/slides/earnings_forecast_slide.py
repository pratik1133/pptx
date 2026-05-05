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
    cell.margin_top = runtime.Inches(0.006)
    cell.margin_bottom = runtime.Inches(0.006)
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


def _get_series(model: Any, name: str) -> Any:
    for s in model.series:
        if s.name.lower() == name.lower():
            return s
    return None

def _get_val(series: Any, period: str, is_ratio: bool = False) -> str:
    if not series:
        return "-"
    if period in series.periods:
        idx = series.periods.index(period)
        val = series.values[idx]
        if val is None:
            return "-"
        if is_ratio:
            return f"{float(val):.1f}%"
        if series.unit == "x":
            return f"{float(val):.1f}x"
        return f"{float(val):,.0f}" if float(val) > 100 else f"{float(val):.1f}"
    return "-"

def _get_ratio(model: Any, name: str, period: str) -> str:
    for r in model.ratios:
        if r.name.lower() == name.lower():
            if period in r.periods:
                idx = r.periods.index(period)
                val = r.values[idx]
                if val is None:
                    return "-"
                if r.unit == "x":
                    return f"{float(val):.1f}x"
                return f"{float(val):.1f}%"
    return "-"


def render_earnings_forecast_slide(
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
        "Earnings Forecast — Multi-Year Financial Model",
        page_number,
        theme,
        runtime,
    )

    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    cmp = report_spec.metadata.cmp

    left_x = 0.32
    left_w = 7.00
    right_x = 7.52
    right_w = 5.50
    top = 1.25

    # ---------------------------------------------------------
    # LEFT COLUMN: P&L FORECAST MODEL
    _add_text(slide, runtime, left_x, top, left_w, 0.20, "P&L FORECAST MODEL (₹ CRORE)", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, top + 0.22, left_w, 0.02, theme.palette.secondary)

    # We will try to pull periods from the 'Revenue' series, or default to FY22A-FY28E
    rev_series = _get_series(model, "Revenue")
    if rev_series and len(rev_series.periods) >= 7:
        periods = rev_series.periods[-7:]
    else:
        periods = ["FY22A", "FY23A", "FY24A", "FY25A", "FY26E", "FY27E", "FY28E"]

    headers = ["Metric"] + periods
    
    # Rows definitions
    rows = [
        {"type": "section", "label": "Revenue & Profitability"},
        {"type": "data", "label": "Net Revenue (Cr)", "source": "Revenue"},
        {"type": "data", "label": "Revenue Growth", "source": "Revenue Growth", "is_pct": True},
        {"type": "data", "label": "EBITDA (Cr)", "source": "EBITDA"},
        {"type": "data", "label": "EBITDA Margin", "source": "EBITDA Margin", "is_ratio": True},
        {"type": "data", "label": "PAT (Cr)", "source": "PAT", "bold": True, "color": theme.palette.green},
        {"type": "data", "label": "PAT Margin", "source": "PAT Margin", "is_ratio": True},
        {"type": "section", "label": "Per Share Data"},
        {"type": "data", "label": "EPS (₹)", "source": "EPS", "bold": True},
        {"type": "data", "label": "EPS Growth", "source": "EPS Growth", "is_pct": True},
        {"type": "data", "label": "BVPS (₹)", "source": "BVPS"},
        {"type": "section", "label": f"Valuation Multiples (at CMP ₹{cmp})"},
        {"type": "data", "label": "P/E (x)", "source": "P/E", "is_ratio": True, "color": theme.palette.accent},
        {"type": "data", "label": "EV/EBITDA (x)", "source": "EV/EBITDA", "is_ratio": True, "color": theme.palette.accent},
        {"type": "data", "label": "P/B (x)", "source": "P/B", "is_ratio": True, "color": theme.palette.accent},
    ]

    table_top = top + 0.35
    row_height = 0.20
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), runtime.Inches(left_x), runtime.Inches(table_top), runtime.Inches(left_w), runtime.Inches(row_height * (len(rows) + 1)))
    table = shape.table
    table.columns[0].width = runtime.Inches(left_w * 0.28)
    for i in range(1, len(headers)):
        table.columns[i].width = runtime.Inches((left_w * 0.72) / (len(headers) - 1))

    # Header Row
    for i, header in enumerate(headers):
        _set_cell(table.cell(0, i), runtime, header, font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if i else runtime.PP_ALIGN.LEFT)

    # Data Rows
    for r_idx, row in enumerate(rows, start=1):
        if row["type"] == "section":
            _set_cell(table.cell(r_idx, 0), runtime, row["label"], font=theme.header_font.family, size=7, color=theme.palette.primary, fill="#E8EEF8", bold=True)
            for c_idx in range(1, len(headers)):
                _set_cell(table.cell(r_idx, c_idx), runtime, "", font=theme.body_font.family, size=7, color="#FFFFFF", fill="#E8EEF8")
        else:
            fill = "#FFFFFF" if r_idx % 2 == 0 else theme.palette.light_grey
            # PAT row gets a special green color in the label, EPS is bold
            label_color = theme.palette.green if "PAT (" in row["label"] else theme.palette.text
            label_bold = row.get("bold", False)
            
            _set_cell(table.cell(r_idx, 0), runtime, row["label"], font=theme.body_font.family, size=7, color=label_color, fill=fill, bold=label_bold)
            
            # Fetch values
            series = _get_series(model, row["source"])
            for c_idx, period in enumerate(periods, start=1):
                val = ""
                if row.get("is_ratio"):
                    val = _get_ratio(model, row["source"], period)
                else:
                    val = _get_val(series, period)
                
                is_forecast = period.endswith("E")
                
                cell_color = theme.palette.text
                cell_bold = False
                
                if val != "-" and val != "":
                    # Base styling for forecasted numbers
                    if is_forecast:
                        cell_color = theme.palette.primary
                        cell_bold = True
                    
                    # PAT and EPS are green when forecasted
                    if is_forecast and ("PAT (" in row["label"] or "EPS (" in row["label"]):
                        cell_color = theme.palette.green
                        
                    # Multiples are orange when forecasted
                    if is_forecast and ("(x)" in row["label"]):
                        cell_color = theme.palette.accent
                        cell_bold = False
                        
                    # Percentage coloring
                    if "%" in val:
                        try:
                            fval = float(val.strip('%').strip('+').strip('-'))
                            # Only color extreme or specific percentages, or keep it simple
                            if "-" in val:
                                cell_color = theme.palette.red
                                cell_bold = True
                            elif "+" in val:
                                cell_color = theme.palette.green
                                cell_bold = True
                            elif is_forecast:
                                # For normal positive YoY in forecast, keep it primary
                                cell_color = theme.palette.primary
                                cell_bold = True
                        except ValueError:
                            pass
                
                # Historical PAT / EPS might be bold
                if not is_forecast and ("PAT (" in row["label"] or "EPS (" in row["label"]):
                    cell_bold = True
                
                _set_cell(table.cell(r_idx, c_idx), runtime, val, font=theme.body_font.family, size=7, color=cell_color, fill=fill, bold=cell_bold, align=runtime.PP_ALIGN.CENTER)

    source_y = table_top + row_height * (len(rows) + 1) + 0.05
    _add_text(slide, runtime, left_x, source_y, left_w, 0.15, "Source: Company filings, Tikona Capital Research estimates, E = Tikona Capital estimates.", font=theme.body_font.family, size=6, color=theme.palette.muted_text)

    # ---------------------------------------------------------
    # LEFT COLUMN: CAGR SUMMARY
    cagr_top = source_y + 0.25
    _add_text(slide, runtime, left_x, cagr_top, left_w, 0.20, "CAGR SUMMARY", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, cagr_top + 0.22, left_w, 0.02, theme.palette.secondary)

    cagr_rows = [
        ("Revenue", "24.7%", "24.7%"),
        ("EBITDA", "28.9%", "23.8%"),
        ("Net Income (PAT)", "24.1%", "27.8%"),
    ]
    
    shape = slide.shapes.add_table(len(cagr_rows) + 1, 3, runtime.Inches(left_x), runtime.Inches(cagr_top + 0.35), runtime.Inches(left_w), runtime.Inches(0.8))
    table = shape.table
    table.columns[0].width = runtime.Inches(left_w * 0.40)
    table.columns[1].width = runtime.Inches(left_w * 0.30)
    table.columns[2].width = runtime.Inches(left_w * 0.30)
    
    _set_cell(table.cell(0, 0), runtime, "Metric", font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True)
    _set_cell(table.cell(0, 1), runtime, "3Y Historical CAGR (FY22-25)", font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)
    _set_cell(table.cell(0, 2), runtime, "Projected 3Y CAGR (FY25-28)", font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)

    for i, (metric, hist, proj) in enumerate(cagr_rows, start=1):
        fill = "#FFFFFF" if i % 2 == 0 else theme.palette.light_grey
        _set_cell(table.cell(i, 0), runtime, metric, font=theme.body_font.family, size=7, color=theme.palette.text, fill=fill)
        _set_cell(table.cell(i, 1), runtime, hist, font=theme.body_font.family, size=7, color=theme.palette.green, fill=fill, bold=True, align=runtime.PP_ALIGN.CENTER)
        _set_cell(table.cell(i, 2), runtime, proj, font=theme.body_font.family, size=7, color=theme.palette.green, fill=fill, bold=True, align=runtime.PP_ALIGN.CENTER)

    # ---------------------------------------------------------
    # RIGHT COLUMN: FORECAST ASSUMPTIONS
    _add_text(slide, runtime, right_x, top, right_w, 0.20, "FORECAST ASSUMPTIONS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_x, top + 0.22, right_w, 0.02, theme.palette.accent)

    # Assump Card 1
    a1_top = top + 0.35
    a1_h = 2.10
    _add_rect(slide, runtime, right_x, a1_top, right_w, a1_h, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, right_x, a1_top, 0.04, a1_h, theme.palette.accent)
    _add_text(slide, runtime, right_x + 0.10, a1_top + 0.08, right_w - 0.20, 0.20, "Revenue Growth Drivers (FY26-28)", font=theme.body_font.family, size=8.5, color=theme.palette.primary, bold=True)
    
    drivers = [
        "AMC & Wealth (30%+ CAGR): AUM compounding at 25-30% CAGR as India's HNI base expands. Management fee income grows proportionally. 91% outperformance track record sustains premium fee capture vs. discount managers.",
        "Housing Finance (25% CAGR): Loan book growing 25% YoY. NII improvement as RM productivity matures. Urbanization and government affordable housing schemes provide secular demand tailwind across geographies.",
        "Alternatives (40%+ CAGR): Private credit fund with ₹58 Cr recurring carry expected to continue and grow. India private credit market record $9B in H1 2025 (+53% YoY) validates the institutional appetite for this product.",
        "Broking Recovery (10-15%): F&O volume normalization post regulatory adaptation. Transaction revenues recovering as market participants adjust. This segment's declining revenue share is per plan - minimal reliance assumed."
    ]
    dy = a1_top + 0.30
    for d in drivers:
        _add_text(slide, runtime, right_x + 0.10, dy, right_w - 0.20, 0.50, d, font=theme.body_font.family, size=7, color=theme.palette.text)
        dy += 0.45

    # Assump Card 2
    a2_top = a1_top + a1_h + 0.15
    a2_h = 1.00
    _add_rect(slide, runtime, right_x, a2_top, right_w, a2_h, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, right_x, a2_top, 0.04, a2_h, theme.palette.primary)
    _add_text(slide, runtime, right_x + 0.10, a2_top + 0.08, right_w - 0.20, 0.20, "PAT Growth Acceleration — Key Assumption", font=theme.body_font.family, size=8.5, color=theme.palette.primary, bold=True)
    pat_text = "PAT re-accelerates at 27% CAGR (FY25-28) driven by: (1) AMC operating leverage - AUM growing 30%+ with marginal incremental costs, (2) Private Wealth advisory fee income compounding, (3) Housing Finance NII growing at 25% on loan book expansion, (4) Alternatives carry income scaling. EBITDA margin sustaining at 52%+ validates the fee model quality. PAT growth of 27% CAGR significantly ahead of revenue growth (25%) - operating leverage is the story."
    _add_text(slide, runtime, right_x + 0.10, a2_top + 0.30, right_w - 0.20, 0.70, _clip(pat_text, 500), font=theme.body_font.family, size=7, color=theme.palette.text)

    # Assump Card 3
    a3_top = a2_top + a2_h + 0.15
    a3_h = 0.85
    _add_rect(slide, runtime, right_x, a3_top, right_w, a3_h, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, right_x, a3_top, 0.04, a3_h, theme.palette.red)
    _add_text(slide, runtime, right_x + 0.10, a3_top + 0.08, right_w - 0.20, 0.20, "Downside Scenario Assumptions", font=theme.body_font.family, size=8.5, color=theme.palette.red, bold=True)
    downside_text = "If SEBI regulatory headwinds intensify (additional F&O restrictions, fee caps on AMC), revenue CAGR compresses to 15-18%. If AUM growth slows to 15% YoY due to market correction, PAT CAGR reverts to ~10%. Combined downside yields PAT of ~₹2,800 Cr in FY26E vs. base ₹3,066 Cr - approximately 9% downside to earnings. Stop loss at ₹750 provides reasonable risk management."
    _add_text(slide, runtime, right_x + 0.10, a3_top + 0.30, right_w - 0.20, 0.60, _clip(downside_text, 400), font=theme.body_font.family, size=7, color=theme.palette.text)

    # ---------------------------------------------------------
    # RIGHT COLUMN: QUARTERLY EARNINGS TREND
    q_top = a3_top + a3_h + 0.20
    _add_text(slide, runtime, right_x, q_top, right_w, 0.20, "QUARTERLY EARNINGS TREND (RECENT)", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_x, q_top + 0.22, right_w, 0.02, theme.palette.secondary)

    q_rows = [
        ("Q2 FY25", "High", "₹1,242", "+123% YoY", theme.palette.green),
        ("H1 FY26 (Op.)", "₹2,888", "₹1,088", "+11% YoY", theme.palette.green),
        ("Q2 FY26", "-34.91%", "-67.64%", "SEBI F&O impact", theme.palette.red),
        ("Op. PAT (Q2 FY26)", "-", "₹611 Cr", "+16% YoY", theme.palette.green),
    ]

    shape = slide.shapes.add_table(len(q_rows) + 1, 4, runtime.Inches(right_x), runtime.Inches(q_top + 0.35), runtime.Inches(right_w), runtime.Inches(0.9))
    table = shape.table
    table.columns[0].width = runtime.Inches(right_w * 0.30)
    table.columns[1].width = runtime.Inches(right_w * 0.25)
    table.columns[2].width = runtime.Inches(right_w * 0.20)
    table.columns[3].width = runtime.Inches(right_w * 0.25)
    
    q_headers = ["Quarter", "Revenue (Cr)", "PAT (Cr)", "YoY Change"]
    for i, header in enumerate(q_headers):
        _set_cell(table.cell(0, i), runtime, header, font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if i else runtime.PP_ALIGN.LEFT)

    for i, (q, rev, pat, yoy, color) in enumerate(q_rows, start=1):
        fill = "#FFFFFF" if i % 2 == 0 else theme.palette.light_grey
        _set_cell(table.cell(i, 0), runtime, q, font=theme.body_font.family, size=7, color=theme.palette.text, fill=fill, bold=True)
        _set_cell(table.cell(i, 1), runtime, rev, font=theme.body_font.family, size=7, color=theme.palette.text, fill=fill, align=runtime.PP_ALIGN.RIGHT)
        _set_cell(table.cell(i, 2), runtime, pat, font=theme.body_font.family, size=7, color=theme.palette.text, fill=fill, align=runtime.PP_ALIGN.RIGHT)
        _set_cell(table.cell(i, 3), runtime, yoy, font=theme.body_font.family, size=7, color=color, fill=fill, bold=True, align=runtime.PP_ALIGN.RIGHT)

    source_q_y = q_top + 0.35 + 1.0
    _add_text(slide, runtime, right_x, source_q_y, right_w, 0.15, "Source: MOFSL Quarterly Reports; Tikona Capital Research estimates.", font=theme.body_font.family, size=6, color=theme.palette.muted_text)
