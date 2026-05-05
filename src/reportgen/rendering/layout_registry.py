from pydantic import BaseModel, ConfigDict, Field

from reportgen.rendering.geometry import Box, PlaceholderGeometry
from reportgen.schemas.common import NonEmptyString
from reportgen.schemas.slides import SlideLayout

# Canvas: 16:9 at 13.333 x 7.5 in.
# Reserved zones (interior slides):
#   header band:  y=0.00..0.45 (brand_shell)
#   title:        y=0.60..1.15
#   divider line: y=1.20
#   content area: y=1.35..7.05
#   footer band:  y=7.15..7.50 (brand_shell)
# Side margin: 0.5 in
SIDE = 0.5
CANVAS_W = 13.333
CONTENT_W = CANVAS_W - 2 * SIDE
TITLE_TOP = 0.60
TITLE_H = 0.55
SUBTITLE_TOP = 1.18
SUBTITLE_H = 0.30
CONTENT_TOP = 1.55
CONTENT_BOTTOM = 7.05
CONTENT_H = CONTENT_BOTTOM - CONTENT_TOP


class BlockRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_type: NonEmptyString
    min_count: int = Field(ge=0)
    max_count: int | None = Field(default=None, ge=1)


class LayoutDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout: SlideLayout
    display_name: NonEmptyString
    allowed_block_types: set[NonEmptyString]
    required_blocks: list[BlockRequirement] = Field(default_factory=list)
    placeholders: list[PlaceholderGeometry] = Field(default_factory=list)
    notes: str | None = None


def _ph(name: str, left: float, top: float, width: float, height: float) -> PlaceholderGeometry:
    return PlaceholderGeometry(name=name, box=Box(left=left, top=top, width=width, height=height))


def _title(top: float = TITLE_TOP, height: float = TITLE_H) -> PlaceholderGeometry:
    return _ph("title", SIDE, top, CONTENT_W, height)


def _subtitle() -> PlaceholderGeometry:
    return _ph("subtitle", SIDE, SUBTITLE_TOP, CONTENT_W, SUBTITLE_H)


LAYOUT_REGISTRY: dict[SlideLayout, LayoutDefinition] = {
    "cover_slide": LayoutDefinition(
        layout="cover_slide",
        display_name="Cover Slide",
        allowed_block_types={"text", "metrics", "bullets"},
        required_blocks=[BlockRequirement(block_type="metrics", min_count=1, max_count=1)],
        placeholders=[
            _ph("title", 0.6, 1.5, 12.0, 1.4),
            _ph("subtitle", 0.6, 2.95, 12.0, 0.6),
            _ph("metrics", 0.6, 5.6, 12.0, 1.2),
        ],
        notes="Cover slide uses cover_shell, not interior_shell. Hero treatment with rating badge.",
    ),
    "investment_thesis": LayoutDefinition(
        layout="investment_thesis",
        display_name="Investment Thesis",
        allowed_block_types={"text", "bullets"},
        required_blocks=[
            BlockRequirement(block_type="text", min_count=1, max_count=1),
            BlockRequirement(block_type="bullets", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 5.6, CONTENT_H),
            _ph("bullets", SIDE + 5.9, CONTENT_TOP, CONTENT_W - 5.9, CONTENT_H),
        ],
    ),
    "company_snapshot": LayoutDefinition(
        layout="company_snapshot",
        display_name="Company Snapshot",
        allowed_block_types={"text", "metrics"},
        required_blocks=[
            BlockRequirement(block_type="text", min_count=1, max_count=1),
            BlockRequirement(block_type="metrics", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 6.5, CONTENT_H),
            _ph("metrics", SIDE + 6.8, CONTENT_TOP, CONTENT_W - 6.8, CONTENT_H),
        ],
    ),
    "text_plus_bullets": LayoutDefinition(
        layout="text_plus_bullets",
        display_name="Text Plus Bullets",
        allowed_block_types={"text", "bullets"},
        required_blocks=[
            BlockRequirement(block_type="text", min_count=1, max_count=1),
            BlockRequirement(block_type="bullets", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 6.0, CONTENT_H),
            _ph("bullets", SIDE + 6.3, CONTENT_TOP, CONTENT_W - 6.3, CONTENT_H),
        ],
    ),
    "text_plus_chart": LayoutDefinition(
        layout="text_plus_chart",
        display_name="Text Plus Chart",
        allowed_block_types={"text", "chart"},
        required_blocks=[
            BlockRequirement(block_type="text", min_count=1, max_count=1),
            BlockRequirement(block_type="chart", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 4.8, CONTENT_H),
            _ph("chart", SIDE + 5.1, CONTENT_TOP, CONTENT_W - 5.1, CONTENT_H),
        ],
    ),
    "full_width_chart": LayoutDefinition(
        layout="full_width_chart",
        display_name="Full Width Chart",
        allowed_block_types={"chart"},
        required_blocks=[BlockRequirement(block_type="chart", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("chart", SIDE, CONTENT_TOP, CONTENT_W, CONTENT_H),
        ],
    ),
    "full_table": LayoutDefinition(
        layout="full_table",
        display_name="Full Table",
        allowed_block_types={"table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("table", SIDE, CONTENT_TOP, CONTENT_W, CONTENT_H),
        ],
    ),
    "valuation_summary": LayoutDefinition(
        layout="valuation_summary",
        display_name="Valuation Summary",
        allowed_block_types={"text", "metrics", "table"},
        required_blocks=[
            BlockRequirement(block_type="text", min_count=1, max_count=1),
            BlockRequirement(block_type="metrics", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("metrics", SIDE, CONTENT_TOP, CONTENT_W, 1.4),
            _ph("text", SIDE, CONTENT_TOP + 1.55, CONTENT_W, CONTENT_H - 1.55),
            _ph("table", SIDE, CONTENT_TOP + 1.55, CONTENT_W, CONTENT_H - 1.55),
        ],
    ),
    "risks_and_catalysts": LayoutDefinition(
        layout="risks_and_catalysts",
        display_name="Risks And Catalysts",
        allowed_block_types={"bullets", "text"},
        required_blocks=[BlockRequirement(block_type="bullets", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("bullets", SIDE, CONTENT_TOP, CONTENT_W, CONTENT_H),
        ],
    ),
    "disclaimer": LayoutDefinition(
        layout="disclaimer",
        display_name="Disclaimer",
        allowed_block_types={"text"},
        required_blocks=[BlockRequirement(block_type="text", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, CONTENT_H),
        ],
    ),
    "analyst_certification": LayoutDefinition(
        layout="analyst_certification",
        display_name="Analyst Certification",
        allowed_block_types={"text"},
        required_blocks=[BlockRequirement(block_type="text", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, CONTENT_H),
        ],
    ),
    "peer_comparison": LayoutDefinition(
        layout="peer_comparison",
        display_name="Peer Comparison",
        allowed_block_types={"text", "table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("table", SIDE, CONTENT_TOP + 0.85, CONTENT_W, CONTENT_H - 0.85),
        ],
    ),
    "valuation_table": LayoutDefinition(
        layout="valuation_table",
        display_name="Valuation — Methods Summary",
        allowed_block_types={"text", "table", "metrics"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("table", SIDE, CONTENT_TOP + 0.85, CONTENT_W, 3.4),
            _ph("metrics", SIDE, CONTENT_TOP + 4.4, CONTENT_W, CONTENT_H - 4.4),
        ],
    ),
    "quarterly_summary": LayoutDefinition(
        layout="quarterly_summary",
        display_name="Quarterly Summary",
        allowed_block_types={"text", "table", "chart"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("table", SIDE, CONTENT_TOP + 0.85, CONTENT_W, CONTENT_H - 0.85),
        ],
    ),
    "ratio_summary": LayoutDefinition(
        layout="ratio_summary",
        display_name="Key Ratios",
        allowed_block_types={"text", "table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("table", SIDE, CONTENT_TOP + 0.85, CONTENT_W, CONTENT_H - 0.85),
        ],
    ),
    "dcf_summary": LayoutDefinition(
        layout="dcf_summary",
        display_name="DCF Summary",
        allowed_block_types={"text", "metrics", "table"},
        required_blocks=[
            BlockRequirement(block_type="metrics", min_count=1, max_count=1),
            BlockRequirement(block_type="text", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 5.5, CONTENT_H),
            _ph("metrics", SIDE + 5.8, CONTENT_TOP, CONTENT_W - 5.8, 1.7),
            _ph("table", SIDE + 5.8, CONTENT_TOP + 1.85, CONTENT_W - 5.8, CONTENT_H - 1.85),
        ],
    ),
    "segment_mix": LayoutDefinition(
        layout="segment_mix",
        display_name="Segment Mix",
        allowed_block_types={"text", "chart", "table"},
        required_blocks=[BlockRequirement(block_type="chart", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 4.8, 2.4),
            _ph("chart", SIDE + 5.1, CONTENT_TOP, CONTENT_W - 5.1, 2.4),
            _ph("table", SIDE, CONTENT_TOP + 2.55, CONTENT_W, CONTENT_H - 2.55),
        ],
    ),
    "price_performance": LayoutDefinition(
        layout="price_performance",
        display_name="Price Performance",
        allowed_block_types={"text", "chart", "metrics"},
        required_blocks=[BlockRequirement(block_type="chart", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("chart", SIDE, CONTENT_TOP + 0.85, CONTENT_W, CONTENT_H - 0.85),
        ],
    ),
    "industry_overview": LayoutDefinition(
        layout="industry_overview",
        display_name="Industry Overview",
        allowed_block_types={"text", "bullets", "metrics"},
        required_blocks=[
            BlockRequirement(block_type="text", min_count=1, max_count=1),
            BlockRequirement(block_type="bullets", min_count=1, max_count=1),
        ],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, 6.0, CONTENT_H),
            _ph("bullets", SIDE + 6.3, CONTENT_TOP, CONTENT_W - 6.3, CONTENT_H),
        ],
    ),
    "saarthi_scorecard": LayoutDefinition(
        layout="saarthi_scorecard",
        display_name="SAARTHI Scorecard",
        allowed_block_types={"text", "table", "metrics"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("metrics", SIDE, CONTENT_TOP + 0.85, CONTENT_W, 0.9),
            _ph("table", SIDE, CONTENT_TOP + 1.85, CONTENT_W, CONTENT_H - 1.85),
        ],
    ),
    "management_profile": LayoutDefinition(
        layout="management_profile",
        display_name="Management Team",
        allowed_block_types={"text", "table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.7),
            _ph("table", SIDE, CONTENT_TOP + 0.85, CONTENT_W, CONTENT_H - 0.85),
        ],
    ),
    "forensic_assessment": LayoutDefinition(
        layout="forensic_assessment",
        display_name="Forensic / Governance Assessment",
        allowed_block_types={"text", "table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.9),
            _ph("table", SIDE, CONTENT_TOP + 1.05, CONTENT_W, CONTENT_H - 1.05),
        ],
    ),
    "trading_strategy": LayoutDefinition(
        layout="trading_strategy",
        display_name="Trading Strategy",
        allowed_block_types={"text", "metrics", "bullets"},
        required_blocks=[BlockRequirement(block_type="bullets", min_count=1, max_count=2)],
        placeholders=[
            _title(),
            _ph("metrics", SIDE, CONTENT_TOP, CONTENT_W, 0.95),
            _ph("text", SIDE, CONTENT_TOP + 1.1, 6.0, CONTENT_H - 1.1),
            _ph("bullets", SIDE + 6.3, CONTENT_TOP + 1.1, CONTENT_W - 6.3, CONTENT_H - 1.1),
        ],
    ),
    "key_highlights": LayoutDefinition(
        layout="key_highlights",
        display_name="Key Highlights",
        allowed_block_types={"text", "bullets"},
        required_blocks=[BlockRequirement(block_type="bullets", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("text", SIDE, CONTENT_TOP, CONTENT_W, 0.6),
            _ph("bullets", SIDE, CONTENT_TOP + 0.75, CONTENT_W, CONTENT_H - 0.75),
        ],
    ),
    "scenario_analysis": LayoutDefinition(
        layout="scenario_analysis",
        display_name="Scenario Analysis",
        allowed_block_types={"text", "table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _title(),
            _ph("table", SIDE, CONTENT_TOP, CONTENT_W, CONTENT_H),
        ],
    ),
}


def get_layout_definition(layout: SlideLayout) -> LayoutDefinition:
    return LAYOUT_REGISTRY[layout]
