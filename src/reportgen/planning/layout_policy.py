from reportgen.rendering.layout_registry import LAYOUT_REGISTRY
from reportgen.schemas.slides import SlideLayout

ALLOWED_LAYOUTS: tuple[SlideLayout, ...] = tuple(LAYOUT_REGISTRY.keys())

MANDATORY_LAYOUTS: tuple[SlideLayout, ...] = ("disclaimer", "analyst_certification")
