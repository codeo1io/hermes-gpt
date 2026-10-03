"""Behavior-only coverage for ui_api.py route composition (rm-189).

``ui_api`` owns the UI route registry, the JSON envelope re-exports, and
static serving of the built SPA. It had no direct suite: ``server.py``
composes it into the full app, and ``test_ui_static_assets`` exercises the
BUILT dist through the full server only. This suite pins the composition
contract directly:

- the /ui route + mount are registered in BOTH built and not-built states
  (stable URL contract, ``_static_routes`` docstring);
- the not-built placeholder behavior (``_ui_not_built`` / ``_ui_not_built_app``);
- the SPA fallback (``_SPAStaticFiles``) at composition level;
- sibling degradation (a missing/broken feature module degrades to [], the
  registry never crashes — parallel-worktree contract);
- the envelope re-exports point at the redaction boundary in ``ui_security``;
- the /ui mount sits behind the outer bearer auth when one is configured
  (server-level, mirroring how MCP is gated).

No semantic changes are encoded here — this pins current behavior only.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

import ui_api
import ui_security

# Static bearer tokens must satisfy the OAuth client-secret shape
# (43-128 URL-safe characters); a short fixture token raises instead of gating.
TOKEN = "ui-mount-test-token-0123456789abcdef0123456789abcdef"


@pytest.fixture()
def ui_env(tmp_path, monkeypatch):
    """Redirect ui_dir() at a scratch directory; returns (dist_dir, env_dict)."""
    dist = tmp_path / "web" / "dist"
    monkeypatch.setenv("HERMES_GPT_UI_DIR", str(dist))
    return dist


def _client_for_routes(routes):
    app = Starlette(routes=routes)
    return TestClient(app)


def _ui_route_shapes(routes):
    routes_at_ui = [r for r in routes if getattr(r, "path", None) == "/ui"]
    mounts = [r for r in routes_at_ui if isinstance(r, Mount)]
    exacts = [r for r in routes_at_ui if isinstance(r, Route)]
    return exacts, mounts


# ---------------------------------------------------------------------------
# Composition registry
# ---------------------------------------------------------------------------


def test_routes_registered_and_static_contract_present(ui_env):
    routes = ui_api.routes()
    exacts, mounts = _ui_route_shapes(routes)
    assert exacts, "bare /ui Route must always be registered"
    assert len(mounts) == 1 and mounts[0].name == "ui-static"
    assert ui_api.ui_routes() == routes  # compatibility alias


def test_broken_sibling_degrades_registry_not_crash(monkeypatch):
    fake = types.ModuleType("ui_fabric")
    fake.ui_fabric_routes = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    monkeypatch.setitem(sys.modules, "ui_fabric", fake)
    routes = ui_api.routes()
    # Registry still returns the static contract instead of crashing.
    exacts, mounts = _ui_route_shapes(routes)
    assert exacts and mounts


def test_sibling_routes_missing_or_factoryless():
    assert ui_api._sibling_routes("ui_definitely_not_a_module") == []
    empty = types.ModuleType("ui_empty_sibling")
    try:
        sys.modules["ui_empty_sibling"] = empty
        assert ui_api._sibling_routes("ui_empty_sibling") == []  # no factory attr
        empty.ui_empty_sibling_routes = "not-callable"
        assert ui_api._sibling_routes("ui_empty_sibling") == []
    finally:
        del sys.modules["ui_empty_sibling"]


def test_envelope_reexports_point_at_redaction_boundary():
    assert ui_api.ok is ui_security.ok
    assert ui_api.err is ui_security.err
    assert ui_api.redact_browser is ui_security.redact_browser
    assert ui_api.error_envelope is ui_security.error_envelope


# ---------------------------------------------------------------------------
# Built dist: SPA serving at composition level
# ---------------------------------------------------------------------------


def _write_dist(dist: Path) -> None:
    assets = dist / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text("<html>spa-shell</html>", encoding="utf-8")
    (assets / "index-ABC123.js").write_text("console.log('x')", encoding="utf-8")


def test_built_dist_serves_index_assets_and_spa_fallback(ui_env):
    _write_dist(ui_env)
    client = _client_for_routes(ui_api.routes())
    assert client.get("/ui").text == "<html>spa-shell</html>"
    assert client.get("/ui/assets/index-ABC123.js").status_code == 200
    # SPA fallback: a client-side route path resolves to index.html.
    assert client.get("/ui/sessions/abc").text == "<html>spa-shell</html>"


def test_not_built_placeholder_json_and_plain(ui_env):
    # dist stays absent -> composition must still register /ui and answer
    # deterministic placeholders instead of omitting the route.
    client = _client_for_routes(ui_api.routes())
    resp = client.get("/ui")
    assert resp.status_code == 404
    assert resp.json() == {"ok": False, "err": "UI static assets not built"}
    sub = client.get("/ui/anything/deep")
    assert sub.status_code == 404
    assert sub.text == "UI static assets not built"


def test_not_built_placeholder_objects_shape():
    import starlette.responses

    scope = {"type": "http", "method": "GET", "path": "/ui/x", "headers": []}
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    import asyncio

    asyncio.run(ui_api._ui_not_built_app(scope, receive, send))
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    assert body == b"UI static assets not built"
    assert ui_api._ui_not_built(None).status_code == 404
    assert isinstance(ui_api._ui_not_built(None), starlette.responses.JSONResponse)


# ---------------------------------------------------------------------------
# Auth gating of the /ui mount (server level)
# ---------------------------------------------------------------------------


def _server_client(monkeypatch, tmp_path, **env):
    """Hermetic full-app client (mirrors test_ui_static_assets' fixture)."""
    import oauth_auth
    import operator_mission as op_mission
    import operator_policy as op
    import server

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.delenv(oauth_auth.OAUTH_ENABLE_ENV, raising=False)
    if oauth_auth.AUTH_TOKEN_ENV not in env:
        monkeypatch.delenv(oauth_auth.AUTH_TOKEN_ENV, raising=False)
    op.set_audit_log_override(tmp_path / "audit.jsonl")
    op_mission._cache_clear()
    root = tmp_path / ".hermes"
    root.mkdir(parents=True, exist_ok=True)
    (root / "config.yaml").write_text(
        "model: test-model\nprovider: test-provider\n", encoding="utf-8"
    )
    monkeypatch.setenv(ui_security.UI_ENABLED_ENV, "1")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    built = server.build_server(http=True)
    app = server.build_asgi_app(built, http=True)
    return TestClient(app, base_url="http://127.0.0.1")


def test_ui_mount_requires_bearer_when_configured(ui_env, monkeypatch, tmp_path):
    import oauth_auth

    client = _server_client(monkeypatch, tmp_path, **{oauth_auth.AUTH_TOKEN_ENV: TOKEN})
    denied = client.get("/ui")
    assert denied.status_code == 401
    assert denied.json() == {"error": "unauthorized"}
    assert denied.headers["www-authenticate"].startswith("Bearer")
    allowed = client.get("/ui", headers={"Authorization": f"Bearer {TOKEN}"})
    assert allowed.status_code == 404  # auth passed; not-built placeholder beyond
    assert allowed.json() == {"ok": False, "err": "UI static assets not built"}
    # The bare root stays public (PUBLIC_PATHS), so the gate is /ui-specific.
    assert client.get("/").status_code != 401


def test_ui_mount_open_without_configured_auth(ui_env, monkeypatch, tmp_path):
    client = _server_client(monkeypatch, tmp_path)
    assert client.get("/ui").status_code == 404  # not-built placeholder, no 401
