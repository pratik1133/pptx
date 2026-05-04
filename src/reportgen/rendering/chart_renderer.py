"""Themed chart rendering. All matplotlib styling is driven from the brand theme."""
from __future__ import annotations

from io import BytesIO
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.number_format import (
    format_currency,
    format_for_unit,
    format_multiple,
    format_number,
    format_percent,
)
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.charts import ChartBlock
from reportgen.schemas.financials import FinancialSeries


def _palette(theme: BrandTheme) -> list[str]:
    if theme.chart_palette:
        return theme.chart_palette
    return [theme.palette.primary, theme.palette.accent, theme.palette.secondary]


def _axis_formatter(unit: str | None):
    u = (unit or "").strip().lower()
    if u in {"%", "pct", "percent"}:
        return FuncFormatter(lambda v, _pos: f"{v:g}%")
    if u in {"x", "multiple"}:
        return FuncFormatter(lambda v, _pos: f"{v:g}x")
    if u in {"bps", "basis points"}:
        return FuncFormatter(lambda v, _pos: f"{v:g} bps")
    if u in {"inr cr", "₹ cr", "rs cr", "cr"}:
        return FuncFormatter(lambda v, _pos: f"₹{v:,.0f} Cr")
    if u in {"inr", "rs", "₹"}:
        return FuncFormatter(lambda v, _pos: f"₹{v:,.0f}")
    return FuncFormatter(lambda v, _pos: f"{v:,.0f}")


def _label_formatter(unit: str | None):
    """Compact value-label formatter for data callouts on bars/lines."""
    def fmt(value: float) -> str:
        u = (unit or "").strip().lower()
        if u in {"%", "pct", "percent"}:
            return format_percent(value, precision=1)
        if u in {"x", "multiple"}:
            return format_multiple(value, precision=1)
        if u in {"inr cr", "cr", "₹ cr", "rs cr"}:
            if abs(value) >= 1000:
                return format_currency(value, "INR", precision=0, suffix=" Cr")
            return format_currency(value, "INR", precision=1, suffix=" Cr")
        return format_number(value, precision=1)

    return fmt


def _values_as_floats(series: FinancialSeries) -> list[float]:
    return [0.0 if value is None else float(value) for value in series.values]


def _apply_theme(ax, fig, theme: BrandTheme) -> None:
    fig.patch.set_facecolor(theme.palette.background)
    ax.set_facecolor(theme.palette.background)
    ax.tick_params(axis="x", colors=theme.palette.text, labelsize=9)
    ax.tick_params(axis="y", colors=theme.palette.text, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme.palette.muted_text)
        ax.spines[side].set_linewidth(0.8)
    ax.grid(axis="y", linestyle="--", alpha=0.25, color=theme.palette.muted_text)


def _add_bar_data_labels(ax, bars, label_fmt) -> None:
    for bar in bars:
        height = bar.get_height()
        if height == 0:
            continue
        ax.annotate(
            label_fmt(height),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def _add_line_point_labels(ax, x_positions, values, label_fmt, color: str) -> None:
    for x, y in zip(x_positions, values, strict=True):
        ax.annotate(
            label_fmt(y),
            xy=(x, y),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            color=color,
        )


def _draw_bar(ax, categories, series_data, colors, theme):
    width = 0.8 / max(len(series_data), 1)
    x_positions = list(range(len(categories)))
    primary_unit = series_data[0].unit if series_data else None
    label_fmt = _label_formatter(primary_unit)
    for index, series in enumerate(series_data):
        offsets = [x + ((index - (len(series_data) - 1) / 2) * width) for x in x_positions]
        values = _values_as_floats(series)
        bars = ax.bar(offsets, values, width=width, label=series.name, color=colors[index % len(colors)])
        if len(series_data) == 1:
            _add_bar_data_labels(ax, bars, label_fmt)
    ax.set_xticks(x_positions, categories)
    ax.yaxis.set_major_formatter(_axis_formatter(primary_unit))


def _draw_line(ax, categories, series_data, colors, theme):
    primary_unit = series_data[0].unit if series_data else None
    label_fmt = _label_formatter(primary_unit)
    x_positions = list(range(len(categories)))
    for index, series in enumerate(series_data):
        values = _values_as_floats(series)
        color = colors[index % len(colors)]
        ax.plot(x_positions, values, marker="o", linewidth=2.2, label=series.name, color=color)
        if len(series_data) == 1:
            _add_line_point_labels(ax, x_positions, values, label_fmt, color=color)
    ax.set_xticks(x_positions, categories)
    ax.yaxis.set_major_formatter(_axis_formatter(primary_unit))


def _draw_stacked_bar(ax, categories, series_data, colors, theme):
    x_positions = list(range(len(categories)))
    bottoms = [0.0] * len(categories)
    primary_unit = series_data[0].unit if series_data else None
    label_fmt = _label_formatter(primary_unit)
    for index, series in enumerate(series_data):
        values = _values_as_floats(series)
        ax.bar(x_positions, values, bottom=bottoms, label=series.name, color=colors[index % len(colors)])
        bottoms = [b + v for b, v in zip(bottoms, values, strict=True)]
    for x, total in zip(x_positions, bottoms, strict=True):
        if total == 0:
            continue
        ax.annotate(
            label_fmt(total),
            xy=(x, total),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color=theme.palette.primary,
        )
    ax.set_xticks(x_positions, categories)
    ax.yaxis.set_major_formatter(_axis_formatter(primary_unit))


def _draw_combo(ax, categories, series_data, colors, theme):
    """First series rendered as bars on the left axis; remaining as lines on a secondary axis."""
    x_positions = list(range(len(categories)))
    bar_series = series_data[0]
    bar_values = _values_as_floats(bar_series)
    bars = ax.bar(x_positions, bar_values, color=colors[0], label=bar_series.name, width=0.6)
    _add_bar_data_labels(ax, bars, _label_formatter(bar_series.unit))
    ax.set_xticks(x_positions, categories)
    ax.yaxis.set_major_formatter(_axis_formatter(bar_series.unit))
    ax.set_ylabel(bar_series.unit, color=theme.palette.text, fontsize=9)

    if len(series_data) > 1:
        ax2 = ax.twinx()
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color(theme.palette.muted_text)
        ax2.tick_params(axis="y", colors=theme.palette.text, labelsize=9)
        for index, series in enumerate(series_data[1:], start=1):
            values = _values_as_floats(series)
            color = colors[index % len(colors)]
            ax2.plot(x_positions, values, marker="o", linewidth=2, label=series.name, color=color)
        ax2.yaxis.set_major_formatter(_axis_formatter(series_data[1].unit))
        ax2.set_ylabel(series_data[1].unit, color=theme.palette.text, fontsize=9)
        # Merged legend
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")


def _draw_donut(ax, categories, series_data, colors, theme):
    series = series_data[0]
    values = _values_as_floats(series)
    total = sum(values) or 1.0
    wedges, _texts = ax.pie(
        values,
        labels=None,
        colors=colors * (len(values) // len(colors) + 1),
        wedgeprops={"width": 0.45, "edgecolor": theme.palette.background, "linewidth": 1.5},
        startangle=90,
    )
    legend_labels = [
        f"{cat} — {format_for_unit(value, series.unit)} ({(value / total) * 100:.0f}%)"
        for cat, value in zip(categories, values, strict=True)
    ]
    ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=8,
    )
    ax.set_aspect("equal")


CHART_DRAWERS = {
    "bar": _draw_bar,
    "line": _draw_line,
    "stacked_bar": _draw_stacked_bar,
    "combo": _draw_combo,
    "donut": _draw_donut,
}


def _build_chart_image(block: ChartBlock, resolver: RenderDataResolver, theme: BrandTheme) -> BytesIO:
    categories = resolver.resolve_period_labels(block.category_source)
    series_data = [resolver.resolve_series(series.source_key) for series in block.series]
    colors = _palette(theme)

    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=160)
    _apply_theme(ax, fig, theme)

    drawer = CHART_DRAWERS.get(block.chart_type, _draw_line)
    drawer(ax, categories, series_data, colors, theme)

    ax.set_title(
        block.title,
        color=theme.palette.primary,
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=10,
    )

    if block.chart_type != "donut" and len(series_data) > 1 and block.chart_type != "combo":
        ax.legend(frameon=False, fontsize=8, loc="upper left")

    source_line = f"Source: {theme.firm_name} model"
    fig.text(
        0.01,
        0.01,
        source_line,
        fontsize=7,
        color=theme.palette.muted_text,
        ha="left",
    )

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    return buffer


def render_chart_block(
    slide: Any,
    box: Box,
    block: ChartBlock,
    resolver: RenderDataResolver,
    runtime: Any,
    *,
    theme: BrandTheme,
) -> None:
    image = _build_chart_image(block, resolver, theme)
    slide.shapes.add_picture(
        image,
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        width=runtime.Inches(box.width),
        height=runtime.Inches(box.height),
    )
