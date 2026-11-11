"""Tests for the AUTO-02 persistent campaign controller.

The controller is a caller over the real stores: every test runs against a
temp hermes_root with the REAL mission store, plan store and autopilot run
store. Only the detached Autopilot worker is stood in for (a fake run record
writer), because these tests exercise cross-segment sequencing — the worker's
own dispatch/reconcile behavior is covered by test_operator_autopilot_*.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import operator_autopilot as autopilot
import operator_campaign_compiler as compiler
import operator_campaign_controller as ctrl
import operator_mission_plan as plan_store
import operator_mission_runtime as mission
import operator_policy as op


def _segment(seq: str, mid: str, *, depends_on: list[str] | None = None) -> dict:
    return {
        "seq": seq,
        "depends_on": depends_on or [],
        "campaign_json": json.dumps({
            "schema": compiler.CAMPAIGN_SCHEMA,
            "campaign_id": "camp-test",
            "mission_id": mid,
            "objective": f"Segment {seq} work",
            "tracks": [
                {"track": "a", "profile": "hermes-dev",
                 "tasks": [{"task": "T1", "evidence": ["implementation"]}]},
            ],
        }),
    }


def _manifest(*segments: dict, campaign_id: str = "camp-test") -> str:
    return json.dumps({
        "schema": ctrl.MANIFEST_SCHEMA,
        "campaign_id": campaign_id,
        "segments": list(segments),
    })


@pytest.fixture
def hermes_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "hermes"
    root.mkdir()
    op.set_audit_log_override(tmp_path / "audit.jsonl")
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.delenv(op.OWNER_ACTIVE_ENV, raising=False)
    monkeypatch.delenv(op.OWNER_ACK_ENV, raising=False)
    monkeypatch.delenv(autopilot.AUTOPILOT_ENV, raising=False)
    return root


def _tick(manifest: str, root: Path, *, apply: bool = True) -> dict:
    return json.loads(ctrl.campaign_controller_tick(
        manifest, confirm=apply, apply=apply, hermes_root=root,
    ))


def _phase(out: dict, seq: str) -> str:
    return next(s for s in out["segments"] if s["seq"] == seq)["phase"]


def _entry(root: Path, campaign_id: str, seq: str) -> dict:
    state = json.loads((root / "campaigns" / campaign_id / "state.json").read_text())
    return state["segments"][seq]


# ---------------------------------------------------------------------------
# Manifest validation (fail closed)
# ---------------------------------------------------------------------------

def test_manifest_rejects_unknown_schema(hermes_root: Path) -> None:
    out = json.loads(ctrl.campaign_controller_tick(json.dumps({"schema": "nope"}), hermes_root=hermes_root))
    assert out["success"] is False
    assert "schema" in out["error"]


def test_manifest_rejects_segment_that_does_not_compile(hermes_root: Path) -> None:
    bad = _segment("s1", "msn-c1")
    doc = json.loads(bad["campaign_json"])
    doc["tracks"][0]["tasks"][0]["evidence"] = ["bogus-evidence"]  # unknown class
    bad["campaign_json"] = json.dumps(doc)
    out = json.loads(ctrl.campaign_controller_tick(_manifest(bad), hermes_root=hermes_root))
    assert out["success"] is False
    assert "does not compile" in out["error"]


def test_manifest_rejects_duplicate_mission_ids(hermes_root: Path) -> None:
    out = json.loads(ctrl.campaign_controller_tick(
        _manifest(_segment("s1", "msn-c1"), _segment("s2", "msn-c1")), hermes_root=hermes_root,
    ))
    assert out["success"] is False
    assert "duplicate mission_id" in out["error"]


def test_manifest_rejects_cycle(hermes_root: Path) -> None:
    out = json.loads(ctrl.campaign_controller_tick(
        _manifest(_segment("s1", "msn-c1", depends_on=["s2"]), _segment("s2", "msn-c2", depends_on=["s1"])),
        hermes_root=hermes_root,
    ))
    assert out["success"] is False
    assert "cycle" in out["error"]


def test_manifest_rejects_unknown_dependency(hermes_root: Path) -> None:
    out = json.loads(ctrl.campaign_controller_tick(
        _manifest(_segment("s1", "msn-c1", depends_on=["ghost"])), hermes_root=hermes_root,
    ))
    assert out["success"] is False
    assert "unknown segment" in out["error"]


def test_dry_run_creates_nothing(hermes_root: Path) -> None:
    manifest = _manifest(_segment("s1", "msn-c1"))
    out = json.loads(ctrl.campaign_controller_tick(manifest, hermes_root=hermes_root))
    assert out["success"] is True and out["dry_run"] is True
    assert out["segments"][0]["next_action"] == "mint_mission"
    assert not (hermes_root / "campaigns").exists()
    assert json.loads(mission.hermes_mission_get("msn-c1", hermes_root=hermes_root)).get("found") is False


def test_apply_requires_confirm(hermes_root: Path) -> None:
    out = json.loads(ctrl.campaign_controller_tick(
        _manifest(_segment("s1", "msn-c1")), apply=True, hermes_root=hermes_root,
    ))
    assert out["success"] is False


# ---------------------------------------------------------------------------
# Phase machine against real stores
# ---------------------------------------------------------------------------

def test_pending_to_minted_creates_real_mission(hermes_root: Path) -> None:
    out = _tick(_manifest(_segment("s1", "msn-c1")), hermes_root)
    assert out["success"] is True
    assert _phase(out, "s1") == "minted"
    created = json.loads(mission.hermes_mission_get("msn-c1", hermes_root=hermes_root))
    assert created.get("found", True) is not False and created["status"] == "draft"
    assert created["status"] == "draft"
    assert created["final_approval_required"] is True  # never forge approval-free


def test_tick_is_idempotent_no_duplicate_mission(hermes_root: Path) -> None:
    manifest = _manifest(_segment("s1", "msn-c1"))
    first = _tick(manifest, hermes_root)
    second = _tick(manifest, hermes_root)
    assert first["success"] and second["success"]
    # The invariant: never a second mission_create for the same segment
    assert [a for a in second["actions"] if a["action"] == "mission_create"] == []
    # minted on tick 2 attempts plan+start; with the machine gate off this
    # parks (correct), never re-mints
    assert _phase(second, "s1") in ("minted", "parked_autopilot_gate")


def test_minted_to_active_via_real_plan_and_start(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []

    def fake_start(mid, **kw):
        started.append(mid)
        run = {"mission_id": mid, "state": "running", "attempt": 1}
        autopilot._write_run(mid, kw.get("hermes_root"), state="running")
        return json.dumps({"success": True, "mission_id": mid, "run": run})

    monkeypatch.setattr(autopilot, "hermes_autopilot_start", fake_start)
    out = _tick(_manifest(_segment("s1", "msn-c1")), hermes_root)
    out = _tick(_manifest(_segment("s1", "msn-c1")), hermes_root)  # second tick: minted -> plan+start
    assert _phase(out, "s1") == "active"
    assert started == ["msn-c1"]
    stored = json.loads(plan_store.hermes_plan_get("msn-c1", hermes_root=hermes_root))
    assert stored.get("found", True) is not False
    assert stored["decomposition"] == compiler.DECOMPOSITION_ID
    assert json.loads(mission.hermes_mission_get("msn-c1", hermes_root=hermes_root))["status"] == "running"


def test_dependencies_gate_ordering(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _manifest(
        _segment("s1", "msn-c1"),
        _segment("s2", "msn-c2", depends_on=["s1"]),
    )
    one = _tick(manifest, hermes_root)
    # deps gate ALL work: s1 mints, s2 stays pending until s1 succeeds
    assert _phase(one, "s1") == "minted" and _phase(one, "s2") == "pending"
    two = _tick(manifest, hermes_root)  # s1 activates; s2 still waits
    assert _phase(two, "s1") == "active"
    assert _phase(two, "s2") == "pending"
    assert next(s for s in two["segments"] if s["seq"] == "s2")["next_action"] == "wait_dependencies"
    # s2 must NOT have a plan yet
    assert json.loads(plan_store.hermes_plan_get("msn-c2", hermes_root=hermes_root)).get("success") is False


def test_failed_dependency_fails_dependents(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _manifest(
        _segment("s1", "msn-c1"),
        _segment("s2", "msn-c2", depends_on=["s1"]),
    )
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    # Force s1's mission to failed (authoritative truth wins over state.json)
    json.loads(mission.hermes_mission_transition(
        "msn-c1", "failed", reason="test", confirm=True, dry_run=False, hermes_root=hermes_root))
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") == "failed"
    assert _phase(out, "s2") == "failed"
    assert "dependency failed" in _entry(hermes_root, "camp-test", "s2")["reason"]


def test_owner_gate_parks_segment(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # awaiting_approval is reconcile-only in the mission store, so the owner
    # gate is exercised by stubbing the authoritative mission view at the
    # phase-derivation seam (the full path is Autopilot acceptance coverage).
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    real_view = ctrl._mission_view
    def gated(mission_id, root):
        view = real_view(mission_id, root)
        if view is not None and mission_id == "msn-c1":
            view = dict(view)
            view["status"] = "awaiting_approval"
        return view
    monkeypatch.setattr(ctrl, "_mission_view", gated)
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") == "parked_owner_gate"
    view = next(s for s in out["segments"] if s["seq"] == "s1")
    assert view["next_action"] == "wait_owner"
    # a parked owner gate never monopolizes: independent segments proceed
    manifest2 = _manifest(_segment("s1", "msn-c1"), _segment("s3", "msn-c3"))
    out2 = _tick(manifest2, hermes_root)
    assert _phase(out2, "s1") == "parked_owner_gate"
    assert _phase(out2, "s3") == "minted"


def test_state_loss_rebuilds_from_truth(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    assert _phase(_tick(manifest, hermes_root), "s1") == "active"
    # Simulate controller state loss (restart with wiped campaigns dir)
    import shutil
    shutil.rmtree(hermes_root / "campaigns")
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") == "active"  # re-derived: mission running + run alive
    assert out["ticks"] == 1  # fresh state document
    assert [a for a in out["actions"] if a["action"] == "mission_create"] == []  # no duplicate mint


def test_stale_state_repaired_from_truth(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    # Corrupt the recorded phase (state says pending; truth says minted+more)
    state_path = hermes_root / "campaigns" / "camp-test" / "state.json"
    state = json.loads(state_path.read_text())
    state["segments"]["s1"]["phase"] = "pending"
    state_path.write_text(json.dumps(state))
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") in ("active", "minted")
    assert any(r["seq"] == "s1" and r["recorded"] == "pending" for r in out["state_repairs"])


def test_terminal_mission_completes_segment(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    json.loads(mission.hermes_mission_transition(
        "msn-c1", "failed", reason="done", confirm=True, dry_run=False, hermes_root=hermes_root))
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") == "failed"
    assert out["finished"] is True


def test_autopilot_machine_gate_parks_segment(hermes_root: Path) -> None:
    # AUTOPILOT_ENV unset => hermes_autopilot_start raises gate error inside
    # its JSON error payload; the controller must park, not fail.
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)  # mint
    out = _tick(manifest, hermes_root)  # plan + start attempt -> gate park
    assert _phase(out, "s1") == "parked_autopilot_gate"
    view = next(s for s in out["segments"] if s["seq"] == "s1")
    assert view["next_action"] == "retry_start"


def test_autopilot_gate_retry_after_operator_enables(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") == "parked_autopilot_gate"
    # Operator flips the gate on
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    out = _tick(manifest, hermes_root)
    assert _phase(out, "s1") == "active"


def test_drained_plan_does_not_start_second_run(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    starts: list[str] = []

    def fake_start(mid, **kw):
        starts.append(mid)
        return json.dumps({"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")})

    monkeypatch.setattr(autopilot, "hermes_autopilot_start", fake_start)
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    assert starts == ["msn-c1"]
    # All plan nodes reach terminal states behind the controller's back
    plan_doc = json.loads(plan_store.hermes_plan_get("msn-c1", hermes_root=hermes_root))
    for node in plan_doc["nodes"]:
        for target in ("dispatched", "running", "awaiting_review", "validated", "awaiting_approval", "completed"):
            res = json.loads(plan_store.hermes_plan_node_transition(
                "msn-c1", node["node_id"], target, confirm=True, dry_run=False, hermes_root=hermes_root))
            assert res["success"], res
    json.loads(mission.hermes_mission_transition(
        "msn-c1", "running", confirm=True, dry_run=False, hermes_root=hermes_root))  # keep non-draft
    out = _tick(manifest, hermes_root)
    # reconcile drives the mission toward awaiting_approval; no second start
    assert starts == ["msn-c1"]
    assert _phase(out, "s1") in ("parked_owner_gate", "active")


def test_manifest_revision_orphans_removed_segment(hermes_root: Path) -> None:
    manifest_v1 = _manifest(_segment("s1", "msn-c1"), _segment("s2", "msn-c2"))
    _tick(manifest_v1, hermes_root)
    manifest_v2 = _manifest(_segment("s1", "msn-c1"))
    out = _tick(manifest_v2, hermes_root)
    assert _phase(out, "s1") in ("minted", "parked_autopilot_gate")
    # s2 is gone from the manifest; its recorded entry is orphaned
    state = json.loads((hermes_root / "campaigns" / "camp-test" / "state.json").read_text())
    assert state["segments"]["s2"]["phase"] == "orphaned"
    # the mission itself is untouched (containment, not mutation)
    assert json.loads(mission.hermes_mission_get("msn-c2", hermes_root=hermes_root)).get("found", True) is not False


def test_status_roundtrip(hermes_root: Path) -> None:
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    out = json.loads(ctrl.campaign_controller_status("camp-test", hermes_root=hermes_root))
    assert out["found"] is True
    assert out["state"]["campaign_id"] == "camp-test"
    assert out["state"]["segments"]["s1"]["phase"] == "minted"
    missing = json.loads(ctrl.campaign_controller_status("camp-none", hermes_root=hermes_root))
    assert missing["found"] is False


# ---------------------------------------------------------------------------
# Recurrence (generation-based, bounded)
# ---------------------------------------------------------------------------

import datetime as _dt  # noqa: E402  (test-local convenience)


def _backdate_finished(root: Path, campaign_id: str, seconds: int = 120) -> None:
    state = json.loads((root / "campaigns" / campaign_id / "state.json").read_text())
    past = _dt.datetime.now(_dt.timezone.utc).timestamp() - seconds
    state["generation_finished_at"] = _dt.datetime.fromtimestamp(
        past, tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (root / "campaigns" / campaign_id / "state.json").write_text(json.dumps(state))


def _rec_manifest(mid: str = "msn-camp-recur-g{gen}", *, interval_s: int = 60,
                   max_generations: int = 3, max_consecutive_failures: int | None = None,
                   campaign_id: str = "camp-test") -> str:
    rec: dict = {"interval_s": interval_s, "max_generations": max_generations}
    if max_consecutive_failures is not None:
        rec["max_consecutive_failures"] = max_consecutive_failures
    return json.dumps({
        "schema": ctrl.MANIFEST_SCHEMA,
        "campaign_id": campaign_id,
        "recurrence": rec,
        "segments": [_segment("s1", mid)],
    })


def _set_generation_outcome(root: Path, mid: str, outcome: str) -> None:
    """Drive a generation mission to a terminal status.

    ``failed`` goes through the sanctioned transition; ``completed`` would
    require the Owner-approve path (children + verified attachments), which
    is operator_autopilot/mission-runtime territory — the controller only
    reads terminal status, so tests set it directly in the store.
    """
    import sqlite3
    if outcome == "failed":
        json.loads(mission.hermes_mission_transition(
            mid, "failed", reason="test fail", confirm=True, dry_run=False, hermes_root=root))
        return
    db_path = root / "missions" / "missions.db"
    con = sqlite3.connect(db_path)
    try:
        con.execute("UPDATE missions SET status=?, updated_at=datetime('now') WHERE mission_id=?",
                    (outcome, mid))
        con.commit()
    finally:
        con.close()


def test_recurrence_requires_gen_token(hermes_root: Path) -> None:
    out = json.loads(ctrl.campaign_controller_tick(
        _rec_manifest("msn-no-token"), hermes_root=hermes_root))
    assert out["success"] is False
    assert "must contain" in out["error"] and "{gen}" in out["error"]


def test_recurrence_rejects_bad_bounds(hermes_root: Path) -> None:
    for bad in ({"interval_s": 59, "max_generations": 3},
                {"interval_s": 30 * 86400 + 1, "max_generations": 3},
                {"interval_s": 60, "max_generations": 0},
                {"interval_s": 60, "max_generations": 1001},
                {"interval_s": "60", "max_generations": 3},
                {"interval_s": 60, "max_generations": 3, "bogus": 1},
                {"interval_s": 60, "max_generations": 3, "max_consecutive_failures": 11}):
        doc = json.loads(_rec_manifest())
        doc["recurrence"] = bad
        out = json.loads(ctrl.campaign_controller_tick(
            json.dumps(doc), hermes_root=hermes_root))
        assert out["success"] is False, bad
        assert "recurrence" in out["error"], bad


def test_generation_rollover_mints_next_generation(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _rec_manifest()
    _tick(manifest, hermes_root)   # mint g1
    _tick(manifest, hermes_root)   # plan+start g1
    _set_generation_outcome(hermes_root, "msn-camp-recur-g1", "completed")
    out = _tick(manifest, hermes_root)  # g1 terminal -> outcome recorded
    assert _phase(out, "s1") == "succeeded"
    assert out["finished"] is False    # recurrence owed: not finished
    assert out["recurrence"]["generation"] == 1
    assert out["recurrence"]["rollover_due"] is False  # pacing just started
    state = json.loads((hermes_root / "campaigns" / "camp-test" / "state.json").read_text())
    assert state["generation_history"][-1]["outcome"] == "succeeded"
    _backdate_finished(hermes_root, "camp-test")
    out = _tick(manifest, hermes_root)  # rollover + same-tick mint of g2
    roll = [a for a in out["actions"] if a["action"] == "generation_rollover"]
    assert roll and roll[0]["to_generation"] == 2
    assert out["recurrence"]["generation"] == 2
    g2 = json.loads(mission.hermes_mission_get("msn-camp-recur-g2", hermes_root=hermes_root))
    assert g2.get("found", True) is not False and g2["status"] == "draft"
    g1 = json.loads(mission.hermes_mission_get("msn-camp-recur-g1", hermes_root=hermes_root))
    assert g1["status"] == "completed"  # prior generation untouched


def test_rollover_paces_by_interval(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _rec_manifest()
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    _set_generation_outcome(hermes_root, "msn-camp-recur-g1", "completed")
    out = _tick(manifest, hermes_root)
    assert out["finished"] is False
    assert out["recurrence"]["rollover_due"] is False
    assert out["recurrence"]["next_generation_at"] is not None
    out2 = _tick(manifest, hermes_root)  # pacing holds: no g2 mint
    assert [a for a in out2["actions"] if a["action"] == "mission_create"] == []
    assert json.loads(mission.hermes_mission_get(
        "msn-camp-recur-g2", hermes_root=hermes_root)).get("success") is False


def test_max_generations_cap_finishes(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _rec_manifest(max_generations=1)
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    _set_generation_outcome(hermes_root, "msn-camp-recur-g1", "completed")
    out = _tick(manifest, hermes_root)
    assert out["finished"] is True  # cap reached: recurring campaign is done
    assert out["recurrence"]["generation"] == 1


def test_consecutive_failure_bound_stops_recurrence(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _rec_manifest(max_generations=10, max_consecutive_failures=2)
    for gen in (1, 2):
        _tick(manifest, hermes_root)
        _tick(manifest, hermes_root)
        json.loads(mission.hermes_mission_transition(
            f"msn-camp-recur-g{gen}", "failed", reason="test fail", confirm=True, dry_run=False,
            hermes_root=hermes_root))
        _tick(manifest, hermes_root)
        _backdate_finished(hermes_root, "camp-test")
    out = _tick(manifest, hermes_root)
    assert out["finished"] is True  # 2 consecutive failures = permanent park
    assert [a for a in out["actions"] if a["action"] == "generation_rollover"] == []
    state = json.loads((hermes_root / "campaigns" / "camp-test" / "state.json").read_text())
    assert state["consecutive_failures"] == 2
    assert str(state["recurrence_stopped"]).startswith("consecutive_failures=2")
    assert json.loads(mission.hermes_mission_get(
        "msn-camp-recur-g3", hermes_root=hermes_root)).get("success") is False


def test_success_resets_failure_counter(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _rec_manifest(max_generations=10, max_consecutive_failures=2)
    for gen, outcome in ((1, "failed"), (2, "completed"), (3, "failed")):
        _tick(manifest, hermes_root)
        _tick(manifest, hermes_root)
        _set_generation_outcome(hermes_root, f"msn-camp-recur-g{gen}", outcome)
        _tick(manifest, hermes_root)
        _backdate_finished(hermes_root, "camp-test")
    out = _tick(manifest, hermes_root)
    assert out["finished"] is False              # bound not hit (1 failure after a success)
    assert out["recurrence"]["generation"] == 4  # rolled to g4


def test_state_loss_recovers_generation(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _rec_manifest(max_generations=5)
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    _set_generation_outcome(hermes_root, "msn-camp-recur-g1", "completed")
    _tick(manifest, hermes_root)
    _backdate_finished(hermes_root, "camp-test")
    _tick(manifest, hermes_root)  # rollover -> g2 minted
    assert json.loads(mission.hermes_mission_get(
        "msn-camp-recur-g2", hermes_root=hermes_root)).get("found") is not False
    # state loss: delete state.json — the next tick must ADOPT g2, never re-mint
    (hermes_root / "campaigns" / "camp-test" / "state.json").unlink()
    out = _tick(manifest, hermes_root)
    assert out["recurrence"]["generation"] == 2
    assert [a for a in out["actions"] if a["action"] == "mission_create"] == []
    assert _phase(out, "s1") in ("minted", "active", "parked_autopilot_gate")


def test_recurrence_dry_run_mutates_nothing(hermes_root: Path) -> None:
    manifest = _rec_manifest()
    out = json.loads(ctrl.campaign_controller_tick(manifest, hermes_root=hermes_root))
    assert out["success"] is True and out["dry_run"] is True
    assert not (hermes_root / "campaigns").exists()
    g1 = json.loads(mission.hermes_mission_get(
        "msn-camp-recur-g1", hermes_root=hermes_root))
    assert g1.get("success") is False or g1.get("found") is False


def test_nonrecurring_manifest_has_no_generation_fields(hermes_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # regression: finite campaigns (the live nrm-cleanup-pilot shape) keep
    # byte-identical behavior — finished once, no generation state
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"), state="running")}))
    manifest = _manifest(_segment("s1", "msn-c1"))
    _tick(manifest, hermes_root)
    _tick(manifest, hermes_root)
    json.loads(mission.hermes_mission_transition(
        "msn-c1", "failed", reason="done", confirm=True, dry_run=False, hermes_root=hermes_root))
    out = _tick(manifest, hermes_root)
    assert out["finished"] is True
    assert out["recurrence"] is None
    state = json.loads((hermes_root / "campaigns" / "camp-test" / "state.json").read_text())
    assert "generation" not in state and "generation_history" not in state
