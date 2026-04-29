from __future__ import annotations

from typing import Any


class PptxRuntime:
    def __init__(self) -> None:
        try:
            from pptx import Presentation  # type: ignore
            from pptx.dml.color import RGBColor  # type: ignore
            from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE  # type: ignore
            from pptx.enum.text import PP_ALIGN  # type: ignore
            from pptx.util import Inches, Pt  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "python-pptx is not installed. Install project dependencies before rendering PPTX files."
            ) from exc

        self.Presentation = Presentation
        self.RGBColor = RGBColor
        self.MSO_AUTO_SHAPE_TYPE = MSO_AUTO_SHAPE_TYPE
        self.PP_ALIGN = PP_ALIGN
        self.Inches = Inches
        self.Pt = Pt


def load_pptx_runtime() -> PptxRuntime:
    return PptxRuntime()
