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
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = family
    run.font.size = runtime.Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = _hex_to_rgb(runtime, color_hex)
    return box


def _format_date_ddmmyyyy(report_date: str) -> str:
    """Convert date string to DD/MM/YYYY format.

    Accepts ISO format (YYYY-MM-DD) or already formatted dates.
    """
    try:
        from datetime import date as dt_date, datetime

        if isinstance(report_date, dt_date):
            return report_date.strftime("%d/%m/%Y")
        parsed = datetime.strptime(str(report_date).strip(), "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(report_date)


def _format_market_cap(market_cap) -> str:
    """Format market cap for display (e.g., ₹49,079 Cr).

    Accepts either:
    - Raw INR value (e.g., 490790000000) → divides by 1 crore
    - Already in crores (e.g., 49079) → uses directly
    """
    try:
        val = float(market_cap)
        # If > 10 lakh (1,000,000), it's likely raw INR — convert to crores
        if val >= 1_000_000:
            val = val / 1_00_00_000  # divide by 1 crore
        if val >= 100:
            return f"₹{val:,.0f} Cr"
        return f"₹{val:,.1f} Cr"
    except (ValueError, TypeError):
        return ""


def _format_currency_compact(value) -> str:
    """Format currency value compactly (e.g., ₹822.90)."""
    try:
        val = float(value)
        if val == int(val):
            return f"₹{val:,.0f}"
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


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
    company_name: str = "",
    section_title: str = "",
    cmp: str = "",
    target_price: str = "",
    upside_pct: str = "",
    market_cap: str = "",
    rating: str = "",
) -> None:
    apply_background(slide, theme, runtime)
    canvas_w = theme.canvas.width_in
    canvas_h = theme.canvas.height_in
    shell = theme.shell

    # ── Navy header bar ──
    _add_filled_rect(slide, runtime, 0, 0, canvas_w, shell.header_height_in, theme.palette.primary)

    # Logo
    logo_path = Path(theme.logo_path) if theme.logo_path else None
    logo_exists = bool(logo_path and logo_path.exists())
    logo_inset = shell.side_margin_in
    if logo_exists:
        try:
            chip_pad_x = 0.16
            chip_height = shell.header_height_in
            chip_width = 1.7 + 2 * chip_pad_x  # initial width
            chip_top = 0
            chip = slide.shapes.add_shape(
                runtime.MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                runtime.Inches(logo_inset - chip_pad_x),
                runtime.Inches(chip_top),
                runtime.Inches(chip_width),
                runtime.Inches(chip_height),
            )
            chip.fill.solid()
            chip.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.background)
            # Remove line/border entirely to make it blend well
            chip.line.fill.background()
            
            logo_top = (shell.header_height_in - shell.logo_height_in) / 2
            pic = slide.shapes.add_picture(
                str(logo_path),
                runtime.Inches(logo_inset),
                runtime.Inches(logo_top),
                height=runtime.Inches(shell.logo_height_in),
            )
            # Adjust the background rectangle width to perfectly wrap the logo
            chip.width = pic.width + int(runtime.Inches(2 * chip_pad_x))
        except Exception:
            pass

    # ── Left: Firm name (accent color, bold) ──
    if not logo_exists:
        _add_text_in_rect(
            slide,
            runtime,
            shell.side_margin_in,
            0,
            2.0,
            shell.header_height_in,
            theme.firm_name,
            theme.header_font.family,
            9,
            True,
            theme.palette.accent,
            runtime.PP_ALIGN.LEFT,
        )

    # ── Center: Company Name — Section Title ──
    center_text = company_name
    if section_title:
        center_text = f"{company_name} — {section_title}"
    center_left = shell.side_margin_in + (1.9 if logo_exists else 2.1)
    center_width = canvas_w - center_left - 5.5
    if center_width > 0:
        _add_text_in_rect(
            slide,
            runtime,
            center_left,
            0,
            center_width,
            shell.header_height_in,
            center_text,
            theme.title_font.family,
            10,
            True,
            "#FFFFFF",
            runtime.PP_ALIGN.LEFT,
        )

    # ── Right: Stats pills (CMP | TP | Upside | Mkt Cap | Rating) ──
    stats_parts = []
    if cmp:
        stats_parts.append(f"CMP {_format_currency_compact(cmp)}")
    if target_price:
        stats_parts.append(f"TP {_format_currency_compact(target_price)}")
    if upside_pct:
        try:
            up = float(upside_pct)
            stats_parts.append(f"UPSIDE {'+' if up > 0 else ''}{up:.0f}%")
        except (ValueError, TypeError):
            stats_parts.append(f"UPSIDE {upside_pct}")
    if market_cap:
        stats_parts.append(f"MKT CAP {_format_market_cap(market_cap)}")

    stats_text = "  |  ".join(stats_parts)
    stats_right_width = 5.0
    stats_right_left = canvas_w - stats_right_width - shell.side_margin_in - 0.7

    if stats_parts:
        _add_text_in_rect(
            slide,
            runtime,
            stats_right_left,
            0,
            stats_right_width,
            shell.header_height_in,
            stats_text,
            theme.header_font.family,
            8,
            False,
            "#FFFFFF",
            runtime.PP_ALIGN.RIGHT,
        )

    # ── Rating badge (inline, right edge) ──
    if rating:
        badge_w = 0.55
        badge_h = 0.22
        badge_left = canvas_w - badge_w - shell.side_margin_in
        badge_top = (shell.header_height_in - badge_h) / 2
        rating_key = rating.upper().strip()
        badge_bg = getattr(theme.rating_colors, rating_key, theme.palette.accent)
        badge = slide.shapes.add_shape(
            runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            runtime.Inches(badge_left),
            runtime.Inches(badge_top),
            runtime.Inches(badge_w),
            runtime.Inches(badge_h),
        )
        badge.fill.solid()
        badge.fill.fore_color.rgb = _hex_to_rgb(runtime, badge_bg)
        badge.line.fill.background()
        tf = badge.text_frame
        tf.margin_left = runtime.Inches(0.02)
        tf.margin_right = runtime.Inches(0.02)
        tf.margin_top = runtime.Inches(0.01)
        tf.margin_bottom = runtime.Inches(0.01)
        p = tf.paragraphs[0]
        p.alignment = runtime.PP_ALIGN.CENTER
        r = p.add_run()
        r.text = rating_key
        r.font.name = theme.header_font.family
        r.font.size = runtime.Pt(8)
        r.font.bold = True
        r.font.color.rgb = _hex_to_rgb(runtime, "#FFFFFF")

    # ── Orange accent divider below header ──
    divider_top = shell.header_height_in
    _add_filled_rect(
        slide,
        runtime,
        0,
        divider_top,
        canvas_w,
        0.04,
        theme.palette.accent,
    )

    # ── Footer ──
    footer_top = canvas_h - shell.footer_height_in
    _add_filled_rect(slide, runtime, 0, footer_top, canvas_w, shell.footer_height_in, theme.palette.primary)

    # Footer left: SEBI info
    formatted_date = _format_date_ddmmyyyy(report_date)
    footer_line = theme.footer_line
    if logo_exists and footer_line.casefold().startswith(theme.firm_name.casefold()):
        footer_line = footer_line[len(theme.firm_name):].lstrip(" |")

    _add_text_in_rect(
        slide,
        runtime,
        shell.side_margin_in,
        footer_top,
        canvas_w * 0.3,
        shell.footer_height_in,
        footer_line,
        theme.footer_font.family,
        theme.footer_font.size_pt,
        theme.footer_font.bold,
        theme.footer_font.color_hex,
        runtime.PP_ALIGN.LEFT,
    )

    # Footer center: Company name — Equity Research
    footer_center_text = f"{company_name} — Equity Research" if company_name else theme.firm_name
    _add_text_in_rect(
        slide,
        runtime,
        canvas_w * 0.3,
        footer_top,
        canvas_w * 0.4,
        shell.footer_height_in,
        footer_center_text,
        theme.footer_font.family,
        theme.footer_font.size_pt,
        True,
        theme.palette.accent,
        runtime.PP_ALIGN.CENTER,
    )

    # Footer right: Date + Page
    _add_text_in_rect(
        slide,
        runtime,
        canvas_w - 2.0 - shell.side_margin_in,
        footer_top,
        2.0,
        shell.footer_height_in,
        f"{formatted_date}  |  Page {page_number} of {total_pages}",
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
