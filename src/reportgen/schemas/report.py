from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.company import CompanyProfile
from reportgen.schemas.metadata import ResearchMetadata
from reportgen.schemas.slides import SlideSpec


class InputReferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    financial_model_ref: str
    approved_content_ref: str


class ReportSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.1.0"
    report_id: UUID
    run_id: UUID
    company: CompanyProfile
    metadata: ResearchMetadata
    inputs: InputReferences
    slides: list[SlideSpec] = Field(min_length=1)
