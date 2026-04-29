import json
from pathlib import Path

from reportgen.schemas.metadata import ResearchMetadata


def load_research_metadata(path: Path) -> ResearchMetadata:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ResearchMetadata.model_validate(payload)
