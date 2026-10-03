"""Tests for v0.7 S4: structured event history surface (operator_events)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import operator_events as ev


@pytest.fixture
def hermes_root(tmp_path: Path) -> Path:
    root = tmp_path / "hermes"
    (root / "logs").mkdir(parents=True)
    (root / "swarm-workflows").mkdir(parents=True)
    (root / "codex-jobs").mkdir(parents=True)
    (root / "kanban" / "boards" / "default").mkdir(parents=True)
    (root / "profiles" / "default" / "cron").mkdir(parents=True)
    return root


@pytest.fixture(autouse=True)
def clean_events_env(monkeypatch):
    for name in (
        ev.EVENTS_ALLOWED_SOURCES_ENV,
        ev.EVENTS_MAX_AGE_DAYS_ENV,
    ):
        monkeypatch.delenv(name, raising=False)
    ev._cache.clear()
    yield
    ev._cache.clear()


def _write_audit(root: Path, rows: list[dict]) -> None:
    with open(root / "logs" / "hermes_gpt_operator_audit.jsonl", "a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _write_swarm(root: Path, workflow_id: str, status: str, ts: str) -> None:
    rec = {
        "schema": "hermes.swarm-workflow/v1",
        "workflow_id": workflow_id,
        "title": "wf",
        "status": status,
        "created_at": ts,
        "updated_at": ts,
        "stages": [
            {"id": "s1", "owner": "dev", "status": status, "started_at": ts, "ended_at": None},
        ],
    }
    (root / "swarm-workflows" / f"{workflow_id}.json").write_text(json.dumps(rec), encoding="utf-8")


def _write_codex(root: Path, job_id: str, status: str, ts: str) -> None:
    rec = {"schema": "codex-job", "job_id": job_id, "status": status, "created_at": ts, "updated_at": ts}
    (root / "codex-jobs" / f"{job_id}.json").write_text(json.dumps(rec), encoding="utf-8")


def _write_cron(root: Path, job_id: str, status: str, ts: str, error: str = "") -> None:
    db = root / "profiles" / "default" / "cron" / "executions.db"
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS executions (job_id TEXT, status TEXT, started_at TEXT, error TEXT)"
        )
        conn.execute(
            "INSERT INTO executions (job_id, status, started_at, error) VALUES (?, ?, ?, ?)",
            (job_id, status, ts, error),
        )
        conn.commit()
    finally:
        conn.close()


def _write_kanban(root: Path, task_id: str, kind: str, ts: str, summary: str = "") -> None:
    db = root / "kanban" / "boards" / "default" / "kanban.db"
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS task_events (task_id TEXT, kind TEXT, created_at TEXT, actor TEXT, summary TEXT)"
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, created_at, actor, summary) VALUES (?, ?, ?, ?, ?)",
            (task_id, kind, ts, "dev", summary),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_all_sources(root: Path) -> None:
    _write_audit(root, [{"timestamp": "2026-08-15T10:00:00+00:00", "tool": "hermes_contract_validate", "profile": "dev", "success": True, "summary": "validate ok"}])
    _write_swarm(root, "sw-1", "done", "2026-08-15T11:00:00+00:00")
    _write_codex(root, "codex-1", "finished", "2026-08-15T12:00:00+00:00")
    _write_cron(root, "job-1", "completed", "2026-08-15T13:00:00+00:00")
    _write_kanban(root, "t_123", "claimed", "2026-08-15T14:00:00+00:00", "claimed by dev")


def test_query_all_sources_returns_ordered_timeline(hermes_root):
    _seed_all_sources(hermes_root)
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root))
    assert out["success"] is True
    assert out["count_total"] >= 5
    # Newest first ordering.
    timestamps = [t for t in (ev._parse_iso_ts(e["ts"]) for e in out["events"]) if t is not None]
    assert timestamps == sorted(timestamps, reverse=True)
    sources = {e["source"] for e in out["events"]}
    assert {"audit", "swarm", "codex", "cron", "kanban"} <= sources


def test_no_raw_body_across_all_sources(hermes_root):
    """No raw messages, prompts, transcripts, or secret bodies on the surface."""
    _seed_all_sources(hermes_root)
    # Add a nasty audit row with prompt text that must be summarized, not passed.
    _write_audit(
        hermes_root,
        [{"timestamp": "2026-08-15T15:00:00+00:00", "tool": "hermes_skill_create", "profile": "dev", "success": True, "summary": "created skill", "prompt": "SECRET PROMPT BODY with api key sk-1234567890abcdefghijklmnop", "content": "raw content body"}],
    )
    out = json.loads(ev.hermes_events_tail(limit=100, hermes_root=hermes_root))
    raw = json.dumps(out)
    for forbidden in (
        "SECRET PROMPT BODY",
        "raw content body",
        "sk-1234567890abcdefghijklmnop",
        "prompt_len",  # audit prompt_sha is not part of the event schema
    ):
        assert forbidden not in raw, f"leaked: {forbidden}"


def test_allowlist_unset_means_all(hermes_root):
    _seed_all_sources(hermes_root)
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root))
    assert out["success"] is True
    assert set(out["sources_allowed"]) == set(ev.EVENT_SOURCES)


def test_allowlist_list_restricts_sources(hermes_root, monkeypatch):
    _seed_all_sources(hermes_root)
    monkeypatch.setenv(ev.EVENTS_ALLOWED_SOURCES_ENV, "swarm,codex")
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root))
    sources = {e["source"] for e in out["events"]}
    assert sources <= {"swarm", "codex"}
    assert out["sources_allowed"] == ["codex", "swarm"]


def test_allowlist_empty_denies_all(hermes_root, monkeypatch):
    _seed_all_sources(hermes_root)
    monkeypatch.setenv(ev.EVENTS_ALLOWED_SOURCES_ENV, "")
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root))
    assert out["success"] is True
    assert out["events"] == []
    assert out["sources_allowed"] == []


def test_retention_window_filters_old_events(hermes_root, monkeypatch):
    monkeypatch.setenv(ev.EVENTS_MAX_AGE_DAYS_ENV, "1")
    fresh = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    _write_audit(hermes_root, [{"timestamp": "2020-01-01T00:00:00+00:00", "tool": "hermes_contract_validate", "profile": "dev", "success": True, "summary": "ancient"}])
    _write_audit(hermes_root, [{"timestamp": fresh, "tool": "hermes_contract_validate", "profile": "dev", "success": True, "summary": "fresh"}])
    out = json.loads(ev.hermes_events_query(source="audit", hermes_root=hermes_root))
    assert out["count_total"] == 1
    assert out["events"][0]["summary"] == "fresh"
    assert out["retention_max_age_days"] == 1


def test_max_age_invalid_falls_back_to_default(hermes_root, monkeypatch):
    monkeypatch.setenv(ev.EVENTS_MAX_AGE_DAYS_ENV, "not-a-number")
    assert ev._max_age_days() == ev.DEFAULT_MAX_AGE_DAYS


def test_max_age_clamped_to_bounds(hermes_root, monkeypatch):
    monkeypatch.setenv(ev.EVENTS_MAX_AGE_DAYS_ENV, "0")
    assert ev._max_age_days() == 1
    monkeypatch.setenv(ev.EVENTS_MAX_AGE_DAYS_ENV, "999999")
    assert ev._max_age_days() == 3650


def test_allowlist_ignores_unknown_entries(hermes_root, monkeypatch):
    _seed_all_sources(hermes_root)
    monkeypatch.setenv(ev.EVENTS_ALLOWED_SOURCES_ENV, "swarm,bogus")
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root))
    sources = {e["source"] for e in out["events"]}
    assert sources <= {"swarm"}
    assert out["sources_allowed"] == ["swarm"]


def test_allowlist_restricts_tail(hermes_root, monkeypatch):
    _seed_all_sources(hermes_root)
    monkeypatch.setenv(ev.EVENTS_ALLOWED_SOURCES_ENV, "swarm,codex")
    out = json.loads(ev.hermes_events_tail(limit=100, hermes_root=hermes_root))
    sources = {e["source"] for e in out["events"]}
    assert sources <= {"swarm", "codex"}
    assert set(out["sources_allowed"]) == {"swarm", "codex"}


def test_query_by_subject_id_returns_ordered_timeline(hermes_root):
    _seed_all_sources(hermes_root)
    out = json.loads(ev.hermes_events_query(subject_id="sw-1", hermes_root=hermes_root))
    assert out["success"] is True
    assert all("sw-1" in str(e.get("subject_id") or "") for e in out["events"])
    assert out["events"][0]["source"] == "swarm"


def test_query_by_kind_filters(hermes_root):
    _seed_all_sources(hermes_root)
    out = json.loads(ev.hermes_events_query(kind="job_run", hermes_root=hermes_root))
    assert out["success"] is True
    assert all(e["kind"] == "job_run" for e in out["events"])
    assert all(e["source"] == "cron" for e in out["events"])


def test_limit_caps_and_truncation_flag(hermes_root):
    for i in range(10):
        _write_audit(hermes_root, [{"timestamp": f"2026-08-15T10:{i:02d}:00+00:00", "tool": "hermes_operator_status", "profile": "dev", "success": True, "summary": f"event {i}"}])
    out = json.loads(ev.hermes_events_query(source="audit", limit=3, hermes_root=hermes_root))
    assert out["count_returned"] == 3
    assert out["count_total"] == 10
    assert out["truncated"] is True


def test_events_surface_is_read_only(hermes_root):
    """The surface must never create or mutate stores."""
    _seed_all_sources(hermes_root)
    before = {
        "swarm": sorted(p.name for p in (hermes_root / "swarm-workflows").iterdir()),
        "codex": sorted(p.name for p in (hermes_root / "codex-jobs").iterdir()),
    }
    json.loads(ev.hermes_events_query(hermes_root=hermes_root))
    json.loads(ev.hermes_events_tail(hermes_root=hermes_root))
    assert sorted(p.name for p in (hermes_root / "swarm-workflows").iterdir()) == before["swarm"]
    assert sorted(p.name for p in (hermes_root / "codex-jobs").iterdir()) == before["codex"]
    # No new DBs/files created.
    assert not (hermes_root / "kanban" / "boards" / "default" / "kanban.db.bak").exists()


def test_events_tail_bounded(hermes_root):
    _seed_all_sources(hermes_root)
    out = json.loads(ev.hermes_events_tail(limit=2, hermes_root=hermes_root))
    assert out["count_returned"] <= 2
    assert out["truncated"] is True


def test_events_calls_are_audited(hermes_root, tmp_path):
    """Every events call writes an audit record (S6 per-tool audit wiring)."""
    import operator_policy as op

    log = tmp_path / "audit.jsonl"
    op.set_audit_log_override(log)
    try:
        _seed_all_sources(hermes_root)
        json.loads(ev.hermes_events_query(hermes_root=hermes_root))
        json.loads(ev.hermes_events_tail(hermes_root=hermes_root))
        records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        tools = {r["tool"] for r in records}
        assert "hermes_events_query" in tools
        assert "hermes_events_tail" in tools
        assert all(r["changed"] is False for r in records)  # read-only
    finally:
        op.set_audit_log_override(None)


# ── rm-079: boundary filtering on both event surfaces ─────────────────────


def test_query_and_tail_warn_and_report_only_allowed_sources(hermes_root, monkeypatch):
    """Both surfaces filter once at the boundary, warn, and report truthfully.

    Pre-fix, only the query path warned (about a subset computed just for the
    warning), the tail path never warned, and both envelopes listed sources
    in ``sources_queried`` that the allowlist had actually prevented from
    being queried.
    """
    _seed_all_sources(hermes_root)
    monkeypatch.setenv(ev.EVENTS_ALLOWED_SOURCES_ENV, "audit")

    tail = json.loads(ev.hermes_events_tail(limit=5, hermes_root=hermes_root))
    assert tail["sources_queried"] == ["audit"]
    assert any("dropped by allowlist" in w for w in tail["warnings"])

    query = json.loads(ev.hermes_events_query(limit=5, hermes_root=hermes_root))
    assert query["sources_queried"] == ["audit"]  # truthful: not EVENT_SOURCES
    assert query["sources_allowed"] == ["audit"]
    assert any("dropped by allowlist" in w for w in query["warnings"])


def test_query_and_tail_do_not_warn_without_allowlist(hermes_root, monkeypatch):
    """No allowlist restriction -> no warning noise on either surface."""
    _seed_all_sources(hermes_root)
    monkeypatch.delenv(ev.EVENTS_ALLOWED_SOURCES_ENV, raising=False)

    tail = json.loads(ev.hermes_events_tail(limit=5, hermes_root=hermes_root))
    assert set(tail["sources_queried"]) == set(ev.EVENT_SOURCES)
    assert tail["warnings"] == []

    query = json.loads(ev.hermes_events_query(limit=5, hermes_root=hermes_root))
    assert set(query["sources_queried"]) == set(ev.EVENT_SOURCES)
    assert query["warnings"] == []


# ---------------------------------------------------------------------------
# rm-104: audit source keeps the NEWEST records (bounded, sibling semantics)
# ---------------------------------------------------------------------------


def _audit_row(i: int, ts: str) -> dict:
    return {
        "timestamp": ts,
        "profile": "dev",
        "tool": "hermes_cron_list",
        "task_id": f"task-{i}",
        "success": True,
        "summary": f"record {i}",
    }


def test_audit_source_keeps_newest_window_over_cap(hermes_root: Path):
    """With more audit rows than MAX_PER_SOURCE, the visible window is the
    latest one (rm-104 regression: the old top-down break kept the OLDEST
    500, so the newest events were invisible and count_total undercounted
    every in-window query)."""
    rows = [
        _audit_row(i, (datetime(2026, 9, 29) + timedelta(days=0.001 * i)).isoformat())
        for i in range(600)
    ]
    _write_audit(hermes_root, rows)

    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root, source="audit", limit=20))
    assert out["success"] is True
    events = out["events"]
    assert len(events) == 20
    # Newest visible record is the last one written, not record 499.
    assert events[0]["summary"] == "record 599"
    # count_total reflects the returned window's population (600 written,
    # newest 500 kept) — not 400 of 600 counted against the oldest window.
    assert out["count_total"] == ev.MAX_PER_SOURCE
    # Distinct, stable event ids across the cap boundary.
    assert len({e["event_id"] for e in events}) == 20


def test_audit_source_full_cap_window_is_contiguous_newest(hermes_root: Path):
    rows = [_audit_row(i, (datetime(2026, 9, 29) + timedelta(days=0.001 * i)).isoformat()) for i in range(600)]
    _write_audit(hermes_root, rows)

    # MAX_QUERY_LIMIT clamps the page size; the full kept window is visible
    # through count_total.
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root, source="audit", limit=ev.MAX_QUERY_LIMIT))
    events = out["events"]
    assert len(events) == ev.MAX_QUERY_LIMIT
    assert out["count_total"] == ev.MAX_PER_SOURCE
    summaries = [e["summary"] for e in events]
    # Newest-first ordering from the newest record down; the oldest side
    # beyond the cap (records < 100) is the dropped side, not the newest.
    assert summaries[0] == "record 599"
    assert summaries[-1] == "record 400"
    assert "record 399" not in summaries


def test_audit_cap_warning_present_at_cap_and_absent_below(hermes_root: Path):
    below = [_audit_row(i, (datetime(2026, 9, 29) + timedelta(days=0.001 * i)).isoformat()) for i in range(10)]
    _write_audit(hermes_root, below)
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root, source="audit", limit=5))
    assert out["success"] is True
    assert out["count_total"] == 10
    assert all("capped" not in w for w in out["warnings"])

    ev._cache.clear()
    at_cap = below + [
        _audit_row(i, (datetime(2026, 10, 1) + timedelta(days=0.001 * i)).isoformat())
        for i in range(ev.MAX_PER_SOURCE)
    ]
    _write_audit(hermes_root, at_cap)
    out2 = json.loads(ev.hermes_events_query(hermes_root=hermes_root, source="audit", limit=5))
    assert any(f"capped at newest {ev.MAX_PER_SOURCE}" in w for w in out2["warnings"]), out2["warnings"]


def test_events_tail_sees_newest_audit_rows(hermes_root: Path):
    rows = [_audit_row(i, (datetime(2026, 9, 29) + timedelta(days=0.001 * i)).isoformat()) for i in range(600)]
    _write_audit(hermes_root, rows)

    out = json.loads(ev.hermes_events_tail(hermes_root=hermes_root, limit=3))
    assert out["success"] is True
    summaries = [e["summary"] for e in out["events"]]
    assert summaries[0] == "record 599"
    assert set(summaries) == {"record 599", "record 598", "record 597"}


def test_audit_since_filter_applies_within_newest_window(hermes_root: Path):
    rows = [_audit_row(i, (datetime(2026, 9, 29) + timedelta(days=0.001 * i)).isoformat()) for i in range(600)]
    _write_audit(hermes_root, rows)

    since = (datetime(2026, 9, 29) + timedelta(days=0.55)).isoformat()
    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root, source="audit", since=since, limit=ev.MAX_QUERY_LIMIT))
    events = out["events"]
    # Newest 500 kept are records 100..599; the since cutoff (~record 550)
    # lands inside that window, so all returned rows satisfy it.
    assert events, "in-window rows must be visible"
    assert all(e["ts"] >= since for e in events)
    assert events[0]["summary"] == "record 599"


def test_audit_malformed_lines_do_not_break_newest_scan(hermes_root: Path):
    with open(hermes_root / "logs" / "hermes_gpt_operator_audit.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(_audit_row(0, "2026-09-29T00:00:00")) + "\n")
        fh.write("not json at all\n")
        fh.write(json.dumps(_audit_row(1, "2026-09-29T00:01:00")) + "\n")
        fh.write(json.dumps(["a", "list"]) + "\n")
        fh.write(json.dumps(_audit_row(2, "2026-09-29T00:02:00")) + "\n")

    out = json.loads(ev.hermes_events_query(hermes_root=hermes_root, source="audit", limit=10))
    summaries = [e["summary"] for e in out["events"]]
    assert summaries == ["record 2", "record 1", "record 0"]
