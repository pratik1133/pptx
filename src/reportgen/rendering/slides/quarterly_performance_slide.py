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


def _get_q_series(model: Any, name: str) -> Any:
    for s in model.quarterly_series:
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

def render_quarterly_performance_slide(
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
        "Quarterly Performance — Earnings Trajectory",
        page_number,
        theme,
        runtime,
    )

    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model

    text_block = next((b for b in slide_spec.blocks if isinstance(b, TextBlock)), None)

    left_x = 0.32
    left_w = 4.20
    right_x = 4.82
    right_w = 8.20
    top = 1.25

    # ---------------------------------------------------------
    # LEFT COLUMN: PERFORMANCE NARRATIVE
    _add_text(slide, runtime, left_x, top, left_w, 0.20, "QUARTERLY HIGHLIGHTS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, top + 0.22, left_w, 0.02, theme.palette.secondary)

    narrative_text = text_block.content if text_block else "Recent quarterly trajectory shows the variability inherent to the cyclical revenue base, alongside the steady growth of the annuity businesses."
    _add_rect(slide, runtime, left_x, top + 0.35, left_w, 2.50, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, left_x, top + 0.35, 0.04, 2.50, theme.palette.primary)
    _add_text(slide, runtime, left_x + 0.15, top + 0.45, left_w - 0.30, 2.30, _clip(narrative_text, 800), font=theme.body_font.family, size=8, color=theme.palette.text)

    # Key KPI Badges
    badge_top = top + 3.0
    _add_text(slide, runtime, left_x, badge_top, left_w, 0.20, "RECENT METRICS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_x, badge_top + 0.22, left_w, 0.02, theme.palette.secondary)
    
    # We pull the latest period's revenue and PAT if available
    rev_q = _get_q_series(model, "Revenue")
    pat_q = _get_q_series(model, "PAT")
    
    latest_q = rev_q.periods[-1] if rev_q and rev_q.periods else "Latest Qtr"
    rev_val = _get_val(rev_q, latest_q) if rev_q else "N/A"
    pat_val = _get_val(pat_q, latest_q) if pat_q else "N/A"

    _add_rect(slide, runtime, left_x, badge_top + 0.35, left_w / 2 - 0.05, 0.6, "#FFFFFF", line=theme.palette.accent, radius=True)
    _add_text(slide, runtime, left_x, badge_top + 0.40, left_w / 2 - 0.05, 0.15, f"{latest_q} REVENUE", font=theme.header_font.family, size=6.5, color=theme.palette.accent, bold=True, align=runtime.PP_ALIGN.CENTER)
    _add_text(slide, runtime, left_x, badge_top + 0.60, left_w / 2 - 0.05, 0.25, rev_val, font=theme.title_font.family, size=14, color=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)

    _add_rect(slide, runtime, left_x + left_w / 2 + 0.05, badge_top + 0.35, left_w / 2 - 0.05, 0.6, "#FFFFFF", line=theme.palette.green, radius=True)
    _add_text(slide, runtime, left_x + left_w / 2 + 0.05, badge_top + 0.40, left_w / 2 - 0.05, 0.15, f"{latest_q} PAT", font=theme.header_font.family, size=6.5, color=theme.palette.green, bold=True, align=runtime.PP_ALIGN.CENTER)
    _add_text(slide, runtime, left_x + left_w / 2 + 0.05, badge_top + 0.60, left_w / 2 - 0.05, 0.25, pat_val, font=theme.title_font.family, size=14, color=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)


    # ---------------------------------------------------------
    # RIGHT COLUMN: QUARTERLY FINANCIAL TABLE
    _add_text(slide, runtime, right_x, top, right_w, 0.20, "QUARTERLY FINANCIAL TREND (₹ CRORE)", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_x, top + 0.22, right_w, 0.02, theme.palette.secondary)

    # We will try to pull periods from the 'Revenue' quarterly series
    if rev_q and len(rev_q.periods) >= 6:
        periods = rev_q.periods[-6:]
    elif rev_q and len(rev_q.periods) > 0:
        periods = rev_q.periods
    else:
        periods = ["Q1 FY24", "Q2 FY24", "Q3 FY24", "Q4 FY24", "Q1 FY25", "Q2 FY25"]

    headers = ["Metric"] + periods
    
    # Rows definitions (similar to annual P&L but for quarters)
    rows = [
        {"type": "section", "label": "Operating Performance"},
        {"type": "data", "label": "Net Revenue", "source": "Revenue"},
        {"type": "data", "label": "Revenue Growth (YoY)", "source": "Revenue Growth YoY", "is_pct": True},
        {"type": "data", "label": "EBITDA", "source": "EBITDA"},
        {"type": "data", "label": "EBITDA Margin", "source": "EBITDA Margin", "is_pct": True},
        {"type": "data", "label": "PAT", "source": "PAT", "bold": True, "color": theme.palette.green},
        {"type": "data", "label": "PAT Margin", "source": "PAT Margin", "is_pct": True},
        {"type": "section", "label": "Per Share Data"},
        {"type": "data", "label": "EPS (₹)", "source": "EPS", "bold": True},
    ]

    table_top = top + 0.35
    row_height = 0.22
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), runtime.Inches(right_x), runtime.Inches(table_top), runtime.Inches(right_w), runtime.Inches(row_height * (len(rows) + 1)))
    table = shape.table
    table.columns[0].width = runtime.Inches(right_w * 0.25)
    for i in range(1, len(headers)):
        table.columns[i].width = runtime.Inches((right_w * 0.75) / (len(headers) - 1))

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
            label_color = theme.palette.green if row["label"] == "PAT" else theme.palette.text
            label_bold = row.get("bold", False)
            
            _set_cell(table.cell(r_idx, 0), runtime, row["label"], font=theme.body_font.family, size=7, color=label_color, fill=fill, bold=label_bold)
            
            series = _get_q_series(model, row["source"])
            for c_idx, period in enumerate(periods, start=1):
                val = _get_val(series, period)
                
                cell_color = theme.palette.text
                cell_bold = False
                
                if val != "-" and val != "":
                    if row["label"] in ("PAT", "EPS (₹)"):
                        cell_color = theme.palette.primary
                        cell_bold = True
                        
                    # Percentage coloring
                    if "%" in val:
                        try:
                            fval = float(val.strip('%').strip('+').strip('-'))
                            if "-" in val:
                                cell_color = theme.palette.red
                                cell_bold = True
                            elif "+" in val:
                                cell_color = theme.palette.green
                                cell_bold = True
                        except ValueError:
                            pass
                
                _set_cell(table.cell(r_idx, c_idx), runtime, val, font=theme.body_font.family, size=7, color=cell_color, fill=fill, bold=cell_bold, align=runtime.PP_ALIGN.CENTER)

    source_y = table_top + row_height * (len(rows) + 1) + 0.10
    _add_text(slide, runtime, right_x, source_y, right_w, 0.15, "Source: Company Quarterly Filings; Tikona Capital Research.", font=theme.body_font.family, size=6, color=theme.palette.muted_text)
