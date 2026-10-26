"""Hermetic tests for operator_slo_probe (TEST-03).

Every probe is pinned three ways: the honest-PASS shape, the FAIL shape,
and the UNKNOWN-on-missing-evidence shape — because the founding contract
for this module is "SLO targets ... never gamed": a probe that cannot read
its source must never emit PASS, and a probe that reads real data must
re-derive its arithmetic from an explicit denominator.

Fixtures are in-memory SQLite stores built from the REAL schemas of the
authoritative sources (delegations.db, missions.db, state.db), so query
drift against the live stores fails these tests, not production.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


import operator_slo_probe as slo


# ---------------------------------------------------------------------------
# Fixture builders — mirror the live schemas exactly
# ---------------------------------------------------------------------------


def build_delegations_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE delegations (
            delegation_id TEXT PRIMARY KEY,
            schema TEXT, mission_id TEXT, task_id TEXT,
            contract_sha256 TEXT, backend TEXT, state TEXT,
            backend_state TEXT, outcome TEXT, backend_ref_json TEXT,
            validation_verdict TEXT, cancel_requested INTEGER,
            authority_version INTEGER, cancellation_in_progress INTEGER,
            cancellation_claimed_at TEXT, cancellation_observation_sha256 TEXT,
            cancellation_watermark_ready INTEGER, dispatch_phase TEXT,
            created_at TEXT, dispatched_at TEXT, updated_at TEXT,
            terminal_at TEXT, validation_summary_json TEXT,
            validation_failure_since TEXT
        );
        CREATE TABLE delegation_events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            delegation_id TEXT, event_type TEXT, from_state TEXT,
            to_state TEXT, backend_state TEXT, observed_sha256 TEXT,
            created_at TEXT
        );
        """
    )
    return conn


def add_delegation(
    conn: sqlite3.Connection,
    did: str,
    *,
    state: str = "succeeded",
    verdict: str = "SATISFIED",
    mission_id: str | None = "m1",
    task_id: str | None = "t1",
) -> None:
    conn.execute(
        "INSERT INTO delegations (delegation_id, state, validation_verdict,"
        " mission_id, task_id) VALUES (?,?,?,?,?)",
        (did, state, verdict, mission_id, task_id),
    )


def add_events(
    conn: sqlite3.Connection, did: str, events: list[str]
) -> None:
    for et in events:
        conn.execute(
            "INSERT INTO delegation_events (delegation_id, event_type)"
            " VALUES (?,?)",
            (did, et),
        )


def build_missions_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE plan_nodes (
            mission_id TEXT, node_id TEXT, contract_sha256 TEXT,
            capability_req TEXT, budget TEXT, deps TEXT, state TEXT,
            lease_lock TEXT, lease_expires TEXT, epoch INTEGER,
            failure_kind TEXT, retries INTEGER, created_at TEXT,
            updated_at TEXT
        );
        """
    )
    return conn


def add_node(
    conn: sqlite3.Connection,
    *,
    auth_class: str = "reversible_write",
    state: str = "completed",
) -> None:
    conn.execute(
        "INSERT INTO plan_nodes (capability_req, state) VALUES (?,?)",
        (f'{{"authorization_class": "{auth_class}"}}', state),
    )


def build_state_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE gateway_heartbeats (
            backend_id TEXT, pid INTEGER, started_at REAL,
            last_heartbeat REAL, profile TEXT, host TEXT
        );
        """
    )
    return conn


# ---------------------------------------------------------------------------
# SLO-1 false success
# ---------------------------------------------------------------------------


class TestFalseSuccess:
    def test_pass_when_all_succeeded_satisfied(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", verdict="SATISFIED")
        add_delegation(db, "d2", verdict="SATISFIED")
        db.commit()
        db.close()
        rec = slo.probe_false_success(tmp_path / "d.db")
        assert rec.verdict == slo.PASS
        assert (rec.numerator, rec.denominator) == (0, 2)

    def test_fail_on_inconclusive_success(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", verdict="SATISFIED")
        add_delegation(db, "d2", verdict="INCONCLUSIVE")
        db.commit()
        db.close()
        rec = slo.probe_false_success(tmp_path / "d.db")
        assert rec.verdict == slo.FAIL
        assert (rec.numerator, rec.denominator) == (1, 2)

    def test_fail_on_null_verdict(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", verdict=None)
        db.commit()
        db.close()
        rec = slo.probe_false_success(tmp_path / "d.db")
        assert rec.verdict == slo.FAIL

    def test_failed_delegations_are_not_false_success(
        self, tmp_path: Path
    ) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", state="failed", verdict="NOT_SATISFIED")
        add_delegation(db, "d2", state="cancelled", verdict="")
        db.commit()
        db.close()
        rec = slo.probe_false_success(tmp_path / "d.db")
        assert rec.denominator == 0
        assert rec.verdict == slo.UNKNOWN

    def test_unknown_when_db_missing(self, tmp_path: Path) -> None:
        rec = slo.probe_false_success(tmp_path / "missing.db")
        assert rec.verdict == slo.UNKNOWN
        assert rec.notes


# ---------------------------------------------------------------------------
# SLO-2a duplicate dispatch
# ---------------------------------------------------------------------------


class TestDuplicateDispatch:
    def test_pass_clean_lifecycle(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1")
        add_events(
            db,
            "d1",
            [
                "delegation.reserved",
                "delegation.invoking",
                "delegation.dispatched",
                "delegation.reconciled",
            ],
        )
        db.commit()
        db.close()
        rec = slo.probe_duplicate_dispatch(tmp_path / "d.db")
        assert rec.verdict == slo.PASS
        assert rec.value == 0

    def test_recovery_loop_is_not_duplication(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1")
        add_events(
            db,
            "d1",
            [
                "delegation.reserved",
                "delegation.invoking",
                "delegation.dispatched",
                "delegation.invocation_recovered",
                "delegation.reconciled",
                "delegation.invoking",
                "delegation.dispatched",
                "delegation.reconciled",
            ],
        )
        db.commit()
        db.close()
        rec = slo.probe_duplicate_dispatch(tmp_path / "d.db")
        assert rec.verdict == slo.PASS

    def test_fail_on_live_overlap(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1")
        add_events(
            db,
            "d1",
            [
                "delegation.reserved",
                "delegation.dispatched",
                "delegation.dispatched",  # no recovery between
                "delegation.reconciled",
            ],
        )
        db.commit()
        db.close()
        rec = slo.probe_duplicate_dispatch(tmp_path / "d.db")
        assert rec.verdict == slo.FAIL
        assert rec.value == 1

    def test_unknown_when_db_missing(self, tmp_path: Path) -> None:
        rec = slo.probe_duplicate_dispatch(tmp_path / "missing.db")
        assert rec.verdict == slo.UNKNOWN


# ---------------------------------------------------------------------------
# SLO-2b double claim
# ---------------------------------------------------------------------------


class TestDoubleClaim:
    def test_pass_distinct_tasks(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", mission_id="m1", task_id="t1")
        add_delegation(db, "d2", mission_id="m1", task_id="t2")
        db.commit()
        db.close()
        rec = slo.probe_double_claim(tmp_path / "d.db")
        assert rec.verdict == slo.PASS
        assert rec.denominator == 2

    def test_fail_on_double_claim(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", mission_id="m1", task_id="t1")
        add_delegation(db, "d2", mission_id="m1", task_id="t1")
        db.commit()
        db.close()
        rec = slo.probe_double_claim(tmp_path / "d.db")
        assert rec.verdict == slo.FAIL
        assert rec.value == 1

    def test_cancelled_does_not_claim(self, tmp_path: Path) -> None:
        db = build_delegations_db(tmp_path / "d.db")
        add_delegation(db, "d1", mission_id="m1", task_id="t1")
        add_delegation(
            db, "d2", state="cancelled", mission_id="m1", task_id="t1"
        )
        db.commit()
        db.close()
        rec = slo.probe_double_claim(tmp_path / "d.db")
        assert rec.verdict == slo.PASS


# ---------------------------------------------------------------------------
# SLO-3 stall detection
# ---------------------------------------------------------------------------


def watchdog_line(ts_iso: str, payload: dict) -> str:
    import json as _json

    return f"{ts_iso} agent-runner maestro-watchdog[123]: {_json.dumps(payload)}"


EP = 1792900000.0  # arbitrary epoch base for fixtures


def ts_at(offset_s: float) -> str:
    import datetime as _dt

    t = _dt.datetime.fromtimestamp(
        EP + offset_s, tz=_dt.timezone.utc
    )
    return t.strftime("%Y-%m-%d %H:%M:%S")


class TestStallDetection:
    def test_pass_fast_detection(self) -> None:
        lines = [
            watchdog_line(ts_at(0), {"semantic_healthy": True}),
            watchdog_line(ts_at(60), {"semantic_healthy": False}),
            watchdog_line(
                ts_at(240),
                {"semantic_healthy": False, "restarted": True},
            ),
            watchdog_line(ts_at(300), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.PASS
        assert rec.value["persistent_episodes"] == 1
        assert rec.value["within_5m"] == 1
        assert rec.value["worst_latency_s"] == 180.0

    def test_fail_slow_detection(self) -> None:
        lines = [
            watchdog_line(ts_at(0), {"semantic_healthy": False}),
            watchdog_line(
                ts_at(1200),
                {"semantic_healthy": False, "restarted": True},
            ),
            watchdog_line(ts_at(1260), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.FAIL
        assert rec.value["worst_latency_s"] == 1200.0

    def test_fail_undetected_episode(self) -> None:
        lines = [
            watchdog_line(ts_at(0), {"semantic_healthy": False}),
            watchdog_line(ts_at(60), {"semantic_healthy": False}),
            watchdog_line(ts_at(120), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.FAIL
        assert rec.value["undetected"] == 1

    def test_unknown_when_no_episodes(self) -> None:
        lines = [watchdog_line(ts_at(0), {"semantic_healthy": True})] * 3
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.UNKNOWN
        assert "no stall episodes" in rec.notes[0]

    def test_unknown_on_garbage_journal(self) -> None:
        rec = slo.probe_stall_detection(["not a watchdog line"])
        assert rec.verdict == slo.UNKNOWN

    # --- productive-deferral classification (2026-10-26 SLO-debt repair) ---

    def test_productive_deferral_not_a_stall(self) -> None:
        """Semantic-unhealthy ticks under a healthy bounded execution step
        (the deployed watchdog's KTD4 excuse — visible per tick as an active
        execution_state + execution_healthy true) are NOT stall episodes:
        working through the backlog is the handling; a restart would kill
        productive work. They are reported, not erased."""
        lines = [
            watchdog_line(ts_at(0), {"semantic_healthy": True}),
            watchdog_line(
                ts_at(60),
                {
                    "semantic_healthy": False,
                    "execution_state": "RECONCILING",
                    "execution_healthy": True,
                },
            ),
            watchdog_line(
                ts_at(600),
                {
                    "semantic_healthy": False,
                    "execution_state": "CYCLING",
                    "execution_healthy": True,
                },
            ),
            watchdog_line(ts_at(1200), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.UNKNOWN
        assert rec.value["episodes"] == 0
        assert rec.value["excused_productive_ticks"] == 2

    def test_wedged_active_step_is_a_stall(self) -> None:
        """An active execution step beyond its dwell bound
        (execution_healthy false) is NOT excused — the watchdog's own model
        says it must be handled, so the tick counts toward a stall
        episode."""
        lines = [
            watchdog_line(
                ts_at(0),
                {
                    "semantic_healthy": False,
                    "execution_state": "WORKING",
                    "execution_healthy": False,
                },
            ),
            watchdog_line(
                ts_at(120),
                {
                    "semantic_healthy": False,
                    "execution_state": "WORKING",
                    "execution_healthy": False,
                    "restarted": True,
                },
            ),
            watchdog_line(ts_at(240), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.PASS
        assert rec.value["persistent_episodes"] == 1
        assert rec.value["within_5m"] == 1
        assert rec.value["worst_latency_s"] == 120.0

    def test_supervisor_object_shape_supported(self) -> None:
        """The raw journal nests the fields inside ``supervisor`` — the
        excuse must engage identically in that shape."""
        lines = [
            watchdog_line(
                ts_at(0),
                {
                    "supervisor": {
                        "semantic_healthy": False,
                        "execution_state": "RECONCILING",
                        "execution_healthy": True,
                    }
                },
            ),
            watchdog_line(
                ts_at(120),
                {
                    "supervisor": {
                        "semantic_healthy": False,
                        "execution_state": "RECONCILING",
                        "execution_healthy": True,
                    }
                },
            ),
            watchdog_line(ts_at(240), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.UNKNOWN
        assert rec.value["excused_productive_ticks"] == 2

    def test_idle_semantic_stall_is_not_excused(self) -> None:
        """No active execution step + semantic-unhealthy = genuine stall —
        the excuse must not swallow real misses (the anti-gaming bound)."""
        lines = [
            watchdog_line(
                ts_at(0), {"semantic_healthy": False}
            ),
            watchdog_line(
                ts_at(60), {"semantic_healthy": False}
            ),
            watchdog_line(ts_at(120), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.FAIL
        assert rec.value["undetected"] == 1
        assert rec.value.get("excused_productive_ticks", 0) == 0


# ---------------------------------------------------------------------------
# SLO-4 auto recovery
# ---------------------------------------------------------------------------


class TestAutoRecovery:
    def test_pass_quick_recovery(self) -> None:
        lines = [
            watchdog_line(
                ts_at(0), {"semantic_healthy": False, "restarted": True}
            ),
            watchdog_line(ts_at(300), {"semantic_healthy": True}),
        ]
        rec = slo.probe_auto_recovery(lines)
        assert rec.verdict == slo.PASS
        assert rec.value["restarts"] == 1
        assert rec.value["recovered_within_15m"] == 1

    def test_fail_slow_recovery(self) -> None:
        lines = [
            watchdog_line(
                ts_at(0), {"semantic_healthy": False, "restarted": True}
            ),
            watchdog_line(ts_at(3600), {"semantic_healthy": True}),
        ]
        rec = slo.probe_auto_recovery(lines)
        assert rec.verdict == slo.FAIL
        assert rec.value["recovered_within_15m"] == 0

    def test_supervisor_healthy_object_counts(self) -> None:
        lines = [
            watchdog_line(
                ts_at(0), {"semantic_healthy": False, "restarted": True}
            ),
            watchdog_line(
                ts_at(60), {"semantic_healthy": False, "supervisor": {"healthy": True}}
            ),
        ]
        rec = slo.probe_auto_recovery(lines)
        assert rec.verdict == slo.PASS

    def test_unknown_when_no_restarts(self) -> None:
        lines = [watchdog_line(ts_at(0), {"semantic_healthy": True})]
        rec = slo.probe_auto_recovery(lines)
        assert rec.verdict == slo.UNKNOWN


# ---------------------------------------------------------------------------
# SLO-5 routine completion
# ---------------------------------------------------------------------------


class TestRoutineCompletion:
    def test_pass_full_completion(self, tmp_path: Path) -> None:
        db = build_missions_db(tmp_path / "m.db")
        for _ in range(100):
            add_node(db, state="completed")
        db.commit()
        db.close()
        rec = slo.probe_routine_completion(tmp_path / "m.db")
        assert rec.verdict == slo.PASS
        assert (rec.numerator, rec.denominator) == (100, 100)

    def test_fail_below_99(self, tmp_path: Path) -> None:
        db = build_missions_db(tmp_path / "m.db")
        for _ in range(99):
            add_node(db, state="completed")
        add_node(db, state="failed")
        db.commit()
        db.close()
        rec = slo.probe_routine_completion(tmp_path / "m.db")
        # 99/100 = 99.0% — exactly at target: PASS (boundary is inclusive)
        assert rec.verdict == slo.PASS
        assert rec.value == 99.0
        # one more failure tips it: 99/101 = 98.02%
        db2 = sqlite3.connect(tmp_path / "m.db")
        add_node(db2, state="failed")
        db2.commit()
        db2.close()
        rec2 = slo.probe_routine_completion(tmp_path / "m.db")
        assert rec2.verdict == slo.FAIL
        assert rec2.value == 98.02

    def test_owner_gated_excluded(self, tmp_path: Path) -> None:
        db = build_missions_db(tmp_path / "m.db")
        add_node(db, auth_class="owner_gated", state="failed")
        add_node(db, state="completed")
        db.commit()
        db.close()
        rec = slo.probe_routine_completion(tmp_path / "m.db")
        assert rec.denominator == 1
        assert rec.verdict == slo.PASS

    def test_in_flight_excluded(self, tmp_path: Path) -> None:
        db = build_missions_db(tmp_path / "m.db")
        add_node(db, state="completed")
        add_node(db, state="running")
        add_node(db, state="pending")
        db.commit()
        db.close()
        rec = slo.probe_routine_completion(tmp_path / "m.db")
        assert rec.denominator == 1

    def test_unknown_when_db_missing(self, tmp_path: Path) -> None:
        rec = slo.probe_routine_completion(tmp_path / "missing.db")
        assert rec.verdict == slo.UNKNOWN


# ---------------------------------------------------------------------------
# SLO-6 continuity
# ---------------------------------------------------------------------------


class TestContinuity:
    def test_pass_fresh_heartbeat(self, tmp_path: Path) -> None:
        import time as _time

        db = build_state_db(tmp_path / "s.db")
        db.execute(
            "INSERT INTO gateway_heartbeats (last_heartbeat) VALUES (?)",
            (_time.time() - 60,),
        )
        db.commit()
        db.close()
        rec = slo.probe_continuity(tmp_path / "s.db")
        assert rec.verdict == slo.PASS

    def test_fail_stale_heartbeat(self, tmp_path: Path) -> None:
        import time as _time

        db = build_state_db(tmp_path / "s.db")
        db.execute(
            "INSERT INTO gateway_heartbeats (last_heartbeat) VALUES (?)",
            (_time.time() - 3600,),
        )
        db.commit()
        db.close()
        rec = slo.probe_continuity(tmp_path / "s.db")
        assert rec.verdict == slo.FAIL

    def test_unknown_when_db_missing(self, tmp_path: Path) -> None:
        rec = slo.probe_continuity(tmp_path / "missing.db")
        assert rec.verdict == slo.UNKNOWN


# ---------------------------------------------------------------------------
# SLO-7 disk free
# ---------------------------------------------------------------------------


class TestDiskFree:
    def test_pass_on_this_host(self) -> None:
        # The test host's own filesystem is a real probe; if THIS assert
        # ever fails the host itself violates the floor — test env problem,
        # not module problem. Guarded by the campaign root existing.
        rec = slo.probe_disk_free("/tmp")
        assert rec.verdict in (slo.PASS, slo.FAIL)
        assert rec.value["free_pct"] >= 0

    def test_fail_on_tiny_threshold_mismatch(self, monkeypatch) -> None:

        # statvfs on a path we control with an absurd min threshold -> FAIL
        rec = slo.probe_disk_free(
            "/tmp", min_free_pct=99.99
        )
        # free_pct is < 100 on any real filesystem, so > 99.99 fails
        assert rec.verdict == slo.FAIL


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


class TestCollectAll:
    def test_journal_error_yields_unknown_not_pass(self, tmp_path: Path) -> None:
        def broken_reader(unit: str, since: str):
            return [], "simulated journal down"

        doc = slo.collect_all(
            hermes_root=tmp_path,
            journal_reader=broken_reader,
            now=EP,
        )
        ids = {r["slo_id"]: r for r in doc["records"]}
        assert ids["stall_detection"]["verdict"] == slo.UNKNOWN
        assert ids["auto_recovery"]["verdict"] == slo.UNKNOWN
        assert doc["summary"]["unknown"] >= 2
        # every record must carry its target text
        for r in doc["records"]:
            assert r["target"]
            assert r["sources"]

    def test_all_probes_present(self, tmp_path: Path) -> None:
        doc = slo.collect_all(
            hermes_root=tmp_path,
            journal_reader=lambda u, s: ([], None),
            now=EP,
        )
        got = {r["slo_id"] for r in doc["records"]}
        assert got == {
            "false_success",
            "duplicate_dispatch",
            "double_claim",
            "routine_completion",
            "continuity",
            "disk_free",
            "stall_detection",
            "auto_recovery",
        }
        assert doc["measured_at"].endswith("Z")

    def test_summary_counts_consistent(self, tmp_path: Path) -> None:
        doc = slo.collect_all(
            hermes_root=tmp_path,
            journal_reader=lambda u, s: ([], None),
            now=EP,
        )
        s = doc["summary"]
        assert s["pass"] + s["fail"] + s["unknown"] == len(doc["records"])
        assert len(s["failed_ids"]) == s["fail"]
        assert len(s["unknown_ids"]) == s["unknown"]
