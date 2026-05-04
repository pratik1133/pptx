"""One-time script: extract CSS from motilal_v1.html and build the Jinja2 template."""
from pathlib import Path
import re

HERE = Path(__file__).parent
ref = HERE / "base_reference.html"
html = ref.read_text(encoding="utf-8")

# Extract CSS between <style> and </style>
css_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
css = css_match.group(1).strip() if css_match else ""

# Write CSS file
(HERE / "base.css").write_text(css, encoding="utf-8")
print(f"Wrote base.css ({len(css)} chars)")
print("Done — now create the Jinja2 template manually.")
