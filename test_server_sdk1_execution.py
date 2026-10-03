"""SDK execution-semantics regression tests (run e29c25913c00, batch B1).

Covers the two proven SDK-1 hazards from the 2026-09-23 adversarial
assessment:

1. ``hermes_web_extract`` / ``hermes_vision_analyze`` called
   ``asyncio.run()`` inside *sync* tool bodies — a 100% ``RuntimeError``
   under MCP SDK 1, which executes sync tools directly on the event loop
   (its FastMCP does ``return fn(**kwargs)`` with no offload).
2. Long-blocking sync tools froze the whole server on SDK 1 for their
   full duration (``hermes_bot_chat_send`` waits up to 900s).

The fixes: the two tools became async bodies that ``await`` their helpers,
and ``mcp_compat.HermesMCP.add_tool`` wraps sync handlers in an offloading
coroutine on BOTH SDK majors (2026-10-03 review fix, run 041a92f6667d):
SDK 1 needs it to run sync bodies off the loop at all, and SDK 2 needs it
so sync bodies run through the explicit ``HERMES_GPT_TOOL_THREAD_LIMIT``
limiter instead of anyio's implicit one.
"""

from __future__ import annotations

import asyncio
import inspect
import threading
import time
from types import SimpleNamespace

import pytest

import mcp_compat
import server


def test_offload_wrapper_runs_sync_body_in_worker_thread():
    seen = {}

    def slow_sync(x: int) -> str:
        seen["thread"] = threading.get_ident()
        time.sleep(0.15)
        return f"done-{x}"

    wrapped = mcp_compat._offload_sync_tool(slow_sync)
    assert inspect.iscoroutinefunction(wrapped)
    # functools.wraps preserves the schema source: signature follows
    # __wrapped__ back to the original sync function.
    assert inspect.signature(wrapped).parameters == inspect.signature(slow_sync).parameters
    # Async callables pass through unwrapped.
    async def already_async() -> str:
        return "ok"

    assert mcp_compat._offload_sync_tool(already_async) is already_async

    async def drive():
        return await wrapped(x=7)

    assert asyncio.run(drive()) == "done-7"
    assert seen["thread"] != threading.get_ident()


def test_offload_wrapper_keeps_event_loop_responsive():
    """rm-037 hazard: a 0.5s sync tool must not stall the loop it runs on."""
    import threading as _threading

    def slow_sync() -> str:
        time.sleep(0.5)
        return "done"

    wrapped = mcp_compat._offload_sync_tool(slow_sync)
    ticks: list[float] = []

    async def ticker() -> None:
        for _ in range(10):
            ticks.append(time.monotonic())
            await asyncio.sleep(0.05)

    async def main() -> None:
        await asyncio.gather(wrapped(), ticker())

    asyncio.run(main())
    assert len(ticks) == 10
    gaps = [b - a for a, b in zip(ticks, ticks[1:])]
    # With the offload, every gap stays at the ~0.05s sleep; without it the
    # 0.5s sync body would freeze the loop and gap out at >= 0.5s.
    assert max(gaps) < 0.25
    del _threading


def test_hermesmcp_add_tool_wrapper_exists_on_both_sdk_majors():
    """The wrapper must exist on BOTH SDK majors (2026-10-03 review fix,
    run 041a92f6667d): SDK 1 runs sync tools on the event loop, and SDK 2's
    native offload uses anyio's implicit limiter that
    ``HERMES_GPT_TOOL_THREAD_LIMIT`` cannot reach — the explicit limiter
    must govern the default lane too, not just the SDK-1 lane."""
    # Registered on the running major regardless of version...
    assert "add_tool" in vars(mcp_compat.HermesMCP)
    # ...and it actually wraps sync handlers into offloading coroutines.
    server_instance = mcp_compat.HermesMCP("wrapper-probe", version="0-test")

    def sync_probe(x: int) -> int:
        return x * 2

    server_instance.add_tool(sync_probe, name="sync_probe")
    registered = server_instance._tool_manager._tools["sync_probe"].fn
    assert inspect.iscoroutinefunction(registered)
    assert registered is not sync_probe

    async def async_probe(y: int) -> int:
        return y + 1

    server_instance.add_tool(async_probe, name="async_probe")
    passthrough = server_instance._tool_manager._tools["async_probe"].fn
    assert passthrough is async_probe


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
