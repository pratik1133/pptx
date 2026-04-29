from __future__ import annotations

from typing import Any

from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.geometry import Box
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.tables import TableBlock


def render_table_block(
    slide: Any,
    box: Box,
    block: TableBlock,
    resolver: RenderDataResolver,
    runtime: Any,
    *,
    theme: BrandTheme,
) -> None:
    rows = resolver.resolve_table_rows(block.source_key)
    row_count = len(rows) + 1
    col_count = len(block.columns)

    shape = slide.shapes.add_table(
        row_count,
        col_count,
        runtime.Inches(box.left),
        runtime.Inches(box.top),
        runtime.Inches(box.width),
        runtime.Inches(box.height),
    )
    table = shape.table

    for col_index, column in enumerate(block.columns):
        header_cell = table.cell(0, col_index)
        header_cell.text = column.label
        header_fill = header_cell.fill
        header_fill.solid()
        header_fill.fore_color.rgb = runtime.RGBColor.from_string(theme.palette.primary.removeprefix("#"))
        paragraph = header_cell.text_frame.paragraphs[0]
        run = paragraph.runs[0]
        run.font.name = theme.body_font.family
        run.font.bold = True
        run.font.size = runtime.Pt(theme.body_font.size_pt)
        run.font.color.rgb = runtime.RGBColor.from_string("FFFFFF")

    for row_index, row in enumerate(rows, start=1):
        for col_index, column in enumerate(block.columns):
            value = row.get(column.key, "-")
            cell = table.cell(row_index, col_index)
            cell.text = value
            paragraph = cell.text_frame.paragraphs[0]
            run = paragraph.runs[0]
            run.font.name = theme.body_font.family
            run.font.size = runtime.Pt(theme.body_font.size_pt)
            run.font.color.rgb = runtime.RGBColor.from_string(theme.palette.text.removeprefix("#"))
            if row_index % 2 == 0:
                fill = cell.fill
                fill.solid()
                fill.fore_color.rgb = runtime.RGBColor.from_string(theme.palette.background.removeprefix("#"))
