from __future__ import annotations

from math import floor

from reportgen.rendering.geometry import Box


def fit_text_to_box(text: str, box: Box, font_size_pt: int, *, max_lines: int | None = None) -> str:
    estimated_lines = max_lines or max(1, floor((box.height * 72) / (font_size_pt * 1.5)))
    estimated_chars_per_line = max(12, floor((box.width * 72) / (font_size_pt * 0.62)))
    max_chars = estimated_lines * estimated_chars_per_line
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max(0, max_chars - 3)].rstrip() + "..."


def fit_bullets_to_box(items: list[str], box: Box, font_size_pt: int) -> list[str]:
    max_items = max(1, floor((box.height * 72) / (font_size_pt * 1.9)))
    fitted: list[str] = []
    for item in items[:max_items]:
        fitted.append(fit_text_to_box(item, box, font_size_pt, max_lines=2))
    return fitted
