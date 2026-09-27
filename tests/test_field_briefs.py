"""P5-01: one A4 field brief per named locality, as HTML, PDF and PNG, each under 1 MB."""

import json
import re
import runpy
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from pipeline import localities

fb = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "field_briefs.py"))


@pytest.fixture(scope="module")
def index(root):
    return json.loads((root / "site" / "briefs" / "index.json").read_text("utf-8"))


@pytest.fixture(scope="module")
def cells(root):
    doc = json.loads((root / "site" / "data" / "cells.geojson").read_text("utf-8"))
    return {f["properties"]["h3"]: f["properties"] for f in doc["features"]}, doc["metadata"]


def test_one_brief_per_named_locality(root, index):
    names = {r["name_en"] for r in localities.read()}
    assert len(names) == 12
    assert {b["name_en"] for b in index["briefs"]} == names


def test_localities_are_the_ones_on_the_expert_form(root):
    """The field briefs and the P2-05 ranking form must name the same places."""
    report = json.loads((root / "data" / "processed" / "validation.json").read_text("utf-8"))
    assert set(report["expert_ranking"]["localities"]) == {r["name_en"] for r in localities.read()}


@pytest.mark.parametrize("ext", ["pdf", "png"])
def test_every_file_exists_and_sends_on_whatsapp(root, index, ext):
    for b in index["briefs"]:
        path = root / "site" / "briefs" / f"{b['slug']}.{ext}"
        assert path.exists(), path.name
        assert path.stat().st_size < 1_000_000, f"{path.name} is over 1 MB"


def test_each_pdf_is_one_a4_page(root, index):
    for b in index["briefs"]:
        reader = PdfReader(root / "site" / "briefs" / f"{b['slug']}.pdf")
        assert len(reader.pages) == 1, b["slug"]
        box = reader.pages[0].mediabox
        # A4 is 595 x 842 pt
        assert abs(float(box.width) - 595.3) < 2 and abs(float(box.height) - 841.9) < 2


def test_each_png_has_a4_proportions(root, index):
    for b in index["briefs"]:
        with Image.open(root / "site" / "briefs" / f"{b['slug']}.png") as im:
            w, h = im.size
        assert abs(h / w - 297 / 210) < 0.01, b["slug"]


def test_briefs_match_the_live_map_data(root, index, cells):
    """A brief cannot say something the map does not: rebuild and compare."""
    by_cell, meta = cells
    for b in index["briefs"]:
        text = (root / "site" / "briefs" / f"{b['slug']}.html").read_text("utf-8")
        ranks = [int(r) for r in re.findall(r'<tr><td class="n">(\d+)</td>', text)]
        assert ranks == sorted(by_cell[c]["rank"] for c in b["cells"])
        assert b["best_rank"] == min(ranks)
        assert f"of {meta['distinguishable_ranks']}" in text


def test_committed_briefs_are_current(root, tmp_path, index):
    written = fb["build"](tmp_path, index["generated"])
    for w in written:
        fresh = (tmp_path / f"{w['slug']}.html").read_text("utf-8")
        committed = (root / "site" / "briefs" / f"{w['slug']}.html").read_text("utf-8")
        assert fresh == committed, f"{w['slug']}.html is stale: run scripts/field_briefs.py"


def test_briefs_carry_the_caveats_and_never_judge_a_place(root, index, cells):
    _, meta = cells
    for b in index["briefs"]:
        text = (root / "site" / "briefs" / f"{b['slug']}.html").read_text("utf-8")
        low = text.lower()
        for needed in ("census", "not the air", "power cuts", "never a verdict",
                       "not an official warning system", "built with claude code"):
            assert needed in low, (b["slug"], needed)
        if meta["weights_provisional"] or meta["model_incomplete"]:
            assert "provisional" in low
        for banned in ("dangerous", "unsafe", " bad "):
            assert banned not in low, (b["slug"], banned)


def test_the_briefs_page_links_every_brief(root, index):
    page = (root / "site" / "briefs.html").read_text("utf-8")
    for b in index["briefs"]:
        for ext in ("html", "pdf", "png"):
            assert f'href="briefs/{b["slug"]}.{ext}"' in page
