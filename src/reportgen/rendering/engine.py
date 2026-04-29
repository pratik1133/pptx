from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportgen.rendering.chart_renderer import render_chart_block
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.layout_registry import LayoutDefinition, get_layout_definition
from reportgen.rendering.metrics_renderer import render_metrics_block
from reportgen.rendering.pptx_runtime import load_pptx_runtime
from reportgen.rendering.table_renderer import render_table_block
from reportgen.rendering.text_renderer import add_bullet_list, add_textbox
from reportgen.rendering.theme import DEFAULT_THEME, BrandTheme
from reportgen.schemas.blocks import BulletBlock, MetricsBlock, TextBlock
from reportgen.schemas.charts import ChartBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec
from reportgen.schemas.tables import TableBlock


class PresentationRenderer:
    def __init__(self, theme: BrandTheme | None = None) -> None:
        self.theme = theme or DEFAULT_THEME

    def render_to_path(self, report_spec: ReportSpec, out_path: Path) -> Path:
        runtime = load_pptx_runtime()
        presentation = runtime.Presentation()
        presentation.slide_width = runtime.Inches(10)
        presentation.slide_height = runtime.Inches(7.5)
        resolver = RenderDataResolver(report_spec)

        for slide_spec in report_spec.slides:
            self._render_slide(presentation, slide_spec, runtime, resolver)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        presentation.save(out_path)
        return out_path

    def _render_slide(
        self,
        presentation: Any,
        slide_spec: SlideSpec,
        runtime: Any,
        resolver: RenderDataResolver,
    ) -> None:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        self._apply_background(slide, runtime)
        layout_definition = get_layout_definition(slide_spec.layout)

        title_box = self._placeholder(layout_definition, "title")
        if title_box:
            add_textbox(
                slide,
                title_box,
                slide_spec.title,
                self.theme.title_font,
                runtime,
                theme=self.theme,
            )

        if slide_spec.subtitle:
            subtitle_box = self._placeholder(layout_definition, "subtitle")
            if subtitle_box:
                add_textbox(
                    slide,
                    subtitle_box,
                    slide_spec.subtitle,
                    self.theme.subtitle_font,
                    runtime,
                    theme=self.theme,
                )

        counters: dict[str, int] = {}
        for block in slide_spec.blocks:
            block_type = getattr(block, "type", "")
            counters[block_type] = counters.get(block_type, 0) + 1
            placeholder = self._placeholder(layout_definition, block_type)
            if not placeholder:
                continue

            if isinstance(block, TextBlock):
                add_textbox(slide, placeholder, block.content, self.theme.body_font, runtime, theme=self.theme)
            elif isinstance(block, BulletBlock):
                add_bullet_list(slide, placeholder, list(block.items), self.theme.body_font, runtime, theme=self.theme)
            elif isinstance(block, MetricsBlock):
                render_metrics_block(slide, placeholder, block, runtime, theme=self.theme)
            elif isinstance(block, ChartBlock):
                render_chart_block(slide, placeholder, block, resolver, runtime, theme=self.theme)
            elif isinstance(block, TableBlock):
                render_table_block(slide, placeholder, block, resolver, runtime, theme=self.theme)

    def _apply_background(self, slide: Any, runtime: Any) -> None:
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = runtime.RGBColor.from_string(
            self.theme.palette.background.removeprefix("#")
        )

    def _placeholder(self, layout_definition: LayoutDefinition, name: str):
        for placeholder in layout_definition.placeholders:
            if placeholder.name == name:
                return placeholder.box
        return None

def load_report_spec(path: Path) -> ReportSpec:
    return ReportSpec.model_validate(json.loads(path.read_text(encoding="utf-8")))
