"""Disclaimer & Analyst Certification slide renderer.

Renders a clean, premium full-page disclaimer with properly formatted
paragraphs, a decorative accent divider, and large legible text (20pt body).
"""
from __future__ import annotations

from typing import Any

from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import TextBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec


def _rgb(runtime: Any, color: str) -> Any:
    return runtime.RGBColor.from_string(color.removeprefix("#"))


def _split_paragraphs(raw_text: str) -> list[str]:
    """Split disclaimer text into clean paragraphs, stripping markdown headings."""
    paragraphs: list[str] = []
    for block in raw_text.split("\n\n"):
        cleaned = block.strip()
        if not cleaned:
            continue
        # Skip markdown heading lines (they're rendered as the slide title already)
        if cleaned.startswith("#"):
            continue
        # Collapse whitespace within a paragraph
        cleaned = " ".join(cleaned.split())
        paragraphs.append(cleaned)
    return paragraphs


def render_disclaimer_slide(
    slide: Any,
    slide_spec: SlideSpec,
    report_spec: ReportSpec,
    theme: BrandTheme,
    runtime: Any,
    *,
    page_number: int = 0,
) -> None:
    """Render the full-page Disclaimer (or Analyst Certification) slide."""

    DISCLAIMER_TEXT = """About Us: Research Analyst is registered with SEBI as Research Analyst with Registration No. INH000009807. The firm got its registration on June 13, 2022, and is engaged in research services.

Disciplinary history: No penalties / directions have been issued by SEBI under the SEBI Act or Regulations made there under. There are no pending material litigations or legal proceedings, findings of inspections or investigations for which action has been taken or initiated by any regulatory authority.

Details of its associates: No associates

Disclosures with respect to Research and Recommendations Services:
· Research Analyst may have financial interest or actual / beneficial ownership in the securities recommended in its personal portfolio. Details of the same may be referred through the disclosures made at the time of recommendation.
· There are no actual or potential conflicts of interest arising from any connection to or association with any issuer of products/ securities, including any material information or facts that might compromise its objectivity independence in the carrying on of Research Analyst services. Such conflict of interest shall be disclosed to the client as and when they arise.
· Research Analyst or its employee or its associates have not received any compensation from the company in past 12 months.
· Research Analyst or its employee or its associates have not managed or co-managed the public offering of Subject company in past 12 months.
· Research Analyst or its employee or its associates have not received any compensation for investment banking or merchant banking of brokerage services from the subject company in past 12 months.
· Research Analyst or its employee or its associates have not received any compensation for products or services other than above from the subject company in past 12 months.
· Research Analyst or its employee or its associates have not received any compensation or other benefits from the Subject Company or 3rd party in connection with the research report/ recommendation.
· The subject company was not a client of Research Analyst or its employee or its associates during twelve months preceding the date of distribution of the research report and recommendation services provided.
· Research Analysts or its employee or its associates has not served as an officer, director, or employee of the subject company
· Registration granted by SEBI, membership of BASL and certification from NISM in no way guarantee performance of the Intermediary or provide any assurance of returns to investors.
· Investment in securities market are subject to market risks. Read all the related documents carefully before investing."""

    paragraphs = _split_paragraphs(DISCLAIMER_TEXT)

    # ── Layout constants ──────────────────────────────────────────
    LEFT_X = 0.50
    CONTENT_W = 12.33
    DIVIDER_TOP = 1.30
    BODY_TOP = 0.80
    BODY_H = 6.00



    # ── Body text box with multiple paragraphs ────────────────────
    body_box = slide.shapes.add_textbox(
        runtime.Inches(LEFT_X),
        runtime.Inches(BODY_TOP),
        runtime.Inches(CONTENT_W),
        runtime.Inches(BODY_H),
    )
    frame = body_box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = runtime.Inches(0.08)
    frame.margin_right = runtime.Inches(0.08)
    frame.margin_top = runtime.Inches(0.10)
    frame.margin_bottom = runtime.Inches(0.10)

    for idx, para_text in enumerate(paragraphs):
        if idx == 0:
            para = frame.paragraphs[0]
        else:
            para = frame.add_paragraph()

        para.space_before = runtime.Pt(6 if idx > 0 else 0)
        para.space_after = runtime.Pt(3)
        para.line_spacing = 1.15

        run = para.add_run()
        run.text = para_text
        run.font.name = theme.body_font.family
        run.font.size = runtime.Pt(12)
        run.font.bold = False
        run.font.color.rgb = _rgb(runtime, theme.palette.text)

    # ── Analyst Signature ─────────────────────────────────────────
    import os
    sig_path = r"c:\pptx\data\images\signature.png"
    if os.path.exists(sig_path):
        slide.shapes.add_picture(
            sig_path,
            runtime.Inches(LEFT_X + CONTENT_W - 2.5),
            runtime.Inches(5.4),
            height=runtime.Inches(0.8)
        )
