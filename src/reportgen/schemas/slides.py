from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.blocks import BulletBlock, MetricsBlock, TextBlock
from reportgen.schemas.charts import ChartBlock
from reportgen.schemas.common import NonEmptyString
from reportgen.schemas.tables import TableBlock

SlideLayout = Literal[
    "cover_slide",
    "investment_thesis",
    "company_snapshot",
    "text_plus_bullets",
    "text_plus_chart",
    "full_width_chart",
    "full_table",
    "valuation_summary",
    "risks_and_catalysts",
    "disclaimer",
    "peer_comparison",
    "valuation_table",
    "quarterly_summary",
    "ratio_summary",
    "dcf_summary",
    "segment_mix",
    "price_performance",
    "industry_overview",
    "saarthi_scorecard",
    "management_profile",
    "forensic_assessment",
    "trading_strategy",
    "key_highlights",
    "analyst_certification",
]

SlideBlock = TextBlock | BulletBlock | MetricsBlock | ChartBlock | TableBlock


class SlideSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slide_id: NonEmptyString
    layout: SlideLayout
    title: NonEmptyString
    subtitle: str | None = None
    blocks: list[SlideBlock] = Field(default_factory=list)
