"""Registry of in-flight streaming responses (SSE + WebSocket) for bounded shutdown.

rm-105: the chat SSE generators and the operator live-events WebSocket loop
only end when their stream ends, so a graceful shutdown used to wait on them
until the process was killed. Streaming handlers register their asyncio task
here (``register``/``deregister``) so the ASGI lifespan shutdown hook in
``server.build_asgi_app`` can cancel them promptly via ``drain``.

The registry is only touched from the event loop that owns the tasks; it is
not thread-safe by design (handlers and the lifespan hook share one loop).
"""

from __future__ import annotations

import asyncio

_tasks: set[asyncio.Task] = set()


def register(task: asyncio.Task) -> None:
    """Track a live streaming task so shutdown can cancel it (rm-105)."""
    _tasks.add(task)


def register_current() -> asyncio.Task | None:
    """Track the calling coroutine's task; returns it for ``deregister``.

    Async generators (SSE) are not tasks themselves, but they always run
    inside one; registering that task lets shutdown cancel the stream.
    Returns ``None`` when no task is running (defensive; never expected).
    """
    task = None
    try:
        task = asyncio.current_task()
    except RuntimeError:
        # No running loop (defensive): nothing to register.
        return None
    if task is not None:
        _tasks.add(task)
    return task


def deregister(task: asyncio.Task | None) -> None:
    """Stop tracking a streaming task that has ended on its own."""
    if task is not None:
        _tasks.discard(task)


def active_count() -> int:
    """Number of live (not yet done) registered streaming tasks."""
    return sum(1 for task in _tasks if not task.done())


async def drain(timeout_s: float = 5.0) -> dict[str, float]:
    """Cancel every live streaming task and wait up to ``timeout_s``.

    A task that swallows ``CancelledError`` is reported under ``uncancelled``
    and handed off to the server's ``timeout_graceful_shutdown`` backstop:
    drained tasks are discarded from the registry either way, so a second
    drain is a clean no-op rather than a retry loop.
    """
    pending = [task for task in _tasks if not task.done()]
    for task in pending:
        _tasks.discard(task)
    if not pending:
        return {"cancelled": 0, "uncancelled": 0, "timeout_s": timeout_s}
    for task in pending:
        task.cancel()
    done, still_pending = await asyncio.wait(pending, timeout=timeout_s)
    return {
        "cancelled": float(len(done)),
        "uncancelled": float(len(still_pending)),
        "timeout_s": timeout_s,
    }
