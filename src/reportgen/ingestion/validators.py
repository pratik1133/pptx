from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from reportgen.ingestion.errors import InputValidationError
from reportgen.schemas.bundle import InputBundle, LoadedInputBundle


def resolve_bundle_paths(bundle_path: Path, bundle: InputBundle) -> dict[str, Path]:
    base_dir = bundle_path.parent.resolve()
    resolved = {
        "company_path": (base_dir / bundle.company_path).resolve(),
        "metadata_path": (base_dir / bundle.metadata_path).resolve(),
        "financial_model_path": (base_dir / bundle.financial_model_path).resolve(),
        "approved_report_path": (base_dir / bundle.approved_report_path).resolve(),
    }

    errors: list[str] = []
    for field_name, path in resolved.items():
        if not path.exists():
            errors.append(f"{field_name} does not exist: {path}")
        elif not path.is_file():
            errors.append(f"{field_name} is not a file: {path}")

    if errors:
        raise InputValidationError(errors)

    return resolved


def validate_loaded_bundle(loaded: LoadedInputBundle) -> None:
    errors: list[str] = []

    if loaded.metadata.currency.upper() != loaded.financial_model.currency.upper():
        errors.append(
            "Metadata currency and financial model currency must match "
            f"({loaded.metadata.currency} vs {loaded.financial_model.currency})."
        )

    if not loaded.financial_model.metrics:
        errors.append("Financial model must contain at least one headline metric.")

    if not loaded.financial_model.series:
        errors.append("Financial model must contain at least one time series.")

    series_names = [series.name.casefold() for series in loaded.financial_model.series]
    if len(series_names) != len(set(series_names)):
        errors.append("Financial model series names must be unique.")

    metric_keys = [key.casefold() for key in loaded.financial_model.metrics.keys()]
    if len(metric_keys) != len(set(metric_keys)):
        errors.append("Financial model metric keys must be unique irrespective of case.")

    if loaded.financial_model.series:
        first_periods = [period.casefold() for period in loaded.financial_model.series[0].periods]
        if any(not period.strip() for period in loaded.financial_model.series[0].periods):
            errors.append("Financial series period labels must not be empty.")

        for series in loaded.financial_model.series[1:]:
            if [period.casefold() for period in series.periods] != first_periods:
                errors.append("All financial series must use the same ordered period labels.")
            if any(not period.strip() for period in series.periods):
                errors.append(f"Financial series '{series.name}' contains an empty period label.")

    if loaded.approved_report.section_count == 0:
        errors.append("Approved report markdown must contain at least one '##' section.")

    if loaded.approved_report.title == "Approved Report":
        errors.append("Approved report markdown must start with a '# ' title.")

    if loaded.metadata.upside_pct is not None:
        computed = ((loaded.metadata.target_price - loaded.metadata.cmp) / loaded.metadata.cmp) * Decimal("100")
        computed = computed.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        supplied = loaded.metadata.upside_pct.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        if abs(computed - supplied) > Decimal("0.3"):
            errors.append(
                "Metadata upside_pct is inconsistent with cmp and target_price "
                f"({supplied}% supplied vs {computed}% computed)."
            )

    if loaded.metadata.target_price < loaded.metadata.cmp and loaded.metadata.rating.upper() == "BUY":
        errors.append("BUY rating should not have a target price below current market price.")

    if errors:
        raise InputValidationError(errors)
