from pathlib import Path

from reportgen.config import settings
from reportgen.orchestration.pipeline import run_local_pipeline


def test_run_local_pipeline_packages_outputs() -> None:
    result = run_local_pipeline(Path("data/samples/bundles/abc_bundle.json"), settings.output_root)

    assert result.run_root.exists()
    assert (result.run_root / "manifest.json").exists()
    assert (result.run_root / "artifacts" / "report.pptx").exists()
    assert (result.run_root / "intermediates" / "slide_plan.json").exists()
    assert result.manifest.artifacts
    assert result.manifest.status in {"complete", "pdf_skipped"}
