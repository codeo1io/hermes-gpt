"""rm-142: hermes_state SessionDB shim attribute protocol and filter contract.

Regression tests for the shim's capability surface:
- missing attributes raise ``AttributeError`` (never ``NotImplementedError``)
  so ``hasattr``/``getattr`` capability probes degrade gracefully;
- ``SUPPORTED_API`` is an explicit, accurate capability surface;
- ``list_sessions_rich`` honors every row-selection filter it accepts or
  raises ``ValueError`` — no filter is silently ignored.
"""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import pytest

# Load the shim by explicit file path.  ``server.py`` eagerly calls
# ``import_hermes()`` at import time, which PREPENDS the discovered Hermes
# Agent deployment root to ``sys.path``; in a full single-process suite run
# (e.g. the local validation gate at workers=1) test modules collected before
# this one (test_codex_proxy_trust, test_gemini_compat) import ``server`` first,
# and a plain ``import hermes_state`` would then resolve to the deployment's
# real multi-mixin SessionDB instead of the shim under test.  Loading by path
# pins the module under test regardless of sys.path state or worker process
# isolation.

_SHIM_PATH = Path(__file__).resolve().with_name("hermes_state.py")
_spec = importlib.util.spec_from_file_location("hermes_state_shim_under_test", _SHIM_PATH)
hermes_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hermes_state)


@pytest.fixture()
def db(tmp_path):
    store = hermes_state.SessionDB(tmp_path / "state.db")
    yield store


def seeded_db(tmp_path):
    store = hermes_state.SessionDB(tmp_path / "state.db")
    store.create_session("s-idle-webui", "webui", title="idle")
    time.sleep(0.01)
    store.create_session("s-active-webui", "webui")
    store.append_message("s-active-webui", "user", "hello")
    store.append_message("s-active-webui", "assistant", "hi")
    store.create_session("s-codex", "codex")
    store.append_message("s-codex", "user", "code")
    time.sleep(0.01)
    # s-idle gets the newest last_activity_at even though it started first.
    store.append_message("s-idle-webui", "user", "later")
    return store


# --------------------------------------------------------------------------
# Attribute protocol (rm-142 / assess F1: hasattr/getattr crash)
# --------------------------------------------------------------------------


def test_missing_attribute_raises_attributeerror(db):
    with pytest.raises(AttributeError, match="does not implement 'search_messages'"):
        db.search_messages  # noqa: B018


def test_missing_attribute_never_raises_notimplementederror(db):
    for name in ("search_messages", "get_session_by_title", "get_compression_tip", "nope"):
        with pytest.raises(AttributeError):
            getattr(db, name)
        assert not isinstance(getattr(db, name, None), NotImplementedError)


def test_hasattr_capability_probes_degrade(db):
    # server.py probes exactly these on the underlying store.
    for name in (
        "get_session_by_title",
        "get_compression_tip",
        "search_messages",
        "_fts_enabled",
        "acquire_session_lease",
    ):
        assert hasattr(db, name) is False


def test_getattr_with_default_returns_default(db):
    assert getattr(db, "search_messages", "fallback") == "fallback"
    assert getattr(db, "__deepcopy__", None) is None  # copy/pickle probing path


def test_calling_unimplemented_method_fails_fast_at_lookup(db):
    with pytest.raises(AttributeError, match="SUPPORTED_API"):
        db.search_messages("query")


def test_supported_api_is_probeable_without_exceptions(db):
    for name in hermes_state.SessionDB.SUPPORTED_API:
        assert hasattr(db, name) is True
        assert callable(getattr(db, name))


def test_supported_api_matches_implemented_public_methods():
    implemented = {
        name
        for name in dir(hermes_state.SessionDB)
        if not name.startswith("_") and callable(getattr(hermes_state.SessionDB, name))
    }
    assert set(hermes_state.SessionDB.SUPPORTED_API) == implemented


# --------------------------------------------------------------------------
# list_sessions_rich: honored filters
# --------------------------------------------------------------------------


def test_source_filter_is_honored(tmp_path):
    store = seeded_db(tmp_path)
    rows = store.list_sessions_rich(source="webui")
    # Default order is started_at DESC: the newest-started session comes first.
    assert [row["id"] for row in rows] == ["s-active-webui", "s-idle-webui"]


def test_sources_and_exclude_filters_are_honored(tmp_path):
    store = seeded_db(tmp_path)
    rows = store.list_sessions_rich(sources=["webui", "codex"])
    assert {row["id"] for row in rows} == {"s-idle-webui", "s-active-webui", "s-codex"}
    rows = store.list_sessions_rich(exclude_sources=["webui"])
    assert {row["id"] for row in rows} == {"s-codex"}


def test_id_query_filter_is_honored(tmp_path):
    store = seeded_db(tmp_path)
    rows = store.list_sessions_rich(id_query="codex")
    assert [row["id"] for row in rows] == ["s-codex"]


def test_min_message_count_filter_is_honored(tmp_path):
    store = seeded_db(tmp_path)
    rows = store.list_sessions_rich(min_message_count=2)
    assert [row["id"] for row in rows] == ["s-active-webui"]


def test_limit_offset_are_honored(tmp_path):
    store = seeded_db(tmp_path)
    rows = store.list_sessions_rich(limit=1)
    assert len(rows) == 1
    first = rows[0]["id"]
    rows = store.list_sessions_rich(limit=1, offset=1)
    assert rows[0]["id"] != first


def test_order_by_last_active_is_honored(tmp_path):
    store = seeded_db(tmp_path)
    by_activity = [row["id"] for row in store.list_sessions_rich(order_by_last_active=True)]
    by_started = [row["id"] for row in store.list_sessions_rich(order_by_last_active=False)]
    # s-idle-webui started first but was appended to last.
    assert by_activity[0] == "s-idle-webui"
    assert by_started[-1] == "s-idle-webui"
    assert by_activity != by_started


# --------------------------------------------------------------------------
# list_sessions_rich: unsupported filters raise instead of silently ignoring
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cwd_prefix": "/work"},
        {"include_children": True},
        {"include_archived": True},
        {"archived_only": True},
        {"search_query": "hello"},
        {"include_pinned": True},
        {"session_key": "abc"},
        {"include_hidden": True},
        {"made_up_filter": 1},
    ],
)
def test_unhonorable_filters_raise_valueerror(db, kwargs):
    with pytest.raises(ValueError):
        db.list_sessions_rich(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"include_archived": False},
        {"archived_only": False},
        {"include_children": False},
        {"include_pinned": False},
        {"include_hidden": False},
        {"search_query": None},
        {"cwd_prefix": None},
        {"session_key": None},
    ],
)
def test_default_filter_values_are_accepted(db, kwargs):
    assert db.list_sessions_rich(**kwargs) == []


def test_presentation_flags_are_accepted_noops(tmp_path):
    store = seeded_db(tmp_path)
    plain = store.list_sessions_rich()
    compact = store.list_sessions_rich(compact_rows=True)
    no_tips = store.list_sessions_rich(project_compression_tips=False)
    assert [row["id"] for row in plain] == [row["id"] for row in compact]
    assert [row["id"] for row in plain] == [row["id"] for row in no_tips]
    # Rows are always the narrow sessions-table column set.
    for row in plain:
        assert set(row) == {
            "id",
            "source",
            "model",
            "profile_name",
            "started_at",
            "last_activity_at",
            "message_count",
            "title",
        }


def test_live_caller_shapes_are_accepted(tmp_path):
    """The two in-repo callers must keep working against the shim."""
    store = seeded_db(tmp_path)
    # ui_chat.py:675
    store.list_sessions_rich(
        source="webui",
        order_by_last_active=True,
        compact_rows=True,
        include_archived=False,
        limit=20,
    )
    # server.py:490
    store.list_sessions_rich(
        limit=50,
        offset=0,
        include_archived=False,
        compact_rows=True,
    )
