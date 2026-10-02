"""Client-visible tool error text (rm-077; MCP python-sdk #3314).

Since MCP Python SDK 2.1.0 the server hides the text of *unexpected* tool
exceptions: unless the handler raised ``ToolError``/``ResourceError`` the
client only receives a generic ``Error executing tool <name>``.
``server.clean_error`` used to return a bare ``RuntimeError``, so on the
resolved SDK 2.x runtime every hermes tool failure lost its reason. These
tests pin the regression on both supported SDK lanes (CI matrix installs
``mcp>=1.28.1,<2`` and ``mcp>=2,<3``): the unit test asserts the wrapped
type, and the client-path test drives a real server over stdio with a probe
tool that fails through ``clean_error`` exactly like the 11 real raise
sites, asserting the failure reason reaches the client session.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent

_SERVER_SCRIPT = (
    f"import sys; sys.path.insert(0, {str(REPO_ROOT)!r}); "
    "import server\n"
    "def probe_boom() -> str:\n"
    "    try:\n"
    "        raise ValueError('boom-reason-xyz')\n"
    "    except Exception as exc:\n"
    "        raise server.clean_error('probe_boom', exc) from exc\n"
    "app = server.build_server()\n"
    "app.add_tool(probe_boom)\n"
    "app.run('stdio')\n"
)

_DISABLED_ENV = (
    "HERMES_GPT_ENABLE_WRITE",
    "HERMES_GPT_ENABLE_MEMORY_WRITE",
    "HERMES_GPT_ENABLE_SESSION_SEARCH",
    "HERMES_GPT_ENABLE_TERMINAL",
    "HERMES_GPT_ENABLE_VISION",
    "HERMES_GPT_ENABLE_WEB",
    "HERMES_GPT_UNSAFE_REMOTE",
    "HERMES_GPT_BEARER_TOKEN",
    "HERMES_GPT_OAUTH_ENABLE",
)


def _server_env() -> dict[str, str]:
    """A clean read-only environment for the spawned stdio server."""
    env = {k: v for k, v in os.environ.items() if k not in _DISABLED_ENV}
    env["PYTHONPATH"] = str(REPO_ROOT)
    return env


def test_clean_error_wraps_as_sdk_toolerror():
    """clean_error returns the SDK's anticipated-failure type, not RuntimeError."""
    import server

    err = server.clean_error("hermes_read_file", ValueError("boom"))

    assert type(err).__name__ == "ToolError"
    assert "hermes_read_file failed: boom" in str(err)


def test_tool_failure_reason_reaches_client_over_stdio():
    """A failing tool surfaces its specific reason to a real client session.

    Without the ToolError migration the SDK 2.x lane would deliver only the
    generic ``Error executing tool hermes_read_file`` mask.
    """
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def scenario() -> tuple[bool, str]:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-c", _SERVER_SCRIPT],
            env=_server_env(),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await asyncio.wait_for(
                    session.call_tool("probe_boom", {}),
                    timeout=90,
                )
                is_error = bool(
                    getattr(result, "isError", False)
                    or getattr(result, "is_error", False)
                )
                parts = list(getattr(result, "content", []) or [])
                text = " ".join(
                    getattr(part, "text", "")
                    for part in parts
                    if getattr(part, "type", "") == "text"
                )
                return is_error, text

    is_error, text = asyncio.run(asyncio.wait_for(scenario(), timeout=180))

    assert is_error, f"expected a tool error result, got: {text!r}"
    assert "probe_boom failed: boom-reason-xyz" in text, (
        "client lost the failure reason (SDK 2.1+ #3314 mask); "
        f"received: {text!r}"
    )
