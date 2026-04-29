from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from reportgen.ai.planner import plan_slides_mock
from reportgen.ai.serializers import dump_slide_plan_json
from reportgen.export.pdf_converter import PdfConversionUnavailableError, resolve_pdf_converter
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.logging import format_log_event
from reportgen.orchestration.statuses import (
    PIPELINE_STATUS_COMPLETE,
    PIPELINE_STATUS_PDF_SKIPPED,
    PIPELINE_STATUS_READY,
)
from reportgen.planning.report_builder import build_report_spec
from reportgen.qa.render_checks import validate_rendered_pptx
from reportgen.qa.validators import validate_report_content
from reportgen.rendering.engine import PresentationRenderer
from reportgen.storage.filesystem_store import FilesystemRunStore
from reportgen.storage.manifest import RunManifest, new_manifest


@dataclass
class PipelineRunResult:
    run_root: Path
    manifest: RunManifest
    pdf_path: Path | None
    pptx_path: Path


def run_local_pipeline(bundle_path: Path, output_root: Path) -> PipelineRunResult:
    normalized = load_normalized_input_bundle(bundle_path)
    plan = plan_slides_mock(normalized)
    report_spec = build_report_spec(normalized, plan)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = uuid4().hex[:12]
    run_root = output_root / f"{timestamp}_{normalized.normalized_ticker.lower()}_{run_id}"
    store = FilesystemRunStore(run_root)
    store.ensure_structure()

    manifest = new_manifest(run_id=run_id, company_ticker=normalized.normalized_ticker, status=PIPELINE_STATUS_READY)

    company_copy = store.copy_into(normalized.source.company_path, "inputs/company.json")
    metadata_copy = store.copy_into(normalized.source.metadata_path, "inputs/metadata.json")
    model_copy = store.copy_into(normalized.source.financial_model_path, "inputs/financial_model.json")
    report_copy = store.copy_into(normalized.source.approved_report_path, "inputs/approved_report.md")
    for label, path in (
        ("company", company_copy),
        ("metadata", metadata_copy),
        ("financial_model", model_copy),
        ("approved_report", report_copy),
    ):
        store.add_artifact(manifest, label, path)

    slide_plan_path = store.write_text("intermediates/slide_plan.json", dump_slide_plan_json(plan))
    report_spec_path = store.write_text(
        "intermediates/report.json", report_spec.model_dump_json(indent=2)
    )
    store.add_artifact(manifest, "slide_plan", slide_plan_path)
    store.add_artifact(manifest, "report_spec", report_spec_path)

    renderer = PresentationRenderer()
    pptx_path = renderer.render_to_path(report_spec, run_root / "artifacts" / "report.pptx")
    store.add_artifact(manifest, "pptx", pptx_path)

    content_checks = validate_report_content(report_spec)
    manifest.notes.extend(content_checks.warnings)

    render_checks = validate_rendered_pptx(pptx_path, report_spec)
    manifest.notes.extend(render_checks.warnings)
    if render_checks.errors:
        manifest.status = "render_failed"
        manifest.notes.extend(render_checks.errors)
        log_path = store.write_text(
            "logs/run.log",
            "\n".join(
                [
                    format_log_event("INFO", "pipeline_started", run_id=manifest.run_id, ticker=manifest.company_ticker),
                    *(format_log_event("WARN", "qa_warning", detail=note) for note in manifest.notes),
                    *(format_log_event("ERROR", "render_check_failed", detail=error) for error in render_checks.errors),
                    format_log_event("INFO", "pipeline_finished", status=manifest.status),
                ]
            ),
        )
        store.add_artifact(manifest, "run_log", log_path)
        store.write_manifest(manifest)
        return PipelineRunResult(run_root=run_root, manifest=manifest, pdf_path=None, pptx_path=pptx_path)

    pdf_path: Path | None = None
    try:
        converter = resolve_pdf_converter()
        pdf_path = converter.convert(pptx_path, run_root / "artifacts" / "report.pdf")
        store.add_artifact(manifest, "pdf", pdf_path)
        manifest.status = PIPELINE_STATUS_COMPLETE
    except PdfConversionUnavailableError as exc:
        manifest.status = PIPELINE_STATUS_PDF_SKIPPED
        manifest.notes.append(str(exc))

    log_path = store.write_text(
        "logs/run.log",
        "\n".join(
            [
                format_log_event("INFO", "pipeline_started", run_id=manifest.run_id, ticker=manifest.company_ticker),
                *(format_log_event("WARN", "qa_warning", detail=note) for note in manifest.notes),
                format_log_event("INFO", "pipeline_finished", status=manifest.status),
            ]
        ),
    )
    store.add_artifact(manifest, "run_log", log_path)
    store.write_manifest(manifest)

    return PipelineRunResult(run_root=run_root, manifest=manifest, pdf_path=pdf_path, pptx_path=pptx_path)
