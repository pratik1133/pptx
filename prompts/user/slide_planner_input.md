# Inputs

## Company

- Name: {company_name}
- Ticker: {ticker}
- Exchange: {exchange}
- Sector: {sector}
- Industry: {industry}
- Description: {description}

## Research metadata

- Rating: {rating}
- Currency: {currency}
- Analyst: {analyst}
- Report type: {report_type}
- Report date: {report_date}

## Layout & structural constraints

- Allowed layouts: {allowed_layouts}
- Mandatory layouts: {mandatory_layouts}
- Slide count range: {min_slides} to {max_slides}

## Layout contracts

{layout_contracts}

## Sector guidance

{sector_guidance}

## Deterministic source keys you may reference

Headline metadata keys:
{metadata_keys}

Financial metrics:
{metric_source_keys}

Annual series:
{series_source_keys}

Quarterly series:
{quarterly_source_keys}

Ratios:
{ratio_source_keys}

Period labels:
- `period_labels` (annual): {period_labels}
- `period_labels.quarterly` (if quarterly data exists)

Special structured tables (use `source_key` of the listed value when present):
{special_tables}

## Structured source data snapshot

Use this JSON only as source context for company-specific judgment and wording.
Do not copy this object into your response. Your response must still be only a `SlidePlan`.
Use source keys for numeric display instead of embedding numbers in prose.
Important: raw JSON field names are not always valid renderer keys. For table blocks, use the column names listed in "Special structured tables", not raw fields from this snapshot.

Common mappings:
- `segments.revenue_share_pct` -> table column `revenue_share`; chart series `segments.revenue_share`
- `segments.ebitda_share_pct` -> table column `ebitda_share`; chart series `segments.ebitda_share`
- `valuation_bands.weight_pct` -> table column `weight`
- `scenarios.revenue_cagr_pct` -> table column `revenue_cagr`
- `scenarios.ebitda_margin_pct` -> table column `ebitda_margin`
- `scenarios.probability_pct` -> table column `probability`
- `forensic.violations` -> table source_key `forensic_violations`
- Chart `category_source` must be `period_labels` or `period_labels.quarterly`, never `segments`.

```json
{data_snapshot}
```

## Approved narrative sections (verbatim source — do not invent)

{narrative_sections}

## Few-shot example (for reference, not to copy verbatim)

{few_shot_example}

# PPTX renderer contract

You are writing the same kind of JSON that the local mock planner writes: a `SlidePlan`.
Do not write python-pptx instructions, coordinates, colors, fonts, shape names, or already-resolved metric values.
The Python software will convert your `source_key` references into `report.json`, then the PPTX renderer will apply the existing template, shell, headers, footers, charts, tables, and branding.

## Custom-renderer coverage

The PPTX engine has bespoke Python renderers only for specific layouts / title patterns.
Prefer these custom-rendered patterns so the deck does not fall back to the basic layout renderer:

- `cover_slide` with any title.
- `text_plus_chart` with title starting exactly `Story in Charts`.
- `investment_thesis`.
- `industry_overview`.
- `company_snapshot`.
- `key_highlights`.
- `segment_mix`, or `full_table` with a title containing `Business Model` / `Business Segment`, when segment data exists.
- `full_table` with title containing `Earnings Forecast`.
- `quarterly_summary`.
- `valuation_table` or `valuation_summary`.
- `saarthi_scorecard`.
- `scenario_analysis`.
- `forensic_assessment`.
- `risks_and_catalysts`.
- `trading_strategy`, or `text_plus_bullets` with title containing both `Entry` and `Exit`.
- `disclaimer`.

Layouts not listed above may render in the basic fallback style. Use them only if no custom-rendered pattern can represent the content.

Use this deck recipe whenever the required data exists. If a data source does not exist, skip only that optional slide and keep the remaining order:

1. `cover_slide` — title, subtitle, `headline_metrics` from metadata, one `text` block for the cover investment thesis, and one `bullets` block for cover highlights.
2. `text_plus_chart` — "Story in Charts" using the strongest available annual series, usually `series.Revenue`, with `period_labels`.
3. `investment_thesis` — company-specific thesis from approved narrative.
4. `industry_overview` — sector tailwinds and risks from approved narrative / structured industry fields.
5. `company_snapshot` — what the company does, with CMP / target / upside metrics.
6. `key_highlights` or `text_plus_bullets` — key investment idea in detail.
7. `segment_mix` or `full_table` with `segments` when segment data exists.
8. `text_plus_bullets` — demand drivers / catalysts when narrative supports it.
9. `text_plus_bullets` — competitive landscape when structured advantages exist.
10. `forensic_assessment` or `key_highlights` for management / governance context when management data exists; avoid `management_profile` unless a basic table is acceptable.
11. `forensic_assessment` when forensic data exists.
12. `full_table` — earnings forecast using a main annual series table.
13. `quarterly_summary` when quarterly data exists.
14. `valuation_table`, `valuation_summary`, or an earnings/financial custom slide for ratio evidence; avoid `ratio_summary` unless a basic table is acceptable.
15. `valuation_table` or `valuation_summary` when valuation data exists.
16. `saarthi_scorecard` when SAARTHI data exists.
17. `scenario_analysis` when scenarios exist.
18. `risks_and_catalysts` — thesis risks and invalidation triggers.
19. `trading_strategy` or `text_plus_bullets` — entry, review, exit strategy when data exists.
20. `disclaimer` — final slide.

For metric blocks, output only `label` and `source_key`; never output `value`.
For chart blocks, output `category_source` and `series_source_keys`; never output chart data arrays.
For table blocks, output `source_key` and renderer-supported column keys; never output table rows.
For text and bullet blocks, use the approved narrative and structured non-numeric fields. Avoid generic placeholder sentences such as "should be grounded in deterministic model outputs".

# Your task

Produce a slide plan that:

1. Tells the investment story clearly across {min_slides}–{max_slides} slides.
2. Opens with `cover_slide` and ends with `disclaimer`.
3. Uses every relevant data source the bundle provides — do not skip peers, segments, scenarios, ratios, SAARTHI, management, forensic, valuation bands, or trading strategy when they exist.
4. Keeps prose evidence-led and free of promotional language.
5. Respects every block-type constraint in the layout contracts.
6. If the structured source data snapshot contains most optional sections, target a full institutional deck of 15–20 slides. The lower bound exists only for genuinely sparse bundles.

Return **only the JSON object**.
