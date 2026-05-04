from __future__ import annotations

from typing import Any

from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme


def render_rating_badge(
    slide: Any,
    box: Box,
    rating: str,
    theme: BrandTheme,
    runtime: Any,
) -> Any:
    rating_key = rating.upper().strip()
    color_hex = getattr(theme.rating_colors, rating_key, theme.palette.primary)

    shape = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        runtime.Inches(box.width),
        runtime.Inches(box.height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = runtime.RGBColor.from_string(color_hex.removeprefix("#"))
    shape.line.fill.background()

    text_frame = shape.text_frame
    text_frame.margin_left = runtime.Inches(0.05)
    text_frame.margin_right = runtime.Inches(0.05)
    text_frame.margin_top = runtime.Inches(0.02)
    text_frame.margin_bottom = runtime.Inches(0.02)
    paragraph = text_frame.paragraphs[0]
    paragraph.alignment = runtime.PP_ALIGN.CENTER
    run = paragraph.add_run()
    run.text = rating_key
    token = theme.rating_badge_font
    run.font.name = token.family
    run.font.size = runtime.Pt(token.size_pt)
    run.font.bold = token.bold
    run.font.color.rgb = runtime.RGBColor.from_string(token.color_hex.removeprefix("#"))
    return shape
