import json

from reportgen.ingestion.errors import InputValidationError
from reportgen.schemas.planning import SlidePlan


def repair_and_parse_slide_plan(raw_text: str) -> SlidePlan:
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise InputValidationError(["Model output did not contain a valid JSON object."])

    candidate = raw_text[start : end + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InputValidationError([f"Model output contained invalid JSON: {exc.msg}."]) from exc

    return SlidePlan.model_validate(payload)
