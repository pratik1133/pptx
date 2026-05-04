from __future__ import annotations

import json
from pathlib import Path

from reportgen.rendering.theme import BrandTheme, DEFAULT_THEME


def load_brand_theme(path: Path | str | None) -> BrandTheme:
    if path is None:
        return DEFAULT_THEME
    json_path = Path(path)
    if not json_path.exists():
        return DEFAULT_THEME
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    return _from_json_dict(raw)


def _from_json_dict(raw: dict) -> BrandTheme:
    fonts = raw.get("fonts", {})
    payload = {
        "name": raw["name"],
        "firm_name": raw.get("firm_name", "Tikona Capital"),
        "footer_line": raw.get("footer_line", ""),
        "logo_path": raw.get("logo_path", ""),
        "canvas": raw.get("canvas", {}),
        "palette": raw["palette"],
        "rating_colors": raw["rating_colors"],
        "chart_palette": raw.get("chart_palette", []),
        "title_font": fonts["title"],
        "subtitle_font": fonts["subtitle"],
        "body_font": fonts["body"],
        "metric_font": fonts["metric"],
        "footer_font": fonts["footer"],
        "header_font": fonts["header"],
        "rating_badge_font": fonts["rating_badge"],
        "shell": raw.get("shell", {}),
    }
    return BrandTheme.model_validate(payload)
