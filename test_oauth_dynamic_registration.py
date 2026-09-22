"""RFC 7591 dynamic client registration + public-client self-heal.

Reproduces the live 2026-09-06 18:42 connector outage: OpenAI's platform
attempted headless re-auth with an ephemeral client_id (401 "Unknown OAuth
client") and called POST /oauth/register (401 — endpoint absent), while the
scheme-flow credential carried no refresh token (scope lacked
offline_access) so the connector could never self-heal.
"""

from __future__ import annotations

import base64
import hashlib

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
    """The registry capacity cap (429 at max_dynamic_clients) in isolation.

    Each registration resets the per-peer rate budget so the 429 asserted
    here can only come from the capacity cap, not the limiter (review
    finding 6: this test silently switched to limiter-429s after rm-048
    added the budget check).
    """
    for _ in range(state.max_dynamic_clients + 2):
        state._register_hits.clear()  # isolate the capacity branch
        response = _register(client)
        if response.status_code == 429:
            break
    else:
        pytest.fail("registry capacity cap never engaged")
    assert response.status_code == 429
    assert len(state.dynamic_clients) == state.max_dynamic_clients


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


# -- rm-048: registration lifecycle (rate limit, TTL, reclaim, purge) -------


def test_register_rate_limited_per_peer(client: TestClient, state: OAuthState):
    """The unauthenticated register endpoint carries a per-peer fixed-window
    budget: a single peer cannot fill the 64-slot registry in one burst."""
    statuses = [_register(client).status_code for _ in range(7)]
    assert statuses[:5] == [201] * 5
    assert statuses[5:] == [429, 429]
    # the budget is per-peer, not global: another peer still registers
    assert state.register_rate_allows("another-peer") is True
    assert state.register_rate_allows("testclient") is False


def test_expired_dynamic_client_fails_closed(client: TestClient, state: OAuthState):
    """TTL expiry kills the registration everywhere at once: authorize no
    longer recognizes the client and token exchange refuses it."""
    import dataclasses
    import time as _time

    dyn_id = _register(client).json()["client_id"]
    live = state.dynamic_clients[dyn_id]
    state.dynamic_clients[dyn_id] = dataclasses.replace(
        live, expires_at=_time.time() - 1
    )
    assert state.is_dynamic_client(dyn_id) is False
    response = _authorize(client, dyn_id, AIP_REDIRECT)
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"
    exchange = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": "unused",
            "redirect_uri": AIP_REDIRECT,
            "code_verifier": VERIFIER,
            "client_id": dyn_id,
        },
    )
    assert exchange.status_code == 401


def test_register_reclaims_expired_capacity(client: TestClient):
    """A registry full of expired entries self-heals: registration reclaims
    expired slots instead of returning 429 forever (fill-up DoS backstop)."""
    import dataclasses
    import time as _time

    from oauth_auth import OAuthState as _OS

    capped = _OS(_config(), max_dynamic_clients=2)
    capped_client = _build(capped)
    first = _register(capped_client).json()["client_id"]
    second = _register(capped_client).json()["client_id"]
    assert _register(capped_client).status_code == 429  # capacity reached
    for cid in (first, second):
        live = capped.dynamic_clients[cid]
        capped.dynamic_clients[cid] = dataclasses.replace(
            live, expires_at=_time.time() - 1
        )
    reclaimed = _register(capped_client)
    assert reclaimed.status_code == 201


def test_cleanup_prunes_expired_dynamic_clients(client: TestClient, state: OAuthState):
    import dataclasses
    import time as _time

    dyn_id = _register(client).json()["client_id"]
    live = state.dynamic_clients[dyn_id]
    state.dynamic_clients[dyn_id] = dataclasses.replace(
        live, expires_at=_time.time() - 1
    )
    state.cleanup()
    assert dyn_id not in state.dynamic_clients


def test_purge_dynamic_client_round_trip(client: TestClient, state: OAuthState):
    """Operator purge: removes the registration (idempotent), fails closed
    immediately, and lists the registry with expiry visibility."""
    dyn_id = _register(client).json()["client_id"]
    listed = state.list_dynamic_clients()
    assert [entry["client_id"] for entry in listed] == [dyn_id]
    assert listed[0]["expired"] is False
    assert listed[0]["expires_at"] > listed[0]["registered_at"]
    assert state.purge_dynamic_client(dyn_id) is True
    assert state.purge_dynamic_client(dyn_id) is False
    response = _authorize(client, dyn_id, AIP_REDIRECT)
    assert response.status_code == 401


def test_import_rejects_non_registerable_redirects(client: TestClient):
    """Restored registry data is re-validated against the chatgpt.com-family
    allowlist — persisted junk is not resurrected."""
    forged = [
        {
            "client_id": "dyn-forged",
            "redirect_uris": ["https://evil.example.com/callback"],
            "registered_at": 1,
            "expires_at": 4102444800.0,
        }
    ]
    fresh = OAuthState(_config())
    assert fresh.import_dynamic_clients(forged) == 0
    assert fresh.is_dynamic_client("dyn-forged") is False


def test_import_bounds_legacy_entries_without_expiry(client: TestClient):
    """Pre-TTL payloads (no expires_at) get a TTL from restore time instead of
    living forever; a future expiry is preserved verbatim."""
    legacy = [
        {
            "client_id": "dyn-legacy",
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": 1,
        }
    ]
    fresh = OAuthState(_config())
    assert fresh.import_dynamic_clients(legacy) == 1
    assert fresh.is_dynamic_client("dyn-legacy") is True
    bound = fresh.dynamic_clients["dyn-legacy"].expires_at
    import time as _time

    assert _time.time() < bound <= _time.time() + 7 * 24 * 3600 + 5


# -- review-fix regressions (independent_review 4f15d132) ------------------


def test_dynamic_client_bearer_token_validates(client: TestClient, state: OAuthState):
    """Review finding 1 (HIGH): dynamic-client access tokens must pass bearer
    validation end-to-end. config.client_registered only knows static
    clients, so every gate funneling through it (validate_access_token,
    _decode_signed_access_token, _durable_access_token_valid) 401'd a
    DCR-onboarded connector at /mcp — the failure mode DCR exists to fix,
    resurfaced one leg later. The state-level gate accepts live dynamic
    registrations and fails closed on expiry/purge.
    """
    import dataclasses
    import time as _time
    import urllib.parse

    dyn_id = _register(client).json()["client_id"]
    response = _authorize(client, dyn_id, AIP_REDIRECT, scope="hermes offline_access")
    assert response.status_code == 302, response.text
    code = urllib.parse.parse_qs(
        urllib.parse.urlparse(response.headers["location"]).query
    )["code"][0]
    exchanged = _exchange(client, code, AIP_REDIRECT, client_id=dyn_id)
    assert exchanged.status_code == 200, exchanged.text
    access_token = exchanged.json()["access_token"]

    # static baseline: the configured client still validates
    assert state.config.client_registered(CLIENT_ID) is True
    # the dynamic registration now validates too (was False pre-fix)
    assert state.validate_access_token(access_token) is True

    # fail closed: expiry kills the bearer leg as well
    live = state.dynamic_clients[dyn_id]
    state.dynamic_clients[dyn_id] = dataclasses.replace(
        live, expires_at=_time.time() - 1
    )
    assert state.validate_access_token(access_token) is False


def test_import_rejects_shadowing_oversized_and_non_ascii(client: TestClient, state: OAuthState):
    """Review finding 7: import re-validation must match register's budget —
    no static-id shadowing (dynamic-first authorize lookup), no >8 redirect
    payload, and restored ids must survive ASCII compare_digest lookups.
    """
    payload = [
        {  # (a) shadows the static client -> never imported
            "client_id": CLIENT_ID,
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": 1,
        },
        {  # (b) nine redirects exceeds the 1..8 budget enforced at register
            "client_id": "dyn-oversized",
            "redirect_uris": [f"https://chatgpt.com/aip/cb{i}" for i in range(9)],
            "registered_at": 1,
        },
        {  # (c) non-ASCII id would TypeError inside compare_digest
            "client_id": "dyn-\u5ba2\u6237\u7aef",
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": 1,
        },
        {  # (d) valid entry imports
            "client_id": "dyn-good",
            "redirect_uris": [AIP_REDIRECT],
            "registered_at": 1,
        },
    ]
    assert state.import_dynamic_clients(payload) == 1
    assert set(state.dynamic_clients) == {"dyn-good"}
    assert state.is_dynamic_client(CLIENT_ID) is False  # static id unshadowed


def test_register_rate_window_prunes_stale_peers(client: TestClient, state: OAuthState):
    """Review finding 8: _register_hits grows unboundedly with distinct peer
    keys; an expired window prunes stale peers so the map stays bounded."""
    import time as _time

    state._register_hits["stale-peer"] = (_time.time() - 3600.0, 1)
    assert state.register_rate_allows("fresh-peer") is True
    assert "stale-peer" not in state._register_hits
    assert "fresh-peer" in state._register_hits
