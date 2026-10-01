"""Loop-offload regression tests for the OAuth token-store path (rm-085).

Guards the serving event loop against synchronous token-store (sqlite) work:

- ``BearerAuthMiddleware`` must run bearer validation off the loop.
- The ``/oauth/token`` endpoint must run client auth plus the code/refresh
  exchanges off the loop — asserted per site (client auth, authorization-code
  exchange, refresh exchange), so re-inlining any single call fails its own
  test.

Also pins the concurrency consequence of the offload: exchanges now run on
worker threads, so single-use fences (the authorization-code replay cache)
must be serialized between those threads — exactly one racing redemption of a
code may mint.

Pattern (mirrors the landed rm-076 regression style): while a deliberately
slow blocking call executes for the request, a heartbeat task scheduled on
the same loop must keep ticking. Before the fix the heartbeat starves.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import time
from types import SimpleNamespace

from starlette.requests import Request

import oauth_auth
from oauth_auth import BearerAuthMiddleware
from oauth_auth import token as oauth_token_endpoint

BLOCK_SECONDS = 0.4

CLIENT_ID = "chatgpt-client"
CLIENT_SECRET = "test-client-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ISSUER = "https://mcp.example.com"
REDIRECT_URI = "https://chatgpt.com/connector/oauth/callback"
RESOURCE = f"{ISSUER}/mcp"
VERIFIER = "a" * 64


def _ticks_while(coro_factory):
    """Run ``coro_factory()`` and count heartbeat ticks (20ms) during it."""

    async def scenario():
        ticks = 0

        async def heartbeat():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.02)
                ticks += 1

        hb = asyncio.create_task(heartbeat())
        try:
            await asyncio.wait_for(coro_factory(), timeout=30)
        finally:
            hb.cancel()
            try:
                await hb
            except asyncio.CancelledError:
                pass
        return ticks

    return asyncio.run(scenario())


def _http_scope(method="POST", path="/mcp", body=b"", content_type=None):
    headers = [(b"authorization", b"Bearer tok")]
    if content_type:
        headers.append((b"content-type", content_type))
    if body:
        headers.append((b"content-length", str(len(body)).encode("ascii")))
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
        "query_string": b"",
    }


def _receive_factory(body):
    sent = False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return receive


async def _send_noop(message):
    pass


def test_bearer_validation_runs_off_event_loop(monkeypatch):
    def slow_validate(token_value, state, *, static_token=None):
        time.sleep(BLOCK_SECONDS)
        return True

    monkeypatch.setattr(oauth_auth, "validate_bearer_token", slow_validate)
    monkeypatch.setattr(oauth_auth, "static_bearer_from_env", lambda: "")

    class Sentinel:
        served = False

        async def __call__(self, scope, receive, send):
            Sentinel.served = True

    middleware = BearerAuthMiddleware(Sentinel(), state=SimpleNamespace(), static_token=None)
    ticks = _ticks_while(
        lambda: middleware(_http_scope(), _receive_factory(b""), _send_noop)
    )
    assert Sentinel.served, "slow validation should have accepted the request"
    assert ticks >= 5, f"event loop stalled during bearer validation (ticks={ticks})"


class _SlowExchangeState:
    """Only ``kind`` blocks; every other exchange step is instant.

    One slow site per test keeps the heartbeat assertion sharp: if the one
    blocking call is inlined onto the loop, ticks collapse to ~0, and no
    offloaded sibling call can mask it.
    """

    def __init__(self, kind: str) -> None:
        self.kind = kind

    def exchange_authorization_code(self, **kwargs):
        if self.kind == "authorization_code":
            time.sleep(BLOCK_SECONDS)
        return {"access_token": "at", "token_type": "Bearer", "expires_in": 3600}

    def exchange_refresh_token(self, **kwargs):
        if self.kind == "refresh_token":
            time.sleep(BLOCK_SECONDS)
        return {
            "access_token": "at",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "rt",
            "scope": "hermes",
        }


def _token_request(body: bytes):
    return Request(
        _http_scope(body=body, content_type=b"application/x-www-form-urlencoded"),
        _receive_factory(body),
    )


def test_oauth_code_exchange_runs_off_event_loop(monkeypatch):
    monkeypatch.setattr(oauth_auth, "_authenticate_client", lambda request, form, state: "client-1")
    body = b"grant_type=authorization_code&code=c&client_id=client-1"
    ticks = _ticks_while(
        lambda: oauth_token_endpoint(_token_request(body), _SlowExchangeState("authorization_code"))
    )
    assert ticks >= 5, f"event loop stalled during authorization-code exchange (ticks={ticks})"


def test_oauth_refresh_exchange_runs_off_event_loop(monkeypatch):
    monkeypatch.setattr(oauth_auth, "_authenticate_client", lambda request, form, state: "client-1")
    body = b"grant_type=refresh_token&refresh_token=r&client_id=client-1"
    ticks = _ticks_while(
        lambda: oauth_token_endpoint(_token_request(body), _SlowExchangeState("refresh_token"))
    )
    assert ticks >= 5, f"event loop stalled during refresh exchange (ticks={ticks})"


def test_oauth_client_auth_runs_off_event_loop(monkeypatch):
    def slow_auth(request, form, state):
        time.sleep(BLOCK_SECONDS)
        return "client-1"

    monkeypatch.setattr(oauth_auth, "_authenticate_client", slow_auth)
    body = b"grant_type=refresh_token&refresh_token=r&client_id=client-1"
    ticks = _ticks_while(
        lambda: oauth_token_endpoint(_token_request(body), _SlowExchangeState("refresh_token"))
    )
    assert ticks >= 5, f"event loop stalled during OAuth client authentication (ticks={ticks})"


def test_concurrent_code_redemption_mints_exactly_once(monkeypatch):
    """rm-085 review fix: worker-thread redemptions stay single-use.

    ``asyncio.to_thread`` makes concurrent ``/oauth/token`` requests genuinely
    parallel; without the OAuthState mutation lock two racing redemptions of
    one authorization code can both pass the ``used_auth_codes`` check and
    both mint token sets (RFC 6749 §4.1.2). The barrier releases both threads
    into the check together, and the injected mint delay models the durable
    commit latency that sits between the check and the write in server mode.
    """
    state = oauth_auth.OAuthState(
        oauth_auth.OAuthConfig(
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uris=(REDIRECT_URI,),
            scope="hermes",
        )
    )
    code = state.issue_authorization_code(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="hermes",
        resource=RESOURCE,
        code_challenge=oauth_auth._s256(VERIFIER),
    )
    original_new_access_token = state._new_access_token

    def slow_new_access_token(**kwargs):
        time.sleep(0.05)
        return original_new_access_token(**kwargs)

    monkeypatch.setattr(state, "_new_access_token", slow_new_access_token)

    barrier = threading.Barrier(2)

    def redeem():
        try:
            barrier.wait(timeout=10)
        except threading.BrokenBarrierError:  # pragma: no cover - harness timing
            return "broken_barrier"
        try:
            state.exchange_authorization_code(
                code=code,
                client_id=CLIENT_ID,
                redirect_uri=REDIRECT_URI,
                code_verifier=VERIFIER,
            )
            return "ok"
        except oauth_auth.OAuthError as exc:
            return exc.error

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(redeem), pool.submit(redeem)]
        results = sorted(future.result() for future in futures)

    assert results == ["invalid_grant", "ok"], results
    assert len(state.used_auth_codes) == 1
    assert len(state.access_tokens) == 1, "both racing redemptions minted (single-use violated)"
    assert len(state.refresh_tokens) == 1
