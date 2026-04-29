from reportgen.config import settings
from reportgen.ingestion.errors import InputValidationError
from reportgen.planning.layout_policy import ALLOWED_LAYOUTS, MANDATORY_LAYOUTS
from reportgen.planning.narrative_constraints import FORBIDDEN_PHRASES
from reportgen.rendering.layout_registry import get_layout_definition
from reportgen.schemas.bundle import NormalizedInputBundle
from reportgen.schemas.planning import (
    PlanningChartBlock,
    PlanningMetricsBlock,
    PlanningTableBlock,
    PlanningTextBlock,
    SlidePlan,
)


def _valid_source_keys(bundle: NormalizedInputBundle) -> set[str]:
    keys = {
        "company.name",
        "company.ticker",
        "company.sector",
        "metadata.rating",
        "metadata.cmp",
        "metadata.target_price",
        "metadata.analyst",
        "period_labels",
        *bundle.data_references.metric_source_keys,
        *bundle.data_references.series_source_keys,
    }
    if bundle.source.metadata.upside_pct is not None:
        keys.add("metadata.upside_pct")
    return keys


def validate_slide_plan(plan: SlidePlan, bundle: NormalizedInputBundle) -> None:
    errors: list[str] = []

    if plan.company_ticker.upper() != bundle.normalized_ticker:
        errors.append(
            f"Slide plan ticker {plan.company_ticker} does not match normalized bundle ticker {bundle.normalized_ticker}."
        )

    slide_count = len(plan.slides)
    if slide_count < settings.min_slide_count or slide_count > settings.max_slide_count:
        errors.append(
            f"Slide plan must contain between {settings.min_slide_count} and {settings.max_slide_count} slides; got {slide_count}."
        )

    used_layouts = [slide.layout for slide in plan.slides]
    for layout in MANDATORY_LAYOUTS:
        if layout not in used_layouts:
            errors.append(f"Slide plan must include mandatory layout '{layout}'.")

    valid_source_keys = _valid_source_keys(bundle)

    for slide in plan.slides:
        if slide.layout not in ALLOWED_LAYOUTS:
            errors.append(f"Slide {slide.slide_id} uses unsupported layout '{slide.layout}'.")
            continue

        layout_definition = get_layout_definition(slide.layout)
        allowed_block_types = layout_definition.allowed_block_types
        type_counts: dict[str, int] = {}
        for block in slide.blocks:
            block_type = getattr(block, "type", "")
            type_counts[block_type] = type_counts.get(block_type, 0) + 1
            if block_type not in allowed_block_types:
                errors.append(
                    f"Slide {slide.slide_id} layout '{slide.layout}' does not allow block type '{block_type}'."
                )

            if isinstance(block, PlanningMetricsBlock):
                for item in block.items:
                    if item.source_key not in valid_source_keys:
                        errors.append(
                            f"Slide {slide.slide_id} metrics block references unknown source '{item.source_key}'."
                        )

            if isinstance(block, PlanningChartBlock):
                if block.category_source not in valid_source_keys:
                    errors.append(
                        f"Slide {slide.slide_id} chart block references unknown category source '{block.category_source}'."
                    )
                for source_key in block.series_source_keys:
                    if source_key not in valid_source_keys:
                        errors.append(
                            f"Slide {slide.slide_id} chart block references unknown series source '{source_key}'."
                        )

            if isinstance(block, PlanningTableBlock) and block.source_key not in valid_source_keys:
                errors.append(
                    f"Slide {slide.slide_id} table block references unknown source '{block.source_key}'."
                )

            if isinstance(block, PlanningTextBlock):
                lowered = block.content.casefold()
                for phrase in FORBIDDEN_PHRASES:
                    if phrase in lowered:
                        errors.append(
                            f"Slide {slide.slide_id} contains forbidden narrative phrase '{phrase}'."
                        )

        for requirement in layout_definition.required_blocks:
            actual_count = type_counts.get(requirement.block_type, 0)
            if actual_count < requirement.min_count:
                errors.append(
                    f"Slide {slide.slide_id} layout '{slide.layout}' requires at least "
                    f"{requirement.min_count} '{requirement.block_type}' block(s)."
                )
            if requirement.max_count is not None and actual_count > requirement.max_count:
                errors.append(
                    f"Slide {slide.slide_id} layout '{slide.layout}' allows at most "
                    f"{requirement.max_count} '{requirement.block_type}' block(s)."
                )

    if errors:
        raise InputValidationError(errors)
