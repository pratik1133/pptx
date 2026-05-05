from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString

HEX_PATTERN = r"^#[0-9A-Fa-f]{6}$"


class FontToken(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: NonEmptyString
    size_pt: int = Field(gt=0)
    bold: bool = False
    color_hex: str = Field(pattern=HEX_PATTERN)


class ThemePalette(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: str = Field(pattern=HEX_PATTERN)
    secondary: str = Field(pattern=HEX_PATTERN)
    accent: str = Field(pattern=HEX_PATTERN)
    soft: str = Field(default="#FFE5B4", pattern=HEX_PATTERN)
    text: str = Field(pattern=HEX_PATTERN)
    text_on_primary: str = Field(default="#FFFFFF", pattern=HEX_PATTERN)
    muted_text: str = Field(pattern=HEX_PATTERN)
    background: str = Field(pattern=HEX_PATTERN)
    divider: str = Field(default="#3A5BA0", pattern=HEX_PATTERN)
    light_grey: str = Field(default="#F4F6F9", pattern=HEX_PATTERN)
    green: str = Field(default="#1A7A4A", pattern=HEX_PATTERN)
    red: str = Field(default="#B91C1C", pattern=HEX_PATTERN)
    teal: str = Field(default="#0E7490", pattern=HEX_PATTERN)
    section_bg: str = Field(default="#E8EEF8", pattern=HEX_PATTERN)
    highlight_row: str = Field(default="#FFF3E0", pattern=HEX_PATTERN)


class RatingColors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    BUY: str = Field(pattern=HEX_PATTERN)
    HOLD: str = Field(pattern=HEX_PATTERN)
    SELL: str = Field(pattern=HEX_PATTERN)
    REDUCE: str = Field(pattern=HEX_PATTERN)


class CanvasSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aspect_ratio: NonEmptyString = "16:9"
    width_in: float = Field(default=13.333, gt=0)
    height_in: float = Field(default=7.5, gt=0)


class ShellSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    header_height_in: float = Field(default=0.45, gt=0)
    footer_height_in: float = Field(default=0.35, gt=0)
    side_margin_in: float = Field(default=0.5, ge=0)
    title_top_in: float = Field(default=0.6, ge=0)
    title_height_in: float = Field(default=0.55, gt=0)
    divider_thickness_pt: float = Field(default=1.5, gt=0)
    logo_height_in: float = Field(default=0.32, gt=0)


class BrandTheme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    firm_name: NonEmptyString = "Tikona Capital"
    firm_tagline: str = "Institutional Equity Research"
    footer_line: str = ""
    logo_path: str = ""
    canvas: CanvasSpec = Field(default_factory=CanvasSpec)
    palette: ThemePalette
    rating_colors: RatingColors
    chart_palette: list[str] = Field(default_factory=list)
    title_font: FontToken
    subtitle_font: FontToken
    body_font: FontToken
    metric_font: FontToken
    footer_font: FontToken
    header_font: FontToken
    rating_badge_font: FontToken
    tagline_font: FontToken = Field(
        default_factory=lambda: FontToken(family="Calibri", size_pt=14, bold=True, color_hex="#1F4690")
    )
    section_number_font: FontToken = Field(
        default_factory=lambda: FontToken(family="Calibri", size_pt=10, bold=True, color_hex="#FFA500")
    )
    shell: ShellSpec = Field(default_factory=ShellSpec)


DEFAULT_THEME = BrandTheme(
    name="tikona_capital_default",
    firm_name="Tikona Capital",
    footer_line="Tikona Capital | SEBI Registration No.: INH000069807",
    logo_path="assets/branding/logo.png",
    firm_tagline="Institutional Equity Research",
    palette=ThemePalette(
        primary="#1F4690",
        secondary="#3A5BA0",
        accent="#FFA500",
        soft="#FFE5B4",
        text="#111111",
        text_on_primary="#FFFFFF",
        muted_text="#5A6573",
        background="#FFFFFF",
        divider="#3A5BA0",
        light_grey="#F4F6F9",
        green="#1A7A4A",
        red="#B91C1C",
        teal="#0E7490",
        section_bg="#E8EEF8",
        highlight_row="#FFF3E0",
    ),
    rating_colors=RatingColors(
        BUY="#1B7F3A",
        HOLD="#FFA500",
        SELL="#B3261E",
        REDUCE="#D97706",
    ),
    chart_palette=["#1F4690", "#FFA500", "#3A5BA0", "#1B7F3A", "#B3261E", "#FFE5B4"],
    title_font=FontToken(family="Calibri", size_pt=26, bold=True, color_hex="#1F4690"),
    subtitle_font=FontToken(family="Calibri", size_pt=13, bold=False, color_hex="#5A6573"),
    body_font=FontToken(family="Calibri", size_pt=14, bold=False, color_hex="#111111"),
    metric_font=FontToken(family="Calibri", size_pt=14, bold=True, color_hex="#1F4690"),
    footer_font=FontToken(family="Calibri", size_pt=9, bold=False, color_hex="#FFFFFF"),
    header_font=FontToken(family="Calibri", size_pt=11, bold=True, color_hex="#FFFFFF"),
    rating_badge_font=FontToken(family="Calibri", size_pt=12, bold=True, color_hex="#FFFFFF"),
)
