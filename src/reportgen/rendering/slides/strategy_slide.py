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
    cell.text = text
    cell.margin_left = runtime.Inches(0.025)
    cell.margin_right = runtime.Inches(0.025)
    cell.margin_top = runtime.Inches(0.006)
    cell.margin_bottom = runtime.Inches(0.006)
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


def _clip(text: str, limit: int) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + "..."


def _money(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"\u20b9{number:,.0f}"


def _percent(value: Any, *, signed: bool = False) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    sign = "+" if signed and number > 0 else ""
    return f"{sign}{number:.0f}%"


def _replace_inr(text: str) -> str:
    return str(text or "").replace("INR ", "\u20b9").replace("INR", "\u20b9")


def _card(
    slide: Any,
    runtime: Any,
    theme: BrandTheme,
    left: float,
    top: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    accent: str,
    fill: str = "#F7F9FC",
    title_fill: str | None = None,
    title_color: str | None = None,
    body_size: float = 5.55,
) -> None:
    _add_rect(slide, runtime, left, top, width, height, fill, line="#C8D2E3")
    if title_fill:
        _add_rect(slide, runtime, left, top, width, 0.32, title_fill)
        _add_text(
            slide,
            runtime,
            left + 0.10,
            top + 0.06,
            width - 0.20,
            0.20,
            title.upper(),
            font=theme.header_font.family,
            size=8.0,
            color=title_color or "#FFFFFF",
            bold=True,
        )
        body_top = top + 0.40
    else:
        _add_rect(slide, runtime, left, top, 0.035, height, accent)
        _add_text(
            slide,
            runtime,
            left + 0.10,
            top + 0.08,
            width - 0.20,
            0.18,
            title,
            font=theme.body_font.family,
            size=9.0,
            color=theme.palette.primary,
            bold=True,
        )
        body_top = top + 0.32
    _add_text(
        slide,
        runtime,
        left + 0.10,
        body_top,
        width - 0.20,
        height - (body_top - top) - 0.08,
        _clip(_replace_inr(body), 620),
        font=theme.body_font.family,
        size=body_size,
        color=theme.palette.text,
    )


def _scorecard_table(
    slide: Any,
    runtime: Any,
    theme: BrandTheme,
    left: float,
    top: float,
    width: float,
    height: float,
    rows: list[tuple[str, str, str]],
) -> None:
    _add_text(
        slide,
        runtime,
        left,
        top - 0.24,
        width,
        0.20,
        "INVESTMENT SUMMARY SCORECARD",
        font=theme.header_font.family,
        size=9.0,
        color=theme.palette.primary,
        bold=True,
    )
    shape = slide.shapes.add_table(
        len(rows) + 1,
        3,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    table = shape.table
    table.columns[0].width = runtime.Inches(width * 0.44)
    table.columns[1].width = runtime.Inches(width * 0.35)
    table.columns[2].width = runtime.Inches(width * 0.21)
    headers = ["Parameter", "Assessment", "Score"]
    for index, header in enumerate(headers):
        _set_cell(
            table.cell(0, index),
            runtime,
            header,
            font=theme.header_font.family,
            size=8.0,
            color="#FFFFFF",
            fill=theme.palette.primary,
            bold=True,
            align=runtime.PP_ALIGN.RIGHT if index else runtime.PP_ALIGN.LEFT,
        )
    for row_index, row in enumerate(rows, start=1):
        fill = "#FFFFFF" if row_index % 2 == 0 else theme.palette.light_grey
        for col_index, value in enumerate(row):
            value_color = theme.palette.green if col_index == 1 and ("BUY" in value.upper() or "STRONG" in value.upper() or "AA+" in value.upper()) else theme.palette.text
            if col_index == 2:
                value_color = theme.palette.primary
            _set_cell(
                table.cell(row_index, col_index),
                runtime,
                value,
                font=theme.body_font.family,
                size=8.0,
                color=value_color,
                fill=fill,
                bold=col_index > 0,
                align=runtime.PP_ALIGN.RIGHT if col_index else runtime.PP_ALIGN.LEFT,
            )


def _exit_strategy(
    slide: Any,
    runtime: Any,
    theme: BrandTheme,
    left: float,
    top: float,
    width: float,
    height: float,
    upside_exit: list[str],
) -> None:
    _add_rect(slide, runtime, left, top, width, height, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, left, top, 0.035, height, theme.palette.accent)
    _add_text(slide, runtime, left + 0.10, top + 0.07, width - 0.20, 0.20, "Exit Strategy - Scaling Out on Gains", font=theme.body_font.family, size=9.0, color=theme.palette.primary, bold=True)
    items = upside_exit or ["Scale out near target price and reassess position if valuation moves ahead of fundamentals."]
    y = top + 0.35
    for index, item in enumerate(items[:3], start=1):
        _add_text(
            slide,
            runtime,
            left + 0.12,
            y,
            width - 0.24,
            0.38,
            f"Sell {index}: {_replace_inr(item)}",
            font=theme.body_font.family,
            size=8.0,
            color=theme.palette.text,
        )
        y += 0.42


def render_strategy_slide(
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

    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    strategy = model.trading_strategy
    if strategy is None:
        return

    meta = report_spec.metadata
    saarthi_score = f"{model.saarthi.total_score}/{model.saarthi.max_score}" if model.saarthi else "-"
    saarthi_zone = "BUY Zone" if model.saarthi and model.saarthi.total_score >= 70 else "Monitor"
    arr = model.metrics.get("arr_pct_of_revenue", "-")
    aum_growth = model.metrics.get("total_aum_yoy_pct", "-")
    credit = str(model.metrics.get("credit_rating", "AA+ Stable")).split()[0]

    left = 0.32
    right = 7.60
    top = 1.25
    left_w = 7.05
    right_w = 5.24

    conviction = (
        f"Conviction Statement: We initiate coverage on {report_spec.company.name} with a "
        f"{(meta.rating or '').upper()} rating and target price of {_money(meta.target_price)}, "
        f"representing {_percent(meta.upside_pct, signed=True)} upside from current levels. "
        f"At CMP {_money(meta.cmp)}, investors are buying a research-driven financial services platform "
        f"with ARR quality, AUM scale, and a clear re-rating pathway."
    )
    _card(
        slide,
        runtime,
        theme,
        left,
        top,
        left_w,
        0.85,
        "Conviction Statement",
        conviction,
        accent=theme.palette.accent,
        fill="#FFF0CC",
        body_size=8.0,
    )

    _add_text(slide, runtime, left, top + 0.95, left_w, 0.20, "ENTRY STRATEGY - WHEN TO BUY", font=theme.header_font.family, size=9.0, color=theme.palette.primary, bold=True)

    _card(
        slide,
        runtime,
        theme,
        left,
        top + 1.20,
        left_w,
        0.85,
        "Immediate Entry Zone",
        f"Current entry range is {strategy.entry_range or 'near current market price'} - optimal accumulation zone. {strategy.entry_rationale or ''} Use staggered buying to reduce market-timing risk while the valuation discount remains available.",
        accent=theme.palette.accent,
        body_size=8.0,
    )
    _card(
        slide,
        runtime,
        theme,
        left,
        top + 2.15,
        left_w,
        0.80,
        "Add-On Zone",
        f"Add on weakness if price corrects toward the downside support area. {strategy.downside_exit or ''} Treat volatility as opportunity only if the core ARR and AUM thesis remains intact.",
        accent=theme.palette.primary,
        body_size=8.0,
    )
    _card(
        slide,
        runtime,
        theme,
        left,
        top + 3.05,
        left_w,
        0.85,
        "Review Points - Thesis Confirmation Milestones",
        "Every quarter: " + "; ".join(_replace_inr(item) for item in strategy.review_metrics[:4]) + ".",
        accent=theme.palette.green,
        body_size=8.0,
    )

    _add_text(slide, runtime, left, top + 4.00, left_w, 0.20, "THESIS INVALIDATION TRIGGERS - WHEN TO EXIT", font=theme.header_font.family, size=9.0, color=theme.palette.primary, bold=True)
    y = top + 4.25
    for item in strategy.thesis_breaking_exits[:4]:
        _add_rect(slide, runtime, left, y + 0.05, 0.40, 0.20, "#FFE1E1")
        _add_text(slide, runtime, left + 0.04, y + 0.08, 0.32, 0.14, "EXIT", font=theme.header_font.family, size=6.0, color=theme.palette.red, bold=True, align=runtime.PP_ALIGN.CENTER)
        _add_text(slide, runtime, left + 0.48, y, left_w - 0.48, 0.30, _replace_inr(item), font=theme.body_font.family, size=8.0, color=theme.palette.text)
        y += 0.38

    scorecard_rows = [
        ("SAARTHI Framework", saarthi_zone, saarthi_score),
        ("Valuation Attractiveness", f"{_percent(meta.upside_pct, signed=True)} undervalued", f"Upside {meta.upside_pct}%"),
        ("Revenue Quality", f"{arr}% ARR recurring", "High quality"),
        ("AUM Growth Visibility", "High", f"{aum_growth}% YoY"),
        ("Management Track Record", "Founder-led", "9/10"),
        ("Governance Risk", "Monitor closely", "6/10"),
        ("Earnings Growth", "Strong", "27% CAGR"),
        ("Credit Rating", credit, "AA+ Stable"),
        ("Overall Recommendation", f"{(meta.rating or '').upper()} - High Conviction", f"TP: {_money(meta.target_price)}"),
    ]
    _scorecard_table(slide, runtime, theme, right, top + 0.05, right_w, 1.80, scorecard_rows)

    _card(
        slide,
        runtime,
        theme,
        right,
        top + 2.00,
        right_w,
        1.30,
        "Position Summary",
        (
            f"Rating: {(meta.rating or '').upper()} | Entry range: {_replace_inr(strategy.entry_range or '-')}. "
            f"Base target price: {_money(meta.target_price)}. Probability-weighted target: "
            f"{_money(model.metrics.get('probability_weighted_target'))}. "
            f"Stop-loss: {_replace_inr(strategy.downside_exit or '-')}. "
            f"Position sizing: {strategy.position_size or '-'}."
        ),
        accent=theme.palette.primary,
        fill="#F7F9FC",
        body_size=8.0,
    )

    _exit_strategy(slide, runtime, theme, right, top + 3.45, right_w, 1.30, list(strategy.upside_exit))

    _card(
        slide,
        runtime,
        theme,
        right,
        top + 4.90,
        right_w,
        0.80,
        "Disclaimer",
        "This research report has been prepared for informational purposes only and does not constitute an offer or solicitation. Investment decisions should be made with independent judgment.",
        accent=theme.palette.secondary,
        fill="#F7F9FC",
        body_size=6.5,
    )
