"""Print progress from features.json.

A feature is RESOLVED when it passes, or when Samraj has approved dropping it
(a non-empty `dropped` reason, recorded in DECISIONS.md).

Usage:
    uv run python scripts/features.py
    uv run python scripts/features.py --phase 1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features.json"


def load() -> list[dict]:
    with FEATURES.open(encoding="utf-8") as fh:
        return json.load(fh)["features"]


def is_resolved(feature: dict) -> bool:
    return bool(feature["passes"]) or bool(feature["dropped"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Progress from features.json")
    parser.add_argument("--phase", type=int, default=None, help="only this phase")
    args = parser.parse_args()

    features = load()
    phases = sorted({f["phase"] for f in features})
    if args.phase is not None:
        phases = [p for p in phases if p == args.phase]
        if not phases:
            print(f"No features in phase {args.phase}")
            return 1

    unresolved: list[dict] = []
    for phase in phases:
        in_phase = [f for f in features if f["phase"] == phase]
        resolved = [f for f in in_phase if is_resolved(f)]
        blocked = [f for f in in_phase if not is_resolved(f) and f["blocked_on"]]
        print(f"Phase {phase}: {len(resolved)} of {len(in_phase)} resolved, {len(blocked)} blocked")
        unresolved.extend(f for f in in_phase if not is_resolved(f))

    if args.phase is None:
        total = len(features)
        done = sum(1 for f in features if is_resolved(f))
        print(f"Overall: {done} of {total} resolved")

    if unresolved:
        print("\nUnresolved:")
        for f in unresolved:
            blocker = f["blocked_on"] or "-"
            deps = [d for d in f["depends_on"]
                    if not is_resolved(next(x for x in features if x["id"] == d))]
            waiting = f"  waiting on {', '.join(deps)}" if deps else ""
            print(f"  {f['id']} {f['title']}")
            print(f"      blocker: {blocker}{waiting}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
