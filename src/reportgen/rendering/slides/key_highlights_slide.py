from __future__ import annotations

from typing import Any

from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import BulletBlock, TextBlock
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


def _clip(text: str, limit: int) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + "..."


def render_key_highlights_slide(
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
        slide_spec.title or "Key Investment Idea — Investment Thesis in Detail",
        page_number,
        theme,
        runtime,
    )

    text_block = next((b for b in slide_spec.blocks if isinstance(b, TextBlock)), None)
    bullets_block = next((b for b in slide_spec.blocks if isinstance(b, BulletBlock)), None)

    # Intro text
    intro_text = text_block.content if text_block else ""
    if intro_text:
        _add_text(slide, runtime, 0.5, 1.25, 11.33, 0.3, intro_text, font=theme.body_font.family, size=9, color=theme.palette.text, bold=False)

    highlights = []
    if bullets_block:
        for item in bullets_block.items:
            if ":" in item:
                parts = item.split(":", 1)
                highlights.append((parts[0].strip(), parts[1].strip()))
            elif " — " in item:
                parts = item.split(" — ", 1)
                highlights.append((parts[0].strip(), parts[1].strip()))
            elif " - " in item:
                parts = item.split(" - ", 1)
                highlights.append((parts[0].strip(), parts[1].strip()))
            else:
                # Fallback
                words = item.split()
                if len(words) > 6:
                    title = " ".join(words[:4])
                    body = item.strip()
                else:
                    title = "Key Point"
                    body = item.strip()
                highlights.append((title, body))

    left_x = 0.5
    top_y = 1.65
    col_w = 5.8
    row_h = 1.35
    gap_x = 0.5
    gap_y = 0.30

    colors = [theme.palette.primary, theme.palette.accent, theme.palette.secondary, theme.palette.green, "#8E24AA", "#F4511E"]

    for i, (title, body) in enumerate(highlights[:6]):
        col = i % 2
        row = i // 2
        
        x = left_x + col * (col_w + gap_x)
        y = top_y + row * (row_h + gap_y)
        
        color = colors[i % len(colors)]
        
        # Card Background
        _add_rect(slide, runtime, x, y, col_w, row_h, "#F7F9FC", line="#DDE5F0")
        # Left Accent Line
        _add_rect(slide, runtime, x, y, 0.06, row_h, color)
        
        # Number badge
        _add_rect(slide, runtime, x + 0.15, y + 0.15, 0.3, 0.3, color, radius=True)
        _add_text(slide, runtime, x + 0.15, y + 0.17, 0.3, 0.3, f"0{i+1}", font=theme.header_font.family, size=10, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
        
        # Title
        _add_text(slide, runtime, x + 0.55, y + 0.16, col_w - 0.65, 0.3, title, font=theme.header_font.family, size=11, color=color, bold=True)
        
        # Body
        _add_text(slide, runtime, x + 0.15, y + 0.55, col_w - 0.3, row_h - 0.65, _clip(body, 350), font=theme.body_font.family, size=8, color=theme.palette.text)
