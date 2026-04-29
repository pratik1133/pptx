from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from reportgen.schemas.blocks import BulletBlock, MetricItem, MetricsBlock, TextBlock
from reportgen.schemas.bundle import NormalizedInputBundle
from reportgen.schemas.charts import ChartBlock, ChartSeriesRef
from reportgen.schemas.planning import (
    PlanningBlock,
    PlanningBulletBlock,
    PlanningChartBlock,
    PlanningMetricsBlock,
    PlanningTableBlock,
    PlanningTextBlock,
    SlidePlan,
    SlidePlanSlide,
)
from reportgen.schemas.report import InputReferences, ReportSpec
from reportgen.schemas.slides import SlideSpec
from reportgen.schemas.tables import TableBlock, TableColumn


def _format_number(value: Decimal, currency: str | None = None, suffix: str = "") -> str:
    quantized = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if currency:
        return f"{currency} {quantized}{suffix}"
    return f"{quantized}{suffix}"


def resolve_source_value(bundle: NormalizedInputBundle, source_key: str) -> str:
    metadata = bundle.source.metadata
    company = bundle.source.company

    source_map: dict[str, str] = {
        "company.name": company.name,
        "company.ticker": company.ticker,
        "company.sector": company.sector,
        "metadata.rating": metadata.rating.upper(),
        "metadata.cmp": _format_number(metadata.cmp, metadata.currency.upper()),
        "metadata.target_price": _format_number(metadata.target_price, metadata.currency.upper()),
        "metadata.analyst": metadata.analyst,
    }

    if metadata.upside_pct is not None:
        source_map["metadata.upside_pct"] = _format_number(metadata.upside_pct, suffix="%")

    if source_key.startswith("financial_metrics."):
        metric_key = source_key.removeprefix("financial_metrics.")
        metric_value = bundle.source.financial_model.metrics[metric_key]
        if isinstance(metric_value, Decimal):
            return _format_number(metric_value)
        return str(metric_value)

    if source_key in source_map:
        return source_map[source_key]

    raise KeyError(f"Unsupported or unavailable source key: {source_key}")


def _convert_block(bundle: NormalizedInputBundle, block: PlanningBlock):
    if isinstance(block, PlanningTextBlock):
        return TextBlock(key=block.key, content=block.content)

    if isinstance(block, PlanningBulletBlock):
        return BulletBlock(key=block.key, items=block.items)

    if isinstance(block, PlanningMetricsBlock):
        return MetricsBlock(
            key=block.key,
            items=[
                MetricItem(
                    label=item.label,
                    value=resolve_source_value(bundle, item.source_key),
                    source=item.source_key,
                )
                for item in block.items
            ],
        )

    if isinstance(block, PlanningChartBlock):
        return ChartBlock(
            key=block.key,
            chart_type=block.chart_type,
            title=block.title,
            category_source=block.category_source,
            series=[
                ChartSeriesRef(
                    label=source_key.removeprefix("series."),
                    source_key=source_key,
                )
                for source_key in block.series_source_keys
            ],
        )

    if isinstance(block, PlanningTableBlock):
        return TableBlock(
            key=block.key,
            title=block.title,
            source_key=block.source_key,
            columns=[TableColumn(key=column.key, label=column.label) for column in block.columns],
        )

    raise TypeError(f"Unsupported planning block type: {type(block)!r}")


def _convert_slide(bundle: NormalizedInputBundle, slide: SlidePlanSlide) -> SlideSpec:
    return SlideSpec(
        slide_id=slide.slide_id,
        layout=slide.layout,
        title=slide.title,
        subtitle=slide.subtitle,
        blocks=[_convert_block(bundle, block) for block in slide.blocks],
    )


def build_report_spec(bundle: NormalizedInputBundle, slide_plan: SlidePlan) -> ReportSpec:
    return ReportSpec(
        report_id=uuid4(),
        run_id=uuid4(),
        company=bundle.source.company,
        metadata=bundle.source.metadata,
        inputs=InputReferences(
            financial_model_ref=str(bundle.source.financial_model_path),
            approved_content_ref=str(bundle.source.approved_report_path),
        ),
        slides=[_convert_slide(bundle, slide) for slide in slide_plan.slides],
    )
