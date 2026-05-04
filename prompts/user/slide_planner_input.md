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

## Approved narrative sections (verbatim source — do not invent)

{narrative_sections}

## Few-shot example (for reference, not to copy verbatim)

{few_shot_example}

# Your task

Produce a slide plan that:

1. Tells the investment story clearly across {min_slides}–{max_slides} slides.
2. Opens with `cover_slide` and ends with `disclaimer`.
3. Uses every relevant data source the bundle provides — do not skip peers, segments, scenarios, ratios, SAARTHI, management, forensic, valuation bands, or trading strategy when they exist.
4. Keeps prose evidence-led and free of promotional language.
5. Respects every block-type constraint in the layout contracts.

Return **only the JSON object**.
