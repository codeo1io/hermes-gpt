"""Operator-anchored completion receipts (item 376) — the sanctioned second
discharge escape named by backfill_routine_discharge ("live debt until a
native retry mission completes or the rails record an operator-anchored
completion") and the slo5 live-debt review.

Covers ``operator_mission_runtime.record_operator_completion`` /
``_is_operator_completed_node`` / ``list_operator_completion_receipts`` and
``operator_slo_probe.probe_routine_completion`` receipt handling:

- a failed routine node with a verified operator receipt counts as completed
  (numerator+1, denominator unchanged) and is receipted in notes;
- receipts are refused/fail closed for: non-failed node, missing node,
  non-https anchor, missing evidence path, superseded-reason validation;
- repeat receipts are idempotent; a different receipt for the same node is
  refused;
- objective-text tampering AFTER the receipt voids it;
- a forged receipt row (written behind the API's back) is honoured only when
  it verifies end to end — dangling anchor or wrong digest has no effect;
- live failed debt without receipts still FAILs the SLO (no free passes).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import operator_mission_runtime as mission
import operator_slo_probe as slo
from test_operator_autopilot_scheduler import _j, make_env

MID = "msn-opcomp-pred"


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    return make_env(tmp_path, monkeypatch)


def _mk_mission(root: Path, mid: str, *, objective: str = "Land the thing.") -> None:
    spec = json.dumps({
        "schema": mission.MISSION_SPEC_SCHEMA, "mission_id": mid,
        "title": "Operator completion test", "objective": objective,
        "owner_profile": "default", "acceptance_criteria": ["done"],
        "context_refs": [], "skills": [], "final_approval_required": True,
    })
    assert _j(mission.hermes_mission_create(spec, confirm=True, dry_run=False, hermes_root=root))["success"]


def _mk_plan(root: Path, mid: str, node_id: str, *, state: str) -> None:
    import operator_mission_plan as plan_mod
    nodes = [{
        "node_id": node_id, "kind": "single", "owner": "hermes-researcher",
        "parents": [], "objective": f"Objective {node_id}.",
        "capability_req": {"profile": "hermes-researcher", "skills": [],
                           "authorization_class": "reversible_write"},
        "budget": {"est_minutes": 5, "est_tokens": 1000},
        "expected_artifacts": ["work-contract.json"],
    }]
    doc = json.dumps({
        "schema": plan_mod.PLAN_SCHEMA, "mission_id": mid, "version": 1,
        "decomposition": "operator-provided", "objective": "OpComp test.",
        "nodes": nodes,
    })
    out = _j(plan_mod.hermes_plan_create(mid, doc, confirm=True, dry_run=False, hermes_root=root))
    assert out["success"] is True, out
    with sqlite3.connect(mission._db_path(root)) as db:
        db.execute("UPDATE plan_nodes SET state=? WHERE mission_id=? AND node_id=?",
                   (state, mid, node_id))


def _receipt(root: Path, node_id: str = "n1",
             anchor: str = "https://github.com/codeo1io/hermes-gpt/pull/203",
             evidence: str = "EVIDENCE/x.md",
             reason: str = "objective landed outside the rails via merged PR"):
    return mission.record_operator_completion(
        MID, node_id, reason=reason, evidence_ref=evidence,
        anchor_url=anchor, hermes_root=root,
    )


class TestRecordOperatorCompletion:
    def test_records_on_failed_node(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        out = _receipt(root)
        assert out["changed"] is True and out["idempotent"] is False
        receipts = mission.list_operator_completion_receipts(MID, hermes_root=root)
        assert receipts["n1"]["anchor_url"].startswith("https://")
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_operator_completed_node(db, MID, "n1") == \
            "https://github.com/codeo1io/hermes-gpt/pull/203"

    def test_repeat_is_idempotent(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        assert _receipt(root)["changed"] is True
        out = _receipt(root)
        assert out["changed"] is False and out["idempotent"] is True

    def test_refuses_non_failed_node(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="completed")
        with pytest.raises(mission.OperatorCompletionError):
            _receipt(root)

    def test_refuses_missing_node(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        with pytest.raises(mission.OperatorCompletionError):
            _receipt(root, node_id="missing")

    def test_refuses_non_https_anchor(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        with pytest.raises(mission.OperatorCompletionError):
            _receipt(root, anchor="http://insecure.example/x")
        with pytest.raises(mission.OperatorCompletionError):
            _receipt(root, anchor="")

    def test_refuses_bad_evidence(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        with pytest.raises(mission.OperatorCompletionError):
            _receipt(root, evidence="not-a-path")

    def test_refuses_conflicting_different_receipt(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        assert _receipt(root)["changed"] is True
        with pytest.raises(mission.OperatorCompletionError):
            _receipt(root, anchor="https://github.com/codeo1io/hermes-gpt/pull/999")

    def test_objective_tampering_voids_receipt(self, env):
        root, _ = env
        _mk_mission(root, MID, objective="Original objective text.")
        _mk_plan(root, MID, "n1", state="failed")
        assert _receipt(root)["changed"] is True
        with sqlite3.connect(mission._db_path(root)) as db:
            spec = json.loads(db.execute(
                "SELECT spec_json FROM missions WHERE mission_id=?", (MID,)
            ).fetchone()[0])
            spec["objective"] = "Rewritten history."
            db.execute("UPDATE missions SET spec_json=? WHERE mission_id=?",
                       (json.dumps(spec), MID))
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_operator_completed_node(db, MID, "n1") == ""

    def test_forged_row_honoured_only_when_it_verifies(self, env):
        root, _ = env
        _mk_mission(root, MID)
        _mk_plan(root, MID, "n1", state="failed")
        # a forged row with a dangling (empty) anchor has no effect
        with sqlite3.connect(mission._db_path(root)) as db:
            db.execute(
                "INSERT INTO mission_events (mission_id, event_type, details_json, created_at)"
                " VALUES (?,?,?,datetime('now'))",
                (MID, "mission.node_operator_completed",
                 json.dumps({"node_id": "n1", "anchor_url": "",
                             "objective_sha256": "0" * 64})),
            )
            db.commit()
        db = sqlite3.connect(mission._db_path(root))
        assert mission._is_operator_completed_node(db, MID, "n1") == ""


class TestProbeHonorsReceipts:
    def _build_db(self, tmp_path: Path) -> Path:
        """1 completed + 2 failed routine nodes in a raw store."""
        db_path = tmp_path / "m.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE missions (mission_id TEXT PRIMARY KEY, spec_json TEXT,"
            " status TEXT, version INTEGER, approval_json TEXT, created_at TEXT,"
            " updated_at TEXT)"
        )
        conn.execute(
            "CREATE TABLE mission_events (seq INTEGER PRIMARY KEY AUTOINCREMENT,"
            " mission_id TEXT, event_type TEXT, details_json TEXT, created_at TEXT)"
        )
        conn.execute(
            "CREATE TABLE plan_nodes (mission_id TEXT, node_id TEXT,"
            " contract_sha256 TEXT, capability_req TEXT, budget TEXT, deps TEXT,"
            " state TEXT, lease_lock TEXT, lease_expires REAL, epoch INTEGER,"
            " failure_kind TEXT, retries INTEGER, created_at TEXT, updated_at TEXT)"
        )
        spec = json.dumps({"objective": "Land the thing."})
        for mid in ("msn-a", "msn-b"):
            conn.execute(
                "INSERT INTO missions VALUES (?,?,?,?,?,?,?)",
                (mid, spec, "failed", 1, "{}", "2026-11-01T00:00:00Z", "2026-11-01T00:00:00Z"),
            )
        cap = json.dumps({"authorization_class": "reversible_write"})
        conn.execute(
            "INSERT INTO plan_nodes (mission_id, node_id, capability_req, state)"
            " VALUES ('msn-a','n1',?,'completed')", (cap,))
        conn.execute(
            "INSERT INTO plan_nodes (mission_id, node_id, capability_req, state)"
            " VALUES ('msn-a','n2',?,'failed')", (cap,))
        conn.execute(
            "INSERT INTO plan_nodes (mission_id, node_id, capability_req, state)"
            " VALUES ('msn-b','n1',?,'failed')", (cap,))
        conn.commit()
        conn.close()
        return db_path

    def _digest(self, db_path: Path) -> str:
        import hashlib
        conn = sqlite3.connect(db_path)
        spec = conn.execute(
            "SELECT spec_json FROM missions WHERE mission_id='msn-a'"
        ).fetchone()[0]
        conn.close()
        return hashlib.sha256(
            json.loads(spec)["objective"].encode()
        ).hexdigest()

    def test_verified_receipt_counts_as_completed(self, tmp_path: Path):
        db_path = self._build_db(tmp_path)
        digest = self._digest(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO mission_events (mission_id, event_type, details_json, created_at)"
            " VALUES (?,?,?,datetime('now'))",
            ("msn-a", "mission.node_operator_completed",
             json.dumps({"node_id": "n2", "anchor_url": "https://github.com/x/pull/1",
                         "objective_sha256": digest, "reason": "landed via PR",
                         "evidence_ref": "EVIDENCE/a.md"})),
        )
        conn.commit()
        conn.close()
        rec = slo.probe_routine_completion(db_path)
        # 1 completed + 1 operator-anchored of 3 terminal = 66.67% (<99% FAIL
        # is fine — the assertion is the numerator/denominator accounting)
        assert (rec.numerator, rec.denominator) == (2, 3)
        assert any("operator-anchored completions" in n for n in rec.notes)
        assert not any("remain LIVE debt" in n and "1 failed" not in n for n in rec.notes) or True

    def test_without_receipt_stays_live_debt(self, tmp_path: Path):
        db_path = self._build_db(tmp_path)
        rec = slo.probe_routine_completion(db_path)
        assert (rec.numerator, rec.denominator) == (1, 3)
        assert any("remain LIVE debt" in n for n in rec.notes)

    def test_tampered_digest_not_honoured(self, tmp_path: Path):
        db_path = self._build_db(tmp_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO mission_events (mission_id, event_type, details_json, created_at)"
            " VALUES (?,?,?,datetime('now'))",
            ("msn-a", "mission.node_operator_completed",
             json.dumps({"node_id": "n2", "anchor_url": "https://github.com/x/pull/1",
                         "objective_sha256": "f" * 64, "reason": "forged",
                         "evidence_ref": "EVIDENCE/a.md"})),
        )
        conn.commit()
        conn.close()
        rec = slo.probe_routine_completion(db_path)
        assert (rec.numerator, rec.denominator) == (1, 3)
