"""Single source of truth for numeric formatting in the deck.

All renderers, table cells, metric cards, and chart labels must route through
this module. AI-authored prose may not embed numbers; numbers always come
through here so display rules (precision, currency, negatives, scale) stay
consistent across the whole report.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Union

NumericLike = Union[Decimal, int, float, None]

EMPTY = "—"
CURRENCY_SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}


def _to_decimal(value: NumericLike) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize(value: Decimal, precision: int) -> Decimal:
    if precision <= 0:
        q = Decimal("1")
    else:
        q = Decimal("1").scaleb(-precision)
    return value.quantize(q, rounding=ROUND_HALF_UP)


def _group_indian(integer_part: str) -> str:
    """Indian numbering: 12,34,567 (last 3 digits, then groups of 2)."""
    if integer_part.startswith("-"):
        return "-" + _group_indian(integer_part[1:])
    if len(integer_part) <= 3:
        return integer_part
    head, tail = integer_part[:-3], integer_part[-3:]
    parts = []
    while len(head) > 2:
        parts.append(head[-2:])
        head = head[:-2]
    if head:
        parts.append(head)
    return ",".join(reversed(parts)) + "," + tail


def _format_with_groups(value: Decimal, precision: int, indian: bool = True) -> str:
    quantized = _quantize(value, precision)
    sign = "-" if quantized < 0 else ""
    abs_str = str(abs(quantized))
    if "." in abs_str:
        int_part, frac_part = abs_str.split(".")
    else:
        int_part, frac_part = abs_str, ""
    grouped = _group_indian(int_part) if indian else f"{int(int_part):,}"
    if precision > 0:
        frac_part = frac_part.ljust(precision, "0")
        return f"{sign}{grouped}.{frac_part}"
    return f"{sign}{grouped}"


def format_number(value: NumericLike, *, precision: int = 1, indian: bool = True) -> str:
    dec = _to_decimal(value)
    if dec is None:
        return EMPTY
    return _format_with_groups(dec, precision, indian=indian)


def format_currency(
    value: NumericLike,
    currency: str = "INR",
    *,
    precision: int = 1,
    suffix: str = "",
) -> str:
    """Format `value` as currency. `suffix` is appended (e.g. ' Cr')."""
    dec = _to_decimal(value)
    if dec is None:
        return EMPTY
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), currency.upper() + " ")
    grouped = _format_with_groups(dec, precision, indian=True)
    sep = "" if symbol.endswith(" ") else ""
    return f"{symbol}{sep}{grouped}{suffix}"


def format_percent(value: NumericLike, *, precision: int = 1) -> str:
    dec = _to_decimal(value)
    if dec is None:
        return EMPTY
    return f"{_format_with_groups(dec, precision, indian=False)}%"


def format_multiple(value: NumericLike, *, precision: int = 1) -> str:
    """Formats a valuation multiple, e.g. 12.3x."""
    dec = _to_decimal(value)
    if dec is None:
        return EMPTY
    return f"{_format_with_groups(dec, precision, indian=False)}x"


def format_basis_points(value: NumericLike) -> str:
    dec = _to_decimal(value)
    if dec is None:
        return EMPTY
    return f"{_format_with_groups(dec, 0, indian=False)} bps"


def format_for_unit(value: NumericLike, unit: str | None) -> str:
    """Dispatch to the right formatter based on a series/ratio unit string."""
    if unit is None:
        return format_number(value)
    u = unit.strip().lower()
    if u in {"%", "pct", "percent"}:
        return format_percent(value)
    if u in {"x", "multiple"}:
        return format_multiple(value)
    if u in {"bps", "basis points"}:
        return format_basis_points(value)
    if u in {"inr", "rs", "₹"}:
        return format_currency(value, "INR")
    if u in {"inr cr", "₹ cr", "rs cr", "cr"}:
        return format_currency(value, "INR", suffix=" Cr")
    return format_number(value)
