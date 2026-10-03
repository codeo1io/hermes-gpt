"""Behavior-only coverage for the hermes_state.py session shim (rm-189).

``hermes_state.SessionDB`` is the local stand-in used by ``ui_chat`` when the
real ``hermes_state`` package from a Hermes root is unavailable (see
``ui_chat._session_db``). It owns sessions, messages, ``list_sessions_rich``
filters, and the SQLite-backed session turn leases that gate concurrent UI
turns. Until now it had no direct suite: ``test_ui_chat`` only exercises it
incidentally through the chat HTTP flow (lease conflicts as HTTP 409).

This suite pins CURRENT semantics only — it deliberately does not encode any
lease-atomicity or retention redesigns (separate roadmap work). Direct
``sqlite3`` writes below are fixture arrangement (force-expiring a lease,
toggling message flags), not semantic changes.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import time
from pathlib import Path as _Path

import pytest

# Bind the module by explicit file path: ``import hermes_state`` is NOT
# deterministic under the fleet's parallel test runner — sibling test modules
# (skill-resolution path setup) can insert other checkouts into sys.path
# first, silently resolving this name to a different project's module with
# different semantics. This suite pins THIS repository's SessionDB contract.
_SPEC = importlib.util.spec_from_file_location(
    "hermes_gpt_state_under_test", _Path(__file__).resolve().parent / "hermes_state.py"
)
hermes_state = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("hermes_gpt_state_under_test", hermes_state)
_SPEC.loader.exec_module(hermes_state)
SessionDB = hermes_state.SessionDB


@pytest.fixture()
def db(tmp_path):
    return SessionDB(db_path=tmp_path / "state.db")


def _direct(db_path, sql, params=()):
    """Fixture helper: raw write against the WAL db from outside the shim."""
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Construction + schema init
# ---------------------------------------------------------------------------


def test_schema_created_and_reopen_is_idempotent(tmp_path):
    path = tmp_path / "state.db"
    first = SessionDB(db_path=path)
    first.create_session("s1", source="test")
    first.append_message("s1", "user", "hello")
    # A second instance over the same file must not fail on the existing
    # schema and must see the same data (thread-local conns share the db).
    second = SessionDB(db_path=path)
    assert second.get_session("s1")["source"] == "test"
    assert second.get_session("s1")["message_count"] == 1
    assert path.exists()
    assert (tmp_path / "state.db-wal").exists()  # WAL mode enabled


def test_default_db_path_under_hermes_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(hermes_state.Path, "home", lambda: home)
    sdb = SessionDB()
    assert sdb.db_path == home / ".hermes" / "state.db"


def test_read_only_rejects_writes_and_allows_reads(tmp_path):
    path = tmp_path / "state.db"
    writable = SessionDB(db_path=path)
    writable.create_session("s1", source="test")
    writable.append_message("s1", "user", "hi")

    ro = SessionDB(db_path=path, read_only=True)
    assert ro.get_session("s1")["id"] == "s1"
    assert [m["content"] for m in ro.get_messages("s1")] == ["hi"]
    with pytest.raises(RuntimeError, match="read-only"):
        ro.create_session("s2", source="test")
    with pytest.raises(RuntimeError, match="read-only"):
        ro.append_message("s1", "user", "nope")


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


def test_create_get_session_defaults_and_unknown(db):
    returned = db.create_session("s1", source="test")
    assert returned == "s1"
    row = db.get_session("s1")
    assert row["id"] == "s1"
    assert row["source"] == "test"
    assert row["model"] is None and row["profile_name"] is None
    assert row["message_count"] == 0
    assert db.get_session("does-not-exist") is None


def test_session_kwargs_roundtrip(db):
    db.create_session("s1", source="ui", model="m1", profile_name="default")
    row = db.get_session("s1")
    assert row["model"] == "m1" and row["profile_name"] == "default"


# ---------------------------------------------------------------------------
# Messages + get_messages filters
# ---------------------------------------------------------------------------


def test_message_ids_increase_and_count_tracks(db):
    db.create_session("s1", source="test")
    ids = [db.append_message("s1", "user", f"m{i}") for i in range(3)]
    assert ids[0] < ids[1] < ids[2]
    assert db.get_session("s1")["message_count"] == 3


def test_message_roles_content_and_tool_calls_json(db):
    db.create_session("s1", source="test")
    db.append_message("s1", "user", "hi", tool_calls=[{"name": "t", "args": {}}])
    msgs = db.get_messages("s1")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "hi"
    # tool_calls round-trips as a JSON string (current contract, not parsed).
    assert json.loads(msgs[0]["tool_calls"]) == [{"name": "t", "args": {}}]


def test_get_messages_ordering_latest_after_id_limit_offset(db):
    db.create_session("s1", source="test")
    for i in range(5):
        db.append_message("s1", "user", f"m{i}")
    all_msgs = db.get_messages("s1")
    assert [m["content"] for m in all_msgs] == [f"m{i}" for i in range(5)]
    # latest=True selects newest-first internally then reverses, so WITH a
    # limit it returns the newest N in chronological order (current contract).
    newest_two = db.get_messages("s1", latest=True, limit=2)
    assert [m["content"] for m in newest_two] == ["m3", "m4"]
    after = db.get_messages("s1", after_id=all_msgs[1]["id"])
    assert [m["content"] for m in after] == ["m2", "m3", "m4"]
    page = db.get_messages("s1", limit=2, offset=1)
    assert [m["content"] for m in page] == ["m1", "m2"]


def test_get_messages_hides_inactive_and_compacted_by_default(db, tmp_path):
    db.create_session("s1", source="test")
    ids = [db.append_message("s1", "user", f"m{i}") for i in range(3)]
    _direct(tmp_path / "state.db", "UPDATE messages SET active=0 WHERE id=?", (ids[0],))
    _direct(tmp_path / "state.db", "UPDATE messages SET compacted=1 WHERE id=?", (ids[2],))
    visible = [m["content"] for m in db.get_messages("s1")]
    assert visible == ["m1"]
    # include_inactive drops only the active filter; compacted still hides m2.
    include_inactive = [m["content"] for m in db.get_messages("s1", include_inactive=True)]
    assert include_inactive == ["m0", "m1"]
    include_both = [
        m["content"]
        for m in db.get_messages("s1", include_inactive=True, include_compacted=True)
    ]
    assert include_both == ["m0", "m1", "m2"]


# ---------------------------------------------------------------------------
# list_sessions_rich filters
# ---------------------------------------------------------------------------


def test_list_sessions_rich_filters(db):
    db.create_session("a", source="ui", profile_name="p1")
    db.create_session("b", source="mcp", profile_name="p2")
    db.create_session("c", source="api", profile_name="p3")
    db.append_message("a", "user", "one")
    db.append_message("b", "user", "two")
    db.append_message("b", "assistant", "three")
    db.append_message("c", "user", "x")

    all_rows = db.list_sessions_rich(limit=50)
    assert {r["id"] for r in all_rows} == {"a", "b", "c"}

    by_source = db.list_sessions_rich(source="mcp")
    assert [r["id"] for r in by_source] == ["b"]

    in_sources = db.list_sessions_rich(sources=["ui", "api"])
    assert {r["id"] for r in in_sources} == {"a", "c"}

    excluded = db.list_sessions_rich(exclude_sources=["ui", "api", "test"])
    assert [r["id"] for r in excluded] == ["b"]

    min2 = db.list_sessions_rich(min_message_count=2)
    assert [r["id"] for r in min2] == ["b"]

    assert len(db.list_sessions_rich(limit=2)) == 2
    assert len(db.list_sessions_rich(limit=2, offset=2)) == 1


def test_list_sessions_rich_orders_by_last_active_desc(db):
    db.create_session("old", source="ui")
    db.create_session("new", source="ui")
    db.append_message("old", "user", "first")
    time.sleep(0.02)
    db.append_message("new", "user", "second")
    assert [r["id"] for r in db.list_sessions_rich(order_by_last_active=True)] == ["new", "old"]
    # A later message on the old session flips the order.
    time.sleep(0.02)
    db.append_message("old", "user", "third")
    assert [r["id"] for r in db.list_sessions_rich(order_by_last_active=True)] == ["old", "new"]


# ---------------------------------------------------------------------------
# Session turn leases (current semantics: SQLite-backed, session-scoped)
# ---------------------------------------------------------------------------


def test_lease_lifecycle_acquire_conflict_release(db):
    assert db.try_acquire_session_turn_lease("s1", holder="a", ttl_seconds=300) is True
    # Same holder re-acquiring is allowed (the upsert refreshes it).
    assert db.try_acquire_session_turn_lease("s1", holder="a", ttl_seconds=300) is True
    # A different holder is rejected while held.
    assert db.try_acquire_session_turn_lease("s1", holder="b", ttl_seconds=300) is False
    # Release by a non-holder does not free the lease.
    db.release_session_turn_lease("s1", holder="b")
    assert db.try_acquire_session_turn_lease("s1", holder="b", ttl_seconds=300) is False
    # Release by the holder frees it.
    db.release_session_turn_lease("s1", holder="a")
    assert db.try_acquire_session_turn_lease("s1", holder="b", ttl_seconds=300) is True


def test_lease_expiry_lets_other_holder_acquire(db, tmp_path):
    assert db.try_acquire_session_turn_lease("s1", holder="a", ttl_seconds=300) is True
    # Force-expire the held lease behind the shim's back.
    _direct(
        tmp_path / "state.db",
        "UPDATE session_turn_leases SET expires_at=? WHERE conversation_id=?",
        (time.time() - 1, "s1"),
    )
    assert db.try_acquire_session_turn_lease("s1", holder="b", ttl_seconds=300) is True


def test_lease_patience_waits_then_fails_or_succeeds(db, tmp_path):
    # Free lease + patience: succeeds immediately.
    assert (
        db.try_acquire_session_turn_lease("s1", holder="a", ttl_seconds=300, patience_s=0.1)
        is True
    )
    # Held by ANOTHER holder + patience: retries the full window, then fails.
    # patience_s waits for ANY non-acquirable state (foreign holder or lock
    # contention) and does not steal an unexpired foreign lease.
    start = time.monotonic()
    got = db.try_acquire_session_turn_lease("s1", holder="b", ttl_seconds=300, patience_s=0.2)
    elapsed = time.monotonic() - start
    assert got is False
    assert elapsed >= 0.15
    # An EXPIRED lease is takeable by a new holder (fixture backdate).
    _direct(
        tmp_path / "state.db",
        "UPDATE session_turn_leases SET expires_at = ? WHERE conversation_id = ?",
        (time.time() - 1, "s1"),
    )
    assert db.try_acquire_session_turn_lease("s1", holder="c", ttl_seconds=300) is True


def test_lease_refresh_extends_expiry_and_requires_holder(db, tmp_path):
    assert db.try_acquire_session_turn_lease("s1", holder="a", ttl_seconds=60) is True
    assert db.refresh_session_turn_lease("s1", holder="a", ttl_seconds=300) is True
    conn = sqlite3.connect(str(tmp_path / "state.db"), timeout=5.0)
    try:
        expires = conn.execute(
            "SELECT expires_at FROM session_turn_leases WHERE conversation_id=?", ("s1",)
        ).fetchone()[0]
    finally:
        conn.close()
    assert expires >= time.time() + 290  # extended, not left at the 60s ttl
    # Wrong holder and released leases are not refreshed.
    assert db.refresh_session_turn_lease("s1", holder="b", ttl_seconds=300) is False
    db.release_session_turn_lease("s1", holder="a")
    assert db.refresh_session_turn_lease("s1", holder="a", ttl_seconds=300) is False


# ---------------------------------------------------------------------------
# Fail-closed contract
# ---------------------------------------------------------------------------


def test_unimplemented_real_hermes_state_api_fails_closed(db):
    # The shim deliberately does not implement list_messages; a caller must
    # get a loud NotImplementedError, not a silent wrong answer.
    with pytest.raises(NotImplementedError, match="list_messages"):
        db.list_messages("any")
