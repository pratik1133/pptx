from __future__ import annotations

from datetime import datetime, timezone

from reportgen.ai.openrouter_client import OpenRouterPlanningClient, PlanningModelClient
from reportgen.ai.prompt_builder import SYSTEM_PROMPT, build_slide_planner_prompt
from reportgen.ai.repair import parse_slide_plan_safely
from reportgen.ai.serializers import dump_slide_plan_json
from reportgen.config import settings
from reportgen.ingestion.errors import InputValidationError
from reportgen.planning.slide_plan_validator import validate_slide_plan
from reportgen.schemas.bundle import NormalizedInputBundle
from reportgen.schemas.planning import (
    PlanningBulletBlock,
    PlanningChartBlock,
    PlanningMetricItem,
    PlanningMetricsBlock,
    PlanningTableBlock,
    PlanningTableColumn,
    PlanningTextBlock,
    SlidePlan,
    SlidePlanSlide,
)


class MockPlanningClient:
    """Sentinel for the local deterministic planner; not a real LLM client."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("MockPlanningClient should not be called directly through generate().")


def _section_by_keyword(bundle: NormalizedInputBundle, keyword: str):
    return next(
        (s for s in bundle.report_sections if keyword in s.heading.casefold()),
        None,
    )


_NUMBER_SANITIZER = __import__("re").compile(
    r"(?<!FY)(?<!fy)\b\d[\d,]*(?:\.\d+)?\s*(?:%|x\b|cr\b|crore\b|bn\b|billion\b|lakh\b|bps\b)"
    r"|(?:₹|\$|€|£|INR\s|USD\s|EUR\s|GBP\s)\s*\d[\d,]*(?:\.\d+)?",
    __import__("re").IGNORECASE,
)


def _strip_numbers(text: str) -> str:
    """Remove orphan numeric tokens with units so mock prose passes the validator.

    Mock planner inherits raw analyst narrative which is allowed to contain numbers;
    the schema-level rule is that the *deck* surfaces numbers via metric/table blocks,
    not in prose. Sanitize narrative prose accordingly.
    """
    cleaned = _NUMBER_SANITIZER.sub("the relevant figure", text)
    return " ".join(cleaned.split())


def _safe_lines(text: str, limit: int = 5, max_len: int = 180) -> list[str]:
    cleaned: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip("- ").strip()
        if stripped:
            cleaned.append(_strip_numbers(stripped)[:max_len])
        if len(cleaned) >= limit:
            break
    return cleaned or [_strip_numbers(text.strip())[:max_len]]


def _next_id(slides: list[SlidePlanSlide]) -> str:
    return f"s{len(slides) + 1}"


def build_mock_slide_plan(bundle: NormalizedInputBundle) -> SlidePlan:
    refs = bundle.data_references
    fm = bundle.source.financial_model
    sections = bundle.report_sections
    first_section = sections[0]
    risk_section = _section_by_keyword(bundle, "risk") or sections[-1]
    industry_section = _section_by_keyword(bundle, "industry")
    catalyst_section = _section_by_keyword(bundle, "catalyst")
    chart_source = refs.series_source_keys[0] if refs.series_source_keys else None

    slides: list[SlidePlanSlide] = []

    slides.append(
        SlidePlanSlide(
            slide_id=_next_id(slides),
            layout="cover_slide",
            title=bundle.primary_title,
            subtitle=f"{bundle.source.company.name} | {bundle.normalized_rating}",
            blocks=[
                PlanningMetricsBlock(
                    key="headline_metrics",
                    items=[
                        PlanningMetricItem(label="Rating", source_key="metadata.rating"),
                        PlanningMetricItem(label="CMP", source_key="metadata.cmp"),
                        PlanningMetricItem(label="TP", source_key="metadata.target_price"),
                    ],
                )
            ],
        )
    )

    slides.append(
        SlidePlanSlide(
            slide_id=_next_id(slides),
            layout="investment_thesis",
            title="Investment Thesis",
            blocks=[
                PlanningTextBlock(key="summary", content=_strip_numbers(first_section.body)),
                PlanningBulletBlock(
                    key="key_points",
                    items=_safe_lines("\n".join(s.body for s in sections[:3]), limit=6),
                ),
            ],
        )
    )

    if refs.has_saarthi:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="saarthi_scorecard",
                title=f"SAARTHI Investment Quality Score — {fm.saarthi.total_score}/{fm.saarthi.max_score}",
                blocks=[
                    PlanningTextBlock(
                        key="saarthi_intro",
                        content=f"Proprietary 7-dimension framework. Overall score {fm.saarthi.total_score}/{fm.saarthi.max_score} ({fm.saarthi.rating}).",
                    ),
                    PlanningTableBlock(
                        key="saarthi_table",
                        title="SAARTHI Dimensions",
                        source_key="saarthi_dimensions",
                        columns=[
                            PlanningTableColumn(key="code", label="Code"),
                            PlanningTableColumn(key="name", label="Dimension"),
                            PlanningTableColumn(key="score", label="Score"),
                            PlanningTableColumn(key="evidence", label="Key Evidence"),
                        ],
                    ),
                ],
            )
        )

    snapshot_metrics = [
        PlanningMetricItem(label="CMP", source_key="metadata.cmp"),
        PlanningMetricItem(label="TP", source_key="metadata.target_price"),
    ]
    if bundle.source.metadata.upside_pct is not None:
        snapshot_metrics.append(PlanningMetricItem(label="Upside", source_key="metadata.upside_pct"))
    slides.append(
        SlidePlanSlide(
            slide_id=_next_id(slides),
            layout="company_snapshot",
            title=f"{bundle.source.company.name} At A Glance",
            blocks=[
                PlanningTextBlock(
                    key="business_summary",
                    content=bundle.source.company.description
                    or f"{bundle.source.company.name} operates in {bundle.source.company.sector}.",
                ),
                PlanningMetricsBlock(key="snapshot_metrics", items=snapshot_metrics),
            ],
        )
    )

    if industry_section:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="industry_overview",
                title="Industry Overview",
                blocks=[
                    PlanningTextBlock(key="industry_text", content=_strip_numbers(industry_section.body)),
                    PlanningBulletBlock(
                        key="industry_points",
                        items=[_strip_numbers(t) for t in ((refs.has_industry_tailwinds and fm.industry_tailwinds[:6]) or _safe_lines(industry_section.body, limit=5))],
                    ),
                ],
            )
        )

    if refs.has_key_highlights:
        highlight_items = [_strip_numbers(f"{h.title}: {h.body}")[:200] for h in fm.key_highlights[:6]]
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="key_highlights",
                title="Key Highlights",
                blocks=[
                    PlanningTextBlock(
                        key="highlights_intro",
                        content="Six themes underpinning the investment view.",
                    ),
                    PlanningBulletBlock(key="highlights_items", items=highlight_items),
                ],
            )
        )

    if chart_source:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="text_plus_chart",
                title="Revenue Trend",
                blocks=[
                    PlanningTextBlock(
                        key="trend_summary",
                        content="Revenue trajectory across the forecast period reflects mix shift and AUM scale-up.",
                    ),
                    PlanningChartBlock(
                        key="trend_chart",
                        chart_type="bar",
                        title="Revenue Trend",
                        category_source="period_labels",
                        series_source_keys=[chart_source],
                    ),
                ],
            )
        )

    if chart_source:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="full_table",
                title="Annual Financial Summary",
                blocks=[
                    PlanningTableBlock(
                        key="financial_table",
                        title="Revenue By Period",
                        source_key=chart_source,
                        columns=[
                            PlanningTableColumn(key="period", label="Period"),
                            PlanningTableColumn(key="value", label="Revenue"),
                        ],
                    )
                ],
            )
        )

    if refs.has_quarterly:
        q_source = refs.quarterly_series_source_keys[0]
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="quarterly_summary",
                title="Quarterly Performance",
                blocks=[
                    PlanningTextBlock(
                        key="quarterly_text",
                        content="Recent quarterly trajectory showing the variability inherent to the cyclical revenue base.",
                    ),
                    PlanningTableBlock(
                        key="quarterly_table",
                        title="Quarterly PAT",
                        source_key=q_source,
                        columns=[
                            PlanningTableColumn(key="period", label="Quarter"),
                            PlanningTableColumn(key="value", label="PAT"),
                        ],
                    ),
                ],
            )
        )

    if refs.has_segments:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="full_table",
                title="Segment Mix",
                blocks=[
                    PlanningTableBlock(
                        key="segment_table",
                        title="Segment Breakdown",
                        source_key="segments",
                        columns=[
                            PlanningTableColumn(key="name", label="Segment"),
                            PlanningTableColumn(key="aum_label", label="Scale Metric"),
                            PlanningTableColumn(key="aum_value", label="Latest"),
                            PlanningTableColumn(key="description", label="Notes"),
                        ],
                    )
                ],
            )
        )

    if refs.has_ratios:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="ratio_summary",
                title="Key Ratios",
                blocks=[
                    PlanningTextBlock(
                        key="ratio_text",
                        content="Margin and return profile across the forecast period.",
                    ),
                    PlanningTableBlock(
                        key="ratio_table",
                        title="Ratio Summary",
                        source_key="ratio_summary",
                        columns=[
                            PlanningTableColumn(key="ratio", label="Ratio"),
                            *[PlanningTableColumn(key=p, label=p) for p in (refs.period_labels or [])],
                        ],
                    ),
                ],
            )
        )

    if refs.has_valuation_bands:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="valuation_table",
                title="Valuation — Methods Summary",
                blocks=[
                    PlanningTextBlock(
                        key="valuation_text",
                        content="Probability-weighted target price reconciles bull, base, and bear cases.",
                    ),
                    PlanningTableBlock(
                        key="valuation_methods_table",
                        title="Target Price Bands",
                        source_key="valuation_bands",
                        columns=[
                            PlanningTableColumn(key="method", label="Case"),
                            PlanningTableColumn(key="base", label="Target"),
                            PlanningTableColumn(key="weight", label="Weight"),
                            PlanningTableColumn(key="notes", label="Basis"),
                        ],
                    ),
                ],
            )
        )

    if refs.has_scenarios:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="full_table",
                title="Scenario Analysis",
                blocks=[
                    PlanningTableBlock(
                        key="scenario_table",
                        title="Bull / Base / Bear",
                        source_key="scenarios",
                        columns=[
                            PlanningTableColumn(key="name", label="Case"),
                            PlanningTableColumn(key="revenue_cagr", label="Rev CAGR"),
                            PlanningTableColumn(key="ebitda_margin", label="EBITDA Mgn"),
                            PlanningTableColumn(key="target_price", label="Target Price"),
                            PlanningTableColumn(key="probability", label="Probability"),
                            PlanningTableColumn(key="notes", label="Drivers"),
                        ],
                    )
                ],
            )
        )

    if catalyst_section:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="text_plus_bullets",
                title="Key Catalysts",
                blocks=[
                    PlanningTextBlock(key="catalysts_text", content=_strip_numbers(catalyst_section.body)),
                    PlanningBulletBlock(
                        key="catalyst_points",
                        items=_safe_lines(catalyst_section.body, limit=5),
                    ),
                ],
            )
        )

    if refs.has_management:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="management_profile",
                title="Management Team",
                blocks=[
                    PlanningTextBlock(
                        key="management_intro",
                        content="Founder-led leadership with deep institutional DNA.",
                    ),
                    PlanningTableBlock(
                        key="management_table",
                        title="Leadership",
                        source_key="management_team",
                        columns=[
                            PlanningTableColumn(key="name", label="Name"),
                            PlanningTableColumn(key="role", label="Role"),
                            PlanningTableColumn(key="bio", label="Background"),
                        ],
                    ),
                ],
            )
        )

    if refs.has_forensic:
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="forensic_assessment",
                title=f"Forensic / Governance — {fm.forensic.category}",
                blocks=[
                    PlanningTextBlock(
                        key="forensic_intro",
                        content=fm.forensic.overall_assessment,
                    ),
                    PlanningTableBlock(
                        key="forensic_table",
                        title="Regulatory Matters",
                        source_key="forensic_violations",
                        columns=[
                            PlanningTableColumn(key="title", label="Matter"),
                            PlanningTableColumn(key="description", label="Description"),
                            PlanningTableColumn(key="severity", label="Severity"),
                        ],
                    ),
                ],
            )
        )

    if refs.has_trading_strategy:
        ts = fm.trading_strategy
        review_items = [_strip_numbers(item) for item in list(ts.review_metrics)[:5]] or ["Review metrics not specified"]
        slides.append(
            SlidePlanSlide(
                slide_id=_next_id(slides),
                layout="text_plus_bullets",
                title="Trading Strategy",
                blocks=[
                    PlanningTextBlock(
                        key="strategy_text",
                        content=_strip_numbers(
                            f"Entry: {ts.entry_range or '-'}. {ts.entry_rationale or ''}\n"
                            f"Position size: {ts.position_size or '-'}.\n"
                            f"Review: {ts.review_frequency or '-'}.\n"
                            f"Downside exit: {ts.downside_exit or '-'}.\n"
                            f"Upside exit: {' / '.join(ts.upside_exit) if ts.upside_exit else '-'}."
                        ),
                    ),
                    PlanningBulletBlock(key="strategy_review", items=review_items),
                ],
            )
        )

    slides.append(
        SlidePlanSlide(
            slide_id=_next_id(slides),
            layout="risks_and_catalysts",
            title="Key Risks",
            blocks=[
                PlanningBulletBlock(
                    key="risk_points",
                    items=_safe_lines(risk_section.body, limit=6),
                )
            ],
        )
    )

    from reportgen.compliance import load_analyst_certification_text, load_disclaimer_text

    slides.append(
        SlidePlanSlide(
            slide_id=_next_id(slides),
            layout="analyst_certification",
            title="Analyst Certification & Disclosures",
            blocks=[PlanningTextBlock(key="cert_text", content=load_analyst_certification_text())],
        )
    )

    slides.append(
        SlidePlanSlide(
            slide_id=_next_id(slides),
            layout="disclaimer",
            title="Disclaimer",
            blocks=[PlanningTextBlock(key="disclaimer_text", content=load_disclaimer_text())],
        )
    )

    return SlidePlan(
        company_ticker=bundle.normalized_ticker,
        generated_at=datetime.now(timezone.utc),
        slides=slides,
    )


def plan_slides_with_client(
    bundle: NormalizedInputBundle,
    client: PlanningModelClient,
) -> SlidePlan:
    """Call the live LLM client with a repair loop. Errors from validation are fed back."""

    last_errors: list[str] = []
    last_attempt_json: str | None = None

    for attempt in range(settings.max_planning_retries + 1):
        user_prompt = build_slide_planner_prompt(
            bundle,
            min_slides=settings.min_slide_count,
            max_slides=settings.max_slide_count,
            error_feedback=last_errors or None,
            previous_attempt_json=last_attempt_json,
        )

        try:
            raw_response = client.generate(SYSTEM_PROMPT, user_prompt)
        except Exception as exc:  # noqa: BLE001
            last_errors = [f"LLM call failed: {exc}"]
            last_attempt_json = None
            continue

        outcome = parse_slide_plan_safely(raw_response)
        if outcome.plan is None:
            last_errors = outcome.errors
            last_attempt_json = raw_response
            continue

        try:
            validate_slide_plan(outcome.plan, bundle)
        except InputValidationError as exc:
            last_errors = list(exc.errors)
            last_attempt_json = raw_response
            continue

        return outcome.plan

    raise InputValidationError(
        ["Slide planning failed after retries."] + last_errors
    )


def plan_slides_mock(bundle: NormalizedInputBundle) -> SlidePlan:
    plan = build_mock_slide_plan(bundle)
    validate_slide_plan(plan, bundle)
    return plan


def plan_slides(bundle: NormalizedInputBundle, *, use_mock: bool = False) -> SlidePlan:
    """Default planning entry point.

    By default, calls the real OpenRouter planner. Falls back to mock if no API key
    is configured, or if `use_mock=True` is passed explicitly.
    """
    if use_mock or not settings.openrouter_api_key:
        return plan_slides_mock(bundle)

    client = OpenRouterPlanningClient()
    return plan_slides_with_client(bundle, client)


def render_plan_payload(bundle: NormalizedInputBundle) -> str:
    return dump_slide_plan_json(plan_slides_mock(bundle))
