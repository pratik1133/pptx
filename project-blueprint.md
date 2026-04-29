# PPTX Research Report Generator Blueprint

## 1. Product Objective

Build a production-grade system that transforms:

- company metadata
- deterministic financial data
- approved research narrative

into:

- branded PPTX research reports
- final PDF reports
- versioned structured report JSON

The system is not a generic presentation builder. It is a controlled document production pipeline for equity research and wealth-management reporting.

Core principle:

`AI decides the story. Software guarantees the document.`

---

## 2. Product Scope

### In Scope

- structured ingestion of company, report, and model inputs
- LLM-assisted slide planning and slide-level writing
- strict JSON schema validation
- deterministic PPTX rendering from predefined layouts
- deterministic chart and table rendering
- PDF export from generated PPTX
- run/version tracking and reproducibility

### Out of Scope for MVP

- free-form slide design generation
- arbitrary user-authored layouts at runtime
- full browser-based editor
- advanced deck animations and transitions
- dynamic support for every overflow edge case
- sector-specific template explosion

---

## 3. Architecture Overview

### Pipeline

`Input Data -> Validation -> AI Slide Planning -> Report Spec JSON -> Deterministic Renderer -> PPTX -> PDF -> Storage + Audit`

### Responsibility Split

#### AI Layer

Responsible for:

- report structure planning
- slide ordering
- layout selection from allowed layout registry
- concise titles and subtitles
- bullets and summaries
- block-level content proposals

Not responsible for:

- x/y coordinates
- low-level PPT generation
- numeric truth
- chart series invention
- table cell calculations

#### Deterministic Software Layer

Responsible for:

- schema validation
- layout mapping
- all rendering coordinates
- theme enforcement
- table/chart generation
- numeric formatting
- overflow management rules
- artifact generation
- versioning and auditability

---

## 4. Recommended Tech Stack

### Core Runtime

- Python 3.11+

### Main Libraries

- `pydantic` for schema and config validation
- `python-pptx` for PPTX generation
- `pandas` for table shaping
- `matplotlib` for initial chart images
- `Pillow` for image utilities if needed
- `jinja2` only if prompt/template generation benefits from it
- `typer` or `click` for CLI
- `pytest` for tests

### AI Integration

- Anthropic SDK
- structured JSON output only
- retry and repair loop for invalid output

### Storage

- filesystem for local MVP artifact storage
- JSON per run/version
- later: object storage + metadata DB

### PDF Export

Options in preferred order depending on deployment environment:

1. LibreOffice headless conversion
2. PowerPoint COM automation on Windows-only deployment
3. external conversion worker if enterprise environment requires it

---

## 5. Canonical Data Model

The canonical artifact is `report.json`.

### Top-Level Entities

- `CompanyProfile`
- `ResearchMetadata`
- `FinancialModelSnapshot`
- `SlidePlan`
- `ReportSpec`
- `RenderManifest`
- `RunRecord`

### Recommended Report Spec Shape

```json
{
  "schema_version": "1.0.0",
  "report_id": "uuid",
  "run_id": "uuid",
  "company": {
    "name": "ABC Ltd",
    "ticker": "ABC",
    "exchange": "NSE",
    "sector": "Chemicals"
  },
  "metadata": {
    "rating": "BUY",
    "cmp": 420,
    "target_price": 515,
    "currency": "INR",
    "analyst": "Jane Doe",
    "report_date": "2026-04-28"
  },
  "inputs": {
    "financial_model_ref": "model_v3.json",
    "approved_content_ref": "approved_report_v7.md"
  },
  "slides": [
    {
      "slide_id": "s1",
      "layout": "company_snapshot",
      "title": "ABC Ltd At A Glance",
      "subtitle": "Market position and headline investment view",
      "blocks": [
        {
          "type": "text",
          "key": "summary",
          "content": "ABC is positioned to benefit from..."
        },
        {
          "type": "metrics",
          "key": "headline_metrics",
          "items": [
            { "label": "CMP", "value": "INR 420", "source": "metadata.cmp" },
            { "label": "TP", "value": "INR 515", "source": "metadata.target_price" }
          ]
        }
      ]
    }
  ]
}
```

### Key Design Rules

- every slide must reference an allowed `layout`
- every data-bearing chart/table block must reference deterministic source fields
- narrative fields may be AI-authored
- numeric fields should be derived or copied from validated input sources only
- schema must be versioned from day one

---

## 6. Layout System

The layout engine should be registry-driven.

### Initial Layout Registry

- `cover_slide`
- `investment_thesis`
- `company_snapshot`
- `text_plus_bullets`
- `text_plus_chart`
- `full_width_chart`
- `full_table`
- `valuation_summary`
- `risks_and_catalysts`
- `disclaimer`

### Layout Definition Responsibilities

Each layout should define:

- allowed block types
- placeholder geometry
- title/subtitle positions
- font styles
- max block counts
- overflow behavior
- reserved chart/table/image areas

### Example Overflow Rules

- metric cards: hard cap per slide
- bullets: max line count before truncation/fail
- tables: split into continuation slide if row threshold exceeded
- charts: fixed aspect ratio and safe padding

---

## 7. Chart and Table Strategy

### Charts

MVP should render image-based charts first.

Supported chart types:

- bar
- line
- stacked bar
- combo
- donut only where necessary

Each chart spec should include:

- chart type
- title
- series definitions
- category axis source
- value source fields
- formatting config
- source audit reference

### Tables

Initial table types:

- annual financial summary
- quarterly summary
- peer comparison
- valuation table
- SOTP table
- ratio summary

Table renderer should standardize:

- widths
- row height
- numeric precision
- negative number formatting
- missing value display
- continuation behavior

---

## 8. Repo Structure

Recommended monorepo layout:

```text
pptx-research-report/
  README.md
  pyproject.toml
  .env.example
  .gitignore
  docs/
    architecture.md
    data-contracts.md
    prompt-contract.md
    rendering-rules.md
    operating-model.md
  assets/
    templates/
      master-template.pptx
    themes/
      brand_theme.json
    fonts/
    sample_outputs/
  prompts/
    system/
      slide_planner.md
    user/
      slide_planner_input.md.j2
    schemas/
      slide_plan_output.schema.json
  data/
    samples/
      companies/
      financial_models/
      approved_reports/
      expected_specs/
  src/
    reportgen/
      __init__.py
      config.py
      logging.py
      cli.py
      domain/
        enums.py
        ids.py
        types.py
      schemas/
        company.py
        metadata.py
        financials.py
        blocks.py
        charts.py
        tables.py
        slides.py
        report.py
        run_record.py
      ingestion/
        company_loader.py
        report_loader.py
        model_loader.py
        normalizers.py
        validators.py
      ai/
        anthropic_client.py
        prompt_builder.py
        planner.py
        repair.py
        serializers.py
      planning/
        layout_policy.py
        slide_plan_validator.py
        narrative_constraints.py
      rendering/
        engine.py
        presentation_builder.py
        layout_registry.py
        theme.py
        geometry.py
        overflow.py
        text_renderer.py
        metrics_renderer.py
        image_renderer.py
        chart_renderer.py
        table_renderer.py
        slides/
          cover_slide.py
          company_snapshot.py
          text_plus_chart.py
          full_table.py
          valuation_summary.py
          disclaimer.py
      export/
        pdf_converter.py
        artifact_writer.py
      storage/
        filesystem_store.py
        manifest.py
        versioning.py
      orchestration/
        pipeline.py
        run_context.py
        statuses.py
      qa/
        validators.py
        regression.py
        render_checks.py
  tests/
    unit/
      test_schemas.py
      test_layout_registry.py
      test_prompt_builder.py
      test_table_renderer.py
      test_chart_renderer.py
    integration/
      test_slide_plan_pipeline.py
      test_render_sample_report.py
      test_pdf_export.py
    fixtures/
      sample_company.json
      sample_financial_model.json
      sample_approved_report.md
  scripts/
    run_sample_pipeline.py
    generate_golden_outputs.py
  output/
    .gitkeep
```

---

## 9. Module Responsibilities

### `schemas/`

- define all pydantic models
- enforce contract validity
- expose schema export if needed

### `ingestion/`

- load raw input files
- normalize field names and units
- validate required fields before AI use

### `ai/`

- build Anthropic prompts
- call the model
- parse JSON output
- run repair flow for malformed but salvageable output

### `planning/`

- enforce allowed slide layouts
- apply business rules like mandatory disclaimer slide
- ensure narrative-to-layout compatibility

### `rendering/`

- map validated `ReportSpec` into PPTX
- own all geometry and formatting
- implement block-level rendering

### `export/`

- convert PPTX to PDF
- write output artifacts and manifests

### `storage/`

- persist JSON spec, source fingerprints, PPTX, PDF, and run metadata

### `qa/`

- regression comparison
- artifact sanity checks
- schema and rendering assertions

---

## 10. Suggested Configuration Model

Use environment-based config plus a typed settings object.

Example config groups:

- `ANTHROPIC_API_KEY`
- `MODEL_NAME`
- `TEMPLATE_PATH`
- `THEME_PATH`
- `OUTPUT_ROOT`
- `PDF_CONVERTER_MODE`
- `LIBREOFFICE_PATH`
- `MAX_PLANNING_RETRIES`
- `LOG_LEVEL`

---

## 11. CLI and Operational Commands

Recommended initial CLI:

```bash
reportgen validate-input --company data/samples/companies/abc.json --model data/samples/financial_models/abc_model.json --report data/samples/approved_reports/abc.md

reportgen plan-slides --input-bundle data/samples/bundles/abc_bundle.json --out output/abc/slide_plan.json

reportgen render-report --spec output/abc/report.json --out output/abc/

reportgen export-pdf --pptx output/abc/report.pptx --out output/abc/report.pdf

reportgen run-pipeline --bundle data/samples/bundles/abc_bundle.json --out output/abc/
```

This keeps the system debuggable because every stage can be run independently.

---

## 12. Prompting Contract

The prompt contract should be strict.

### Prompt Inputs

- company metadata
- approved report narrative
- normalized financial highlights
- allowed layouts
- required slides
- forbidden behaviors

### Prompt Output Rules

- output valid JSON only
- choose layouts only from registry
- do not fabricate numbers
- cite data references for metrics, charts, and tables
- keep slide count within configured bounds
- include disclaimer slide

### Validation Rules After Model Output

- schema-valid JSON
- slide count within range
- layout names allowed
- mandatory slides present
- chart/table blocks reference valid data source keys
- numeric text fields cross-check against deterministic sources where required

---

## 13. Versioning and Audit Trail

Every run should produce:

- input manifest
- source file hashes
- report spec JSON
- render log
- PPTX output
- PDF output
- run metadata JSON

Recommended run directory layout:

```text
output/
  2026-04-28_abc_buy_initiation/
    manifest.json
    inputs/
      company.json
      financial_model.json
      approved_report.md
    intermediates/
      prompt_payload.json
      slide_plan.json
      validated_report.json
    artifacts/
      report.pptx
      report.pdf
    logs/
      run.log
```

This gives traceability for approvals, debugging, and future compliance needs.

---

## 14. Testing Strategy

### Unit Tests

- schema validation
- layout registry integrity
- text truncation behavior
- numeric formatting
- chart spec construction
- table overflow rules

### Integration Tests

- end-to-end slide planning on sample inputs
- render sample spec into PPTX
- verify expected slide count and key placeholder presence
- verify PDF export invocation path

### Golden Regression Tests

- keep 2 to 5 known sample companies
- generate output artifacts
- compare against expected structural properties
- optionally compare generated chart images or text manifests

### Manual QA Checklist

- title overflow
- bullet readability
- table legibility
- color/theme correctness
- chart axis readability
- PDF fidelity versus PPTX

---

## 15. MVP Delivery Plan

### Phase 1: Foundation

Goal:
Create the project skeleton and define canonical schemas.

Deliverables:

- repo scaffold
- pyproject and tooling
- pydantic schema set
- sample input bundle
- basic CLI

### Phase 2: Input Ingestion and Validation

Goal:
Normalize and validate raw inputs before planning.

Deliverables:

- company/model/report loaders
- validation errors with good messages
- normalized input bundle object

### Phase 3: AI Slide Planning

Goal:
Generate a strict slide plan JSON from approved narrative and model summary.

Deliverables:

- Anthropic client wrapper
- prompt templates
- JSON-only planning flow
- output validator and retry/repair path

### Phase 4: Layout Library

Goal:
Build predefined slide layout definitions and theme primitives.

Deliverables:

- layout registry
- brand theme object
- geometry constants
- initial 6 to 8 layouts

### Phase 5: Deterministic PPTX Rendering

Goal:
Render validated report specs into stable PPTX output.

Deliverables:

- rendering engine
- text and metrics block renderers
- slide factory
- sample branded deck output

### Phase 6: Charts and Tables

Goal:
Support core finance blocks.

Deliverables:

- chart image generation
- table block rendering
- overflow handling basics
- formatting helpers

### Phase 7: PDF Export and Artifact Packaging

Goal:
Make outputs distributable and traceable.

Deliverables:

- PDF conversion wrapper
- artifact folder structure
- run manifest
- basic audit logging

### Phase 8: QA Hardening

Goal:
Increase reliability for real analyst usage.

Deliverables:

- regression suite
- sample company set
- error taxonomy
- render sanity checks

---

## 16. Milestone Sequence

### Milestone 1

Given one sample company bundle, produce a valid `report.json` and a simple 3-slide PPTX.

### Milestone 2

Expand to 6 to 8 slides with cover, thesis, snapshot, chart, table, risks, disclaimer.

### Milestone 3

Add PDF export and run manifests.

### Milestone 4

Add regression suite and prepare for pilot analyst testing.

---

## 17. Recommended First Build Order

If building immediately, the order should be:

1. create repo skeleton
2. define pydantic schemas
3. prepare one sample data bundle
4. implement CLI pipeline shell
5. implement layout registry
6. implement simple PPTX renderer for text-only slides
7. add Anthropic slide planner
8. add chart/table blocks
9. add PDF export
10. add manifests, tests, and regression harness

This order reduces risk because rendering discipline is established before the AI planning layer becomes deeply coupled.

---

## 18. Key Risks and Mitigations

### Risk: Poor schema design early

Mitigation:

- version schemas
- keep block model explicit
- validate all source references

### Risk: AI produces unusable slide plans

Mitigation:

- constrain layouts
- use strict JSON
- validate and retry
- keep deterministic fallback rules

### Risk: PPTX output quality drifts

Mitigation:

- fixed layout registry
- centralized theme tokens
- golden sample regression renders

### Risk: Tables overflow badly

Mitigation:

- hard row limits
- continuation slides
- precomputed truncation rules

### Risk: PDF export is environment-sensitive

Mitigation:

- abstract converter interface
- support multiple backends
- test target deployment environment early

---

## 19. Immediate Next Steps

The best next implementation step is to build the repo foundation and schema layer first.

Immediate execution checklist:

1. create project scaffold
2. add `pyproject.toml`
3. define pydantic models for report spec
4. create one sample company/model/report bundle
5. implement `reportgen validate-input`
6. implement `reportgen render-report` with 2 to 3 simple layouts

That will give a stable base before connecting Anthropic or PDF conversion.
