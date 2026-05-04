from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import ValidationError

from reportgen.ingestion.errors import InputValidationError
from reportgen.schemas.planning import SlidePlan


@dataclass
class ParseOutcome:
    plan: SlidePlan | None
    errors: list[str]


def _extract_json(raw_text: str) -> str | None:
    if not raw_text:
        return None
    fenced_start = raw_text.find("```json")
    if fenced_start != -1:
        body_start = raw_text.find("\n", fenced_start) + 1
        fenced_end = raw_text.find("```", body_start)
        if fenced_end != -1:
            return raw_text[body_start:fenced_end].strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return raw_text[start : end + 1]


def parse_slide_plan_safely(raw_text: str) -> ParseOutcome:
    candidate = _extract_json(raw_text)
    if candidate is None:
        return ParseOutcome(plan=None, errors=["Model output did not contain a JSON object."])

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return ParseOutcome(plan=None, errors=[f"JSON could not be parsed: {exc.msg} (line {exc.lineno}, col {exc.colno})."])

    try:
        plan = SlidePlan.model_validate(payload)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", ()))
            errors.append(f"Schema error at `{loc}`: {err.get('msg', 'invalid')}.")
        return ParseOutcome(plan=None, errors=errors)

    return ParseOutcome(plan=plan, errors=[])


def repair_and_parse_slide_plan(raw_text: str) -> SlidePlan:
    outcome = parse_slide_plan_safely(raw_text)
    if outcome.plan is None:
        raise InputValidationError(outcome.errors)
    return outcome.plan
