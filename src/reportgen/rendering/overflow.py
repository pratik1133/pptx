from __future__ import annotations

from dataclasses import dataclass
from math import floor

from reportgen.rendering.geometry import Box


def _capacity(box: Box, font_size_pt: int) -> tuple[int, int]:
    lines = max(1, floor((box.height * 72) / (font_size_pt * 1.5)))
    chars_per_line = max(12, floor((box.width * 72) / (font_size_pt * 0.62)))
    return lines, chars_per_line


def fit_text_to_box(text: str, box: Box, font_size_pt: int, *, max_lines: int | None = None) -> str:
    lines, chars_per_line = _capacity(box, font_size_pt)
    estimated_lines = max_lines or lines
    max_chars = estimated_lines * chars_per_line
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max(0, max_chars - 3)].rstrip() + "..."


@dataclass
class AutoshrinkResult:
    text: str
    font_size_pt: int


def autoshrink_text(text: str, box: Box, base_font_size_pt: int, *, min_font_pt: int = 9) -> AutoshrinkResult:
    """Try the base font; if the text overflows, step down to fit before truncating."""
    compact = " ".join(text.split())
    for size in range(base_font_size_pt, min_font_pt - 1, -1):
        lines, chars_per_line = _capacity(box, size)
        if len(compact) <= lines * chars_per_line:
            return AutoshrinkResult(text=compact, font_size_pt=size)
    return AutoshrinkResult(text=fit_text_to_box(text, box, min_font_pt), font_size_pt=min_font_pt)


def fit_bullets_to_box(items: list[str], box: Box, font_size_pt: int) -> list[str]:
    max_items = max(1, floor((box.height * 72) / (font_size_pt * 1.9)))
    fitted: list[str] = []
    for item in items[:max_items]:
        fitted.append(fit_text_to_box(item, box, font_size_pt, max_lines=2))
    return fitted


def split_bullets_for_continuation(items: list[str], box: Box, font_size_pt: int) -> tuple[list[str], list[str]]:
    """Return (fits_on_this_slide, remaining_for_continuation_slide)."""
    max_items = max(1, floor((box.height * 72) / (font_size_pt * 1.9)))
    if len(items) <= max_items:
        return list(items), []
    return list(items[:max_items]), list(items[max_items:])


def text_char_budget(box: Box, font_size_pt: int) -> int:
    """Approximate visible character capacity for a text block at the given size."""
    lines, chars_per_line = _capacity(box, font_size_pt)
    return lines * chars_per_line


def bullet_capacity(box: Box, font_size_pt: int, *, chars_per_bullet: int = 140) -> tuple[int, int]:
    """Return (max_bullets, target_chars_per_bullet) the box can comfortably hold."""
    lines, chars_per_line = _capacity(box, font_size_pt)
    # Each bullet uses ~1.6 lines on average (text + spacing).
    max_bullets = max(1, int(lines / 1.6))
    return max_bullets, chars_per_bullet


def cap_table_rows(rows: list[dict], max_rows: int) -> tuple[list[dict], int]:
    """Return (capped_rows, hidden_count). Caller can render a continuation row if hidden_count > 0."""
    if len(rows) <= max_rows:
        return rows, 0
    return rows[:max_rows], len(rows) - max_rows
