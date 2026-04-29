from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from reportgen.config import settings


class PdfConversionUnavailableError(RuntimeError):
    """Raised when no supported PDF conversion backend is available."""


class PdfConverter:
    def convert(self, pptx_path: Path, pdf_path: Path) -> Path:
        raise NotImplementedError


class LibreOfficePdfConverter(PdfConverter):
    def __init__(self, executable: Path) -> None:
        self.executable = executable

    def convert(self, pptx_path: Path, pdf_path: Path) -> Path:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                str(self.executable),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pdf_path.parent),
                str(pptx_path),
            ],
            check=True,
        )
        generated = pdf_path.parent / f"{pptx_path.stem}.pdf"
        if not generated.exists():
            raise PdfConversionUnavailableError("LibreOffice did not produce a PDF output file.")
        if generated != pdf_path:
            generated.replace(pdf_path)
        return pdf_path


class PowerPointPdfConverter(PdfConverter):
    def convert(self, pptx_path: Path, pdf_path: Path) -> Path:
        try:
            import win32com.client  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise PdfConversionUnavailableError(
                "pywin32 is not installed, so PowerPoint COM export is unavailable."
            ) from exc

        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        app = win32com.client.Dispatch("PowerPoint.Application")
        app.Visible = 1
        presentation = app.Presentations.Open(str(pptx_path), WithWindow=False)
        try:
            presentation.SaveAs(str(pdf_path), 32)
        finally:
            presentation.Close()
            app.Quit()
        if not pdf_path.exists():
            raise PdfConversionUnavailableError("PowerPoint did not produce a PDF output file.")
        return pdf_path


def resolve_pdf_converter() -> PdfConverter:
    mode = settings.pdf_converter_mode.lower()

    if mode in {"auto", "libreoffice"}:
        executable = settings.libreoffice_path or _which("soffice")
        if executable is not None:
            return LibreOfficePdfConverter(executable)
        if mode == "libreoffice":
            raise PdfConversionUnavailableError("LibreOffice executable was not found.")

    if mode in {"auto", "powerpoint"}:
        executable = settings.powerpoint_path or _which("powerpnt")
        if executable is not None or mode == "powerpoint":
            return PowerPointPdfConverter()

    raise PdfConversionUnavailableError(
        "No supported PDF conversion backend is available. Configure LibreOffice or PowerPoint."
    )


def _which(name: str) -> Path | None:
    located = shutil.which(name)
    return Path(located) if located else None
