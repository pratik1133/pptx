from pathlib import Path

from reportgen.rendering.theme_loader import load_brand_theme


THEME_PATH = Path("assets/themes/brand_theme.json")


def test_loads_tikona_theme_from_json():
    theme = load_brand_theme(THEME_PATH)
    assert theme.name == "tikona_capital"
    assert theme.firm_name == "Tikona Capital"
    assert theme.palette.primary == "#1F4690"
    assert theme.palette.accent == "#FFA500"
    assert theme.rating_colors.BUY == "#1B7F3A"
    assert theme.rating_colors.SELL == "#B3261E"
    assert theme.canvas.width_in == 13.333
    assert theme.canvas.height_in == 7.5
    assert "INH000069807" in theme.footer_line
    assert len(theme.chart_palette) >= 4


def test_falls_back_to_default_theme_when_path_missing():
    theme = load_brand_theme(Path("does-not-exist.json"))
    assert theme.name.startswith("tikona_capital")
    assert theme.palette.primary.startswith("#")
