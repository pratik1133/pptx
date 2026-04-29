from pathlib import Path

import pytest

from reportgen.ai.planner import plan_slides_mock
from reportgen.ingestion.errors import InputValidationError
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.schemas.planning import PlanningTextBlock
from reportgen.planning.slide_plan_validator import validate_slide_plan


def test_mock_slide_plan_validates() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    plan = plan_slides_mock(bundle)

    assert len(plan.slides) >= 5
    assert any(slide.layout == "disclaimer" for slide in plan.slides)
    assert any(slide.layout == "full_table" for slide in plan.slides)


def test_slide_plan_validation_rejects_unknown_source_key() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    plan = plan_slides_mock(bundle)
    plan.slides[0].blocks[0].items[0].source_key = "metadata.fake_field"  # type: ignore[attr-defined]

    with pytest.raises(InputValidationError) as exc:
        validate_slide_plan(plan, bundle)

    assert "unknown source" in str(exc.value).lower()


def test_slide_plan_validation_rejects_missing_required_chart_block() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))
    plan = plan_slides_mock(bundle)
    plan.slides[3].blocks = [PlanningTextBlock(key="trend_summary", content="Only text remains.")]

    with pytest.raises(InputValidationError) as exc:
        validate_slide_plan(plan, bundle)

    assert "requires at least 1 'chart' block" in str(exc.value).lower()
