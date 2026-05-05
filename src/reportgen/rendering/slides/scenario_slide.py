from __future__ import annotations

from decimal import Decimal
from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _rgb(runtime: Any, color: str) -> Any:
    return runtime.RGBColor.from_string(color.removeprefix("#"))


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_money(value: Any) -> str:
    numeric = _as_float(value)
    if numeric is None:
        return "-"
    return f"\u20b9{numeric:,.0f}"


def _format_percent(value: Any) -> str:
    numeric = _as_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.1f}%"


def _vs_cmp(target_price: Any, cmp: Any) -> str:
    target = _as_float(target_price)
    cmp_value = _as_float(cmp)
    if target is None or cmp_value in (None, 0):
        return "-"
    change = ((target - cmp_value) / cmp_value) * 100
    return f"{change:+.1f}%"


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
) -> Any:
    shape = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(runtime, fill)
    if line:
        shape.line.color.rgb = _rgb(runtime, line)
        shape.line.width = runtime.Pt(0.8)
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
) -> Any:
    box = slide.shapes.add_textbox(
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = runtime.Inches(0.05)
    frame.margin_right = runtime.Inches(0.05)
    frame.margin_top = runtime.Inches(0.02)
    frame.margin_bottom = runtime.Inches(0.02)
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


def _add_assumption_card(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    theme: BrandTheme,
    accent: str,
) -> None:
    _add_rect(slide, runtime, left, top, width, height, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, left, top, 0.035, height, accent)
    _add_text(
        slide,
        runtime,
        left + 0.08,
        top + 0.04,
        width - 0.16,
        0.20,
        title,
        font=theme.body_font.family,
        size=9,
        color=theme.palette.primary,
        bold=True,
    )
    _add_text(
        slide,
        runtime,
        left + 0.08,
        top + 0.26,
        width - 0.16,
        height - 0.30,
        body,
        font=theme.body_font.family,
        size=8,
        color=theme.palette.text,
    )


def _set_table_cell(
    cell: Any,
    runtime: Any,
    text: str,
    *,
    font: str,
    size: float,
    color: str,
    bold: bool = False,
    fill: str | None = None,
    align: Any | None = None,
) -> None:
    cell.text = text
    cell.margin_left = runtime.Inches(0.03)
    cell.margin_right = runtime.Inches(0.03)
    cell.margin_top = runtime.Inches(0.01)
    cell.margin_bottom = runtime.Inches(0.01)
    if fill:
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(runtime, fill)
    paragraph = cell.text_frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.runs[0]
    run.font.name = font
    run.font.size = runtime.Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(runtime, color)


def _scenario_lookup(report_spec: ReportSpec) -> dict[str, Any]:
    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    return {scenario.name.strip().lower(): scenario for scenario in model.scenarios}


def _valuation_notes(report_spec: ReportSpec) -> dict[str, str]:
    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    notes: dict[str, str] = {}
    for band in model.valuation_bands:
        key = band.method.lower()
        if "bear" in key:
            notes["bear"] = band.notes or ""
        elif "base" in key:
            notes["base"] = band.notes or ""
        elif "bull" in key:
            notes["bull"] = band.notes or ""
    return notes


def _scenario_title(name: str, target: Decimal | None, cmp: Any) -> str:
    label = f"{name.upper()} CASE - {_format_money(target)} ({_vs_cmp(target, cmp)} vs CMP)"
    if name == "base":
        label = f"{label} - PRIMARY RECOMMENDATION"
    return label


def _macro_text(name: str, scenario: Any) -> str:
    rev = _format_percent(scenario.revenue_cagr_pct)
    margin = _format_percent(scenario.ebitda_margin_pct)
    if name == "bear":
        return f"Equity markets remain subdued. Revenue CAGR slows to {rev}; EBITDA margin compresses to {margin} as regulation and lower risk appetite pressure activity."
    if name == "bull":
        return f"Market participation strengthens and structural savings flows accelerate. Revenue compounds at {rev}; EBITDA margin expands to {margin} with operating leverage."
    return f"Markets normalize and savings flows remain constructive. Revenue compounds at {rev}; EBITDA margin holds near {margin} on steady AUM growth."


def _business_text(name: str, scenario: Any) -> str:
    notes = scenario.notes or ""
    if name == "bear":
        prefix = "Broking headwinds and fee pressure reduce operating momentum."
    elif name == "bull":
        prefix = "ARR mix, AMC scale, and wealth management momentum trigger re-rating."
    else:
        prefix = "ARR stability and diversified financial services earnings support the base case."
    return f"{prefix} {notes}".strip()


def _valuation_text(name: str, scenario: Any, valuation_notes: dict[str, str], cmp: Any) -> str:
    note = valuation_notes.get(name) or "Target price reflects scenario assumptions and assigned probability."
    return f"{note} Target price {_format_money(scenario.target_price)}, probability {_format_percent(scenario.probability_pct)}, vs CMP {_vs_cmp(scenario.target_price, cmp)}."


def _render_metric_table(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    scenario_name: str,
    scenario: Any,
    *,
    theme: BrandTheme,
    value_color: str,
    cmp: Any,
) -> None:
    rows = [
        ("Revenue CAGR", _format_percent(scenario.revenue_cagr_pct)),
        ("EBITDA Margin", _format_percent(scenario.ebitda_margin_pct)),
        ("Target Price", _format_money(scenario.target_price)),
        ("Probability", _format_percent(scenario.probability_pct)),
        ("vs CMP", _vs_cmp(scenario.target_price, cmp)),
    ]
    shape = slide.shapes.add_table(
        len(rows) + 1,
        2,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    table = shape.table
    table.columns[0].width = runtime.Inches(width * 0.56)
    table.columns[1].width = runtime.Inches(width * 0.44)
    _set_table_cell(
        table.cell(0, 0),
        runtime,
        "Metric",
        font=theme.header_font.family,
        size=8,
        color="#FFFFFF",
        bold=True,
        fill=theme.palette.primary,
    )
    _set_table_cell(
        table.cell(0, 1),
        runtime,
        f"{scenario_name.title()} Value",
        font=theme.header_font.family,
        size=8,
        color="#FFFFFF",
        bold=True,
        fill=theme.palette.primary,
        align=runtime.PP_ALIGN.RIGHT,
    )
    for row_index, (label, value) in enumerate(rows, start=1):
        fill = theme.palette.background if row_index % 2 == 0 else theme.palette.light_grey
        _set_table_cell(
            table.cell(row_index, 0),
            runtime,
            label,
            font=theme.body_font.family,
            size=8,
            color=theme.palette.text,
            bold=True,
            fill=fill,
        )
        _set_table_cell(
            table.cell(row_index, 1),
            runtime,
            value,
            font=theme.body_font.family,
            size=8,
            color=value_color if label in {"Target Price", "vs CMP"} else theme.palette.text,
            bold=label in {"Target Price", "vs CMP"},
            fill=fill,
            align=runtime.PP_ALIGN.RIGHT,
        )


def render_scenario_slide(
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
        slide_spec.title,
        page_number,
        theme,
        runtime,
    )

    scenarios = _scenario_lookup(report_spec)
    valuation_notes = _valuation_notes(report_spec)
    cmp = report_spec.metadata.cmp
    column_defs = [
        ("bear", theme.palette.primary, theme.palette.red, theme.palette.red),
        ("base", theme.palette.primary, theme.palette.accent, theme.palette.accent),
        ("bull", theme.palette.green, theme.palette.green, theme.palette.green),
    ]
    col_w = 4.18
    gap = 0.16
    left0 = 0.5
    top = 1.35

    for index, (name, header_fill, accent, value_color) in enumerate(column_defs):
        scenario = scenarios.get(name)
        if scenario is None:
            continue

        left = left0 + index * (col_w + gap)
        _add_rect(slide, runtime, left, top, col_w, 0.38, header_fill)
        _add_text(
            slide,
            runtime,
            left + 0.08,
            top + 0.05,
            col_w - 0.16,
            0.28,
            _scenario_title(name, scenario.target_price, cmp),
            font=theme.header_font.family,
            size=8.5,
            color="#FFFFFF" if name == "bull" else accent,
            bold=True,
        )

        card_top = top + 0.45
        _add_assumption_card(
            slide,
            runtime,
            left,
            card_top,
            col_w,
            0.82,
            "Macro Assumptions",
            _macro_text(name, scenario),
            theme=theme,
            accent=accent,
        )
        _add_assumption_card(
            slide,
            runtime,
            left,
            card_top + 0.94,
            col_w,
            1.24,
            "Business Assumptions",
            _business_text(name, scenario)[:430],
            theme=theme,
            accent=accent,
        )
        _add_assumption_card(
            slide,
            runtime,
            left,
            card_top + 2.30,
            col_w,
            0.88,
            "Valuation Assumptions",
            _valuation_text(name, scenario, valuation_notes, cmp)[:330],
            theme=theme,
            accent=accent,
        )
        _render_metric_table(
            slide,
            runtime,
            left,
            card_top + 3.30,
            col_w,
            1.07,
            name,
            scenario,
            theme=theme,
            value_color=value_color,
            cmp=cmp,
        )
