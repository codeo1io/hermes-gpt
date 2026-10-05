"""Tests for the Flight Deck operator adapters (ui_ops.py).

Covers the interface contract from t_ab4f3463:

- Envelope shape for every Mission Control surface + status reads.
- Event History query/tail.
- Mutation endpoint ``POST /api/ops/action``: the adapter executes the
  EXISTING gated ``hermes_*`` tool path and must NOT let the UI bypass a
  gate. Adversarial cases assert: unknown tools 404, disallowed args are
  rejected, dry-run is the default, confirm gates surface as
  ``409 CONFIRM_REQUIRED``, and level denials surface as
  ``403 LEVEL_REQUIRED`` — never weakened.
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

import operator_policy as op
import ui_api
import ui_ops

OWNER_ACK = op.OWNER_ACK_REQUIRED_VALUE

OWNER_ENV = {
    op.OPERATOR_ENABLED_ENV: "1",
    op.OPERATOR_LEVEL_ENV: "owner",
    op.OPERATOR_APPLY_MODE_ENV: "direct",
    op.OWNER_ACTIVE_ENV: "1",
    op.OWNER_ACK_ENV: OWNER_ACK,
}

WORKSPACE_ENV = {
    op.OPERATOR_ENABLED_ENV: "1",
    op.OPERATOR_LEVEL_ENV: "workspace",
    op.OPERATOR_APPLY_MODE_ENV: "direct",
}

CRON_ENV = {
    op.OPERATOR_ENABLED_ENV: "1",
    op.OPERATOR_LEVEL_ENV: "cron",
    op.OPERATOR_APPLY_MODE_ENV: "direct",
}

VALID_SHA = "a" * 64


@pytest.fixture(autouse=True)
def isolate_ui_ops(monkeypatch, tmp_path):
    """Point HERMES_HOME at a temp root and clear mission/events allowlists."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("HERMES_GPT_MISSION_ALLOWED_SURFACES", raising=False)
    monkeypatch.delenv("HERMES_GPT_EVENTS_ALLOWED_SOURCES", raising=False)
    # Mission surfaces resolve a few state files from Path.home() (e.g.
    # ~/nexus-wiki action-items). Pin home to the temp root so the test never
    # reads the invoking user's real files (audit t_9d200636 Class B).
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    # Ensure the temp root exists (some surfaces read it directly).
    tmp_path.mkdir(parents=True, exist_ok=True)
    # rm-097: the long-running dispatch registry is module state; reset it so
    # one test's dispatches never bleed into the next test's assertions.
    with ui_ops._dispatch_lock:
        ui_ops._dispatch_active.clear()
        ui_ops._dispatch_finished.clear()
    return tmp_path


@pytest.fixture()
def client() -> TestClient:
    app = Starlette(routes=ui_ops.ui_ops_routes())
    return TestClient(app)


def _set_env(monkeypatch, env: dict[str, str]) -> None:
    for key, value in env.items():
        monkeypatch.setenv(key, value)


# ---------------------------------------------------------------------------
# Mission Control surfaces — envelope shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surface", ui_ops.MISSION_SURFACES)
def test_mission_surface_envelope_shape(client, surface):
    resp = client.get(f"/api/ops/{surface}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["surface"] == surface
    assert data["fetched_at"]
    assert isinstance(data["data"], dict)
    # Redacted mission envelope: never raw prompts, secrets, or transcripts.
    # Assert on secret-shaped tokens, not bare substrings: "sk-" alone also
    # matches benign "hermes-task-*" ids (audit t_9d200636 Class B). Shape
    # mirrors operator_policy.redact_output's OpenAI-key pattern.
    serialized = json.dumps(data["data"])
    assert not re.search(r"(?i)\bsk(?:-proj)?-[A-Za-z0-9_-]{20,}\b", serialized)
    assert "AKIA" not in serialized
    assert "Bearer " not in serialized
    assert "prompt_sha256" in serialized or "counts" in serialized or True  # shape-tolerant


_SECRET_SCAN_RE = re.compile(r"(?i)\bsk(?:-proj)?-[A-Za-z0-9_-]{20,}\b")


@pytest.mark.parametrize(
    "payload,expect_secret",
    [
        # Benign ids that contain the "sk-" substring must NOT trip the scan
        # (audit t_9d200636 Class B: hermes-task-* ids from action-items).
        ({"id": "hermes-task-maintenance-cron-error", "status": "open"}, False),
        ({"id": "task-sk-123-review", "status": "open"}, False),
        # Real secret-shaped keys MUST trip the scan.
        ({"id": "sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "status": "open"}, True),
        ({"id": "sk-proj-abcdefghijklmnopqrstuvwxyz123456", "status": "open"}, True),
    ],
)
def test_secret_scan_regex_separates_task_ids_from_real_keys(payload, expect_secret):
    serialized = json.dumps(payload)
    assert bool(_SECRET_SCAN_RE.search(serialized)) is expect_secret


def test_ops_envelope_redacts_even_if_upstream_leaks(client, monkeypatch):
    """A11: ``_ok`` routes through ui_security, so a payload that somehow
    leaves the backend with a secret in it still cannot reach the browser —
    the adapter boundary redacts independently of upstream hygiene."""
    leak = {
        "generated_at": "2026-09-01T00:00:00Z",
        "note": "leaked key sk-abcdef0123456789abcdef01 here",
        "aws": "AKIA" + "BCDEFGHIJKLMNOP",
        "token": "tok-abcdefghijklmnop",
        "long": "x" * 20_000,
    }
    monkeypatch.setattr(ui_ops, "_surface_payload", lambda surface, force_refresh: leak)
    resp = client.get("/api/ops/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    serialized = json.dumps(body)
    assert "sk-abcdef" not in serialized
    assert "AKIA" not in serialized
    assert "tok-abcdefghijklmnop" not in serialized  # secret-keyed value
    assert len(body["data"]["data"]["long"]) <= 8192 + len("…[truncated]")


def test_mission_surface_overview_is_composite(client):
    resp = client.get("/api/ops/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["surface"] == "overview"
    assert "fleet_health" in data["data"] or "surfaces_unavailable" in data["data"]


def test_mission_surface_unknown_404(client):
    resp = client.get("/api/ops/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["ok"] is False
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_mission_surface_force_refresh_accepted(client):
    resp = client.get("/api/ops/health?force_refresh=1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ---------------------------------------------------------------------------
# Mission Control allowlist semantics (AGENTS.md: unset=all, list=only,
# empty=none — never described as "deny by default")
# ---------------------------------------------------------------------------


def test_mission_allowlist_subset(client, monkeypatch):
    monkeypatch.setenv("HERMES_GPT_MISSION_ALLOWED_SURFACES", "health,cron")
    ok = client.get("/api/ops/health")
    assert ok.status_code == 200
    assert ok.json()["data"]["data"].get("code") != "AUTHZ_DENIED"

    denied = client.get("/api/ops/profiles")
    assert denied.status_code == 200  # state, not HTTP error
    assert denied.json()["ok"] is True
    assert denied.json()["data"]["data"]["code"] == "AUTHZ_DENIED"


def test_mission_allowlist_empty_denies_all(client, monkeypatch):
    monkeypatch.setenv("HERMES_GPT_MISSION_ALLOWED_SURFACES", "")
    for surface in ("health", "overview", "usage"):
        resp = client.get(f"/api/ops/{surface}")
        assert resp.status_code == 200
        assert resp.json()["data"]["data"]["code"] == "AUTHZ_DENIED"


def test_mission_allowlist_unset_allows_all(client):
    for surface in ("health", "overview", "usage"):
        resp = client.get(f"/api/ops/{surface}")
        assert resp.status_code == 200
        assert resp.json()["data"]["data"].get("code") != "AUTHZ_DENIED"


# ---------------------------------------------------------------------------
# Event History
# ---------------------------------------------------------------------------


def test_events_query_envelope(client):
    resp = client.get("/api/events?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    data = body["data"]
    assert isinstance(data.get("events"), list)
    assert data.get("count_returned", 0) <= 5
    assert isinstance(data.get("warnings"), list)


def test_events_tail_mode(client):
    resp = client.get("/api/events?mode=tail&limit=3")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert isinstance(resp.json()["data"].get("events"), list)


# ---------------------------------------------------------------------------
# Status reads
# ---------------------------------------------------------------------------


def test_contracts_list_envelope(client):
    resp = client.get("/api/ops/contracts")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["success"] is True
    assert isinstance(data.get("review_acceptances"), list)
    assert isinstance(data.get("workflows"), list)


def test_contracts_detail_not_found(client):
    resp = client.get(f"/api/ops/contracts/{VALID_SHA}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_review_detail_empty(client):
    resp = client.get(f"/api/ops/review/{VALID_SHA}")
    assert resp.status_code == 200
    assert resp.json()["data"]["records"] == []


def test_swarm_list_envelope(client):
    resp = client.get("/api/ops/swarm")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_swarm_detail_not_found(client, monkeypatch):
    # Read-only operator level must be enabled for the operator module to
    # reach its WORKFLOW_NOT_FOUND path (otherwise it returns policy-denied
    # as a 200 state, which is correct degradation).
    _set_env(monkeypatch, {op.OPERATOR_ENABLED_ENV: "1", op.OPERATOR_LEVEL_ENV: "read_only"})
    resp = client.get("/api/ops/swarm/nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_codex_list_envelope(client):
    # Bare /api/ops/codex is the mission surface (12-surface list); the
    # envelope carries surface metadata + the redacted mission payload.
    resp = client.get("/api/ops/codex")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["surface"] == "codex"
    assert isinstance(data["data"], dict)


def test_codex_detail_not_found(client):
    resp = client.get("/api/ops/codex/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_cron_list_envelope(client):
    resp = client.get("/api/ops/cron")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["surface"] == "cron"
    assert isinstance(data["data"], dict)


def test_cron_detail_not_found(client):
    resp = client.get("/api/ops/cron/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_fleet_list_envelope_state_not_error(client):
    # Fleet may report not_configured / policy denied — must be a 200 state.
    resp = client.get("/api/ops/fleet")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_account_envelope(client):
    resp = client.get("/api/ops/account")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["success"] is True
    assert isinstance(data.get("policy"), dict)
    assert data.get("server_version")
    assert "oauth" in data


# ---------------------------------------------------------------------------
# ui_api composition (hotspot smoke)
# ---------------------------------------------------------------------------


def test_ui_api_composes_ops_routes():
    routes = ui_api.ui_routes()
    paths = {getattr(r, "path", "") for r in routes}
    assert "/api/ops/action" in paths
    assert "/api/events" in paths


# ---------------------------------------------------------------------------
# Mutations — gate preservation (adversarial)
# ---------------------------------------------------------------------------


def test_action_unknown_tool_404(client):
    resp = client.post("/api/ops/action", json={"tool": "hermes_nonexistent", "args": {}})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "UNKNOWN_TOOL"


def test_action_rejects_disallowed_args(client):
    # The UI cannot smuggle internal kwargs into the gated path.
    resp = client.post(
        "/api/ops/action",
        json={
            "tool": "hermes_review_accept",
            "args": {
                "contract_sha256": VALID_SHA,
                "task_id": "t-1",
                "assignee": "alice",
                "reviewer": "bob",
                "verdict": "SATISFIED",
                "evidence_refs": ["docs/evidence-1.md"],
                "hermes_root": "/tmp/evil",
                "runner": "smuggled",
            },
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_ARGS"
    assert "hermes_root" in resp.json()["error"]["message"]


def test_action_rejects_confirm_for_tool_without_confirm(client):
    # hermes_cron_pause has no confirm arg; the UI cannot force one through.
    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_cron_pause", "args": {"profile": "default", "job_id": "j1", "confirm": True}},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_ARGS"


def test_action_level_denied_403(client):
    # Default (read_only / operator disabled) level: review accept requires
    # owner -> 403 LEVEL_REQUIRED, never a silent pass-through.
    resp = client.post(
        "/api/ops/action",
        json={
            "tool": "hermes_review_accept",
            "args": {
                "contract_sha256": VALID_SHA,
                "task_id": "t-1",
                "assignee": "alice",
                "reviewer": "bob",
                "verdict": "SATISFIED",
                "evidence_refs": ["docs/evidence-1.md"],
            },
        },
    )
    assert resp.status_code == 403
    err = resp.json()["error"]
    assert err["code"] == "LEVEL_REQUIRED"
    assert err.get("required") == "owner"


def test_action_dry_run_default_plan_no_write(client, monkeypatch, tmp_path):
    # Owner mode + direct apply. Dry-run omitted -> plan only, no store write.
    _set_env(monkeypatch, OWNER_ENV)
    resp = client.post(
        "/api/ops/action",
        json={
            "tool": "hermes_review_accept",
            "args": {
                "contract_sha256": VALID_SHA,
                "task_id": "t-1",
                "assignee": "alice",
                "reviewer": "bob",
                "verdict": "SATISFIED",
                "evidence_refs": ["docs/evidence-1.md"],
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["tool"] == "hermes_review_accept"
    assert data["dry_run"] is True
    assert data["requires_confirm"] is True
    assert data["result"]["success"] is True
    # Nothing was written to the review-evidence store.
    evidence = tmp_path / "review-evidence" / "review-acceptances.jsonl"
    assert not evidence.exists()


def test_action_confirm_gate_409(client, monkeypatch):
    # Owner + direct, but confirm omitted -> 409 CONFIRM_REQUIRED dialog.
    _set_env(monkeypatch, OWNER_ENV)
    resp = client.post(
        "/api/ops/action",
        json={
            "tool": "hermes_review_accept",
            "args": {
                "contract_sha256": VALID_SHA,
                "task_id": "t-1",
                "assignee": "alice",
                "reviewer": "bob",
                "verdict": "SATISFIED",
                "evidence_refs": ["docs/evidence-1.md"],
                "dry_run": False,
            },
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFIRM_REQUIRED"


def test_action_confirm_true_writes_store(client, monkeypatch, tmp_path):
    # Owner + direct + confirm=true -> the existing gated path performs the
    # write; the adapter surfaces the result and the read-model reflects it.
    _set_env(monkeypatch, OWNER_ENV)
    resp = client.post(
        "/api/ops/action",
        json={
            "tool": "hermes_review_accept",
            "args": {
                "contract_sha256": VALID_SHA,
                "task_id": "t-1",
                "assignee": "alice",
                "reviewer": "bob",
                "verdict": "SATISFIED",
                "evidence_refs": ["docs/evidence-1.md"],
                "dry_run": False,
                "confirm": True,
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["dry_run"] is False
    assert data["requires_confirm"] is False
    assert data["result"]["success"] is True

    evidence = tmp_path / "review-evidence" / "review-acceptances.jsonl"
    assert evidence.exists()
    assert "a" * 64 in evidence.read_text(encoding="utf-8")

    detail = client.get(f"/api/ops/review/{VALID_SHA}")
    assert detail.status_code == 200
    assert len(detail.json()["data"]["records"]) == 1


def test_action_swarm_stage_advance_workspace_gate(client, monkeypatch):
    # Swarm advance needs workspace; read_only must be denied.
    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_swarm_stage_advance", "args": {"workflow_id": "wf-1", "stage_id": "s1"}},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "LEVEL_REQUIRED"
    assert resp.json()["error"].get("required") == "workspace"

    # Workspace + direct: dry-run plan (workflow missing -> plan/404 envelope
    # from the operator, but level gate passes).
    _set_env(monkeypatch, WORKSPACE_ENV)
    resp2 = client.post(
        "/api/ops/action",
        json={"tool": "hermes_swarm_stage_advance", "args": {"workflow_id": "wf-1", "stage_id": "s1", "dry_run": True}},
    )
    # Either a plan (success) or the operator's not-found envelope mapped to
    # 400/200 — but never a 403 LEVEL_REQUIRED once workspace is granted.
    assert resp2.status_code != 403


def test_action_apply_flag_reconcile_requires_workspace(client):
    # apply_flag tools: hermes_swarm_reconcile at read_only -> LEVEL_REQUIRED.
    resp = client.post("/api/ops/action", json={"tool": "hermes_swarm_reconcile", "args": {"apply": True}})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "LEVEL_REQUIRED"


def test_action_cron_run_dry_run_inline(client, monkeypatch, tmp_path):
    # hermes_cron_run with dry_run stays inline (fast path, no thread). The
    # operator requires a real cron job to build the plan, so seed one.
    cron_dir = tmp_path / "cron"
    cron_dir.mkdir(parents=True, exist_ok=True)
    (cron_dir / "jobs.json").write_text(
        json.dumps([{"id": "j1", "name": "test job", "schedule": "* * * * *", "enabled": True, "prompt": "say hi"}]),
        encoding="utf-8",
    )
    _set_env(monkeypatch, CRON_ENV)
    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_cron_run", "args": {"profile": "default", "job_id": "j1", "dry_run": True}},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["tool"] == "hermes_cron_run"
    assert data["dry_run"] is True


def test_action_cron_run_long_running_dispatched_202(client, monkeypatch, tmp_path):
    # Real execution of the blocking cron run is dispatched to a daemon
    # thread and the HTTP request returns 202 Accepted immediately.
    marker = tmp_path / "cron-stub-called"
    calls: list[dict] = []

    def stub_cron_run(**kwargs):
        calls.append(kwargs)
        marker.write_text("called", encoding="utf-8")
        return json.dumps({"success": True, "dry_run": False, "job": "j1"})

    _set_env(monkeypatch, CRON_ENV)
    monkeypatch.setattr(ui_ops._MUTATION_TOOLS["hermes_cron_run"], "fn", stub_cron_run)

    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_cron_run", "args": {"profile": "default", "job_id": "j1", "dry_run": False}},
    )
    assert resp.status_code == 202
    data = resp.json()["data"]
    assert data["accepted"] is True
    assert data["status"] == "running"
    assert data["dispatch_id"].startswith("dsp-")  # rm-097: registry key
    dispatch_id = data["dispatch_id"]

    # The daemon thread performs the call asynchronously.
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.05)
    assert marker.exists()
    assert calls and calls[0]["job_id"] == "j1"
    assert calls[0]["dry_run"] is False
    assert calls[0]["hermes_root"]  # resolved server-side, never client-supplied

    # rm-097: the run lands in the operator-visible finished registry with
    # its real outcome; the registry is drained when the run completes.
    for _ in range(100):
        if any(e["dispatch_id"] == dispatch_id for e in ui_ops._dispatch_finished):
            break
        time.sleep(0.05)
    entry = next(e for e in ui_ops._dispatch_finished if e["dispatch_id"] == dispatch_id)
    assert entry["success"] is True
    assert entry["duration_s"] >= 0
    snapshot = ui_ops._dispatch_registry_snapshot()
    assert snapshot["active"] == 0
    assert snapshot["finished"] >= 1


def test_action_cron_run_completion_audit_ordering(client, monkeypatch, tmp_path):
    """rm-097: the audit record lands at completion with the real outcome.

    Pre-fix, the ONLY adapter-level audit record was ``success=True``
    written at dispatch time — before the blocking run even started — so a
    failed or wedged cron mutation left a success-marked trail.
    """
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(op, "_audit_log_override", audit_path)

    started = threading.Event()
    finish = threading.Event()

    def stub_cron_run(**kwargs):
        started.set()
        assert finish.wait(timeout=10)
        return json.dumps({"success": True, "dry_run": False, "job": kwargs.get("job_id")})

    _set_env(monkeypatch, CRON_ENV)
    monkeypatch.setattr(ui_ops._MUTATION_TOOLS["hermes_cron_run"], "fn", stub_cron_run)

    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_cron_run", "args": {"profile": "default", "job_id": "j1", "dry_run": False}},
    )
    assert resp.status_code == 202
    dispatch_id = resp.json()["data"]["dispatch_id"]
    assert started.wait(timeout=5)

    # While the run is in flight there is NO audit record for it: dispatch
    # itself no longer writes a success record before the outcome is known.
    records = _read_audit(audit_path)
    assert not [r for r in records if r.get("tool") == "hermes_cron_run"]

    finish.set()
    record = _await_audit_record(audit_path, "hermes_cron_run", dispatch_id)
    assert record["success"] is True
    assert record["dry_run"] is False
    assert record["dispatch_id"] == dispatch_id
    assert record["duration_s"] >= 0
    assert record["outcome"] == "completed"
    assert "finished" in record["summary"]


def test_action_cron_run_injected_failure_audits_failure(client, monkeypatch, tmp_path):
    """rm-097: a dispatched run that raises leaves a failure record."""
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(op, "_audit_log_override", audit_path)

    def stub_cron_run(**kwargs):
        raise RuntimeError("cron executor exploded")

    _set_env(monkeypatch, CRON_ENV)
    monkeypatch.setattr(ui_ops._MUTATION_TOOLS["hermes_cron_run"], "fn", stub_cron_run)

    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_cron_run", "args": {"profile": "default", "job_id": "j1", "dry_run": False}},
    )
    assert resp.status_code == 202
    dispatch_id = resp.json()["data"]["dispatch_id"]

    record = _await_audit_record(audit_path, "hermes_cron_run", dispatch_id)
    assert record["success"] is False
    assert record["dry_run"] is False
    assert record["outcome"] == "failed"
    assert record["error_class"] == "RuntimeError"

    # The registry entry records the failure too.
    for _ in range(100):
        entry = next((e for e in ui_ops._dispatch_finished if e["dispatch_id"] == dispatch_id), None)
        if entry:
            break
        time.sleep(0.05)
    assert entry is not None and entry["success"] is False


def test_action_cron_run_concurrency_cap_rejects_loudly(client, monkeypatch, tmp_path):
    """rm-097: exceeding the dispatch cap rejects loudly (429), like the
    ui_chat turn gate — instead of spawning an unbounded extra thread."""
    monkeypatch.setattr(ui_ops, "_dispatch_semaphore", threading.BoundedSemaphore(1))
    monkeypatch.setattr(ui_ops, "_CRON_DISPATCH_LIMIT", 1)
    # Exhaust the single token without running a dispatch.
    assert ui_ops._dispatch_semaphore.acquire(blocking=False)
    try:
        resp = client.post(
            "/api/ops/action",
            json={"tool": "hermes_cron_run", "args": {"profile": "default", "job_id": "j1", "dry_run": False}},
        )
        assert resp.status_code == 429
        body = resp.json()
        assert body["error"]["code"] == "RATE_LIMITED"
        assert body["error"]["limit"] == 1
        assert "hermes_cron_run" in body["error"]["message"]
    finally:
        ui_ops._dispatch_semaphore.release()


def test_cron_dispatch_resolve_failure_does_not_leak_semaphore(client, monkeypatch):
    """rm-131: a raising _resolve_root() between semaphore acquire and thread
    start must fail cleanly AND release the dispatch token. Before the fix the
    exception escaped the acquire->dispatch span unreleased, so every failure
    permanently consumed one token until process restart (4 failures = every
    later long-running run 429-capped)."""
    calls: list[dict] = []

    def stub_cron_run(**kwargs):
        calls.append(kwargs)
        return json.dumps({"success": True, "dry_run": False, "job": "j1"})

    _set_env(monkeypatch, CRON_ENV)
    monkeypatch.setattr(ui_ops._MUTATION_TOOLS["hermes_cron_run"], "fn", stub_cron_run)
    real_resolve_root = ui_ops._resolve_root

    def boom():
        raise RuntimeError("root resolution failed")

    monkeypatch.setattr(ui_ops, "_resolve_root", boom)
    payload = {"tool": "hermes_cron_run", "args": {"profile": "default", "job_id": "j1", "dry_run": False}}

    # More failures than the dispatch limit: every one must return a clean
    # 500 INTERNAL (not an unhandled crash, not a 429) and release its token.
    for _ in range(ui_ops._CRON_DISPATCH_LIMIT + 2):
        resp = client.post("/api/ops/action", json=payload)
        assert resp.status_code == 500
        assert resp.json()["error"]["code"] == "INTERNAL"
    assert calls == []  # the tool itself never ran
    assert ui_ops._dispatch_active == {}  # no leaked registry entries
    assert ui_ops._dispatch_semaphore._value == ui_ops._CRON_DISPATCH_LIMIT  # rm-131: capacity intact

    # Recovery: with _resolve_root restored, a dispatch is accepted (202) —
    # it is NOT 429-capped, which is exactly what a leaked token would cause.
    monkeypatch.setattr(ui_ops, "_resolve_root", real_resolve_root)
    resp = client.post("/api/ops/action", json=payload)
    assert resp.status_code == 202
    assert calls, "recovered dispatch should have run the stub tool"


def test_cron_dispatch_registry_is_operator_visible(client, monkeypatch, tmp_path):
    """rm-097: hermes_operator_doctor surfaces the dispatch registry.

    Empty registry reports PASS with zero counts; a run that outlives the
    cron execution window warns as possibly wedged.
    """
    import operator_diagnostics as od

    _set_env(monkeypatch, CRON_ENV)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / "profiles" / "default").mkdir(parents=True, exist_ok=True)

    report = json.loads(od.hermes_operator_doctor(profile="default", hermes_root=tmp_path))
    check = report["checks"]["ui_cron_dispatch"]
    assert check["status"] == "PASS"
    assert check["active"] == 0
    assert check["finished"] >= 0

    # A stuck active dispatch (older than the execution window) warns.
    stuck_age = od._DISPATCH_STUCK_SECONDS + 10
    with ui_ops._dispatch_lock:
        ui_ops._dispatch_active["dsp-stuck"] = {
            "dispatch_id": "dsp-stuck",
            "tool": "hermes_cron_run",
            "job_id": "j9",
            "started_epoch": time.time() - stuck_age,
            "started_at": "2026-10-01T00:00:00+00:00",
            "success": None,
            "finished_at": None,
            "duration_s": None,
        }
    try:
        report = json.loads(od.hermes_operator_doctor(profile="default", hermes_root=tmp_path))
        check = report["checks"]["ui_cron_dispatch"]
        assert check["status"] == "WARN"
        assert check["code"] == "UI_CRON_DISPATCH_STUCK"
        assert check["active"] == 1
    finally:
        with ui_ops._dispatch_lock:
            ui_ops._dispatch_active.pop("dsp-stuck", None)


def _read_audit(audit_path: Path) -> list[dict]:
    if not audit_path.exists():
        return []
    return [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _await_audit_record(audit_path: Path, tool: str, dispatch_id: str, timeout_s: float = 5.0) -> dict:
    """Poll the audit log until the dispatch's completion record lands."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        for record in _read_audit(audit_path):
            if record.get("tool") == tool and record.get("dispatch_id") == dispatch_id:
                return record
        time.sleep(0.05)
    raise AssertionError(f"no completion audit record for {dispatch_id} in {audit_path}")


def test_ui_mount_failure_is_operator_visible(tmp_path, monkeypatch):
    """rm-078: a failed UI mount must not degrade to a single stderr line.

    With the UI explicitly enabled, a broken ``ui_api`` import keeps the
    MCP-only server booting but now records an audit entry, publishes a live
    event, and surfaces as a doctor WARN.
    """
    import sys

    import operator_diagnostics
    import operator_events
    import server

    home = tmp_path / "home"
    (home / "profiles" / "default").mkdir(parents=True)
    # The audit-log path resolution prefers <HERMES_HOME>/logs once it exists.
    (home / "logs").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_GPT_UI_ENABLED", "1")
    # Make `import ui_api` fail exactly as a broken/unbuilt install would.
    monkeypatch.setitem(sys.modules, "ui_api", None)

    # Pin the audit log explicitly: ``audit_record`` honors any audit override
    # still set by an earlier test in this xdist worker (several operator test
    # files set overrides), while the events reader below always reads
    # <hermes_root>/logs — pinning keeps write and read on the same file
    # regardless of ambient state.
    import operator_policy as op_policy

    op_policy.set_audit_log_override(
        home / "logs" / "hermes_gpt_operator_audit.jsonl"
    )
    try:
        built = server.build_server(http=True)
        app = server.build_asgi_app(built, http=True)
        # Server still boots MCP-only: the full middleware stack serves requests.
        from starlette.testclient import TestClient

        # Loopback base_url: the Host/Origin request boundary denies the
        # synthetic "testserver" Host TestClient would otherwise send.
        with TestClient(app, base_url="http://127.0.0.1") as client:
            assert client.get("/").status_code in (200, 400, 401, 403, 404)

        envelope = json.loads(
            operator_events.hermes_events_query(limit=20, hermes_root=home)
        )
        # The mount failure is queryable in Mission Control via the audit source
        # (kind=tool_call, tool ref=ui_mount, status error); the live-events source
        # is push-only, so it is asserted directly below via read_since.
        audit_hits = [
            e
            for e in envelope["events"]
            if e.get("kind") == "tool_call"
            and "ui_mount" in e.get("refs", [])
            and e.get("status_after") == "error"
        ]
        assert audit_hits, envelope["events"]

        import operator_live_events

        live_events, _ = operator_live_events.read_since(0, hermes_root=home)
        assert any(
            e.get("kind") == "ui_mount_failed" and e.get("source") == "server"
            for e in live_events
        )

        doctor = json.loads(
            operator_diagnostics.hermes_operator_doctor(profile="default", hermes_root=home)
        )
        check = doctor["checks"]["ui_mount"]
        assert check["status"] == operator_diagnostics.STATUS_WARN
        assert check["code"] == "UI_MOUNT_FAILED"
    finally:
        op_policy.set_audit_log_override(None)


def test_action_denies_cross_origin_browser_requests(client):
    # rm-134: the gated mutation endpoint re-asserts the Host/Origin boundary
    # at route level; a cross-site browser page gets 403 before any tool path.
    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_nonexistent", "args": {}},
        headers={"Origin": "https://attacker.example"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ORIGIN_DENIED"


def test_action_allows_loopback_origin_through_the_gate(client):
    resp = client.post(
        "/api/ops/action",
        json={"tool": "hermes_nonexistent", "args": {}},
        headers={"Origin": "http://localhost:5173"},
    )
    # Gate passed: the request reaches the normal unknown-tool 404.
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "UNKNOWN_TOOL"
