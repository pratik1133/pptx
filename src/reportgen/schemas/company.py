from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    ticker: NonEmptyString
    exchange: NonEmptyString = "NSE"
    sector: NonEmptyString
    industry: NonEmptyString | None = None
    isin: NonEmptyString | None = None
    country: NonEmptyString = "India"
    description: str | None = None
    peer_list: list[NonEmptyString] = Field(default_factory=list)
