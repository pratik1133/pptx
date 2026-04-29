# Muscle Plan — Phases 9–14

The skeleton (Phases 1–8 from `project-blueprint.md`) is complete. This document defines the next phases — adding depth, brand, and real AI content on top of the existing pipeline.

Each phase has a clear goal, concrete deliverables, and an exit check that must be met before moving on.

---

## Phase 9 — Brand Shell & Theme System

**Goal:** Output stops looking generic; every slide carries the firm's visual identity.

**Deliverables**

- `assets/templates/master-template.pptx` with header band, footer (analyst, date, page #), logo placeholder, rating-badge zone, divider rules.
- `assets/themes/brand_theme.json` — colors, fonts, sizes, chart palette, rating-color map (BUY/HOLD/SELL/REDUCE).
- Theme loader replaces hardcoded `DEFAULT_THEME`; rendering engine loads master template instead of `slide_layouts[6]`.
- Header/footer applied to every non-cover slide; cover slide gets a distinct hero treatment.
- Rating badge component on cover and snapshot slides.

**Exit check:** Open the PPTX — it must read as a branded sell-side note at first glance.

---

## Phase 10 — Finance Content Depth

**Goal:** Cover the full equity research stack, not just 7 placeholder slides.

**Deliverables**

- New layouts: `peer_comparison`, `valuation_table`, `quarterly_summary`, `ratio_summary`, `dcf_summary`, `segment_mix`, `price_performance`, `industry_overview`.
- New schema blocks where needed (`peer_table`, `valuation_band`, `scenario_table`).
- `financial_model` schema extended for: peer multiples, quarterly series, segment splits, valuation bands, scenarios.
- Sample bundles updated with realistic peer + quarterly + valuation data for ABC and XYZ.

**Exit check:** A generated deck has 12–18 slides covering thesis → business → industry → financials → peers → valuation → scenarios → risks → disclaimer.

---

## Phase 11 — Real AI Planner (kill the mock as default)

**Goal:** Anthropic actually authors the narrative; mock becomes test-only.

**Deliverables**

- Externalized prompts under `prompts/system/` and `prompts/user/` with few-shot examples of high-quality slides.
- Per-layout output contract embedded in the prompt (what bullets look like, tone, length, forbidden phrases).
- Sector-specific hooks (chemicals vs banks vs IT) selectable via `company.sector`.
- Pipeline default switches to real planner; `--mock` flag preserves offline mode.
- Repair loop hardened with structured error feedback to the model.

**Exit check:** Bullets read like analyst prose, not sliced markdown lines. No leading `"- "` artifacts. Thesis differs meaningfully between ABC and XYZ.

---

## Phase 12 — Numeric Integrity & Formatting Authority

**Goal:** No AI-authored numbers ever reach the deck; every number is traceable.

**Deliverables**

- `rendering/number_format.py` — single authority for currency, precision, negatives, %, large-number suffixes (Cr/Bn).
- Validator rejects any metric/table/chart `value` not linked to a `source_key`.
- Cross-check: numbers mentioned in approved narrative must match model snapshot within tolerance, else flag.
- Render manifest records every `(slide, block, source_key, resolved_value)` tuple for audit.

**Exit check:** A QA test that mutates a model number flips every dependent slide value; no orphan numbers found by the auditor.

---

## Phase 13 — Chart Quality Pass

**Goal:** Charts become the visual differentiator, not the weak link.

**Deliverables**

- matplotlib styled from `brand_theme.json` (palette, fonts, gridlines, spines).
- Axis formatters per series unit (₹ Cr, %, x, FY labels).
- Data labels, value callouts, dual-axis combo chart, stacked bar with totals.
- Chart title/subtitle/source-line standardization.
- Optional native python-pptx charts for bar/line behind a flag (image is default).

**Exit check:** Charts in the deck are indistinguishable from a hand-built analyst chart in color, type, and labeling.

---

## Phase 14 — Compliance, PDF, and Pilot Hardening

**Goal:** Deck is distributable, traceable, and survives pilot analyst use.

**Deliverables**

- Real disclaimer + disclosures content loaded from `assets/disclaimers/`; analyst certification slide; ratings distribution slide.
- PDF export wired into default pipeline; every run produces `report.pdf`.
- Overflow polish: title autoshrink, bullet continuation slide, table row-cap with continuation.
- Golden regression: 3 sample companies, structural snapshot diff on every PR.
- Error taxonomy + actionable error messages surfaced through CLI.

**Exit check:** Hand the deck to one analyst, get usable feedback in under 10 minutes — not "where's the logo" or "these numbers aren't formatted."

---

## Execution Order

Run **9 → 10 → 11** in sequence:

1. Brand shell first (cheap visual win, foundation for everything else).
2. Then content depth (more layouts available for the planner to use).
3. Then real AI (now has rich layouts and brand to plan against).

**12 and 13** can run in parallel after 11 lands.

**14** is the closer — compliance, PDF, regression, and pilot readiness.

---

## Working Rules for Agents

- Do not skip exit checks. A phase is not done until its check passes.
- Schema changes must keep `schema_version` discipline — bump and migrate, do not silently break old `report.json`.
- Do not regress the deterministic separation: AI plans narrative, software owns geometry/numbers/formatting.
- Every new layout must register in `LAYOUT_REGISTRY` with placeholders, allowed block types, and required-block rules.
- Every new numeric field must be reachable via `source_key` from a deterministic source (model snapshot or metadata) — never authored by the LLM.
- Update sample bundles (`abc`, `xyz`) whenever schema or layout coverage expands, so end-to-end runs exercise new code paths.
- Treat `assets/` and `prompts/` as first-class — externalize anything currently hardcoded that a non-engineer would want to tune.
