"""Quality gates for the Karachi heat priority map.

Runs every check in the order set out in PROMPT.md section 10 and ends with
exactly one summary line:

    CHECK: PASS (n checks)
    CHECK: FAIL (k of n failed: names)

Checks that cannot run yet report NOT APPLICABLE with the feature that will
enable them. A NOT APPLICABLE check is never counted as a pass, and this
mechanism must never be used to hide a failure (PROMPT.md section 2.2).

Usage:
    uv run python scripts/check.py --quick
    uv run python scripts/check.py
    uv run python scripts/check.py --lighthouse
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PASS, FAIL, NA = "PASS", "FAIL", "N/A"
MAX_PROCESSED_BYTES = 5 * 1024 * 1024  # PROMPT.md section 4: data/processed under 5 MB


def run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).strip()
    tail = "\n".join(out.splitlines()[-12:])
    return proc.returncode == 0, tail


def check_ruff() -> tuple[str, str]:
    ok, out = run(["ruff", "check", "."])
    return (PASS, "no lint errors") if ok else (FAIL, out)


def check_pytest() -> tuple[str, str]:
    cmd = ["pytest"]
    if os.environ.get("CI"):
        # Tests marked `raw` need the local download cache, which CI does not have.
        cmd += ["-m", "not raw"]
    ok, out = run(cmd)
    summary = out.splitlines()[-1] if out else "no output"
    return (PASS, summary) if ok else (FAIL, out)


def check_data() -> tuple[str, str]:
    """Schemas, value ranges, missing-value policy and the size budget."""
    import yaml
    from jsonschema import Draft202012Validator

    problems: list[str] = []

    schema = json.loads((ROOT / "tests" / "features.schema.json").read_text(encoding="utf-8"))
    doc = json.loads((ROOT / "features.json").read_text(encoding="utf-8"))
    for err in Draft202012Validator(schema).iter_errors(doc):
        problems.append(f"features.json: {'/'.join(str(p) for p in err.path)}: {err.message}")

    ids = [f["id"] for f in doc["features"]]
    if len(ids) != len(set(ids)):
        problems.append("features.json: duplicate feature ids")
    known = set(ids)
    for feature in doc["features"]:
        for dep in feature["depends_on"]:
            if dep not in known:
                problems.append(f"features.json: {feature['id']} depends on unknown {dep}")

    configs = ("area", "indicators", "weights", "model", "allocation", "heat",
               "population", "landcover", "access")
    for name in configs:
        path = ROOT / "config" / f"{name}.yaml"
        if not path.exists():
            problems.append(f"config/{name}.yaml is missing")
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:  # pragma: no cover - configuration error
            problems.append(f"config/{name}.yaml: {exc}")

    weights = yaml.safe_load((ROOT / "config" / "weights.yaml").read_text(encoding="utf-8"))
    for group in ("dimensions", "vulnerability", "hazard", "exposure"):
        total = sum(weights[group].values())
        if abs(total - 1.0) > 1e-9:
            problems.append(f"config/weights.yaml: {group} weights sum to {total}, not 1")

    processed = ROOT / "data" / "processed"
    size = sum(p.stat().st_size for p in processed.rglob("*") if p.is_file())
    if size > MAX_PROCESSED_BYTES:
        problems.append(f"data/processed is {size / 1e6:.1f} MB, over the 5 MB budget")

    if problems:
        return FAIL, "\n".join(problems)
    return PASS, (f"features.json + {len(configs)} configs valid; "
                  f"data/processed {size / 1e6:.2f} MB")


def check_site_data() -> tuple[str, str]:
    """Every cell the site serves must exist in the processed data with matching values."""
    path = ROOT / "site" / "data" / "cells.geojson"
    if not path.exists():
        return NA, "site/data/cells.geojson not built yet - run scripts/build_site_data.py"
    import pandas as pd

    doc = json.loads(path.read_text(encoding="utf-8"))
    scores = pd.read_csv(ROOT / "data" / "processed" / "scores.csv").set_index("h3")
    indicators = pd.read_parquet(
        ROOT / "data" / "processed" / "indicators.parquet").set_index("h3")

    required = {"h3", "rank", "priority", "hazard", "exposure", "vulnerability",
                "reasons", "stability", "lst", "people", "dist_health"}
    problems: list[str] = []
    site_cells = set()
    for feature in doc["features"]:
        props = feature["properties"]
        missing = required - set(props)
        if missing:
            problems.append(f"{props.get('h3', '?')}: missing fields {sorted(missing)}")
            continue
        cell = props["h3"]
        site_cells.add(cell)
        if cell not in scores.index:
            problems.append(f"{cell}: served by the site but absent from scores.csv")
            continue
        if abs(float(props["priority"]) - float(scores.loc[cell, "priority"])) > 5e-4:
            problems.append(f"{cell}: priority {props['priority']} != processed value")
        if int(props["rank"]) != int(scores.loc[cell, "rank"]):
            problems.append(f"{cell}: rank {props['rank']} != processed value")
        if abs(float(props["lst"]) - float(indicators.loc[cell, "lst_mean_c"])) > 0.05:
            problems.append(f"{cell}: lst {props['lst']} != processed value")

    if site_cells != set(scores.index):
        problems.append(f"the site serves {len(site_cells)} cells, the model has "
                        f"{len(scores)}")
    meta = doc.get("metadata", {})
    for flag in ("weights_provisional", "model_incomplete"):
        if flag not in meta:
            problems.append(f"metadata is missing {flag}; the site must not present "
                            f"provisional results as final")

    size_kb = path.stat().st_size / 1024
    if size_kb > 1024:
        problems.append(f"cells.geojson is {size_kb:.0f} kB, over the 1 MB budget")
    if problems:
        return FAIL, "\n".join(problems[:10])
    return PASS, (f"{len(site_cells)} cells match the processed data; "
                  f"{size_kb:.0f} kB")


def _node_tooling_ready() -> bool:
    return (ROOT / "node_modules").exists()


def check_html_validate() -> tuple[str, str]:
    if not _node_tooling_ready():
        return NA, "node tooling not installed - enabled by P3-02"
    ok, out = run(["npx", "html-validate", "site"])
    return (PASS, "html-validate clean") if ok else (FAIL, out)


def check_playwright() -> tuple[str, str]:
    if not _node_tooling_ready():
        return NA, "node tooling not installed - enabled by P3-02"
    ok, out = run(["npx", "playwright", "test"])
    return (PASS, "playwright suite passed") if ok else (FAIL, out)


def check_axe() -> tuple[str, str]:
    if not _node_tooling_ready():
        return NA, "node tooling not installed - enabled by P3-04"
    listed, _ = run(["npx", "playwright", "test", "--grep", "axe", "--list"])
    if not listed:
        return NA, "no axe-tagged end-to-end test yet - enabled by P3-04"
    ok, out = run(["npx", "playwright", "test", "--grep", "axe"])
    return (PASS, "no serious or critical violations") if ok else (FAIL, out)


def check_lighthouse() -> tuple[str, str]:
    """Thresholds from PROMPT.md section 10, enforced by scripts/lighthouse.mjs."""
    if not _node_tooling_ready():
        return NA, "node tooling not installed - enabled by P3-08"
    url = os.environ.get("SITE_URL")
    command = ["node", "scripts/lighthouse.mjs"] + ([url + "/index.html"] if url else [])
    ok, out = run(command)
    summary = out.splitlines()[-1] if out else "no output"
    return (PASS, summary) if ok else (FAIL, out)


CHECKS = [
    ("ruff", check_ruff),
    ("pytest", check_pytest),
    ("data validation", check_data),
    ("site-data consistency", check_site_data),
    ("html-validate", check_html_validate),
    ("playwright", check_playwright),
    ("axe-core", check_axe),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the quality gates")
    parser.add_argument("--quick", action="store_true", help="skip Lighthouse")
    parser.add_argument("--lighthouse", action="store_true", help="also run Lighthouse")
    args = parser.parse_args()

    checks = list(CHECKS)
    if args.lighthouse and not args.quick:
        checks.append(("lighthouse", check_lighthouse))

    failed: list[str] = []
    skipped: list[str] = []
    ran = 0

    for name, fn in checks:
        try:
            status, detail = fn()
        except Exception as exc:  # a broken check is a failing check
            status, detail = FAIL, f"{type(exc).__name__}: {exc}"
        if status == NA:
            skipped.append(name)
            print(f"[{NA} ] {name}: {detail}")
            continue
        ran += 1
        print(f"[{status}] {name}: {detail}")
        if status == FAIL:
            failed.append(name)

    if skipped:
        print(f"Not applicable yet ({len(skipped)}): {', '.join(skipped)}")

    if failed:
        print(f"CHECK: FAIL ({len(failed)} of {ran} failed: {', '.join(failed)})")
        return 1
    print(f"CHECK: PASS ({ran} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
