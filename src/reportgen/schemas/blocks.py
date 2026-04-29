from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"] = "text"
    key: NonEmptyString
    content: str = Field(min_length=1)


class BulletBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["bullets"] = "bullets"
    key: NonEmptyString
    items: list[NonEmptyString] = Field(min_length=1, max_length=8)


class MetricItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: NonEmptyString
    value: str | Decimal
    source: NonEmptyString | None = None


class MetricsBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["metrics"] = "metrics"
    key: NonEmptyString
    items: list[MetricItem] = Field(min_length=1, max_length=8)
