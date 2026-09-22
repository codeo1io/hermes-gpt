"""Keep Hermes' transport defaults consistent across MCP Python SDK 1 and 2.

SDK 2 renamed FastMCP and moved transport options from the constructor to
the ASGI factories. Keep that adaptation here; tools use SDK types directly.
"""

from typing import Any

try:
    from mcp.server import MCPServer as _Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as _Server

    SDK_V2 = False
else:
    SDK_V2 = True


def _offload_sync_tool(fn: Any) -> Any:
    """Wrap a sync tool handler in an async coroutine that runs it in a thread.

    SDK 2 already offloads sync tools via ``anyio.to_thread.run_sync``; SDK
    1 executes them directly on the event loop. ``HermesMCP.add_tool`` only
    applies this wrapper on SDK 1, so both majors end up with the same
    execution semantics (sync bodies never block or nest ``asyncio.run``
    on the loop). ``functools.wraps`` keeps name/doc/signature intact for
    schema generation.
    """
    import functools
    import inspect

    if inspect.iscoroutinefunction(fn):
        return fn

    @functools.wraps(fn)
    async def _offloaded(**call_kwargs: Any) -> Any:
        import anyio

        return await anyio.to_thread.run_sync(lambda: fn(**call_kwargs))

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

    if not SDK_V2:

        def add_tool(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
            """Register a tool, offloading sync handlers to a worker thread.

            SDK 1 executes sync tools on the event loop (its FastMCP calls
            ``fn(**kwargs)`` inline), so any long-blocking sync tool — e.g.
            ``hermes_bot_chat_send`` with its 900s session timeout — froze
            the entire server, and sync bodies calling ``asyncio.run()``
            raised ``RuntimeError``. Wrapping sync handlers into offloading
            coroutines reproduces SDK 2 semantics. No-op passthrough on
            SDK 2, which already offloads.
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
