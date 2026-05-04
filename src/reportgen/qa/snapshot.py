"""Golden structural snapshot for sample bundles.

Captures the structural fingerprint of each generated deck — slide count,
ordered layouts, source keys touched per slide. Stored in
`tests/golden/<ticker>.json`. The regression suite compares the live
fingerprint against the stored one and fails on drift.

Diffs that are intentional get committed by re-running the snapshot
recorder (see `record_golden_snapshot`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.report_builder import build_report_spec
from reportgen.schemas.charts import ChartBlock
from reportgen.schemas.report import ReportSpec
from reportgen.schemas.tables import TableBlock
from reportgen.schemas.blocks import MetricsBlock


GOLDEN_ROOT = Path("tests/golden")


@dataclass
class SnapshotDiff:
    bundle: str
    differences: list[str]

    @property
    def ok(self) -> bool:
        return not self.differences


def fingerprint(spec: ReportSpec) -> dict:
    slides_fp = []
    for slide in spec.slides:
        sources: list[str] = []
        for block in slide.blocks:
            if isinstance(block, MetricsBlock):
                sources.extend(item.source or item.label for item in block.items)
            elif isinstance(block, TableBlock):
                sources.append(block.source_key)
            elif isinstance(block, ChartBlock):
                sources.append(block.category_source)
                sources.extend(s.source_key for s in block.series)
        slides_fp.append({
            "slide_id": slide.slide_id,
            "layout": slide.layout,
            "sources": sources,
        })
    return {"slide_count": len(spec.slides), "slides": slides_fp}


def _bundle_to_fingerprint(bundle_path: Path) -> dict:
    bundle = load_normalized_input_bundle(bundle_path)
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    return fingerprint(spec)


def record_golden_snapshot(bundle_path: Path, golden_root: Path = GOLDEN_ROOT) -> Path:
    fp = _bundle_to_fingerprint(bundle_path)
    golden_root.mkdir(parents=True, exist_ok=True)
    target = golden_root / f"{bundle_path.stem}.json"
    target.write_text(json.dumps(fp, indent=2), encoding="utf-8")
    return target


def diff_against_golden(bundle_path: Path, golden_root: Path = GOLDEN_ROOT) -> SnapshotDiff:
    target = golden_root / f"{bundle_path.stem}.json"
    if not target.exists():
        return SnapshotDiff(bundle=bundle_path.name, differences=[f"No golden snapshot recorded at {target}."])

    expected = json.loads(target.read_text(encoding="utf-8"))
    actual = _bundle_to_fingerprint(bundle_path)

    diffs: list[str] = []
    if expected.get("slide_count") != actual["slide_count"]:
        diffs.append(f"slide_count: expected {expected.get('slide_count')}, got {actual['slide_count']}")

    expected_slides = expected.get("slides", [])
    actual_slides = actual["slides"]
    for index, (e, a) in enumerate(zip(expected_slides, actual_slides, strict=False)):
        if e.get("layout") != a.get("layout"):
            diffs.append(f"slide[{index}].layout: expected {e.get('layout')}, got {a.get('layout')}")
        if sorted(e.get("sources", [])) != sorted(a.get("sources", [])):
            diffs.append(
                f"slide[{index}] ({a.get('layout')}) sources changed: "
                f"expected {sorted(e.get('sources', []))}, got {sorted(a.get('sources', []))}"
            )
    if len(expected_slides) != len(actual_slides):
        diffs.append(f"slide order length: expected {len(expected_slides)}, got {len(actual_slides)}")
    return SnapshotDiff(bundle=bundle_path.name, differences=diffs)
