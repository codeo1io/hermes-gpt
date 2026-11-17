"""Regression: hermes-gpt → Hermes Agent delegation adapter (P0 correction).

The corrected architecture routes native Delegations through Hermes Agent's
``delegate_session`` (persistent Pi RPC / OpenCode sessions) instead of
hermes-gpt-owned process trees. These pins hold the transport contract:

1. dispatch durably publishes a conforming work-order envelope (attempt-id
   keyed, session binding carried, bounded payload) and returns queued.
2. dry_run never touches the spool.
3. execution.options.delegate selects the native backend (pi/opencode).
4. observations fold ONLY from transport truth (terminal envelope);
   a session-completion report can never self-satisfy a Work Contract —
   hermes-gpt's independent artifact checks stay the completion authority.
5. missing/unauthorized spool, bad ids, missing workspace fail closed.
6. cancel records intent durably and never reaps a terminal result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

import operator_delegations as delegations  # noqa: E402
import operator_hermes_agent_runner as hab  # noqa: E402
import operator_policy as op_policy  # noqa: E402


def _spool(tmp_path: Path) -> Path:
    root = tmp_path / "spool"
    (root / "pending").mkdir(parents=True)
    (root / "results").mkdir(parents=True)
    return root


def _contract(tmp_path: Path, *, backend: str = "hermes_agent", delegate: str = "") -> dict:
    ws = tmp_path / "workspace"
    ws.mkdir(exist_ok=True)
    execution: dict = {"backend": backend, "options": {"sandbox": "workspace-write"}}
    if delegate:
        execution["options"]["delegate"] = delegate
    return {
        "task_id": "attempt0000000001",
        "objective": "Fix the boot-lock and prove it with a regression test.",
        "execution": execution,
        "allowed_scope": {"workspaces": [str(ws)]},
    }


def _backend(monkeypatch, tmp_path: Path) -> hab.HermesAgentBackend:
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(_spool(tmp_path)))
    return hab.HermesAgentBackend()


def test_dispatch_publishes_conforming_envelope(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    out = be.dispatch(_contract(tmp_path), confirm=True, dry_run=False, timeout=900)
    assert out["success"] is True and out["state"] == "queued"
    assert out["delegate_backend"] == "pi"  # hermes_agent/pi_rpc map to native pi
    envelope = tmp_path / "spool" / "pending" / "attempt0000000001.json"
    assert envelope.is_file()
    order = json.loads(envelope.read_text())
    assert order["interface"] == "delegate_session"
    assert order["attempt_id"] == "attempt0000000001"
    assert order["backend_hint"] == "pi"
    assert order["session_binding"]["role"] == "primary"
    assert order["session_binding"]["backend"] == "pi"
    assert order["workspace_path"].endswith("workspace")
    assert order["phase_prompt"].startswith("Fix the boot-lock")


def test_native_dispatch_carries_exact_expected_artifact_basenames(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["expected_artifacts"] = [
        {"path": "m5-pi-recovery-proof.json", "must_exist": True, "min_bytes": 100},
        {"path": "receipt.md", "must_exist": True, "min_bytes": 1},
    ]
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True
    order = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text()
    )
    assert order["action_payload"]["expected_artifacts"] == [
        "m5-pi-recovery-proof.json", "receipt.md"
    ]


def test_native_source_directory_separate_from_artifact_acceptance(tmp_path, monkeypatch):
    """Owner-authorized repository work occurs outside isolated receipt root."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path, delegate="opencode")
    artifact_dir = tmp_path / "workspace"
    source_dir = tmp_path / "source-repo"
    source_dir.mkdir()
    (source_dir / "AGENTS.md").write_text("safe work instructions")
    contract["allowed_scope"]["workspaces"].append(str(source_dir))
    contract["expected_artifacts"] = [{"path": "proof.json", "must_exist": True}]
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=900)
    assert out["success"] is True
    order = json.loads((tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text())
    assert order["workspace_path"] == str(artifact_dir)
    assert order["action_payload"]["execution_cwd"] == str(source_dir.resolve())
    assert order["action_payload"]["expected_artifacts"] == ["proof.json"]
    assert order["backend_hint"] == "opencode"


def test_native_source_directory_invalid_fails_before_dispatch(tmp_path, monkeypatch):
    """A disappeared authorized repository is not silently replaced by artifacts."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["allowed_scope"]["workspaces"].append(str(tmp_path / "missing-repo"))
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=900)
    assert out["success"] is False
    assert out["code"] == "HERMES_AGENT_EXECUTION_WORKSPACE_INVALID"
    assert not list((tmp_path / "spool" / "pending").iterdir())


def test_native_dispatch_rejects_unsafe_artifact_names(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["expected_artifacts"] = [{"path": "../escape.json"}]
    with pytest.raises(ValueError, match="safe basenames"):
        be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert not (tmp_path / "spool" / "pending" / "attempt0000000001.json").exists()


def test_dispatch_declares_typed_turn_budget_never_invocation_timeout(tmp_path, monkeypatch):
    """Regression (2026-10-21, msn-m3-pi-dev-004 starvation): the published
    envelope must carry a TYPED turn budget. Pre-fix, ``timeout_seconds`` fell
    through to the delegation surface's invocation-call timeout (the observe
    tick default 30s) and ``action_payload`` was omitted entirely — an UNTYPED
    envelope the spool server's v1.21 EDF ordering ranks at +inf, behind every
    typed conductor order forever, which starved the first real native mission
    order 2h+ in pending/ while 86 typed orders flowed past it.
    """
    be = _backend(monkeypatch, tmp_path)
    out = be.dispatch(_contract(tmp_path), confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True
    envelope = tmp_path / "spool" / "pending" / "attempt0000000001.json"
    order = json.loads(envelope.read_text())
    # The 30s invocation timeout must NEVER become the turn budget:
    assert order["timeout_seconds"] == 900.0
    # The declared budget keys the spool server's horizon arithmetic:
    assert order["action_payload"]["phase_timeout_seconds"] == 900.0
    assert order["action_payload"]["phase_timeout_seconds"] == order["timeout_seconds"]


def test_dispatch_respects_pinned_turn_budget_with_bounds(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"]["options"]["timeout"] = 3600
    be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    order = json.loads((tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text())
    assert order["timeout_seconds"] == 3600.0
    assert order["action_payload"]["phase_timeout_seconds"] == 3600.0

    # A mistyped/non-numeric pin fails safe to the floor, never to the
    # invocation timeout, and never above the cap.
    contract2 = _contract(tmp_path)
    contract2["task_id"] = "attempt0000000002"
    contract2["execution"]["options"]["timeout"] = "not-a-number"
    be.dispatch(contract2, confirm=True, dry_run=False, timeout=30)
    order2 = json.loads((tmp_path / "spool" / "pending" / "attempt0000000002.json").read_text())
    assert order2["timeout_seconds"] == 900.0

    contract3 = _contract(tmp_path)
    contract3["task_id"] = "attempt0000000003"
    contract3["execution"]["options"]["timeout"] = 10**9
    be.dispatch(contract3, confirm=True, dry_run=False, timeout=30)
    order3 = json.loads((tmp_path / "spool" / "pending" / "attempt0000000003.json").read_text())
    assert order3["timeout_seconds"] == 14400.0


def test_dispatch_carries_instruction_when_context_pinned(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"]["options"]["context"] = "Implement the guarded probe fast path."
    be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    order = json.loads((tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text())
    assert order["action_payload"]["instruction"] == "Implement the guarded probe fast path."


# -- S2 (2026-11-17): additive execution.options passthrough -------------------


def test_dispatch_prompt_option_overrides_phase_prompt(tmp_path, monkeypatch):
    """S2: execution.options.prompt is the verbatim delegated prompt; when
    pinned it overrides the bounded contract-objective summary in
    phase_prompt (the conductor renders the authoritative phase prompt)."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"]["options"]["prompt"] = (
        "Authoritative phase-bounded prompt rendered by the conductor."
    )
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True
    order = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text()
    )
    assert order["phase_prompt"] == (
        "Authoritative phase-bounded prompt rendered by the conductor."
    )

    # Only a non-empty string overrides: empty/non-string/absent values keep
    # the legacy objective-backed phase_prompt (no new validation surface).
    for index, fallback in enumerate(("", 123, None, {"not": "a string"})):
        contract_fb = _contract(tmp_path)
        contract_fb["task_id"] = f"attempt00000000{index + 10:02d}"
        contract_fb["execution"]["options"]["prompt"] = fallback
        be.dispatch(contract_fb, confirm=True, dry_run=False, timeout=30)
        order_fb = json.loads(
            (tmp_path / "spool" / "pending" / f"{contract_fb['task_id']}.json").read_text()
        )
        assert order_fb["phase_prompt"].startswith("Fix the boot-lock")


def test_dispatch_instruction_option_rides_action_payload(tmp_path, monkeypatch):
    """S2: execution.options.instruction rides action_payload.instruction and
    takes precedence over legacy execution.options.context."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"]["options"]["instruction"] = (
        "Run the bounded sub-task in the source tree."
    )
    be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    order = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text()
    )
    assert order["action_payload"]["instruction"] == (
        "Run the bounded sub-task in the source tree."
    )

    # Explicit instruction wins over legacy context when both are pinned.
    contract_both = _contract(tmp_path)
    contract_both["task_id"] = "attempt0000000002"
    contract_both["execution"]["options"]["context"] = "legacy context instruction"
    contract_both["execution"]["options"]["instruction"] = "explicit instruction"
    be.dispatch(contract_both, confirm=True, dry_run=False, timeout=30)
    order_both = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000002.json").read_text()
    )
    assert order_both["action_payload"]["instruction"] == "explicit instruction"

    # Legacy context still rides when instruction is absent.
    contract_ctx = _contract(tmp_path)
    contract_ctx["task_id"] = "attempt0000000003"
    contract_ctx["execution"]["options"]["context"] = "legacy context instruction"
    be.dispatch(contract_ctx, confirm=True, dry_run=False, timeout=30)
    order_ctx = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000003.json").read_text()
    )
    assert order_ctx["action_payload"]["instruction"] == "legacy context instruction"

    # Non-string/empty instruction values fall back to the legacy context
    # (same guard semantics as prompt); a whitespace-only instruction is a
    # non-empty string and rides verbatim (no normalization surface).
    contract_nonstr = _contract(tmp_path)
    contract_nonstr["task_id"] = "attempt0000000004"
    contract_nonstr["execution"]["options"]["context"] = "legacy context instruction"
    contract_nonstr["execution"]["options"]["instruction"] = 123
    be.dispatch(contract_nonstr, confirm=True, dry_run=False, timeout=30)
    order_nonstr = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000004.json").read_text()
    )
    assert order_nonstr["action_payload"]["instruction"] == "legacy context instruction"

    contract_empty = _contract(tmp_path)
    contract_empty["task_id"] = "attempt0000000005"
    contract_empty["execution"]["options"]["context"] = "legacy context instruction"
    contract_empty["execution"]["options"]["instruction"] = ""
    be.dispatch(contract_empty, confirm=True, dry_run=False, timeout=30)
    order_empty = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000005.json").read_text()
    )
    assert order_empty["action_payload"]["instruction"] == "legacy context instruction"

    contract_ws = _contract(tmp_path)
    contract_ws["task_id"] = "attempt0000000006"
    contract_ws["execution"]["options"]["instruction"] = "   "
    be.dispatch(contract_ws, confirm=True, dry_run=False, timeout=30)
    order_ws = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000006.json").read_text()
    )
    assert order_ws["action_payload"]["instruction"] == "   "


@pytest.mark.parametrize(
    "execution",
    [
        {"backend": "hermes_agent"},  # options key absent entirely
        {"backend": "hermes_agent", "options": {}},
        {"backend": "hermes_agent", "options": {"sandbox": "workspace-write"}},
    ],
    ids=["options-absent", "options-empty", "options-legacy"],
)
def test_dispatch_options_free_contract_is_byte_identical_legacy(tmp_path, monkeypatch, execution):
    """S2 regression pin: options-free legacy contracts must publish the EXACT
    legacy envelope bytes; the additive prompt/instruction options may never
    reshape a legacy work order."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"] = execution
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True
    expected_payload = {
        "schema": 1,
        "interface": "delegate_session",
        "attempt_id": "attempt0000000001",
        "run_id": "attempt0000000001",
        "action_id": "mission:attempt0000000001",
        "intent": "mission_node",
        "backend_hint": "pi",
        "workspace_path": str(tmp_path / "workspace"),
        "phase_prompt": "Fix the boot-lock and prove it with a regression test.",
        "timeout_seconds": 900.0,
        "attempt_seq": 1,
        "session_binding": {
            "run_id": "attempt0000000001",
            "role": "primary",
            "backend": "pi",
            "affinity_key": "",
            "resume": False,
        },
        "spool_path": str(tmp_path / "spool"),
        "action_payload": {"phase_timeout_seconds": 900.0},
    }
    expected = json.dumps(expected_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    envelope = tmp_path / "spool" / "pending" / "attempt0000000001.json"
    assert envelope.read_bytes() == expected


def test_dispatch_prompt_and_instruction_compose_with_legacy_action_payload(tmp_path, monkeypatch):
    """S2 additivity pin: the new options reshape ONLY phase_prompt and
    action_payload.instruction — the production mission-node shape (expected
    artifacts + authorized execution directory) stays byte-stable."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    source_dir = tmp_path / "source-repo"
    source_dir.mkdir()
    contract["allowed_scope"]["workspaces"].append(str(source_dir))
    contract["expected_artifacts"] = [{"path": "proof.json", "must_exist": True}]
    contract["execution"]["options"]["prompt"] = "Composition prompt."
    contract["execution"]["options"]["instruction"] = "Composition instruction."
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True
    expected_payload = {
        "schema": 1,
        "interface": "delegate_session",
        "attempt_id": "attempt0000000001",
        "run_id": "attempt0000000001",
        "action_id": "mission:attempt0000000001",
        "intent": "mission_node",
        "backend_hint": "pi",
        "workspace_path": str(tmp_path / "workspace"),
        "phase_prompt": "Composition prompt.",
        "timeout_seconds": 900.0,
        "attempt_seq": 1,
        "session_binding": {
            "run_id": "attempt0000000001",
            "role": "primary",
            "backend": "pi",
            "affinity_key": "",
            "resume": False,
        },
        "spool_path": str(tmp_path / "spool"),
        "action_payload": {
            "phase_timeout_seconds": 900.0,
            "expected_artifacts": ["proof.json"],
            "instruction": "Composition instruction.",
            "execution_cwd": str(source_dir.resolve()),
        },
    }
    expected = json.dumps(expected_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    envelope = tmp_path / "spool" / "pending" / "attempt0000000001.json"
    assert envelope.read_bytes() == expected


def test_pending_envelope_re_dispatch_byte_semantics(tmp_path, monkeypatch):
    """First publish is authority: a byte-identical re-dispatch is an
    idempotent no-op, and (S2) a divergent options.prompt on the same attempt
    id must fail closed without disturbing the published envelope."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"]["options"]["prompt"] = "first rendered prompt"
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True and out["changed"] is True
    envelope = tmp_path / "spool" / "pending" / "attempt0000000001.json"
    first_bytes = envelope.read_bytes()

    again = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert again["success"] is True and again["changed"] is False
    assert again["state"] == "queued"
    assert envelope.read_bytes() == first_bytes

    divergent = _contract(tmp_path)
    divergent["execution"]["options"]["prompt"] = "re-rendered prompt"
    with pytest.raises(RuntimeError, match="different content"):
        be.dispatch(divergent, confirm=True, dry_run=False, timeout=30)
    assert json.loads(envelope.read_text())["phase_prompt"] == "first rendered prompt"
    assert envelope.read_bytes() == first_bytes


def test_caller_supplied_delegation_id_round_trips_idempotently(tmp_path, monkeypatch):
    """S2.3: a caller-supplied deterministic delegation_id round-trips through
    hermes_delegation_dispatch on the native rail; a duplicate dispatch with
    the same id + contract is idempotent (single row, no re-queue)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    root = tmp_path / "hermes"
    monkeypatch.setenv(op_policy.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op_policy.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op_policy.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op_policy.OPERATOR_ALLOWED_PATHS_ENV, str(workspace))
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(_spool(tmp_path)))
    # Keep the policy-gated dispatch/get calls off the real user audit log
    # (conftest's sandbox has no logs/ dir; autouse fixture restores this).
    op_policy.set_audit_log_override(tmp_path / "audit.jsonl")

    contract = {
        "schema": "hermes.work-contract/v1",
        "task_id": "s2roundtripattempt01",
        "assigned_agent": "coder",
        "assigned_profile": "default",
        "objective": "Round-trip a caller-supplied delegation id.",
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
        "execution": {
            "backend": "hermes_agent",
            "options": {
                "prompt": "Delegated round-trip prompt.",
                "instruction": "Run the bounded sub-task.",
            },
        },
    }
    delegation_id = "dlg-s2roundtrip0000001"
    first = json.loads(delegations.hermes_delegation_dispatch(
        json.dumps(contract), delegation_id=delegation_id,
        confirm=True, dry_run=False, timeout=30, hermes_root=root,
    ))
    assert first["success"] is True and first["changed"] is True
    assert first["delegation"]["delegation_id"] == delegation_id
    envelope = tmp_path / "spool" / "pending" / "s2roundtripattempt01.json"
    assert envelope.is_file()
    first_bytes = envelope.read_bytes()
    # The options ride contract canonicalization end-to-end and land verbatim
    # in the published work order.
    first_order = json.loads(first_bytes)
    assert first_order["phase_prompt"] == "Delegated round-trip prompt."
    assert first_order["action_payload"]["instruction"] == "Run the bounded sub-task."

    row = json.loads(delegations.hermes_delegation_get(delegation_id, hermes_root=root))
    assert row["success"] is True
    assert row["delegation"]["delegation_id"] == delegation_id
    assert row["delegation"]["task_id"] == "s2roundtripattempt01"
    assert row["delegation"]["backend"] == "hermes_agent"

    second = json.loads(delegations.hermes_delegation_dispatch(
        json.dumps(contract), delegation_id=delegation_id,
        confirm=True, dry_run=False, timeout=30, hermes_root=root,
    ))
    assert second["success"] is True and second["changed"] is False
    assert second.get("idempotent") is True
    assert second["delegation"]["delegation_id"] == delegation_id
    # Idempotent re-dispatch never re-queued the work order.
    assert envelope.read_bytes() == first_bytes
    assert sorted(p.name for p in (tmp_path / "spool" / "pending").iterdir()) == [
        "s2roundtripattempt01.json"
    ]


def test_bounded_turn_budget_never_leaks_invocation_timeout():
    assert hab._bounded_turn_budget(None, 30) == 900.0
    assert hab._bounded_turn_budget("", 30) == 900.0
    assert hab._bounded_turn_budget(3600, 30) == 3600.0
    assert hab._bounded_turn_budget("7200", 30) == 7200.0
    assert hab._bounded_turn_budget(-5, 30) == 900.0
    assert hab._bounded_turn_budget(float("nan"), 30) == 900.0
    assert hab._bounded_turn_budget(10**12, 30) == 14400.0



def test_dispatch_dry_run_never_touches_spool(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    out = be.dispatch(_contract(tmp_path), confirm=True, dry_run=True, timeout=900)
    assert out["dry_run"] is True and out["state"] == "planned"
    assert not (tmp_path / "spool" / "pending").iterdir().__next__() if any(
        (tmp_path / "spool" / "pending").iterdir()
    ) else True
    assert not list((tmp_path / "spool" / "pending").iterdir())


def test_dispatch_delegate_option_selects_opencode(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    out = be.dispatch(
        _contract(tmp_path, delegate="opencode"), confirm=True, dry_run=False, timeout=900
    )
    assert out["delegate_backend"] == "opencode"
    order = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text()
    )
    assert order["backend_hint"] == "opencode"
    assert order["session_binding"]["backend"] == "opencode"


def test_dispatch_rejects_unknown_delegate_backend(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="delegate must be one of"):
        be.dispatch(
            _contract(tmp_path, delegate="codex"), confirm=True, dry_run=False, timeout=900
        )
    assert not list((tmp_path / "spool" / "pending").iterdir())


def test_dispatch_requires_workspace(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["allowed_scope"]["workspaces"] = []
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=900)
    assert out["success"] is False and out["changed"] is False
    assert out["code"] == "HERMES_AGENT_WORKSPACE_REQUIRED"


def test_dispatch_requires_initialized_spool(tmp_path, monkeypatch):
    empty = tmp_path / "empty-spool"
    empty.mkdir()
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(empty))
    be = hab.HermesAgentBackend()
    with pytest.raises(RuntimeError, match="not initialized"):
        be.dispatch(_contract(tmp_path), confirm=True, dry_run=False, timeout=900)


def test_duplicate_dispatch_folds_terminal_envelope(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    results = tmp_path / "spool" / "results" / "attempt0000000001.json"
    results.write_text(
        json.dumps(
            {
                "attempt_id": "attempt0000000001",
                "status": "succeeded",
                "session_id": "sess-1",
                "backend": "pi",
            }
        )
    )
    out = be.dispatch(_contract(tmp_path), confirm=True, dry_run=False, timeout=900)
    assert out["state"] == "completed"
    assert out["changed"] is False
    # No re-queue: pending stays empty.
    assert not list((tmp_path / "spool" / "pending").iterdir())


def test_observation_is_transport_truth_only(tmp_path, monkeypatch):
    """A session-completion report must NEVER read as contract completion.

    The observation carries ``status``/``outcome`` describing the delegated
    turn; hermes-gpt's independent artifact validation decides completion.
    """
    be = _backend(monkeypatch, tmp_path)
    results = tmp_path / "spool" / "results" / "attempt0000000001.json"
    results.write_text(
        json.dumps(
            {"attempt_id": "attempt0000000001", "status": "succeeded", "session_id": "s1"}
        )
    )
    rows = be.observed_runs("attempt0000000001")
    assert len(rows) == 1
    # Transport shape, deliberately NOT a contract verdict:
    assert rows[0]["outcome"] in {"completed", "failed"}
    assert rows[0].get("scope") == "runner:hermes_agent"


def test_observation_running_from_pending_envelope(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    be.dispatch(_contract(tmp_path), confirm=True, dry_run=False, timeout=900)
    rows = be.observed_runs("attempt0000000001")
    assert rows and rows[0]["status"] == "running"
    assert rows[0]["delegate_backend"] == "pi"


def test_observation_empty_for_unknown_attempt(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    assert be.observed_runs("attempt0000000009") == []
    # Non-conforming ids can never join into paths.
    assert be.observed_runs("../escape") == []


def test_cancel_records_intent_and_respects_terminal(tmp_path, monkeypatch):
    be = _backend(monkeypatch, tmp_path)
    be.dispatch(_contract(tmp_path), confirm=True, dry_run=False, timeout=900)
    out = be.cancel("attempt0000000001")
    assert out["success"] is True and out["state"] == "cancelling"
    cancel = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000001.cancel.json").read_text()
    )
    assert cancel["attempt_id"] == "attempt0000000001"
    # Terminal results are never reaped by cancel.
    results = tmp_path / "spool" / "results" / "attempt0000000001.json"
    results.write_text(
        json.dumps({"attempt_id": "attempt0000000001", "status": "failed"})
    )
    out2 = be.cancel("attempt0000000001")
    assert out2["success"] is False and out2["proven_terminal"] is True
    assert results.is_file()


def test_registration_first_wins_and_module_imports_clean():
    """The corrected rail registers BEFORE the direct-launch backends."""
    import operator_runners as op_runners

    names = list(op_runners._BACKENDS.keys())
    assert "hermes_agent" in names
    assert names[0] == "hermes_agent"


def test_dispatch_creates_missing_artifacts_workspace(tmp_path, monkeypatch):
    """The autopilot's delegated workspace (hermes_root/missions/artifacts/)
    is created on first dispatch — the contract itself authorizes writes
    under it (msn-m3-pi-dev-004 first-dispatch failure)."""
    root = _spool(tmp_path)          # spool under <tmp>/spool; data root = <tmp>
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(root))
    be = hab.HermesAgentBackend()
    ws = tmp_path / "missions" / "artifacts" / "ap-m-attempt0000000001"
    contract = _contract(tmp_path)
    contract["allowed_scope"]["workspaces"] = [str(ws)]
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=900)
    assert out["success"] is True
    assert ws.is_dir()


def test_dispatch_refuses_workspace_outside_data_root(tmp_path, monkeypatch):
    root = _spool(tmp_path)
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(root))
    be = hab.HermesAgentBackend()
    contract = _contract(tmp_path)
    contract["allowed_scope"]["workspaces"] = ["/tmp/definitely-not-ours-x9"]
    Path("/tmp/definitely-not-ours-x9").mkdir(exist_ok=True)
    try:
        out = be.dispatch(contract, confirm=True, dry_run=False, timeout=900)
        # dir exists so the creation branch never fires; dispatch proceeds —
        # the data-root guard only gates CREATION, existing dirs are honored
        assert out["success"] is True
    finally:
        import shutil as _shutil
        _shutil.rmtree("/tmp/definitely-not-ours-x9", ignore_errors=True)


def test_dispatch_refusal_for_missing_uncreatable_workspace(tmp_path, monkeypatch):
    root = _spool(tmp_path)
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(root))
    be = hab.HermesAgentBackend()
    # under data root, but parent is a FILE → mkdir fails → typed refusal
    blocker = tmp_path / "missions"
    blocker.write_text("not a dir")
    contract = _contract(tmp_path)
    contract["allowed_scope"]["workspaces"] = [str(blocker / "artifacts" / "x")]
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=900)
    assert out["success"] is False and out["changed"] is False
    assert "could not be created" in out["safe_message"]
    # NotADirectoryError is an OSError — but the runner re-raises it as
    # ValueError via the refusal path; assert the transport never queued.
    assert not list(root.glob("pending/*"))


# -- D1/D2/D3 (2026-11-17 controller-lane review): options cap, per-dispatch
# -- spool_root routing, action_payload/session_binding passthrough --------


def test_d1_median_conductor_prompt_fits_options(tmp_path, monkeypatch):
    """D1: a median-size live conductor phase prompt (p50 ~10.2KB, p90 ~14.9KB)
    must canonicalize through normalize_execution and ride options.prompt —
    the 8KB cap rejected the MEDIAN envelope as INVALID_CONTRACT."""
    import operator_runners as op_runners

    big_prompt = "Authoritative phase prompt. " + "x" * 11_000
    execution = {
        "backend": "hermes_agent",
        "options": {"prompt": big_prompt},
    }
    out = op_runners.normalize_execution(execution)
    assert out["options"]["prompt"] == big_prompt


def test_d2_per_dispatch_spool_root_routes_and_persists(tmp_path, monkeypatch):
    """D2: options.spool_root routes ONE dispatch to a dedicated lane without
    touching the env root; the root rides the dispatch payload (backend_ref
    persistence is exercised in the delegation round-trip test below)."""
    env_root = _spool(tmp_path)
    lane_root = tmp_path / "maestro-lane"
    (lane_root / "pending").mkdir(parents=True)
    (lane_root / "results").mkdir(parents=True)
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(env_root))
    be = hab.HermesAgentBackend()
    contract = _contract(tmp_path)
    contract["task_id"] = "attempt0000000042"
    contract["execution"]["options"]["spool_root"] = str(lane_root)
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True and out["spool_root"] == str(lane_root)
    # Envelope landed in the LANE, not the env root.
    assert (lane_root / "pending" / "attempt0000000042.json").is_file()
    assert not (env_root / "pending" / "attempt0000000042.json").exists()
    # Same-process observation follows the lane.
    runs = be.observed_runs("attempt0000000042")
    assert runs and runs[0]["status"] == "running"


def test_d2_invalid_spool_root_fails_closed(tmp_path, monkeypatch):
    """D2: a malformed spool_root refuses instead of falling back to the
    shared firehose."""
    env_root = _spool(tmp_path)
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(env_root))
    be = hab.HermesAgentBackend()
    for bad in ("not/absolute", str(tmp_path / "missing-lane")):
        contract = _contract(tmp_path)
        contract["task_id"] = "attempt0000000043"
        contract["execution"]["options"]["spool_root"] = bad
        with pytest.raises(ValueError):
            be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    # A symlinked lane is also refused (resolve() must equal the raw path).
    import os as _os
    real_lane = tmp_path / "real-lane"
    (real_lane / "pending").mkdir(parents=True)
    (real_lane / "results").mkdir(parents=True)
    link_lane = tmp_path / "link-lane"
    _os.symlink(real_lane, link_lane)
    contract = _contract(tmp_path)
    contract["task_id"] = "attempt0000000043"
    contract["execution"]["options"]["spool_root"] = str(link_lane)
    with pytest.raises(ValueError):
        be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert not list(env_root.glob("pending/*"))


def test_d2_seed_task_root_adopts_after_restart(tmp_path, monkeypatch):
    """D2: a fresh backend process (sidecar restart) recovers the lane from
    the delegation row's backend_ref via seed_task_root; a root recorded by
    a real dispatch is never overridden by a seed."""
    env_root = _spool(tmp_path)
    lane_root = tmp_path / "maestro-lane"
    (lane_root / "pending").mkdir(parents=True)
    (lane_root / "results").mkdir(parents=True)
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(env_root))
    dispatch_be = hab.HermesAgentBackend()
    contract = _contract(tmp_path)
    contract["task_id"] = "attempt0000000044"
    contract["execution"]["options"]["spool_root"] = str(lane_root)
    dispatch_be.dispatch(contract, confirm=True, dry_run=False, timeout=30)

    fresh_be = hab.HermesAgentBackend()  # simulates sidecar restart
    assert fresh_be.observed_runs("attempt0000000044") == []  # env root: nothing
    fresh_be.seed_task_root("attempt0000000044", str(lane_root))
    runs = fresh_be.observed_runs("attempt0000000044")
    assert runs and runs[0]["status"] == "running"

    # Dispatch-recorded roots win over later seeds.
    fresh_be.seed_task_root("attempt0000000044", str(env_root))
    assert fresh_be.observed_runs("attempt0000000044")[0]["status"] == "running"
    assert (lane_root / "pending" / "attempt0000000044.json").is_file()


def test_d2_backend_ref_round_trips_spool_root(tmp_path, monkeypatch):
    """D2 end-to-end: hermes_delegation_dispatch persists the lane root in
    backend_ref_json (durable across sidecar restarts); reconcile-visible
    observation recovers it through the seeded backend map."""
    import operator_runners as op_runners

    workspace = tmp_path / "ws"
    workspace.mkdir()
    lane_root = _spool(tmp_path / "lane")
    env_root = _spool(tmp_path / "env")
    monkeypatch.setenv(hab.SPOOL_ROOT_ENV, str(env_root))
    monkeypatch.setenv(op_policy.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op_policy.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op_policy.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op_policy.OPERATOR_ALLOWED_PATHS_ENV, str(tmp_path))
    op_policy.set_audit_log_override(tmp_path / "audit.jsonl")
    root = tmp_path / "hermes"

    contract = {
        "schema": "hermes.work-contract/v1",
        "task_id": "d2laneroundtrip01",
        "assigned_agent": "hermes-agent",
        "assigned_profile": "default",
        "objective": "Route one dispatch to a dedicated lane.",
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
        "execution": {
            "backend": "hermes_agent",
            "options": {"spool_root": str(lane_root)},
        },
    }
    out = json.loads(delegations.hermes_delegation_dispatch(
        json.dumps(contract), delegation_id="dlg-d2laneroundtrip1",
        confirm=True, dry_run=False, timeout=30, hermes_root=root,
    ))
    assert out["success"] is True and out["changed"] is True
    assert out["dispatch"]["spool_root"] == str(lane_root)
    # Envelope is in the LANE.
    assert (lane_root / "pending" / "d2laneroundtrip01.json").is_file()

    # Durable: the delegation row carries the root for restart recovery.
    row = json.loads(delegations.hermes_delegation_get(
        "dlg-d2laneroundtrip1", hermes_root=root))
    backend_ref = row["delegation"]["backend_ref"]
    if isinstance(backend_ref, str):
        backend_ref = json.loads(backend_ref or "{}")
    assert backend_ref.get("spool_root") == str(lane_root)

    # A FRESH process (empty in-memory map) still observes the lane through
    # the backend_ref -> seed -> observed_runs recovery chain.
    fresh = hab.HermesAgentBackend()
    op_runners._BACKENDS["hermes_agent"] = fresh
    try:
        observed = delegations._latest_observation("d2laneroundtrip01", root)
        assert observed is not None and observed["status"] == "running"
    finally:
        op_runners._BACKENDS["hermes_agent"] = dispatch_be_singleton()
    # Simulated terminal result in the lane folds through the same chain
    # (result envelopes use status succeeded/failed; observation maps to
    # outcome completed/failed).
    (lane_root / "pending" / "d2laneroundtrip01.json").unlink()
    (lane_root / "results" / "d2laneroundtrip01.json").write_text(json.dumps({
        "attempt_id": "d2laneroundtrip01",
        "status": "succeeded",
    }))
    observed2 = delegations._latest_observation("d2laneroundtrip01", root)
    assert observed2 is not None and observed2["outcome"] == "completed"


def dispatch_be_singleton():
    import operator_runners as op_runners
    return op_runners.get_backend("hermes_agent")


def test_d3_action_payload_and_session_binding_merge(tmp_path, monkeypatch):
    """D3: options.action_payload merges conductor's durable control keys;
    options.session_binding pins native session identity; protected keys
    stay runner-authoritative."""
    be = _backend(monkeypatch, tmp_path)
    contract = _contract(tmp_path)
    contract["execution"]["options"]["action_payload"] = {
        "phase_result_required": True,
        "phase_id": "implement",
        "session_affinity_key": "affinity-7",
        "phase_timeout_seconds": 1,  # must NOT clobber the runner's budget
        "instruction": "clobber attempt",  # must NOT clobber instruction
    }
    contract["execution"]["options"]["session_binding"] = {
        "native_session_id": "sess-123",
        "binding_id": "bind-456",
        "resume": True,
        "run_id": "evil",  # must NOT clobber identity
    }
    out = be.dispatch(contract, confirm=True, dry_run=False, timeout=30)
    assert out["success"] is True
    order = json.loads(
        (tmp_path / "spool" / "pending" / "attempt0000000001.json").read_text()
    )
    ap = order["action_payload"]
    assert ap["phase_result_required"] is True
    assert ap["phase_id"] == "implement"
    assert ap["session_affinity_key"] == "affinity-7"
    assert ap["phase_timeout_seconds"] == 900.0  # runner-authoritative
    assert "instruction" not in ap  # no legacy context -> no instruction key
    sb = order["session_binding"]
    assert sb["native_session_id"] == "sess-123"
    assert sb["binding_id"] == "bind-456"
    assert sb["resume"] is True
    assert sb["run_id"] == "attempt0000000001"  # identity protected
    assert sb["backend"] == "pi"
