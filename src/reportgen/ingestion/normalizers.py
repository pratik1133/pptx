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
    metric_keys = sorted(loaded.financial_model.metrics.keys())
    metric_source_keys = [f"financial_metrics.{key}" for key in metric_keys]
    series_names = [series.name for series in loaded.financial_model.series]
    series_source_keys = [f"series.{name}" for name in series_names]
    period_labels: list[str] = []
    if loaded.financial_model.series:
        period_labels = list(loaded.financial_model.series[0].periods)

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
            period_labels=period_labels,
        ),
    )
