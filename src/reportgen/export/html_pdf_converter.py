"""Convert HTML to PDF using Playwright (Chromium headless)."""
from __future__ import annotations

from pathlib import Path


class PlaywrightPdfConverter:
    """Renders an HTML file or string to PDF using Playwright's Chromium."""

    def convert_file(self, html_path: Path, pdf_path: Path) -> Path:
        """Convert an HTML file on disk to PDF."""
        html_content = html_path.read_text(encoding="utf-8")
        return self.convert_string(html_content, pdf_path)

    def convert_string(self, html: str, pdf_path: Path) -> Path:
        """Convert an HTML string to PDF."""
        from playwright.sync_api import sync_playwright

        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                landscape=True,
                margin={
                    "top": "8mm",
                    "bottom": "8mm",
                    "left": "8mm",
                    "right": "8mm",
                },
                print_background=True,
            )
            browser.close()

        return pdf_path
