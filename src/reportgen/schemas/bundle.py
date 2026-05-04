from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.approved_report import ApprovedReport
from reportgen.schemas.company import CompanyProfile
from reportgen.schemas.financials import FinancialModelSnapshot
from reportgen.schemas.metadata import ResearchMetadata
from reportgen.schemas.common import NonEmptyString


class InputBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_path: Path
    metadata_path: Path
    financial_model_path: Path
    approved_report_path: Path


class LoadedInputBundle(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    bundle_path: Path
    company_path: Path
    metadata_path: Path
    financial_model_path: Path
    approved_report_path: Path
    company: CompanyProfile
    metadata: ResearchMetadata
    financial_model: FinancialModelSnapshot
    approved_report: ApprovedReport


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: NonEmptyString
    body: str = Field(min_length=1)


class DataReferenceCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_keys: list[NonEmptyString] = Field(default_factory=list)
    metric_source_keys: list[NonEmptyString] = Field(default_factory=list)
    series_names: list[NonEmptyString] = Field(default_factory=list)
    series_source_keys: list[NonEmptyString] = Field(default_factory=list)
    quarterly_series_source_keys: list[NonEmptyString] = Field(default_factory=list)
    ratio_source_keys: list[NonEmptyString] = Field(default_factory=list)
    period_labels: list[NonEmptyString] = Field(default_factory=list)
    has_peers: bool = False
    has_quarterly: bool = False
    has_segments: bool = False
    has_valuation_bands: bool = False
    has_scenarios: bool = False
    has_ratios: bool = False
    has_saarthi: bool = False
    has_management: bool = False
    has_forensic: bool = False
    has_key_highlights: bool = False
    has_competitive_advantages: bool = False
    has_industry_tailwinds: bool = False
    has_industry_risks: bool = False
    has_trading_strategy: bool = False


class NormalizedInputBundle(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    source: LoadedInputBundle
    primary_title: NonEmptyString
    report_sections: list[ReportSection] = Field(default_factory=list)
    normalized_rating: NonEmptyString
    normalized_currency: NonEmptyString
    normalized_ticker: NonEmptyString
    normalized_exchange: NonEmptyString
    headline_metrics: dict[NonEmptyString, str] = Field(default_factory=dict)
    data_references: DataReferenceCatalog
