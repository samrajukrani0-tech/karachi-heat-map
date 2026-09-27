"""P5-02: the service worker precaches every file the site serves, and nothing else."""

import json
import re


def _shell(root):
    text = (root / "site" / "sw.js").read_text(encoding="utf-8")
    block = re.search(r"var SHELL = \[(.*?)\];", text, re.S).group(1)
    return set(re.findall(r'"([^"]+)"', block))


def test_every_site_file_is_precached(root):
    site = root / "site"
    served = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    served -= {"sw.js"}                      # the worker is not cached by itself
    # The briefs' PDF/PNG downloads are cached on first open, not precached: twelve
    # pairs would cost a phone ~8 MB on its first visit (see the note in sw.js). The
    # brief pages themselves ARE precached, so every brief still opens offline.
    served -= {f for f in served if f.startswith("briefs/") and f.endswith((".pdf", ".png"))}
    missing = served - _shell(root)
    assert not missing, f"not precached, so broken offline: {sorted(missing)}"


def test_the_shell_lists_no_file_that_does_not_exist(root):
    """cache.addAll fails the whole install if any one URL 404s."""
    site = root / "site"
    ghosts = {p for p in _shell(root) - {"./"} if not (site / p).is_file()}
    assert not ghosts, f"sw.js precaches missing files: {sorted(ghosts)}"


def test_basemap_tiles_are_not_cached(root):
    """Esri's tiles are requested at view time and never stored (data/SOURCES.md)."""
    text = (root / "site" / "sw.js").read_text(encoding="utf-8")
    assert "arcgisonline" not in text
    assert "self.location.origin" in text


def test_the_road_outline_is_small_osm_data(root):
    doc = json.loads((root / "site" / "data" / "roads.geojson").read_text("utf-8"))
    size_kb = (root / "site" / "data" / "roads.geojson").stat().st_size / 1024
    assert size_kb < 150
    assert "ODbL" in doc["metadata"]["licence"]
    assert len(doc["features"]) > 50
    for f in doc["features"]:
        assert f["geometry"]["type"] == "LineString"
        for lon, lat in f["geometry"]["coordinates"]:
            assert 67.1 < lon < 67.3 and 24.78 < lat < 24.9
