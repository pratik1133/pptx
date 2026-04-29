from pydantic import BaseModel, ConfigDict, Field

from reportgen.rendering.geometry import Box, PlaceholderGeometry
from reportgen.schemas.common import NonEmptyString
from reportgen.schemas.slides import SlideLayout


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


LAYOUT_REGISTRY: dict[SlideLayout, LayoutDefinition] = {
    "cover_slide": LayoutDefinition(
        layout="cover_slide",
        display_name="Cover Slide",
        allowed_block_types={"text", "metrics"},
        required_blocks=[BlockRequirement(block_type="metrics", min_count=1, max_count=1)],
        placeholders=[
            _ph("title", 0.7, 0.8, 8.6, 0.8),
            _ph("subtitle", 0.7, 1.7, 7.8, 0.5),
            _ph("metrics", 0.7, 5.5, 8.0, 1.2),
        ],
        notes="Used for report title, recommendation, and headline metrics.",
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
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("text", 0.7, 1.3, 3.8, 4.5),
            _ph("bullets", 5.0, 1.3, 4.0, 4.8),
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
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("text", 0.7, 1.4, 4.5, 3.8),
            _ph("metrics", 5.5, 1.4, 3.4, 3.0),
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
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("text", 0.7, 1.4, 4.0, 4.5),
            _ph("bullets", 5.0, 1.4, 4.0, 4.5),
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
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("text", 0.7, 1.4, 3.3, 4.6),
            _ph("chart", 4.3, 1.2, 4.7, 4.8),
        ],
    ),
    "full_width_chart": LayoutDefinition(
        layout="full_width_chart",
        display_name="Full Width Chart",
        allowed_block_types={"chart"},
        required_blocks=[BlockRequirement(block_type="chart", min_count=1, max_count=1)],
        placeholders=[
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("chart", 0.7, 1.4, 8.3, 4.9),
        ],
    ),
    "full_table": LayoutDefinition(
        layout="full_table",
        display_name="Full Table",
        allowed_block_types={"table"},
        required_blocks=[BlockRequirement(block_type="table", min_count=1, max_count=1)],
        placeholders=[
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("table", 0.7, 1.3, 8.3, 5.1),
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
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("text", 0.7, 1.3, 3.4, 1.7),
            _ph("metrics", 4.4, 1.2, 4.6, 1.8),
            _ph("table", 0.7, 3.2, 8.3, 3.2),
        ],
    ),
    "risks_and_catalysts": LayoutDefinition(
        layout="risks_and_catalysts",
        display_name="Risks And Catalysts",
        allowed_block_types={"bullets", "text"},
        required_blocks=[BlockRequirement(block_type="bullets", min_count=1, max_count=1)],
        placeholders=[
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("bullets", 0.8, 1.4, 8.0, 4.8),
        ],
    ),
    "disclaimer": LayoutDefinition(
        layout="disclaimer",
        display_name="Disclaimer",
        allowed_block_types={"text"},
        required_blocks=[BlockRequirement(block_type="text", min_count=1, max_count=1)],
        placeholders=[
            _ph("title", 0.6, 0.5, 8.5, 0.6),
            _ph("text", 0.8, 1.4, 8.0, 4.9),
        ],
    ),
}


def get_layout_definition(layout: SlideLayout) -> LayoutDefinition:
    return LAYOUT_REGISTRY[layout]
