# Layout contracts

Each layout below states its purpose, required blocks, and writing guidance.

## cover_slide
- **Purpose**: report cover with rating, CMP, target price.
- **Required blocks**: 1 `metrics` block.
- **Title**: full report title (e.g., "Motilal Oswal Initiation Note").
- **Subtitle**: company name + rating short form.
- **Metrics**: 3 cards — Rating, CMP, TP — referencing `metadata.rating`, `metadata.cmp`, `metadata.target_price`.

## investment_thesis
- **Purpose**: one-paragraph thesis + 4–6 supporting bullets.
- **Required blocks**: 1 `text` block, 1 `bullets` block.
- **Text**: 2–4 sentences distilling the thesis from approved narrative.
- **Bullets**: 4–6 evidence-led points; parallel construction; no numbers fabricated.

## company_snapshot
- **Purpose**: at-a-glance company summary.
- **Required blocks**: 1 `text` block, 1 `metrics` block.
- **Text**: 2–4 sentences on what the company does and how it makes money.
- **Metrics**: 2–4 cards — typically CMP, TP, and one diversification metric (e.g., upside).

## industry_overview
- **Purpose**: sector context.
- **Required blocks**: 1 `text` block, 1 `bullets` block.
- **Text**: 3–5 sentences on industry size, structure, dynamics.
- **Bullets**: 3–6 tailwinds.

## key_highlights
- **Purpose**: themed callouts that anchor the deck.
- **Required blocks**: 1 `bullets` block (and optional `text`).
- **Bullets**: 5–6 themed entries, each formatted as `Title: short body`.

## text_plus_chart
- **Purpose**: narrative paired with a single chart.
- **Required blocks**: 1 `text` block, 1 `chart` block.
- **Chart**: `bar` or `line`; reference `period_labels` for categories and one `series.<name>` source.

## full_width_chart
- **Purpose**: a single hero chart.
- **Required blocks**: 1 `chart` block.

## full_table
- **Purpose**: standalone table — works for revenue summary, segments, scenarios.
- **Required blocks**: 1 `table` block.

## quarterly_summary
- **Purpose**: quarter-over-quarter view.
- **Required blocks**: 1 `table` block (optional `text` + `chart`).
- **Source**: `quarterly_series.<name>`.

## ratio_summary
- **Purpose**: margins, returns, leverage, multiples.
- **Required blocks**: 1 `table` block.
- **Source**: `ratio_summary` with one column per period in `period_labels`.

## segment_mix
- **Purpose**: revenue / EBITDA / scale split by segment.
- **Required blocks**: 1 `chart` block (optional `text` and `table`).
- **Source**: `segments.revenue_share` (chart) or `segments` (table).

## peer_comparison
- **Purpose**: peer multiples table with target highlighted.
- **Required blocks**: 1 `table` block.
- **Source**: `peers`. Skip this layout entirely if the bundle has no peers.

## valuation_table
- **Purpose**: methods → low/base/high → target reconciliation.
- **Required blocks**: 1 `table` block.
- **Source**: `valuation_bands`.

## valuation_summary
- **Purpose**: valuation narrative with metric cards.
- **Required blocks**: 1 `text`, 1 `metrics`.

## dcf_summary
- **Purpose**: DCF assumptions + outputs.
- **Required blocks**: 1 `text`, 1 `metrics`.
- **Metrics**: WACC, terminal-g if available.

## price_performance
- **Purpose**: share-price + index relative performance.
- **Required blocks**: 1 `chart` block.

## saarthi_scorecard
- **Purpose**: proprietary 7-dimension investment-quality score.
- **Required blocks**: 1 `table` block (optional `text` + `metrics`).
- **Source**: `saarthi_dimensions`.
- **Title**: include the total score, e.g., "SAARTHI Score 72/100".

## management_profile
- **Purpose**: leadership team.
- **Required blocks**: 1 `table` block (optional `text`).
- **Source**: `management_team`.

## forensic_assessment
- **Purpose**: governance / regulatory matters.
- **Required blocks**: 1 `table` block (optional `text`).
- **Source**: `forensic_violations`. Title may include category, e.g. "Forensic — Monitor Closely".

## trading_strategy
- **Purpose**: entry / review / exit guidance.
- **Required blocks**: 1–2 `bullets` blocks (optional `text`, `metrics`).

## risks_and_catalysts
- **Purpose**: monitoring points.
- **Required blocks**: 1 `bullets` block.
- **Bullets**: 4–6 thesis-breaking risks; clean prose.

## text_plus_bullets
- **Purpose**: generic narrative + bullets.
- **Required blocks**: 1 `text` block, 1 `bullets` block.

## disclaimer
- **Purpose**: mandatory closing slide.
- **Required blocks**: 1 `text` block.
- **Text**: standard SEBI disclaimer language. The renderer may replace this with approved boilerplate.
