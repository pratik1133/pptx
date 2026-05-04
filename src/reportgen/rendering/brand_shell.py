from __future__ import annotations

from pathlib import Path
from typing import Any

from reportgen.rendering.theme import BrandTheme


def _hex_to_rgb(runtime: Any, hex_color: str) -> Any:
    return runtime.RGBColor.from_string(hex_color.removeprefix("#"))


def apply_background(slide: Any, theme: BrandTheme, runtime: Any) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.background)


def _add_filled_rect(
    slide: Any,
    runtime: Any,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
    color_hex: str,
) -> Any:
    shape = slide.shapes.add_shape(
        runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        runtime.Inches(left_in),
        runtime.Inches(top_in),
        runtime.Inches(width_in),
        runtime.Inches(height_in),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _hex_to_rgb(runtime, color_hex)
    shape.line.fill.background()
    return shape


def _add_text_in_rect(
    slide: Any,
    runtime: Any,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
    text: str,
    family: str,
    size_pt: int,
    bold: bool,
    color_hex: str,
    align: Any,
) -> Any:
    box = slide.shapes.add_textbox(
        runtime.Inches(left_in),
        runtime.Inches(top_in),
        runtime.Inches(width_in),
        runtime.Inches(height_in),
    )
    frame = box.text_frame
    frame.margin_left = runtime.Inches(0.05)
    frame.margin_right = runtime.Inches(0.05)
    frame.margin_top = runtime.Inches(0.02)
    frame.margin_bottom = runtime.Inches(0.02)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = family
    run.font.size = runtime.Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = _hex_to_rgb(runtime, color_hex)
    return box


def apply_interior_shell(
    slide: Any,
    theme: BrandTheme,
    runtime: Any,
    *,
    page_number: int,
    total_pages: int,
    ticker: str,
    analyst: str,
    report_date: str,
) -> None:
    apply_background(slide, theme, runtime)
    canvas_w = theme.canvas.width_in
    canvas_h = theme.canvas.height_in
    shell = theme.shell

    _add_filled_rect(slide, runtime, 0, 0, canvas_w, shell.header_height_in, theme.palette.primary)

    logo_path = Path(theme.logo_path) if theme.logo_path else None
    logo_inset = shell.side_margin_in
    if logo_path and logo_path.exists():
        try:
            chip_pad_x = 0.08
            chip_pad_y = 0.06
            chip_height = shell.logo_height_in + 2 * chip_pad_y
            chip_width = 1.7 + 2 * chip_pad_x
            chip_top = (shell.header_height_in - chip_height) / 2
            chip = slide.shapes.add_shape(
                runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
                runtime.Inches(logo_inset - chip_pad_x),
                runtime.Inches(chip_top),
                runtime.Inches(chip_width),
                runtime.Inches(chip_height),
            )
            chip.fill.solid()
            chip.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.background)
            chip.line.fill.background()
            slide.shapes.add_picture(
                str(logo_path),
                runtime.Inches(logo_inset),
                runtime.Inches((shell.header_height_in - shell.logo_height_in) / 2),
                height=runtime.Inches(shell.logo_height_in),
            )
        except Exception:
            pass

    _add_text_in_rect(
        slide,
        runtime,
        canvas_w - 4.0 - shell.side_margin_in,
        0,
        4.0,
        shell.header_height_in,
        f"{ticker}  |  {analyst}  |  {report_date}",
        theme.header_font.family,
        theme.header_font.size_pt,
        theme.header_font.bold,
        theme.header_font.color_hex,
        runtime.PP_ALIGN.RIGHT,
    )

    divider_top = shell.title_top_in + shell.title_height_in + 0.05
    _add_filled_rect(
        slide,
        runtime,
        shell.side_margin_in,
        divider_top,
        canvas_w - 2 * shell.side_margin_in,
        shell.divider_thickness_pt / 72.0,
        theme.palette.accent,
    )

    footer_top = canvas_h - shell.footer_height_in
    _add_filled_rect(slide, runtime, 0, footer_top, canvas_w, shell.footer_height_in, theme.palette.primary)

    _add_text_in_rect(
        slide,
        runtime,
        shell.side_margin_in,
        footer_top,
        canvas_w - 2 * shell.side_margin_in - 1.5,
        shell.footer_height_in,
        theme.footer_line,
        theme.footer_font.family,
        theme.footer_font.size_pt,
        theme.footer_font.bold,
        theme.footer_font.color_hex,
        runtime.PP_ALIGN.LEFT,
    )

    _add_text_in_rect(
        slide,
        runtime,
        canvas_w - 1.5 - shell.side_margin_in,
        footer_top,
        1.5,
        shell.footer_height_in,
        f"Page {page_number} of {total_pages}",
        theme.footer_font.family,
        theme.footer_font.size_pt,
        theme.footer_font.bold,
        theme.footer_font.color_hex,
        runtime.PP_ALIGN.RIGHT,
    )


def apply_cover_shell(slide: Any, theme: BrandTheme, runtime: Any) -> None:
    apply_background(slide, theme, runtime)
    canvas_w = theme.canvas.width_in
    canvas_h = theme.canvas.height_in

    _add_filled_rect(slide, runtime, 0, 0, canvas_w, canvas_h * 0.55, theme.palette.primary)
    _add_filled_rect(slide, runtime, 0, canvas_h * 0.55, canvas_w, 0.06, theme.palette.accent)

    logo_path = Path(theme.logo_path) if theme.logo_path else None
    if logo_path and logo_path.exists():
        try:
            chip_left = 0.42
            chip_top = 0.38
            chip_width = 2.7
            chip_height = 0.72
            chip = slide.shapes.add_shape(
                runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
                runtime.Inches(chip_left),
                runtime.Inches(chip_top),
                runtime.Inches(chip_width),
                runtime.Inches(chip_height),
            )
            chip.fill.solid()
            chip.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.background)
            chip.line.fill.background()
            slide.shapes.add_picture(
                str(logo_path),
                runtime.Inches(0.5),
                runtime.Inches(0.45),
                height=runtime.Inches(0.55),
            )
        except Exception:
            pass

    _add_filled_rect(slide, runtime, 0, canvas_h - 0.45, canvas_w, 0.45, theme.palette.primary)
    _add_text_in_rect(
        slide,
        runtime,
        0.5,
        canvas_h - 0.45,
        canvas_w - 1.0,
        0.45,
        theme.footer_line,
        theme.footer_font.family,
        theme.footer_font.size_pt,
        theme.footer_font.bold,
        theme.footer_font.color_hex,
        runtime.PP_ALIGN.LEFT,
    )
