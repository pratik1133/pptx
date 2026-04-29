from pathlib import Path

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.report_builder import build_report_spec


def test_build_report_spec_from_mock_plan() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    plan = plan_slides_mock(bundle)
    report_spec = build_report_spec(bundle, plan)

    assert report_spec.company.ticker == "ABC"
    assert len(report_spec.slides) == len(plan.slides)
    metric_block = report_spec.slides[0].blocks[0]
    assert metric_block.type == "metrics"
    assert any(slide.layout == "full_table" for slide in report_spec.slides)
