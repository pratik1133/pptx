from __future__ import annotations

from io import BytesIO
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.charts import ChartBlock


def _build_chart_image(block: ChartBlock, resolver: RenderDataResolver, theme: BrandTheme) -> BytesIO:
    categories = resolver.resolve_period_labels(block.category_source)
    series_data = [resolver.resolve_series(series.source_key) for series in block.series]

    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=160)
    fig.patch.set_facecolor(theme.palette.background)
    ax.set_facecolor(theme.palette.background)

    colors = [theme.palette.primary, theme.palette.secondary, theme.palette.accent]

    if block.chart_type == "bar":
        width = 0.8 / max(len(series_data), 1)
        x_positions = list(range(len(categories)))
        for index, series in enumerate(series_data):
            offsets = [x + ((index - (len(series_data) - 1) / 2) * width) for x in x_positions]
            values = [0 if value is None else float(value) for value in series.values]
            ax.bar(offsets, values, width=width, label=series.name, color=colors[index % len(colors)])
        ax.set_xticks(x_positions, categories)
    elif block.chart_type == "line":
        for index, series in enumerate(series_data):
            values = [0 if value is None else float(value) for value in series.values]
            ax.plot(categories, values, marker="o", linewidth=2, label=series.name, color=colors[index % len(colors)])
    elif block.chart_type == "donut":
        series = series_data[0]
        values = [0 if value is None else float(value) for value in series.values]
        ax.pie(
            values,
            labels=categories,
            colors=colors * max(1, len(values)),
            wedgeprops={"width": 0.45, "edgecolor": theme.palette.background},
        )
    else:
        for index, series in enumerate(series_data):
            values = [0 if value is None else float(value) for value in series.values]
            ax.plot(categories, values, marker="o", linewidth=2, label=series.name, color=colors[index % len(colors)])

    ax.set_title(block.title, color=theme.palette.primary, fontsize=12, fontweight="bold")
    ax.tick_params(axis="x", colors=theme.palette.text, labelsize=9)
    ax.tick_params(axis="y", colors=theme.palette.text, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(theme.palette.muted_text)

    if block.chart_type != "donut":
        ax.grid(axis="y", linestyle="--", alpha=0.25)
        if len(series_data) > 1:
            ax.legend(frameon=False, fontsize=8)

    fig.tight_layout()
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
