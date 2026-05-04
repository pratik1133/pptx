from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportgen.config import settings
from reportgen.rendering.brand_shell import apply_interior_shell
from reportgen.rendering.chart_renderer import render_chart_block
from reportgen.rendering.components.section_header import render_section_header
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.layout_registry import LayoutDefinition, get_layout_definition
from reportgen.rendering.metrics_renderer import render_metrics_block
from reportgen.rendering.pptx_runtime import load_pptx_runtime
from reportgen.rendering.render_manifest import RenderManifest
from reportgen.rendering.slides.cover_slide import render_cover_slide
from reportgen.rendering.table_renderer import render_table_block
from reportgen.rendering.text_renderer import add_bullet_list, add_textbox
from reportgen.rendering.theme import DEFAULT_THEME, BrandTheme
from reportgen.rendering.theme_loader import load_brand_theme
from reportgen.schemas.blocks import BulletBlock, MetricsBlock, TextBlock
from reportgen.schemas.charts import ChartBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.slides import SlideSpec
from reportgen.schemas.tables import TableBlock


class PresentationRenderer:
    def __init__(self, theme: BrandTheme | None = None) -> None:
        self.theme = theme or load_brand_theme(settings.theme_path) or DEFAULT_THEME
        self.manifest = RenderManifest()

    def render_to_path(self, report_spec: ReportSpec, out_path: Path) -> Path:
        runtime = load_pptx_runtime()
        presentation = runtime.Presentation()
        presentation.slide_width = runtime.Inches(self.theme.canvas.width_in)
        presentation.slide_height = runtime.Inches(self.theme.canvas.height_in)
        resolver = RenderDataResolver(report_spec)
        self.manifest = RenderManifest()

        total = len(report_spec.slides)
        for index, slide_spec in enumerate(report_spec.slides, start=1):
            self._render_slide(
                presentation,
                slide_spec,
                report_spec,
                runtime,
                resolver,
                page_number=index,
                total_pages=total,
            )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        presentation.save(out_path)
        return out_path

    def _render_slide(
        self,
        presentation: Any,
        slide_spec: SlideSpec,
        report_spec: ReportSpec,
        runtime: Any,
        resolver: RenderDataResolver,
        *,
        page_number: int,
        total_pages: int,
    ) -> None:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])

        if slide_spec.layout == "cover_slide":
            render_cover_slide(slide, slide_spec, report_spec, self.theme, runtime)
            return

        # Compute upside percentage for display
        upside_str = ""
        if report_spec.metadata.upside_pct is not None:
            upside_str = str(report_spec.metadata.upside_pct)
        elif report_spec.metadata.target_price and report_spec.metadata.cmp:
            try:
                cmp_val = float(report_spec.metadata.cmp)
                tp_val = float(report_spec.metadata.target_price)
                if cmp_val > 0:
                    upside_str = f"{((tp_val - cmp_val) / cmp_val) * 100:.0f}"
            except (ValueError, TypeError):
                pass

        apply_interior_shell(
            slide,
            self.theme,
            runtime,
            page_number=page_number,
            total_pages=total_pages,
            ticker=report_spec.company.ticker,
            analyst=report_spec.metadata.analyst or "",
            report_date=str(report_spec.metadata.report_date),
            company_name=report_spec.company.name,
            section_title=slide_spec.title,
            cmp=str(report_spec.metadata.cmp),
            target_price=str(report_spec.metadata.target_price),
            upside_pct=upside_str,
            market_cap=str(report_spec.metadata.market_cap) if report_spec.metadata.market_cap else "",
            rating=report_spec.metadata.rating or "",
        )

        layout_definition = get_layout_definition(slide_spec.layout)

        title_box = self._placeholder(layout_definition, "title")
        if title_box:
            render_section_header(
                slide,
                title_box,
                slide_spec.title,
                page_number,
                self.theme,
                runtime,
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

        for block in slide_spec.blocks:
            block_type = getattr(block, "type", "")
            placeholder = self._placeholder(layout_definition, block_type)
            if not placeholder:
                continue

            if isinstance(block, TextBlock):
                add_textbox(slide, placeholder, block.content, self.theme.body_font, runtime, theme=self.theme)
            elif isinstance(block, BulletBlock):
                add_bullet_list(slide, placeholder, list(block.items), self.theme.body_font, runtime, theme=self.theme)
            elif isinstance(block, MetricsBlock):
                render_metrics_block(slide, placeholder, block, runtime, theme=self.theme)
                for item in block.items:
                    self.manifest.add(
                        slide_id=slide_spec.slide_id,
                        block_key=block.key,
                        source_key=item.source or item.label,
                        resolved_value=item.value,
                        kind="metric",
                    )
            elif isinstance(block, ChartBlock):
                render_chart_block(slide, placeholder, block, resolver, runtime, theme=self.theme)
                try:
                    categories = resolver.resolve_period_labels(block.category_source)
                    self.manifest.add(
                        slide_id=slide_spec.slide_id,
                        block_key=block.key,
                        source_key=block.category_source,
                        resolved_value=", ".join(categories),
                        kind="chart_category",
                    )
                    for series_ref in block.series:
                        series = resolver.resolve_series(series_ref.source_key)
                        for period, value in zip(series.periods, series.values):
                            self.manifest.add(
                                slide_id=slide_spec.slide_id,
                                block_key=block.key,
                                source_key=f"{series_ref.source_key}@{period}",
                                resolved_value=str(value),
                                kind="chart_series",
                            )
                except KeyError:
                    pass
            elif isinstance(block, TableBlock):
                render_table_block(slide, placeholder, block, resolver, runtime, theme=self.theme)
                try:
                    rows = resolver.resolve_table_rows(block.source_key)
                    for row_index, row in enumerate(rows):
                        for column in block.columns:
                            self.manifest.add(
                                slide_id=slide_spec.slide_id,
                                block_key=block.key,
                                source_key=f"{block.source_key}[{row_index}].{column.key}",
                                resolved_value=str(row.get(column.key, "")),
                                kind="table_cell",
                            )
                except KeyError:
                    pass

    def _placeholder(self, layout_definition: LayoutDefinition, name: str):
        for placeholder in layout_definition.placeholders:
            if placeholder.name == name:
                return placeholder.box
        return None


def load_report_spec(path: Path) -> ReportSpec:
    return ReportSpec.model_validate(json.loads(path.read_text(encoding="utf-8")))
