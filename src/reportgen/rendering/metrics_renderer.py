from __future__ import annotations

from typing import Any

from reportgen.rendering.geometry import Box
from reportgen.rendering.text_renderer import add_textbox
from reportgen.rendering.theme import BrandTheme
from reportgen.schemas.blocks import MetricsBlock


def render_metrics_block(
    slide: Any,
    box: Box,
    block: MetricsBlock,
    runtime: Any,
    *,
    theme: BrandTheme,
) -> None:
    item_count = len(block.items)
    column_width = box.width / max(item_count, 1)

    for index, item in enumerate(block.items):
        item_box = Box(
            left=box.left + (index * column_width),
            top=box.top,
            width=column_width - 0.05,
            height=box.height,
        )
        add_textbox(
            slide,
            item_box,
            f"{item.label}\n{item.value}",
            theme.metric_font,
            runtime,
            theme=theme,
            align=runtime.PP_ALIGN.CENTER,
        )
