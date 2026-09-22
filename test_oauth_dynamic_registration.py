"""RFC 7591 dynamic client registration + public-client self-heal.

Reproduces the live 2026-09-06 18:42 connector outage: OpenAI's platform
attempted headless re-auth with an ephemeral client_id (401 "Unknown OAuth
client") and called POST /oauth/register (401 — endpoint absent), while the
scheme-flow credential carried no refresh token (scope lacked
offline_access) so the connector could never self-heal.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import time
from urllib.parse import parse_qs, urlparse

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from oauth_auth import (
    OAuthConfig,
    OAuthState,
    authorize,
    register_client,
    token,
)

CLIENT_ID = "chatgpt-client"
CLIENT_SECRET = "test-client-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
REDIRECT_URI = "https://chatgpt.com/connector/oauth/callback"
ISSUER = "https://mcp.example.com"

VERIFIER = "b" * 64
CHALLENGE_S256 = (
    base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest())
    .rstrip(b"=")
    .decode()
)

AIP_REDIRECT = "https://chatgpt.com/aip/oauth/callback"


def _config() -> OAuthConfig:
    return OAuthConfig(
        issuer=ISSUER,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uris=(REDIRECT_URI,),
        scope="hermes",
    )


def _build(state: OAuthState) -> TestClient:
    async def authorize_ep(request: Request) -> JSONResponse:
        return authorize(request, state)

    async def token_ep(request: Request) -> JSONResponse:
        return await token(request, state)

    async def register_ep(request: Request) -> JSONResponse:
        return await register_client(request, state)

    app = Starlette(
        routes=[
            Route("/oauth/authorize", authorize_ep, methods=["GET"]),
            Route("/oauth/token", token_ep, methods=["POST"]),
            Route("/oauth/register", register_ep, methods=["POST"]),
        ]
    )
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def state() -> OAuthState:
    return OAuthState(_config())


@pytest.fixture
def client(state: OAuthState) -> TestClient:
    return _build(state)


def _register(client: TestClient, **overrides):
    payload = {
        "client_name": "OpenAI apps flow",
        "redirect_uris": [AIP_REDIRECT],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
    }
    payload.update(overrides)
    return client.post("/oauth/register", json=payload)


def _authorize(client: TestClient, client_id: str, redirect: str, scope: str = "hermes"):
    return client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect,
            "scope": scope,
            "state": "s1",
            "code_challenge": CHALLENGE_S256,
            "code_challenge_method": "S256",
        },
    )


def _exchange(client: TestClient, code: str, redirect: str, client_id: str = ""):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
        "code_verifier": VERIFIER,
    }
    if client_id:
        data["client_id"] = client_id
    return client.post("/oauth/token", data=data)


# -- registration endpoint -------------------------------------------------


def test_metadata_advertises_registration_endpoint(client: TestClient):
    """2026-09-13 outage: the discovery doc omitted registration_endpoint.

    A credential-less ChatGPT connector polls
    ``/.well-known/oauth-authorization-server`` specifically for
    ``registration_endpoint``; with it missing the connector loops
    discovery -> 401 forever and can never onboard even though
    ``/oauth/register`` was live (verified live: loop ran since the
    2026-09-10 cutover; endpoint answered 201 on direct probe).
    """
    from oauth_auth import authorization_metadata

    app = Starlette(
        routes=[
            Route(
                "/.well-known/oauth-authorization-server",
                lambda request: authorization_metadata(request, OAuthState(_config())),
                methods=["GET"],
            )
        ]
    )
    probe = TestClient(app)
    response = probe.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["registration_endpoint"] == f"{ISSUER}/oauth/register"
    assert metadata["authorization_endpoint"] == f"{ISSUER}/oauth/authorize"
    assert metadata["token_endpoint"] == f"{ISSUER}/oauth/token"
    # every advertised endpoint is absolutely derived from the issuer
    for key in ("authorization_endpoint", "token_endpoint", "registration_endpoint"):
        assert metadata[key].startswith(f"{ISSUER}/")


def test_register_mints_dynamic_public_client(client: TestClient):
    response = _register(client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["client_id"] != CLIENT_ID
    assert body["client_id_issued_at"] > 0
    assert "client_secret" not in body
    assert body["redirect_uris"] == [AIP_REDIRECT]
    assert body["token_endpoint_auth_method"] == "none"


def test_register_refuses_non_chatgpt_redirects(client: TestClient):
    response = _register(client, redirect_uris=["https://evil.example.com/cb"])
    assert response.status_code == 400
    assert "redirect" in response.json()["error_description"].lower()


def test_register_refuses_confidential_auth_method(client: TestClient):
    response = _register(client, token_endpoint_auth_method="client_secret_post")
    assert response.status_code == 400


def test_register_rejects_malformed_payload(client: TestClient):
    response = client.post("/oauth/register", data="not-json")
    assert response.status_code == 400


def test_register_capacity_is_bounded(client: TestClient, state: OAuthState):
    codes = [_register(client).status_code for _ in range(state.max_dynamic_clients + 2)]
    assert 429 in codes


# -- dynamic client authorize + exchange ------------------------------------


def test_dynamic_client_authorizes_with_pkce(client: TestClient):
    dyn_id = _register(client).json()["client_id"]
    response = _authorize(client, dyn_id, AIP_REDIRECT)
    assert response.status_code == 302, response.text
    assert "code=" in response.headers["location"]
    assert "error" not in response.headers["location"]


def test_dynamic_client_redirect_must_match_registered(client: TestClient):
    dyn_id = _register(client).json()["client_id"]
    response = _authorize(client, dyn_id, REDIRECT_URI)  # not its registered one
    # error redirect per RFC (the client's redirect_uri is unknown to us, so
    # the static config allowlist catches it); never a usable code
    assert response.status_code in (302, 400)
    body = response.headers.get("location", "") + response.text
    assert "error" in body


def test_unknown_client_still_refused(client: TestClient):
    response = _authorize(client, "totally-unknown", AIP_REDIRECT)
    assert response.status_code == 401


def test_dynamic_client_full_flow_self_heals(client: TestClient):
    dyn_id = _register(client).json()["client_id"]
    auth = _authorize(client, dyn_id, AIP_REDIRECT, scope="hermes offline_access")
    assert auth.status_code == 302, auth.text
    code = auth.headers["location"].split("code=")[1].split("&")[0]
    tok = _exchange(client, code, AIP_REDIRECT, client_id=dyn_id)
    assert tok.status_code == 200, tok.text
    body = tok.json()
    assert body.get("refresh_token"), "offline_access must yield a refresh token"

    # self-heal: the refresh grant works secretless for a public client
    refresh = client.post(
        "/oauth/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": body["refresh_token"],
            "client_id": dyn_id,
        },
    )
    assert refresh.status_code == 200, refresh.text
    rotated = refresh.json()
    assert rotated["access_token"]
    assert rotated.get("refresh_token")


def test_dynamic_client_without_offline_access_still_gets_refresh_token(client: TestClient):
    """Every code exchange now yields a refresh token so a dying credential
    can self-heal (the 18:42 outage root cause)."""
    dyn_id = _register(client).json()["client_id"]
    auth = _authorize(client, dyn_id, AIP_REDIRECT, scope="hermes")
    code = auth.headers["location"].split("code=")[1].split("&")[0]
    tok = _exchange(client, code, AIP_REDIRECT, client_id=dyn_id)
    assert tok.status_code == 200, tok.text
    assert tok.json().get("refresh_token"), "refresh token must always be issued"


def test_dynamic_client_pkce_required(client: TestClient):
    dyn_id = _register(client).json()["client_id"]
    response = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": dyn_id,
            "redirect_uri": AIP_REDIRECT,
            "scope": "hermes",
        },
    )
    # error redirect to the registered redirect_uri; never a usable code
    assert response.status_code == 302
    assert "error=" in response.headers["location"]


def test_dynamic_client_registry_survives_state_serialization(client: TestClient, state: OAuthState):
    dyn_id = _register(client).json()["client_id"]
    bundle = state.export_dynamic_clients()
    state2 = OAuthState(_config())
    state2.import_dynamic_clients(bundle)
    response = _authorize(_build(state2), dyn_id, AIP_REDIRECT)
    assert "code=" in response.headers["location"]


def test_dynamic_client_registry_survives_disk_restart(tmp_path):
    root = tmp_path / "hermes"
    state1 = OAuthState(_config())
    state1.restore_tokens(root)
    dyn_id = _register(_build(state1)).json()["client_id"]
    state1.persist_tokens(root)

    state2 = OAuthState(_config())
    state2.restore_tokens(root)
    response = _authorize(_build(state2), dyn_id, AIP_REDIRECT)
    assert "code=" in response.headers["location"]


# -- legacy static client unchanged ------------------------------------------


def test_legacy_static_client_flow_unchanged(client: TestClient):
    """chatgpt-client confidential + optional-PKCE compat is untouched: in
    optional mode a challenge-less authorize still issues a code (the
    confidential redemption is enforced at the token endpoint)."""
    state_opt = OAuthState(
        OAuthConfig(
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uris=(REDIRECT_URI,),
            scope="hermes",
            pkce_mode="optional",
        )
    )
    legacy = _build(state_opt)
    auth = legacy.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "hermes",
            "state": "legacy",
        },
    )
    assert auth.status_code == 302, auth.text
    assert "code=" in auth.headers["location"]


# -- registry lifecycle (TTL eviction, import parity, DCR gate, iss) ---------


def test_cleanup_evicts_expired_dynamic_clients(state: OAuthState, client: TestClient):
    dyn_id = _register(client).json()["client_id"]
    assert state.is_dynamic_client(dyn_id)
    state.dynamic_clients[dyn_id] = dataclasses.replace(
        state.dynamic_clients[dyn_id], expires_at=time.time() - 1
    )
    state.cleanup()
    assert dyn_id not in state.dynamic_clients
    assert not state.is_dynamic_client(dyn_id)


def test_expired_dynamic_client_refused_before_cleanup(state: OAuthState, client: TestClient):
    dyn_id = _register(client).json()["client_id"]
    state.dynamic_clients[dyn_id] = dataclasses.replace(
        state.dynamic_clients[dyn_id], expires_at=time.time() - 1
    )
    # no cleanup() call: the lookup itself must treat an expired dynamic
    # client as unknown, so expiry cannot be raced by skipping cleanup
    response = _authorize(client, dyn_id, AIP_REDIRECT)
    assert response.status_code == 401


def test_capacity_exhaustion_recovers_after_ttl(state: OAuthState, client: TestClient):
    """The 2026-09-22 exhaustion vector: /oauth/register is unauthenticated,
    so anyone can fill the 64-slot registry with 429s. TTL eviction must make
    the exhaustion self-healing instead of permanent."""
    for _ in range(state.max_dynamic_clients):
        assert _register(client).status_code == 201
    assert _register(client).status_code == 429
    expired = time.time() - 1
    for dyn_id, dynamic in list(state.dynamic_clients.items()):
        state.dynamic_clients[dyn_id] = dataclasses.replace(dynamic, expires_at=expired)
    response = _register(client)
    assert response.status_code == 201, response.text


def test_import_applies_live_registration_parity(state: OAuthState):
    """The persisted registry is operator-writable state: every imported
    entry must pass the same validation as a live registration."""
    payload = [
        # a non-dyn id attempting to shadow the operator-provisioned client
        {"client_id": CLIENT_ID, "redirect_uris": [AIP_REDIRECT]},
        # redirects the register endpoint would refuse
        {"client_id": "dyn-evil", "redirect_uris": ["https://evil.example.com/cb"]},
        # more than the 8-URI live cap
        {"client_id": "dyn-many", "redirect_uris": [AIP_REDIRECT] * 9},
        # already expired
        {
            "client_id": "dyn-dead",
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": 1.0,
            "expires_at": 2.0,
        },
        # valid
        {
            "client_id": "dyn-good",
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": 1.0,
            "expires_at": time.time() + 3600.0,
        },
    ]
    assert state.import_dynamic_clients(payload) == 1
    assert set(state.dynamic_clients) == {"dyn-good"}


def test_import_rejects_tampered_redirect_payload():
    """A tampered store payload cannot smuggle in redirects the register
    endpoint refuses (import parity with live registration)."""
    probe = OAuthState(_config())
    probe.import_dynamic_clients(
        [
            {
                "client_id": "dyn-evil",
                "redirect_uris": ["https://evil.example.com/cb"],
                "expires_at": time.time() + 3600.0,
            }
        ]
    )
    assert not probe.is_dynamic_client("dyn-evil")
    response = _authorize(_build(probe), "dyn-evil", "https://evil.example.com/cb")
    assert response.status_code == 401


def test_import_gives_pre_ttl_rows_a_ttl_from_registration(state: OAuthState):
    """Registry rows persisted before TTLs existed must age out, not live
    forever: on import they are granted a full fresh TTL (measured from
    import time, never earlier), after which cleanup() evicts them."""
    from oauth_auth import DYNAMIC_CLIENT_TTL_SECONDS

    assert (
        state.import_dynamic_clients(
            [
                {
                    "client_id": "dyn-old",
                    "redirect_uris": [AIP_REDIRECT],
                    "registered_at": time.time() - 1,
                }
            ]
        )
        == 1
    )
    client = state.dynamic_clients["dyn-old"]
    assert client.expires_at >= time.time() + DYNAMIC_CLIENT_TTL_SECONDS - 5
    state.dynamic_clients["dyn-old"] = dataclasses.replace(
        client, expires_at=time.time() - 1
    )
    state.cleanup()
    assert "dyn-old" not in state.dynamic_clients


def test_registry_ttl_survives_export_round_trip(client: TestClient, state: OAuthState):
    dyn_id = _register(client).json()["client_id"]
    bundle = state.export_dynamic_clients()
    assert bundle[0]["expires_at"] > bundle[0]["registered_at"]
    state2 = OAuthState(_config())
    assert state2.import_dynamic_clients(bundle) == 1
    assert state2.dynamic_clients[dyn_id].expires_at == bundle[0]["expires_at"]
    assert "code=" in _authorize(_build(state2), dyn_id, AIP_REDIRECT).headers["location"]


def test_metadata_dcr_gate_controls_registration_endpoint(monkeypatch):
    from oauth_auth import OAUTH_DCR_ENV, authorization_metadata

    def _metadata() -> dict:
        app = Starlette(
            routes=[
                Route(
                    "/.well-known/oauth-authorization-server",
                    lambda request: authorization_metadata(request, OAuthState(_config())),
                    methods=["GET"],
                )
            ]
        )
        probe = TestClient(app)
        response = probe.get("/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        return response.json()

    monkeypatch.setenv(OAUTH_DCR_ENV, "0")
    assert "registration_endpoint" not in _metadata()
    monkeypatch.setenv(OAUTH_DCR_ENV, "1")
    assert _metadata().get("registration_endpoint") == f"{ISSUER}/oauth/register"


def test_authorize_redirect_carries_rfc9207_iss(client: TestClient):
    """RFC 9207: the issuer identifier rides every authorization-code
    redirect so the client can bind the code to the AS that issued it."""
    dyn_id = _register(client).json()["client_id"]
    dynamic = _authorize(client, dyn_id, AIP_REDIRECT)
    static = _authorize(client, CLIENT_ID, REDIRECT_URI)
    for response in (dynamic, static):
        assert response.status_code == 302, response.text
        query = parse_qs(urlparse(response.headers["location"]).query)
        assert query["iss"] == [ISSUER]
        assert query["code"]


def test_authorize_error_redirect_carries_rfc9207_iss(client: TestClient):
    """RFC 9207 §2: error responses are authorization responses too — the
    iss parameter MUST ride the error redirect as well, so a client can
    bind a failure (not just an issued code) to exactly this AS."""
    response = client.get(
        "/oauth/authorize",
        params={
            "response_type": "token",  # only code is supported
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "hermes",
            "state": "s1",
            "code_challenge": CHALLENGE_S256,
            "code_challenge_method": "S256",
        },
    )
    assert response.status_code == 302, response.text
    query = parse_qs(urlparse(response.headers["location"]).query)
    assert query["error"] == ["unsupported_response_type"]
    assert query["iss"] == [ISSUER]
    assert query["state"] == ["s1"]
    assert "code" not in query


def test_metadata_advertises_iss_parameter_supported():
    """RFC 9207 §2.3: an AS supporting iss on authorization responses MUST
    advertise authorization_response_iss_parameter_supported=true in its
    metadata; it is unconditional (iss is never omitted, not even for the
    DCR-gated single-client profile)."""
    from oauth_auth import authorization_metadata

    def _metadata() -> dict:
        app = Starlette(
            routes=[
                Route(
                    "/.well-known/oauth-authorization-server",
                    lambda request: authorization_metadata(request, OAuthState(_config())),
                    methods=["GET"],
                )
            ]
        )
        probe = TestClient(app)
        response = probe.get("/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        return response.json()

    assert _metadata()["authorization_response_iss_parameter_supported"] is True


def test_import_dedupes_ids_and_never_overwrites(state: OAuthState):
    """Import accounting is exact: a duplicated id inside one payload counts
    once (first occurrence wins) and an id already in the registry never
    silently replaces a live row's redirects or expiry."""
    payload = [
        {
            "client_id": "dyn-dup",
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": time.time() - 10,
            "expires_at": time.time() + 3600.0,
        },
        # same id again with different (still allowlisted) redirects
        {
            "client_id": "dyn-dup",
            "redirect_uris": ["https://openai.com/other/callback"],
            "registered_at": time.time() - 5,
            "expires_at": time.time() + 7200.0,
        },
    ]
    assert state.import_dynamic_clients(payload) == 1
    assert state.dynamic_clients["dyn-dup"].redirect_uris == (AIP_REDIRECT,)

    # an id already registered live is not overwritten by an import
    live = state.register_dynamic_client([AIP_REDIRECT])
    before = state.dynamic_clients[live.client_id].redirect_uris
    assert (
        state.import_dynamic_clients(
            [
                {
                    "client_id": live.client_id,
                    "redirect_uris": ["https://openai.com/other/callback"],
                    "registered_at": time.time(),
                    "expires_at": time.time() + 3600.0,
                }
            ]
        )
        == 0
    )
    assert state.dynamic_clients[live.client_id].redirect_uris == before
