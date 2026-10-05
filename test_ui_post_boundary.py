"""rm-134: mutating-POST browser boundary (ui_security.post_boundary).

Focused tests for the Sec-Fetch-Site / Origin / Content-Type boundary wired
onto `POST /api/sessions`, `POST /api/chat`, `POST /api/chat/stop` and
`POST /api/ops/action` (ui_chat.ui_chat_routes / ui_ops.ui_ops_routes).

Allow-cases prove the request REACHED the handler by asserting the handler's
own 400 validation error (boundary failures are 403/415, never 400), so no
session state or model config is needed. Deny-cases never execute handlers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ui_chat  # noqa: E402
import ui_ops  # noqa: E402
import ui_security  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_boundary_env(monkeypatch, tmp_path):
    """Isolate boundary/oauth env so each test controls its own allow-set."""
    monkeypatch.delenv(ui_security.UI_POST_BOUNDARY_ENV, raising=False)
    monkeypatch.delenv("HERMES_GPT_OAUTH_ENABLE", raising=False)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    # Deterministic issuer for tests that do not monkeypatch it explicitly.
    monkeypatch.setattr(ui_security, "_issuer_origin", lambda: "")


@pytest.fixture()
def chat_client() -> TestClient:
    return TestClient(Starlette(routes=ui_chat.ui_chat_routes()))


@pytest.fixture()
def ops_client() -> TestClient:
    return TestClient(Starlette(routes=ui_ops.ui_ops_routes()))


JSON = {"Content-Type": "application/json"}

# ---------------------------------------------------------------------------
# Allow: requests reach the handler (handler's own 400 = proof of passage)
# ---------------------------------------------------------------------------


def test_same_origin_json_post_reaches_handler(chat_client):
    resp = chat_client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400  # BAD_REQUEST from the handler, not 403/415
    assert resp.json()["error"]["code"] == "BAD_REQUEST"


def test_chatgpt_origin_post_reaches_handler(chat_client):
    resp = chat_client.post(
        "/api/chat", json={"message": ""}, headers={"Origin": "https://chatgpt.com"}
    )
    assert resp.status_code == 400


def test_non_browser_post_without_origin_headers_reaches_handler(chat_client):
    # MCP tools / curl send neither Sec-Fetch-Site nor Origin.
    resp = chat_client.post("/api/chat/stop", json={})
    assert resp.status_code == 400  # "session_id is required" from the handler


def test_issuer_origin_post_reaches_handler(chat_client, monkeypatch):
    monkeypatch.setattr(ui_security, "_issuer_origin", lambda: "https://issuer.example")
    resp = chat_client.post(
        "/api/chat", json={"message": ""}, headers={"Origin": "https://issuer.example"}
    )
    assert resp.status_code == 400


def test_bodyless_post_without_content_type_is_not_gated(chat_client):
    # Bodyless POSTs (e.g. session create) are not content-type-gated;
    # /api/chat/stop then fails in the handler's own JSON parse (400).
    resp = chat_client.post(
        "/api/chat/stop",
        headers={"Origin": "http://testserver"},  # same-origin
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Deny: cross-site browser signals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/api/sessions", "/api/chat", "/api/chat/stop"])
def test_cross_site_origin_post_is_rejected_403(chat_client, path):
    resp = chat_client.post(
        path, json={"message": "", "session_id": "s"}, headers={"Origin": "https://evil.example"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"


def test_ops_action_cross_site_origin_post_is_rejected_403(ops_client):
    resp = ops_client.post(
        "/api/ops/action", json={"tool": "x"}, headers={"Origin": "https://evil.example"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"


def test_sec_fetch_site_cross_site_is_rejected_403_without_origin(chat_client):
    # Even without Origin (some privacy extensions strip it), the browser-only
    # Sec-Fetch-Site metadata still identifies the cross-site POST.
    resp = chat_client.post(
        "/api/chat", json={"message": ""}, headers={"Sec-Fetch-Site": "cross-site"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "CROSS_SITE_POST"


@pytest.mark.parametrize("fetch_site", ["same-origin", "same-site", "none"])
def test_sec_fetch_site_same_origin_is_allowed(chat_client, fetch_site):
    resp = chat_client.post(
        "/api/chat", json={"message": ""}, headers={"Sec-Fetch-Site": fetch_site}
    )
    assert resp.status_code == 400  # reached the handler


def test_wrong_content_type_with_body_is_rejected_415(chat_client):
    resp = chat_client.post(
        "/api/chat",
        content=b"message=x",
        headers={"Origin": "http://testserver", "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "JSON_CONTENT_TYPE_REQUIRED"


def test_preflight_options_is_never_blocked_by_the_boundary(chat_client):
    # CORS preflights are answered by CORSMiddleware (or 405 in this bare
    # app) — the boundary only wraps POST handlers, so an OPTIONS with a
    # hostile Origin must NOT surface a boundary 403.
    resp = chat_client.options(
        "/api/chat",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code != 403


# ---------------------------------------------------------------------------
# Escape hatch
# ---------------------------------------------------------------------------


def test_post_boundary_env_off_disables_the_boundary(chat_client, monkeypatch):
    monkeypatch.setenv(ui_security.UI_POST_BOUNDARY_ENV, "off")
    resp = chat_client.post(
        "/api/chat", json={"message": ""}, headers={"Origin": "https://evil.example"}
    )
    assert resp.status_code == 400  # reached the handler despite hostile Origin
