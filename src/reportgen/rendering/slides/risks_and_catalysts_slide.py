from __future__ import annotations

from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import BulletBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _rgb(runtime: Any, color: str) -> Any:
    return runtime.RGBColor.from_string(color.removeprefix("#"))


def _add_rect(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    fill: str,
    *,
    line: str | None = None,
    radius: bool = False,
) -> Any:
    shape_type = runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type,
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(runtime, fill)
    if line:
        shape.line.color.rgb = _rgb(runtime, line)
        shape.line.width = runtime.Pt(0.7)
    else:
        shape.line.fill.background()
    return shape


def _add_text(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    text: str,
    *,
    font: str,
    size: float,
    color: str,
    bold: bool = False,
    align: Any | None = None,
    valign: Any | None = None,
) -> Any:
    box = slide.shapes.add_textbox(
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    if valign:
        frame.vertical_anchor = valign
    frame.margin_left = runtime.Inches(0.04)
    frame.margin_right = runtime.Inches(0.04)
    frame.margin_top = runtime.Inches(0.01)
    frame.margin_bottom = runtime.Inches(0.01)
    paragraph = frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = runtime.Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(runtime, color)
    return box


def _add_rich_text(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    runs: list[tuple[str, str, float, str, bool]],
    *,
    align: Any | None = None,
    valign: Any | None = None,
) -> Any:
    box = slide.shapes.add_textbox(
        runtime.Inches(left),
        runtime.Inches(top),
        runtime.Inches(width),
        runtime.Inches(height),
    )
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    if valign:
        frame.vertical_anchor = valign
    frame.margin_left = runtime.Inches(0.04)
    frame.margin_right = runtime.Inches(0.04)
    frame.margin_top = runtime.Inches(0.01)
    frame.margin_bottom = runtime.Inches(0.01)
    paragraph = frame.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    
    for text, font, size, color, bold in runs:
        run = paragraph.add_run()
        run.text = text
        run.font.name = font
        run.font.size = runtime.Pt(size)
        run.font.bold = bold
        run.font.color.rgb = _rgb(runtime, color)
    return box


def _add_risk_item(
    slide: Any,
    runtime: Any,
    left: float,
    top: float,
    width: float,
    tag: str,
    title: str,
    description: str,
    theme: BrandTheme,
    height_estimate: float = 0.6
):
    if tag == "HIGH":
        tag_bg = "#FEE2E2"
        tag_fg = "#DC2626"
    elif tag == "MED":
        tag_bg = "#FEF3C7"
        tag_fg = "#D97706"
    else: # LOW
        tag_bg = "#DCFCE7"
        tag_fg = "#166534"
        
    tag_width = 0.45
    tag_height = 0.15
    tag_top = top + 0.03
    
    _add_rect(slide, runtime, left, tag_top, tag_width, tag_height, tag_bg, radius=True)
    _add_text(slide, runtime, left, tag_top, tag_width, tag_height, tag, font=theme.body_font.family, size=6.5, color=tag_fg, bold=True, align=runtime.PP_ALIGN.CENTER, valign=runtime.MSO_ANCHOR.MIDDLE)
    
    text_left = left + tag_width + 0.1
    text_width = width - tag_width - 0.1
    
    runs = [
        (title + " ", theme.header_font.family, 8.5, theme.palette.primary, True),
        (description, theme.body_font.family, 8.5, theme.palette.text, False)
    ]
    
    _add_rich_text(slide, runtime, text_left, top, text_width, height_estimate, runs)


def render_risks_and_catalysts_slide(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
    *,
    page_number: int,
) -> None:
    render_section_header(
        slide,
        Box(left=0.5, top=0.6, width=12.333, height=0.55),
        slide_spec.title,
        page_number,
        theme,
        runtime,
    )

    left_col_x = 0.5
    right_col_x = 6.8
    col_width = 6.0
    top_y = 1.3

    _add_text(slide, runtime, left_col_x, top_y, col_width, 0.25, "KEY RISKS", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, left_col_x, top_y + 0.25, col_width, 0.015, theme.palette.secondary)
    
    _add_text(slide, runtime, right_col_x, top_y, col_width, 0.25, "THESIS INVALIDATION TRIGGERS", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right_col_x, top_y + 0.25, col_width, 0.015, theme.palette.secondary)

    bullets = []
    for block in slide_spec.blocks:
        if isinstance(block, BulletBlock):
            bullets.extend(block.items)

    y_offset_left = top_y + 0.35
    y_offset_right = top_y + 0.35
    
    for i, item in enumerate(bullets):
        # Extract tag and title if possible
        tag = "MED"
        title = f"Risk Factor {i+1}"
        desc = item
        
        parts = item.split(":", 1)
        if len(parts) == 2:
            title = parts[0].strip()
            desc = parts[1].strip()
            
        if "high" in title.lower() or "high" in desc.lower()[:30]:
            tag = "HIGH"
        elif "low" in title.lower() or "low" in desc.lower()[:30]:
            tag = "LOW"
            
        # Distribute left and right
        if i % 2 == 0:
            _add_risk_item(slide, runtime, left_col_x, y_offset_left, col_width, tag, title, desc, theme, 0.7)
            y_offset_left += 0.8
            _add_rect(slide, runtime, left_col_x, y_offset_left - 0.05, col_width, 0.01, "#E2E8F0")
        else:
            _add_risk_item(slide, runtime, right_col_x, y_offset_right, col_width, tag, title, desc, theme, 0.7)
            y_offset_right += 0.8
            _add_rect(slide, runtime, right_col_x, y_offset_right - 0.05, col_width, 0.01, "#E2E8F0")

