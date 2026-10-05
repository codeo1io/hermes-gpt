"""SessionDB contract: the ``last_active`` row alias (rm-297).

A UI conversation in hermes-gpt IS a Hermes Agent SessionDB session
(``source='webui'``): ui_chat imports the full agent ``hermes_state.SessionDB``
when it is importable and falls back to the in-repo shim otherwise. Both
providers must honor the same row contract for session listing, and the
consumer (``ui_chat._serialize_session``) reads the activity timestamp from
the ``last_active`` key.

The agent provider computes that column in its session-list SQL as
``rt.activity AS last_active`` (and ``_sql_session_last_active("s") AS
last_active``); an upstream rename of that alias would silently degrade
hermes-gpt's session list to the ``started_at`` fallback. This contract test
pins all three sides:

1. the agent source (when a checkout is available) still emits the alias;
2. the in-repo shim projects ``last_active`` on every listed row;
3. the consumer maps ``last_active`` -> ``last_activity_at`` with the
   documented fallback.

The CI-side companion (pinning the agent checkout ref in ci.yml) is tracked
separately on the board; this file must never depend on a hard-coded ref so it
keeps working on unpinned checkouts — it pins the *contract*, not the ref.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import hermes_state
import ui_chat

#: The SQL alias the agent's session-list query projects. Matched against the
#: agent source text, so an upstream rename fails this pin even when the
#: checkout moves (the alias has already moved lines at least once:
#: hermes_state_sessions.py:1235 -> :1190 as of 2026-10-05).
AGENT_ALIAS_PATTERN = re.compile(r"AS\s+last_active\b")

#: Where a Hermes Agent checkout is looked up, in order.
AGENT_SOURCE_ENV = "HERMES_AGENT_SOURCE"
AGENT_SOURCE_DEFAULT = "/home/agent/.hermes/hermes-agent"


def _agent_root() -> Path | None:
    """Locate a Hermes Agent checkout, or None when none is present."""
    candidates = [os.environ.get(AGENT_SOURCE_ENV), AGENT_SOURCE_DEFAULT]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return Path(candidate)
    return None


def _agent_head(root: Path) -> str:
    try:
        out = subprocess.run(  # noqa: S603 - fixed argv, shell=False
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return out.stdout.strip() or "unknown"


def test_agent_session_list_sql_still_projects_last_active():
    """Provider side: the agent's session-list SQL keeps the ``last_active`` alias."""
    root = _agent_root()
    if root is None:
        pytest.skip(f"no Hermes Agent checkout (set {AGENT_SOURCE_ENV} to pin one)")
    hits: list[str] = []
    for path in sorted(root.glob("*.py")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if AGENT_ALIAS_PATTERN.search(text):
            hits.append(f"{path.name}")
    assert hits, (
        "Hermes Agent no longer projects 'AS last_active' in its session-list "
        f"SQL at {root} (HEAD {_agent_head(root)}); ui_chat session ordering "
        "would silently degrade to the started_at fallback — re-pin the "
        "consumer mapping in ui_chat._serialize_session"
    )


REPO_SHIM = Path(__file__).resolve().parent / "hermes_state.py"


def test_bound_provider_list_sessions_projects_last_active(tmp_path: Path):
    """Provider side: every listed row carries a non-null ``last_active``.

    Whichever ``hermes_state`` module this test process bound is the provider
    ui_chat would use, so the pin is stated for that provider. The in-repo
    shim projects its native ``last_activity_at`` column under the alias; the
    full agent SessionDB computes the alias from message activity (falling
    back to ``started_at``), so on hosts where the agent checkout wins the
    import the behavioral pin is the presence and non-nullness of the key.
    """
    db = hermes_state.SessionDB(db_path=tmp_path / "state.db")
    db.create_session(session_id="s-contract", source="webui", model="m", profile_name="default")
    rows = db.list_sessions_rich(source="webui")
    assert rows, f"provider {hermes_state.__file__} listed no sessions"
    for row in rows:
        assert "last_active" in row, f"row missing last_active alias: {sorted(row)}"
        assert row["last_active"] is not None, f"last_active is null: {row}"
    if Path(hermes_state.__file__).resolve() == REPO_SHIM:
        for row in rows:
            assert row["last_active"] == row["last_activity_at"], f"shim row: {row}"


def test_consumer_maps_last_active_with_started_at_fallback():
    """Consumer side: ``_serialize_session`` reads ``last_active`` first."""
    live = ui_chat._serialize_session(
        {
            "id": "s1",
            "title": "t",
            "profile_name": "default",
            "model": "m",
            "message_count": 2,
            "started_at": 100.0,
            "last_active": 200.0,
        }
    )
    assert live["last_activity_at"] == 200.0
    assert live["created_at"] == 100.0
    fallback = ui_chat._serialize_session(
        {
            "id": "s2",
            "title": "t",
            "message_count": 0,
            "started_at": 100.0,
        }
    )
    assert fallback["last_activity_at"] == 100.0


def test_consumer_over_shim_rows_end_to_end(tmp_path: Path):
    """The in-repo pair (shim provider + ui consumer) honors the contract."""
    db = hermes_state.SessionDB(db_path=tmp_path / "state.db")
    db.create_session(session_id="s-e2e", source="webui", model="m")
    db.append_message("s-e2e", "user", content="hello")
    rows = db.list_sessions_rich(source="webui")
    serialized = [ui_chat._serialize_session(row) for row in rows]
    assert serialized and serialized[0]["session_id"] == "s-e2e"
    assert serialized[0]["last_activity_at"] == rows[0]["last_active"]
    assert serialized[0]["last_activity_at"] is not None


if __name__ == "__main__":  # pragma: no cover - manual pin check
    sys.exit(pytest.main([__file__, "-v"]))
