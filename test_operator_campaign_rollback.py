"""M6 canary ramp/rollback pin: unregister is the reversible campaign switch.

Production semantics proven live 2026-11-12 (family nrm-m6-canary-rollback,
EVIDENCE/M6/owner-m6-canary-rollback-20261112T*.json) and pinned here:

1. a recurring family mid-recurrence, whose next generation is DUE (pacing
   anchor backdated past interval_s), never mints that generation once the
   family is unregistered — no matter how many lane passes run afterwards;
2. containment: the controller state and the minted missions survive the
   switch untouched (the lane never mutates what it does not own);
3. reversibility: re-registering the same manifest resumes recurrence from
   the controller's own state — the owed generation mints via the normal
   rollover path, with no duplicate side effects.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import operator_autopilot as autopilot
import operator_campaign_lane as lane
import operator_mission_runtime as mission
import operator_policy as op

from test_operator_campaign_controller import (
    _backdate_finished,
    _rec_manifest,
    _set_generation_outcome,
)


@pytest.fixture
def hermes_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mirrors test_operator_campaign_controller.hermes_root (self-contained)."""
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


def _manifest_file(tmp_path: Path, name: str, manifest: str) -> Path:
    path = tmp_path / name
    path.write_text(manifest, encoding="utf-8")
    return path


def _register(path: Path, root: Path) -> dict:
    return json.loads(lane.register_campaign(
        path, confirm=True, apply=True, hermes_root=root))


def _run(root: Path, **kw) -> dict:
    kw.setdefault("confirm", True)
    kw.setdefault("apply", True)
    return json.loads(lane.campaign_lane_run(hermes_root=root, **kw))


def _mission_exists(root: Path, mid: str) -> bool:
    return json.loads(mission.hermes_mission_get(mid, hermes_root=root)).get(
        "success") is True


def test_unregister_with_due_rollover_never_mints_next_generation(
    hermes_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # hermetic autopilot start seam (same as the controller recurrence tests)
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"),
                                                      state="running")}))

    path = _manifest_file(tmp_path, "camp.json", _rec_manifest())
    assert _register(path, hermes_root)["success"] is True
    _run(hermes_root)   # tick 1: mint g1
    _run(hermes_root)   # tick 2: plan + start g1
    _set_generation_outcome(hermes_root, "msn-camp-recur-g1", "completed")
    out = _run(hermes_root)   # tick 3: g1 terminal -> outcome recorded, pacing started
    assert out["all_ok"] is True
    state = json.loads((hermes_root / "campaigns" / "camp-test" / "state.json").read_text())
    assert state["generation_history"][-1]["outcome"] == "succeeded"

    # make the next generation DUE (pacing anchor backdated past interval_s)
    _backdate_finished(hermes_root, "camp-test", seconds=120)

    # the switch: rollback before the lane ever mints g2
    unreg = json.loads(lane.unregister_campaign(
        "camp-test", confirm=True, apply=True, hermes_root=hermes_root))
    assert unreg["success"] is True
    assert [e["campaign_id"] for e in unreg["removed"]] == ["camp-test"]

    # the owed generation never mints, across repeated lane passes
    for _ in range(3):
        after = _run(hermes_root)
        assert after["success"] is True
        assert after["campaigns"] == []  # registry empty: nothing to tick
        assert _mission_exists(hermes_root, "msn-camp-recur-g2") is False

    # containment: the family's state and the terminal g1 mission survive
    assert (hermes_root / "campaigns" / "camp-test" / "state.json").is_file()
    g1 = json.loads(mission.hermes_mission_get("msn-camp-recur-g1", hermes_root=hermes_root))
    assert g1.get("success") is True and g1["status"] == "completed"


def test_reregister_resumes_recurrence_via_rollover_no_duplicates(
    hermes_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(autopilot, "hermes_autopilot_start", lambda mid, **kw: json.dumps(
        {"success": True, "run": autopilot._write_run(mid, kw.get("hermes_root"),
                                                      state="running")}))

    path = _manifest_file(tmp_path, "camp.json", _rec_manifest())
    assert _register(path, hermes_root)["success"] is True
    _run(hermes_root)
    _run(hermes_root)
    _set_generation_outcome(hermes_root, "msn-camp-recur-g1", "completed")
    _run(hermes_root)   # outcome recorded
    _backdate_finished(hermes_root, "camp-test", seconds=120)
    assert json.loads(lane.unregister_campaign(
        "camp-test", confirm=True, apply=True, hermes_root=hermes_root))["success"] is True

    # ramp back up: the SAME manifest re-registers and recurrence resumes
    re = _register(path, hermes_root)
    assert re["success"] is True and re["already_registered"] is False
    resumed = _run(hermes_root)   # rollover due: g2 mints in this pass
    view = resumed["campaigns"][0]
    assert view["ok"] is True
    assert view["actions"].get("mission_create", 0) == 1
    assert _mission_exists(hermes_root, "msn-camp-recur-g2") is True

    # no duplicate side effects: exactly one g1 and one g2 exist
    ids = [m["mission_id"] for m in json.loads(
        mission.hermes_mission_list(hermes_root=hermes_root))["missions"]]
    assert sorted(ids) == ["msn-camp-recur-g1", "msn-camp-recur-g2"]

    # state continuity: generation advanced from the controller's own truth
    state = json.loads((hermes_root / "campaigns" / "camp-test" / "state.json").read_text())
    assert state["generation"] == 2
    assert len(state["generation_history"]) == 1  # g1's record intact, not reset
