from pathlib import Path

import pytest

from reportgen.ai.planner import plan_slides, plan_slides_with_client
from reportgen.ai.prompt_builder import (
    SYSTEM_PROMPT,
    _resolve_sector_file,
    build_slide_planner_prompt,
)
from reportgen.ai.repair import parse_slide_plan_safely
from reportgen.config import settings
from reportgen.ingestion.errors import InputValidationError
from reportgen.ingestion.loaders import load_normalized_input_bundle


MOTILAL_BUNDLE = Path("data/samples/bundles/motilal_bundle.json")
ABC_BUNDLE = Path("data/samples/bundles/abc_bundle.json")


def test_system_prompt_loaded_from_file():
    assert "equity-research" in SYSTEM_PROMPT.lower() or "tikona" in SYSTEM_PROMPT.lower()
    assert "json" in SYSTEM_PROMPT.lower()


def test_user_prompt_includes_company_data_and_layouts():
    bundle = load_normalized_input_bundle(MOTILAL_BUNDLE)
    prompt = build_slide_planner_prompt(
        bundle, min_slides=settings.min_slide_count, max_slides=settings.max_slide_count
    )
    assert "Motilal Oswal" in prompt
    assert "MOFSL" in prompt
    assert "saarthi_dimensions" in prompt
    assert "valuation_bands" in prompt
    assert "disclaimer" in prompt
    assert "Few-shot example" in prompt or "few-shot" in prompt.lower()


def test_sector_resolver_picks_financial_services_for_capital_markets():
    path = _resolve_sector_file("Financial Services")
    assert path.name == "financial_services.md"


def test_sector_resolver_falls_back_to_default_for_unknown_sector():
    path = _resolve_sector_file("Outer Space Mining")
    assert path.name == "default.md"


def test_repair_loop_extracts_json_from_fenced_block():
    raw = """Sure, here is the plan:

```json
{"schema_version": "1.0.0", "company_ticker": "ABC", "generated_at": "2026-04-28T00:00:00Z", "slides": []}
```
"""
    outcome = parse_slide_plan_safely(raw)
    assert outcome.plan is None
    assert any("at least 1 item" in e or "min_length" in e for e in outcome.errors)


def test_repair_loop_handles_no_json_at_all():
    outcome = parse_slide_plan_safely("Sorry, I cannot help with that.")
    assert outcome.plan is None
    assert "did not contain a JSON object" in outcome.errors[0]


def test_real_planner_with_failing_client_surfaces_errors():
    bundle = load_normalized_input_bundle(ABC_BUNDLE)

    class FailingClient:
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return "no json here"

    with pytest.raises(InputValidationError):
        plan_slides_with_client(bundle, FailingClient())


def test_default_plan_slides_falls_back_to_mock_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    bundle = load_normalized_input_bundle(ABC_BUNDLE)
    plan = plan_slides(bundle)
    assert len(plan.slides) >= 5
    assert any(s.layout == "disclaimer" for s in plan.slides)


def test_explicit_mock_flag_uses_mock_even_with_api_key(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    bundle = load_normalized_input_bundle(ABC_BUNDLE)
    plan = plan_slides(bundle, use_mock=True)
    assert any(s.layout == "disclaimer" for s in plan.slides)


def test_validator_rejects_dash_artifact_bullets():
    bundle = load_normalized_input_bundle(ABC_BUNDLE)
    plan = plan_slides(bundle, use_mock=True)
    bullet_slide = next(
        s for s in plan.slides if any(getattr(b, "type", None) == "bullets" for b in s.blocks)
    )
    bullet_block = next(b for b in bullet_slide.blocks if getattr(b, "type", None) == "bullets")
    bullet_block.items = ["- this looks like a markdown bullet artifact"]

    from reportgen.planning.slide_plan_validator import validate_slide_plan

    with pytest.raises(InputValidationError) as exc:
        validate_slide_plan(plan, bundle)
    assert "leading list markers" in str(exc.value).lower() or "starts with a dash" in str(exc.value).lower()
