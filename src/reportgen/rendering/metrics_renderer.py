from __future__ import annotations

from typing import Any

from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import MetricsBlock


def _hex_to_rgb(runtime: Any, hex_color: str) -> Any:
    return runtime.RGBColor.from_string(hex_color.removeprefix("#"))


def render_metrics_block(
    slide: Any,
    box: Box,
    block: MetricsBlock,
    runtime: Any,
    *,
    theme: BrandTheme,
) -> None:
    """Render metric cards with colored backgrounds matching the HTML .metric-card style.

    Alternates between navy, accent, mid-blue, and teal backgrounds.
    """
    item_count = len(block.items)
    gap = 0.12
    column_width = (box.width - gap * (item_count - 1)) / max(item_count, 1)
    card_h = min(box.height, 1.1)

    # Color rotation for card backgrounds
    bg_colors = [
        theme.palette.primary,    # navy
        theme.palette.accent,     # orange
        theme.palette.secondary,  # mid-blue
        theme.palette.teal,       # teal
        theme.palette.primary,    # navy (repeat)
        theme.palette.accent,     # orange (repeat)
        theme.palette.secondary,
        theme.palette.teal,
    ]

    for index, item in enumerate(block.items):
        left = box.left + index * (column_width + gap)
        bg = bg_colors[index % len(bg_colors)]
        is_accent_bg = bg == theme.palette.accent

        # Card shape
        card = slide.shapes.add_shape(
            runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            runtime.Inches(left),
            runtime.Inches(box.top),
            runtime.Inches(column_width),
            runtime.Inches(card_h),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = _hex_to_rgb(runtime, bg)
        card.line.fill.background()

        # Text colors
        label_color = theme.palette.primary if is_accent_bg else "#C0C8D4"
        value_color = theme.palette.primary if is_accent_bg else "#FFFFFF"

        tf = card.text_frame
        tf.margin_left = runtime.Inches(0.08)
        tf.margin_right = runtime.Inches(0.08)
        tf.margin_top = runtime.Inches(0.1)
        tf.margin_bottom = runtime.Inches(0.05)

        # Label (small, uppercase)
        p_label = tf.paragraphs[0]
        p_label.alignment = runtime.PP_ALIGN.CENTER
        p_label.space_after = runtime.Pt(2)
        rl = p_label.add_run()
        rl.text = item.label.upper()
        rl.font.name = theme.body_font.family
        rl.font.size = runtime.Pt(8)
        rl.font.bold = False
        rl.font.color.rgb = _hex_to_rgb(runtime, label_color)

        # Value (large, bold)
        p_val = tf.add_paragraph()
        p_val.alignment = runtime.PP_ALIGN.CENTER
        rv = p_val.add_run()
        rv.text = str(item.value) if item.value is not None else ""
        rv.font.name = theme.metric_font.family
        rv.font.size = runtime.Pt(16)
        rv.font.bold = True
        rv.font.color.rgb = _hex_to_rgb(runtime, value_color)
