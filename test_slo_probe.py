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

    def test_idle_stall_engaged_within_bound_is_detected(self) -> None:
        """The 2026-11-08 18:04:34Z live shape: two IDLE semantic-unhealthy
        ticks (nothing working the backlog), then the supervisor ENGAGES
        (CYCLING, execution_healthy) 135s after the run closed. Engagement
        IS the handling under the deployed watchdog's KTD4 model — a
        restart there would kill productive work — so the episode is
        detected-and-handled (latency 135s <= 5m), not undetected."""
        lines = [
            watchdog_line(
                ts_at(0),
                {"semantic_healthy": True},
            ),
            # stall run: IDLE, execution not healthy-working the backlog
            watchdog_line(
                ts_at(60),
                {"supervisor": {"semantic_healthy": False, "execution_state": "IDLE"}},
            ),
            watchdog_line(
                ts_at(120),
                {"supervisor": {"semantic_healthy": False, "execution_state": "IDLE"}},
            ),
            # engagement tick: healthy-by-model (active state, excused)
            watchdog_line(
                ts_at(255),
                {"supervisor": {"semantic_healthy": False, "execution_state": "CYCLING", "execution_healthy": True}},
            ),
            watchdog_line(ts_at(320), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.PASS, rec.value
        assert rec.value["persistent_episodes"] == 1
        assert rec.value["within_5m"] == 1
        assert rec.value["undetected"] == 0
        assert rec.value["worst_latency_s"] == 195.0
        assert rec.value["excused_productive_ticks"] == 1

    def test_engagement_beyond_bound_is_still_undetected(self) -> None:
        """An engagement that only arrives after the 900s SLO bound is NOT
        a detection credit — the episode stays undetected (FAIL), because
        the directive bound is 15m worst-case and 5m for 95%."""
        lines = [
            watchdog_line(
                ts_at(0),
                {"supervisor": {"semantic_healthy": False, "execution_state": "IDLE"}},
            ),
            watchdog_line(
                ts_at(60),
                {"supervisor": {"semantic_healthy": False, "execution_state": "IDLE"}},
            ),
            watchdog_line(
                ts_at(1200),
                {"supervisor": {"semantic_healthy": False, "execution_state": "CYCLING", "execution_healthy": True}},
            ),
            watchdog_line(ts_at(1260), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.FAIL
        assert rec.value["undetected"] == 1

    def test_active_run_still_needs_explicit_restart(self) -> None:
        """A stall run whose ticks were already ACTIVE (wedged beyond dwell)
        is not credited by mere continued activity — only a restart or the
        run's own recovery counts; here neither fires, so undetected."""
        lines = [
            watchdog_line(
                ts_at(0),
                {"supervisor": {"semantic_healthy": False, "execution_state": "CYCLING", "execution_healthy": False}},
            ),
            watchdog_line(
                ts_at(60),
                {"supervisor": {"semantic_healthy": False, "execution_state": "CYCLING", "execution_healthy": False}},
            ),
            watchdog_line(
                ts_at(120),
                {"supervisor": {"semantic_healthy": False, "execution_state": "CYCLING", "execution_healthy": True}},
            ),
            watchdog_line(ts_at(180), {"semantic_healthy": True}),
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

    def test_explicit_live_idle_pacing_is_reported_not_a_stall(self) -> None:
        """A healthy idle pacing interval must carry an explicit watchdog
        exemption receipt; semantic staleness alone cannot imply pacing."""
        paced = {"semantic_healthy": False, "execution_state": "IDLE",
                 "execution_healthy": True, "healthy": True,
                 "pacing_exempted": True, "operator_lane_stalled": None}
        lines = [
            watchdog_line(ts_at(0), {"supervisor": paced}),
            watchdog_line(ts_at(60), {"supervisor": paced}),
            watchdog_line(ts_at(120), {"semantic_healthy": True}),
        ]
        rec = slo.probe_stall_detection(lines)
        assert rec.verdict == slo.UNKNOWN
        assert rec.value["episodes"] == 0
        assert rec.value["excused_pacing_ticks"] == 2
        assert rec.value["excused_productive_ticks"] == 0

    def test_pacing_receipt_cannot_hide_unhealthy_or_wedged_idle(self) -> None:
        """A forged or stale exemption must not hide an undetected stall."""
        for bad in ({"healthy": False}, {"execution_healthy": False},
                    {"pacing_exempted": False}, {"operator_lane_stalled": {"id": "x"}}):
            tick = {"semantic_healthy": False, "execution_state": "IDLE",
                    "execution_healthy": True, "healthy": True,
                    "pacing_exempted": True, "operator_lane_stalled": None}
            tick.update(bad)
            lines = [
                watchdog_line(ts_at(0), {"supervisor": tick}),
                watchdog_line(ts_at(60), {"supervisor": tick}),
                watchdog_line(ts_at(120), {"semantic_healthy": True}),
            ]
            rec = slo.probe_stall_detection(lines)
            assert rec.verdict == slo.FAIL
            assert rec.value["undetected"] == 1

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


# ---------------------------------------------------------------------------
# Regression: journalctl -o short-iso emits +HHMM offsets (no colon); Python
# <=3.10 datetime.fromisoformat rejects them, silently parsing the ENTIRE
# live journal to 0 ticks -> fabricated "no stall episodes" UNKNOWN. Found
# live 2026-11-04: 252/252 journal lines dropped on /usr/bin/python3 3.10.
# ---------------------------------------------------------------------------


class TestParseWatchdogJournalOffsetCompat:
    def _line(self, ts: str, payload: dict | None = None) -> str:
        import json as _json

        body = _json.dumps(payload or {"healthy": True})
        return f"{ts} agent-runner maestro-watchdog[2356306]: {body}"

    def test_short_iso_plus_hhmm_offset_parses_on_all_pythons(self) -> None:
        lines = [
            self._line("2026-11-04T12:28:13+0000"),
            self._line("2026-11-04T12:28:43+0000"),
        ]
        ticks = slo.parse_watchdog_journal(lines)
        assert len(ticks) == 2, (
            "journalctl -o short-iso +HHMM offsets must parse on every "
            "supported interpreter (py<=3.10 fromisoformat rejects them)"
        )
        assert ticks[0]["__ts"] == 1793795293.0
        assert ticks[1]["__ts"] - ticks[0]["__ts"] == 30.0

    def test_negative_hhmm_offset_parses(self) -> None:
        ticks = slo.parse_watchdog_journal(
            [self._line("2026-11-04T07:28:13-0500")]
        )
        assert len(ticks) == 1
        assert ticks[0]["__ts"] == 1793795293.0

    def test_colon_offsets_and_naive_still_parse(self) -> None:
        # Pre-existing accepted shapes keep parsing: short-iso with colon
        # offsets, and naive (short) lines which default to UTC.
        colon = slo.parse_watchdog_journal(
            [self._line("2026-11-04T12:28:13+00:00")]
        )
        naive = slo.parse_watchdog_journal(
            [self._line("2026-11-04 12:28:13")]
        )
        assert len(colon) == 1 and len(naive) == 1
        assert colon[0]["__ts"] == naive[0]["__ts"] == 1793795293.0

    def test_malformed_timestamp_still_skipped_silently(self) -> None:
        # Unparseable/non-matching lines are skipped, never fatal (pre-
        # existing contract); garbage payload JSON likewise.
        ticks = slo.parse_watchdog_journal(
            [
                self._line("2026-11-04T12:28:13+0000"),
                "2026-11-04T99:99:99+0000 agent-runner maestro-watchdog[1]: {}",
                "not a journal line at all",
                self._line("2026-11-04T12:29:13+0000"),
            ]
        )
        assert len(ticks) == 2

    def test_live_shape_roundtrip_count(self) -> None:
        # Byte-shape captured from journalctl --user -t maestro-watchdog
        # -o short-iso on the production host 2026-11-04 (verbatim prefix).
        line = (
            "2026-11-04T12:28:13+0000 agent-runner maestro-watchdog[2356306]: "
            '{"api_ok": true, "healthy": true, "heartbeat_age_seconds": 10.7}'
        )
        ticks = slo.parse_watchdog_journal([line])
        assert len(ticks) == 1
        assert ticks[0]["api_ok"] is True


# ---------------------------------------------------------------------------
# Regression: journald retention laundering (2026-11-04). journald retains
# only ~3h of maestro-watchdog ticks on the production host while the SLO
# window is trailing 24h — a journal-only read over the window reported
# UNKNOWN "only transient blips (nothing to handle)" while the window's
# start was physically unauditable, and episodes that rotated out of the
# journal were invisible. collect_all must (a) union the durable rolling
# archive so archived episodes count, and (b) PROVE coverage before any
# verdict: an unauditable window is an explicit coverage edge and can
# never certify absence.
# ---------------------------------------------------------------------------


class TestWatchdogArchiveUnionCoverage:
    EP2 = 1793790000.0  # fixed epoch base; collect_all(now=...) pins the window

    def _line(self, offset_s: float, payload: dict | None = None) -> str:
        import datetime as _dt
        import json as _json

        t = _dt.datetime.fromtimestamp(
            self.EP2 + offset_s, tz=_dt.timezone.utc
        )
        body = _json.dumps(payload or {"semantic_healthy": True})
        return f"{t.strftime('%Y-%m-%dT%H:%M:%S+0000')} agent-runner maestro-watchdog[2356306]: {body}"

    def _run(self, tmp_path: Path, journal: list[str], archive: list[str]):
        import os

        (tmp_path / "ticks.jsonl").write_text("\n".join(archive) + "\n")
        old = {
            k: os.environ.get(k)
            for k in (
                "NRM_WATCHDOG_ARCHIVE",
                "NRM_WATCHDOG_TICK_MAX_GAP_S",
                "NRM_WATCHDOG_WINDOW_S",
            )
        }
        os.environ["NRM_WATCHDOG_ARCHIVE"] = str(tmp_path / "ticks.jsonl")
        os.environ["NRM_WATCHDOG_TICK_MAX_GAP_S"] = "3600"
        try:
            return slo.collect_all(
                hermes_root=tmp_path,
                journal_reader=lambda u, s: (journal, None),
                # fixture offsets span [0, 86400]; anchor `now` at the
                # window END so offset 0 IS the window start
                now=self.EP2 + 86400.0,
            )
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_retention_hole_degrades_instead_of_nothing_to_measure(
        self, tmp_path: Path
    ) -> None:
        # Journal retains only the last ~2h of a 24h window; no archive.
        # The pre-fix harness reported UNKNOWN "only transient blips in
        # window (nothing to handle)" for exactly this shape.
        journal = [
            self._line(float(o))
            for o in range(79200, 86400, 60)  # last 2h only
        ]
        doc = self._run(tmp_path, journal, archive=[])
        ids = {r["slo_id"]: r for r in doc["records"]}
        stall = ids["stall_detection"]
        assert stall["verdict"] == slo.UNKNOWN
        assert stall["value"]["coverage_complete"] is False
        assert any(
            "window start unauditable" in n for n in stall["notes"]
        ), f"expected coverage edge, notes={stall['notes']}"
        assert not any(
            "nothing to handle" in n or "nothing to measure" in n
            for n in stall["notes"]
        ), "benign absence note must not survive an unauditable window"
        auto = ids["auto_recovery"]
        assert auto["value"]["coverage_complete"] is False

    def test_archive_union_restores_window_and_counts_archived_episode(
        self, tmp_path: Path
    ) -> None:
        # The archive holds the early-window span (incl. a persistent
        # undetected episode at ~5.2h in) that journald rotated away; the
        # journal holds only the last 2h. Union must (a) kill the head
        # gap, (b) count the archived episode, (c) FAIL the SLO honestly
        # (undetected episode), and (d) record archive provenance.
        archive = [self._line(0.0)]
        # healthy ticks each 30min bridging the whole window until the
        # journal takes over at 22h (no interior hole)
        for off in range(1800, 79200, 1800):
            archive.append(self._line(float(off)))
        # persistent undetected episode at ~5.2h: 3 stall ticks, no action
        archive.extend(
            self._line(float(o), {"semantic_healthy": False})
            for o in (18600, 18720, 18840)
        )
        journal = [
            self._line(float(o)) for o in range(79200, 86400, 600)
        ]  # last 2h, healthy
        doc = self._run(tmp_path, journal, archive=archive)
        ids = {r["slo_id"]: r for r in doc["records"]}
        stall = ids["stall_detection"]
        # union closed the head gap: coverage complete, episode measured
        assert stall["value"]["coverage_complete"] is True
        assert stall["value"]["persistent_episodes"] == 1
        assert stall["value"]["undetected"] == 1
        assert stall["verdict"] == slo.FAIL, (
            "an archived undetected persistent episode must FAIL the SLO — "
            "rotation must not launder it away"
        )
        assert any("rolling archive" in s for s in stall["sources"])

    def test_full_coverage_journal_only_still_clean(self, tmp_path: Path):
        # A fully-covered window from the journal alone (no archive file)
        # keeps its normal verdict and reports coverage_complete True.
        journal = [
            self._line(float(o)) for o in range(0, 86400, 1800)
        ]
        doc = self._run(tmp_path, journal, archive=[])
        ids = {r["slo_id"]: r for r in doc["records"]}
        stall = ids["stall_detection"]
        assert stall["value"]["coverage_complete"] is True
        # pre-existing zero-episode value shape keeps its "episodes" key
        assert stall["value"]["episodes"] == 0
        # verdict stays the honest UNKNOWN-nothing-to-measure ONLY when
        # coverage is proven complete
        assert any(
            "nothing to measure" in n or "nothing to handle" in n
            for n in stall["notes"]
        )
        assert stall["verdict"] == slo.UNKNOWN

    def test_unreadable_archive_contributes_nothing_but_is_surfaced(
        self, tmp_path: Path
    ) -> None:
        # Journal covers only the tail; the archive exists but is a
        # directory (unreadable): coverage must stay degraded and the
        # breakage surfaced — an unreadable archive never restores
        # coverage nor crashes the probe.
        journal = [
            self._line(float(o)) for o in range(79200, 86400, 600)
        ]
        import os

        (tmp_path / "ticks.jsonl").mkdir()
        old = {
            k: os.environ.get(k)
            for k in ("NRM_WATCHDOG_ARCHIVE",)
        }
        os.environ["NRM_WATCHDOG_ARCHIVE"] = str(tmp_path / "ticks.jsonl")
        try:
            doc = slo.collect_all(
                hermes_root=tmp_path,
                journal_reader=lambda u, s: (journal, None),
                now=self.EP2 + 86400.0,
            )
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        ids = {r["slo_id"]: r for r in doc["records"]}
        stall = ids["stall_detection"]
        assert stall["value"]["coverage_complete"] is False
        assert any("unreadable" in n for n in stall["notes"])

    def test_interior_gap_is_an_edge_even_with_archive(self, tmp_path):
        # Archive + journal both present but leave an interior hole
        # (archive stops at 4h, journal starts at 22h): episodes inside
        # the hole are invisible — an explicit interior-gap edge.
        archive = [self._line(float(o)) for o in range(0, 14400, 1800)]
        journal = [self._line(float(o)) for o in range(79200, 86400, 600)]
        doc = self._run(tmp_path, journal, archive=archive)
        ids = {r["slo_id"]: r for r in doc["records"]}
        stall = ids["stall_detection"]
        assert stall["value"]["coverage_complete"] is False
        assert any("interior gap" in n for n in stall["notes"])
        assert not any(
            "nothing to handle" in n or "nothing to measure" in n
            for n in stall["notes"]
        )

    def test_coverage_gap_downgrades_pass_to_unknown(self, tmp_path: Path):
        # last 1h only, healthy, with one fast-detected stall episode
        # (2 stall ticks, restart at +200s) — a PASS shape that must be
        # downgraded because the window's head is unauditable.
        journal = [
            self._line(82800.0),
            self._line(83400.0, {"semantic_healthy": False}),
            self._line(
                83600.0, {"semantic_healthy": False, "restarted": True}
            ),
            self._line(84000.0),
            self._line(84600.0),
            self._line(85200.0),
            self._line(85800.0),
        ]
        doc = self._run(tmp_path, journal, archive=[])
        ids = {r["slo_id"]: r for r in doc["records"]}
        stall = ids["stall_detection"]
        assert stall["value"]["persistent_episodes"] == 1
        assert stall["value"]["within_5m"] == 1
        assert stall["verdict"] == slo.UNKNOWN, (
            "PASS under an unauditable window launders the missing span"
        )
