import json
from pathlib import Path

from reportgen.schemas.company import CompanyProfile


def load_company_profile(path: Path) -> CompanyProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return CompanyProfile.model_validate(payload)
