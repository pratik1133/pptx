from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class ChartSeriesRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: NonEmptyString
    source_key: NonEmptyString


class ChartBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["chart"] = "chart"
    key: NonEmptyString
    chart_type: Literal["bar", "line", "stacked_bar", "combo", "donut"]
    title: NonEmptyString
    category_source: NonEmptyString
    series: list[ChartSeriesRef] = Field(min_length=1)
