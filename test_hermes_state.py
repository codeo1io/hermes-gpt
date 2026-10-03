"""Contract tests for the shipped SessionDB shim (hermes_state.py, rm-108).

The shim is production-shipped (server.py imports it; ui_chat.py calls it)
but previously had zero dedicated tests while implementing
concurrency-relevant lease arbitration and a read contract that silently
accepted-and-ignored four list_sessions_rich filters. These tests pin the
lease CAS semantics, the honored/rejected filter split, and the
``__getattr__`` AttributeError contract.

Every test passes an explicit ``db_path`` under ``tmp_path``: the shim's
default is the real ``~/.hermes/state.db`` and must never be touched.
"""

from __future__ import annotations

import sqlite3
import sys
import threading
from pathlib import Path

import pytest


def _bind_repo_hermes_state() -> tuple[dict, list[str]]:
    """Bind this repo's ``hermes_state`` shim deterministically.

    Full-suite ordering hazard: earlier tests import ``server`` (and other
    surfaces) whose root discovery inserts the deployed Hermes Agent install
    at ``sys.path[0]`` (server.py:195) — and the deployed agent ships its own
    ``hermes_state``/``hermes_state_sessions`` modules. This file holds the
    suite's only module-scope ``import hermes_state``; without this guard the
    full suite silently binds the AGENT's module (observed: failures with
    tracebacks in ``~/.hermes/hermes-agent/hermes_state_sessions.py``) while
    standalone/targeted runs bind the repo shim and pass. Purge any foreign
    binding, put the repo root first on ``sys.path``, import, and fail loudly
    unless the bound file is this repo's shim. Returns the captured
    ``sys.modules``/``sys.path`` state for session-teardown restoration.
    """
    saved_modules = {
        name: mod
        for name, mod in sys.modules.items()
        if name == "hermes_state" or name.startswith("hermes_state")
    }
    saved_path = list(sys.path)
    for name in list(sys.modules):
        if name == "hermes_state" or name.startswith("hermes_state"):
            del sys.modules[name]
    repo_root = str(Path(__file__).resolve().parent)
    if repo_root in sys.path:
        sys.path.remove(repo_root)
    sys.path.insert(0, repo_root)
    import hermes_state

    bound = Path(hermes_state.__file__).resolve()
    expected = Path(__file__).resolve().parent / "hermes_state.py"
    assert bound == expected, (
        f"test_hermes_state bound a foreign hermes_state: {bound} "
        f"(expected {expected})"
    )
    return saved_modules, saved_path


_HERMES_STATE_SAVED_MODULES, _HERMES_STATE_SAVED_PATH = _bind_repo_hermes_state()

import hermes_state  # noqa: E402  (must follow the binding guard)


@pytest.fixture(scope="session", autouse=True)
def _restore_hermes_state_binding():
    """Leave sys.modules/sys.path exactly as this file found them."""
    yield
    for name in list(sys.modules):
        if name == "hermes_state" or name.startswith("hermes_state"):
            del sys.modules[name]
    sys.modules.update(_HERMES_STATE_SAVED_MODULES)
    sys.path[:] = _HERMES_STATE_SAVED_PATH


@pytest.fixture
def db(tmp_path: Path) -> hermes_state.SessionDB:
    return hermes_state.SessionDB(db_path=tmp_path / "state.db")


def _seed(db: hermes_state.SessionDB, n: int = 3, source: str = "webui") -> list[str]:
    ids = []
    for i in range(n):
        sid = f"sess-{source}-{i:03d}"
        db.create_session(sid, source, model="test-model", profile_name="dev")
        db.append_message(sid, "user", content=f"hello {i}")
        ids.append(sid)
    return ids


# ---------------------------------------------------------------------------
# Turn lease: acquire / expire / CAS arbitration (rm-108)
# ---------------------------------------------------------------------------


def test_lease_acquire_and_second_holder_rejected(db):
    assert db.try_acquire_session_turn_lease("sess-1", "worker-a") is True
    # A live lease held by another worker must refuse (single-writer CAS).
    assert db.try_acquire_session_turn_lease("sess-1", "worker-b") is False


def test_lease_same_holder_reacquires_and_renews(db):
    assert db.try_acquire_session_turn_lease("sess-1", "worker-a") is True
    assert db.try_acquire_session_turn_lease("sess-1", "worker-a") is True


def test_lease_expired_lease_releasable_by_other_holder(db):
    assert db.try_acquire_session_turn_lease("sess-1", "worker-a") is True
    # Age the lease past its expiry directly (deterministic; no sleeps).
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            "UPDATE session_turn_leases SET expires_at = ? WHERE conversation_id = ?",
            (time_epoch_minus_1(), "sess-1"),
        )
        conn.commit()
    finally:
        conn.close()
    # Stale lease is expired, not honored: the new holder wins.
    assert db.try_acquire_session_turn_lease("sess-1", "worker-b") is True


def time_epoch_minus_1() -> float:
    import time

    return time.time() - 1.0


def test_lease_release_lets_other_holder_acquire(db):
    db.try_acquire_session_turn_lease("sess-1", "worker-a")
    db.release_session_turn_lease("sess-1", "worker-a")
    assert db.try_acquire_session_turn_lease("sess-1", "worker-b") is True


def test_lease_release_by_other_holder_is_noop(db):
    db.try_acquire_session_turn_lease("sess-1", "worker-a")
    db.release_session_turn_lease("sess-1", "worker-b")  # wrong holder: no effect
    assert db.try_acquire_session_turn_lease("sess-1", "worker-b") is False


def test_lease_refresh_extends_expiry_only_for_holder(db):
    import time

    db.try_acquire_session_turn_lease("sess-1", "worker-a", ttl_seconds=10.0)
    before = time.time() + 10.0
    ok = db.refresh_session_turn_lease("sess-1", "worker-a", ttl_seconds=300.0)
    assert ok is True
    conn = sqlite3.connect(str(db.db_path))
    try:
        row = conn.execute(
            "SELECT holder, expires_at FROM session_turn_leases WHERE conversation_id = ?",
            ("sess-1",),
        ).fetchone()
    finally:
        conn.close()
    assert row[0] == "worker-a"
    assert row[1] >= before + 250.0  # extended, not the original 10s window
    # A refresh by anyone else must not steal or extend the lease.
    assert db.refresh_session_turn_lease("sess-1", "worker-b", ttl_seconds=300.0) is False
    assert db.try_acquire_session_turn_lease("sess-1", "worker-b") is False


def test_lease_refresh_without_lease_fails(db):
    assert db.refresh_session_turn_lease("sess-none", "worker-a") is False


def test_lease_concurrent_acquire_is_single_winner(db):
    barrier = threading.Barrier(2)
    results: list[bool] = []
    results_lock = threading.Lock()

    def attempt(holder: str) -> None:
        barrier.wait()
        got = db.try_acquire_session_turn_lease("sess-1", holder)
        with results_lock:
            results.append(got)

    threads = [
        threading.Thread(target=attempt, args=(f"worker-{i}",)) for i in range(2)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Exactly one concurrent acquisition may win the conversation.
    assert sorted(results) == [False, True]


def test_lease_patience_returns_false_while_lease_live(db):
    # A live long lease + tiny patience: bounded wait, then refusal.
    assert db.try_acquire_session_turn_lease("sess-1", "worker-a", ttl_seconds=300.0) is True
    got = db.try_acquire_session_turn_lease(
        "sess-1", "worker-b", ttl_seconds=300.0, patience_s=0.12
    )
    assert got is False


# ---------------------------------------------------------------------------
# list_sessions_rich: honored / inert / rejected filters (rm-108)
# ---------------------------------------------------------------------------


def test_list_sessions_filters_by_source(db):
    _seed(db, 2, source="webui")
    _seed(db, 1, source="cli")
    assert {r["id"] for r in db.list_sessions_rich(source="webui")} == {
        "sess-webui-000",
        "sess-webui-001",
    }
    assert {r["id"] for r in db.list_sessions_rich(sources=["cli"])} == {
        "sess-cli-000"
    }


def test_list_sessions_search_query_matches_title_and_id(db):
    db.create_session("sess-alpha", "webui", title=None)
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute("UPDATE sessions SET title = 'Daily Standup Notes' WHERE id = 'sess-alpha'")
        conn.commit()
    finally:
        conn.close()
    db.create_session("sess-beta", "webui")
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute("UPDATE sessions SET title = 'Bug Hunt' WHERE id = 'sess-beta'")
        conn.commit()
    finally:
        conn.close()

    # Substring against title (case-insensitive for ASCII by SQLite LIKE).
    assert [r["id"] for r in db.list_sessions_rich(search_query="standup")] == [
        "sess-alpha"
    ]
    # Substring against id.
    assert [r["id"] for r in db.list_sessions_rich(search_query="beta")] == [
        "sess-beta"
    ]
    # No match: empty, not "everything" (silent-ignore regression guard).
    assert db.list_sessions_rich(search_query="no-such-session") == []


def test_list_sessions_search_query_escapes_like_wildcards(db):
    db.create_session("sess-one", "webui")
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute("UPDATE sessions SET title = 'plain title' WHERE id = 'sess-one'")
        conn.commit()
    finally:
        conn.close()
    # A literal % or _ in the query must not act as a wildcard.
    assert db.list_sessions_rich(search_query="100%") == []
    assert db.list_sessions_rich(search_query="sess_one") == []


def test_list_sessions_archived_only_is_empty_not_everything(db):
    _seed(db, 3)
    # The shim schema has no archived concept: "only archived" is provably
    # empty. Previously this returned every session (rm-108).
    assert db.list_sessions_rich(archived_only=True) == []


def test_list_sessions_include_archived_accepted_as_inert(db):
    _seed(db, 2)
    included = db.list_sessions_rich(include_archived=True)
    excluded = db.list_sessions_rich(include_archived=False)
    # No session can be archived in the shim schema: identical by
    # construction, and the parameter is accepted (both real callers pass
    # it — server.py session adapter and ui_chat.py).
    assert {r["id"] for r in included} == {r["id"] for r in excluded}


def test_list_sessions_cwd_prefix_rejected_explicitly(db):
    _seed(db, 1)
    with pytest.raises(ValueError, match="cwd_prefix"):
        db.list_sessions_rich(cwd_prefix="/work/projects")


def test_list_sessions_ordering_and_limit(db):
    _seed(db, 4)
    recent = db.list_sessions_rich(order_by_last_active=True, limit=2)
    assert len(recent) == 2
    # last_activity ordering: the two most recently touched sessions.
    all_by_activity = db.list_sessions_rich(order_by_last_active=True)
    assert [r["id"] for r in recent] == [r["id"] for r in all_by_activity[:2]]


# ---------------------------------------------------------------------------
# __getattr__: AttributeError contract (rm-108)
# ---------------------------------------------------------------------------


def test_getattr_missing_method_raises_attribute_error(db):
    with pytest.raises(AttributeError, match="does not implement 'search_messages'"):
        db.search_messages(query="x", limit=1, offset=0)


def test_hasattr_reports_missing_not_raises(db):
    # The capability-probe contract server.py relies on (e.g. the
    # _SessionSearchUnavailable path): hasattr must answer, never raise.
    assert hasattr(db, "list_sessions_rich") is True
    assert hasattr(db, "search_messages") is False
    assert hasattr(db, "get_compression_tip") is False


def test_getattr_with_default_returns_default(db):
    assert getattr(db, "resolve_session_id", None) is None


# ---------------------------------------------------------------------------
# Core store contract anchors (what the lease/list paths stand on)
# ---------------------------------------------------------------------------


def test_create_and_message_roundtrip(db):
    db.create_session("sess-rt", "webui", model="m1", profile_name="dev")
    mid = db.append_message("sess-rt", "user", content="hello")
    assert isinstance(mid, int) and mid > 0
    msgs = db.get_messages("sess-rt")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "hello"
    session = db.get_session("sess-rt")
    assert session["message_count"] == 1
    assert session["source"] == "webui"


def test_read_only_db_refuses_writes(tmp_path: Path):
    ro = hermes_state.SessionDB(db_path=tmp_path / "ro.db", read_only=True)
    with pytest.raises(RuntimeError, match="read-only"):
        ro.create_session("sess-ro", "webui")
