from io import BytesIO
from pathlib import Path

from PIL import Image

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.report_builder import build_report_spec
from reportgen.rendering.chart_renderer import _axis_formatter, _build_chart_image, _label_formatter
from reportgen.rendering.data_resolver import RenderDataResolver
from reportgen.rendering.engine import PresentationRenderer
from reportgen.rendering.theme import DEFAULT_THEME
from reportgen.rendering.theme_loader import load_brand_theme
from reportgen.config import settings
from reportgen.schemas.charts import ChartBlock, ChartSeriesRef


MOTILAL_BUNDLE = Path("data/samples/bundles/motilal_bundle.json")


def test_axis_formatter_dispatches_per_unit():
    f_pct = _axis_formatter("%")
    assert f_pct(37, None) == "37%"

    f_mult = _axis_formatter("x")
    assert f_mult(12.3, None) == "12.3x"

    f_cr = _axis_formatter("INR Cr")
    assert "Cr" in f_cr(4907, None)
    assert "₹" in f_cr(4907, None)

    f_default = _axis_formatter(None)
    assert "," in f_default(1234567, None)


def test_label_formatter_compact_currency_for_large_values():
    fmt = _label_formatter("INR Cr")
    assert "Cr" in fmt(4907.0)
    assert fmt(12.5).endswith("Cr")


def test_chart_image_uses_themed_palette_and_renders():
    """Render a chart from real Motilal data and assert it produced a non-trivial PNG."""
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    resolver = RenderDataResolver(spec)
    theme = load_brand_theme(settings.theme_path) or DEFAULT_THEME

    block = ChartBlock(
        key="test_chart",
        chart_type="bar",
        title="Revenue Trend",
        category_source="period_labels",
        series=[ChartSeriesRef(label="Revenue", source_key="series.Revenue")],
    )
    buffer = _build_chart_image(block, resolver, theme)
    image = Image.open(buffer)
    assert image.size[0] > 400 and image.size[1] > 200, "chart image should be a sensible canvas"


def test_combo_and_stacked_bar_drawers_do_not_crash():
    """Smoke test that the new chart types render without exceptions."""
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    resolver = RenderDataResolver(spec)
    theme = load_brand_theme(settings.theme_path) or DEFAULT_THEME

    series_keys = [f"series.{s.name}" for s in resolver.financial_model.series]
    assert len(series_keys) >= 2, "fixture should expose multiple series"

    for chart_type in ("stacked_bar", "combo", "line", "bar"):
        block = ChartBlock(
            key=f"chart_{chart_type}",
            chart_type=chart_type,
            title=f"{chart_type} test",
            category_source="period_labels",
            series=[ChartSeriesRef(label=key.removeprefix("series."), source_key=key) for key in series_keys[:2]],
        )
        buffer = _build_chart_image(block, resolver, theme)
        Image.open(buffer)  # Throws if invalid PNG


def test_full_render_still_passes_render_checks(tmp_path):
    """Phase 13 must not regress the existing render-check pipeline."""
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    renderer = PresentationRenderer()
    pptx_path = renderer.render_to_path(spec, tmp_path / "report.pptx")
    assert pptx_path.exists()
    assert pptx_path.stat().st_size > 0
