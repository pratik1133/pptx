import json
from pathlib import Path

from reportgen.ingestion.company_loader import load_company_profile
from reportgen.ingestion.metadata_loader import load_research_metadata
from reportgen.ingestion.model_loader import load_financial_model
from reportgen.ingestion.normalizers import normalize_loaded_bundle
from reportgen.ingestion.report_loader import load_approved_report
from reportgen.ingestion.validators import resolve_bundle_paths, validate_loaded_bundle
from reportgen.schemas.bundle import InputBundle, LoadedInputBundle, NormalizedInputBundle


def load_input_bundle(bundle_path: Path) -> LoadedInputBundle:
    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle = InputBundle.model_validate(bundle_payload)
    resolved_paths = resolve_bundle_paths(bundle_path, bundle)

    loaded = LoadedInputBundle(
        bundle_path=bundle_path.resolve(),
        company_path=resolved_paths["company_path"],
        metadata_path=resolved_paths["metadata_path"],
        financial_model_path=resolved_paths["financial_model_path"],
        approved_report_path=resolved_paths["approved_report_path"],
        company=load_company_profile(resolved_paths["company_path"]),
        metadata=load_research_metadata(resolved_paths["metadata_path"]),
        financial_model=load_financial_model(resolved_paths["financial_model_path"]),
        approved_report=load_approved_report(resolved_paths["approved_report_path"]),
    )
    validate_loaded_bundle(loaded)
    return loaded


def load_normalized_input_bundle(bundle_path: Path) -> NormalizedInputBundle:
    loaded = load_input_bundle(bundle_path)
    return normalize_loaded_bundle(loaded)
