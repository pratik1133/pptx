# Team Execution Plan — Pratik & Kishan

We are two people working **simultaneously** on the same repo to take this from skeleton to a real equity research deck. This document splits each muscle phase (9–14) between Pratik and Kishan so we can work in parallel without colliding, and tells us how to merge everything at the end.

---

## Working Model

- Phases have a real dependency order. We do **not** pretend each phase is independent — see the dependency note at the bottom of this doc.
- Inside each phase, both people work at the same time on different files.
- One phase = one shared branch (`phase-9`, `phase-10`, …). Both push to it. Merge to `main` only when the phase's exit check passes.
- We do **not** keep working on a phase after its exit check passes. We move on.

---

## Phase 9 — Brand Shell & Theme System

**Goal:** Every slide carries firm identity. Output reads as a sell-side note.

### Pratik

- Build `assets/themes/brand_theme.json` (colors, fonts, rating colors, chart palette)
- Add `assets/branding/logo.png` (placeholder is fine to start)
- Write `src/reportgen/rendering/brand_shell.py` — header band, footer strip, page number, divider line, logo
- Write `src/reportgen/rendering/components/rating_badge.py` — colored pill (BUY/HOLD/SELL/REDUCE)
- Write `src/reportgen/rendering/slides/cover_slide.py` — hero cover variant
- Edit `engine.py` to call brand shell on every slide and treat cover slide as a hero
- Edit `geometry.py` to switch canvas to 16:9 (13.33 × 7.5)
- Edit `layout_registry.py` placeholders so titles/blocks respect header/footer reserved zones

### Kishan

- Write `src/reportgen/rendering/theme_loader.py` — JSON → `BrandTheme` pydantic
- Extend `BrandTheme` in `theme.py` with `firm_name`, `logo_path`, `rating_colors`, `chart_palette`, `header_height`, `footer_height`, `accent_color`
- Add `THEME_PATH` setting in `config.py`
- Write `tests/unit/test_theme_loader.py` (round-trip JSON → BrandTheme)
- Write `tests/unit/test_brand_shell.py` (header/footer shapes present after render)

**Exit check:** Generated PPTX shows branded header/footer on every interior slide; cover has hero treatment; rating badge color matches rating; opens cleanly in PowerPoint and LibreOffice.

---

## Phase 10 — Finance Content Depth

**Goal:** 12–18 slides covering the full equity research stack.

### Pratik

- Define new layout geometry in `layout_registry.py`:
  - `peer_comparison`, `valuation_table`, `quarterly_summary`, `ratio_summary`, `dcf_summary`, `segment_mix`, `price_performance`, `industry_overview`
- Build slide files under `src/reportgen/rendering/slides/` for each new layout
- Update `report_builder.py` (deterministic plan) so the new layouts get populated end-to-end
- Wire new block renderers (peer table, valuation band) into `engine.py`

### Kishan

- Extend `schemas/financials.py` with: peer multiples, quarterly series, segment splits, valuation bands, scenarios
- Add new block schemas: `peer_table`, `valuation_band`, `scenario_table` in `schemas/blocks.py` and `schemas/tables.py`
- Bump `schema_version` and add a migration note in `docs/data-contracts.md`
- Extend sample data: `data/samples/financial_models/abc_model.json`, `xyz_model.json`
- Update sample bundles: `data/samples/bundles/abc_bundle.json`, `xyz_bundle.json`
- Add unit tests for the new schemas in `tests/unit/test_schemas.py`

**Exit check:** ABC deck has 12–18 slides covering thesis → business → industry → financials → peers → valuation → scenarios → risks → disclaimer.

---

## Phase 11 — Real AI Planner

**Goal:** Anthropic authors the narrative by default. Mock becomes test-only.

### Pratik

- Externalize prompts:
  - `prompts/system/slide_planner.md`
  - `prompts/user/slide_planner_input.md.j2`
  - `prompts/examples/` — few-shot slides per layout
- Embed per-layout output contracts and forbidden phrases in the prompt
- Add sector-specific hooks (chemicals / banks / IT / consumer) in `prompt_builder.py`
- Add `--mock` flag in `cli.py`; default switches to real planner
- Update `planner.py` so the real path is the default branch

### Kishan

- Harden `repair.py` — feed structured validation errors back to the model
- Strengthen `slide_plan_validator.py`:
  - reject leading-dash bullet artifacts
  - reject AI-authored numbers in metric values (must come via `source_key`)
  - enforce per-layout block contracts
- Tests: `tests/unit/test_repair.py`, `tests/integration/test_real_planner_flow.py` (use a recorded fixture, no live API in tests)

**Exit check:** ABC and XYZ produce visibly different, sector-appropriate narratives. No `"- "` artifacts. No fabricated numbers.

---

## Phase 12 — Numeric Integrity & Formatting

**Goal:** Zero AI-authored numbers reach the deck. Every number traceable.

### Pratik

- Consume the new formatter everywhere numbers are rendered:
  - `metrics_renderer.py`
  - `table_renderer.py`
  - `chart_renderer.py` (axis labels)
  - `cover_slide.py` (CMP/TP card)
- Replace any inline number formatting with calls to the new authority

### Kishan

- Build `src/reportgen/rendering/number_format.py` — single authority for currency, precision, negatives, %, Cr/Bn suffixes
- Add validator in `qa/validators.py` rejecting any block `value` not linked to a `source_key`
- Cross-check approved-narrative numbers vs model snapshot within tolerance
- Extend render manifest to record every `(slide, block, source_key, resolved_value)` tuple
- Tests: `tests/unit/test_number_format.py`, `tests/integration/test_numeric_integrity.py`

**Exit check:** A QA test mutates one model number → every dependent slide value flips; auditor finds zero orphan numbers.

---

## Phase 13 — Chart Quality

**Goal:** Charts become a visual differentiator.

### Pratik

- Confirm `brand_theme.json` chart palette is rich enough; add palette variants (sequential, qualitative)
- Visual review pass: open every chart type in a sample deck, file issues against Kishan's chart code
- Standardize chart titles, subtitles, source-line copy across all chart blocks in slide files

### Kishan

- Style matplotlib from `brand_theme.json` (palette, fonts, gridlines, spines)
- Per-unit axis formatters (₹ Cr, %, x, FY labels)
- Data labels and value callouts
- Implement dual-axis combo chart and stacked bar with totals
- Optional native python-pptx chart path behind a feature flag
- Extend `tests/unit/test_chart_renderer.py`

**Exit check:** Charts in the deck are indistinguishable from a hand-built analyst chart in color, type, and labeling.

---

## Phase 14 — Compliance, PDF, Pilot Hardening

**Goal:** Distributable, traceable, pilot-ready deck.

### Pratik

- Real disclaimer + disclosures content under `assets/disclaimers/`
- Build analyst-certification slide and ratings-distribution slide
- Cover and footer compliance polish (analyst name, date, ticker, page numbers correct)

### Kishan

- Wire PDF export into the default pipeline; every run produces `report.pdf`
- Overflow polish: title autoshrink, bullet continuation slide, table row-cap with continuation
- Golden regression suite: 3 sample companies, structural snapshot diff
- Error taxonomy and CLI error messages

**Exit check:** Hand the deck to one analyst → feedback is about content, not "where's the logo" or "numbers aren't formatted."

---

## How We Work the Same Repo (no clashes)

### Branches

- One phase = one shared branch: `phase-9`, `phase-10`, etc.
- Both Pratik and Kishan push to the same phase branch.
- Inside the phase branch, each person commits to their own files (per the split above).
- We do NOT branch off each other's branches mid-phase — keep it flat.

### Sync routine

Every morning, before writing any code:

```bash
git checkout main
git pull --rebase origin main
git checkout phase-N
git pull --rebase origin phase-N
git rebase main
```

End of every work session: `git push origin phase-N` even if WIP.

### File rule (the only rule that prevents 90% of conflicts)

The only files **both of us legitimately need to edit** are:

- `src/reportgen/rendering/engine.py`
- `src/reportgen/orchestration/pipeline.py`
- `src/reportgen/cli.py`
- `src/reportgen/config.py`

Rule: **before editing any of these four, ping the other person.** Coordinate the edit. Push immediately after.

Everything else is split clean by the per-phase ownership above.

### Commits

- Imperative mood: `add brand shell footer`
- Prefix with phase tag: `[P9] add brand shell footer`
- One logical change per commit

### Daily message (1 minute)

Both post on chat each morning:

1. What I'm doing today
2. What files I'll touch
3. Anything I need from you

That's it.

---

## Final Merge — How to Close Out the Project

When all six phases are merged to `main` and exit checks pass, do this once:

1. **Cut a release branch:** `release/v1.0`
2. **Run the full pipeline** on both ABC and XYZ end-to-end. Verify:
   - 12–18 slides
   - Brand shell on every slide
   - Charts themed and labeled
   - Numbers traceable in the manifest
   - PDF generated
   - Disclaimer slide present
3. **Run the regression suite** on all golden samples. Must pass.
4. **Open final review PR** (`release/v1.0` → `main`). Both Pratik and Kishan review and approve.
5. **Tag the release:** `git tag -a v1.0 -m "muscle phases complete"` and push the tag.
6. **Archive the phase branches:** delete `phase-9` through `phase-14` from the remote after they're merged.
7. **Write release notes** in `docs/CHANGELOG.md` listing what each phase delivered.

After that, `main` is the single source of truth. Future work happens in feature branches off `main`, no longer in numbered phase branches.

---

## Phase Dependency Note (the part you pushed back on)

Phases are not strictly independent. The real flow is:

```
P9 ──┐
     ├─► P11 ──► P12 ─┐
P10 ─┘                ├─► P14
              P13 ────┘
```

- **P9 and P10 can run at the same time** (different files), but P11 cannot start until both are merged because the planner needs both the layouts (P10) and the brand shell geometry (P9).
- **P11 must merge before P12** because P12 validates the planner's output.
- **P12 and P13 run in parallel** after P11 — different concerns (numbers vs charts).
- **P14 closes everything.**

Within each phase, we do **not** continue working on it after the exit check. We close it out, merge to `main`, and start the next.

---

## When in Doubt

- Smaller commit > bigger commit.
- Ask before touching the other person's files.
- The exit check is the truth. If it passes, the phase is done. If not, it's not done — regardless of code written.
- This document is a living contract. If reality drifts from the plan, edit the plan in a PR.
