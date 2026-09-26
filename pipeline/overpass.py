"""A small, polite Overpass client with an on-disk cache.

PROMPT.md section 2.8: be gentle with Overpass and cache downloads. P1-03 replaces
this module's caching with the full manifest-and-checksum version; until then the
cache is a plain file plus the sha256 recorded in whatever output uses it.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from pipeline.config import RAW

ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
USER_AGENT = (
    "karachi-heat-map/0.1 (A Level student project; "
    "https://github.com/samrajukrani0-tech/karachi-heat-map)"
)
CACHE_DIR = RAW / "osm"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def query(body: str, cache_key: str, *, refresh: bool = False,
          tries: int = 5, timeout: int = 300) -> tuple[dict[str, Any], str]:
    """Run an Overpass query, returning (parsed json, sha256 of the raw text).

    The raw response is cached at data/raw/osm/<cache_key>.json. A second call with
    the same key downloads nothing unless refresh=True.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"{cache_key}.json"
    if cached.exists() and not refresh:
        text = cached.read_text(encoding="utf-8")
        return json.loads(text), sha256(text)

    last: Exception | None = None
    for attempt in range(tries):
        endpoint = ENDPOINTS[attempt % len(ENDPOINTS)]
        request = urllib.request.Request(
            endpoint,
            data=urllib.parse.urlencode({"data": body}).encode(),
            headers={"User-Agent": USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8")
            json.loads(text)  # fail here rather than later if it is not JSON
            cached.write_text(text, encoding="utf-8")
            return json.loads(text), sha256(text)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last = exc
            wait = 8 * (attempt + 1)
            print(f"  overpass retry {attempt + 1}/{tries} "
                  f"({endpoint.split('/')[2]}): {exc}; waiting {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Overpass unavailable after {tries} attempts: {last}")


def cache_path(cache_key: str) -> Path:
    return CACHE_DIR / f"{cache_key}.json"
