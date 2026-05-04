from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from reportgen.rendering.number_format import (
    format_currency,
    format_for_unit,
    format_multiple,
    format_number,
    format_percent,
)
from reportgen.schemas.financials import FinancialModelSnapshot, FinancialSeries
from reportgen.schemas.report import ReportSpec


def _fmt(value, suffix: str = "") -> str:
    if suffix == "%":
        return format_percent(value)
    if suffix == "x":
        return format_multiple(value)
    return format_number(value)


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
        if source_key == "period_labels":
            if not self.financial_model.series:
                return []
            return list(self.financial_model.series[0].periods)
        if source_key == "period_labels.quarterly":
            if not self.financial_model.quarterly_series:
                return []
            return list(self.financial_model.quarterly_series[0].periods)
        raise KeyError(f"Unsupported category source: {source_key}")

    def resolve_series(self, source_key: str) -> FinancialSeries:
        if source_key.startswith("series."):
            target = source_key.removeprefix("series.")
            for series in self.financial_model.series:
                if series.name == target:
                    return series
            raise KeyError(f"Series source not found: {source_key}")
        if source_key.startswith("quarterly_series."):
            target = source_key.removeprefix("quarterly_series.")
            for series in self.financial_model.quarterly_series:
                if series.name == target:
                    return series
            raise KeyError(f"Quarterly series not found: {source_key}")
        if source_key.startswith("ratios."):
            target = source_key.removeprefix("ratios.")
            for ratio in self.financial_model.ratios:
                if ratio.name == target:
                    return FinancialSeries(
                        name=ratio.name, unit=ratio.unit, periods=ratio.periods, values=ratio.values
                    )
            raise KeyError(f"Ratio not found: {source_key}")
        if source_key == "segments.revenue_share":
            return self._segments_as_series("revenue_share_pct", "Revenue Share")
        if source_key == "segments.ebitda_share":
            return self._segments_as_series("ebitda_share_pct", "EBITDA Share")
        raise KeyError(f"Unsupported series source: {source_key}")

    def _segments_as_series(self, attr: str, name: str) -> FinancialSeries:
        segs = self.financial_model.segments
        return FinancialSeries(
            name=name,
            unit="%",
            periods=[s.name for s in segs] or ["-"],
            values=[getattr(s, attr) for s in segs] or [None],
        )

    def resolve_table_rows(self, source_key: str) -> list[dict[str, str]]:
        if source_key.startswith("series.") or source_key.startswith("quarterly_series.") or source_key.startswith("ratios."):
            series = self.resolve_series(source_key)
            return [
                {"period": p, "value": format_for_unit(v, series.unit), "series": series.name, "unit": series.unit}
                for p, v in zip(series.periods, series.values, strict=True)
            ]
        if source_key == "peers":
            target_ticker = self.report_spec.company.ticker.upper()
            rows: list[dict[str, str]] = []
            for peer in self.financial_model.peers:
                is_target = peer.is_target or (peer.ticker and peer.ticker.upper() == target_ticker)
                rows.append(
                    {
                        "name": peer.name + (" *" if is_target else ""),
                        "ticker": peer.ticker or "-",
                        "market_cap": format_currency(peer.market_cap_cr, "INR", suffix=" Cr"),
                        "pe": _fmt(peer.pe, "x"),
                        "ev_ebitda": _fmt(peer.ev_ebitda, "x"),
                        "pb": _fmt(peer.pb, "x"),
                        "roe": _fmt(peer.roe_pct, "%"),
                        "revenue_growth": _fmt(peer.revenue_growth_pct, "%"),
                    }
                )
            return rows
        if source_key == "valuation_bands":
            return [
                {
                    "method": v.method,
                    "low": _fmt(v.low),
                    "base": _fmt(v.base),
                    "high": _fmt(v.high),
                    "weight": _fmt(v.weight_pct, "%"),
                    "notes": v.notes or "",
                }
                for v in self.financial_model.valuation_bands
            ]
        if source_key == "scenarios":
            return [
                {
                    "name": s.name,
                    "revenue_cagr": _fmt(s.revenue_cagr_pct, "%"),
                    "ebitda_margin": _fmt(s.ebitda_margin_pct, "%"),
                    "target_price": _fmt(s.target_price),
                    "probability": _fmt(s.probability_pct, "%"),
                    "notes": s.notes or "",
                }
                for s in self.financial_model.scenarios
            ]
        if source_key == "ratio_summary":
            rows: list[dict[str, str]] = []
            for ratio in self.financial_model.ratios:
                row = {"ratio": ratio.name, "unit": ratio.unit}
                for period, value in zip(ratio.periods, ratio.values, strict=True):
                    row[period] = format_for_unit(value, ratio.unit)
                rows.append(row)
            return rows
        if source_key == "segments":
            return [
                {
                    "name": s.name,
                    "revenue_share": _fmt(s.revenue_share_pct, "%"),
                    "ebitda_share": _fmt(s.ebitda_share_pct, "%"),
                    "growth": _fmt(s.growth_pct, "%"),
                    "aum_label": s.aum_or_book_label or "",
                    "aum_value": s.aum_or_book_value or "",
                    "description": s.description or "",
                }
                for s in self.financial_model.segments
            ]
        if source_key == "saarthi_dimensions":
            scorecard = self.financial_model.saarthi
            if not scorecard:
                return []
            return [
                {
                    "code": d.code,
                    "name": d.name,
                    "score": f"{d.score}/{d.max_score}",
                    "assessment": d.assessment or "",
                    "evidence": d.key_evidence or "",
                }
                for d in scorecard.dimensions
            ]
        if source_key == "management_team":
            return [
                {"name": m.name, "role": m.role, "bio": m.bio}
                for m in self.financial_model.management_team
            ]
        if source_key == "forensic_violations":
            f = self.financial_model.forensic
            if not f:
                return []
            return [
                {"title": v.title, "description": v.description, "severity": v.severity}
                for v in f.violations
            ]

        raise KeyError(f"Unsupported table source: {source_key}")
