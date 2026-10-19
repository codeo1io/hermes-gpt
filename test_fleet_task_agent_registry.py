"""rm-156: fleet task->agent registry correctness and cancellation observation.

Regression suite for the P1 where ``_task_agent_registry_path`` resolved the
default home via ``op.default_home()`` — a name that does not exist on
operator_policy — so with HERMES_HOME unset every registry write raised
AttributeError (silently swallowed) and every fleet-delegation cancel
observed UNKNOWN_AGENT (RUNNER_CANCEL_UNOBSERVABLE; the cancellation latch
was held forever).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

import operator_delegations as delegations
import operator_fleet as op_fleet
import operator_policy as op
import operator_runners as runners


def _enable_workspace(monkeypatch: pytest.MonkeyPatch, workspace: Path) -> None:
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PATHS_ENV, str(workspace))


def _read_registry(root: Path) -> dict[str, str]:
    return json.loads((op_fleet._task_agent_registry_path(root)).read_text("utf-8"))


# --- resolver ---------------------------------------------------------------

def test_registry_path_resolves_default_home_without_op_default_home(tmp_path, monkeypatch):
    # F1 repro: HERMES_HOME unset must resolve via Path.home()/.hermes without
    # AttributeError (op.default_home never existed on operator_policy).
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    assert op_fleet._task_agent_registry_path(None) == home / ".hermes" / "fleet-task-agents.json"


def test_registry_path_honors_hermes_home_env_and_explicit_root(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "custom"))
    assert op_fleet._task_agent_registry_path(None) == tmp_path / "custom" / "fleet-task-agents.json"
    # explicit root wins over the environment
    assert op_fleet._task_agent_registry_path(tmp_path / "root") == tmp_path / "root" / "fleet-task-agents.json"


# --- registry writes ---------------------------------------------------------

def test_registry_roundtrip_is_root_scoped(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    op_fleet._record_task_agent("a2a-task-1", "rza", root_a)
    op_fleet._record_task_agent("a2a-task-2", "gza", root_b)
    assert op_fleet._task_agent("a2a-task-1", root_a) == "rza"
    assert op_fleet._task_agent("a2a-task-2", root_b) == "gza"
    # no cross-root leak, and nothing lands in the default home
    assert op_fleet._task_agent("a2a-task-2", root_a) == ""
    assert not (home / ".hermes" / "fleet-task-agents.json").exists()


def test_registry_corrupt_file_is_logged_and_restarts(tmp_path, caplog):
    path = op_fleet._task_agent_registry_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", "utf-8")
    with caplog.at_level(logging.WARNING, logger="operator_fleet"):
        op_fleet._record_task_agent("a2a-task-x", "rza", tmp_path)
    assert "unreadable" in caplog.text
    assert op_fleet._task_agent("a2a-task-x", tmp_path) == "rza"


def test_registry_write_failure_is_logged_and_does_not_raise(tmp_path, caplog):
    # parent exists as a FILE -> mkdir fails -> logged, never raised
    blocker = tmp_path / "blocker"
    blocker.write_text("x", "utf-8")
    with caplog.at_level(logging.WARNING, logger="operator_fleet"):
        op_fleet._record_task_agent("a2a-task-y", "rza", blocker)
    assert "write failed" in caplog.text


def test_registry_prune_is_recency_based_and_never_evicts_the_just_written(tmp_path, monkeypatch):
    monkeypatch.setattr(op_fleet, "_FLEET_TASK_AGENT_REGISTRY_MAX", 4)
    for i in (1, 2, 3, 4):
        op_fleet._record_task_agent(f"z-task-000{i}", f"old-{i}", tmp_path)
    # "a-just-written" sorts FIRST lexicographically; a lexicographic trim
    # would evict exactly the mapping this call exists to persist.
    op_fleet._record_task_agent("a-just-written", "fresh", tmp_path)
    data = _read_registry(tmp_path)
    assert len(data) == 4
    assert data["a-just-written"] == "fresh"
    assert "z-task-0001" not in data  # oldest evicted
    assert "z-task-0004" in data


def test_registry_rerecord_refreshes_recency(tmp_path, monkeypatch):
    monkeypatch.setattr(op_fleet, "_FLEET_TASK_AGENT_REGISTRY_MAX", 3)
    op_fleet._record_task_agent("t-1", "a1", tmp_path)
    op_fleet._record_task_agent("t-2", "a2", tmp_path)
    op_fleet._record_task_agent("t-3", "a3", tmp_path)
    op_fleet._record_task_agent("t-1", "a1", tmp_path)  # refresh recency of t-1
    op_fleet._record_task_agent("t-4", "a4", tmp_path)  # evicts t-2 (LRU), not t-1
    data = _read_registry(tmp_path)
    assert set(data) == {"t-1", "t-3", "t-4"}


def test_registry_records_contract_task_id_alias(tmp_path):
    # A peer may mint its own A2A task id that differs from the Work
    # Contract's task_id; the registry must also key the caller-facing id
    # (that is what hermes_delegation_cancel resolves by).
    op_fleet._record_task_agent("a2a-peer-minted", "rza", tmp_path, alias_task_id="ap-msn-n1-k1")
    data = _read_registry(tmp_path)
    assert data == {"a2a-peer-minted": "rza", "ap-msn-n1-k1": "rza"}
    assert op_fleet._task_agent("ap-msn-n1-k1", tmp_path) == "rza"


def test_registry_alias_requires_a_valid_task_id_shape(tmp_path):
    op_fleet._record_task_agent("a2a-real", "rza", tmp_path, alias_task_id="not a task id!")
    data = _read_registry(tmp_path)
    assert "not a task id!" not in data
    assert data == {"a2a-real": "rza"}


# --- cancellation observation through the REAL resolver ----------------------

def _capture_fleet_task(monkeypatch, state="completed"):
    calls = []

    def fake_task(agent, task_id, timeout=15, *, runner=None, hermes_bin=None):
        calls.append({"agent": agent, "task_id": task_id})
        return json.dumps({"success": True, "state": state, "task_id": task_id, "agent": agent})

    monkeypatch.setattr(op_fleet, "hermes_fleet_task", fake_task)
    return calls


def test_cancel_resolves_peer_from_registry_through_real_resolver(tmp_path, monkeypatch):
    # F9 gap: the only prior FleetBackend.cancel test monkeypatched
    # _peer_for_task itself — bypassing the resolver is exactly how the F1
    # AttributeError shipped. This test exercises the real resolver.
    calls = _capture_fleet_task(monkeypatch)
    op_fleet._record_task_agent("a2a-live-task", "rza", tmp_path)
    out = runners.FleetBackend().cancel("a2a-live-task", hermes_root=tmp_path)
    assert calls == [{"agent": "rza", "task_id": "a2a-live-task"}]
    assert out.get("proven_terminal") is True


def test_cancel_resolves_peer_via_default_home_with_hermes_home_unset(tmp_path, monkeypatch):
    # F1 end-to-end: write without an explicit root lands in the default
    # home; cancel without an explicit root must resolve it there (pre-fix
    # both sides raised/swallowed AttributeError -> RUNNER_CANCEL_UNOBSERVABLE).
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    calls = _capture_fleet_task(monkeypatch)
    op_fleet._record_task_agent("a2a-default-home", "gza")
    out = runners.FleetBackend().cancel("a2a-default-home")
    assert calls and calls[0]["agent"] == "gza"
    assert out.get("proven_terminal") is True


def test_cancel_resolves_peer_via_the_alias_recorded_at_dispatch(tmp_path, monkeypatch):
    calls = _capture_fleet_task(monkeypatch)
    op_fleet._record_task_agent("a2a-peer-minted", "rza", tmp_path, alias_task_id="ap-msn-n1-k1")
    out = runners.FleetBackend().cancel("ap-msn-n1-k1", hermes_root=tmp_path)
    assert calls == [{"agent": "rza", "task_id": "ap-msn-n1-k1"}]
    assert out.get("proven_terminal") is True


def test_cancel_falls_back_to_the_contracts_own_agent(tmp_path, monkeypatch):
    # Registry lost / never written: the delegation's own Work Contract
    # carries assigned_agent; cancel must still resolve the peer —
    # pre-registry rows were RUNNER_CANCEL_UNOBSERVABLE forever.
    workspace = tmp_path / "ws"
    workspace.mkdir()
    root = tmp_path / "hermes"
    op.set_audit_log_override(tmp_path / "audit.jsonl")
    _enable_workspace(monkeypatch, workspace)

    import operator_mission_runtime as mission

    spec = json.dumps({
        "schema": mission.MISSION_SPEC_SCHEMA, "mission_id": "msn-fleet-fallback",
        "title": "fleet fallback", "objective": "resolve the peer from the contract.",
        "owner_profile": "default", "acceptance_criteria": ["done"], "context_refs": [],
        "skills": [], "final_approval_required": True,
    })
    assert json.loads(mission.hermes_mission_create(spec, confirm=True, dry_run=False, hermes_root=root))["success"]

    # item-252 dispatch shape: the fleet contract itself carries the
    # assigned agent the fallback must resolve.
    contract = {
        "schema": "hermes.work-contract/v1",
        "task_id": "fleet-fallback-task-001",
        "assigned_agent": "hermes-researcher",
        "assigned_profile": "default",
        "objective": "verify the contract-side cancel fallback (rm-156)",
        "allowed_scope": {"workspaces": [str(workspace)], "profiles": ["default"]},
        "forbidden_actions": [],
        "expected_artifacts": [],
        "tests": [],
        "review_requirements": {},
        "completion_criteria": {
            "run_state": {"terminal": True, "outcome_ok": ["completed"]},
            "artifacts_present": False,
            "tests_pass": False,
            "review_satisfied": False,
            "no_forbidden_actions": True,
        },
        "inputs": [],
        "constraints": [],
        "authorization": {
            "class": "reversible_write",
            "approved": True,
            "approved_by": "owner",
            "approval_reference": "test",
        },
        "execution": {"backend": "fleet", "options": {}},
    }

    def _fake_dispatch_ok(contract_json: str, **kwargs) -> str:
        return json.dumps({"success": True, "changed": True, "state": "running",
                           "backend": "fleet",
                           "task_id": json.loads(contract_json)["task_id"]})

    monkeypatch.setattr(delegations.contract_mod, "hermes_contract_dispatch", _fake_dispatch_ok)
    out = json.loads(delegations.hermes_delegation_dispatch(
        json.dumps(contract),
        mission_id="msn-fleet-fallback", delegation_id="dlg-fleet-fallback",
        confirm=True, dry_run=False, hermes_root=root),
    )
    assert out["success"] is True and out["changed"] is True, out
    task_id = out["delegation"]["task_id"]

    # no registry entry anywhere: the fallback must read the delegation's manifest
    assert not op_fleet._task_agent_registry_path(root).exists()
    calls = _capture_fleet_task(monkeypatch)
    result = runners.FleetBackend().cancel(task_id, hermes_root=root)
    assert calls and calls[0]["agent"] == "hermes-researcher"
    assert result.get("proven_terminal") is True
