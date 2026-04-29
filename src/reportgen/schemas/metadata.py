from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class ResearchMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: NonEmptyString
    currency: NonEmptyString = "INR"
    cmp: Decimal = Field(..., ge=0)
    target_price: Decimal = Field(..., ge=0)
    upside_pct: Decimal | None = None
    market_cap: Decimal | None = Field(default=None, ge=0)
    analyst: NonEmptyString
    report_date: date
    report_type: NonEmptyString = "Initiation"
