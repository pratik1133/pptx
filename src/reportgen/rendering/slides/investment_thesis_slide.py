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


def _score_parts(score_text: str) -> tuple[int, int]:
    try:
        raw, max_raw = str(score_text).split("/", 1)
        return int(raw.strip()), int(max_raw.strip())
    except (ValueError, TypeError):
        return 0, 1


def _bar_color(score: int, max_score: int, theme: BrandTheme) -> str:
    ratio = score / max(max_score, 1)
    if ratio >= 0.80:
        return theme.palette.green
    if ratio >= 0.65:
        return theme.palette.accent
    return theme.palette.red


def _render_saarthi_dimension(
    slide: Any,
    runtime: Any,
    theme: BrandTheme,
    row: dict[str, Any],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
) -> None:
    score, max_score = _score_parts(row.get("score", "0/1"))
    color = _bar_color(score, max_score, theme)
    
    # Bottom line
    _add_rect(slide, runtime, left, top + height - 0.05, width, 0.01, "#E8EEF8")
    
    title = f"{row.get('code', '')} - {row.get('name', '')}".strip(" -")
    _add_text(slide, runtime, left, top, width - 0.70, 0.16, title, font=theme.body_font.family, size=7.5, color=theme.palette.primary, bold=True)
    _add_text(slide, runtime, left + width - 0.68, top, 0.68, 0.16, f"{score} / {max_score}", font=theme.header_font.family, size=9, color=theme.palette.primary, bold=True, align=runtime.PP_ALIGN.RIGHT)
    
    bar_top = top + 0.18
    _add_rect(slide, runtime, left, bar_top, width, 0.035, "#DDE5F0")
    _add_rect(slide, runtime, left, bar_top, width * min(score / max(max_score, 1), 1), 0.035, color)
    
    body = row.get("assessment") or row.get("evidence") or ""
    if row.get("evidence") and row.get("assessment"):
        body = f"{row.get('assessment')} {row.get('evidence')}"
    _add_text(slide, runtime, left, top + 0.25, width, height - 0.30, _clip(body, 220), font=theme.body_font.family, size=6.5, color=theme.palette.text)


def render_investment_thesis_slide(
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
        "Investment Thesis & Key Catalysts",
        page_number,
        theme,
        runtime,
    )

    resolver = RenderDataResolver(report_spec)
    model = resolver.financial_model
    
    text_block = next((b for b in slide_spec.blocks if isinstance(b, TextBlock)), None)
    bullets_block = next((b for b in slide_spec.blocks if isinstance(b, BulletBlock)), None)

    left = 0.32
    right = 7.60
    top = 1.25
    left_w = 7.00
    right_w = 5.30

    # LEFT COLUMN - THESIS TEXT
    thesis_text = text_block.content if text_block else ""
    paragraphs = [p for p in thesis_text.split("\n") if p.strip()]
    y = top
    for p in paragraphs[:3]:
        # Emphasize first few words
        p = p.strip()
        parts = p.split(":", 1)
        if len(parts) == 2 and len(parts[0]) < 60:
            box = _add_text(slide, runtime, left, y, left_w, 0.6, p, font=theme.body_font.family, size=8, color=theme.palette.text)
            # Make first part bold (using native python-pptx styling isn't fully exposed via _add_text, 
            # so we just render it as normal text, or we can use a small hack by overlapping or ignoring).
            # For simplicity, we just render the text.
        else:
            box = _add_text(slide, runtime, left, y, left_w, 0.6, p, font=theme.body_font.family, size=8, color=theme.palette.text)
        
        y += 0.70

    # LEFT COLUMN - SAARTHI
    scorecard = model.saarthi
    if scorecard:
        saarthi_y = y + 0.1  # dynamically use the space below the paragraph
        _add_text(slide, runtime, left, saarthi_y, left_w, 0.20, f"SAARTHI MULTI-DIMENSIONAL ASSESSMENT - SCORE: {scorecard.total_score}/{scorecard.max_score} ({scorecard.rating or 'BUY'})", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
        _add_rect(slide, runtime, left, saarthi_y + 0.22, left_w, 0.02, theme.palette.primary)
        
        dim_y = saarthi_y + 0.30
        dim_h = 0.45
        for dim in scorecard.dimensions:
            row = {
                "code": dim.code,
                "name": dim.name,
                "score": f"{dim.score}/{dim.max_score}",
                "assessment": dim.assessment,
                "evidence": dim.key_evidence,
            }
            _render_saarthi_dimension(slide, runtime, theme, row, left=left, top=dim_y, width=left_w, height=dim_h)
            dim_y += dim_h + 0.03

    # RIGHT COLUMN - CATALYSTS
    _add_text(slide, runtime, right, top, right_w, 0.20, "KEY CATALYSTS - VALUE REALIZATION TRIGGERS", font=theme.header_font.family, size=8, color=theme.palette.primary, bold=True)
    _add_rect(slide, runtime, right, top + 0.22, right_w, 0.02, theme.palette.accent)

    cat_y = top + 0.30
    cat_h = 0.70
    highlights = model.key_highlights if model.key_highlights else []
    if not highlights and bullets_block:
        highlights = [{"title": b.split(":")[0] if ":" in b else b[:30], "body": b} for b in bullets_block.items]
    
    tags = ["PRIMARY CATALYST", "ONGOING", "NEAR-TERM", "NEXT 3-4 QTRS", "FY26-27"]
    
    for i, hl in enumerate(highlights[:5]):
        _add_rect(slide, runtime, right, cat_y, right_w, cat_h, "#FFFFFF", line="#E8EEF8")
        _add_rect(slide, runtime, right, cat_y, 0.04, cat_h, theme.palette.accent)
        
        # Tag
        tag = tags[i % len(tags)]
        _add_rect(slide, runtime, right + 0.15, cat_y + 0.06, 1.2, 0.12, theme.palette.primary if i == 0 else theme.palette.accent, radius=True)
        _add_text(slide, runtime, right + 0.15, cat_y + 0.07, 1.2, 0.10, tag, font=theme.header_font.family, size=5.5, color="#FFFFFF", bold=True, align=runtime.PP_ALIGN.CENTER)
        
        title = hl.title if hasattr(hl, "title") else hl["title"]
        body = hl.body if hasattr(hl, "body") else hl["body"]
        
        _add_text(slide, runtime, right + 1.45, cat_y + 0.04, right_w - 1.5, 0.16, title, font=theme.body_font.family, size=8, color=theme.palette.primary, bold=True)
        _add_text(slide, runtime, right + 0.15, cat_y + 0.22, right_w - 0.25, cat_h - 0.25, _clip(body, 250), font=theme.body_font.family, size=7, color=theme.palette.text)
        
        cat_y += cat_h + 0.06

    # RIGHT COLUMN - RISK MONITOR
    risk_y = cat_y + 0.05
    risk_h = 0.85
    _add_rect(slide, runtime, right, risk_y, right_w, risk_h, "#F7F9FC", line="#DDE5F0")
    _add_rect(slide, runtime, right, risk_y, 0.04, risk_h, theme.palette.accent)
    _add_text(slide, runtime, right + 0.10, risk_y + 0.08, right_w - 0.20, 0.18, "Thesis Risk Monitor", font=theme.body_font.family, size=8.5, color=theme.palette.primary, bold=True)
    
    risks = model.industry_risks if model.industry_risks else []
    risk_text = " / ".join(risks) if risks else "Monitor regulatory headwinds and potential revenue compression."
    if model.trading_strategy and model.trading_strategy.thesis_breaking_exits:
        risk_text += " " + " ".join(model.trading_strategy.thesis_breaking_exits)
        
    _add_text(slide, runtime, right + 0.10, risk_y + 0.30, right_w - 0.20, risk_h - 0.40, _clip(risk_text, 350), font=theme.body_font.family, size=7, color=theme.palette.text)

