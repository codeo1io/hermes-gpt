"""Focused tests for the live-stream registry used by bounded shutdown (rm-105)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import live_streams  # noqa: E402


def test_register_current_outside_loop_returns_none():
    assert live_streams.register_current() is None
    assert live_streams.active_count() == 0
    live_streams.deregister(None)  # must be a no-op


def test_drain_cancels_registered_tasks_and_reports_counts():
    async def scenario():
        cancelled_seen = []

        async def plain():
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                cancelled_seen.append("plain")
                raise

        async def stubborn():
            # Swallow the first cancellation, then finish: drains must still
            # be able to count it as cancelled via task.cancelled().
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                await asyncio.sleep(0)
                return

        plain_task = asyncio.create_task(plain())
        stubborn_task = asyncio.create_task(stubborn())
        await asyncio.sleep(0)  # let both tasks start
        live_streams.register(plain_task)
        live_streams.register(stubborn_task)
        assert live_streams.active_count() == 2

        stats = await live_streams.drain(timeout_s=1.0)
        assert stats["cancelled"] >= 2, stats
        assert stats["uncancelled"] == 0, stats
        assert cancelled_seen == ["plain"]
        assert live_streams.active_count() == 0

    asyncio.run(scenario())


def test_drain_counts_uncancelled_tasks_after_timeout():
    async def scenario():
        stop = asyncio.Event()

        async def hang_forever():
            # Genuinely refuses to stop until told: swallows cancellation.
            while not stop.is_set():
                try:
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    continue

        task = asyncio.create_task(hang_forever())
        await asyncio.sleep(0)
        live_streams.register(task)
        stats = await live_streams.drain(timeout_s=0.2)
        assert stats["uncancelled"] == 1, stats
        # Drain hands stubborn tasks to the shutdown backstop and stops
        # tracking them: the task is still running but the registry is empty,
        # so a next drain is a no-op.
        assert live_streams.active_count() == 0
        # Deterministic teardown: release the loop, then let the cancel exit it.
        stop.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(scenario())


def test_deregister_unknown_task_is_safe():
    async def scenario():
        task = asyncio.create_task(asyncio.sleep(0.01))
        live_streams.deregister(task)  # never registered
        await task

    asyncio.run(scenario())
