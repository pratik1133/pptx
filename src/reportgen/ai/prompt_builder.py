from reportgen.planning.layout_policy import ALLOWED_LAYOUTS, MANDATORY_LAYOUTS
from reportgen.schemas.bundle import NormalizedInputBundle

SYSTEM_PROMPT = """You are generating a finance-grade slide plan for an equity research report.
Return valid JSON only.
Choose layouts only from the allowed registry.
Do not invent numbers or chart data.
Use deterministic source references for metrics, charts, and tables.
Include the mandatory disclaimer slide.
"""


def build_slide_planner_prompt(bundle: NormalizedInputBundle) -> str:
    sections = "\n".join(
        f"- {section.heading}: {section.body}" for section in bundle.report_sections
    )
    metrics = "\n".join(
        f"- {key}: {value}" for key, value in bundle.headline_metrics.items()
    )
    references = "\n".join(
        [
            f"- metric source keys: {', '.join(bundle.data_references.metric_source_keys)}",
            f"- series source keys: {', '.join(bundle.data_references.series_source_keys)}",
            f"- period labels source: period_labels ({', '.join(bundle.data_references.period_labels)})",
        ]
    )
    layouts = ", ".join(ALLOWED_LAYOUTS)
    mandatory = ", ".join(MANDATORY_LAYOUTS)

    return f"""Company: {bundle.source.company.name} ({bundle.normalized_ticker})
Sector: {bundle.source.company.sector}
Rating: {bundle.normalized_rating}
Analyst: {bundle.source.metadata.analyst}

Allowed layouts: {layouts}
Mandatory layouts: {mandatory}
Slide count range: 5 to 8

Headline metrics:
{metrics}

Approved report sections:
{sections}

Deterministic source references:
{references}

Return a JSON object with schema_version, company_ticker, generated_at, and slides.
Each slide must include slide_id, layout, title, optional subtitle, optional rationale, and blocks.
"""
