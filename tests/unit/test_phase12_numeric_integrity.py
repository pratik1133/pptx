import json
from decimal import Decimal
from pathlib import Path

import pytest

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.errors import InputValidationError
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.planning.report_builder import build_report_spec
from reportgen.planning.slide_plan_validator import _find_orphan_numbers, validate_slide_plan
from reportgen.rendering.engine import PresentationRenderer
from reportgen.rendering.number_format import (
    EMPTY,
    format_currency,
    format_multiple,
    format_number,
    format_percent,
)
from reportgen.schemas.planning import PlanningTextBlock


MOTILAL_BUNDLE = Path("data/samples/bundles/motilal_bundle.json")
ABC_BUNDLE = Path("data/samples/bundles/abc_bundle.json")


def test_format_number_handles_none_and_indian_grouping():
    assert format_number(None) == EMPTY
    assert format_number(Decimal("1234567.89")) == "12,34,567.9"
    assert format_number(Decimal("-1234.5")) == "-1,234.5"
    assert format_number(Decimal("0.5"), precision=2) == "0.50"


def test_format_currency_uses_symbol_and_grouping():
    assert format_currency(Decimal("822.9"), "INR") == "₹822.9"
    assert format_currency(Decimal("49079"), "INR", suffix=" Cr") == "₹49,079.0 Cr"
    assert format_currency(None, "INR") == EMPTY


def test_format_percent_and_multiple():
    assert format_percent(Decimal("37")) == "37.0%"
    assert format_multiple(Decimal("12.345"), precision=2) == "12.35x"


def test_orphan_number_detector_flags_units_in_prose():
    assert _find_orphan_numbers("Upside of 37% to target.")
    assert _find_orphan_numbers("Trading at 12.3x FY26E earnings.")
    assert _find_orphan_numbers("Market cap of ₹4,907 Cr.")
    assert _find_orphan_numbers("Spread expanded by 70 bps in Q3.")
    assert _find_orphan_numbers("Target price of INR 1127.")


def test_orphan_number_detector_allows_years_and_counts():
    assert not _find_orphan_numbers("FY26E estimates show margin expansion.")
    assert not _find_orphan_numbers("The 7-dimension framework covers governance and growth.")
    assert not _find_orphan_numbers("In 2024 the segment expanded into three new regions.")


def test_validator_rejects_orphan_numbers_in_text_block():
    bundle = load_normalized_input_bundle(ABC_BUNDLE)
    plan = plan_slides_mock(bundle)
    target = next(s for s in plan.slides if any(isinstance(b, PlanningTextBlock) for b in s.blocks))
    text_block = next(b for b in target.blocks if isinstance(b, PlanningTextBlock))
    text_block.content = "Trading at 12.3x FY26E EPS with 18% upside."

    with pytest.raises(InputValidationError) as exc:
        validate_slide_plan(plan, bundle)
    assert "orphan numeric tokens" in str(exc.value).lower()


def test_render_manifest_records_every_resolved_value(tmp_path):
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    renderer = PresentationRenderer()
    renderer.render_to_path(spec, tmp_path / "report.pptx")

    payload = json.loads(renderer.manifest.to_json())
    records = payload["records"]
    assert len(records) > 30, "manifest should record many resolved values across the deck"

    kinds = {r["kind"] for r in records}
    assert {"metric", "table_cell"}.issubset(kinds)

    for r in records:
        assert r["slide_id"] and r["block_key"] and r["source_key"]


def test_mutating_a_model_number_propagates_to_render_manifest(tmp_path, monkeypatch):
    """Bump the model's CMP and assert every dependent metric reflects the new value."""
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    bundle.source.metadata.cmp = Decimal("999.5")
    plan = plan_slides_mock(bundle)
    spec = build_report_spec(bundle, plan)
    renderer = PresentationRenderer()
    renderer.render_to_path(spec, tmp_path / "report.pptx")

    cmp_records = [r for r in renderer.manifest.records if r["source_key"] == "metadata.cmp"] \
        if isinstance(renderer.manifest.records[0], dict) \
        else [r for r in renderer.manifest.records if r.source_key == "metadata.cmp"]
    assert cmp_records, "expected at least one metric to reference metadata.cmp"
    for r in cmp_records:
        value = r.resolved_value if hasattr(r, "resolved_value") else r["resolved_value"]
        assert "999.5" in value
