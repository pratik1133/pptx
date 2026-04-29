import pytest

from reportgen.export.pdf_converter import PdfConversionUnavailableError, resolve_pdf_converter


def test_pdf_converter_resolution_is_explicit() -> None:
    try:
        converter = resolve_pdf_converter()
    except PdfConversionUnavailableError as exc:
        assert "backend" in str(exc).lower() or "configure" in str(exc).lower()
    else:
        assert converter is not None
