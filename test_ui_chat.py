"""Backend tests for the chat bridge (ui_chat.py) — no live model.

The agent turn is stubbed: ``ui_chat._build_agent`` is replaced with a stub
agent that drives the real stream callbacks (``_make_stream_callbacks``), so
the SSE event encoding, lease handling, stop plumbing, replay buffer, and
persistence are all exercised end-to-end without any LLM call.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

# The chat UI resolves ``hermes_state`` lazily (ui_chat._session_db). The repo
# ships a SessionDB-compatible shim (hermes_state.py) for environments without
# a Hermes Agent checkout (CI, packaged installs) — the same resolution order
# applies here, with the repo dir on sys.path below. Do NOT insert the real
# agent source root at collection time: it makes ``hermes_cli`` importable in
# the pytest process and lets fleet tests read the invoking machine's real
# Hermes config (audit t_9d200636 Class A).

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ui_chat  # noqa: E402

#: Inter-thread coordination budget for this module's concurrency tests.
# These ``Event.wait``/``Thread.join`` timeouts are deadlock detectors, not
# wall-clock contracts: the assertion behind each call cares that coordination
# COMPLETES, never that it completes within a fixed few seconds. The shared
# validation runner is routinely saturated (load average 30-50 while concurrent
# full-suite fleets run), where 2-15 s budgets produce load-timing false
# positives (ROADMAP.md, "Cycle 1 learnings", rules 9 and 13). Healthy runs are
# not slowed at all -- wait/join return the moment coordination completes; a
# real deadlock still fails, at the widened deadline. Override with
# HERMES_TEST_THREAD_BUDGET when debugging a genuine hang.
_THREAD_BUDGET = float(os.environ.get("HERMES_TEST_THREAD_BUDGET", "30"))


# ── Test doubles ──────────────────────────────────────────────────────────

class StubAgent:
    """Minimal AIAgent double that emits events through the real callbacks.

    ``block_event`` (optional) makes the stub block inside ``run_conversation``
    until the event is set or the agent is interrupted — used to keep a turn
    alive while the test asserts lease conflicts and stop behavior.
    """

    def __init__(self, callbacks, *, db, session_id, block_event=None):
        self._callbacks = callbacks
        self.db = db
        self.session_id = session_id
        self.interrupted = threading.Event()
        self.block_event = block_event

    def interrupt(self, message=None, *, hard_cancel=False):
        self.interrupted.set()

    def run_conversation(self, user_message, task_id=None, **kwargs):
        on_token, on_reasoning, on_tool_start, on_tool_complete = self._callbacks
        self.db.append_message(self.session_id, "user", content=user_message)
        if self.block_event is not None:
            while not self.interrupted.is_set() and not self.block_event.is_set():
                self.block_event.wait(0.1)
            if self.interrupted.is_set():
                return {"interrupted": True, "failed": False, "final_response": ""}
        on_tool_start("call_1", "hermes_search_files", {"pattern": "test", "path": "."})
        time.sleep(0.01)
        on_tool_complete("call_1", "hermes_search_files", {}, "3 matches")
        self.db.append_message(
            self.session_id, "assistant",
            content="Hello world",
            tool_calls=[{"id": "call_1", "type": "function", "function": {"name": "hermes_search_files", "arguments": "{}"}}],
            finish_reason="end_turn",
        )
        for chunk in ("Hello ", "world"):
            if self.interrupted.is_set():
                return {"interrupted": True, "failed": False, "final_response": "Hello "}
            on_token(chunk)
            time.sleep(0.01)
        return {"interrupted": False, "failed": False, "final_response": "Hello world"}


def install_stub_agent(monkeypatch, **agent_kwargs):
    captured = {}

    def _stub_build_agent(*, turn, db, model, profile):
        callbacks = ui_chat._make_stream_callbacks(turn)
        agent = StubAgent(callbacks, db=db, session_id=turn.session_id, **agent_kwargs)
        captured["agent"] = agent
        return agent

    monkeypatch.setattr(ui_chat, "_build_agent", _stub_build_agent)
    return captured


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_ui_env(monkeypatch, tmp_path):
    """Point HERMES_HOME at a temp dir and reset module state per test."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv(ui_chat.UI_PROFILE_ENV, raising=False)
    monkeypatch.delenv(ui_chat.UI_TOOL_PREVIEW_BYTES_ENV, raising=False)
    monkeypatch.delenv(ui_chat.UI_MAX_CONCURRENT_ENV, raising=False)
    ui_chat._session_db_instance = None
    with ui_chat._turns_lock:
        ui_chat._turns.clear()
    yield
    with ui_chat._turns_lock:
        ui_chat._turns.clear()
    ui_chat._session_db_instance = None


@pytest.fixture()
def app():
    return Starlette(routes=ui_chat.ui_chat_routes())


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


def _wait_for_turn(session_id: str, timeout: float = _THREAD_BUDGET) -> None:
    """Poll the turn registry until the handler registered the turn."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with ui_chat._turns_lock:
            if session_id in ui_chat._turns:
                return
        time.sleep(0.05)
    raise AssertionError(f"turn for {session_id} never started")


def _parse_sse(text: str):
    """Parse SSE text into [(event, seq, data_dict), ...]."""
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event = seq = None
        data_lines = []
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("id: "):
                seq = int(line[len("id: "):])
            elif line.startswith("data: "):
                data_lines.append(line[len("data: "):])
            elif line.startswith(": ping"):
                continue
        if event is not None:
            import json as _json

            events.append((event, seq, _json.loads("".join(data_lines))))
    return events


def _create_session_via_api(client) -> str:
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    return body["data"]["session_id"]


# ── Sessions ──────────────────────────────────────────────────────────────

def test_session_create_and_list(client):
    sid = _create_session_via_api(client)
    assert sid

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    sessions = resp.json()["data"]["sessions"]
    assert any(s["session_id"] == sid for s in sessions)
    found = next(s for s in sessions if s["session_id"] == sid)
    assert found["profile"] == "default"
    assert found["message_count"] == 0


def test_session_messages_resume(client):
    db = ui_chat._session_db()
    sid = "deadbeefsession1"
    db.create_session(sid, "webui", model="test-model", profile_name=None)
    db.append_message(sid, "user", content="hello")
    db.append_message(sid, "assistant", content="hi there", finish_reason="end_turn")

    resp = client.get(f"/api/sessions/{sid}/messages")
    assert resp.status_code == 200
    messages = resp.json()["data"]["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["content"] == "hi there"
    assert messages[1]["finish_reason"] == "end_turn"
    assert messages[1]["interrupted"] is False


def test_session_messages_unknown_404(client):
    resp = client.get("/api/sessions/doesnotexist/messages")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_tool_rows_are_truncated_and_redacted(client, monkeypatch):
    monkeypatch.setenv(ui_chat.UI_TOOL_PREVIEW_BYTES_ENV, "64")
    db = ui_chat._session_db()
    sid = "tool-session-1"
    db.create_session(sid, "webui")
    # Key material ≥20 payload chars: the threshold the canonical redactor
    # (operator_policy.redact_output via ui_security) is pinned to.
    long_result = "sk-abcdef0123456789abcdef01 " + "x" * 500
    db.append_message(sid, "assistant", content="using tools", tool_calls='[{"id": "c1", "function": {"name": "read_file", "arguments": "{}"}}]')
    db.append_message(sid, "tool", content=long_result, tool_call_id="c1", tool_name="read_file")

    resp = client.get(f"/api/sessions/{sid}/messages")
    messages = resp.json()["data"]["messages"]
    tool_msg = next(m for m in messages if m["role"] == "tool")
    assert "sk-" not in tool_msg["tool_result"]
    assert "[REDACTED_OPENAI_KEY]" in tool_msg["tool_result"]
    assert len(tool_msg["tool_result"]) <= 64 + len("\n…[truncated]")


# ── Chat streaming ────────────────────────────────────────────────────────

# ── A2: redaction boundary on the SSE path ───────────────────────────

def _turn_with_callbacks():
    turn = ui_chat.Turn(session_id="redact-s", turn_id="t-redact", holder="h")
    return turn, ui_chat._make_stream_callbacks(turn)


def _token_text(turn):
    return "".join(e[2].get("delta", "") for e in turn.events if e[1] == "token")


def test_sse_token_secret_redacted():
    turn, (on_token, _on_reasoning, _ts, _tc) = _turn_with_callbacks()
    on_token("key sk-abcdef0123456789abcdef01 now")
    turn.flush_deltas()
    assert "sk-abcdef" not in _token_text(turn)
    assert "[REDACTED_OPENAI_KEY]" in _token_text(turn)


def test_sse_secret_split_across_deltas_does_not_reassemble():
    """D9: a secret split across consecutive token deltas must never
    reassemble in the browser (redaction regexes need the whole run in one
    string, so the bridge holds back a straddle-safe tail)."""
    secret = "AKIA" + "BCDEFGHIJKLMNOP"  # 20-char AWS-style key
    turn, (on_token, _on_reasoning, _ts, _tc) = _turn_with_callbacks()
    # Fill the buffer past the hold-back window, then stream the secret one
    # character per delta, then keep streaming past it so the hold-back
    # window advances across the secret boundary.
    on_token("a" * 300)
    for ch in secret:
        on_token(ch)
    on_token("b" * 300)
    turn.flush_deltas()
    text = _token_text(turn)
    assert "AKIA" not in text
    assert "AKIA" not in json.dumps([e[2] for e in turn.events])
    assert "[REDACTED_AWS_KEY]" in text


def test_sse_reasoning_channel_redacts_too():
    turn, (_on_token, on_reasoning, _ts, _tc) = _turn_with_callbacks()
    on_reasoning("thinking about Bearer abcdefghijklmnopqrstuvwxyz123456 done")
    turn.flush_deltas()
    text = "".join(e[2].get("delta", "") for e in turn.events if e[1] == "reasoning")
    assert "abcdefghijklmnopqrstuvwxyz123456" not in text
    assert "Bearer [REDACTED]" in text


def test_sse_content_mode_preserves_conversation_text():
    """token/reasoning deltas are the user's own conversation: PII and paths
    survive (content mode); only secret shapes are removed."""
    turn, (on_token, _on_reasoning, _ts, _tc) = _turn_with_callbacks()
    on_token("read /home/tony/.hermes/notes.md — mail tony@example.com — ok")
    turn.flush_deltas()
    text = _token_text(turn)
    assert "/home/tony/.hermes/notes.md" in text
    assert "tony@example.com" in text


def test_publish_chokepoint_redacts_tool_and_error_events():
    """Every SSE data line goes through ui_security at Turn.publish — tool
    summaries, error messages, and secret-keyed values cannot skip it."""
    turn, _ = _turn_with_callbacks()
    turn.publish("tool_end", {"call_id": "c1", "name": "t", "status": "ok",
                              "summary": "AKIA" + "BCDEFGHIJKLMNOP"})
    turn.publish("error", {"code": "INTERNAL", "message": "auth failed Bearer abcdefghijklmnopqrstuvwxyz123456"})
    turn.publish("meta", {"session_id": "s", "password": "hunter2hunter2"})
    blob = json.dumps([e[2] for e in turn.events])
    assert "AKIA" not in blob
    assert "abcdefghijklmnopqrstuvwxyz123456" not in blob
    assert "hunter2hunter2" not in blob


def test_chat_stream_full_sequence(client, monkeypatch):
    install_stub_agent(monkeypatch)
    with client.stream("POST", "/api/chat", json={"message": "hello"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        text = "".join(resp.iter_text())

    events = _parse_sse(text)
    event_names = [e[0] for e in events]
    assert event_names[0] == "meta"
    assert "token" in event_names
    assert "tool_start" in event_names
    assert "tool_end" in event_names
    assert "message_complete" in event_names
    assert event_names[-1] == "done"

    meta = events[0][2]
    assert meta["session_id"]
    assert meta["turn_id"].startswith("t-")
    done = events[-1][2]
    assert done["finish_reason"] == "end_turn"
    assert done["message_id"] is not None

    # turn persisted: thread re-read shows user + assistant rows
    sid = meta["session_id"]
    resp = client.get(f"/api/sessions/{sid}/messages")
    roles = [m["role"] for m in resp.json()["data"]["messages"]]
    assert "user" in roles and "assistant" in roles

    # ids are monotonically increasing for replay
    seqs = [e[1] for e in events]
    assert seqs == sorted(seqs)
    assert seqs[0] == 1


def test_chat_creates_lazy_session(client, monkeypatch):
    install_stub_agent(monkeypatch)
    with client.stream("POST", "/api/chat", json={"message": "hi"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
    events = _parse_sse(text)
    assert events[0][0] == "meta"
    sid = events[0][2]["session_id"]
    resp = client.get("/api/sessions")
    assert any(s["session_id"] == sid for s in resp.json()["data"]["sessions"])


def test_chat_unknown_session_404(client, monkeypatch):
    install_stub_agent(monkeypatch)
    resp = client.post("/api/chat", json={"session_id": "nope", "message": "hi"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_chat_busy_session_returns_409(client, app, monkeypatch):
    # TestClient buffers the whole streaming body inside ``__enter__``, so the
    # first (never-ending) stream runs in a background thread while the main
    # thread asserts the lease conflict.
    hold = threading.Event()
    install_stub_agent(monkeypatch, block_event=hold)
    sid = _create_session_via_api(client)
    result: dict = {}

    def _stream():
        with client.stream("POST", "/api/chat", json={"session_id": sid, "message": "first"}) as resp:
            result["status"] = resp.status_code
            result["text"] = "".join(resp.iter_text())

    stream_thread = threading.Thread(target=_stream, daemon=True)
    stream_thread.start()
    try:
        _wait_for_turn(sid)
        # the stub is blocked, so the lease is still held — second send → 409
        resp = client.post("/api/chat", json={"session_id": sid, "message": "second"})
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "TURN_IN_PROGRESS"
    finally:
        hold.set()
        stream_thread.join(timeout=_THREAD_BUDGET)
    assert result.get("status") == 200
    assert not stream_thread.is_alive()


def test_chat_stop_interrupts_turn(client, monkeypatch):
    hold = threading.Event()
    install_stub_agent(monkeypatch, block_event=hold)
    sid = _create_session_via_api(client)
    result: dict = {}

    def _stream():
        with client.stream("POST", "/api/chat", json={"session_id": sid, "message": "go"}) as resp:
            result["status"] = resp.status_code
            result["text"] = "".join(resp.iter_text())

    stream_thread = threading.Thread(target=_stream, daemon=True)
    stream_thread.start()
    try:
        _wait_for_turn(sid)
        # let the stub reach its block loop, then interrupt
        time.sleep(0.2)
        resp = client.post("/api/chat/stop", json={"session_id": sid})
        assert resp.status_code == 200
        assert resp.json()["data"]["stopped"] is True
    finally:
        hold.set()
        stream_thread.join(timeout=_THREAD_BUDGET)
    assert result.get("status") == 200
    events = _parse_sse(result.get("text", ""))
    assert events[-1][0] == "done"
    assert events[-1][2]["finish_reason"] == "interrupted"


def test_reconnect_replays_buffer(client, monkeypatch):
    install_stub_agent(monkeypatch)
    with client.stream("POST", "/api/chat", json={"message": "replay me"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
    events = _parse_sse(text)
    meta = events[0][2]
    sid, turn_id = meta["session_id"], meta["turn_id"]

    # Reconnect: replay from after=0 → the same buffered events come back.
    resp = client.get(f"/api/chat/stream?session_id={sid}&turn_id={turn_id}&after=0")
    assert resp.status_code == 200
    replay = _parse_sse(resp.text)
    assert [e[1] for e in replay] == [e[1] for e in events]

    # Replay after the final seq → no events (turn already done).
    resp = client.get(f"/api/chat/stream?session_id={sid}&turn_id={turn_id}&after={events[-1][1]}")
    assert resp.status_code == 200
    assert _parse_sse(resp.text) == []


def test_reconnect_unknown_turn_404(client):
    resp = client.get("/api/chat/stream?session_id=abc&turn_id=t-xyz&after=0")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "TURN_NOT_FOUND"


def test_stop_unknown_session_noop(client):
    resp = client.post("/api/chat/stop", json={"session_id": "nonexistent"})
    assert resp.status_code == 200
    assert resp.json()["data"]["stopped"] is False


# ── Redaction / boundaries ────────────────────────────────────────────────

def test_tool_brief_masks_prompt_content():
    brief = ui_chat._safe_tool_brief(
        "hermes_search_files",
        {"pattern": "needle", "prompt": "find my secret plan", "path": "/tmp"},
    )
    assert "find my secret plan" not in brief
    assert "prompt=…" in brief
    assert '"needle"' in brief
    assert '"/tmp"' in brief


def test_redact_text_masks_credentials():
    # Secret shapes and thresholds come from operator_policy.redact_output
    # (single source) via ui_security.redact_browser — not a local list.
    key = "sk-abcdef0123456789abcdef01"  # ≥20 payload chars: canonical threshold
    assert key not in ui_chat._redact_text(f"key {key} here")
    assert "[REDACTED_OPENAI_KEY]" in ui_chat._redact_text(f"key {key} here")
    assert ui_chat._redact_text("Bearer abcdefghijklmnopqrstuvwxyz123456") == "Bearer [REDACTED]"
    assert "/home/u/.hermes/secrets/token.json" not in ui_chat._redact_text("path /home/u/.hermes/secrets/token.json")


def test_error_envelope_shape():
    import json as _json

    resp = ui_chat._error(409, "TURN_IN_PROGRESS", "busy")
    assert resp.status_code == 409
    body = _json.loads(resp.body)
    assert body == {"ok": False, "error": {"code": "TURN_IN_PROGRESS", "message": "busy"}}



# ── B1/B7: canonical shapes on the streaming path; exactly-once redaction ──

def test_sse_canonical_secret_shapes_never_reassemble():
    """B1: every canonical shape is redacted on the token channel, whole AND
    when split one character per delta (the markers ghp_/xoxb-/AIza used to
    slip through both the hold-back buffer and the shape table)."""
    families = [
        ("ghp_" + "A" * 40, "[REDACTED_GITHUB_TOKEN]"),
        ("xoxb-" + "1234567890-ABCDEF", "[REDACTED_SLACK_TOKEN]"),
        ("AIza" + "a" * 35, "[REDACTED_GOOGLE_KEY]"),
        ("sk-ant-" + "b" * 30, "[REDACTED_ANTHROPIC_KEY]"),
        ("ASIA" + "D" * 16, "[REDACTED_AWS_KEY]"),
        (
            "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXkAAA\n-----END OPENSSH PRIVATE KEY-----",
            "[REDACTED_PRIVATE_KEY]",
        ),
    ]
    for secret, marker in families:
        # Whole in one delta.
        turn, (on_token, _on_reasoning, _ts, _tc) = _turn_with_callbacks()
        on_token(f"prefix {secret} suffix")
        turn.flush_deltas()
        assert secret not in json.dumps([e[2] for e in turn.events])
        assert marker in _token_text(turn), secret
        # Split one character per delta across the hold-back window.
        turn, (on_token, _on_reasoning, _ts, _tc) = _turn_with_callbacks()
        on_token("a" * 300)
        for ch in secret:
            on_token(ch)
        on_token("b" * 300)
        turn.flush_deltas()
        blob = json.dumps([e[2] for e in turn.events])
        assert secret not in blob, secret
        assert marker in blob, secret


def test_sse_delta_redacted_exactly_once():
    """B7: Turn.publish is the single redaction chokepoint — a streamed
    secret becomes its placeholder exactly once and the placeholder itself
    is never re-mangled by a second pass."""
    turn, (on_token, _on_reasoning, _ts, _tc) = _turn_with_callbacks()
    on_token("key sk-" + "e" * 30 + " done")
    on_token("more sk-" + "f" * 30 + " done")
    turn.flush_deltas()
    text = _token_text(turn)
    assert text.count("[REDACTED_OPENAI_KEY]") == 2
    assert "[REDACTED_[REDACTED" not in text
    # A pre-redacted placeholder passes through the chokepoint untouched.
    turn2 = ui_chat.Turn(session_id="p", turn_id="p-once", holder="h")
    turn2.publish("token", {"delta": "already [REDACTED_GITHUB_TOKEN] here"})
    assert json.dumps([e[2] for e in turn2.events]).count("[REDACTED_GITHUB_TOKEN]") == 1


async def _asgi_call(app, method, path, query=b""):
    """Minimal dependency-free ASGI client (the uv dev env has no httpx)."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": query,
        "headers": [(b"content-length", b"0")],
        "scheme": "http",
        "server": ("test", 80),
        "client": ("test", 1234),
    }
    status: dict[str, int] = {}
    body = bytearray()

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            status["code"] = message["status"]
        elif message["type"] == "http.response.body":
            body.extend(message.get("body", b""))

    await app(scope, receive, send)
    return status.get("code", 0), bytes(body)


def test_session_endpoints_do_not_stall_event_loop_under_sessiondb_lock(app):
    """rm-076 regression: blocking SessionDB work must run off the event loop.

    While another thread holds the shared SessionDB lock, a concurrent
    request that touches no database must still complete quickly. Before the
    asyncio.to_thread offload, POST /api/sessions ran create_session's sqlite
    work (and its lock acquisition) directly on the serving loop and froze
    every other request until the lock was released.
    """
    import asyncio

    db = ui_chat._session_db()
    lock_held = threading.Event()
    release = threading.Event()

    def hold_lock() -> None:
        with db._lock:
            lock_held.set()
            release.wait(_THREAD_BUDGET)

    async def scenario() -> None:
        holder = threading.Thread(target=hold_lock, daemon=True)
        holder.start()
        assert lock_held.wait(5.0)
        try:
            # POST /api/sessions blocks inside create_session until the
            # lock is released — post-fix inside an offloaded worker.
            create = asyncio.create_task(_asgi_call(app, "POST", "/api/sessions"))
            await asyncio.sleep(0.2)  # let the request reach the handler

            # DB-free probe: unknown session + turn -> 404 from the
            # in-memory replay buffer. On pre-fix code the loop is frozen
            # inside create_session and this wait_for times out.
            probe_status, _ = await asyncio.wait_for(
                _asgi_call(
                    app,
                    "GET",
                    "/api/chat/stream",
                    query=b"session_id=nope&turn_id=nope",
                ),
                timeout=5.0,
            )
            assert probe_status == 404

            release.set()
            create_status, create_body = await asyncio.wait_for(create, timeout=10.0)
            assert create_status == 200
            assert json.loads(create_body)["data"]["session_id"]
        finally:
            release.set()

    asyncio.run(scenario())


# ── rm-124/125/126/127/129: transcript window, order, reconnect, lifecycle ──

def _seed_messages(db, session_id: str, count: int, *, prefix: str = "m") -> None:
    for i in range(1, count + 1):
        db.append_message(session_id, "user", content=f"{prefix}-{i:04d}")


def _probe_holder() -> str:
    import uuid

    return f"probe-{uuid.uuid4().hex}"


def _drive(generator, timeout: float = _THREAD_BUDGET):
    """Drain an async SSE generator to a string (turn must be done)."""
    import asyncio

    async def _collect():
        chunks = []
        async for chunk in generator:
            chunks.append(chunk)
        return "".join(chunks)

    return asyncio.run(asyncio.wait_for(_collect(), timeout))


def test_session_messages_default_returns_newest_page(client):
    """rm-124 (assess F1): the no-params window must be the NEWEST page.

    Before the fix the handler read oldest-first, so in a 600-message session
    the endpoint served msg-001..msg-500 and the 100 most recent messages
    were unreachable through the API.
    """
    db = ui_chat._session_db()
    sid = "window-session-1"
    db.create_session(sid, "webui")
    _seed_messages(db, sid, 600)

    resp = client.get(f"/api/sessions/{sid}/messages")
    assert resp.status_code == 200
    body = resp.json()["data"]
    ids = [m["message_id"] for m in body["messages"]]
    assert len(ids) == ui_chat.MESSAGE_PAGE_LIMIT == 500
    assert ids == sorted(ids)          # oldest-first WITHIN the newest page
    assert ids[-1] == 600              # repro: the default window ends at the
    assert ids[0] == 101               # newest message, not the oldest rows
    assert body["messages"][0]["content"] == "m-0101"
    assert body["messages"][-1]["content"] == "m-0600"
    assert body["page"]["limit"] == 500
    assert body["page"]["oldest_id"] == 101
    assert body["page"]["has_older"] is True


def test_session_messages_resume_beyond_page_limit(client):
    """rm-124: the resume path extended past MESSAGE_PAGE_LIMIT — keyset
    paging backward from the default window reaches every message, gapless."""
    db = ui_chat._session_db()
    sid = "window-session-long"
    db.create_session(sid, "webui")
    total = ui_chat.MESSAGE_PAGE_LIMIT * 2 + 30
    _seed_messages(db, sid, total)

    seen: list[int] = []
    page_ids: list[list[int]] = []
    cursor = None
    pages = 0
    while True:
        url = f"/api/sessions/{sid}/messages"
        if cursor is not None:
            url += f"?before_id={cursor}"
        body = client.get(url).json()["data"]
        ids = [m["message_id"] for m in body["messages"]]
        assert ids == sorted(ids)
        assert len(ids) <= ui_chat.MESSAGE_PAGE_LIMIT
        seen.extend(ids)
        page_ids.append(ids)
        pages += 1
        if not body["page"]["has_older"]:
            assert ids[0] == 1
            break
        cursor = body["page"]["oldest_id"]
    assert pages == 3                       # 1030 messages / 500 per page
    assert sorted(seen) == list(range(1, total + 1))  # every message, once
    # pages walk newest-window → older-window, each rendered oldest-first
    bounds = [(ids[0], ids[-1]) for ids in page_ids]
    assert [b[1] for b in bounds] == sorted((b[1] for b in bounds), reverse=True)
    for newer, older in zip(bounds, bounds[1:]):
        assert newer[0] - 1 == older[1]    # adjacent windows: no gap, no overlap


def test_session_messages_after_id_returns_only_newer(client):
    """rm-124: ``after_id`` is the forward cursor (poll for new messages)."""
    db = ui_chat._session_db()
    sid = "window-session-forward"
    db.create_session(sid, "webui")
    _seed_messages(db, sid, 10, prefix="old")

    newest = client.get(f"/api/sessions/{sid}/messages").json()["data"]["messages"][-1]["message_id"]
    _seed_messages(db, sid, 3, prefix="new")

    body = client.get(f"/api/sessions/{sid}/messages?after_id={newest}").json()["data"]
    assert [m["content"] for m in body["messages"]] == ["new-0001", "new-0002", "new-0003"]
    assert body["page"]["has_older"] is True   # older rows exist behind the cursor

    empty = client.get(f"/api/sessions/{sid}/messages?after_id={newest + 3}").json()["data"]
    assert empty["messages"] == []
    assert empty["page"]["oldest_id"] is None
    assert empty["page"]["has_older"] is False


def test_session_messages_rejects_non_integer_cursor(client):
    """rm-124: a cursor that cannot be parsed is a 400, never a silently
    ignored param that hands the client the wrong page."""
    db = ui_chat._session_db()
    sid = "window-session-bad"
    db.create_session(sid, "webui")
    db.append_message(sid, "user", content="hello")
    for param in ("before_id", "after_id"):
        resp = client.get(f"/api/sessions/{sid}/messages?{param}=not-an-int")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "BAD_REQUEST"


def test_session_list_serializes_real_last_activity_at(client):
    """rm-125 (assess F2): ``last_active`` was a key that never existed, so
    every session serialized its creation time as its last activity."""
    db = ui_chat._session_db()
    sid = "lastact-session-1"
    db.create_session(sid, "webui", model="m")
    row = db.get_session(sid)
    assert row["last_activity_at"] == row["started_at"]
    time.sleep(0.01)
    db.append_message(sid, "user", content="hello")
    truth = db.get_session(sid)
    assert truth["last_activity_at"] > truth["started_at"]

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    found = next(s for s in resp.json()["data"]["sessions"] if s["session_id"] == sid)
    assert found["last_activity_at"] == truth["last_activity_at"]
    assert found["last_activity_at"] > found["created_at"]


def test_replay_without_overflow_emits_no_gap_event():
    turn = ui_chat.Turn(session_id="nogap-s", turn_id="t-nogap", holder="h")
    for i in range(5):
        turn.publish("token", {"delta": f"c{i}"})
    turn.mark_done("end_turn")

    text = _drive(ui_chat._replay_generator(turn, 0))
    events = _parse_sse(text)
    # mark_done only flips the turn's flags — the `done` frame is published
    # by _finalize_turn on the worker path, so a hand-built turn replays its
    # events and then the generator closes.
    assert [e[0] for e in events] == ["token"] * 5
    assert [e[1] for e in events] == [1, 2, 3, 4, 5]
    # a mid-stream cursor is gap-free too (nothing was evicted)
    mid = _parse_sse(_drive(ui_chat._replay_generator(turn, 2)))
    assert all(e[0] != "gap" for e in mid)
    assert [e[1] for e in mid] == [3, 4, 5]


def test_ring_overflow_emits_gap_event_naming_floor(monkeypatch):
    """rm-126 (assess F3): after ring eviction a reconnect at after=0 used to
    receive a silently truncated batch; it must be told the floor + gap."""
    monkeypatch.setattr(ui_chat, "TURN_EVENT_RING_MAX", 32)
    turn = ui_chat.Turn(session_id="gap-s", turn_id="t-gap", holder="h")
    for i in range(40):
        turn.publish("token", {"delta": f"chunk-{i}"})
    turn.mark_done("end_turn")
    floor = 40 - 32 + 1  # seq 9 is the oldest surviving event

    events = _parse_sse(_drive(ui_chat._replay_generator(turn, 0)))
    assert events[0][0] == "gap"
    assert events[0][2]["ring_floor"] == floor
    assert events[0][2]["gap_from"] == 1
    assert events[0][2]["type"] == "ring_floor"
    # the gap event's id is floor-1, so a reconnect carrying it resumes at
    # the surviving floor and does not re-trigger the signal
    assert events[0][1] == floor - 1
    assert [e[1] for e in events[1:]] == list(range(floor, 41))

    resumed = _parse_sse(_drive(ui_chat._replay_generator(turn, floor - 1)))
    assert resumed[0][0] != "gap"
    assert [e[1] for e in resumed] == list(range(floor, 41))


def test_reconnect_honors_last_event_id_header(client, monkeypatch):
    """rm-126: a native EventSource resends Last-Event-ID automatically — the
    header is the resume cursor (and wins over ?after=)."""
    install_stub_agent(monkeypatch)
    with client.stream("POST", "/api/chat", json={"message": "replay me"}) as resp:
        assert resp.status_code == 200
        text = "".join(resp.iter_text())
    events = _parse_sse(text)
    meta = events[0][2]
    sid, turn_id = meta["session_id"], meta["turn_id"]
    cut = events[2][1]
    expected = [e[1] for e in events if e[1] > cut]

    resp = client.get(
        f"/api/chat/stream?session_id={sid}&turn_id={turn_id}",
        headers={"Last-Event-ID": str(cut)},
    )
    assert resp.status_code == 200
    replay = _parse_sse(resp.text)
    assert [e[1] for e in replay] == expected
    assert all(e[0] != "gap" for e in replay)

    # header precedence: ?after=0 is ignored when the header is present
    resp = client.get(
        f"/api/chat/stream?session_id={sid}&turn_id={turn_id}&after=0",
        headers={"Last-Event-ID": str(cut)},
    )
    assert [e[1] for e in _parse_sse(resp.text)] == expected


def test_reconnect_after_ring_overflow_names_the_floor(client, monkeypatch):
    """rm-126, over HTTP: the first batch of an overflowed reconnect carries
    the explicit gap event before the surviving events."""
    monkeypatch.setattr(ui_chat, "TURN_EVENT_RING_MAX", 32)
    turn = ui_chat.Turn(session_id="gap-http", turn_id="t-gap-http", holder="h")
    for i in range(40):
        turn.publish("token", {"delta": str(i)})
    turn.mark_done("end_turn")
    ui_chat._register_turn(turn)

    resp = client.get("/api/chat/stream?session_id=gap-http&turn_id=t-gap-http&after=0")
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events[0][0] == "gap"
    assert events[0][2]["ring_floor"] == 9
    assert events[0][2]["gap_from"] == 1
    assert [e[1] for e in events[1:]] == list(range(9, 41))


class _ThreadStartFailureProxy:
    """``threading`` stand-in whose Thread.start() always fails (rm-127 F4)."""

    def __getattr__(self, name):
        return getattr(threading, name)

    class Thread:  # noqa: N801 — mirrors threading.Thread's construction site
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            raise RuntimeError("can't start new thread")


def test_thread_start_failure_releases_lease_and_closes_turn(client, monkeypatch):
    """rm-127 (assess F4): a failed Thread.start must not strand the 300 s
    lease (session 409s until TTL) nor leave a never-done, unprunable Turn
    that keeps burning a _max_concurrent slot."""
    install_stub_agent(monkeypatch)
    real_threading = ui_chat.threading
    ui_chat.threading = _ThreadStartFailureProxy()  # restored below: the
    # monkeypatch fixture instance is shared with the autouse env isolation,
    # so undo() here would also revert HERMES_HOME back to the real home.
    sid = _create_session_via_api(client)
    try:
        with client.stream("POST", "/api/chat", json={"session_id": sid, "message": "go"}) as resp:
            assert resp.status_code == 200
            text = "".join(resp.iter_text())
    finally:
        ui_chat.threading = real_threading

    events = _parse_sse(text)
    assert [e[0] for e in events] == ["meta", "error", "done"]
    assert events[1][2]["code"] == "THREAD_START_FAILED"
    assert events[-1][2]["finish_reason"] == "error"

    turn = ui_chat._turns[sid]
    assert turn.done is True
    assert turn.finish_reason == "error"
    assert ui_chat._active_turn_count() == 0

    # the lease is free: a second send on the same session is NOT 409
    db = ui_chat._session_db()
    holder = _probe_holder()
    assert db.try_acquire_session_turn_lease(sid, holder, ttl_seconds=300.0) is True
    db.release_session_turn_lease(sid, holder)


def test_stop_during_agent_build_is_honored(client, monkeypatch):
    """rm-127 (assess F5): a stop arriving while _build_agent runs (cold
    imports take seconds; turn.agent is not set yet) must prevent the turn
    from executing, not return {stopped:true} and run to completion."""
    build_started = threading.Event()
    release_build = threading.Event()
    executed = {"run_conversation": 0}

    class _BuiltButNeverRunAgent:
        def interrupt(self, *args, **kwargs):
            pass

        def run_conversation(self, *args, **kwargs):
            executed["run_conversation"] += 1
            return {"interrupted": False, "failed": False, "final_response": ""}

    def _slow_build_agent(*, turn, db, model, profile):
        build_started.set()
        assert release_build.wait(_THREAD_BUDGET), "test never released the build"
        return _BuiltButNeverRunAgent()

    monkeypatch.setattr(ui_chat, "_build_agent", _slow_build_agent)
    sid = _create_session_via_api(client)
    result: dict = {}

    def _stream():
        with client.stream("POST", "/api/chat", json={"session_id": sid, "message": "go"}) as resp:
            result["status"] = resp.status_code
            result["text"] = "".join(resp.iter_text())

    stream_thread = threading.Thread(target=_stream, daemon=True)
    stream_thread.start()
    try:
        _wait_for_turn(sid)
        assert build_started.wait(_THREAD_BUDGET), "agent build never started"
        # the stop lands while _build_agent is still running
        resp = client.post("/api/chat/stop", json={"session_id": sid})
        assert resp.status_code == 200
        assert resp.json()["data"]["stopped"] is True
    finally:
        release_build.set()
        stream_thread.join(timeout=_THREAD_BUDGET)

    assert result.get("status") == 200
    events = _parse_sse(result.get("text", ""))
    assert events[-1][0] == "done"
    assert events[-1][2]["finish_reason"] == "interrupted"
    assert executed["run_conversation"] == 0

    db = ui_chat._session_db()
    holder = _probe_holder()
    assert db.try_acquire_session_turn_lease(sid, holder, ttl_seconds=300.0) is True
    db.release_session_turn_lease(sid, holder)


def test_session_db_is_the_single_hermes_state_store():
    """rm-129 (assess F7): there is exactly one SessionDB implementation and
    no 'real vs shim' fallback indirection left to mislead a reader."""
    import hermes_state

    db = ui_chat._session_db()
    assert isinstance(db, hermes_state.SessionDB)
    assert "ShimSessionDB" not in Path(ui_chat.__file__).read_text()
    assert "drop-in replacement" not in hermes_state.__doc__
