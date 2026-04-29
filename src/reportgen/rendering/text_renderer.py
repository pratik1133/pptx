from __future__ import annotations

from typing import Any

from reportgen.rendering.geometry import Box
from reportgen.rendering.overflow import fit_bullets_to_box, fit_text_to_box
from reportgen.rendering.theme import BrandTheme, FontToken


def _apply_font(run: Any, token: FontToken, runtime: Any) -> None:
    run.font.name = token.family
    run.font.size = runtime.Pt(token.size_pt)
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
    fitted_text = fit_text_to_box(text, box, token.size_pt)
    shape = slide.shapes.add_textbox(
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        runtime.Inches(box.width),
        runtime.Inches(box.height),
    )
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run()
    run.text = fitted_text
    _apply_font(run, token, runtime)
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

    for index, item in enumerate(fitted_items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.level = 0
        run = paragraph.add_run()
        run.text = f"- {item}"
        _apply_font(run, token, runtime)

    return shape
