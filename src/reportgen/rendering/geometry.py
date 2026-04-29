from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class Box(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: float = Field(ge=0)
    top: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class PlaceholderGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    box: Box
