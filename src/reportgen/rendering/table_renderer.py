from __future__ import annotations

from typing import Any

from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.overflow import cap_table_rows
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.tables import TableBlock

MAX_TABLE_ROWS = 14
CELL_MARGIN_IN = 0.04  # tighter than python-pptx default of 0.1
TABLE_BODY_FONT_SHRINK_THRESHOLD = 6  # cols beyond this trigger 1pt shrink


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

    for col_index, column in enumerate(block.columns):
        header_cell = table.cell(0, col_index)
        header_cell.text = column.label
        _set_cell_margins(header_cell, runtime)
        header_fill = header_cell.fill
        header_fill.solid()
        header_fill.fore_color.rgb = runtime.RGBColor.from_string(theme.palette.primary.removeprefix("#"))
        paragraph = header_cell.text_frame.paragraphs[0]
        run = paragraph.runs[0]
        run.font.name = theme.body_font.family
        run.font.bold = True
        run.font.size = runtime.Pt(body_font_pt)
        run.font.color.rgb = runtime.RGBColor.from_string("FFFFFF")

    for row_index, row in enumerate(rows, start=1):
        for col_index, column in enumerate(block.columns):
            value = row.get(column.key, "—")
            cell = table.cell(row_index, col_index)
            cell.text = value
            _set_cell_margins(cell, runtime)
            paragraph = cell.text_frame.paragraphs[0]
            run = paragraph.runs[0]
            run.font.name = theme.body_font.family
            run.font.size = runtime.Pt(body_font_pt)
            run.font.color.rgb = runtime.RGBColor.from_string(theme.palette.text.removeprefix("#"))
            if row_index % 2 == 0:
                fill = cell.fill
                fill.solid()
                fill.fore_color.rgb = runtime.RGBColor.from_string(theme.palette.background.removeprefix("#"))
