from pathlib import Path

from reportgen.schemas.approved_report import ApprovedReport


def load_approved_report(path: Path) -> ApprovedReport:
    return ApprovedReport(markdown=path.read_text(encoding="utf-8"))
