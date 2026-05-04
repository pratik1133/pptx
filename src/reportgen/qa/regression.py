from __future__ import annotations

from pathlib import Path

from reportgen.config import settings
from reportgen.orchestration.pipeline import run_local_pipeline
from reportgen.qa.validators import QaResult


def discover_sample_bundles(root: Path | None = None) -> list[Path]:
    search_root = root or Path("data/samples/bundles")
    return sorted(search_root.glob("*.json"))


def run_regression_sample_set(output_root: Path | None = None, *, use_mock: bool = True) -> QaResult:
    """Run every sample bundle through the pipeline. Defaults to mock for deterministic regression."""
    result = QaResult()
    for bundle_path in discover_sample_bundles():
        try:
            run_local_pipeline(bundle_path, output_root or settings.output_root, use_mock=use_mock)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"Regression bundle {bundle_path.name} failed: {exc}")
    return result
