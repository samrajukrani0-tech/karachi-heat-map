"""Fetch a single member out of a remote ZIP, using HTTP range requests.

HDX serves the Meta population layers as ~550 MB zips covering India and Pakistan, but
each zip holds 13 separate 10-degree tiles. Karachi lives in one of them, about 18 MB.
Zip stores each member's compressed bytes at a known offset, so the central directory
can be read from the tail of the file and then one member pulled directly -- roughly a
30x saving, and the same principle as reading a raster in windows (PROMPT.md 2.8).

Run:
    uv run python -m pipeline.hdx --list <hdx-dataset-id>
"""

from __future__ import annotations

import argparse
import json
import struct
import urllib.request
import zlib
from pathlib import Path
from typing import Any, NamedTuple

from pipeline import fetch as fetchmod
from pipeline.config import RAW

HDX_API = "https://data.humdata.org/api/3/action/package_show?id="
UA = {"User-Agent": fetchmod.USER_AGENT}
EOCD_SIGNATURE = b"PK\x05\x06"
TAIL_BYTES = 65536


class Member(NamedTuple):
    name: str
    compressed_size: int
    uncompressed_size: int
    method: int
    header_offset: int


def _range(url: str, start: int | None, end: int | None = None) -> bytes:
    spec = f"bytes=-{start}" if end is None and start is not None and start < 0 else \
           f"bytes={start}-{end}" if end is not None else f"bytes={start}-"
    request = urllib.request.Request(url, headers={**UA, "Range": spec})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def dataset(dataset_id: str, *, refresh: bool = False, tries: int = 6) -> dict[str, Any]:
    """Dataset metadata from HDX, cached.

    HDX answers a burst of requests with `202 Accepted` and an empty body rather than
    an error, so a naive client sees a JSON parse failure. Treat that as "slow down":
    back off, retry, and cache the answer so a rebuild asks once, not once per layer.
    """
    cached = RAW / "hdx" / f"{dataset_id}.json"
    if cached.exists() and not refresh:
        return json.loads(cached.read_text(encoding="utf-8"))["result"]

    last = ""
    for attempt in range(tries):
        request = urllib.request.Request(HDX_API + dataset_id, headers=UA)
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = response.read()
                status = response.status
            payload = json.loads(body)
            if payload.get("success"):
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(body)
                fetchmod.record(cached, url=HDX_API + dataset_id,
                                licence="HDX metadata; the dataset carries its own licence",
                                note=f"package_show for {dataset_id}")
                return payload["result"]
            last = f"success=false: {payload.get('error')}"
        except (json.JSONDecodeError, ValueError):
            last = f"HTTP {status} with a {len(body)}-byte body (HDX rate limit)"
        except Exception as exc:  # network hiccup
            last = f"{type(exc).__name__}: {exc}"
        wait = min(15 * (attempt + 1), 90)
        print(f"  HDX retry {attempt + 1}/{tries}: {last}; waiting {wait}s", flush=True)
        fetchmod._sleep(wait)
    raise RuntimeError(f"HDX metadata unavailable for {dataset_id} after {tries} attempts: {last}")


def resource_url(meta: dict[str, Any], resource_name: str) -> str:
    for resource in meta["resources"]:
        if resource["name"] == resource_name:
            return resource["url"]
    available = ", ".join(r["name"] for r in meta["resources"])
    raise KeyError(f"{resource_name!r} not in this dataset. Available: {available}")


def list_members(url: str) -> list[Member]:
    """Read the zip's central directory from the tail of the remote file."""
    request = urllib.request.Request(url, headers={**UA, "Range": f"bytes=-{TAIL_BYTES}"})
    with urllib.request.urlopen(request, timeout=180) as response:
        tail = response.read()
    index = tail.rfind(EOCD_SIGNATURE)
    if index < 0:
        raise ValueError("no end-of-central-directory record; is this a zip?")
    cd_size, cd_offset = struct.unpack("<II", tail[index + 12:index + 20])
    directory = _range(url, cd_offset, cd_offset + cd_size - 1)

    members: list[Member] = []
    offset = 0
    while offset < len(directory) and directory[offset:offset + 4] == b"PK\x01\x02":
        method, = struct.unpack("<H", directory[offset + 10:offset + 12])
        compressed, uncompressed = struct.unpack("<II", directory[offset + 20:offset + 28])
        name_len, extra_len, comment_len = struct.unpack("<HHH", directory[offset + 28:offset + 34])
        header_offset, = struct.unpack("<I", directory[offset + 42:offset + 46])
        name = directory[offset + 46:offset + 46 + name_len].decode("utf-8", "replace")
        if not name.endswith("/") and "__MACOSX" not in name:
            members.append(Member(name, compressed, uncompressed, method, header_offset))
        offset += 46 + name_len + extra_len + comment_len
    return members


def extract_member(url: str, member: Member, destination: Path) -> Path:
    """Range-fetch one member's bytes and decompress them to `destination`."""
    header = _range(url, member.header_offset, member.header_offset + 29)
    if header[:4] != b"PK\x03\x04":
        raise ValueError(f"no local file header at offset {member.header_offset}")
    name_len, extra_len = struct.unpack("<HH", header[26:30])
    start = member.header_offset + 30 + name_len + extra_len
    payload = _range(url, start, start + member.compressed_size - 1)
    if len(payload) != member.compressed_size:
        raise ValueError(f"expected {member.compressed_size} bytes, received {len(payload)}")

    if member.method == 0:
        data = payload
    elif member.method == 8:
        data = zlib.decompress(payload, -zlib.MAX_WBITS)
    else:
        raise ValueError(f"unsupported zip compression method {member.method}")
    if len(data) != member.uncompressed_size:
        raise ValueError(f"decompressed {len(data)} bytes, directory says "
                         f"{member.uncompressed_size}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.write_bytes(data)
    partial.replace(destination)
    return destination


def fetch_tile(dataset_id: str, resource_name: str, member_contains: str,
               relative_path: str, *, licence: str, note: str = "") -> Path:
    """Download one tile out of an HDX zip, cache it, and record it in the manifest."""
    destination = RAW / relative_path
    manifest = fetchmod.load_manifest()
    key = destination.relative_to(RAW).as_posix()
    if destination.exists() and key in manifest:
        if fetchmod.sha256_of(destination) == manifest[key]["sha256"]:
            print(f"  cached: {relative_path} ({destination.stat().st_size / 1e6:.1f} MB)")
            return destination

    url = resource_url(dataset(dataset_id), resource_name)
    members = list_members(url)
    matches = [m for m in members if member_contains in m.name]
    if len(matches) != 1:
        names = ", ".join(m.name for m in members)
        raise KeyError(f"{member_contains!r} matched {len(matches)} members. Available: {names}")
    member = matches[0]
    total = sum(m.compressed_size for m in members)
    print(f"  {resource_name}: {len(members)} tiles, {total / 1e6:.0f} MB total; "
          f"fetching only {member.name.split('/')[-1]} "
          f"({member.compressed_size / 1e6:.1f} MB compressed, "
          f"{member.uncompressed_size / 1e6:.1f} MB raster)")
    extract_member(url, member, destination)
    fetchmod.record(destination, url=url, licence=licence,
                    note=note or f"zip member {member.name} from {resource_name}")
    print(f"  downloaded: {relative_path} ({destination.stat().st_size / 1e6:.1f} MB)")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an HDX zip without downloading it")
    parser.add_argument("dataset_id")
    parser.add_argument("resource_name")
    args = parser.parse_args()
    url = resource_url(dataset(args.dataset_id), args.resource_name)
    for member in list_members(url):
        print(f"  {member.uncompressed_size / 1e6:>8.1f} MB raster  "
              f"{member.compressed_size / 1e6:>7.1f} MB compressed  {member.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
