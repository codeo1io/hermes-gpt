"""Regression tests for the bounded fleet POST read (rm-183).

``_http_post_json`` buffered the peer response unbounded while the GET helper
in the same module was already bounded by ``_MAX_REMOTE_BYTES`` — a hostile or
compromised A2A peer could exhaust this process's memory with an oversized
response. Kept in a dedicated module because the canonical
``test_operator_fleet.py`` is owned by a concurrently-landing cycle.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

import operator_fleet


class _StubResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self, size: int | None = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]

    def __enter__(self) -> "_StubResponse":
        return self

    def __exit__(self, *_exc: Any) -> None:
        return None


def test_post_response_over_bound_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    oversized = b"x" * (operator_fleet._MAX_REMOTE_BYTES + 1)
    monkeypatch.setattr(
        operator_fleet.urllib.request,
        "urlopen",
        lambda *a, **k: _StubResponse(oversized),
    )
    with pytest.raises(ValueError, match="bounded response limit"):
        operator_fleet._http_post_json("http://peer.example/a2a", {}, {}, timeout=5)


def test_post_response_within_bound_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"ok": True}).encode("utf-8")
    assert len(payload) <= operator_fleet._MAX_REMOTE_BYTES
    monkeypatch.setattr(
        operator_fleet.urllib.request,
        "urlopen",
        lambda *a, **k: _StubResponse(payload),
    )
    assert operator_fleet._http_post_json(
        "http://peer.example/a2a", {}, {}, timeout=5
    ) == {"ok": True}


def test_post_read_requests_exactly_bound_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bound must be enforced by a bounded read, not a full buffer."""
    requested: list[int | None] = []

    class _Recording(_StubResponse):
        def read(self, size: int | None = -1) -> bytes:
            requested.append(size)
            return super().read(size)

    payload = b"{}"
    monkeypatch.setattr(
        operator_fleet.urllib.request,
        "urlopen",
        lambda *a, **k: _Recording(payload),
    )
    operator_fleet._http_post_json("http://peer.example/a2a", {}, {}, timeout=5)
    assert requested == [operator_fleet._MAX_REMOTE_BYTES + 1]
