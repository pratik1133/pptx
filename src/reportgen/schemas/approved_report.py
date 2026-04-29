from pydantic import BaseModel, ConfigDict, Field, computed_field

from reportgen.schemas.common import NonEmptyString


class ApprovedReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str = Field(min_length=1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def title(self) -> str:
        for line in self.markdown.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped.removeprefix("# ").strip()
        return "Approved Report"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def section_count(self) -> int:
        return sum(1 for line in self.markdown.splitlines() if line.strip().startswith("## "))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def preview(self) -> NonEmptyString:
        for line in self.markdown.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return "No preview available."
