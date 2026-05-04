from pathlib import Path

from reportgen.ai.planner import plan_slides_mock
from reportgen.compliance import (
    load_analyst_certification_text,
    load_disclaimer_text,
)
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.layout_policy import MANDATORY_LAYOUTS
from reportgen.planning.report_builder import build_report_spec
from reportgen.qa.snapshot import (
    diff_against_golden,
    fingerprint,
    record_golden_snapshot,
)
from reportgen.qa.regression import discover_sample_bundles
from reportgen.rendering.engine import PresentationRenderer
from reportgen.rendering.overflow import (
    autoshrink_text,
    cap_table_rows,
    split_bullets_for_continuation,
)
from reportgen.rendering.geometry import Box


MOTILAL_BUNDLE = Path("data/samples/bundles/motilal_bundle.json")


def test_disclaimer_loaded_from_assets_contains_sebi_registration():
    text = load_disclaimer_text()
    assert "SEBI" in text
    assert "INH000069807" in text


def test_analyst_certification_loaded_from_assets():
    text = load_analyst_certification_text()
    assert "Analyst Certification" in text
    assert "personal views" in text.lower()


def test_analyst_certification_layout_is_mandatory():
    assert "analyst_certification" in MANDATORY_LAYOUTS
    assert "disclaimer" in MANDATORY_LAYOUTS


def test_mock_plan_includes_certification_and_real_disclaimer():
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    plan = plan_slides_mock(bundle)
    layouts = [s.layout for s in plan.slides]
    assert "analyst_certification" in layouts
    assert "disclaimer" in layouts

    disclaimer_slide = next(s for s in plan.slides if s.layout == "disclaimer")
    disclaimer_text = disclaimer_slide.blocks[0].content
    assert "INH000069807" in disclaimer_text


def test_autoshrink_steps_down_to_fit():
    box = Box(left=0, top=0, width=4, height=2)
    long_text = "abcdefg " * 200
    result = autoshrink_text(long_text, box, base_font_size_pt=14, min_font_pt=9)
    assert 9 <= result.font_size_pt <= 14


def test_split_bullets_returns_continuation():
    box = Box(left=0, top=0, width=6, height=1.2)
    items = [f"point {i}" for i in range(20)]
    fits, rest = split_bullets_for_continuation(items, box, font_size_pt=12)
    assert fits and rest
    assert len(fits) + len(rest) == len(items)


def test_cap_table_rows_returns_hidden_count():
    rows = [{"name": str(i)} for i in range(20)]
    capped, hidden = cap_table_rows(rows, max_rows=10)
    assert len(capped) == 10
    assert hidden == 10


def test_record_and_diff_golden_snapshots_for_all_samples(tmp_path):
    """Record golden snapshots for every sample bundle, then assert they diff clean."""
    golden_root = tmp_path / "golden"
    bundles = discover_sample_bundles()
    assert len(bundles) >= 2

    for bundle_path in bundles:
        record_golden_snapshot(bundle_path, golden_root=golden_root)

    for bundle_path in bundles:
        diff = diff_against_golden(bundle_path, golden_root=golden_root)
        assert diff.ok, f"{bundle_path.name}: {diff.differences}"


def test_renderer_handles_full_motilal_deck_with_compliance_slides(tmp_path):
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    fp = fingerprint(spec)
    layouts_in_order = [s["layout"] for s in fp["slides"]]
    assert "analyst_certification" in layouts_in_order
    assert layouts_in_order[-1] == "disclaimer"

    renderer = PresentationRenderer()
    pptx_path = renderer.render_to_path(spec, tmp_path / "report.pptx")
    assert pptx_path.exists() and pptx_path.stat().st_size > 0
