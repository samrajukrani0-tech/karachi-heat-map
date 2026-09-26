"""centres.csv is the only source for relief centres, and D13 constrains its shape."""

import csv
from pathlib import Path

EXPECTED = ["name", "org", "role", "can_hold_stock", "lat", "lon",
            "source", "verified_by", "verified_on", "notes"]
ROLES = {"ambulance_standby", "distribution_point", "clinic", "morgue", "office", "other"}
STOCK = {"yes", "no", "unknown"}


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_centres_header(root):
    with (root / "data" / "manual" / "centres.csv").open(encoding="utf-8") as fh:
        assert next(csv.reader(fh)) == EXPECTED


def test_every_centre_is_verified(root):
    """PROMPT.md section 6: unverified centres are excluded, not guessed."""
    for row in _read(root / "data" / "manual" / "centres.csv"):
        assert row["verified_by"].strip(), f"{row['name']} has no verifier"
        assert row["verified_on"].strip(), f"{row['name']} has no verification date"
        assert row["source"].strip(), f"{row['name']} has no source"


def test_roles_and_stock_flags_are_valid(root):
    for row in _read(root / "data" / "manual" / "centres.csv"):
        assert row["role"] in ROLES, f"{row['name']}: bad role {row['role']!r}"
        assert row["can_hold_stock"] in STOCK, f"{row['name']}: bad can_hold_stock"


def test_centres_are_inside_the_karachi_bounding_box(root):
    for row in _read(root / "data" / "manual" / "centres.csv"):
        lat, lon = float(row["lat"]), float(row["lon"])
        assert 24.6 <= lat <= 25.2, f"{row['name']}: lat {lat} outside Karachi"
        assert 66.8 <= lon <= 67.6, f"{row['name']}: lon {lon} outside Karachi"


def test_candidates_never_leak_into_centres(root):
    """D13/PROMPT.md section 6: the candidate list is research, not data."""
    candidates = {r["name"] for r in _read(root / "data" / "manual" / "centre_candidates.csv")}
    centres = {r["name"] for r in _read(root / "data" / "manual" / "centres.csv")}
    leaked = candidates & centres
    for row in _read(root / "data" / "manual" / "centres.csv"):
        if row["name"] in leaked:
            assert row["verified_by"].strip(), (
                f"{row['name']} came from the candidate list without being verified"
            )


def test_candidates_are_all_marked_unverified(root):
    rows = _read(root / "data" / "manual" / "centre_candidates.csv")
    assert rows, "candidate list is empty"
    for row in rows:
        assert row["status"] == "UNVERIFIED", f"{row['name']} is not marked UNVERIFIED"
