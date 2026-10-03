"""Keep Hermes' transport defaults consistent across MCP Python SDK 1 and 2.

SDK 2 renamed FastMCP and moved transport options from the constructor to
the ASGI factories. Keep that adaptation here; tools use SDK types directly.

Sync tool bodies run on worker threads on both SDK majors (both via
``HermesMCP.add_tool``'s ``_offload_sync_tool`` wrapper). Thread capacity is bounded
by an explicit
``anyio.CapacityLimiter`` sized from ``HERMES_GPT_TOOL_THREAD_LIMIT``
(default 40, matching anyio's own default): without an explicit limiter,
``anyio.to_thread.run_sync`` silently shares one process-wide 40-thread pool,
so a burst of long ``hermes_codex_plan`` / ``hermes_bot_chat_send`` calls
(bounded by ``DEFAULT_SESSION_TIMEOUT`` = 900s) head-of-line blocks every
queued sync tool — cheap read-only ones included. Sustained saturation is
surfaced as a rate-limited warning so operators can retune the knob.
``HermesMCP.add_tool`` applies the wrapper on both SDK majors, so the
knob governs the default SDK-2 lane as well as the SDK-1 lane (SDK 2's
native offload would otherwise run sync bodies through anyio's implicit
limiter, which the knob cannot reach).
"""

import logging
import os
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

#: anyio's ``to_thread`` default pool size; kept as the default so the
#: explicit limiter changes nothing until ``HERMES_GPT_TOOL_THREAD_LIMIT``
#: is set.
_DEFAULT_TOOL_THREAD_LIMIT = 40

#: Minimum seconds between repeated offload-saturation warnings.
_SATURATION_WARN_INTERVAL = 60.0

_tool_thread_limit: int | None = None
_tool_limiter: Any = None
_last_saturation_warning = 0.0
#: Guards lazy limiter construction: two concurrent first calls could
#: otherwise each build a ``CapacityLimiter`` (one orphaned), transiently
#: doubling the effective token budget.
_limiter_lock = threading.Lock()


def _resolve_tool_thread_limit() -> int:
    """Parse ``HERMES_GPT_TOOL_THREAD_LIMIT`` (default 40; malformed falls back)."""
    raw = os.environ.get("HERMES_GPT_TOOL_THREAD_LIMIT", "").strip()
    if not raw:
        return _DEFAULT_TOOL_THREAD_LIMIT
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_TOOL_THREAD_LIMIT


def _tool_thread_limiter() -> Any:
    """Return the process-wide limiter for sync tool offload threads.

    Built lazily (not at import time) so importing this shim never touches
event-loop machinery, and under a lock so a burst of concurrent first
calls cannot construct two limiters (one orphaned) and transiently
double the effective token budget. One per-process limiter matches the
single-loop,
single-process server model; transient test loops never queue because
acquisition only waits when the limit is actually reached. Read once per
process — changing the env var requires a server restart (documented).
    """
    global _tool_thread_limit, _tool_limiter
    if _tool_limiter is None:
        with _limiter_lock:
            if _tool_limiter is None:
                import anyio

                _tool_thread_limit = _resolve_tool_thread_limit()
                _tool_limiter = anyio.CapacityLimiter(_tool_thread_limit)
    return _tool_limiter


def _warn_if_saturated(limiter: Any) -> None:
    """Emit a rate-limited warning when every offload token is in flight."""
    global _last_saturation_warning
    try:
        stats = limiter.statistics()
        in_flight = stats.borrowed_tokens + stats.tasks_waiting
        total = limiter.total_tokens
    except Exception:  # pragma: no cover - defensive: never break a tool call
        return
    if in_flight < total:
        return
    now = time.monotonic()
    if now - _last_saturation_warning < _SATURATION_WARN_INTERVAL:
        return
    _last_saturation_warning = now
    logger.warning(
        "sync tool offload pool saturated (%d in flight / %d tokens); "
        "further sync tools queue behind it — raise HERMES_GPT_TOOL_THREAD_LIMIT "
        "(currently %d) if this recurs",
        in_flight,
        total,
        total,
    )

try:
    from mcp.server import MCPServer as _Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as _Server

    SDK_V2 = False
else:
    SDK_V2 = True


def _offload_sync_tool(fn: Any) -> Any:
    """Wrap a sync tool handler in an async coroutine that runs it in a thread.

    SDK 1 executes sync tools directly on the event loop; SDK 2 offloads
    them itself, but through anyio's implicit process-wide 40-token
    limiter, which ``HERMES_GPT_TOOL_THREAD_LIMIT`` cannot size.
    ``HermesMCP.add_tool`` applies this wrapper on BOTH majors, so every
    sync body runs through the explicit limiter (sync bodies never block
    or nest ``asyncio.run`` on the loop, and the knob plus saturation
    warning govern both lanes). ``functools.wraps`` keeps
    name/doc/signature intact for schema generation.
    """
    import functools
    import inspect

    if inspect.iscoroutinefunction(fn):
        return fn

    @functools.wraps(fn)
    async def _offloaded(**call_kwargs: Any) -> Any:
        import anyio

        limiter = _tool_thread_limiter()
        _warn_if_saturated(limiter)
        return await anyio.to_thread.run_sync(
            lambda: fn(**call_kwargs), limiter=limiter
        )

    return _offloaded


class HermesMCP(_Server):
    """A server with explicit, version-independent transport configuration."""

    def __init__(
        self, name: str, *, version: str, host: str = "127.0.0.1",
        port: int = 7677, streamable_http_path: str = "/mcp",
        sse_path: str = "/sse", message_path: str = "/messages/",
        stateless_http: bool = False, json_response: bool = False,
        transport_security: Any = None, **extra: Any,
    ) -> None:
        # ``extra`` forwards any SDK constructor option Hermes does not
        # translate (instructions, auth, token_verifier, lifespan, ...).
        self._hermes_http_options = {
            "host": host, "streamable_http_path": streamable_http_path,
            "stateless_http": stateless_http, "json_response": json_response,
            "transport_security": transport_security,
        }
        self._hermes_sse_options = {
            "host": host, "sse_path": sse_path, "message_path": message_path,
            "transport_security": transport_security,
        }
        if SDK_V2:
            super().__init__(name, version=version, **extra)
        else:
            super().__init__(
                name, port=port, sse_path=sse_path, message_path=message_path,
                **self._hermes_http_options, **extra,
            )
            # SDK 1 has no public app-version constructor parameter.
            self._mcp_server.version = version

    def add_tool(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Register a tool, offloading sync handlers to a worker thread.

        Both SDK majors need the wrapper. SDK 1 executes sync tools on
        the event loop (its FastMCP calls ``fn(**kwargs)`` inline), so any
        long-blocking sync tool — e.g. ``hermes_bot_chat_send`` with its
        900s session timeout — froze the entire server, and sync bodies
        calling ``asyncio.run()`` raised ``RuntimeError``. SDK 2 offloads
        sync tools itself, but through anyio's implicit 40-token limiter
        that ``HERMES_GPT_TOOL_THREAD_LIMIT`` cannot reach. Wrapping sync
        handlers into offloading coroutines on BOTH majors routes every
        sync body through the explicit limiter, so the knob and the
        saturation warning govern the default SDK-2 lane exactly as they
        govern the SDK-1 lane.
        """
        return super().add_tool(_offload_sync_tool(fn), *args, **kwargs)

    def streamable_http_app(self, **kwargs: Any) -> Any:
        if SDK_V2:
            return super().streamable_http_app(**{**self._hermes_http_options, **kwargs})
        return super().streamable_http_app(**kwargs)

    def sse_app(self, *args: Any, **kwargs: Any) -> Any:
        if SDK_V2:
            return super().sse_app(*args, **{**self._hermes_sse_options, **kwargs})
        return super().sse_app(*args, **kwargs)
