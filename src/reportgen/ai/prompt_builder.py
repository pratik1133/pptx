from __future__ import annotations

from pathlib import Path

from reportgen.planning.layout_policy import ALLOWED_LAYOUTS, MANDATORY_LAYOUTS
from reportgen.rendering.layout_registry import LAYOUT_REGISTRY
from reportgen.rendering.overflow import bullet_capacity, text_char_budget
from reportgen.rendering.theme import DEFAULT_THEME
from reportgen.rendering.theme_loader import load_brand_theme
from reportgen.config import settings
from reportgen.schemas.bundle import NormalizedInputBundle


PROMPTS_ROOT = Path("prompts")
SYSTEM_PROMPT_PATH = PROMPTS_ROOT / "system" / "slide_planner.md"
USER_TEMPLATE_PATH = PROMPTS_ROOT / "user" / "slide_planner_input.md"
LAYOUT_CONTRACTS_PATH = PROMPTS_ROOT / "contracts" / "layout_contracts.md"
SECTORS_DIR = PROMPTS_ROOT / "sectors"
EXAMPLES_DIR = PROMPTS_ROOT / "examples"


_SECTOR_ALIASES = {
    "financial services": "financial_services",
    "capital markets": "financial_services",
    "broking": "financial_services",
    "asset management": "financial_services",
    "wealth management": "financial_services",
    "nbfc": "financial_services",
    "insurance": "financial_services",
    "banks": "banks",
    "banking": "banks",
    "pvt bank": "banks",
    "psu bank": "banks",
    "chemicals": "chemicals",
    "specialty chemicals": "chemicals",
    "information technology": "it",
    "it services": "it",
    "software": "it",
    "consumer": "consumer",
    "fmcg": "consumer",
    "retail": "consumer",
}


def _read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def _read_system_prompt() -> str:
    return _read_text(
        SYSTEM_PROMPT_PATH,
        default=(
            "You are an equity-research analyst. Output valid JSON only. "
            "Use only allowed layouts. Do not fabricate numbers. Use deterministic source keys."
        ),
    )


SYSTEM_PROMPT = _read_system_prompt()


def _resolve_sector_file(sector: str) -> Path:
    key = sector.strip().lower()
    for needle, slug in _SECTOR_ALIASES.items():
        if needle in key:
            return SECTORS_DIR / f"{slug}.md"
    return SECTORS_DIR / "default.md"


def _read_sector_guidance(sector: str) -> str:
    sector_path = _resolve_sector_file(sector)
    text = _read_text(sector_path)
    if text:
        return text
    return _read_text(SECTORS_DIR / "default.md", default="(no sector guidance available)")


def _read_few_shot_example() -> str:
    example_path = EXAMPLES_DIR / "investment_thesis_example.json"
    return _read_text(example_path, default="(no example available)")


def _format_special_tables(refs) -> str:
    rows: list[str] = []
    if refs.has_peers:
        rows.append("- `peers` — columns: name, ticker, market_cap, pe, ev_ebitda, pb, roe, revenue_growth")
    if refs.has_segments:
        rows.append("- `segments` — columns: name, revenue_share, ebitda_share, growth, aum_label, aum_value, description")
        rows.append("- `segments.revenue_share`, `segments.ebitda_share` — donut chart series ONLY (NOT valid for bar/line/combo charts; NOT chart category sources)")
    if refs.has_valuation_bands:
        rows.append("- `valuation_bands` — columns: method, low, base, high, weight, notes")
    if refs.has_scenarios:
        rows.append("- `scenarios` — columns: name, revenue_cagr, ebitda_margin, target_price, probability, notes")
    if refs.has_ratios:
        rows.append("- `ratio_summary` — columns: ratio, unit, plus one column per period label")
    if refs.has_saarthi:
        rows.append("- `saarthi_dimensions` — columns: code, name, score, assessment, evidence")
    if refs.has_management:
        rows.append("- `management_team` — columns: name, role, bio")
    if refs.has_forensic:
        rows.append("- `forensic_violations` — columns: title, description, severity")
    rows.append("")
    rows.append("**Chart category_source must be exactly `period_labels` or `period_labels.quarterly` — never a segment/peer key.**")
    return "\n".join(rows) if rows else "- (none — bundle has no extended structured data)"


def _build_layout_budgets() -> str:
    """For each layout, list block placeholders with concrete prose / bullet budgets.

    The renderer already knows the exact placeholder geometry. Surface that
    knowledge to the planner so it sizes prose to the actual real estate
    instead of guessing and underfilling.
    """
    theme = load_brand_theme(settings.theme_path) or DEFAULT_THEME
    body_pt = theme.body_font.size_pt

    blocks: list[str] = []
    for layout_name, layout in LAYOUT_REGISTRY.items():
        lines = [f"### `{layout_name}` — {layout.display_name}"]
        # Surface required block constraints
        if layout.required_blocks:
            req = ", ".join(
                f"{r.min_count}{'+' if r.max_count is None else f'-{r.max_count}'} {r.block_type}"
                for r in layout.required_blocks
            )
            lines.append(f"- requires: {req}")
        # Per-placeholder budget
        for ph in layout.placeholders:
            if ph.name == "title" or ph.name == "subtitle":
                continue
            box = ph.box
            if ph.name == "text":
                budget = text_char_budget(box, body_pt)
                target_low = int(budget * 0.55)
                target_high = int(budget * 0.85)
                lines.append(
                    f"- `{ph.name}` block: {box.width:.1f}\" × {box.height:.1f}\" → "
                    f"target {target_low}–{target_high} chars of prose (hard ceiling {budget})."
                )
            elif ph.name == "bullets":
                max_b, per_b = bullet_capacity(box, body_pt)
                lines.append(
                    f"- `{ph.name}` block: {box.width:.1f}\" × {box.height:.1f}\" → "
                    f"target {max(3, max_b - 1)}–{max_b} bullets, {per_b - 40}–{per_b} chars each."
                )
            elif ph.name == "metrics":
                lines.append(
                    f"- `{ph.name}` block: {box.width:.1f}\" × {box.height:.1f}\" → "
                    f"3–6 metric cards (each card needs ~{max(1.6, box.width/4):.1f}\" of width)."
                )
            elif ph.name == "table":
                lines.append(
                    f"- `{ph.name}` block: {box.width:.1f}\" × {box.height:.1f}\" → "
                    "≤ 14 rows; ≤ 6 columns ideal (more triggers font shrink)."
                )
            elif ph.name == "chart":
                lines.append(
                    f"- `{ph.name}` block: {box.width:.1f}\" × {box.height:.1f}\" → "
                    "1 chart; 1 series gets data labels, 2+ series uses legend."
                )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _format_metadata_keys(bundle: NormalizedInputBundle) -> str:
    keys = ["company.name", "company.ticker", "company.sector", "metadata.rating", "metadata.cmp", "metadata.target_price", "metadata.analyst"]
    if bundle.source.metadata.upside_pct is not None:
        keys.append("metadata.upside_pct")
    return "\n".join(f"- `{k}`" for k in keys)


def _format_list(items: list[str], empty: str = "- (none)") -> str:
    if not items:
        return empty
    return "\n".join(f"- `{item}`" for item in items)


def _format_narrative_sections(bundle: NormalizedInputBundle) -> str:
    if not bundle.report_sections:
        return "(no narrative sections available)"
    blocks = []
    for section in bundle.report_sections:
        blocks.append(f"### {section.heading}\n\n{section.body}")
    return "\n\n".join(blocks)


def build_slide_planner_prompt(
    bundle: NormalizedInputBundle,
    *,
    min_slides: int,
    max_slides: int,
    error_feedback: list[str] | None = None,
    previous_attempt_json: str | None = None,
) -> str:
    refs = bundle.data_references
    template = _read_text(USER_TEMPLATE_PATH)
    if not template:
        raise FileNotFoundError(f"Slide planner user template missing at {USER_TEMPLATE_PATH}")

    static_contracts = _read_text(LAYOUT_CONTRACTS_PATH, default="")
    dynamic_budgets = _build_layout_budgets()
    layout_contracts = (
        "## Per-layout block budgets (computed from real placeholder geometry)\n\n"
        + dynamic_budgets
        + ("\n\n## Additional layout notes\n\n" + static_contracts if static_contracts else "")
    )

    body = template.format(
        company_name=bundle.source.company.name,
        ticker=bundle.normalized_ticker,
        exchange=bundle.normalized_exchange,
        sector=bundle.source.company.sector,
        industry=bundle.source.company.industry or "-",
        description=bundle.source.company.description or "-",
        rating=bundle.normalized_rating,
        currency=bundle.normalized_currency,
        analyst=bundle.source.metadata.analyst,
        report_type=bundle.source.metadata.report_type,
        report_date=str(bundle.source.metadata.report_date),
        allowed_layouts=", ".join(ALLOWED_LAYOUTS),
        mandatory_layouts=", ".join(MANDATORY_LAYOUTS),
        min_slides=min_slides,
        max_slides=max_slides,
        layout_contracts=layout_contracts,
        sector_guidance=_read_sector_guidance(bundle.source.company.sector),
        metadata_keys=_format_metadata_keys(bundle),
        metric_source_keys=_format_list(refs.metric_source_keys),
        series_source_keys=_format_list(refs.series_source_keys),
        quarterly_source_keys=_format_list(refs.quarterly_series_source_keys),
        ratio_source_keys=_format_list(refs.ratio_source_keys),
        period_labels=", ".join(refs.period_labels) if refs.period_labels else "-",
        special_tables=_format_special_tables(refs),
        narrative_sections=_format_narrative_sections(bundle),
        few_shot_example=_read_few_shot_example(),
    )

    if error_feedback:
        feedback_block = (
            "\n\n# REPAIR FEEDBACK — your previous attempt was rejected\n\n"
            "Fix exactly the errors below. Do not change anything else.\n\n"
            + "\n".join(f"- {err}" for err in error_feedback)
        )
        body += feedback_block
        if previous_attempt_json:
            body += "\n\n## Previous attempt (for reference)\n\n```json\n" + previous_attempt_json + "\n```"

    return body
