from __future__ import annotations

from pathlib import Path
from typing import Any

from reportgen.rendering.brand_shell import _format_date_ddmmyyyy, _hex_to_rgb, apply_background
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.number_format import format_for_unit
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import BulletBlock, TextBlock
from reportgen.schemas.financials import FinancialModelSnapshot, FinancialSeries
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _money(value: Any, *, precision: int = 0) -> str:
    number = _num(value)
    if number is None:
        return "-"
    return f"\u20b9{number:,.{precision}f}"


def _market_cap(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "-"
    if number >= 1_000_000:
        number = number / 1_00_00_000
    return f"\u20b9{number:,.0f} Cr"


def _percent(value: Any, *, signed: bool = False) -> str:
    number = _num(value)
    if number is None:
        return "-"
    sign = "+" if signed and number > 0 else ""
    return f"{sign}{number:.0f}%"


def _clip(text: str, limit: int) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + "..."


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
    shape_type = runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _hex_to_rgb(runtime, fill)
    if line:
        shape.line.color.rgb = _hex_to_rgb(runtime, line)
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
    run.font.color.rgb = _hex_to_rgb(runtime, color)
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
    cell.vertical_anchor = runtime.MSO_ANCHOR.MIDDLE
    cell.margin_left = runtime.Inches(0.025)
    cell.margin_right = runtime.Inches(0.025)
    cell.margin_top = runtime.Inches(0.006)
    cell.margin_bottom = runtime.Inches(0.006)
    cell.fill.solid()
    cell.fill.fore_color.rgb = _hex_to_rgb(runtime, fill)
    paragraph = cell.text_frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.runs[0]
    run.font.name = font
    run.font.size = runtime.Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _hex_to_rgb(runtime, color)


def _series_by_name(model: FinancialModelSnapshot, name: str) -> FinancialSeries | None:
    for series in model.series:
        if series.name.lower() == name.lower():
            return series
    return None


def _series_value(model: FinancialModelSnapshot, name: str, period: str) -> str:
    series = _series_by_name(model, name)
    if not series or period not in series.periods:
        return "-"
    index = series.periods.index(period)
    return format_for_unit(series.values[index], series.unit)


def _ratio_value(model: FinancialModelSnapshot, name: str, period: str) -> str:
    for ratio in model.ratios:
        if ratio.name.lower() == name.lower() and period in ratio.periods:
            return format_for_unit(ratio.values[ratio.periods.index(period)], ratio.unit)
    return "-"


def _metric(model: FinancialModelSnapshot, key: str, default: str = "-") -> str:
    value = model.metrics.get(key)
    if value is None:
        return default
    return str(value)


def _market_cap_category(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "-"
    crore = number / 1_00_00_000 if number >= 1_000_000 else number
    if crore >= 100_000:
        return "Large Cap"
    if crore >= 20_000:
        return "Mid Cap"
    return "Small Cap"


def _latest_series_value(model: FinancialModelSnapshot, name: str) -> str:
    series = _series_by_name(model, name)
    if not series or not series.values:
        return "-"
    return format_for_unit(series.values[-1], series.unit)


def _latest_ratio_value(model: FinancialModelSnapshot, name: str) -> str:
    for ratio in model.ratios:
        if ratio.name.lower() == name.lower() and ratio.values:
            return format_for_unit(ratio.values[-1], ratio.unit)
    return "-"


def _display_periods(model: FinancialModelSnapshot) -> list[str]:
    if model.series:
        return list(model.series[0].periods[-4:])
    if model.ratios:
        return list(model.ratios[0].periods[-4:])
    return ["P1", "P2", "P3", "P4"]


def _series_row(model: FinancialModelSnapshot, name: str, periods: list[str]) -> tuple[str, list[str]] | None:
    series = _series_by_name(model, name)
    if not series:
        return None
    return (name, [_series_value(model, name, p) for p in periods])


def _ratio_row(model: FinancialModelSnapshot, name: str, periods: list[str]) -> tuple[str, list[str]] | None:
    if not any(r.name.lower() == name.lower() for r in model.ratios):
        return None
    return (name, [_ratio_value(model, name, p) for p in periods])


def _growth_row(model: FinancialModelSnapshot, name: str, base_series_name: str, periods: list[str]) -> tuple[str, list[str]] | None:
    if any(r.name.lower() == name.lower() for r in model.ratios):
        return (name, [_ratio_value(model, name, p) for p in periods])
    
    series = _series_by_name(model, base_series_name)
    if not series:
        return None
        
    values = []
    for p in periods:
        if p in series.periods:
            idx = series.periods.index(p)
            if idx > 0 and series.values[idx] is not None and series.values[idx-1] is not None and float(series.values[idx-1]) != 0:
                growth = ((float(series.values[idx]) - float(series.values[idx-1])) / float(series.values[idx-1])) * 100
                values.append(f"{growth:.1f}%")
            else:
                values.append("-")
        else:
            values.append("-")
    return (name, values)


def _cover_text(slide_spec: SlideSpec) -> tuple[str, list[str]]:
    thesis = ""
    bullets: list[str] = []
    for block in slide_spec.blocks:
        if isinstance(block, TextBlock) and not thesis:
            thesis = block.content
        if isinstance(block, BulletBlock):
            bullets = list(block.items)
    return thesis, bullets


def _fallback_thesis(report_spec: ReportSpec) -> str:
    for layout in ("investment_thesis", "key_highlights"):
        for slide in report_spec.slides:
            if slide.layout != layout:
                continue
            for block in slide.blocks:
                if isinstance(block, TextBlock) and block.content.strip():
                    return block.content
    return ""


def _fallback_bullets(report_spec: ReportSpec) -> list[str]:
    for layout in ("investment_thesis", "key_highlights"):
        for slide in report_spec.slides:
            if slide.layout != layout:
                continue
            for block in slide.blocks:
                if isinstance(block, BulletBlock) and block.items:
                    return list(block.items)
    return []


def _render_brand_header(
    slide: Any,
    report_spec: ReportSpec,
    slide_spec: SlideSpec,
    theme: BrandTheme,
    runtime: Any,
    model: FinancialModelSnapshot | None,
) -> None:
    canvas_w = theme.canvas.width_in
    meta = report_spec.metadata
    header_h = 1.90
    _add_rect(slide, runtime, 0, 0, canvas_w, header_h, theme.palette.primary)

    logo_path = Path(theme.logo_path) if theme.logo_path else None
    logo_exists = bool(logo_path and logo_path.exists())
    if logo_exists:
        try:
            # Add a white background "chip" behind the logo to ensure visibility
            chip_pad_x = 0.08
            chip_pad_y = 0.06
            logo_height = 0.36
            chip_height = logo_height + 2 * chip_pad_y
            chip_width = 1.7 + 2 * chip_pad_x
            chip = slide.shapes.add_shape(
                runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                runtime.Inches(0.22 - chip_pad_x),
                runtime.Inches(0.12 - chip_pad_y),
                runtime.Inches(chip_width),
                runtime.Inches(chip_height),
            )
            chip.fill.solid()
            chip.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.background)
            chip.line.fill.background()
            slide.shapes.add_picture(str(logo_path), runtime.Inches(0.22), runtime.Inches(0.12), height=runtime.Inches(logo_height))
        except Exception:
            pass
    else:
        emblem = slide.shapes.add_shape(
            runtime.MSO_AUTO_SHAPE_TYPE.OVAL,
            runtime.Inches(0.22),
            runtime.Inches(0.12),
            runtime.Inches(0.36),
            runtime.Inches(0.36),
        )
        emblem.fill.solid()
        emblem.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.accent)
        emblem.line.fill.background()
        _add_text(slide, runtime, 0.28, 0.18, 0.24, 0.18, "T", font=theme.header_font.family, size=10, color=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)
        _add_text(slide, runtime, 0.62, 0.09, 2.1, 0.24, theme.firm_name, font=theme.title_font.family, size=14, color="#FFFFFF", bold=True)
        _add_text(slide, runtime, 0.62, 0.34, 2.6, 0.16, theme.firm_tagline.upper(), font=theme.header_font.family, size=7, color="#C8D2E3")
    _add_text(
        slide,
        runtime,
        canvas_w - 2.85,
        0.10,
        2.55,
        0.22,
        f"{(meta.report_type or 'Initiating').upper()} COVERAGE",
        font=theme.header_font.family,
        size=8,
        color="#FFFFFF",
        bold=True,
        align=runtime.PP_ALIGN.CENTER,
    )

    _add_text(slide, runtime, 0.22, 0.55, 5.15, 0.45, report_spec.company.name, font=theme.title_font.family, size=24, color="#FFFFFF", bold=True)
    rating = (meta.rating or "").upper()
    if rating:
        _add_rect(slide, runtime, 5.40, 0.62, 0.62, 0.28, theme.palette.accent)
        _add_text(slide, runtime, 5.42, 0.64, 0.58, 0.22, rating, font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)

    exchange = f"NSE: {report_spec.company.ticker}"
    if report_spec.company.exchange and report_spec.company.exchange.upper() != "NSE":
        exchange = f"{report_spec.company.exchange}: {report_spec.company.ticker}"
    descriptor = f"{exchange}  |  {report_spec.company.sector or ''} / {report_spec.company.industry or ''}"
    _add_text(slide, runtime, 6.10, 0.70, 4.47, 0.16, descriptor, font=theme.header_font.family, size=7.5, color="#D9E2F2")

    _add_rect(slide, runtime, 0.22, 1.02, canvas_w - 0.44, 0.01, theme.palette.secondary)
    saarthi = "-"
    if model and model.saarthi:
        saarthi = f"{model.saarthi.total_score}/{model.saarthi.max_score}"
    market_cap = _market_cap(meta.market_cap)
    stats = [
        ("CMP", _money(meta.cmp, precision=2), f"As of {_format_date_ddmmyyyy(str(meta.report_date))}"),
        ("TARGET PRICE", _money(meta.target_price), "12M upside case"),
        ("MARKET CAP", market_cap, ""),
        ("MARKET CAP CATEGORY", _market_cap_category(meta.market_cap), f"{report_spec.company.sector} company"),
        ("SAARTHI SCORE", saarthi, model.saarthi.rating if model and model.saarthi and model.saarthi.rating else ""),
    ]
    stat_w = (canvas_w - 0.44) / len(stats)
    for index, (label, value, sub) in enumerate(stats):
        left = 0.22 + index * stat_w
        _add_text(slide, runtime, left, 1.08, stat_w - 0.05, 0.14, label, font=theme.header_font.family, size=7, color="#BFD0EA", bold=True)
        _add_text(slide, runtime, left, 1.24, stat_w - 0.05, 0.22, value, font=theme.metric_font.family, size=12, color=theme.palette.accent if index in {0, 1, 4} else "#FFFFFF", bold=True)
        if sub:
            _add_text(slide, runtime, left, 1.48, stat_w - 0.05, 0.14, _clip(sub, 35), font=theme.header_font.family, size=6, color="#C8D2E3")
        if index < len(stats) - 1:
            _add_rect(slide, runtime, left + stat_w - 0.04, 1.12, 0.006, 0.40, theme.palette.secondary)

    tagline = slide_spec.subtitle or ""
    if not tagline:
        thesis, _ = _cover_text(slide_spec)
        tagline = thesis.split(".")[0] if thesis else report_spec.company.description
    _add_rect(slide, runtime, 0, header_h, canvas_w, 0.55, theme.palette.accent)
    _add_text(slide, runtime, 0.22, header_h + 0.08, canvas_w - 0.44, 0.35, f'"{_clip(tagline, 160)}"', font=theme.title_font.family, size=13, color=theme.palette.primary, bold=True)


def _render_highlight_card(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    title: str,
    body: str,
    theme: BrandTheme,
    accent: str,
) -> None:
    _add_rect(slide, runtime, left, top, width, height, "#F7F9FC", line="#C8D2E3")
    _add_rect(slide, runtime, left, top, 0.035, height, accent)
    _add_text(slide, runtime, left + 0.10, top + 0.06, width - 0.18, 0.20, title, font=theme.body_font.family, size=8.5, color=theme.palette.primary, bold=True)
    _add_text(slide, runtime, left + 0.10, top + 0.28, width - 0.18, height - 0.34, _clip(body, 185), font=theme.body_font.family, size=7.5, color=theme.palette.text)


def _render_left_column(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    model: FinancialModelSnapshot | None,
    theme: BrandTheme,
    runtime: Any,
) -> None:
    thesis, bullets = _cover_text(slide_spec)
    if not thesis:
        thesis = _fallback_thesis(report_spec)
    if not bullets:
        bullets = _fallback_bullets(report_spec)
    highlights = [(item.split(":", 1)[0], item.split(":", 1)[1].strip() if ":" in item else item) for item in bullets]
    if model and model.key_highlights:
        highlights = [(h.title, h.body) for h in model.key_highlights]

    left = 0.22
    top = 2.58
    width = 6.86
    thesis_h = 1.36
    _add_rect(slide, runtime, left, top, width, thesis_h, "#FFF0CC", line="#F3C673")
    _add_rect(slide, runtime, left, top, 0.035, thesis_h, theme.palette.accent)
    _add_text(slide, runtime, left + 0.12, top + 0.08, width - 0.24, 0.20, "Investment Thesis", font=theme.body_font.family, size=9, color=theme.palette.primary, bold=True)
    _add_text(slide, runtime, left + 0.12, top + 0.30, width - 0.24, thesis_h - 0.38, _clip(thesis, 760), font=theme.body_font.family, size=8, color=theme.palette.text, bold=True)

    card_top = top + thesis_h + 0.12
    gap_x = 0.14
    gap_y = 0.10
    card_w = (width - gap_x) / 2
    card_h = 0.88
    accents = [theme.palette.primary, theme.palette.accent, theme.palette.green, theme.palette.secondary, theme.palette.teal, theme.palette.green]
    for index, (title, body) in enumerate(highlights[:6]):
        col = index % 2
        row = index // 2
        _render_highlight_card(
            slide,
            runtime,
            left + col * (card_w + gap_x),
            card_top + row * (card_h + gap_y),
            card_w,
            card_h,
            _clip(title, 42),
            body,
            theme,
            accents[index % len(accents)],
        )


def _render_financial_summary(
    slide: Any,
    model: FinancialModelSnapshot | None,
    theme: BrandTheme,
    runtime: Any,
) -> None:
    if model is None:
        return
    left = 7.22
    top = 2.58
    width = 3.48
    _add_text(slide, runtime, left, top, width, 0.18, "FINANCIAL SUMMARY (INR CRORE)", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    periods = _display_periods(model)
    candidate_rows = [
        _series_row(model, "Revenue", periods),
        _growth_row(model, "Revenue Growth", "Revenue", periods),
        _series_row(model, "EBITDA", periods),
        _growth_row(model, "EBITDA Growth", "EBITDA", periods),
        _ratio_row(model, "EBITDA Margin", periods),
        _series_row(model, "PAT", periods),
        _growth_row(model, "PAT Growth", "PAT", periods),
        _ratio_row(model, "PAT Margin", periods),
        _series_row(model, "EPS", periods),
        _ratio_row(model, "P/E", periods),
        _ratio_row(model, "P/B", periods),
        _ratio_row(model, "EV/EBITDA", periods),
        _ratio_row(model, "ROE", periods),
    ]
    rows = [row for row in candidate_rows if row is not None][:13]
    if not rows:
        rows = [("Revenue", ["-"] * len(periods))]
    shape = slide.shapes.add_table(
        len(rows) + 1,
        len(periods) + 1,
        runtime.Inches(left),
        runtime.Inches(top + 0.23),
        runtime.Inches(width),
        runtime.Inches(2.55),
    )
    table = shape.table
    table.columns[0].width = runtime.Inches(0.86)
    for col in range(1, len(periods) + 1):
        table.columns[col].width = runtime.Inches((width - 0.86) / len(periods))
    headers = ["Metric", *periods]
    for col, header in enumerate(headers):
        _set_cell(table.cell(0, col), runtime, header, font=theme.header_font.family, size=7, color="#FFFFFF", fill=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER if col else runtime.PP_ALIGN.LEFT)
    for row_index, (label, values) in enumerate(rows, start=1):
        fill = "#FFFFFF" if row_index % 2 == 0 else theme.palette.light_grey
        _set_cell(table.cell(row_index, 0), runtime, label, font=theme.body_font.family, size=7, color=theme.palette.text, fill=fill, bold=True)
        for col, value in enumerate(values, start=1):
            color = theme.palette.green if col >= 3 and label in {"EPS", "P/E", "P/B", "EV/EBITDA", "ROE"} else theme.palette.text
            _set_cell(table.cell(row_index, col), runtime, value.replace(" Cr", ""), font=theme.body_font.family, size=7, color=color, fill=fill, bold=col >= 3, align=runtime.PP_ALIGN.CENTER)

    _add_text(slide, runtime, left, top + 2.95, width, 0.18, "LATEST MODEL SNAPSHOT", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    snapshot_rows = [
        ("Latest Revenue", _latest_series_value(model, "Revenue")),
        ("Latest EBITDA", _latest_series_value(model, "EBITDA")),
        ("Latest PAT", _latest_series_value(model, "PAT")),
        ("Latest ROE", _latest_ratio_value(model, "ROE")),
        ("Latest Margin", _latest_ratio_value(model, "EBITDA Margin")),
    ]
    _render_key_value_table(slide, runtime, left, top + 3.16, width, 1.02, snapshot_rows, theme, title_fill=theme.palette.light_grey)


def _render_key_value_table(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    rows: list[tuple[str, str]],
    theme: BrandTheme,
    *,
    title_fill: str = "#FFFFFF",
    value_color: str | None = None,
) -> None:
    shape = slide.shapes.add_table(len(rows), 2, runtime.Inches(left), runtime.Inches(top), runtime.Inches(width), runtime.Inches(height))
    table = shape.table
    table.columns[0].width = runtime.Inches(width * 0.63)
    table.columns[1].width = runtime.Inches(width * 0.37)
    for row_index, (label, value) in enumerate(rows):
        fill = title_fill if row_index % 2 == 0 else "#FFFFFF"
        _set_cell(table.cell(row_index, 0), runtime, label, font=theme.body_font.family, size=7, color=theme.palette.text, fill=fill, bold=False)
        _set_cell(table.cell(row_index, 1), runtime, value, font=theme.body_font.family, size=7, color=value_color or theme.palette.primary, fill=fill, bold=True, align=runtime.PP_ALIGN.RIGHT)


def _render_side_panel(
    slide: Any,
    model: FinancialModelSnapshot | None,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
) -> None:
    if model is None:
        return
    left = 10.86
    top = 2.58
    width = 2.25

    def panel(y: float, h: float, title: str, rows: list[tuple[str, str]], *, fill: str = theme.palette.primary, value_color: str | None = None) -> None:
        _add_rect(slide, runtime, left, y, width, h, fill, radius=True)
        _add_text(slide, runtime, left + 0.09, y + 0.06, width - 0.18, 0.18, title.upper(), font=theme.header_font.family, size=7.5, color=theme.palette.accent if fill == theme.palette.primary else theme.palette.primary, bold=True)
        if fill == theme.palette.primary:
            row_top = y + 0.27
            for index, (label, value) in enumerate(rows):
                _add_text(slide, runtime, left + 0.10, row_top + index * 0.20, width * 0.55, 0.14, label, font=theme.body_font.family, size=7, color="#E8EEF8")
                _add_text(slide, runtime, left + width * 0.55, row_top + index * 0.20, width * 0.40, 0.14, value, font=theme.body_font.family, size=7.5, color=value_color or "#FFFFFF", bold=True, align=runtime.PP_ALIGN.RIGHT)
        else:
            row_top = y + 0.28
            for index, (label, value) in enumerate(rows):
                _add_text(slide, runtime, left + 0.10, row_top + index * 0.20, width * 0.55, 0.14, label, font=theme.body_font.family, size=7, color=theme.palette.text)
                _add_text(slide, runtime, left + width * 0.55, row_top + index * 0.20, width * 0.40, 0.14, value, font=theme.body_font.family, size=7.5, color=value_color or theme.palette.primary, bold=True, align=runtime.PP_ALIGN.RIGHT)

    panel(
        top,
        1.02,
        "Valuation Scenarios",
        [
            ("Bull Case TP", _money(model.valuation_bands[0].base if len(model.valuation_bands) > 0 else None)),
            ("Base Case TP", _money(model.valuation_bands[1].base if len(model.valuation_bands) > 1 else None)),
            ("Bear Case TP", _money(model.valuation_bands[2].base if len(model.valuation_bands) > 2 else None)),
        ],
    )
    panel(
        top + 1.10,
        0.80,
        "Key Operating Stats",
        [
            ("Revenue", _latest_series_value(model, "Revenue")),
            ("EBITDA", _latest_series_value(model, "EBITDA")),
            ("PAT", _latest_series_value(model, "PAT")),
        ],
        fill="#F7F9FC",
    )
    
    arr_value = _metric(model, "arr_pct_of_revenue", "65")
    _add_rect(slide, runtime, left, top + 1.98, width, 0.78, theme.palette.secondary, radius=True)
    _add_text(slide, runtime, left + 0.10, top + 2.04, width - 0.20, 0.16, "ARR INFLECTION WATCH", font=theme.header_font.family, size=7.5, color=theme.palette.accent, bold=True)
    _add_text(slide, runtime, left + 0.10, top + 2.23, width - 0.20, 0.26, f"{arr_value}%", font=theme.metric_font.family, size=20, color=theme.palette.accent, bold=True)
    _add_text(slide, runtime, left + 0.10, top + 2.51, width - 0.20, 0.18, "ARR of total net revenues. Re-rating trigger: 70%+ ARR.", font=theme.body_font.family, size=6.5, color="#FFFFFF")


def _render_footer(slide: Any, report_spec: ReportSpec, theme: BrandTheme, runtime: Any) -> None:
    canvas_w = theme.canvas.width_in
    canvas_h = theme.canvas.height_in
    footer_top = canvas_h - 0.18
    _add_rect(slide, runtime, 0, footer_top, canvas_w, 0.18, "#F7F9FC", line="#D8DEE8")
    _add_text(slide, runtime, 0.22, footer_top + 0.02, 3.0, 0.12, "SEBI Reg. No.: INH000069807", font=theme.footer_font.family, size=6.5, color=theme.palette.muted_text)
    _add_text(slide, runtime, canvas_w * 0.25, footer_top + 0.02, canvas_w * 0.30, 0.12, f"{report_spec.company.name} - Equity Research", font=theme.footer_font.family, size=6.5, color=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.CENTER)
    report_ref = f"Report Reference: Q2 FY2025-26 | {_format_date_ddmmyyyy(str(report_spec.metadata.report_date))}"
    _add_text(slide, runtime, canvas_w * 0.56, footer_top + 0.02, canvas_w * 0.27, 0.12, report_ref, font=theme.footer_font.family, size=6.2, color=theme.palette.muted_text, align=runtime.PP_ALIGN.RIGHT)
    _add_text(slide, runtime, canvas_w - 1.05, footer_top + 0.02, 0.85, 0.12, "Page 1 of 15", font=theme.footer_font.family, size=6.5, color=theme.palette.muted_text, align=runtime.PP_ALIGN.RIGHT)


def render_cover_slide(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
) -> None:
    apply_background(slide, theme, runtime)
    try:
        model = RenderDataResolver(report_spec).financial_model
    except Exception:
        model = None

    _render_brand_header(slide, report_spec, slide_spec, theme, runtime, model)
    _render_left_column(slide, slide_spec, report_spec, model, theme, runtime)
    _render_financial_summary(slide, model, theme, runtime)
    _render_side_panel(slide, model, report_spec, theme, runtime)
    _render_footer(slide, report_spec, theme, runtime)
