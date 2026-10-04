"""Async execution-semantics regression tests (run e29c25913c00, batch B1).

Covers the SDK-1 hazards from the 2026-09-23 adversarial assessment that are
fixed on the SERVER side (tool bodies themselves): ``hermes_web_extract`` /
``hermes_vision_analyze`` called ``asyncio.run()`` inside *sync* tool bodies —
a 100% ``RuntimeError`` under MCP SDK 1, which executes sync tools directly
on the event loop. The two tools are now async bodies that ``await`` their
helpers.

The ``mcp_compat.HermesMCP.add_tool`` SDK-1 offload wrapper that shipped with
these fixes was REMOVED 2026-10-05 as superseded capability: deployments pin
MCP SDK 2 (``mcp>=2``), which offloads sync tools natively
(``anyio.to_thread.run_sync``), making the wrapper dead code on every
supported runtime. mcp_compat.py is now identical to upstream.
"""

from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace

import pytest

import server


@pytest.mark.parametrize("tool_name", ["hermes_web_extract", "hermes_vision_analyze"])
def test_tool_bodies_are_coroutine_functions(tool_name):
    assert inspect.iscoroutinefunction(getattr(server, tool_name))


@pytest.mark.parametrize("tool_name", ["hermes_web_extract", "hermes_vision_analyze"])
def test_tool_bodies_contain_no_nested_asyncio_run(tool_name):
    source = inspect.getsource(getattr(server, tool_name))
    assert "asyncio.run(" not in source


def test_async_tools_run_on_a_live_event_loop(monkeypatch):
    """rm-035 regression harness: enabled-path, executed inside a running
    loop exactly as SDK 1 would dispatch it. Pre-fix this raised
    ``RuntimeError: asyncio.run() cannot be called from a running event
    loop``."""
    monkeypatch.setattr(server, "require_imports", lambda: None)
    monkeypatch.setenv(server.ENABLE_VISION_ENV, "1")
    monkeypatch.setenv(server.ENABLE_WEB_ENV, "1")

    async def fake_vision(**kwargs):
        return f"saw:{kwargs.get('image_url')}"

    async def fake_extract(**kwargs):
        return f"extracted:{kwargs.get('urls')}"

    monkeypatch.setattr(
        server, "vision_tool", SimpleNamespace(vision_analyze_tool=fake_vision)
    )
    monkeypatch.setattr(
        server, "web_tool", SimpleNamespace(web_extract_tool=fake_extract)
    )

    async def main():
        vision = await server.hermes_vision_analyze(
            image_url="https://example.com/i.png", question="what is this?"
        )
        web = await server.hermes_web_extract(
            urls=["https://example.com/a"], char_limit=10
        )
        return vision, web

    vision, web = asyncio.run(main())
    assert vision == "saw:https://example.com/i.png"
    assert web == "extracted:['https://example.com/a']"


def test_disabled_gate_still_raises_for_async_tools(monkeypatch):
    monkeypatch.setattr(server, "require_imports", lambda: None)
    monkeypatch.delenv(server.ENABLE_VISION_ENV, raising=False)

    async def main():
        return await server.hermes_vision_analyze(image_url="https://example.com/x.png")

    with pytest.raises(RuntimeError, match=server.ENABLE_VISION_ENV):
        asyncio.run(main())
