from pydantic import BaseModel, ConfigDict, Field

from reportgen.schemas.common import NonEmptyString


class FontToken(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: NonEmptyString
    size_pt: int = Field(gt=0)
    bold: bool = False
    color_hex: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class ThemePalette(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    text: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    muted_text: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    background: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class BrandTheme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyString
    palette: ThemePalette
    title_font: FontToken
    subtitle_font: FontToken
    body_font: FontToken
    metric_font: FontToken


DEFAULT_THEME = BrandTheme(
    name="research_default",
    palette=ThemePalette(
        primary="#123B5D",
        secondary="#2B6C8E",
        accent="#C58B2A",
        text="#1F2A33",
        muted_text="#667784",
        background="#F7F5F0",
    ),
    title_font=FontToken(family="Aptos Display", size_pt=24, bold=True, color_hex="#123B5D"),
    subtitle_font=FontToken(family="Aptos", size_pt=12, bold=False, color_hex="#667784"),
    body_font=FontToken(family="Aptos", size_pt=12, bold=False, color_hex="#1F2A33"),
    metric_font=FontToken(family="Aptos", size_pt=14, bold=True, color_hex="#123B5D"),
)
