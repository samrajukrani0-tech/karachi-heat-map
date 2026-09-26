"""P1-03: the raw download cache.

Every byte this project downloads lands in data/raw/ and gets an entry in
data/raw/manifest.json recording its URL, sha256, size, date and licence
(PROMPT.md section 6). A second run of the same fetch touches the network zero times.

Run:
    uv run python -m pipeline.fetch --verify
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pipeline.config import RAW

MANIFEST = RAW / "manifest.json"
USER_AGENT = (
    "karachi-heat-map/0.1 (A Level student project; "
    "https://github.com/samrajukrani0-tech/karachi-heat-map)"
)
CHUNK = 1 << 16
DEFAULT_TRIES = 5
BASE_BACKOFF = 4.0
MAX_BACKOFF = 120.0
# Worth retrying: the server is busy or the connection broke. Everything else -- 401,
# 403, 404, 410 -- means retrying would just repeat the same mistake politely.
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


class PermanentFetchError(RuntimeError):
    """The request will never succeed by repeating it."""


class IntegrityError(RuntimeError):
    """What arrived is not what was expected."""


def _open(request: urllib.request.Request, timeout: float):  # patched in tests
    return urllib.request.urlopen(request, timeout=timeout)


def _sleep(seconds: float) -> None:  # patched in tests
    time.sleep(seconds)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict[str, Any]:
    if not MANIFEST.exists():
        return {}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    ordered = {key: manifest[key] for key in sorted(manifest)}
    MANIFEST.write_text(json.dumps(ordered, indent=1) + "\n", encoding="utf-8")


def _key(path: Path) -> str:
    return path.relative_to(RAW).as_posix()


def record(path: Path, *, url: str, licence: str, note: str = "",
           digest: str | None = None) -> dict[str, Any]:
    """Add or update a manifest entry for a file already in data/raw/."""
    manifest = load_manifest()
    entry = {
        "url": url,
        "sha256": digest or sha256_of(path),
        "bytes": path.stat().st_size,
        "downloaded": dt.date.today().isoformat(),
        "licence": licence,
    }
    if note:
        entry["note"] = note
    manifest[_key(path)] = entry
    _save_manifest(manifest)
    return entry


def _backoff(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return min(float(retry_after), MAX_BACKOFF)
        except ValueError:
            pass
    return min(BASE_BACKOFF * (2 ** attempt), MAX_BACKOFF)


def _download(url: str, destination: Path, timeout: float, tries: int) -> str:
    """Stream to a .part file, hashing as we go, then move it into place atomically."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    last: Exception | None = None

    for attempt in range(tries):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            digest = hashlib.sha256()
            with _open(request, timeout) as response, partial.open("wb") as out:
                while chunk := response.read(CHUNK):
                    digest.update(chunk)
                    out.write(chunk)
            partial.replace(destination)
            return digest.hexdigest()
        except urllib.error.HTTPError as exc:
            partial.unlink(missing_ok=True)
            if exc.code not in RETRY_STATUS:
                raise PermanentFetchError(f"HTTP {exc.code} for {url}") from exc
            last = exc
            wait = _backoff(attempt, exc.headers.get("Retry-After") if exc.headers else None)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            partial.unlink(missing_ok=True)
            last = exc
            wait = _backoff(attempt, None)

        if attempt == tries - 1:
            break
        print(f"  fetch retry {attempt + 1}/{tries} for {url}: {last}; waiting {wait:.0f}s",
              flush=True)
        _sleep(wait)

    raise RuntimeError(f"giving up on {url} after {tries} attempts: {last}")


def fetch(url: str, relative_path: str, *, licence: str, note: str = "",
          expected_sha256: str | None = None, refresh: bool = False,
          timeout: float = 120.0, tries: int = DEFAULT_TRIES) -> Path:
    """Download `url` to data/raw/<relative_path>, or reuse the cached copy.

    The cache is trusted only when the file on disk still hashes to what the manifest
    says. A truncated or edited file is re-downloaded rather than silently used.
    """
    destination = RAW / relative_path
    manifest = load_manifest()
    entry = manifest.get(_key(destination))

    if destination.exists() and entry and not refresh:
        actual = sha256_of(destination)
        if actual == entry["sha256"]:
            if expected_sha256 and actual != expected_sha256:
                raise IntegrityError(
                    f"cached {relative_path} has sha256 {actual}, expected {expected_sha256}"
                )
            print(f"  cached: {relative_path} ({entry['bytes'] / 1024:.0f} kB, sha256 "
                  f"{actual[:12]}...)")
            return destination
        print(f"  cache miss: {relative_path} changed on disk "
              f"({actual[:12]}... != {entry['sha256'][:12]}...); re-downloading")

    digest = _download(url, destination, timeout, tries)
    if expected_sha256 and digest != expected_sha256:
        destination.unlink(missing_ok=True)
        raise IntegrityError(
            f"{relative_path} downloaded with sha256 {digest}, expected {expected_sha256}"
        )
    written = record(destination, url=url, licence=licence, note=note, digest=digest)
    print(f"  downloaded: {relative_path} ({written['bytes'] / 1024:.0f} kB, sha256 "
          f"{digest[:12]}...)")
    return destination


def verify_cache() -> list[str]:
    """Re-hash every manifested file. Returns a list of problems, empty when clean."""
    problems: list[str] = []
    manifest = load_manifest()
    for key, entry in manifest.items():
        path = RAW / key
        if not path.exists():
            problems.append(f"{key}: listed in the manifest but missing from data/raw/")
            continue
        actual = sha256_of(path)
        if actual != entry["sha256"]:
            problems.append(f"{key}: sha256 {actual[:12]}... != manifest {entry['sha256'][:12]}...")
        if path.stat().st_size != entry["bytes"]:
            problems.append(f"{key}: size {path.stat().st_size} != manifest {entry['bytes']}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Raw download cache (P1-03)")
    parser.add_argument("--verify", action="store_true", help="re-hash every cached file")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.verify:
        problems = verify_cache()
        for problem in problems:
            print(f"FAIL {problem}")
        print(f"Verified {len(manifest)} cached file(s): "
              f"{'all match the manifest' if not problems else f'{len(problems)} problem(s)'}")
        return 1 if problems else 0
    total = sum(e["bytes"] for e in manifest.values())
    print(f"{len(manifest)} file(s) cached, {total / 1024:.0f} kB total")
    for key, entry in manifest.items():
        print(f"  {key}  {entry['bytes'] / 1024:>8.0f} kB  {entry['downloaded']}  "
              f"{entry['licence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
