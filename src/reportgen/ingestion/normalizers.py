from decimal import Decimal, ROUND_HALF_UP

from reportgen.schemas.bundle import (
    DataReferenceCatalog,
    LoadedInputBundle,
    NormalizedInputBundle,
    ReportSection,
)


def _format_decimal(value: Decimal, suffix: str = "") -> str:
    quantized = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{quantized}{suffix}"


def _extract_sections(markdown: str) -> list[ReportSection]:
    sections: list[ReportSection] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current_heading and current_lines:
                sections.append(
                    ReportSection(heading=current_heading, body="\n".join(current_lines).strip())
                )
            current_heading = line.removeprefix("## ").strip()
            current_lines = []
            continue

        if current_heading and line:
            current_lines.append(line)

    if current_heading and current_lines:
        sections.append(ReportSection(heading=current_heading, body="\n".join(current_lines).strip()))

    return sections


def normalize_loaded_bundle(loaded: LoadedInputBundle) -> NormalizedInputBundle:
    fm = loaded.financial_model
    metric_keys = sorted(fm.metrics.keys())
    metric_source_keys = [f"financial_metrics.{key}" for key in metric_keys]
    series_names = [series.name for series in fm.series]
    series_source_keys = [f"series.{name}" for name in series_names]
    quarterly_series_source_keys = [f"quarterly_series.{s.name}" for s in fm.quarterly_series]
    ratio_source_keys = [f"ratios.{r.name}" for r in fm.ratios]
    period_labels: list[str] = []
    if fm.series:
        period_labels = list(fm.series[0].periods)

    headline_metrics = {
        "cmp": f"{loaded.metadata.currency.upper()} {_format_decimal(loaded.metadata.cmp)}",
        "target_price": f"{loaded.metadata.currency.upper()} {_format_decimal(loaded.metadata.target_price)}",
        "rating": loaded.metadata.rating.upper(),
        "analyst": loaded.metadata.analyst,
    }
    if loaded.metadata.upside_pct is not None:
        headline_metrics["upside_pct"] = _format_decimal(loaded.metadata.upside_pct, "%")

    return NormalizedInputBundle(
        source=loaded,
        primary_title=loaded.approved_report.title,
        report_sections=_extract_sections(loaded.approved_report.markdown),
        normalized_rating=loaded.metadata.rating.upper(),
        normalized_currency=loaded.metadata.currency.upper(),
        normalized_ticker=loaded.company.ticker.upper(),
        normalized_exchange=loaded.company.exchange.upper(),
        headline_metrics=headline_metrics,
        data_references=DataReferenceCatalog(
            metric_keys=metric_keys,
            metric_source_keys=metric_source_keys,
            series_names=series_names,
            series_source_keys=series_source_keys,
            quarterly_series_source_keys=quarterly_series_source_keys,
            ratio_source_keys=ratio_source_keys,
            period_labels=period_labels,
            has_peers=bool(fm.peers),
            has_quarterly=bool(fm.quarterly_series),
            has_segments=bool(fm.segments),
            has_valuation_bands=bool(fm.valuation_bands),
            has_scenarios=bool(fm.scenarios),
            has_ratios=bool(fm.ratios),
            has_saarthi=fm.saarthi is not None,
            has_management=bool(fm.management_team),
            has_forensic=fm.forensic is not None,
            has_key_highlights=bool(fm.key_highlights),
            has_competitive_advantages=bool(fm.competitive_advantages),
            has_industry_tailwinds=bool(fm.industry_tailwinds),
            has_industry_risks=bool(fm.industry_risks),
            has_trading_strategy=fm.trading_strategy is not None,
        ),
    )
