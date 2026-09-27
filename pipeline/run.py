"""Rebuild everything, in dependency order, from the download cache.

    uv run python -m pipeline.run --all          # every step
    uv run python -m pipeline.run --from score   # a step and everything after it
    uv run python -m pipeline.run --list         # the steps, in order

Each step is the module's own ``main()``, exactly as it runs on its own. With
data/raw/ populated nothing is downloaded; on a fresh clone the first run fetches
and caches each source once (data/raw/manifest.json records every byte).

Not rebuilt here, on purpose: config/weights.yaml, which only Samraj's AHP session
writes (``uv run python -m pipeline.ahp``), and docs/model-report.md, which is written
by hand from these outputs and checked against them by tests/test_model_report.py.
"""

from __future__ import annotations

import argparse
import importlib
import runpy
import sys
import time

from pipeline.config import ROOT

STEPS: list[tuple[str, str]] = [
    ("boundary", "P1-01 pilot boundary"),
    ("grid", "P1-02 H3 grid"),
    ("lst", "P1-04a hot-season LST composite"),
    ("heat", "P1-04b heat per cell"),
    ("population", "P1-06 people per cell"),
    ("demographics", "P1-07 age groups"),
    ("landcover", "P1-08 built-up and green cover"),
    ("access", "P1-09a distance to health facility"),
    ("indicators", "P1-11 indicator table"),
    ("normalise", "P2-01 normalisation"),
    ("score", "P2-03 scores"),
    ("sensitivity", "P2-04 sensitivity"),
    ("validate", "P2-05 validation pack"),
    ("localities", "named OSM places, for the form and the briefs"),
    ("scenarios", "P4-02a allocation scenarios"),
    ("roads", "P5-02 offline road outline"),
    ("site", "site data files"),
    ("briefs", "P5-01 field briefs (needs node: npm ci)"),
    ("expert", "P6-01 expert agreement (does nothing until real rankings exist)"),
]


def run_step(name: str) -> None:
    scripts = {"site": "build_site_data.py", "briefs": "field_briefs.py"}
    if name in scripts:
        # These scripts end in `raise SystemExit(main())`, which would end this run too.
        try:
            runpy.run_path(str(ROOT / "scripts" / scripts[name]), run_name="__main__")
        except SystemExit as done:
            if done.code:
                raise SystemExit(f"step {name} failed: {done.code}") from None
        return
    module = importlib.import_module(f"pipeline.{name}")
    saved, sys.argv = sys.argv, [f"pipeline.{name}"]   # steps parse their own argv
    try:
        code = module.main()
    finally:
        sys.argv = saved
    if code:
        raise SystemExit(f"step {name} failed with exit code {code}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the pipeline from the cache")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="run every step")
    group.add_argument("--from", dest="start", choices=[s for s, _ in STEPS],
                       help="run this step and every step after it")
    group.add_argument("--list", action="store_true", help="print the steps")
    args = parser.parse_args()

    if args.list:
        for i, (name, what) in enumerate(STEPS, 1):
            print(f"{i:2d}. {name:<13} {what}")
        return 0
    names = [s for s, _ in STEPS]
    todo = names if args.all else names[names.index(args.start):]
    for name in todo:
        what = dict(STEPS)[name]
        print(f"\n== {name}: {what}", flush=True)
        started = time.perf_counter()
        run_step(name)
        print(f"   done in {time.perf_counter() - started:.1f}s", flush=True)
    print(f"\nRebuilt {len(todo)} step(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
