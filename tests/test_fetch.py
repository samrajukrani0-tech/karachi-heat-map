"""P1-03: the raw download cache.

Every test uses a mocked transport, so the suite never touches the network and never
writes to the real data/raw/. SYNTHETIC payloads only.
"""

import hashlib
import io
import json
import urllib.error

import pytest

from pipeline import fetch as F

SYNTHETIC_BODY = b"SYNTHETIC test payload, not real data\n" * 40
SYNTHETIC_SHA = hashlib.sha256(SYNTHETIC_BODY).hexdigest()


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes):
        super().__init__(body)
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class Transport:
    """Replays a scripted list of responses and counts how often it is called."""

    def __init__(self, *script):
        self.script = list(script)
        self.calls = 0
        self.waits: list[float] = []

    def __call__(self, request, timeout):
        self.calls += 1
        item = self.script.pop(0) if self.script else SYNTHETIC_BODY
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Point the module at a temporary cache and a mocked transport."""
    monkeypatch.setattr(F, "RAW", tmp_path)
    monkeypatch.setattr(F, "MANIFEST", tmp_path / "manifest.json")
    transport = Transport()
    monkeypatch.setattr(F, "_open", transport)
    monkeypatch.setattr(F, "_sleep", transport.waits.append)
    return transport


def http_error(code: int, headers: dict | None = None):
    return urllib.error.HTTPError("https://example.test/x", code, "boom", headers or {}, None)


# --- happy path -------------------------------------------------------------------

def test_downloads_and_records_the_manifest(cache, tmp_path):
    path = F.fetch("https://example.test/a.bin", "sub/a.bin",
                   licence="CC BY 4.0", note="synthetic")
    assert path.read_bytes() == SYNTHETIC_BODY
    entry = F.load_manifest()["sub/a.bin"]
    assert entry["sha256"] == SYNTHETIC_SHA
    assert entry["bytes"] == len(SYNTHETIC_BODY)
    assert entry["url"] == "https://example.test/a.bin"
    assert entry["licence"] == "CC BY 4.0"
    assert entry["note"] == "synthetic"
    assert entry["downloaded"]


def test_second_run_downloads_nothing(cache):
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert cache.calls == 1
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert cache.calls == 1, "the cached copy should have been reused"


def test_refresh_forces_a_new_download(cache):
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0", refresh=True)
    assert cache.calls == 2


def test_manifest_keys_are_sorted(cache):
    for name in ("z.bin", "a.bin", "m.bin"):
        F.fetch(f"https://example.test/{name}", name, licence="CC0")
    keys = list(json.loads(F.MANIFEST.read_text(encoding="utf-8")))
    assert keys == sorted(keys)


# --- the cache is trusted only when it verifies ------------------------------------

def test_a_tampered_cache_is_redownloaded(cache):
    path = F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    path.write_bytes(b"corrupted")
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert cache.calls == 2
    assert path.read_bytes() == SYNTHETIC_BODY


def test_a_file_with_no_manifest_entry_is_not_trusted(cache, tmp_path):
    stray = tmp_path / "a.bin"
    stray.write_bytes(SYNTHETIC_BODY)
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert cache.calls == 1, "an unmanifested file must not be treated as cached"


def test_checksum_mismatch_raises_and_removes_the_file(cache, tmp_path):
    with pytest.raises(F.IntegrityError):
        F.fetch("https://example.test/a.bin", "a.bin", licence="CC0",
                expected_sha256="0" * 64)
    assert not (tmp_path / "a.bin").exists()
    assert "a.bin" not in F.load_manifest()


def test_matching_expected_checksum_is_accepted(cache):
    path = F.fetch("https://example.test/a.bin", "a.bin", licence="CC0",
                   expected_sha256=SYNTHETIC_SHA)
    assert path.exists()


# --- retries and backoff -----------------------------------------------------------

def test_retries_a_transient_error_then_succeeds(cache, monkeypatch):
    transport = Transport(http_error(503), http_error(502), SYNTHETIC_BODY)
    monkeypatch.setattr(F, "_open", transport)
    monkeypatch.setattr(F, "_sleep", transport.waits.append)
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert transport.calls == 3
    assert transport.waits == [F.BASE_BACKOFF, F.BASE_BACKOFF * 2], "backoff should grow"


def test_retry_after_header_is_honoured(cache, monkeypatch):
    transport = Transport(http_error(429, {"Retry-After": "7"}), SYNTHETIC_BODY)
    monkeypatch.setattr(F, "_open", transport)
    monkeypatch.setattr(F, "_sleep", transport.waits.append)
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert transport.waits == [7.0]


def test_backoff_is_capped(cache):
    assert F._backoff(99, None) == F.MAX_BACKOFF
    assert F._backoff(0, "999999") == F.MAX_BACKOFF


def test_a_permanent_error_is_not_retried(cache, monkeypatch):
    transport = Transport(http_error(404), SYNTHETIC_BODY)
    monkeypatch.setattr(F, "_open", transport)
    monkeypatch.setattr(F, "_sleep", transport.waits.append)
    with pytest.raises(F.PermanentFetchError):
        F.fetch("https://example.test/gone", "gone.bin", licence="CC0")
    assert transport.calls == 1, "404 must not be retried"


def test_gives_up_after_the_try_limit(cache, monkeypatch):
    transport = Transport(*[http_error(503)] * 9)
    monkeypatch.setattr(F, "_open", transport)
    monkeypatch.setattr(F, "_sleep", transport.waits.append)
    with pytest.raises(RuntimeError, match="giving up"):
        F.fetch("https://example.test/a.bin", "a.bin", licence="CC0", tries=3)
    assert transport.calls == 3
    assert len(transport.waits) == 2, "no sleep after the final attempt"


def test_partial_files_are_cleaned_up_on_failure(cache, tmp_path, monkeypatch):
    transport = Transport(*[urllib.error.URLError("connection reset")] * 5)
    monkeypatch.setattr(F, "_open", transport)
    monkeypatch.setattr(F, "_sleep", transport.waits.append)
    with pytest.raises(RuntimeError):
        F.fetch("https://example.test/a.bin", "a.bin", licence="CC0", tries=2)
    assert list(tmp_path.glob("*.part")) == []


# --- verification ------------------------------------------------------------------

def test_verify_cache_is_clean_after_a_good_fetch(cache):
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    assert F.verify_cache() == []


def test_verify_cache_detects_tampering(cache, tmp_path):
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    (tmp_path / "a.bin").write_bytes(b"edited")
    problems = F.verify_cache()
    # Tampering breaks both the hash and the size, and both are worth reporting.
    assert len(problems) == 2
    assert any("sha256" in p for p in problems)
    assert any("size" in p for p in problems)
    assert all(p.startswith("a.bin:") for p in problems)


def test_verify_cache_detects_a_missing_file(cache, tmp_path):
    F.fetch("https://example.test/a.bin", "a.bin", licence="CC0")
    (tmp_path / "a.bin").unlink()
    assert any("missing" in p for p in F.verify_cache())
