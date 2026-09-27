"""P5-03: the NGO one-pager draft and its PDF."""

import re
import runpy
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
op = runpy.run_path(str(ROOT / "scripts" / "one_pager.py"))


def _md(root):
    return (root / "docs" / "pitch" / "one-pager.md").read_text(encoding="utf-8")


def test_it_covers_the_four_things_it_must(root):
    text = _md(root)
    for heading in ("## What it is", "## What it is not",
                    "## How to read the map in two minutes", "## What would help most"):
        assert heading in text, heading


def test_it_is_marked_as_a_draft_for_samraj(root):
    text = _md(root)
    assert "DRAFT for Samraj to edit" in text
    assert "fill in once one has said yes" in text      # not yet tailored (P5-03b)


def test_it_leaves_a_line_for_a_handwritten_contact_and_shows_none(root):
    """D11c: no contact is printed; a blank is left to write one by hand."""
    text = _md(root)
    assert "Contact (written by hand):" in text and 'class="blank"' in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.\w+", text), "an email address is printed"
    assert not re.search(r"\+?\d[\d\s-]{8,}\d", text), "a phone number is printed"


def test_it_states_the_limits_and_the_official_sources(root):
    low = " ".join(_md(root).lower().split())      # Markdown wraps lines anywhere
    for needed in ("not an official warning system", "pakistan meteorological department",
                   "pdma sindh", "census", "power cuts", "placeholders",
                   "built with claude code as a coding assistant"):
        assert needed in low, needed
    for banned in ("dangerous", "unsafe", "nixor"):
        assert banned not in low, banned


def test_the_pdf_is_one_a4_page_and_current(root):
    pdf = root / "docs" / "pitch" / "one-pager.pdf"
    reader = PdfReader(pdf)
    assert len(reader.pages) == 1
    assert abs(float(reader.pages[0].mediabox.height) - 841.9) < 2
    assert pdf.stat().st_size < 1_000_000
    committed = (root / "docs" / "pitch" / "one-pager.html").read_text(encoding="utf-8")
    assert committed == op["build_html"](), "re-run scripts/one_pager.py"
    text = reader.pages[0].extract_text()
    assert "What would help most" in text and "Contact" in text
