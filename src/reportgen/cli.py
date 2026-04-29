from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from reportgen.ai.planner import plan_slides_mock
from reportgen.ai.serializers import dump_slide_plan_json
from reportgen.config import settings
from reportgen.export.pdf_converter import PdfConversionUnavailableError, resolve_pdf_converter
from reportgen.ingestion.errors import InputValidationError
from reportgen.ingestion.loaders import load_normalized_input_bundle
from reportgen.orchestration.pipeline import run_local_pipeline
from reportgen.planning.report_builder import build_report_spec
from reportgen.rendering.engine import PresentationRenderer, load_report_spec

app = typer.Typer(help="PPTX-first research report generator CLI.")
console = Console()


@app.command("validate-input")
def validate_input(bundle: Path = typer.Option(..., exists=True, readable=True, help="Path to input bundle JSON.")) -> None:
    """Validate a company/model/report input bundle and print a concise summary."""

    try:
        normalized = load_normalized_input_bundle(bundle)
    except InputValidationError as exc:
        console.print("[bold red]Input bundle is invalid.[/bold red]")
        for error in exc.errors:
            console.print(f"[red]- {error}[/red]")
        raise typer.Exit(code=1) from exc

    table = Table(title="Validated Input Bundle")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Bundle", str(bundle))
    table.add_row("Company", f"{normalized.source.company.name} ({normalized.normalized_ticker})")
    table.add_row("Sector", normalized.source.company.sector)
    table.add_row("Report title", normalized.primary_title)
    table.add_row("Rating", normalized.normalized_rating)
    table.add_row("Currency", normalized.normalized_currency)
    table.add_row("Metric count", str(len(normalized.data_references.metric_keys)))
    table.add_row("Series count", str(len(normalized.data_references.series_names)))
    table.add_row("Sections", str(len(normalized.report_sections)))

    console.print(table)
    console.print("[bold]Headline metrics[/bold]")
    for key, value in normalized.headline_metrics.items():
        console.print(f"- {key}: {value}")
    console.print("[bold green]Input bundle is valid.[/bold green]")


@app.command("plan-slides")
def plan_slides(
    bundle: Path = typer.Option(..., exists=True, readable=True, help="Path to input bundle JSON."),
    out: Path = typer.Option(..., help="Path to write the slide plan JSON."),
) -> None:
    """Generate a validated slide plan using the deterministic local planner scaffold."""

    try:
        normalized = load_normalized_input_bundle(bundle)
        plan = plan_slides_mock(normalized)
    except InputValidationError as exc:
        console.print("[bold red]Slide planning failed.[/bold red]")
        for error in exc.errors:
            console.print(f"[red]- {error}[/red]")
        raise typer.Exit(code=1) from exc

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dump_slide_plan_json(plan), encoding="utf-8")
    console.print(f"[bold green]Slide plan written to[/bold green] {out}")


@app.command("build-report-spec")
def build_report_spec_command(
    bundle: Path = typer.Option(..., exists=True, readable=True, help="Path to input bundle JSON."),
    out: Path = typer.Option(..., help="Path to write the report spec JSON."),
) -> None:
    """Build a render-ready report spec from the validated local planning scaffold."""

    try:
        normalized = load_normalized_input_bundle(bundle)
        plan = plan_slides_mock(normalized)
        report_spec = build_report_spec(normalized, plan)
    except InputValidationError as exc:
        console.print("[bold red]Report spec build failed.[/bold red]")
        for error in exc.errors:
            console.print(f"[red]- {error}[/red]")
        raise typer.Exit(code=1) from exc

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Report spec written to[/bold green] {out}")


@app.command("render-report")
def render_report(
    spec: Path = typer.Option(..., exists=True, readable=True, help="Path to report spec JSON."),
    out: Path = typer.Option(..., help="Path to write the PPTX file."),
) -> None:
    """Render a report spec into a PPTX deck."""

    try:
        report_spec = load_report_spec(spec)
        renderer = PresentationRenderer()
        renderer.render_to_path(report_spec, out)
    except RuntimeError as exc:
        console.print("[bold red]PPTX rendering is unavailable.[/bold red]")
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]PPTX written to[/bold green] {out}")


@app.command("export-pdf")
def export_pdf(
    pptx: Path = typer.Option(..., exists=True, readable=True, help="Path to PPTX file."),
    out: Path = typer.Option(..., help="Path to write the PDF file."),
) -> None:
    """Convert a PPTX to PDF using the configured backend."""

    try:
        converter = resolve_pdf_converter()
        converter.convert(pptx, out)
    except PdfConversionUnavailableError as exc:
        console.print("[bold yellow]PDF export skipped.[/bold yellow]")
        console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]PDF written to[/bold green] {out}")


@app.command("run-pipeline")
def run_pipeline(
    bundle: Path = typer.Option(..., exists=True, readable=True, help="Path to input bundle JSON."),
    out_root: Path = typer.Option(settings.output_root, help="Root directory for packaged run outputs."),
) -> None:
    """Run the local end-to-end pipeline and package outputs into a run folder."""

    try:
        result = run_local_pipeline(bundle, out_root)
    except (InputValidationError, RuntimeError) as exc:
        console.print("[bold red]Pipeline run failed.[/bold red]")
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]Run folder created:[/bold green] {result.run_root}")
    console.print(f"[bold]Status:[/bold] {result.manifest.status}")
    console.print(f"[bold]PPTX:[/bold] {result.pptx_path}")
    if result.pdf_path is not None:
        console.print(f"[bold]PDF:[/bold] {result.pdf_path}")
    elif result.manifest.notes:
        for note in result.manifest.notes:
            console.print(f"[yellow]- {note}[/yellow]")


if __name__ == "__main__":
    app()
