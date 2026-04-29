from datetime import datetime, timezone

from reportgen.ai.anthropic_client import PlanningModelClient
from reportgen.ai.prompt_builder import SYSTEM_PROMPT, build_slide_planner_prompt
from reportgen.ai.repair import repair_and_parse_slide_plan
from reportgen.ai.serializers import dump_slide_plan_json
from reportgen.config import settings
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
    """Deterministic local planner for development, tests, and offline workflow design."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("MockPlanningClient should not be called directly through generate().")


def build_mock_slide_plan(bundle: NormalizedInputBundle) -> SlidePlan:
    first_section = bundle.report_sections[0]
    risk_section = next(
        (section for section in bundle.report_sections if "risk" in section.heading.casefold()),
        bundle.report_sections[-1],
    )
    chart_source = bundle.data_references.series_source_keys[0]

    plan = SlidePlan(
        company_ticker=bundle.normalized_ticker,
        generated_at=datetime.now(timezone.utc),
        slides=[
            SlidePlanSlide(
                slide_id="s1",
                layout="cover_slide",
                title=bundle.primary_title,
                subtitle=f"{bundle.source.company.name} | {bundle.normalized_rating}",
                rationale="Introduce the company and headline recommendation.",
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
            ),
            SlidePlanSlide(
                slide_id="s2",
                layout="investment_thesis",
                title="Investment Thesis",
                rationale="Lead with the core investment case from the approved narrative.",
                blocks=[
                    PlanningTextBlock(key="summary", content=first_section.body),
                    PlanningBulletBlock(
                        key="key_points",
                        items=[
                            section.body.splitlines()[0][:160]
                            for section in bundle.report_sections[:3]
                        ],
                    ),
                ],
            ),
            SlidePlanSlide(
                slide_id="s3",
                layout="company_snapshot",
                title=f"{bundle.source.company.name} At A Glance",
                rationale="Provide company context and headline metrics.",
                blocks=[
                    PlanningTextBlock(
                        key="business_summary",
                        content=bundle.source.company.description
                        or f"{bundle.source.company.name} operates in {bundle.source.company.sector}.",
                    ),
                    PlanningMetricsBlock(
                        key="snapshot_metrics",
                        items=[
                            PlanningMetricItem(label="CMP", source_key="metadata.cmp"),
                            PlanningMetricItem(label="TP", source_key="metadata.target_price"),
                            *(
                                [PlanningMetricItem(label="Upside", source_key="metadata.upside_pct")]
                                if bundle.source.metadata.upside_pct is not None
                                else []
                            ),
                        ],
                    ),
                ],
            ),
            SlidePlanSlide(
                slide_id="s4",
                layout="text_plus_chart",
                title="Financial Trend Overview",
                rationale="Connect narrative to deterministic historical and forecast series.",
                blocks=[
                    PlanningTextBlock(
                        key="trend_summary",
                        content="Revenue and profitability trends should be grounded in deterministic model outputs.",
                    ),
                    PlanningChartBlock(
                        key="trend_chart",
                        chart_type="bar",
                        title="Revenue Trend",
                        category_source="period_labels",
                        series_source_keys=[chart_source],
                    ),
                ],
            ),
            SlidePlanSlide(
                slide_id="s5",
                layout="full_table",
                title="Revenue Summary Table",
                rationale="Provide a deterministic tabular view of the main financial series.",
                blocks=[
                    PlanningTableBlock(
                        key="revenue_table",
                        title="Revenue By Period",
                        source_key=chart_source,
                        columns=[
                            PlanningTableColumn(key="period", label="Period"),
                            PlanningTableColumn(key="value", label="Value"),
                        ],
                    )
                ],
            ),
            SlidePlanSlide(
                slide_id="s6",
                layout="risks_and_catalysts",
                title="Risks And Catalysts",
                rationale="Capture key monitoring points from the approved narrative.",
                blocks=[
                    PlanningBulletBlock(
                        key="risk_points",
                        items=[line[:160] for line in risk_section.body.splitlines() if line][:5],
                    )
                ],
            ),
            SlidePlanSlide(
                slide_id="s7",
                layout="disclaimer",
                title="Disclaimer",
                rationale="Mandatory compliance slide.",
                blocks=[
                    PlanningTextBlock(
                        key="disclaimer_text",
                        content="For internal research workflow validation only. Final legal disclaimer copy will be supplied from approved assets.",
                    )
                ],
            ),
        ],
    )
    return plan


def plan_slides_with_client(
    bundle: NormalizedInputBundle,
    client: PlanningModelClient,
) -> SlidePlan:
    system_prompt = SYSTEM_PROMPT
    user_prompt = build_slide_planner_prompt(bundle)

    last_error: Exception | None = None
    for _ in range(settings.max_planning_retries + 1):
        try:
            raw_response = client.generate(system_prompt, user_prompt)
            plan = repair_and_parse_slide_plan(raw_response)
            validate_slide_plan(plan, bundle)
            return plan
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError("Slide planning failed without an explicit error.")


def plan_slides_mock(bundle: NormalizedInputBundle) -> SlidePlan:
    plan = build_mock_slide_plan(bundle)
    validate_slide_plan(plan, bundle)
    return plan


def render_plan_payload(bundle: NormalizedInputBundle) -> str:
    return dump_slide_plan_json(plan_slides_mock(bundle))
