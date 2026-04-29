from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from reportgen.schemas.financials import FinancialModelSnapshot, FinancialSeries
from reportgen.schemas.report import ReportSpec


@dataclass
class SeriesTableRow:
    period: str
    value: Decimal | None


class RenderDataResolver:
    def __init__(self, report_spec: ReportSpec) -> None:
        self.report_spec = report_spec
        self._financial_model: FinancialModelSnapshot | None = None

    @property
    def financial_model(self) -> FinancialModelSnapshot:
        if self._financial_model is None:
            model_path = Path(self.report_spec.inputs.financial_model_ref)
            payload = json.loads(model_path.read_text(encoding="utf-8"))
            self._financial_model = FinancialModelSnapshot.model_validate(payload)
        return self._financial_model

    def resolve_period_labels(self, source_key: str) -> list[str]:
        if source_key != "period_labels":
            raise KeyError(f"Unsupported category source: {source_key}")
        first_series = self.financial_model.series[0]
        return list(first_series.periods)

    def resolve_series(self, source_key: str) -> FinancialSeries:
        if not source_key.startswith("series."):
            raise KeyError(f"Unsupported series source: {source_key}")
        target_name = source_key.removeprefix("series.")
        for series in self.financial_model.series:
            if series.name == target_name:
                return series
        raise KeyError(f"Series source not found: {source_key}")

    def resolve_table_rows(self, source_key: str) -> list[dict[str, str]]:
        if source_key.startswith("series."):
            series = self.resolve_series(source_key)
            rows: list[dict[str, str]] = []
            for period, value in zip(series.periods, series.values, strict=True):
                rows.append(
                    {
                        "period": period,
                        "value": "-" if value is None else f"{value}",
                        "series": series.name,
                        "unit": series.unit,
                    }
                )
            return rows

        raise KeyError(f"Unsupported table source: {source_key}")
