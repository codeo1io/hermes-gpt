"""Private, digest-pinned native mission work-order dispatch regression."""

import hashlib
import json

import pytest

import operator_autopilot as ap
import operator_mission_plan as plan
import operator_policy as op


def _setup(tmp_path, monkeypatch):
    root = tmp_path / "hermes"
    root.mkdir()
    repo = tmp_path / "authorized-repo"
    repo.mkdir()
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PATHS_ENV, str(tmp_path))
    mission_id = "msn-workorder-test"
    node_id = "native-dev"
    objective = "Make a real, tested change to the authorized repository."
    directory = root / "missions" / "workorders" / mission_id
    directory.mkdir(parents=True)
    blob = json.dumps({"objective": objective, "workspaces": [str(repo)]}, sort_keys=True).encode()
    digest = hashlib.sha256(blob).hexdigest()
    path = directory / (node_id + ".json")
    path.write_bytes(blob)
    node = plan._canonical_node({
        "node_id": node_id, "kind": "single", "owner": "default",
        "parents": [], "objective": objective,
        "contract_ref": f"workorder:{mission_id}/{node_id}@{digest}",
        "capability_req": {"profile": "default", "skills": [],
                           "authorization_class": "reversible_write"},
        "budget": {"est_minutes": 60, "est_tokens": 20000},
        "expected_artifacts": ["m9-merge-receipt.json"],
    })
    return root, repo, path, mission_id, node, objective


def test_authorized_workorder_objective_and_scope_reach_contract(tmp_path, monkeypatch):
    root, repo, path, mission_id, node, objective = _setup(tmp_path, monkeypatch)
    assert "objective" not in node  # INV-9: private raw prompt not in MissionPlan
    built = ap._build_contract(
        mission_id, node, requirement=node["capability_req"], agent="default",
        key="a" * 64, attempt=0, hermes_root=root,
    )
    assert built["objective"] == objective
    assert str(repo) in built["allowed_scope"]["workspaces"]
    assert str(root / "missions" / "artifacts" / built["task_id"]) in built["allowed_scope"]["workspaces"]
    # Same immutable work order can be reconstructed on crash recovery.
    assert ap._verified_workorder(mission_id, node, root)[0] == objective


def test_workorder_tamper_and_plan_hash_mismatch_fail_closed(tmp_path, monkeypatch):
    root, repo, path, mission_id, node, objective = _setup(tmp_path, monkeypatch)
    path.write_text(json.dumps({"objective": "Changed job", "workspaces": [str(repo)]}))
    with pytest.raises(ValueError, match="digest mismatch"):
        ap._build_contract(
            mission_id, node, requirement=node["capability_req"], agent="default",
            key="a" * 64, attempt=0, hermes_root=root,
        )
    # Pinning the work order bytes is necessary but objective hash must match.
    blob = path.read_bytes()
    node["contract_ref"] = f"workorder:{mission_id}/{node['node_id']}@" + hashlib.sha256(blob).hexdigest()
    with pytest.raises(ValueError, match="does not match PlanNode"):
        ap._verified_workorder(mission_id, node, root)


def test_workorder_identity_and_scope_fail_closed(tmp_path, monkeypatch):
    root, repo, path, mission_id, node, objective = _setup(tmp_path, monkeypatch)
    node["contract_ref"] = node["contract_ref"].replace(mission_id, "msn-other")
    with pytest.raises(ValueError, match="mismatched"):
        ap._verified_workorder(mission_id, node, root)
    node["contract_ref"] = node["contract_ref"].replace("msn-other", mission_id)
    other = tmp_path.parent / "not-authorized"
    other.mkdir(exist_ok=True)
    blob = json.dumps({"objective": objective, "workspaces": [str(other)]}, sort_keys=True).encode()
    path.write_bytes(blob)
    node["contract_ref"] = f"workorder:{mission_id}/{node['node_id']}@" + hashlib.sha256(blob).hexdigest()
    with pytest.raises(PermissionError):
        ap._verified_workorder(mission_id, node, root)
