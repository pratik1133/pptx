from pathlib import Path

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.report_builder import build_report_spec
from reportgen.rendering.engine import PresentationRenderer
from reportgen.rendering.layout_registry import LAYOUT_REGISTRY


PHASE10_LAYOUTS = {
    "peer_comparison",
    "valuation_table",
    "quarterly_summary",
    "ratio_summary",
    "dcf_summary",
    "segment_mix",
    "price_performance",
    "industry_overview",
    "saarthi_scorecard",
    "management_profile",
    "forensic_assessment",
    "trading_strategy",
    "key_highlights",
}


def test_phase10_layouts_registered():
    assert PHASE10_LAYOUTS.issubset(set(LAYOUT_REGISTRY.keys()))


def test_motilal_plan_has_full_research_stack():
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/motilal_bundle.json"))
    plan = plan_slides_mock(bundle)
    layouts = {s.layout for s in plan.slides}

    assert 14 <= len(plan.slides) <= 22
    assert "cover_slide" in layouts
    assert "investment_thesis" in layouts
    assert "saarthi_scorecard" in layouts
    assert "industry_overview" in layouts
    assert "key_highlights" in layouts
    assert "ratio_summary" in layouts
    assert "valuation_table" in layouts
    assert "management_profile" in layouts
    assert "forensic_assessment" in layouts
    assert "disclaimer" in layouts


def test_abc_plan_still_renders_under_smaller_data():
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    plan = plan_slides_mock(bundle)
    assert 5 <= len(plan.slides) <= 22
    assert any(s.layout == "disclaimer" for s in plan.slides)


def test_motilal_renders_to_pptx(tmp_path):
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/motilal_bundle.json"))
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    out = PresentationRenderer().render_to_path(spec, tmp_path / "motilal.pptx")
    assert out.exists()
    assert out.stat().st_size > 0
