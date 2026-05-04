from __future__ import annotations

import re
from typing import Any

from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.overflow import cap_table_rows
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.tables import TableBlock

MAX_TABLE_ROWS = 14
CELL_MARGIN_IN = 0.04  # tighter than python-pptx default of 0.1
TABLE_BODY_FONT_SHRINK_THRESHOLD = 6  # cols beyond this trigger 1pt shrink

# Patterns to detect sign-sensitive values (percentages, growth)
_NEGATIVE_PATTERN = re.compile(r"^\s*[–\-].*%")
_POSITIVE_PATTERN = re.compile(r"^\s*\+?\d+.*%")
_SECTION_KEYWORDS = frozenset({
    "income statement", "per share", "multiples", "return ratios",
    "balance sheet", "cash flow", "valuation", "growth", "profitability",
    "key ratios", "operating metrics",
})


def _is_section_row(row: dict, columns: list) -> bool:
    """Detect rows that serve as section headers (like tbl-section in HTML)."""
    if not columns:
        return False
    first_key = columns[0].key
    first_val = str(row.get(first_key, "")).strip().lower()
    # Section rows typically span all columns or have only the first column filled
    non_empty = sum(1 for c in columns if str(row.get(c.key, "")).strip())
    if non_empty <= 1 and first_val and any(kw in first_val for kw in _SECTION_KEYWORDS):
        return True
    return False


def _is_highlight_row(row: dict, columns: list) -> bool:
    """Detect rows that should be highlighted (like PAT, Total, etc.)."""
    if not columns:
        return False
    first_key = columns[0].key
    first_val = str(row.get(first_key, "")).strip().lower()
    highlight_keywords = {"pat", "net profit", "total", "ebitda", "net income", "bottom line"}
    return any(kw in first_val for kw in highlight_keywords)


def _detect_value_color(value: str, theme: BrandTheme) -> str | None:
    """Return green/red color hex for sign-colored values, or None for default."""
    val = str(value).strip()
    if _NEGATIVE_PATTERN.match(val):
        return theme.palette.red
    if _POSITIVE_PATTERN.match(val):
        return theme.palette.green
    return None


def _set_cell_margins(cell: Any, runtime: Any) -> None:
    margin = runtime.Inches(CELL_MARGIN_IN)
    cell.margin_left = margin
    cell.margin_right = margin
    cell.margin_top = runtime.Inches(0.02)
    cell.margin_bottom = runtime.Inches(0.02)


def render_table_block(
    slide: Any,
    box: Box,
    block: TableBlock,
    resolver: RenderDataResolver,
    runtime: Any,
    *,
    theme: BrandTheme,
) -> None:
    full_rows = resolver.resolve_table_rows(block.source_key)
    rows, hidden = cap_table_rows(full_rows, MAX_TABLE_ROWS)
    if hidden > 0 and block.columns:
        continuation_row = {block.columns[0].key: f"+ {hidden} more rows (see appendix)"}
        rows = list(rows) + [continuation_row]
    row_count = len(rows) + 1
    col_count = len(block.columns)

    body_font_pt = theme.body_font.size_pt
    if col_count > TABLE_BODY_FONT_SHRINK_THRESHOLD:
        body_font_pt = max(9, body_font_pt - 2)

    shape = slide.shapes.add_table(
        row_count,
        col_count,
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        runtime.Inches(box.width),
        runtime.Inches(box.height),
    )
    table = shape.table

    # Force equal column widths summing to exactly the placeholder box width
    # (prevents auto-grown columns pushing the right edge off the slide).
    column_width_emu = runtime.Inches(box.width / col_count)
    for col_index in range(col_count):
        table.columns[col_index].width = column_width_emu

    # ── Header row: Navy background, white bold text ──
    for col_index, column in enumerate(block.columns):
        header_cell = table.cell(0, col_index)
        header_cell.text = column.label
        _set_cell_margins(header_cell, runtime)
        header_fill = header_cell.fill
        header_fill.solid()
        header_fill.fore_color.rgb = runtime.RGBColor.from_string(theme.palette.primary.removeprefix("#"))
        paragraph = header_cell.text_frame.paragraphs[0]
        # Right-align all columns except first
        if col_index > 0:
            paragraph.alignment = runtime.PP_ALIGN.RIGHT
        run = paragraph.runs[0]
        run.font.name = theme.body_font.family
        run.font.bold = True
        run.font.size = runtime.Pt(body_font_pt)
        run.font.color.rgb = runtime.RGBColor.from_string("FFFFFF")

    # ── Body rows with rich colorization ──
    for row_index, row in enumerate(rows, start=1):
        is_section = _is_section_row(row, block.columns)
        is_highlight = _is_highlight_row(row, block.columns)

        for col_index, column in enumerate(block.columns):
            value = row.get(column.key, "—")
            cell = table.cell(row_index, col_index)
            cell.text = value
            _set_cell_margins(cell, runtime)

            # ── Row background coloring ──
            if is_section:
                # Section header rows: light blue background like HTML .tbl-section
                fill = cell.fill
                fill.solid()
                fill.fore_color.rgb = runtime.RGBColor.from_string(
                    theme.palette.section_bg.removeprefix("#")
                )
            elif is_highlight:
                # Highlight rows (PAT, Total): orange tint like HTML .tbl-highlight
                fill = cell.fill
                fill.solid()
                fill.fore_color.rgb = runtime.RGBColor.from_string(
                    theme.palette.highlight_row.removeprefix("#")
                )
            elif row_index % 2 == 1:
                # Odd body rows: light grey alternating band
                fill = cell.fill
                fill.solid()
                fill.fore_color.rgb = runtime.RGBColor.from_string(
                    theme.palette.light_grey.removeprefix("#")
                )
            else:
                # Even body rows: white
                fill = cell.fill
                fill.solid()
                fill.fore_color.rgb = runtime.RGBColor.from_string(
                    theme.palette.background.removeprefix("#")
                )

            # ── Text styling ──
            paragraph = cell.text_frame.paragraphs[0]
            # Right-align all columns except first
            if col_index > 0:
                paragraph.alignment = runtime.PP_ALIGN.RIGHT
            run = paragraph.runs[0]
            run.font.name = theme.body_font.family
            run.font.size = runtime.Pt(body_font_pt)

            if is_section:
                # Section rows: bold primary text
                run.font.bold = True
                run.font.color.rgb = runtime.RGBColor.from_string(
                    theme.palette.primary.removeprefix("#")
                )
            elif is_highlight:
                # Highlight rows: bold primary text
                run.font.bold = True
                run.font.color.rgb = runtime.RGBColor.from_string(
                    theme.palette.primary.removeprefix("#")
                )
            elif col_index == 0:
                # First column: semi-bold slate color (row label)
                run.font.bold = True
                run.font.color.rgb = runtime.RGBColor.from_string(
                    theme.palette.muted_text.removeprefix("#")
                )
            else:
                # Numeric columns: check for green/red coloring
                value_color = _detect_value_color(str(value), theme)
                if value_color:
                    run.font.bold = True
                    run.font.color.rgb = runtime.RGBColor.from_string(
                        value_color.removeprefix("#")
                    )
                else:
                    run.font.color.rgb = runtime.RGBColor.from_string(
                        theme.palette.text.removeprefix("#")
                    )
