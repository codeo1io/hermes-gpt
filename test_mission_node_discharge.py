"""Mission-level node discharge markers + routine_completion probe semantics.

Covers ``operator_mission_runtime.supersede_mission_node`` /
``list_node_discharge_markers`` / ``_is_discharged_node`` and the
``operator_slo_probe.probe_routine_completion`` discharge handling:

- a failed routine node discharged by a COMPLETED successor mission counts as
  completed (numerator+1, denominator unchanged) and is receipted in notes;
- discharge is refused/fails closed for: non-failed node, non-completed
  successor, missing successor, missing node, self-succession, bad
  evidence_ref, conflicting different-successor marker;
- repeat discharge of the same (node, successor) is idempotent;
- objective-text tampering AFTER the marker was written voids the discharge;
- a forged marker (row written behind the API's back) is only honoured when it
  verifies end to end — a dangling successor or wrong digest has no effect;
- live failed debt is reported and still FAILs the SLO.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import operator_mission_runtime as mission
import operator_slo_probe as slo
from test_operator_autopilot_scheduler import _j, make_env

MID = "msn-discharge-pred"
SUCCESSOR = "msn-discharge-succ"
OTHER = "msn-discharge-other"


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    return make_env(tmp_path, monkeypatch)


def _mk_mission(root: Path, mid: str, *, objective: str = "Land the thing.") -> None:
    spec = json.dumps({
        "schema": mission.MISSION_SPEC_SCHEMA, "mission_id": mid,
        "title": "Discharge test", "objective": objective,
        "owner_profile": "default", "acceptance_criteria": ["done"],
        "context_refs": [], "skills": [], "final_approval_required": True,
    })
    assert _j(mission.hermes_mission_create(spec, confirm=True, dry_run=False, hermes_root=root))["success"]


def _mk_plan(root: Path, mid: str, node_id: str, *, state: str) -> None:
    """Add the node through the plan API, then force its terminal state.

    hermes_plan_create is replace-version: an existing plan for the mission is
    superseded, so each call must carry the FULL node set wanted. The test
    suite only ever needs one or two nodes per mission, and any second call
    for the same mission re-declares every node (see _mk_two_plan below).
    """
    _put_nodes(root, mid, [node_id])
    with sqlite3.connect(mission._db_path(root)) as db:
        db.execute("UPDATE plan_nodes SET state=? WHERE mission_id=? AND node_id=?",
                   (state, mid, node_id))


def _mk_two_plan(root: Path, mid: str, node_a: str, state_a: str,
                 node_b: str, state_b: str) -> None:
    """Two nodes on ONE plan (replace-version keeps only the latest plan)."""
    _put_nodes(root, mid, [node_a, node_b])
    with sqlite3.connect(mission._db_path(root)) as db:
        db.execute("UPDATE plan_nodes SET state=? WHERE mission_id=? AND node_id=?",
                   (state_a, mid, node_a))
        db.execute("UPDATE plan_nodes SET state=? WHERE mission_id=? AND node_id=?",
                   (state_b, mid, node_b))


def _put_nodes(root: Path, mid: str, node_ids: list[str]) -> None:
    import operator_mission_plan as plan_mod
    nodes = [{
        "node_id": n, "kind": "single", "owner": "hermes-researcher",
        "parents": [], "objective": f"Objective {n}.",
        "capability_req": {"profile": "hermes-researcher", "skills": [],
                           "authorization_class": "reversible_write"},
        "budget": {"est_minutes": 5, "est_tokens": 1000},
        "expected_artifacts": ["work-contract.json"],
    } for n in node_ids]
    doc = json.dumps({
        "schema": plan_mod.PLAN_SCHEMA, "mission_id": mid, "version": 1,
        "decomposition": "operator-provided", "objective": "Discharge test.",
        "nodes": nodes,
    })
    out = _j(plan_mod.hermes_plan_create(mid, doc, confirm=True, dry_run=False, hermes_root=root))
    assert out["success"] is True, out


def _set_status(root: Path, mid: str, status: str) -> None:
    with sqlite3.connect(mission._db_path(root)) as db:
        db.execute("UPDATE missions SET status=? WHERE mission_id=?", (status, mid))


def _discharge(root: Path, node_id: str = "n1", successor: str = SUCCESSOR,
               evidence: str = "EVIDENCE/x.md", reason: str = "landed by successor"):
    return mission.supersede_mission_node(
        MID, node_id, successor, reason=reason, evidence_ref=evidence,
        hermes_root=root,
    )


class TestSupersedeMissionNode:
    def test_discharges_failed_node_by_completed_successor(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        out = _discharge(root)
        assert out["changed"] is True and out["idempotent"] is False
        markers = mission.list_node_discharge_markers(MID, hermes_root=root)
        assert markers["n1"]["successor_mission_id"] == SUCCESSOR
        assert mission._is_discharged_node(
            sqlite3.connect(mission._db_path(root)), MID, "n1"
        ) == SUCCESSOR

    def test_repeat_discharge_is_idempotent(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        assert _discharge(root)["changed"] is True
        assert _discharge(root)["changed"] is False
        assert _discharge(root)["idempotent"] is True

    def test_refuses_non_failed_node(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="completed")
        _set_status(root, SUCCESSOR, "completed")
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root)

    def test_refuses_incomplete_successor(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)  # stays draft
        _mk_plan(root, MID, "n1", state="failed")
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root)

    def test_refuses_missing_successor_and_node(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root)  # successor mission does not exist
        _mk_mission(root, SUCCESSOR)
        _set_status(root, SUCCESSOR, "completed")
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root, node_id="missing")

    def test_refuses_self_succession_and_bad_evidence(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root, successor=MID)
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root, evidence="not-a-path")

    def test_refuses_conflicting_different_successor(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_mission(root, OTHER)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        _set_status(root, OTHER, "completed")
        assert _discharge(root)["changed"] is True
        with pytest.raises(mission.MissionSupersedeError):
            _discharge(root, successor=OTHER)

    def test_objective_tampering_voids_discharge(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        assert _discharge(root)["changed"] is True
        with sqlite3.connect(mission._db_path(root)) as db:
            spec = json.loads(db.execute(
                "SELECT spec_json FROM missions WHERE mission_id=?", (MID,)
            ).fetchone()[0])
            spec["objective"] = "Rewritten history."
            db.execute("UPDATE missions SET spec_json=? WHERE mission_id=?",
                       (json.dumps(spec), MID))
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_discharged_node(db, MID, "n1") == ""

    def test_failed_successor_no_longer_discharges(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        assert _discharge(root)["changed"] is True
        _set_status(root, SUCCESSOR, "failed")  # truth changed underneath
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_discharged_node(db, MID, "n1") == ""

    def test_forged_marker_row_is_only_honoured_when_it_verifies(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        # marker written behind the API's back but with a WRONG digest
        with sqlite3.connect(mission._db_path(root)) as db:
            db.execute(
                "INSERT INTO mission_events(mission_id,event_type,from_status,"
                "to_status,reason_sha256,details_json,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (MID, "mission.node_superseded", "", "", "0" * 64,
                 json.dumps({"node_id": "n1",
                             "successor_mission_id": SUCCESSOR,
                             "objective_sha256": "f" * 64,
                             "reason": "forged", "evidence_ref": "x/y"}),
                 "2026-01-01T00:00:00Z"),
            )
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_discharged_node(db, MID, "n1") == ""
        # same forged shape but citing a dangling successor also fails closed
        with sqlite3.connect(mission._db_path(root)) as db2:
            db2.execute(
                "INSERT INTO mission_events(mission_id,event_type,from_status,"
                "to_status,reason_sha256,details_json,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (MID, "mission.node_superseded", "", "", "0" * 64,
                 json.dumps({"node_id": "n2",
                             "successor_mission_id": "msn-does-not-exist",
                             "objective_sha256": "0" * 64,
                             "reason": "forged", "evidence_ref": "x/y"}),
                 "2026-01-01T00:00:00Z"),
            )
        _mk_plan(root, MID, "n2", state="failed")
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_discharged_node(db, MID, "n2") == ""


class TestProbeDischargeSemantics:
    def _db(self, root: Path) -> Path:
        return mission._db_path(root)

    def test_discharged_failure_counts_as_completed(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_plan(root, MID, "n1", state="failed")
        _set_status(root, SUCCESSOR, "completed")
        rec_before = slo.probe_routine_completion(self._db(root))
        assert rec_before.verdict == slo.FAIL
        assert (rec_before.numerator, rec_before.denominator) == (0, 1)
        assert _discharge(root)["changed"] is True
        rec = slo.probe_routine_completion(self._db(root))
        assert rec.verdict == slo.PASS
        assert (rec.numerator, rec.denominator) == (1, 1)
        assert any(f"{MID}/n1->{SUCCESSOR}" in n for n in rec.notes)

    def test_live_debt_still_fails_and_is_reported(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_mission(root, SUCCESSOR)
        _mk_two_plan(root, MID, "n1", "failed", "n2", "failed")
        _set_status(root, SUCCESSOR, "completed")
        _discharge(root, node_id="n1")
        rec = slo.probe_routine_completion(self._db(root))
        assert rec.verdict == slo.FAIL
        assert (rec.numerator, rec.denominator) == (1, 2)
        assert any("1 failed node(s) remain LIVE debt" in n for n in rec.notes)
        assert not any(f"{MID}/n2->" in n for n in rec.notes)

    def test_denominator_shape_unchanged_without_markers(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_two_plan(root, MID, "n1", "completed", "n2", "failed")
        rec = slo.probe_routine_completion(self._db(root))
        assert (rec.numerator, rec.denominator) == (1, 2)
        assert rec.verdict == slo.FAIL
        assert all("discharged failures" not in n for n in rec.notes)
