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


class PeerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    ticker: NonEmptyString | None = None
    market_cap_cr: Decimal | None = None
    pe: Decimal | None = None
    ev_ebitda: Decimal | None = None
    pb: Decimal | None = None
    roe_pct: Decimal | None = None
    revenue_growth_pct: Decimal | None = None
    is_target: bool = False


class ValuationBand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: NonEmptyString
    low: Decimal
    base: Decimal
    high: Decimal
    weight_pct: Decimal | None = None
    notes: str | None = None


class ScenarioEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    revenue_cagr_pct: Decimal | None = None
    ebitda_margin_pct: Decimal | None = None
    target_price: Decimal | None = None
    probability_pct: Decimal | None = None
    notes: str | None = None


class SegmentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    revenue_share_pct: Decimal | None = None
    ebitda_share_pct: Decimal | None = None
    growth_pct: Decimal | None = None
    aum_or_book_label: str | None = None
    aum_or_book_value: str | None = None
    description: str | None = None


class RatioEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    unit: NonEmptyString = "%"
    periods: list[NonEmptyString] = Field(min_length=1)
    values: list[Decimal | None] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_lengths(self) -> "RatioEntry":
        if len(self.periods) != len(self.values):
            raise ValueError("Ratio periods and values must have the same length.")
        return self


class SaarthiDimension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: NonEmptyString
    name: NonEmptyString
    score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    assessment: str | None = None
    key_evidence: str | None = None


class SaarthiScorecard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    rating: NonEmptyString | None = None
    dimensions: list[SaarthiDimension] = Field(default_factory=list)


class ManagementMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    role: NonEmptyString
    bio: str = ""


class ForensicViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyString
    description: str = ""
    severity: NonEmptyString


class ForensicAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: NonEmptyString
    overall_assessment: str = ""
    violations: list[ForensicViolation] = Field(default_factory=list)


class KeyHighlight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyString
    body: str


class TradingStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_range: NonEmptyString | None = None
    entry_rationale: str | None = None
    position_size: NonEmptyString | None = None
    review_frequency: NonEmptyString | None = None
    review_metrics: list[NonEmptyString] = Field(default_factory=list)
    upside_exit: list[NonEmptyString] = Field(default_factory=list)
    downside_exit: NonEmptyString | None = None
    thesis_breaking_exits: list[NonEmptyString] = Field(default_factory=list)


class FinancialModelSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: NonEmptyString
    model_version: NonEmptyString
    currency: NonEmptyString = "INR"
    fiscal_year_end: NonEmptyString
    metrics: dict[NonEmptyString, Decimal | str]
    series: list[FinancialSeries] = Field(default_factory=list)
    quarterly_series: list[FinancialSeries] = Field(default_factory=list)
    segments: list[SegmentEntry] = Field(default_factory=list)
    peers: list[PeerEntry] = Field(default_factory=list)
    valuation_bands: list[ValuationBand] = Field(default_factory=list)
    scenarios: list[ScenarioEntry] = Field(default_factory=list)
    ratios: list[RatioEntry] = Field(default_factory=list)
    saarthi: SaarthiScorecard | None = None
    management_team: list[ManagementMember] = Field(default_factory=list)
    forensic: ForensicAssessment | None = None
    key_highlights: list[KeyHighlight] = Field(default_factory=list)
    competitive_advantages: list[NonEmptyString] = Field(default_factory=list)
    industry_tailwinds: list[NonEmptyString] = Field(default_factory=list)
    industry_risks: list[NonEmptyString] = Field(default_factory=list)
    trading_strategy: TradingStrategy | None = None
