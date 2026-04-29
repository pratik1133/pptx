import json

from reportgen.schemas.planning import SlidePlan


def parse_slide_plan_json(payload: str) -> SlidePlan:
    return SlidePlan.model_validate(json.loads(payload))


def dump_slide_plan_json(plan: SlidePlan) -> str:
    return plan.model_dump_json(indent=2)
