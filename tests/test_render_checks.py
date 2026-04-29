from pathlib import Path

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.report_builder import build_report_spec
from reportgen.qa.render_checks import validate_rendered_pptx
from reportgen.qa.validators import validate_report_content
from reportgen.rendering.engine import PresentationRenderer


def test_render_checks_accept_valid_output() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    report_spec = build_report_spec(bundle, plan_slides_mock(bundle))
    out_dir = Path("output/test-temp/render-checks")
    out_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = PresentationRenderer().render_to_path(report_spec, out_dir / "report.pptx")

    result = validate_rendered_pptx(pptx_path, report_spec)

    assert result.ok


def test_content_validator_returns_non_blocking_result() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    report_spec = build_report_spec(bundle, plan_slides_mock(bundle))

    result = validate_report_content(report_spec)

    assert result.errors == []
