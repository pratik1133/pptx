from __future__ import annotations

from io import BytesIO
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.financials import FinancialModelSnapshot, FinancialSeries, RatioEntry
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _rgb(runtime: Any, color: str) -> Any:
    return runtime.RGBColor.from_string(color.removeprefix("#"))


def _as_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _series(model: FinancialModelSnapshot, name: str) -> tuple[list[str], list[float]]:
    series = _series_entry(model, name)
    if series:
        return list(series.periods), [_as_float(v) for v in series.values]
    return [], []


def _ratio(model: FinancialModelSnapshot, name: str) -> tuple[list[str], list[float]]:
    ratio = _ratio_entry(model, name)
    if ratio:
        return list(ratio.periods), [_as_float(v) for v in ratio.values]
    return [], []


def _series_entry(model: FinancialModelSnapshot, name: str) -> FinancialSeries | None:
    for series in model.series:
        if series.name.lower() == name.lower():
            return series
    return None


def _ratio_entry(model: FinancialModelSnapshot, name: str) -> RatioEntry | None:
    for ratio in model.ratios:
        if ratio.name.lower() == name.lower():
            return ratio
    return None


def _metric(model: FinancialModelSnapshot, key: str) -> float:
    return _as_float(model.metrics.get(key))


def _k_label(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value / 1000:.1f}K"
    return f"{value:.0f}"


def _period_range(periods: list[str]) -> str:
    if not periods:
        return ""
    if len(periods) == 1:
        return periods[0]
    return f"{periods[0]} to {periods[-1]}"


def _source_note(report_spec: ReportSpec) -> str:
    return f"Source: {report_spec.company.ticker or report_spec.company.name}, Tikona Capital estimates"


def _panel_image(
    theme: BrandTheme,
    title: str,
    draw: Callable[[Any], None],
    *,
    footnote: str = "",
    height: float = 2.05,
) -> BytesIO:
    fig, ax = plt.subplots(figsize=(4.25, height), dpi=180)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    draw(ax)
    ax.set_title(title.upper(), loc="left", fontsize=7.5, fontweight="bold", color=theme.palette.primary, pad=7)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.28, color=theme.palette.muted_text)
    ax.tick_params(axis="x", labelsize=5.8, colors=theme.palette.muted_text)
    ax.tick_params(axis="y", labelsize=5.8, colors=theme.palette.muted_text)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#CDD6E5")
        ax.spines[side].set_linewidth(0.7)
    if footnote:
        fig.text(0.02, 0.02, footnote, fontsize=5.2, color=theme.palette.muted_text, style="italic")
    fig.tight_layout(rect=(0, 0.06 if footnote else 0.01, 1, 0.98))
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _add_panel(
    slide: Any,
    runtime: Any,
    image: BytesIO,
    left: float,
    top: float,
    width: float,
    height: float,
    theme: BrandTheme,
) -> None:
    card = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    card.fill.solid()
    card.fill.fore_color.rgb = _rgb(runtime, "#FFFFFF")
    card.line.color.rgb = _rgb(runtime, "#C8D2E3")
    card.line.width = runtime.Pt(0.8)
    slide.shapes.add_picture(
        image,
        runtime.Inches(left + 0.10),
        runtime.Inches(top + 0.10),
        width=runtime.Inches(width - 0.20),
        height=runtime.Inches(height - 0.20),
    )
    accent = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        runtime.Inches(left + 0.12),
        runtime.Inches(top + 0.20),
        runtime.Inches(0.035),
        runtime.Inches(0.26),
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = _rgb(runtime, theme.palette.accent)
    accent.line.fill.background()


def _bars_with_labels(ax, labels: list[str], values: list[float], colors: list[str], *, percent: bool = False) -> None:
    bars = ax.bar(range(len(labels)), values, color=colors, width=0.68)
    ax.set_xticks(range(len(labels)), labels)
    upper = max(values or [1]) * 1.22
    ax.set_ylim(0, upper if upper else 1)
    for bar, value in zip(bars, values, strict=True):
        label = f"{value:.1f}%" if percent else _k_label(value)
        ax.annotate(label, (bar.get_x() + bar.get_width() / 2, value), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=5.4, color="#244A8F")


def render_story_charts_slide(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
    *,
    page_number: int,
) -> None:
    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model

    render_section_header(
        slide,
        Box(left=0.5, top=0.6, width=12.333, height=0.55),
        slide_spec.title or f"Story in Charts - {report_spec.company.name}",
        page_number,
        theme,
        runtime,
    )

    primary = theme.palette.primary
    accent = theme.palette.accent
    green = theme.palette.green
    teal = theme.palette.teal

    periods, revenue = _series(model, "Revenue")
    _, pat = _series(model, "PAT")
    _, eps = _series(model, "EPS")
    _, ebitda = _series(model, "EBITDA")
    _, ebitda_margin = _ratio(model, "EBITDA Margin")
    _, roe = _ratio(model, "RoE")

    hist_forecast_colors = [primary if i < 4 else accent for i in range(len(periods))]

    images: list[BytesIO] = []
    revenue_unit = (_series_entry(model, "Revenue").unit if _series_entry(model, "Revenue") else model.currency)
    pat_unit = (_series_entry(model, "PAT").unit if _series_entry(model, "PAT") else model.currency)
    ebitda_unit = (_series_entry(model, "EBITDA").unit if _series_entry(model, "EBITDA") else model.currency)

    if periods and revenue:
        images.append(
            _panel_image(
                theme,
                f"Revenue ({revenue_unit}) - {_period_range(periods)}",
                lambda ax: _bars_with_labels(ax, periods, revenue, hist_forecast_colors),
                footnote=f"Revenue trajectory across model periods | {_source_note(report_spec)}",
            )
        )
    if periods and pat:
        images.append(
            _panel_image(
                theme,
                f"PAT ({pat_unit}) - {_period_range(periods)}",
                lambda ax: (
                    _bars_with_labels(ax, periods, pat, hist_forecast_colors),
                    ax.plot(range(len(pat)), pat, color=green, linewidth=1.4, marker="o", markersize=2.8),
                ),
                footnote=f"Profit trajectory across model periods | {_source_note(report_spec)}",
            )
        )
    if periods and ebitda_margin:
        images.append(
            _panel_image(
                theme,
                f"EBITDA Margin (%) - {_period_range(periods)}",
                lambda ax: _bars_with_labels(ax, periods, ebitda_margin, hist_forecast_colors, percent=True),
                footnote=f"Margin profile from model ratios | {_source_note(report_spec)}",
            )
        )

    latest_aum = _metric(model, "total_aum_lakh_cr")
    yoy = _metric(model, "total_aum_yoy_pct") / 100 if _metric(model, "total_aum_yoy_pct") else 0.0
    if latest_aum:
        prior_aum = latest_aum / (1 + yoy) if yoy else latest_aum * 0.75
        aum_periods = ["Prior", "Latest", "Forward"]
        aum_values = [prior_aum, latest_aum, latest_aum * 1.22]
        images.append(
            _panel_image(
                theme,
                "Total AUM Growth (INR Lakh Cr)",
                lambda ax: (
                    _bars_with_labels(ax, aum_periods, aum_values, [primary, accent, accent]),
                    ax.plot(range(len(aum_values)), aum_values, color=green, linewidth=1.4, marker="o", markersize=2.8),
                ),
                footnote="AUM panel shown only when AUM metrics are available in the model",
            )
        )

    arr = _metric(model, "arr_pct_of_revenue")
    fee = _metric(model, "fee_based_pct_of_revenue")
    brokerage = _metric(model, "brokerage_pct_of_revenue")
    if arr and fee and brokerage:
        legacy_other = max(0, 100 - fee - brokerage)
        now_other = max(0, 100 - arr - brokerage)

        def draw_mix(ax) -> None:
            labels = ["Fee Mix", "ARR Mix"]
            bottoms = [0, 0]
            for values, color, label in [
                ([brokerage, brokerage], primary, "Brokerage"),
                ([fee, arr], accent, "Fee / ARR"),
                ([legacy_other, now_other], teal, "Other"),
            ]:
                ax.bar(labels, values, bottom=bottoms, color=color, width=0.52, label=label)
                bottoms = [b + v for b, v in zip(bottoms, values, strict=True)]
            ax.set_ylim(0, 100)
            ax.legend(frameon=False, fontsize=5.4, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.28))
            for x, total in enumerate(bottoms):
                ax.annotate(f"{total:.0f}%", (x, total), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=5.4)

        images.append(
            _panel_image(
                theme,
                "Revenue Mix - Fee / ARR / Brokerage",
                draw_mix,
                footnote="Revenue-quality panel shown only when fee, ARR, and brokerage metrics exist",
            )
        )
    elif model.segments:
        segment_labels = [segment.name[:18] for segment in model.segments if segment.revenue_share_pct is not None]
        segment_values = [_as_float(segment.revenue_share_pct) for segment in model.segments if segment.revenue_share_pct is not None]
        if segment_labels and segment_values:
            images.append(
                _panel_image(
                    theme,
                    "Revenue Mix by Segment (%)",
                    lambda ax: _bars_with_labels(
                        ax,
                        segment_labels,
                        segment_values,
                        [primary, accent, teal, green, theme.palette.secondary, theme.palette.red][: len(segment_values)],
                        percent=True,
                    ),
                    footnote=f"Segment revenue share from structured model | {_source_note(report_spec)}",
                    height=2.20,
                )
            )

    def draw_roe_eps(ax) -> None:
        _bars_with_labels(ax, periods, roe, hist_forecast_colors, percent=True)
        if eps:
            ax2 = ax.twinx()
            ax2.plot(range(len(eps)), eps, color=green, linewidth=1.6, marker="o", markersize=2.8)
            ax2.tick_params(axis="y", labelsize=5.8, colors=green)
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_color("#CDD6E5")
            for x, value in enumerate(eps):
                ax2.annotate(f"{value:.0f}", (x, value), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=5.0, color=green)

    if periods and roe:
        title = "RoE (%) & EPS - Multi-Year Trajectory" if eps else f"RoE (%) - {_period_range(periods)}"
        images.append(
            _panel_image(
                theme,
                title,
                draw_roe_eps,
                footnote=f"Return profile from model ratios | {_source_note(report_spec)}",
            )
        )
    elif periods and ebitda:
        images.append(
            _panel_image(
                theme,
                f"EBITDA ({ebitda_unit}) - {_period_range(periods)}",
                lambda ax: _bars_with_labels(ax, periods, ebitda, hist_forecast_colors),
                footnote=f"Operating profit trajectory | {_source_note(report_spec)}",
            )
        )

    if model.scenarios and len(images) < 6:
        scenario_labels = [scenario.name for scenario in model.scenarios if scenario.target_price is not None]
        scenario_values = [_as_float(scenario.target_price) for scenario in model.scenarios if scenario.target_price is not None]
        if scenario_labels and scenario_values:
            images.append(
                _panel_image(
                    theme,
                    f"Scenario Target Prices ({model.currency})",
                    lambda ax: _bars_with_labels(
                        ax,
                        scenario_labels,
                        scenario_values,
                        [theme.palette.red, primary, green, accent][: len(scenario_values)],
                    ),
                    footnote=f"Scenario targets from valuation model | {_source_note(report_spec)}",
                )
            )

    left = 0.32
    top = 1.32
    gap_x = 0.15
    gap_y = 0.14
    panel_w = (12.68 - 2 * gap_x) / 3
    panel_h = 2.20
    for index, image in enumerate(images):
        col = index % 3
        row = index // 3
        _add_panel(
            slide,
            runtime,
            image,
            left + col * (panel_w + gap_x),
            top + row * (panel_h + gap_y),
            panel_w,
            panel_h,
            theme,
        )
