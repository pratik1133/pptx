from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from reportgen.schemas.common import NonEmptyString
from reportgen.schemas.slides import SlideLayout


class PlanningTextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"] = "text"
    key: NonEmptyString
    content: str = Field(min_length=1)


class PlanningBulletBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["bullets"] = "bullets"
    key: NonEmptyString
    items: list[NonEmptyString] = Field(min_length=1, max_length=8)


class PlanningMetricItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: NonEmptyString
    source_key: NonEmptyString
    display_hint: str | None = None


class PlanningMetricsBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["metrics"] = "metrics"
    key: NonEmptyString
    items: list[PlanningMetricItem] = Field(min_length=1, max_length=8)


class PlanningChartBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["chart"] = "chart"
    key: NonEmptyString
    chart_type: Literal["bar", "line", "stacked_bar", "combo", "donut"]
    title: NonEmptyString
    category_source: NonEmptyString
    series_source_keys: list[NonEmptyString] = Field(min_length=1)


class PlanningTableColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: NonEmptyString
    label: NonEmptyString


class PlanningTableBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["table"] = "table"
    key: NonEmptyString
    title: NonEmptyString
    source_key: NonEmptyString
    columns: list[PlanningTableColumn] = Field(min_length=1)


PlanningBlock = (
    PlanningTextBlock
    | PlanningBulletBlock
    | PlanningMetricsBlock
    | PlanningChartBlock
    | PlanningTableBlock
)


class SlidePlanSlide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slide_id: NonEmptyString
    layout: SlideLayout
    title: NonEmptyString
    subtitle: str | None = None
    rationale: str | None = None
    blocks: list[PlanningBlock] = Field(default_factory=list)


class SlidePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    company_ticker: NonEmptyString
    generated_at: datetime
    slides: list[SlidePlanSlide] = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_unique_slide_ids(self) -> "SlidePlan":
        slide_ids = [slide.slide_id.casefold() for slide in self.slides]
        if len(slide_ids) != len(set(slide_ids)):
            raise ValueError("Slide plan slide_id values must be unique.")
        return self
