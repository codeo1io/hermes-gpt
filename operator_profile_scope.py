"""Process-wide serialization of the Hermes profile-home override.

The Hermes Agent exposes ``set_hermes_home_override`` /
``reset_hermes_home_override`` as *process-global* state: whatever override a
thread installs is what every other thread resolves until it is reset.
Operator tool bodies execute on concurrent worker threads (the rm-074
off-loop seam), so two profile-scoped tool calls that interleave can observe
each other's profile home mid-call — a cross-profile data bleed (assess
finding F03, roadmap rm-207).

This module provides the process-wide profile lock the roadmap accepts:
holders of the *same* profile home may overlap (per-profile work stays
parallel), while holders of *different* profile homes are mutually exclusive
for the whole override window. Every in-process override site enters through
this gate so the lock is shared:

* ``operator_skill_resolution._profile_scope`` (skill discovery and the
  explicit-load validation probe), via :func:`profile_override_scope`;
* ``operator_skills._call_skill_manager`` (direct skill mutation), via
  :func:`profile_override_gate` around its existing set/reset pair.

Child-process profile scoping (``operator_session``, ``operator_finance``,
``finance_worker``) builds a private ``env`` mapping per call and never
mutates this process's ``os.environ`` (``finance_worker`` sets it only inside
its own child process), so it needs no gate. Subprocesses spawned inside a
gated window inherit a parent whose override state is consistent for the
whole window.

The gate keeps no registry of profiles beyond the normalized home currently
held, adds no logging, and records no profile-identifying material anywhere;
nothing here reaches audit records.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

__all__ = [
    "ProfileScopeConflict",
    "profile_override_gate",
    "profile_override_scope",
]


class ProfileScopeConflict(RuntimeError):
    """A thread tried to hold two different profile scopes at once.

    Nesting scopes for different homes in one thread would wait on a gate
    the same thread already holds, deadlocking it. That is a calling-layer
    bug, so it fails loudly instead of hanging.
    """


_condition = threading.Condition()
_current_key: str | None = None  # normalized home held by the current holders
_holders = 0
_owner_stack = threading.local()  # per-thread list of currently held keys


def _gate_key(profile_home: Any) -> str:
    """Normalize a profile home to one gate key per physical home."""
    try:
        return str(Path(profile_home).expanduser().resolve())
    except (OSError, RuntimeError, TypeError, ValueError):
        # Pathological home (bad type/symlink loop): still gate, just on the
        # raw representation so the window is never left unserialized.
        return repr(profile_home)


@contextmanager
def profile_override_gate(profile_home: Any) -> Iterator[None]:
    """Hold the shared override window exclusively for ``profile_home``.

    Same-home holders overlap; different-home holders block until the
    current holders drain. Re-entering for the same home in one thread is
    allowed; entering for a different home while this thread already holds
    one raises :class:`ProfileScopeConflict` instead of deadlocking.
    """
    global _holders, _current_key
    key = _gate_key(profile_home)
    stack = getattr(_owner_stack, "keys", None)
    if stack is None:
        stack = []
        _owner_stack.keys = stack
    if stack and stack[-1] != key:
        raise ProfileScopeConflict(
            "thread already holds a profile scope for "
            f"{stack[-1]!r}; refusing to nest a conflicting scope for {key!r}"
        )
    with _condition:
        while _current_key is not None and _current_key != key:
            _condition.wait()
        _current_key = key
        _holders += 1
    stack.append(key)
    try:
        yield
    finally:
        with _condition:
            _holders -= 1
            if _holders == 0:
                _current_key = None
            _condition.notify_all()
        try:
            stack.pop()
        except IndexError:  # pragma: no cover - defensive
            pass


@contextmanager
def profile_override_scope(profile_home: Any, constants: Any) -> Iterator[None]:
    """Gate plus install the process-global home override from ``constants``.

    Degradation contract (unchanged from the previous inline scope): when
    the provided ``constants`` module does not expose the override pair
    there is nothing to serialize, so the scope is a no-op. Callers that
    must fail closed on a missing override (skill *mutation*) keep that
    decision at their call site and use :func:`profile_override_gate`
    directly around their own set/reset pair.
    """
    setter = getattr(constants, "set_hermes_home_override", None)
    resetter = getattr(constants, "reset_hermes_home_override", None)
    if not callable(setter) or not callable(resetter):
        yield
        return
    with profile_override_gate(profile_home):
        token = setter(profile_home)
        try:
            yield
        finally:
            resetter(token)
