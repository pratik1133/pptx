from __future__ import annotations

from dataclasses import dataclass, field

from reportgen.schemas.blocks import BulletBlock, MetricsBlock, TextBlock
from reportgen.schemas.report import ReportSpec


@dataclass
class QaResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_report_content(report_spec: ReportSpec) -> QaResult:
    result = QaResult()
    for slide in report_spec.slides:
        if len(slide.title) > 90:
            result.warnings.append(f"Slide {slide.slide_id} title is long and may overflow.")
        if slide.subtitle and len(slide.subtitle) > 140:
            result.warnings.append(f"Slide {slide.slide_id} subtitle is long and may overflow.")

        for block in slide.blocks:
            if isinstance(block, TextBlock) and len(block.content) > 3000:
                result.warnings.append(f"Slide {slide.slide_id} text block '{block.key}' is very long.")
            if isinstance(block, BulletBlock):
                if len(block.items) > 8:
                    result.warnings.append(f"Slide {slide.slide_id} bullet block '{block.key}' is dense.")
                for item in block.items:
                    if len(item) > 250:
                        result.warnings.append(
                            f"Slide {slide.slide_id} bullet item in '{block.key}' is long and may wrap heavily."
                        )
            if isinstance(block, MetricsBlock) and len(block.items) > 8:
                result.warnings.append(f"Slide {slide.slide_id} metrics block '{block.key}' is dense.")

    return result
