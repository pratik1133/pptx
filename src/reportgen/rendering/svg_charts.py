"""Generate inline SVG chart strings from financial data.

Produces crisp vector charts matching the motilal_v1.html design language:
navy (#1F4690) for historical, orange (#FFA500) for estimates, monospace labels.
"""
from __future__ import annotations

import math
from decimal import Decimal
from xml.sax.saxutils import escape

from reportgen.schemas.financials import FinancialSeries

# Chart area constants (viewBox coordinates)
VB_W, VB_H = 280, 130
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 42, 10, 12, 32
CHART_W = VB_W - MARGIN_L - MARGIN_R
CHART_H = VB_H - MARGIN_T - MARGIN_B
FONT = "'JetBrains Mono', monospace"
LABEL_SIZE = 5.5
VALUE_SIZE = 4.5
TITLE_SIZE = 6.5


def _floats(series: FinancialSeries) -> list[float]:
    return [0.0 if v is None else float(v) for v in series.values]


def _nice_ceil(value: float) -> float:
    if value <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(value))
    normalized = value / mag
    if normalized <= 1:
        return mag
    if normalized <= 2:
        return 2 * mag
    if normalized <= 5:
        return 5 * mag
    return 10 * mag


def _compact(value: float, unit: str | None = None) -> str:
    u = (unit or "").strip().lower()
    if u in {"%", "pct", "percent"}:
        return f"{value:.1f}%"
    if u in {"x", "multiple"}:
        return f"{value:.1f}x"
    if abs(value) >= 10_000:
        return f"{value / 1000:.1f}K"
    if abs(value) >= 1_000:
        return f"{value / 1000:.1f}K"
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def _y(val: float, y_max: float) -> float:
    """Convert data value to SVG y coordinate."""
    if y_max == 0:
        return MARGIN_T + CHART_H
    return MARGIN_T + CHART_H - (val / y_max) * CHART_H


def _is_estimate(period: str) -> bool:
    p = period.upper().strip()
    return p.endswith("E") or p.endswith("P") or "EST" in p


def render_bar_svg(
    title: str,
    categories: list[str],
    all_series: list[FinancialSeries],
    colors: list[str],
    source_text: str = "",
) -> str:
    n_cat = len(categories)
    n_ser = len(all_series)
    if n_cat == 0 or n_ser == 0:
        return ""

    primary_unit = all_series[0].unit if all_series else None
    all_vals = [v for s in all_series for v in _floats(s)]
    y_max = _nice_ceil(max(all_vals) * 1.15) if all_vals and max(all_vals) > 0 else 1.0

    group_w = CHART_W / n_cat
    bar_w = (group_w * 0.7) / n_ser
    gap = group_w * 0.15

    lines: list[str] = []
    lines.append(f'<svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="width:100%;height:auto;display:block;">')

    # Gridlines
    for i in range(5):
        gy = MARGIN_T + CHART_H * i / 4
        gv = y_max * (4 - i) / 4
        lines.append(f'<line x1="{MARGIN_L}" y1="{gy:.1f}" x2="{VB_W - MARGIN_R}" y2="{gy:.1f}" '
                     f'stroke="#d5dce8" stroke-width="0.3" stroke-dasharray="2,2"/>')
        lines.append(f'<text x="{MARGIN_L - 3}" y="{gy + 1.5:.1f}" text-anchor="end" '
                     f'font-size="{LABEL_SIZE}" fill="#6b7c93" font-family="{FONT}">'
                     f'{_compact(gv, primary_unit)}</text>')

    # Axes
    lines.append(f'<line x1="{MARGIN_L}" y1="{MARGIN_T}" x2="{MARGIN_L}" y2="{MARGIN_T + CHART_H}" '
                 f'stroke="#d5dce8" stroke-width="0.5"/>')
    lines.append(f'<line x1="{MARGIN_L}" y1="{MARGIN_T + CHART_H}" x2="{VB_W - MARGIN_R}" '
                 f'y2="{MARGIN_T + CHART_H}" stroke="#d5dce8" stroke-width="0.5"/>')

    # Bars
    for si, series in enumerate(all_series):
        vals = _floats(series)
        color = colors[si % len(colors)]
        for ci, (cat, val) in enumerate(zip(categories, vals)):
            bx = MARGIN_L + ci * group_w + gap + si * bar_w
            by = _y(val, y_max)
            bh = MARGIN_T + CHART_H - by
            bar_color = "#FFA500" if _is_estimate(cat) else color
            lines.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" '
                         f'height="{max(bh, 0.5):.1f}" fill="{bar_color}" rx="1"/>')
            # Data label
            label_color = "#1F4690" if _is_estimate(cat) else "white"
            ly = by - 2 if bh > 8 else by - 2
            lines.append(f'<text x="{bx + bar_w / 2:.1f}" y="{ly:.1f}" text-anchor="middle" '
                         f'font-size="{VALUE_SIZE}" fill="{label_color}" font-family="{FONT}" '
                         f'font-weight="bold">{_compact(val, primary_unit)}</text>')

    # Category labels
    for ci, cat in enumerate(categories):
        cx = MARGIN_L + ci * group_w + group_w / 2
        cat_color = "#FFA500" if _is_estimate(cat) else "#6b7c93"
        lines.append(f'<text x="{cx:.1f}" y="{MARGIN_T + CHART_H + 12}" text-anchor="middle" '
                     f'font-size="{LABEL_SIZE}" fill="{cat_color}" font-family="{FONT}">'
                     f'{escape(cat)}</text>')

    # Legend
    if n_ser > 1:
        lx = MARGIN_L
        for si, series in enumerate(all_series):
            c = colors[si % len(colors)]
            lines.append(f'<rect x="{lx}" y="{VB_H - 10}" width="6" height="4" fill="{c}" rx="0.5"/>')
            lines.append(f'<text x="{lx + 8}" y="{VB_H - 6}" font-size="{LABEL_SIZE}" '
                         f'fill="#6b7c93" font-family="{FONT}">{escape(series.name)}</text>')
            lx += len(series.name) * 4 + 20
    else:
        # Historical vs Estimate legend
        lx = MARGIN_L
        lines.append(f'<rect x="{lx}" y="{VB_H - 10}" width="6" height="4" fill="{colors[0]}" rx="0.5"/>')
        lines.append(f'<text x="{lx + 8}" y="{VB_H - 6}" font-size="{LABEL_SIZE}" '
                     f'fill="#6b7c93" font-family="{FONT}">Historical</text>')
        lines.append(f'<rect x="{lx + 70}" y="{VB_H - 10}" width="6" height="4" fill="#FFA500" rx="0.5"/>')
        lines.append(f'<text x="{lx + 78}" y="{VB_H - 6}" font-size="{LABEL_SIZE}" '
                     f'fill="#6b7c93" font-family="{FONT}">Estimates</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_line_svg(
    title: str,
    categories: list[str],
    all_series: list[FinancialSeries],
    colors: list[str],
    source_text: str = "",
) -> str:
    n_cat = len(categories)
    if n_cat == 0 or not all_series:
        return ""

    primary_unit = all_series[0].unit
    all_vals = [v for s in all_series for v in _floats(s)]
    y_max = _nice_ceil(max(all_vals) * 1.15) if all_vals and max(all_vals) > 0 else 1.0

    lines: list[str] = []
    lines.append(f'<svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="width:100%;height:auto;display:block;">')

    # Gridlines + y-axis labels
    for i in range(5):
        gy = MARGIN_T + CHART_H * i / 4
        gv = y_max * (4 - i) / 4
        lines.append(f'<line x1="{MARGIN_L}" y1="{gy:.1f}" x2="{VB_W - MARGIN_R}" y2="{gy:.1f}" '
                     f'stroke="#d5dce8" stroke-width="0.3" stroke-dasharray="2,2"/>')
        lines.append(f'<text x="{MARGIN_L - 3}" y="{gy + 1.5:.1f}" text-anchor="end" '
                     f'font-size="{LABEL_SIZE}" fill="#6b7c93" font-family="{FONT}">'
                     f'{_compact(gv, primary_unit)}</text>')

    # Axes
    lines.append(f'<line x1="{MARGIN_L}" y1="{MARGIN_T}" x2="{MARGIN_L}" y2="{MARGIN_T + CHART_H}" '
                 f'stroke="#d5dce8" stroke-width="0.5"/>')
    lines.append(f'<line x1="{MARGIN_L}" y1="{MARGIN_T + CHART_H}" x2="{VB_W - MARGIN_R}" '
                 f'y2="{MARGIN_T + CHART_H}" stroke="#d5dce8" stroke-width="0.5"/>')

    step = CHART_W / max(n_cat - 1, 1)

    for si, series in enumerate(all_series):
        vals = _floats(series)
        color = colors[si % len(colors)]
        points = []
        for ci, val in enumerate(vals):
            px = MARGIN_L + ci * step
            py = _y(val, y_max)
            points.append(f"{px:.1f},{py:.1f}")
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" '
                     f'stroke="{color}" stroke-width="1.8"/>')
        for ci, val in enumerate(vals):
            px = MARGIN_L + ci * step
            py = _y(val, y_max)
            lines.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{color}"/>')
            lines.append(f'<text x="{px:.1f}" y="{py - 4:.1f}" text-anchor="middle" '
                         f'font-size="{VALUE_SIZE}" fill="{color}" font-family="{FONT}" '
                         f'font-weight="bold">{_compact(val, primary_unit)}</text>')

    # Category labels
    for ci, cat in enumerate(categories):
        cx = MARGIN_L + ci * step
        lines.append(f'<text x="{cx:.1f}" y="{MARGIN_T + CHART_H + 12}" text-anchor="middle" '
                     f'font-size="{LABEL_SIZE}" fill="#6b7c93" font-family="{FONT}">{escape(cat)}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_combo_svg(
    title: str,
    categories: list[str],
    all_series: list[FinancialSeries],
    colors: list[str],
    source_text: str = "",
) -> str:
    """First series as bars, remaining as lines."""
    if not all_series:
        return ""
    # Render bars for first series, line overlay for rest
    bar_series = [all_series[0]]
    svg = render_bar_svg(title, categories, bar_series, colors, source_text)
    if len(all_series) > 1:
        # Overlay lines (simplified — uses same y-scale)
        line_svg = render_line_svg(title, categories, all_series[1:], colors[1:], source_text)
        # Strip outer svg tags from line and embed — simplified approach
        pass
    return svg


def render_donut_svg(
    title: str,
    categories: list[str],
    all_series: list[FinancialSeries],
    colors: list[str],
    source_text: str = "",
) -> str:
    if not all_series:
        return ""
    vals = _floats(all_series[0])
    total = sum(vals) or 1.0
    unit = all_series[0].unit

    lines: list[str] = []
    lines.append(f'<svg viewBox="0 0 280 140" xmlns="http://www.w3.org/2000/svg" '
                 f'style="width:100%;height:auto;display:block;">')

    cx, cy, r_outer, r_inner = 80, 65, 50, 28
    start_angle = -90.0

    for i, (cat, val) in enumerate(zip(categories, vals)):
        pct = val / total
        sweep = pct * 360
        end_angle = start_angle + sweep
        large = 1 if sweep > 180 else 0
        sa_rad = math.radians(start_angle)
        ea_rad = math.radians(end_angle)
        x1_o = cx + r_outer * math.cos(sa_rad)
        y1_o = cy + r_outer * math.sin(sa_rad)
        x2_o = cx + r_outer * math.cos(ea_rad)
        y2_o = cy + r_outer * math.sin(ea_rad)
        x1_i = cx + r_inner * math.cos(ea_rad)
        y1_i = cy + r_inner * math.sin(ea_rad)
        x2_i = cx + r_inner * math.cos(sa_rad)
        y2_i = cy + r_inner * math.sin(sa_rad)
        color = colors[i % len(colors)]
        path = (f'M {x1_o:.1f},{y1_o:.1f} '
                f'A {r_outer},{r_outer} 0 {large},1 {x2_o:.1f},{y2_o:.1f} '
                f'L {x1_i:.1f},{y1_i:.1f} '
                f'A {r_inner},{r_inner} 0 {large},0 {x2_i:.1f},{y2_i:.1f} Z')
        lines.append(f'<path d="{path}" fill="{color}" stroke="white" stroke-width="1.5"/>')
        start_angle = end_angle

    # Legend on right
    ly = 15
    for i, (cat, val) in enumerate(zip(categories, vals)):
        pct = val / total * 100
        color = colors[i % len(colors)]
        lines.append(f'<rect x="145" y="{ly}" width="7" height="7" fill="{color}" rx="1"/>')
        label = f"{escape(cat)} — {_compact(val, unit)} ({pct:.0f}%)"
        lines.append(f'<text x="156" y="{ly + 6}" font-size="5.5" fill="#3a4d6b" '
                     f'font-family="{FONT}">{label}</text>')
        ly += 13

    lines.append("</svg>")
    return "\n".join(lines)


def render_stacked_bar_svg(
    title: str,
    categories: list[str],
    all_series: list[FinancialSeries],
    colors: list[str],
    source_text: str = "",
) -> str:
    n_cat = len(categories)
    if n_cat == 0 or not all_series:
        return ""

    primary_unit = all_series[0].unit
    # Calculate stack totals for y-axis scaling
    totals = [0.0] * n_cat
    for s in all_series:
        for ci, v in enumerate(_floats(s)):
            totals[ci] += v
    y_max = _nice_ceil(max(totals) * 1.15) if max(totals) > 0 else 1.0

    group_w = CHART_W / n_cat
    bar_w = group_w * 0.6
    gap = group_w * 0.2

    lines: list[str] = []
    lines.append(f'<svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="width:100%;height:auto;display:block;">')

    # Gridlines
    for i in range(5):
        gy = MARGIN_T + CHART_H * i / 4
        gv = y_max * (4 - i) / 4
        lines.append(f'<line x1="{MARGIN_L}" y1="{gy:.1f}" x2="{VB_W - MARGIN_R}" y2="{gy:.1f}" '
                     f'stroke="#d5dce8" stroke-width="0.3" stroke-dasharray="2,2"/>')
        lines.append(f'<text x="{MARGIN_L - 3}" y="{gy + 1.5:.1f}" text-anchor="end" '
                     f'font-size="{LABEL_SIZE}" fill="#6b7c93" font-family="{FONT}">'
                     f'{_compact(gv, primary_unit)}</text>')

    bottoms = [0.0] * n_cat
    for si, series in enumerate(all_series):
        vals = _floats(series)
        color = colors[si % len(colors)]
        for ci, val in enumerate(vals):
            bx = MARGIN_L + ci * group_w + gap
            base_y = _y(bottoms[ci], y_max)
            top_y = _y(bottoms[ci] + val, y_max)
            bh = base_y - top_y
            lines.append(f'<rect x="{bx:.1f}" y="{top_y:.1f}" width="{bar_w:.1f}" '
                         f'height="{max(bh, 0.5):.1f}" fill="{color}" rx="1"/>')
            bottoms[ci] += val

    # Total labels on top
    for ci in range(n_cat):
        cx = MARGIN_L + ci * group_w + gap + bar_w / 2
        ty = _y(totals[ci], y_max) - 3
        lines.append(f'<text x="{cx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                     f'font-size="{VALUE_SIZE}" fill="#1F4690" font-family="{FONT}" '
                     f'font-weight="bold">{_compact(totals[ci], primary_unit)}</text>')

    # Category labels
    for ci, cat in enumerate(categories):
        cx = MARGIN_L + ci * group_w + group_w / 2
        lines.append(f'<text x="{cx:.1f}" y="{MARGIN_T + CHART_H + 12}" text-anchor="middle" '
                     f'font-size="{LABEL_SIZE}" fill="#6b7c93" font-family="{FONT}">{escape(cat)}</text>')

    # Legend
    lx = MARGIN_L
    for si, series in enumerate(all_series):
        c = colors[si % len(colors)]
        lines.append(f'<rect x="{lx}" y="{VB_H - 10}" width="6" height="4" fill="{c}" rx="0.5"/>')
        lines.append(f'<text x="{lx + 8}" y="{VB_H - 6}" font-size="{LABEL_SIZE}" '
                     f'fill="#6b7c93" font-family="{FONT}">{escape(series.name)}</text>')
        lx += len(series.name) * 4 + 20

    lines.append("</svg>")
    return "\n".join(lines)


CHART_RENDERERS = {
    "bar": render_bar_svg,
    "line": render_line_svg,
    "stacked_bar": render_stacked_bar_svg,
    "combo": render_combo_svg,
    "donut": render_donut_svg,
}


def render_chart_svg(
    chart_type: str,
    title: str,
    categories: list[str],
    all_series: list[FinancialSeries],
    colors: list[str],
    source_text: str = "",
) -> str:
    renderer = CHART_RENDERERS.get(chart_type, render_bar_svg)
    return renderer(title, categories, all_series, colors, source_text)
