"""rm-207 regression coverage: concurrent profile scopes stay isolated.

The Hermes Agent home override is process-global. Before the shared profile
gate (``operator_profile_scope``), two Operator tool calls scoped to
different profiles could interleave on the rm-074 worker threads and observe
each other's profile home mid-call (assess finding F03). These tests pin:

* distinct-profile override windows never overlap (sampling AND a
  structural barrier proof);
* same-profile windows still overlap (no throughput regression);
* the full repo paths (``operator_skill_resolution._explicit_load_ok`` and
  ``operator_skills._call_skill_manager``) are scoped under the shared gate;
* rm-319: the server READ path (``skill_roots`` / ``discover_skills`` /
  ``hermes_skill_list`` / ``hermes_skill_view``) also resolves under the
  shared gate, so an un-profiled read never lists another profile's skills
  or returns their contents while that profile's window is open, and
  same-home windows still overlap;
* rm-319: the cross-home wait is bounded — past
  ``HERMES_GPT_PROFILE_GATE_TIMEOUT`` (default 300s) the gate fails closed
  with ``ProfileScopeTimeout`` instead of blocking forever;
* a subprocess spawned inside a window observes only that window's profile
  through the operator env-construction pattern, and the parent's
  ``os.environ`` is never mutated;
* nothing profile-identifying is written to logs from the scoped paths.

All tests run hermetically against fake ``hermes_constants`` /
``tools.skills_tool`` stand-ins; no Hermes Agent checkout is required.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import ModuleType

import pytest

import operator_profile_scope as profile_scope
import operator_skills as osk
import operator_skill_resolution as resolution
import server


class _FakeAgentConstants:
    """In-memory stand-in for the Agent's process-global override state.

    Mirrors the real contract: ``set_hermes_home_override`` installs a
    process-visible value and returns a token; ``reset_hermes_home_override``
    removes it. The "process" here is this object, exactly as shared and
    racy as the real global.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stack: list[tuple[str, str]] = []
        self.max_concurrent = 0
        self.observed: list[str | None] = []

    def set_hermes_home_override(self, home) -> str:
        token = f"tok-{time.monotonic_ns()}-{threading.get_ident()}"
        with self._lock:
            self._stack.append((token, str(home)))
            self.max_concurrent = max(self.max_concurrent, len(self._stack))
        return token

    def reset_hermes_home_override(self, token: str) -> None:
        with self._lock:
            for index in range(len(self._stack) - 1, -1, -1):
                if self._stack[index][0] == token:
                    del self._stack[index]
                    break
            else:
                raise RuntimeError(f"unknown override token {token!r}")

    def current_home(self) -> str | None:
        with self._lock:
            return self._stack[-1][1] if self._stack else None

    def observe(self) -> str | None:
        """Record what a loader running right now would resolve."""
        value = self.current_home()
        with self._lock:
            self.observed.append(value)
        return value

    def reset_for_test(self) -> None:
        with self._lock:
            self._stack.clear()
            self.observed.clear()
            self.max_concurrent = 0


def _two_homes(tmp_path: Path) -> dict[str, Path]:
    homes: dict[str, Path] = {}
    for profile in ("alpha", "beta"):
        home = tmp_path / "hermes" / "profiles" / profile
        home.mkdir(parents=True, exist_ok=True)
        homes[profile] = home
    return homes


def _run_threads(targets) -> list[BaseException]:
    errors: list[BaseException] = []

    def wrapped(target):
        def inner():
            try:
                target()
            except BaseException as exc:  # noqa: BLE001 - recorded, re-raised on join
                errors.append(exc)

        return inner

    threads = [threading.Thread(target=wrapped(t)) for t in targets]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive(), "worker thread hung"
    if errors:
        raise errors[0]
    return errors


# ---------------------------------------------------------------------------
# Unit level: the shared gate itself
# ---------------------------------------------------------------------------


def test_concurrent_distinct_profiles_never_observe_foreign_home(tmp_path):
    """Interleaved windows: every loader observation is the window's own home."""
    constants = _FakeAgentConstants()
    homes = _two_homes(tmp_path)
    observations: dict[str, list[str | None]] = {"alpha": [], "beta": []}

    def worker(profile: str) -> None:
        def run():
            with profile_scope.profile_override_scope(homes[profile], constants):
                deadline = time.monotonic() + 0.3
                while time.monotonic() < deadline:
                    observations[profile].append(constants.observe())
                    time.sleep(0.003)

        return run

    alpha = threading.Thread(target=worker("alpha"))
    alpha.start()
    time.sleep(0.03)  # guarantee alpha's window is open when beta starts
    beta = threading.Thread(target=worker("beta"))
    beta.start()
    for thread in (alpha, beta):
        thread.join(timeout=30)
        assert not thread.is_alive(), "worker thread hung"

    for profile, home in homes.items():
        seen = observations[profile]
        assert seen, f"{profile} observed nothing"
        foreign = {value for value in seen if value != str(home)}
        assert not foreign, (
            f"profile bleed: '{profile}' window observed foreign homes {foreign}"
        )


def test_gateless_override_can_hold_two_homes_simultaneously(tmp_path):
    """Non-vacuity proof: without the gate, two different homes coexist.

    Uses the raw setter/resetter pair with barriers, so the hazard is shown
    deterministically — this is the state the gate exists to make impossible
    inside a scoped window.
    """
    constants = _FakeAgentConstants()
    homes = _two_homes(tmp_path)
    barrier = threading.Barrier(2, timeout=10)

    def enter(home: Path) -> None:
        token = constants.set_hermes_home_override(home)
        barrier.wait()  # both threads now hold different homes
        barrier.wait()  # observe, then release
        constants.reset_hermes_home_override(token)

    _run_threads([lambda: enter(homes["alpha"]), lambda: enter(homes["beta"])])
    assert constants.max_concurrent == 2


def test_gate_allows_same_profile_overlap(tmp_path):
    """Same-home windows overlap: per-profile parallelism is preserved."""
    home = tmp_path / "hermes" / "profiles" / "alpha"
    home.mkdir(parents=True)
    barrier = threading.Barrier(2, timeout=10)

    def hold() -> None:
        with profile_scope.profile_override_gate(home):
            barrier.wait()  # only passes if BOTH threads are inside at once

    errors = _run_threads([hold, hold])
    assert not errors
    assert not barrier.broken


def test_gate_excludes_distinct_profiles_structurally(tmp_path):
    """Distinct-home windows cannot be open at the same time (barrier proof)."""
    homes = _two_homes(tmp_path)
    inside = threading.Event()
    other_entered = threading.Event()

    def holder() -> None:
        with profile_scope.profile_override_gate(homes["alpha"]):
            inside.set()
            # Hold long enough that a concurrent beta entry would have to
            # overlap if the gate did not exclude it.
            assert not other_entered.wait(timeout=1.0), (
                "beta entered its window while alpha still held the gate"
            )

    def waiter() -> None:
        assert inside.wait(timeout=5.0)
        with profile_scope.profile_override_gate(homes["beta"]):
            other_entered.set()

    errors = _run_threads([holder, waiter])
    assert not errors
    assert other_entered.is_set(), "beta never ran after alpha released"


def test_nested_conflicting_scope_raises_instead_of_deadlocking(tmp_path):
    homes = _two_homes(tmp_path)

    with profile_scope.profile_override_gate(homes["alpha"]):
        with profile_scope.profile_override_gate(homes["alpha"]):
            pass  # same-home nesting is allowed
        with pytest.raises(profile_scope.ProfileScopeConflict):
            with profile_scope.profile_override_gate(homes["beta"]):
                pass  # pragma: no cover - must not be reached

    # The conflicting attempt left no residue: beta can be held afterwards.
    with profile_scope.profile_override_gate(homes["beta"]):
        pass


def test_scope_degrades_to_noop_without_override_pair(tmp_path):
    """Missing setter/resetter keeps the previous plain-scope contract."""
    constants = _FakeAgentConstants()
    broken = ModuleType("hermes_constants_broken")

    with profile_scope.profile_override_scope(tmp_path, broken):
        assert constants.current_home() is None  # nothing installed
    assert constants.current_home() is None  # nothing left behind


# ---------------------------------------------------------------------------
# rm-319: the cross-home wait is bounded and fails closed
# ---------------------------------------------------------------------------


def test_gate_wait_timeout_env_parsing(monkeypatch):
    """HERMES_GPT_PROFILE_GATE_TIMEOUT tunes the bound; garbage never
    disables it (the wait must never become unbounded again)."""
    monkeypatch.delenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", raising=False)
    assert profile_scope._gate_wait_timeout() == 300.0
    for raw in ("garbage", "0", "-5", ""):
        monkeypatch.setenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", raw)
        assert profile_scope._gate_wait_timeout() == 300.0, raw
    monkeypatch.setenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", "0.25")
    assert profile_scope._gate_wait_timeout() == 0.25


def test_gate_wait_is_bounded_and_fails_closed(tmp_path, monkeypatch):
    """Waiting out a different home's window raises ProfileScopeTimeout
    past the bound (no hang) and leaves no gate residue behind."""
    homes = _two_homes(tmp_path)
    monkeypatch.setenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", "0.25")
    inside = threading.Event()
    release = threading.Event()

    def holder() -> None:
        with profile_scope.profile_override_gate(homes["alpha"]):
            inside.set()
            assert release.wait(timeout=10)

    thread = threading.Thread(target=holder)
    thread.start()
    assert inside.wait(timeout=5.0)

    started = time.monotonic()
    with pytest.raises(profile_scope.ProfileScopeTimeout):
        with profile_scope.profile_override_gate(homes["beta"]):
            pass  # pragma: no cover - must not be reached
    elapsed = time.monotonic() - started
    assert 0.2 <= elapsed < 5.0, elapsed

    release.set()
    thread.join(timeout=10)
    assert not thread.is_alive()
    with profile_scope.profile_override_gate(homes["beta"]):  # no residue
        pass


# ---------------------------------------------------------------------------
# Repo path 1: explicit-load validation (operator_skill_resolution)
# ---------------------------------------------------------------------------


def test_explicit_load_interleaved_two_profiles_stays_isolated(
    tmp_path, monkeypatch
):
    """Two threads validating skills for different profiles never cross."""
    root = tmp_path / "hermes"
    homes = _two_homes(tmp_path)
    constants = _FakeAgentConstants()
    records: list[tuple[int, str | None, str | None]] = []

    class _FakeSkillsTool:
        @staticmethod
        def _find_all_skills():
            return []

        def skill_view(self, name, preprocess=False):
            entry_home = constants.observe()
            time.sleep(0.05)  # widen the race window the gate must close
            exit_home = constants.observe()
            records.append((threading.get_ident(), entry_home, exit_home))
            return json.dumps({"success": True, "name": name})

    monkeypatch.setattr(resolution, "_skill_loader_override", None)
    monkeypatch.setattr(
        resolution, "_require_agent_modules", lambda: (_FakeSkillsTool(), constants)
    )

    results: dict[str, tuple[bool, str]] = {}

    def validate(profile: str) -> None:
        def run():
            ok, detail = resolution._explicit_load_ok(profile, "demo", root)
            results[profile] = (ok, detail)

        return run

    errors = _run_threads([validate("alpha"), validate("beta")])
    assert not errors

    assert results["alpha"][0] is True, results["alpha"]
    assert results["beta"][0] is True, results["beta"]

    thread_to_profile = {}
    # Identify each validating thread by the home it must have seen first.
    for ident, entry_home, _exit_home in records:
        for profile, home in homes.items():
            if entry_home == str(home):
                thread_to_profile[ident] = profile
    assert len(thread_to_profile) == 2, records

    for ident, entry_home, exit_home in records:
        profile = thread_to_profile[ident]
        assert entry_home == str(homes[profile]), (
            f"loader started on foreign home {entry_home!r} for {profile}"
        )
        assert exit_home == str(homes[profile]), (
            f"loader ended on foreign home {exit_home!r} for {profile}"
        )


# ---------------------------------------------------------------------------
# Repo path 2: direct skill mutation (operator_skills)
# ---------------------------------------------------------------------------


def test_call_skill_manager_windows_are_isolated(tmp_path, monkeypatch):
    constants = _FakeAgentConstants()
    fake_agent_constants = ModuleType("hermes_constants")
    fake_agent_constants.set_hermes_home_override = (
        constants.set_hermes_home_override
    )
    fake_agent_constants.reset_hermes_home_override = (
        constants.reset_hermes_home_override
    )
    monkeypatch.setitem(sys.modules, "hermes_constants", fake_agent_constants)

    observed: dict[str, list[str | None]] = {"alpha": [], "beta": []}
    lock = threading.Lock()

    class _FakeManagerModule:
        @staticmethod
        def skill_manage(**kwargs):
            profile = str(kwargs.get("_observer_profile"))
            deadline = time.monotonic() + 0.2
            while time.monotonic() < deadline:
                value = constants.observe()
                with lock:
                    observed[profile].append(value)
                time.sleep(0.003)
            return {"success": True, "action": kwargs.get("action")}

    monkeypatch.setattr(
        osk, "_get_skill_manager", lambda hermes_root=None: _FakeManagerModule
    )

    results: dict[str, dict] = {}

    def mutate(profile: str, home: Path) -> None:
        def run():
            results[profile] = osk._call_skill_manager(
                "create",
                "demo",
                hermes_root=tmp_path / "hermes",
                profile_home=home,
                _observer_profile=profile,
                content="---\nname: demo\ndescription: demo\n---\n",
            )

        return run

    homes = _two_homes(tmp_path)
    errors = _run_threads([mutate("alpha", homes["alpha"]), mutate("beta", homes["beta"])])
    assert not errors

    assert results["alpha"].get("success") is True, results["alpha"]
    assert results["beta"].get("success") is True, results["beta"]
    for profile, home in homes.items():
        seen = observed[profile]
        assert seen, f"{profile} observed nothing"
        foreign = {value for value in seen if value != str(home)}
        assert not foreign, (
            f"profile bleed through skill mutation: {profile} saw {foreign}"
        )


def test_call_skill_manager_fail_closed_without_agent_constants(
    tmp_path, monkeypatch
):
    """The pre-existing fail-closed degradation is preserved under the gate."""
    class _Missing:  # import finds the name; the override pair is not callable
        pass

    fake = ModuleType("hermes_constants")
    fake.set_hermes_home_override = _Missing()  # not callable
    fake.reset_hermes_home_override = _Missing()
    monkeypatch.setitem(sys.modules, "hermes_constants", fake)
    monkeypatch.setattr(
        osk, "_get_skill_manager", lambda hermes_root=None: ModuleType("m")
    )

    non_default = tmp_path / "hermes" / "profiles" / "alpha"
    non_default.mkdir(parents=True)
    result = osk._call_skill_manager(
        "create", "demo", hermes_root=tmp_path / "hermes", profile_home=non_default
    )
    assert result["success"] is False
    assert "Could not scope skill mutation" in result["error"]


# ---------------------------------------------------------------------------
# Subprocess env purity + log purity
# ---------------------------------------------------------------------------


def test_scoped_window_subprocess_env_is_profile_pure(tmp_path, monkeypatch):
    """Subprocess env built at spawn inside a window carries only that profile."""
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.delenv("HERMES_PROFILE", raising=False)
    constants = _FakeAgentConstants()
    homes = _two_homes(tmp_path)
    seen: dict[str, dict[str, str | None]] = {}

    def spawn_env(profile: str, home: Path) -> None:
        def run():
            with profile_scope.profile_override_scope(home, constants):
                # Operator pattern (operator_session/operator_finance):
                # build a private child env per call; never mutate os.environ.
                child_env = os.environ.copy()
                child_env["HERMES_HOME"] = str(home)
                child_env["HERMES_PROFILE"] = profile
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "import json,os; print(json.dumps({"
                        "'HERMES_HOME': os.environ.get('HERMES_HOME'),"
                        "'HERMES_PROFILE': os.environ.get('HERMES_PROFILE')}))",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=child_env,
                )
                seen[profile] = json.loads(completed.stdout)

        return run

    errors = _run_threads([spawn_env("alpha", homes["alpha"]), spawn_env("beta", homes["beta"])])
    assert not errors

    for profile, home in homes.items():
        assert seen[profile]["HERMES_HOME"] == str(home), seen[profile]
        assert seen[profile]["HERMES_PROFILE"] == profile, seen[profile]

    # The scope must never mutate this process's environment.
    assert os.environ.get("HERMES_HOME") is None
    assert os.environ.get("HERMES_PROFILE") is None


def test_scoped_paths_log_no_profile_material(tmp_path):
    """No log record from the scoped paths carries the home or profile name."""
    constants = _FakeAgentConstants()
    home = tmp_path / "hermes" / "profiles" / "alpha"
    home.mkdir(parents=True)

    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    collector = _Collector()
    root = logging.getLogger()
    root.addHandler(collector)
    try:
        with profile_scope.profile_override_scope(home, constants):
            constants.observe()
    finally:
        root.removeHandler(collector)

    for record in records:
        message = record.getMessage()
        assert str(home) not in message, message
        assert "alpha" not in message, message
        assert "profiles" not in message, message


# ---------------------------------------------------------------------------
# rm-319: the server READ path resolves under the shared gate
# ---------------------------------------------------------------------------


def _skill_read_env(tmp_path, monkeypatch, constants):
    """Two homes: the default (base) home and a foreign profile 'beta'.

    Mirrors the real mechanics hermetically: server's ``get_hermes_home``
    stand-in returns whatever override the fake process-global currently
    holds, falling back to the base home — exactly the resolution the real
    global performs.
    """
    base = tmp_path / "home-base"
    beta = tmp_path / "hermes" / "profiles" / "beta"
    for home, marker in ((base, "base"), (beta, "beta-secret")):
        skill = home / "skills" / f"{marker}-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {marker}-skill\ndescription: demo {marker}\n---\n"
            f"contents of {marker}\n",
            encoding="utf-8",
        )
    monkeypatch.setenv("HERMES_HOME", str(base))
    monkeypatch.setattr(server, "HERMES_ROOT", None)
    monkeypatch.setattr(server, "require_imports", lambda: None)
    monkeypatch.setattr(
        server,
        "get_hermes_home",
        lambda: constants.current_home() or str(base),
    )
    return base, beta


def _hold_foreign_window(beta: Path, constants):
    """Thread body holding beta's override window until released."""
    window_open = threading.Event()
    release = threading.Event()

    def holder() -> None:
        with profile_scope.profile_override_scope(beta, constants):
            window_open.set()
            assert release.wait(timeout=10)

    thread = threading.Thread(target=holder)
    thread.start()
    return window_open, release, thread


def test_skill_read_waits_out_foreign_profile_window(tmp_path, monkeypatch):
    """rm-319 regression: an un-profiled listing never materializes another
    profile's home held mid-window by a concurrent call.

    Pre-gate behavior (assess 988c9b7a F6): skill_roots read the process
    global override directly, so this listing returned beta's skills
    immediately. Now the read is serialized behind the shared gate: while
    the foreign window is open it waits (bounded) and fails closed instead
    of leaking; once the window drains it lists only the base home.
    """
    constants = _FakeAgentConstants()
    base, beta = _skill_read_env(tmp_path, monkeypatch, constants)
    monkeypatch.setenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", "0.3")

    window_open, release, thread = _hold_foreign_window(beta, constants)
    assert window_open.wait(timeout=5.0)
    assert constants.current_home() == str(beta)  # foreign override is live

    with pytest.raises(RuntimeError) as excinfo:
        server.hermes_skill_list()
    assert "HERMES_GPT_PROFILE_GATE_TIMEOUT" in str(excinfo.value)

    release.set()
    thread.join(timeout=10)
    assert not thread.is_alive()

    listing = server.hermes_skill_list()
    assert "base-skill" in listing, listing
    assert "beta-secret" not in listing, listing


def test_discover_skills_waits_out_foreign_window(tmp_path, monkeypatch):
    """The shared discovery helper itself is gated (skill_roots -> SKILL.md
    walk), not just the tools that call it."""
    constants = _FakeAgentConstants()
    base, beta = _skill_read_env(tmp_path, monkeypatch, constants)
    monkeypatch.setenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", "0.3")

    window_open, release, thread = _hold_foreign_window(beta, constants)
    assert window_open.wait(timeout=5.0)
    with pytest.raises(profile_scope.ProfileScopeTimeout):
        server.discover_skills()

    release.set()
    thread.join(timeout=10)
    assert not thread.is_alive()

    names = {skill["name"] for skill in server.discover_skills()}
    assert names == {"base-skill"}, names
    roots = server.skill_roots()
    assert len(roots) == 1, roots
    assert roots[0].parent.name == base.name, roots


def test_skill_view_never_reads_foreign_profile_contents(tmp_path, monkeypatch):
    """rm-319 regression: hermes_skill_view can neither resolve into nor
    return the contents of another profile's skill mid-window, and beta is
    invisible to the un-profiled view at rest."""
    constants = _FakeAgentConstants()
    base, beta = _skill_read_env(tmp_path, monkeypatch, constants)
    monkeypatch.setenv("HERMES_GPT_PROFILE_GATE_TIMEOUT", "0.3")

    window_open, release, thread = _hold_foreign_window(beta, constants)
    assert window_open.wait(timeout=5.0)

    with pytest.raises(RuntimeError):
        server.hermes_skill_view("beta-secret-skill")  # bounded, never contents

    release.set()
    thread.join(timeout=10)
    assert not thread.is_alive()

    assert "No skill matched" in server.hermes_skill_view("beta-secret-skill")
    visible = server.hermes_skill_view("base-skill")
    assert "contents of base" in visible, visible
    assert "contents of beta" not in visible, visible


def test_skill_read_overlaps_same_home_window(tmp_path, monkeypatch):
    """A same-home (default-profile) window does not block un-profiled
    reads: per-profile parallelism is preserved."""
    constants = _FakeAgentConstants()
    base, beta = _skill_read_env(tmp_path, monkeypatch, constants)

    with profile_scope.profile_override_scope(base, constants):
        listing = server.hermes_skill_list()  # same key: must not wait

    assert "base-skill" in listing, listing
    assert "beta-secret" not in listing, listing


def test_read_hazard_is_live_mid_window(tmp_path, monkeypatch):
    """Non-vacuity: mid-window the resolution server consults really does
    point at the foreign home — the tests above guard a live hazard (the
    exact state ungated skill_roots used to read), not a fictional one."""
    constants = _FakeAgentConstants()
    base, beta = _skill_read_env(tmp_path, monkeypatch, constants)

    with profile_scope.profile_override_scope(beta, constants):
        assert server.get_hermes_home() == str(beta)
    assert server.get_hermes_home() == str(base)
