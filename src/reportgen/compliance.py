"""Compliance asset loader. Disclaimer + analyst certification copy is read
from `assets/disclaimers/` so legal can edit the text without code changes.
"""
from __future__ import annotations

from pathlib import Path

DISCLAIMERS_ROOT = Path("assets/disclaimers")
DEFAULT_DISCLAIMER_PATH = DISCLAIMERS_ROOT / "tikona_default.md"
ANALYST_CERTIFICATION_PATH = DISCLAIMERS_ROOT / "analyst_certification.md"

_FALLBACK_DISCLAIMER = (
    "For internal research workflow validation only. "
    "Final legal disclaimer copy will be supplied from approved assets."
)
_FALLBACK_CERTIFICATION = (
    "Analyst certification copy will be supplied from approved compliance assets."
)


def _read(path: Path, fallback: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return fallback


def load_disclaimer_text() -> str:
    return _read(DEFAULT_DISCLAIMER_PATH, _FALLBACK_DISCLAIMER)


def load_analyst_certification_text() -> str:
    return _read(ANALYST_CERTIFICATION_PATH, _FALLBACK_CERTIFICATION)
