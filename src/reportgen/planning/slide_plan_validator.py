import re

from reportgen.config import settings
from reportgen.ingestion.errors import InputValidationError
from reportgen.planning.layout_policy import ALLOWED_LAYOUTS, MANDATORY_LAYOUTS
from reportgen.planning.narrative_constraints import FORBIDDEN_PHRASES
from reportgen.rendering.layout_registry import get_layout_definition
from reportgen.schemas.bundle import NormalizedInputBundle
from reportgen.schemas.planning import (
    PlanningBulletBlock,
    PlanningChartBlock,
    PlanningMetricsBlock,
    PlanningTableBlock,
    PlanningTextBlock,
    SlidePlan,
)


TABLE_COLUMN_KEYS: dict[str, set[str]] = {
    "peers": {"name", "ticker", "market_cap", "pe", "ev_ebitda", "pb", "roe", "revenue_growth"},
    "valuation_bands": {"method", "low", "base", "high", "weight", "notes"},
    "scenarios": {"name", "revenue_cagr", "ebitda_margin", "target_price", "probability", "notes"},
    "segments": {"name", "revenue_share", "ebitda_share", "growth", "aum_label", "aum_value", "description"},
    "saarthi_dimensions": {"code", "name", "score", "assessment", "evidence"},
    "management_team": {"name", "role", "bio"},
    "forensic_violations": {"title", "description", "severity"},
}


def _looks_like_dash_artifact(item: str) -> bool:
    stripped = item.lstrip()
    return stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• ")


# Tokens with attached units that look like financial figures planted in prose.
# Examples flagged: "37%", "₹822.90", "12.3x", "4,907 Cr", "INR 1127", "70 bps".
# Allowed in prose: bare years ("2024"), FY tokens ("FY26E"), counts ("7-dimension", "6 segments").
_ORPHAN_NUMBER_RE = re.compile(
    r"(?<!FY)(?<!fy)\b\d[\d,]*(?:\.\d+)?\s*(?:%|x\b|cr\b|crore\b|bn\b|billion\b|lakh\b|bps\b)"
    r"|(?:₹|\$|€|£|INR\s|USD\s|EUR\s|GBP\s)\s*\d[\d,]*(?:\.\d+)?",
    re.IGNORECASE,
)


def _find_orphan_numbers(text: str) -> list[str]:
    return _ORPHAN_NUMBER_RE.findall(text)


def _valid_source_keys(bundle: NormalizedInputBundle) -> set[str]:
    refs = bundle.data_references
    keys = {
        "company.name",
        "company.ticker",
        "company.sector",
        "metadata.rating",
        "metadata.cmp",
        "metadata.target_price",
        "metadata.analyst",
        "period_labels",
        *refs.metric_source_keys,
        *refs.series_source_keys,
        *refs.quarterly_series_source_keys,
        *refs.ratio_source_keys,
    }
    if bundle.source.metadata.upside_pct is not None:
        keys.add("metadata.upside_pct")
    if refs.has_quarterly:
        keys.add("period_labels.quarterly")
    if refs.has_peers:
        keys.add("peers")
    if refs.has_valuation_bands:
        keys.add("valuation_bands")
    if refs.has_scenarios:
        keys.add("scenarios")
    if refs.has_segments:
        keys.update({"segments", "segments.revenue_share", "segments.ebitda_share"})
    if refs.has_ratios:
        keys.add("ratio_summary")
    if refs.has_saarthi:
        keys.update({"saarthi_dimensions", "saarthi.total_score", "saarthi.max_score"})
    if refs.has_management:
        keys.add("management_team")
    if refs.has_forensic:
        keys.update({"forensic_violations", "forensic.category"})
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
                valid_category_sources = {"period_labels"}
                if bundle.data_references.has_quarterly:
                    valid_category_sources.add("period_labels.quarterly")
                if block.category_source not in valid_category_sources:
                    errors.append(
                        f"Slide {slide.slide_id} chart block category_source must be one of "
                        f"{sorted(valid_category_sources)}; got '{block.category_source}'."
                    )
                valid_series_sources = set(bundle.data_references.series_source_keys) | set(
                    bundle.data_references.quarterly_series_source_keys
                )
                for source_key in block.series_source_keys:
                    if source_key not in valid_series_sources:
                        errors.append(
                            f"Slide {slide.slide_id} chart block series source '{source_key}' is not a valid series key. "
                            f"Allowed: {sorted(valid_series_sources)}."
                        )

            if isinstance(block, PlanningTableBlock):
                if block.source_key not in valid_source_keys:
                    errors.append(
                        f"Slide {slide.slide_id} table block references unknown source '{block.source_key}'."
                    )
                else:
                    allowed_columns = TABLE_COLUMN_KEYS.get(block.source_key)
                    if allowed_columns is not None:
                        bad = [c.key for c in block.columns if c.key not in allowed_columns]
                        if bad:
                            errors.append(
                                f"Slide {slide.slide_id} table block source '{block.source_key}' has invalid column keys {bad}. "
                                f"Allowed column keys: {sorted(allowed_columns)}."
                            )

            if isinstance(block, PlanningTextBlock):
                lowered = block.content.casefold()
                for phrase in FORBIDDEN_PHRASES:
                    if phrase in lowered:
                        errors.append(
                            f"Slide {slide.slide_id} contains forbidden narrative phrase '{phrase}'."
                        )
                orphans = _find_orphan_numbers(block.content)
                if orphans:
                    errors.append(
                        f"Slide {slide.slide_id} text block '{block.key}' contains orphan numeric tokens "
                        f"{orphans[:3]} — numbers must come from `source_key` references in metric/table/chart blocks, "
                        "not embedded in prose. Rewrite the prose to describe direction/driver and surface the figures via metric/table blocks."
                    )

            if isinstance(block, PlanningBulletBlock):
                for index, item in enumerate(block.items):
                    if _looks_like_dash_artifact(item):
                        errors.append(
                            f"Slide {slide.slide_id} bullet {index + 1} starts with a dash/asterisk — "
                            "bullets must be clean prose without leading list markers."
                        )
                    lowered = item.casefold()
                    for phrase in FORBIDDEN_PHRASES:
                        if phrase in lowered:
                            errors.append(
                                f"Slide {slide.slide_id} bullet {index + 1} contains forbidden phrase '{phrase}'."
                            )
                    orphans = _find_orphan_numbers(item)
                    if orphans:
                        errors.append(
                            f"Slide {slide.slide_id} bullet {index + 1} contains orphan numeric tokens "
                            f"{orphans[:3]} — bullets must be qualitative; expose figures via metric/table blocks."
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
