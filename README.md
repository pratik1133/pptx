# PPTX Research Report Generator

This repository contains the Phase 1 foundation for a PPTX-first research report generator for equity research and wealth-management workflows.

## Phase 1 Goals

- define the canonical source-of-truth schema
- scaffold the Python project and CLI
- validate sample company, financial model, and approved report inputs
- establish a clean base for planning and rendering phases

## Current Capabilities

- typed Pydantic models for the report domain
- sample input bundle under `data/samples/`
- CLI command to validate and normalize the bundle with business-rule checks

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
reportgen validate-input --bundle data/samples/bundles/abc_bundle.json
```

## Current Repo Areas

- `src/reportgen/schemas/` holds canonical domain models
- `src/reportgen/ingestion/` loads, validates, and normalizes raw inputs
- `data/samples/` contains one reference input bundle
- `project-blueprint.md` captures the full implementation direction

## Next Planned Steps

- Phase 3: AI slide-planning contract
- Phase 4: layout registry and theme system
- Phase 5: deterministic PPTX rendering
# pptx
