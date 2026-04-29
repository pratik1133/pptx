from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class TableColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: NonEmptyString
    label: NonEmptyString


class TableBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["table"] = "table"
    key: NonEmptyString
    title: NonEmptyString
    source_key: NonEmptyString
    columns: list[TableColumn] = Field(min_length=1)
