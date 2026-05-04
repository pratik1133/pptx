"""Section header with numbered badge, matching the HTML report's .section-header style.

Renders: [02] Investment Thesis & Key Catalysts
         ─── orange divider ───────────────────
"""
from __future__ import annotations

from typing import Any

from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme


def _hex_to_rgb(runtime: Any, hex_color: str) -> Any:
    return runtime.RGBColor.from_string(hex_color.removeprefix("#"))


def render_section_header(
    slide: Any,
    box: Box,
    title: str,
    page_number: int,
    theme: BrandTheme,
    runtime: Any,
) -> None:
    """Render a section header with a numbered badge and orange underline.

    Layout:
        ┌──────┐
        │  02  │  Investment Thesis & Key Catalysts
        └──────┘
        ──────────── orange line ────────────────
    """
    badge_w = 0.45
    badge_h = 0.3
    badge_gap = 0.12

    # ── Number badge (navy background, orange/accent text) ──
    badge = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        runtime.Inches(box.left),
        runtime.Inches(box.top + (box.height - badge_h) / 2),
        runtime.Inches(badge_w),
        runtime.Inches(badge_h),
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.primary)
    badge.line.fill.background()

    badge_tf = badge.text_frame
    badge_tf.margin_left = runtime.Inches(0.02)
    badge_tf.margin_right = runtime.Inches(0.02)
    badge_tf.margin_top = runtime.Inches(0.01)
    badge_tf.margin_bottom = runtime.Inches(0.01)
    p = badge_tf.paragraphs[0]
    p.alignment = runtime.PP_ALIGN.CENTER
    r = p.add_run()
    r.text = f"{page_number:02d}"
    r.font.name = theme.section_number_font.family
    r.font.size = runtime.Pt(theme.section_number_font.size_pt)
    r.font.bold = True
    r.font.color.rgb = _hex_to_rgb(runtime, theme.palette.accent)

    # ── Title text (to the right of badge) ──
    title_left = box.left + badge_w + badge_gap
    title_w = box.width - badge_w - badge_gap
    title_box = slide.shapes.add_textbox(
        runtime.Inches(title_left),
        runtime.Inches(box.top),
        runtime.Inches(title_w),
        runtime.Inches(box.height),
    )
    frame = title_box.text_frame
    frame.word_wrap = True
    frame.margin_left = runtime.Inches(0.02)
    frame.margin_top = runtime.Inches(0.02)
    p = frame.paragraphs[0]
    run = p.add_run()
    run.text = title
    run.font.name = theme.title_font.family
    run.font.size = runtime.Pt(theme.title_font.size_pt)
    run.font.bold = True
    run.font.color.rgb = _hex_to_rgb(runtime, theme.palette.primary)

    # ── Orange divider line below ──
    line_top = box.top + box.height + 0.03
    line = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        runtime.Inches(box.left),
        runtime.Inches(line_top),
        runtime.Inches(box.width),
        runtime.Inches(0.025),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.primary)
    line.line.fill.background()
