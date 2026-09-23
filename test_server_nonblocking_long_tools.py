import asyncio
import time

import server


def test_owner_run_command_does_not_block_event_loop(monkeypatch):
    def blocking_owner(**kwargs):
        time.sleep(0.2)
        return "done"

    monkeypatch.setattr(server.op_workspace, "hermes_owner_run_command", blocking_owner)

    async def scenario():
        task = asyncio.create_task(
            server.hermes_owner_run_command("noop", timeout=1, workdir=None, dry_run=True)
        )
        await asyncio.sleep(0)
        started = time.perf_counter()
        await asyncio.sleep(0.02)
        elapsed = time.perf_counter() - started
        assert elapsed < 0.1
        assert not task.done()
        assert await task == "done"

    asyncio.run(scenario())


def test_job_wait_does_not_block_event_loop(monkeypatch):
    def blocking_wait(*args, **kwargs):
        time.sleep(0.2)
        return "done"

    monkeypatch.setattr(server.op_jobs, "hermes_job_wait", blocking_wait)

    async def scenario():
        task = asyncio.create_task(server.hermes_job_wait("job-1", wait_seconds=1))
        await asyncio.sleep(0)
        started = time.perf_counter()
        await asyncio.sleep(0.02)
        elapsed = time.perf_counter() - started
        assert elapsed < 0.1
        assert not task.done()
        assert await task == "done"

    asyncio.run(scenario())
