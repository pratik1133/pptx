from pathlib import Path

from reportgen.rendering.engine import PresentationRenderer
from reportgen.rendering.theme_loader import load_brand_theme
from reportgen.schemas.report import ReportSpec


def _load_sample_report() -> ReportSpec:
    candidate_dirs = sorted(Path("output").glob("*_abc_*"))
    for d in candidate_dirs:
        report_path = d / "intermediates" / "report.json"
        if report_path.exists():
            return ReportSpec.model_validate_json(report_path.read_text(encoding="utf-8"))
    raise FileNotFoundError("No sample report.json found under output/.")


def test_render_produces_pptx_with_branded_shell(tmp_path):
    theme = load_brand_theme(Path("assets/themes/brand_theme.json"))
    report = _load_sample_report()
    renderer = PresentationRenderer(theme=theme)
    out = renderer.render_to_path(report, tmp_path / "branded.pptx")
    assert out.exists()
    assert out.stat().st_size > 0


def test_canvas_dimensions_are_widescreen():
    theme = load_brand_theme(Path("assets/themes/brand_theme.json"))
    assert theme.canvas.aspect_ratio == "16:9"
    assert abs(theme.canvas.width_in - 13.333) < 0.01
