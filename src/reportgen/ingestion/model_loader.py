import json
from pathlib import Path

from reportgen.schemas.financials import FinancialModelSnapshot


def load_financial_model(path: Path) -> FinancialModelSnapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return FinancialModelSnapshot.model_validate(payload)
