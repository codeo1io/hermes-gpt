"""Regression tests for the bearer-token ASCII guard (rm-181, B4 class).

The B4 class: a non-ASCII credential reaching ``hmac.compare_digest`` raises
``TypeError: comparing strings with non-ASCII characters is not supported``.
The token-endpoint paths (``authorize``) and ``_authenticate_client`` already
guard; ``validate_bearer_token`` — the path every protected route takes via
``BearerAuthMiddleware`` — was the last unguarded site and surfaced as an
unauthenticated 500. See oauth_auth.py:1303 (guard) and :1444/:1609 (twins).
"""

from __future__ import annotations

import hmac

import pytest

import oauth_auth


def test_non_ascii_bearer_token_is_rejected_not_raised() -> None:
    # Pre-guard this raised TypeError inside hmac.compare_digest.
    token = "b\u00e9arer-token-\u00fc"
    assert (
        oauth_auth.validate_bearer_token(token, None, static_token="correct-token")
        is False
    )


def test_non_ascii_bearer_token_without_static_token_is_rejected() -> None:
    assert oauth_auth.validate_bearer_token("t\u00f6ken", None) is False


def test_ascii_bearer_token_still_validates_against_static_token() -> None:
    assert (
        oauth_auth.validate_bearer_token(
            "correct-token", None, static_token="correct-token"
        )
        is True
    )


def test_ascii_bearer_token_wrong_value_still_rejected() -> None:
    assert (
        oauth_auth.validate_bearer_token(
            "wrong-token", None, static_token="correct-token"
        )
        is False
    )


def test_empty_bearer_token_still_rejected() -> None:
    assert (
        oauth_auth.validate_bearer_token("", None, static_token="correct-token")
        is False
    )


def test_regression_proof_compare_digest_raises_on_non_ascii() -> None:
    # Documents the failure mode the guard prevents: without the early
    # isascii() return, hmac.compare_digest itself raises.
    with pytest.raises(TypeError):
        hmac.compare_digest("b\u00e9", "correct-token")


def test_bearer_auth_middleware_non_ascii_header_is_401_not_500() -> None:
    """End-to-end: a non-ASCII Authorization header must not crash the app."""
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    async def protected(request: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/protected", protected)])
    app = oauth_auth.BearerAuthMiddleware(app, static_token="correct-token")
    client = TestClient(app, raise_server_exceptions=False)
    # httpx rejects non-ASCII header strings, but a real server (h11/uvicorn)
    # decodes header bytes as latin-1, so non-ASCII header values DO reach
    # Starlette as non-ASCII str. Send the wire bytes to reproduce that.
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer t\u00f6ken".encode("latin-1")},
    )
    assert response.status_code == 401, response.text
