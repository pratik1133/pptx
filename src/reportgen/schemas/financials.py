from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from reportgen.schemas.common import NonEmptyString


class FinancialSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    unit: NonEmptyString
    periods: list[NonEmptyString] = Field(min_length=1)
    values: list[Decimal | None] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_lengths(self) -> "FinancialSeries":
        if len(self.periods) != len(self.values):
            raise ValueError("Financial series periods and values must have the same length.")
        return self


class FinancialModelSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: NonEmptyString
    model_version: NonEmptyString
    currency: NonEmptyString = "INR"
    fiscal_year_end: NonEmptyString
    metrics: dict[NonEmptyString, Decimal | str]
    series: list[FinancialSeries] = Field(default_factory=list)
