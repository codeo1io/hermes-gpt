from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

import operator_live_events as live_events
import operator_mission_runtime as missions
import operator_policy as op
import ui_api
import ui_missions


def _spec(mission_id: str = "msn-ui-test") -> str:
    return json.dumps(
        {
            "schema": missions.MISSION_SPEC_SCHEMA,
            "mission_id": mission_id,
            "title": "Flight Deck mission",
            "objective": "Observe mission progress without adding browser authority.",
            "owner_profile": "default",
            "acceptance_criteria": ["mission state visible", "delegations visible"],
            "context_refs": [
                {
                    "kind": "document",
                    "ref": "docs:v0.9-plan",
                    "label": "v0.9 plan",
                    "sha256": "a" * 64,
                }
            ],
            "skills": [
                {
                    "name": "compound-engineering",
                    "version": "1",
                    "ref": "skill:compound-engineering",
                }
            ],
            "final_approval_required": True,
        }
    )


@pytest.fixture
def mission_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "hermes"
    root.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PATHS_ENV, str(workspace))
    op.set_audit_log_override(tmp_path / "audit.jsonl")
    created = json.loads(
        missions.hermes_mission_create(
            _spec(),
            confirm=True,
            dry_run=False,
            hermes_root=root,
        )
    )
    assert created["success"] is True
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "read_only")
    return root


def _client() -> TestClient:
    return TestClient(Starlette(routes=ui_missions.ui_missions_routes()))


def test_mission_routes_are_get_only_and_composed(mission_root: Path):
    routes = ui_missions.ui_missions_routes()
    assert routes
    assert all(route.methods == {"GET", "HEAD"} for route in routes)
    composed_paths = {getattr(route, "path", "") for route in ui_api.routes()}
    assert "/api/ops/missions" in composed_paths
    assert "/api/ops/missions/{mission_id}" in composed_paths
    assert "/api/ops/missions/{mission_id}/events" in composed_paths


def test_composed_ui_routes_do_not_shadow_mission_list(mission_root: Path):
    client = TestClient(Starlette(routes=ui_api.routes()))
    response = client.get("/api/ops/missions?limit=20")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["missions"][0]["mission_id"] == "msn-ui-test"


def test_mission_list_and_detail_surface_bounded_runtime_state(
    mission_root: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        ui_missions.delegations,
        "hermes_delegation_list",
        lambda **kwargs: json.dumps(
            {
                "success": True,
                "delegations": [
                    {
                        "delegation_id": "dlg-ui-test",
                        "mission_id": "msn-ui-test",
                        "task_id": "task-ui-test",
                        "backend": "opencode",
                        "state": "running",
                    }
                ],
                "count": 1,
            }
        ),
    )
    client = _client()
    listed = client.get("/api/ops/missions?limit=20")
    assert listed.status_code == 200
    list_body = listed.json()
    assert list_body["ok"] is True
    assert list_body["data"]["count"] == 1
    assert list_body["data"]["missions"][0]["mission_id"] == "msn-ui-test"
    assert list_body["data"]["read_only"] is True

    detail = client.get("/api/ops/missions/msn-ui-test")
    assert detail.status_code == 200
    body = detail.json()
    assert body["ok"] is True
    assert body["data"]["mission"]["mission_id"] == "msn-ui-test"
    assert body["data"]["mission"]["context_refs"][0]["sha256"] == "a" * 64
    assert body["data"]["mission"]["skills"][0]["name"] == "compound-engineering"
    assert body["data"]["delegations"][0]["backend"] == "opencode"
    assert body["data"]["delegation_count"] == 1
    assert body["data"]["read_only"] is True


def test_mission_events_deliver_cursor_filtered_wakeup(mission_root: Path):
    published = live_events.publish_event(
        topic="mission",
        kind="mission.test",
        subject_type="mission",
        subject_id="msn-ui-test",
        mission_id="msn-ui-test",
        source="test-ui-missions",
        payload={"state": "running"},
        hermes_root=mission_root,
    )
    assert published["mission_id"] == "msn-ui-test"
    client = _client()
    response = client.get("/api/ops/missions/msn-ui-test/events?cursor=0&limit=10")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["count"] >= 1
    assert any(event["mission_id"] == "msn-ui-test" for event in body["events"])
    assert body["next_cursor"] >= 1
    assert body["read_only"] is True


def test_delegation_detail_uses_existing_read_surface(
    mission_root: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        ui_missions.delegations,
        "hermes_delegation_get",
        lambda delegation_id, hermes_root=None: json.dumps(
            {
                "success": True,
                "delegation": {
                    "delegation_id": delegation_id,
                    "task_id": "task-ui-test",
                    "backend": "pi_rpc",
                    "state": "succeeded",
                },
            }
        ),
    )
    response = _client().get("/api/ops/delegations/dlg-ui-test")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["delegation"]["state"] == "succeeded"
    assert body["read_only"] is True


def test_missing_mission_returns_not_found(mission_root: Path):
    response = _client().get("/api/ops/missions/msn-missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MISSION_NOT_FOUND"


# ── rm-096: long-poll waits must not occupy shared threadpool tokens ─────────


def test_mission_events_short_wait_completes_promptly(mission_root: Path):
    """A short wait_ms long-poll still completes with the bounded-wait
    semantics (empty result after the wait window, cursor unchanged)."""
    import time

    client = _client()
    cursor = live_events.high_watermark(mission_root)
    started = time.monotonic()
    response = client.get(
        f"/api/ops/missions/msn-ui-test/events?cursor={cursor}&wait_ms=150&limit=5"
    )
    elapsed = time.monotonic() - started
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["count"] == 0
    assert data["next_cursor"] == cursor
    assert elapsed < 5.0


def test_mission_events_survives_shared_threadpool_saturation(mission_root: Path):
    """rm-096: the mission-events long-poll draws from a dedicated limiter.

    Pre-fix, the route used starlette's ``run_in_threadpool``, which draws
    from anyio's shared default thread limiter (40 tokens). With every
    shared token held by parked holders, a mission-events request queued
    behind them and stalled; the long-poll wait must occupy its own bounded
    capacity, not the pool every other offloaded handler shares.
    """
    asyncio.run(_saturated_mission_events_request(mission_root))


async def _saturated_mission_events_request(mission_root: Path) -> None:
    import anyio.to_thread

    limiter = anyio.to_thread.current_default_thread_limiter()
    tokens = int(limiter.available_tokens)
    assert tokens >= 1, "shared thread limiter must hold at least one token"
    release = asyncio.Event()

    async def hold_one_token() -> None:
        await limiter.acquire()
        await release.wait()
        limiter.release()

    holders = [asyncio.create_task(hold_one_token()) for _ in range(tokens)]
    try:
        deadline = time.monotonic() + 5.0
        while limiter.available_tokens > 0 and time.monotonic() < deadline:
            await asyncio.sleep(0.01)
        assert limiter.available_tokens == 0, "shared limiter never saturated"

        app = Starlette(routes=ui_missions.ui_missions_routes())
        status, body = await asyncio.wait_for(
            _asgi_get(app, "/api/ops/missions/msn-ui-test/events?cursor=0&wait_ms=0&limit=5"),
            timeout=5.0,
        )
        assert status == 200
        data = body["data"]
        assert data["read_only"] is True
    finally:
        release.set()
        await asyncio.gather(*holders)


async def _asgi_get(app, path_with_query: str) -> tuple[int, dict]:
    """Invoke a GET against ``app`` without an HTTP client dependency."""
    path, _, query = path_with_query.partition("?")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query.encode(),
        "root_path": "",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    sent: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        sent.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    raw = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(raw)
