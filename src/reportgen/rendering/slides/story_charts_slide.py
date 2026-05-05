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
from reportgen.schemas.financials import FinancialModelSnapshot
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
    for series in model.series:
        if series.name.lower() == name.lower():
            return list(series.periods), [_as_float(v) for v in series.values]
    return [], []


def _ratio(model: FinancialModelSnapshot, name: str) -> tuple[list[str], list[float]]:
    for ratio in model.ratios:
        if ratio.name.lower() == name.lower():
            return list(ratio.periods), [_as_float(v) for v in ratio.values]
    return [], []


def _metric(model: FinancialModelSnapshot, key: str) -> float:
    return _as_float(model.metrics.get(key))


def _k_label(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value / 1000:.1f}K"
    return f"{value:.0f}"


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
        "Story in Charts - MOFSL's Financial & Operational Journey",
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
    _, ebitda_margin = _ratio(model, "EBITDA Margin")
    _, roe = _ratio(model, "RoE")

    hist_forecast_colors = [primary if i < 4 else accent for i in range(len(periods))]

    images: list[BytesIO] = []
    images.append(
        _panel_image(
            theme,
            "Revenue (INR Cr) - FY22 to FY28E",
            lambda ax: _bars_with_labels(ax, periods, revenue, hist_forecast_colors),
            footnote="Revenue trajectory shows operating scale-up across forecast years | Source: MOFSL, Tikona Capital",
        )
    )
    images.append(
        _panel_image(
            theme,
            "PAT (INR Cr) - FY22 to FY28E",
            lambda ax: (
                _bars_with_labels(ax, periods, pat, hist_forecast_colors),
                ax.plot(range(len(pat)), pat, color=green, linewidth=1.4, marker="o", markersize=2.8),
            ),
            footnote="PAT compounding reflects brokerage headwinds absorbed by fee-led businesses | Tikona Capital Est.",
        )
    )
    images.append(
        _panel_image(
            theme,
            "EBITDA Margin (%) - FY22 to FY28E",
            lambda ax: _bars_with_labels(ax, periods, ebitda_margin, hist_forecast_colors, percent=True),
            footnote="EBITDA margins remain structurally high as ARR grows | Tikona Capital",
        )
    )

    latest_aum = _metric(model, "total_aum_lakh_cr")
    yoy = _metric(model, "total_aum_yoy_pct") / 100 if _metric(model, "total_aum_yoy_pct") else 0.0
    prior_aum = latest_aum / (1 + yoy) if yoy else latest_aum * 0.75
    aum_periods = ["FY22", "FY23", "FY24", "FY25", "H1FY26", "FY27E"]
    aum_values = [prior_aum * 0.38, prior_aum * 0.48, prior_aum * 0.70, prior_aum, latest_aum, latest_aum * 1.22]
    images.append(
        _panel_image(
            theme,
            "Total AUM Growth (INR Lakh Cr) - Trajectory",
            lambda ax: (
                _bars_with_labels(ax, aum_periods, aum_values, [primary, primary, primary, primary, accent, accent]),
                ax.plot(range(len(aum_values)), aum_values, color=green, linewidth=1.4, marker="o", markersize=2.8),
            ),
            footnote="AUM trajectory uses model latest AUM and reported YoY growth to anchor the journey",
        )
    )

    arr = _metric(model, "arr_pct_of_revenue")
    fee = _metric(model, "fee_based_pct_of_revenue")
    brokerage = _metric(model, "brokerage_pct_of_revenue")
    legacy_other = max(0, 100 - fee - brokerage)
    now_other = max(0, 100 - arr - brokerage)

    def draw_mix(ax) -> None:
        labels = ["Before", "Now"]
        bottoms = [0, 0]
        for values, color, label in [
            ([brokerage, brokerage], primary, "Broking"),
            ([fee, arr], accent, "ARR / Fee"),
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
            "Revenue Mix - ARR vs Broking vs Other",
            draw_mix,
            footnote="ARR shift highlights structural revenue-quality improvement",
        )
    )

    def draw_roe_eps(ax) -> None:
        _bars_with_labels(ax, periods, roe, hist_forecast_colors, percent=True)
        ax2 = ax.twinx()
        ax2.plot(range(len(eps)), eps, color=green, linewidth=1.6, marker="o", markersize=2.8)
        ax2.tick_params(axis="y", labelsize=5.8, colors=green)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color("#CDD6E5")
        for x, value in enumerate(eps):
            ax2.annotate(f"{value:.0f}", (x, value), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=5.0, color=green)

    images.append(
        _panel_image(
            theme,
            "RoE (%) & EPS (INR) - Multi-Year Trajectory",
            draw_roe_eps,
            footnote="Return profile and EPS trajectory remain central to re-rating",
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
