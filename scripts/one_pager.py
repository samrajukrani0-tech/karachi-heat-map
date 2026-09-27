"""P5-03: render docs/pitch/one-pager.md to an A4 PDF.

    uv run python scripts/one_pager.py

The Markdown is the draft Samraj edits; the PDF is regenerated from it, so the two
cannot disagree. Nothing here sends it anywhere (§2.6): Samraj hands it over himself.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
PITCH = ROOT / "docs" / "pitch"
SOURCE = PITCH / "one-pager.md"
HTML = PITCH / "one-pager.html"
PDF = PITCH / "one-pager.pdf"

CSS = """
@page { size: A4; margin: 0; }
html, body { margin: 0; background: #FFFFFF; color: #1A1C1E;
  font: 10.2pt/1.42 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }
.page { width: 210mm; min-height: 297mm; padding: 13mm 16mm 11mm; box-sizing: border-box; }
h1 { font-size: 20pt; margin: 0 0 2mm; line-height: 1.1; }
h2 { font-size: 11pt; margin: 4.2mm 0 1.2mm; color: #6C2A1F; }
p { margin: 0 0 2mm; } ul, ol { margin: 0 0 1mm; padding-left: 5mm; } li { margin: 0 0 1mm; }
p:first-of-type { border-left: 3px solid #6C2A1F; padding-left: 3mm; font-size: 9.2pt; }
.blank { display: inline-block; width: 120mm; border-bottom: 1px solid #1A1C1E;
  height: 7mm; vertical-align: bottom; }
p:last-child { font-size: 8pt; color: #58554E; border-top: 1px solid #D8D2C9;
  padding-top: 2mm; margin-top: 4mm; }
"""


def build_html() -> str:
    body = markdown.markdown(SOURCE.read_text(encoding="utf-8"))
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f"<title>Karachi Heat Priority Map, one-page introduction</title>"
            f"<style>{CSS}</style></head><body><main class=\"page\">{body}</main>"
            f"</body></html>\n")


def main() -> int:
    HTML.write_text(build_html(), encoding="utf-8")
    node = shutil.which("node")
    if not node:
        print("node is not installed, so no PDF was rendered (npm ci first)")
        return 1
    subprocess.run([node, str(ROOT / "scripts" / "render_pdf.mjs"), str(HTML), str(PDF)],
                   check=True, cwd=ROOT)
    print(f"{PDF.relative_to(ROOT)}: {PDF.stat().st_size // 1024} kB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
