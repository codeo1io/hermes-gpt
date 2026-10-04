"""Fork addition: typed MissionSpec approval_policy field.

The approval frontier and Autopilot are unchanged — they still never approve.
This field only lets a Mission DECLARE, at mint time, that an owner-side
resolver may resolve its final gate once evidence is independently
re-verified. Default (absent) is exactly upstream behavior: owner-gated.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import operator_policy as op
import operator_mission_runtime as mr


@pytest.fixture
def hermes_root(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "hermes"
    root.mkdir()
    op.set_audit_log_override(tmp_path / "audit.jsonl")
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.delenv(op.OWNER_ACTIVE_ENV, raising=False)
    monkeypatch.delenv(op.OWNER_ACK_ENV, raising=False)
    monkeypatch.setattr(Path, "home", lambda: root)
    return root


def _spec_db(root: Path, mid: str) -> dict:
    db = sqlite3.connect(root / "missions" / "missions.db")
    row = db.execute("SELECT spec_json FROM missions WHERE mission_id=?", (mid,)).fetchone()
    return json.loads(row[0])


def _create(root, mid, **extra):
    return json.loads(mr.hermes_mission_create(
        json.dumps({"mission_id": mid, "title": "T", "objective": "O", **extra}),
        confirm=True, dry_run=False, hermes_root=root))


def test_absent_policy_defaults_to_owner(hermes_root):
    assert _create(hermes_root, "msn-p1")["changed"] is True
    assert _spec_db(hermes_root, "msn-p1")["approval_policy"] == {"policy": "owner"}


def test_auto_policy_round_trips(hermes_root):
    _create(hermes_root, "msn-p2", approval_policy={"policy": "auto_when_evidence_verified", "max_wait_seconds": 300})
    assert _spec_db(hermes_root, "msn-p2")["approval_policy"] == {"policy": "auto_when_evidence_verified", "max_wait_seconds": 300}


def test_string_owner_is_normalized(hermes_root):
    _create(hermes_root, "msn-p3", approval_policy="owner")
    assert _spec_db(hermes_root, "msn-p3")["approval_policy"] == {"policy": "owner"}


def test_unknown_policy_rejected(hermes_root):
    out = _create(hermes_root, "msn-p4", approval_policy={"policy": "yolo"})
    assert out["success"] is False
    assert "auto_when_evidence_verified" in out["error"]


def test_max_wait_bounds(hermes_root):
    assert _create(hermes_root, "msn-p5", approval_policy={"policy": "auto_when_evidence_verified", "max_wait_seconds": 999999})["success"] is False
    assert _create(hermes_root, "msn-p6", approval_policy={"policy": "auto_when_evidence_verified", "max_wait_seconds": True})["success"] is False


def test_policy_immutable_after_mint(hermes_root):
    _create(hermes_root, "msn-p7", approval_policy={"policy": "auto_when_evidence_verified"})
    out = json.loads(mr.hermes_mission_update(
        "msn-p7", json.dumps({"approval_policy": {"policy": "owner"}}),
        confirm=True, dry_run=False, hermes_root=hermes_root))
    assert out["success"] is False
    assert "unknown fields" in out["error"]


def test_extra_policy_keys_rejected(hermes_root):
    out = _create(hermes_root, "msn-p8", approval_policy={"policy": "owner", "who": "me"})
    assert out["success"] is False
    assert "unknown fields" in out["error"]
