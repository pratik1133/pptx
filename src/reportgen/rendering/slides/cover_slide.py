from __future__ import annotations

from typing import Any

from reportgen.rendering.brand_shell import apply_cover_shell
from reportgen.rendering.components.rating_badge import render_rating_badge
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import MetricsBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _hex_to_rgb(runtime: Any, hex_color: str) -> Any:
    return runtime.RGBColor.from_string(hex_color.removeprefix("#"))


def render_cover_slide(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
) -> None:
    apply_cover_shell(slide, theme, runtime)
    canvas_w = theme.canvas.width_in
    canvas_h = theme.canvas.height_in

    title_box = slide.shapes.add_textbox(
        runtime.Inches(0.6),
        runtime.Inches(1.5),
        runtime.Inches(canvas_w - 1.2),
        runtime.Inches(1.4),
    )
    frame = title_box.text_frame
    frame.word_wrap = True
    p = frame.paragraphs[0]
    run = p.add_run()
    run.text = slide_spec.title
    run.font.name = theme.title_font.family
    run.font.size = runtime.Pt(40)
    run.font.bold = True
    run.font.color.rgb = _hex_to_rgb(runtime, theme.palette.text_on_primary)

    if slide_spec.subtitle:
        sub_box = slide.shapes.add_textbox(
            runtime.Inches(0.6),
            runtime.Inches(2.95),
            runtime.Inches(canvas_w - 1.2),
            runtime.Inches(0.6),
        )
        sp = sub_box.text_frame.paragraphs[0]
        srun = sp.add_run()
        srun.text = slide_spec.subtitle
        srun.font.name = theme.subtitle_font.family
        srun.font.size = runtime.Pt(18)
        srun.font.bold = False
        srun.font.color.rgb = _hex_to_rgb(runtime, theme.palette.soft)

    rating = (report_spec.metadata.rating or "").upper()
    if rating:
        render_rating_badge(
            slide,
            Box(left=canvas_w - 2.4, top=0.6, width=1.8, height=0.55),
            rating,
            theme,
            runtime,
        )

    _render_cover_metrics(slide, slide_spec, theme, runtime, canvas_h)


def _render_cover_metrics(
    slide: Any,
    slide_spec: SlideSpec,
    theme: BrandTheme,
    runtime: Any,
    canvas_h: float,
) -> None:
    metrics_block = next(
        (b for b in slide_spec.blocks if isinstance(b, MetricsBlock)),
        None,
    )
    if not metrics_block or not metrics_block.items:
        return

    items = list(metrics_block.items)
    n = len(items)
    canvas_w = theme.canvas.width_in
    side = 0.6
    gap = 0.3
    total_w = canvas_w - 2 * side
    card_w = (total_w - gap * (n - 1)) / n
    card_h = 1.1
    card_top = canvas_h - card_h - 0.85

    for index, item in enumerate(items):
        left = side + index * (card_w + gap)
        card = slide.shapes.add_shape(
            runtime.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            runtime.Inches(left),
            runtime.Inches(card_top),
            runtime.Inches(card_w),
            runtime.Inches(card_h),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = _hex_to_rgb(runtime, theme.palette.background)
        card.line.color.rgb = _hex_to_rgb(runtime, theme.palette.accent)
        card.line.width = runtime.Pt(1.25)

        tf = card.text_frame
        tf.margin_left = runtime.Inches(0.1)
        tf.margin_right = runtime.Inches(0.1)
        tf.margin_top = runtime.Inches(0.08)
        tf.margin_bottom = runtime.Inches(0.08)
        p_label = tf.paragraphs[0]
        p_label.alignment = runtime.PP_ALIGN.CENTER
        rl = p_label.add_run()
        rl.text = item.label
        rl.font.name = theme.body_font.family
        rl.font.size = runtime.Pt(11)
        rl.font.bold = False
        rl.font.color.rgb = _hex_to_rgb(runtime, theme.palette.muted_text)

        p_val = tf.add_paragraph()
        p_val.alignment = runtime.PP_ALIGN.CENTER
        rv = p_val.add_run()
        rv.text = str(item.value) if item.value is not None else ""
        rv.font.name = theme.metric_font.family
        rv.font.size = runtime.Pt(20)
        rv.font.bold = True
        rv.font.color.rgb = _hex_to_rgb(runtime, theme.palette.primary)
