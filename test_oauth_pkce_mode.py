"""HERMES_GPT_OAUTH_PKCE_MODE knob tests.

"required" (default): challenge-less authorize refused, challenge-less codes
never exchanged. "optional": pre-2026-08-31 confidential-client compat —
challenge-less codes redeemable only with the client_secret.
"""

from __future__ import annotations

import base64
import hashlib
import urllib.parse

import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from oauth_auth import (
    OAUTH_CLIENT_ID_ENV,
    OAUTH_CLIENT_SECRET_ENV,
    OAUTH_ENABLE_ENV,
    OAUTH_ISSUER_ENV,
    OAUTH_PKCE_MODE_ENV,
    OAUTH_REDIRECT_URI_ENV,
    OAuthConfig,
    OAuthState,
    authorization_metadata,
    authorize,
    config_from_env,
    protected_resource_metadata,
    token,
)

CLIENT_ID = "chatgpt-client"
CLIENT_SECRET = "test-client-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
REDIRECT_URI = "https://chatgpt.com/connector/oauth/callback"
ISSUER = "https://mcp.example.com"
VERIFIER = "a" * 64


def s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _client(pkce_mode: str) -> TestClient:
    state = OAuthState(
        OAuthConfig(
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uris=(REDIRECT_URI,),
            scope="hermes",
            pkce_mode=pkce_mode,
        )
    )

    async def resource_endpoint(request):
        return protected_resource_metadata(request, state)

    async def metadata_endpoint(request):
        return authorization_metadata(request, state)

    async def authorize_endpoint(request):
        return authorize(request, state)

    async def token_endpoint(request):
        return await token(request, state)

    app = Starlette(
        routes=[
            Route("/oauth/authorize", authorize_endpoint),
            Route("/oauth/token", token_endpoint, methods=["POST"]),
        ]
    )
    return TestClient(app)


def _authorize(client: TestClient, **extra) -> tuple[str, str]:
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "hermes",
        "state": "s",
        "resource": ISSUER + "/mcp",
    }
    params.update(extra)
    response = client.get("/oauth/authorize", params=params, follow_redirects=False)
    query = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers["location"]).query)
    return query.get("error", [""])[0], query.get("code", [""])[0]


def _exchange(client: TestClient, code: str, secret: str, verifier: str):
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    if secret:
        data["client_secret"] = secret
    if verifier:
        data["code_verifier"] = verifier
    return client.post("/oauth/token", data=data)


@pytest.fixture
def optional_client() -> TestClient:
    return _client("optional")


@pytest.fixture
def required_client() -> TestClient:
    return _client("required")


def test_optional_confidential_flow(optional_client):
    error, code = _authorize(optional_client)
    assert error == ""
    assert code
    response = _exchange(optional_client, code, CLIENT_SECRET, "")
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_optional_rejects_secretless_challengeless_redemption(optional_client):
    _, code = _authorize(optional_client)
    response = _exchange(optional_client, code, "", VERIFIER)
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_grant"


def test_optional_pkce_flow_still_works(optional_client):
    _, code = _authorize(optional_client, code_challenge=s256(VERIFIER), code_challenge_method="S256")
    response = _exchange(optional_client, code, "", VERIFIER)
    assert response.status_code == 200


def test_required_rejects_challengeless_authorize(required_client):
    error, code = _authorize(required_client)
    assert error == "invalid_request"
    assert "code_challenge" in error or code == ""


def test_required_pkce_flow_still_works(required_client):
    _, code = _authorize(required_client, code_challenge=s256(VERIFIER), code_challenge_method="S256")
    response = _exchange(required_client, code, "", VERIFIER)
    assert response.status_code == 200


def _set_oauth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(OAUTH_ENABLE_ENV, "1")
    monkeypatch.setenv(OAUTH_ISSUER_ENV, ISSUER)
    monkeypatch.setenv(OAUTH_CLIENT_ID_ENV, CLIENT_ID)
    monkeypatch.setenv(OAUTH_CLIENT_SECRET_ENV, CLIENT_SECRET)
    monkeypatch.setenv(OAUTH_REDIRECT_URI_ENV, REDIRECT_URI)


def test_env_knob_default_is_required(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(OAUTH_PKCE_MODE_ENV, raising=False)
    _set_oauth_env(monkeypatch)
    config = config_from_env()
    assert config is not None
    assert config.pkce_mode == "required"


def test_env_knob_optional(monkeypatch: pytest.MonkeyPatch):
    _set_oauth_env(monkeypatch)
    monkeypatch.setenv(OAUTH_PKCE_MODE_ENV, "Optional ")
    config = config_from_env()
    assert config is not None
    assert config.pkce_mode == "optional"


def test_env_knob_rejects_invalid(monkeypatch: pytest.MonkeyPatch):
    _set_oauth_env(monkeypatch)
    monkeypatch.setenv(OAUTH_PKCE_MODE_ENV, "sometimes")
    with pytest.raises(ValueError, match="pkce_mode"):
        config_from_env()
