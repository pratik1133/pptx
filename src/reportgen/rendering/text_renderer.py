from __future__ import annotations

from typing import Any

from reportgen.rendering.geometry import Box
from reportgen.rendering.overflow import autoshrink_text, fit_bullets_to_box
from reportgen.rendering.theme import BrandTheme, FontToken


def _apply_font(run: Any, token: FontToken, runtime: Any, *, size_override_pt: int | None = None) -> None:
    run.font.name = token.family
    run.font.size = runtime.Pt(size_override_pt if size_override_pt else token.size_pt)
    run.font.bold = token.bold
    run.font.color.rgb = runtime.RGBColor.from_string(token.color_hex.removeprefix("#"))


def add_textbox(
    slide: Any,
    box: Box,
    text: str,
    token: FontToken,
    runtime: Any,
    *,
    theme: BrandTheme,
    align: Any | None = None,
) -> Any:
    shrink = autoshrink_text(text, box, token.size_pt)
    shape = slide.shapes.add_textbox(
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        runtime.Inches(box.width),
        runtime.Inches(box.height),
    )
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = runtime.MSO_ANCHOR.TOP
    frame.margin_left = runtime.Inches(0.05)
    frame.margin_right = runtime.Inches(0.05)
    frame.margin_top = runtime.Inches(0.02)
    frame.margin_bottom = runtime.Inches(0.02)
    paragraph = frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run()
    run.text = shrink.text
    _apply_font(run, token, runtime, size_override_pt=shrink.font_size_pt)
    return shape


def add_bullet_list(
    slide: Any,
    box: Box,
    items: list[str],
    token: FontToken,
    runtime: Any,
    *,
    theme: BrandTheme,
) -> Any:
    fitted_items = fit_bullets_to_box(items, box, token.size_pt)
    shape = slide.shapes.add_textbox(
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        runtime.Inches(box.width),
        runtime.Inches(box.height),
    )
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = runtime.MSO_ANCHOR.TOP
    frame.margin_left = runtime.Inches(0.05)
    frame.margin_right = runtime.Inches(0.05)
    frame.margin_top = runtime.Inches(0.02)
    frame.margin_bottom = runtime.Inches(0.02)

    for index, item in enumerate(fitted_items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.level = 0
        paragraph.space_after = runtime.Pt(4)
        run = paragraph.add_run()
        run.text = f"•  {item}"
        _apply_font(run, token, runtime)

    return shape
