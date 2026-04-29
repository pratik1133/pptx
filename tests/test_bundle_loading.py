from pathlib import Path
from uuid import uuid4

import pytest

from reportgen.ingestion.errors import InputValidationError
from reportgen.ingestion.loaders import load_input_bundle, load_normalized_input_bundle


def test_sample_bundle_loads() -> None:
    bundle = load_input_bundle(Path("data/samples/bundles/abc_bundle.json"))

    assert bundle.company.name == "ABC Ltd"
    assert bundle.metadata.rating == "BUY"
    assert bundle.financial_model.model_name == "ABC Base Model"
    assert bundle.approved_report.title == "ABC Ltd Initiation Note"


def test_sample_bundle_normalizes() -> None:
    bundle = load_normalized_input_bundle(Path("data/samples/bundles/abc_bundle.json"))

    assert bundle.normalized_ticker == "ABC"
    assert bundle.normalized_currency == "INR"
    assert bundle.data_references.metric_keys
    assert bundle.data_references.metric_source_keys
    assert bundle.data_references.series_source_keys
    assert bundle.report_sections[0].heading == "Investment View"


def _make_local_temp_dir() -> Path:
    temp_dir = Path("output/test-temp") / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=False)
    return temp_dir


def test_validation_fails_on_currency_mismatch() -> None:
    temp_dir = _make_local_temp_dir()
    company_path = temp_dir / "company.json"
    metadata_path = temp_dir / "metadata.json"
    model_path = temp_dir / "model.json"
    report_path = temp_dir / "report.md"
    bundle_path = temp_dir / "bundle.json"

    company_path.write_text(
        '{"name":"ABC Ltd","ticker":"ABC","exchange":"NSE","sector":"Chemicals","country":"India","peer_list":["Peer 1"]}',
        encoding="utf-8",
    )
    metadata_path.write_text(
        '{"rating":"BUY","currency":"USD","cmp":420,"target_price":515,"upside_pct":22.6,"analyst":"Jane Doe","report_date":"2026-04-28","report_type":"Initiation"}',
        encoding="utf-8",
    )
    model_path.write_text(
        '{"model_name":"ABC Base Model","model_version":"v1.0","currency":"INR","fiscal_year_end":"March","metrics":{"revenue_fy26":28500},"series":[{"name":"Revenue","unit":"INR Cr","periods":["FY24"],"values":[19800]}]}',
        encoding="utf-8",
    )
    report_path.write_text("# Title\n\n## Section\n\nBody text.", encoding="utf-8")
    bundle_path.write_text(
        '{"company_path":"company.json","metadata_path":"metadata.json","financial_model_path":"model.json","approved_report_path":"report.md"}',
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError) as exc:
        load_input_bundle(bundle_path)

    assert "currency" in str(exc.value).lower()


def test_validation_fails_when_report_has_no_sections() -> None:
    temp_dir = _make_local_temp_dir()
    company_path = temp_dir / "company.json"
    metadata_path = temp_dir / "metadata.json"
    model_path = temp_dir / "model.json"
    report_path = temp_dir / "report.md"
    bundle_path = temp_dir / "bundle.json"

    company_path.write_text(
        '{"name":"ABC Ltd","ticker":"ABC","exchange":"NSE","sector":"Chemicals","country":"India","peer_list":["Peer 1"]}',
        encoding="utf-8",
    )
    metadata_path.write_text(
        '{"rating":"BUY","currency":"INR","cmp":420,"target_price":515,"upside_pct":22.6,"analyst":"Jane Doe","report_date":"2026-04-28","report_type":"Initiation"}',
        encoding="utf-8",
    )
    model_path.write_text(
        '{"model_name":"ABC Base Model","model_version":"v1.0","currency":"INR","fiscal_year_end":"March","metrics":{"revenue_fy26":28500},"series":[{"name":"Revenue","unit":"INR Cr","periods":["FY24"],"values":[19800]}]}',
        encoding="utf-8",
    )
    report_path.write_text("# Title\n\nPlain text without section headings.", encoding="utf-8")
    bundle_path.write_text(
        '{"company_path":"company.json","metadata_path":"metadata.json","financial_model_path":"model.json","approved_report_path":"report.md"}',
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError) as exc:
        load_input_bundle(bundle_path)

    assert "section" in str(exc.value).lower()


def test_validation_fails_on_mismatched_series_periods() -> None:
    temp_dir = _make_local_temp_dir()
    company_path = temp_dir / "company.json"
    metadata_path = temp_dir / "metadata.json"
    model_path = temp_dir / "model.json"
    report_path = temp_dir / "report.md"
    bundle_path = temp_dir / "bundle.json"

    company_path.write_text(
        '{"name":"ABC Ltd","ticker":"ABC","exchange":"NSE","sector":"Chemicals","country":"India","peer_list":["Peer 1"]}',
        encoding="utf-8",
    )
    metadata_path.write_text(
        '{"rating":"BUY","currency":"INR","cmp":420,"target_price":515,"upside_pct":22.6,"analyst":"Jane Doe","report_date":"2026-04-28","report_type":"Initiation"}',
        encoding="utf-8",
    )
    model_path.write_text(
        '{"model_name":"ABC Base Model","model_version":"v1.0","currency":"INR","fiscal_year_end":"March","metrics":{"revenue_fy26":28500},"series":[{"name":"Revenue","unit":"INR Cr","periods":["FY24","FY25"],"values":[19800,21000]},{"name":"EBITDA","unit":"INR Cr","periods":["FY24","FY26"],"values":[3500,3900]}]}',
        encoding="utf-8",
    )
    report_path.write_text("# Title\n\n## Section\n\nBody text.", encoding="utf-8")
    bundle_path.write_text(
        '{"company_path":"company.json","metadata_path":"metadata.json","financial_model_path":"model.json","approved_report_path":"report.md"}',
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError) as exc:
        load_input_bundle(bundle_path)

    assert "period" in str(exc.value).lower()
