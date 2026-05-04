"""HTML report renderer — converts ReportSpec into a styled HTML document.

Uses Jinja2 templates with the design system from motilal_v1.html.
The output HTML is self-contained and can be printed to PDF via Playwright.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from reportgen.config import settings
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.svg_charts import render_chart_svg
from reportgen.rendering.theme import DEFAULT_THEME, BrandTheme
from reportgen.rendering.theme_loader import load_brand_theme
from reportgen.schemas.blocks import BulletBlock, MetricsBlock, TextBlock
from reportgen.schemas.charts import ChartBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.tables import TableBlock

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class HtmlReportRenderer:
    def __init__(self, theme: BrandTheme | None = None) -> None:
        self.theme = theme or load_brand_theme(settings.theme_path) or DEFAULT_THEME
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_to_html(self, report_spec: ReportSpec) -> str:
        """Render a ReportSpec into a complete HTML string."""
        resolver = RenderDataResolver(report_spec)
        context = self._build_context(report_spec, resolver)
        template = self.env.get_template("report.html.j2")
        return template.render(**context)

    def render_to_path(self, report_spec: ReportSpec, out_path: Path) -> Path:
        """Render to an HTML file on disk."""
        html = self.render_to_html(report_spec)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        return out_path

    def _build_context(self, spec: ReportSpec, resolver: RenderDataResolver) -> dict[str, Any]:
        slides = []
        for idx, slide_spec in enumerate(spec.slides, start=1):
            slides.append({
                "page_number": idx,
                "slide_id": slide_spec.slide_id,
                "layout": slide_spec.layout,
                "title": slide_spec.title,
                "subtitle": slide_spec.subtitle or "",
                "blocks": self._prepare_blocks(slide_spec.blocks, resolver),
            })

        # Compute upside
        upside_pct = ""
        if spec.metadata.upside_pct is not None:
            upside_pct = f"+{spec.metadata.upside_pct}%"
        elif spec.metadata.target_price and spec.metadata.cmp:
            try:
                cmp_val = float(spec.metadata.cmp)
                tp_val = float(spec.metadata.target_price)
                if cmp_val > 0:
                    upside_pct = f"+{((tp_val - cmp_val) / cmp_val) * 100:.0f}%"
            except (ValueError, TypeError):
                pass

        # Format market cap
        market_cap_str = ""
        if spec.metadata.market_cap:
            try:
                mc = float(spec.metadata.market_cap)
                if mc >= 1e9:
                    market_cap_str = f"₹{mc / 1e7:,.0f} Cr"
                elif mc >= 1e7:
                    market_cap_str = f"₹{mc / 1e7:,.0f} Cr"
                else:
                    market_cap_str = f"₹{mc:,.0f}"
            except (ValueError, TypeError):
                market_cap_str = str(spec.metadata.market_cap)

        # Try to load financial model for enriched cover data
        model = None
        try:
            model = resolver.financial_model
        except Exception:
            pass

        # Build financial summary rows from series data
        fin_summary_rows = self._build_financial_summary(resolver)

        return {
            "company": spec.company,
            "meta": spec.metadata,
            "theme": self.theme,
            "slides": slides,
            "total_pages": len(spec.slides),
            "upside_pct": upside_pct,
            "market_cap_str": market_cap_str,
            "cmp_str": f"₹{float(spec.metadata.cmp):,.2f}",
            "tp_str": f"₹{float(spec.metadata.target_price):,.0f}",
            "model": model,
            "fin_summary_rows": fin_summary_rows,
        }

    def _prepare_blocks(self, blocks: list, resolver: RenderDataResolver) -> list[dict]:
        prepared = []
        for block in blocks:
            if isinstance(block, TextBlock):
                prepared.append({
                    "type": "text",
                    "key": block.key,
                    "content": block.content,
                })
            elif isinstance(block, BulletBlock):
                prepared.append({
                    "type": "bullets",
                    "key": block.key,
                    "items": list(block.items),
                })
            elif isinstance(block, MetricsBlock):
                prepared.append({
                    "type": "metrics",
                    "key": block.key,
                    "items": [{"label": i.label, "value": str(i.value)} for i in block.items],
                })
            elif isinstance(block, ChartBlock):
                try:
                    categories = resolver.resolve_period_labels(block.category_source)
                    series_data = [resolver.resolve_series(s.source_key) for s in block.series]
                    colors = self.theme.chart_palette or [
                        self.theme.palette.primary,
                        self.theme.palette.accent,
                        self.theme.palette.secondary,
                    ]
                    svg = render_chart_svg(
                        block.chart_type, block.title, categories, series_data, colors
                    )
                    prepared.append({
                        "type": "chart",
                        "key": block.key,
                        "title": block.title,
                        "chart_type": block.chart_type,
                        "svg_html": svg,
                    })
                except KeyError:
                    prepared.append({
                        "type": "text",
                        "key": block.key,
                        "content": f"[Chart data unavailable: {block.title}]",
                    })
            elif isinstance(block, TableBlock):
                try:
                    rows = resolver.resolve_table_rows(block.source_key)
                    prepared.append({
                        "type": "table",
                        "key": block.key,
                        "title": block.title,
                        "columns": [{"key": c.key, "label": c.label} for c in block.columns],
                        "rows": rows,
                    })
                except KeyError:
                    prepared.append({
                        "type": "text",
                        "key": block.key,
                        "content": f"[Table data unavailable: {block.title}]",
                    })
        return prepared

    def _build_financial_summary(self, resolver: RenderDataResolver) -> list[dict]:
        """Build financial summary table rows from series data for the cover page."""
        rows = []
        series_names = ["Revenue", "EBITDA", "PAT", "EPS"]
        try:
            model = resolver.financial_model
        except Exception:
            return rows

        for s in model.series:
            if s.name in series_names:
                row = {"label": s.name, "unit": s.unit}
                for period, value in zip(s.periods, s.values):
                    row[period] = str(value) if value is not None else "—"
                row["_periods"] = list(s.periods)
                rows.append(row)

        # Add key ratios
        for r in model.ratios:
            row = {"label": r.name, "unit": r.unit}
            for period, value in zip(r.periods, r.values):
                row[period] = f"{value}%" if r.unit == "%" else str(value) if value is not None else "—"
            row["_periods"] = list(r.periods)
            rows.append(row)

        return rows


def load_report_spec(path: Path) -> ReportSpec:
    return ReportSpec.model_validate(json.loads(path.read_text(encoding="utf-8")))
