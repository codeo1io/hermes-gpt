"""rm-094 drift guard: shipped ``HERMES_GPT_*`` environment knobs stay documented.

The assess finding (run 0aa75ea4, F4) was that the fleet-trust attestation
and runner-executable override knobs were discoverable only from source
code. The structural fix — one central knob registry (ROADMAP ``rm-088``) —
is deferred, so this guard is the interim contract:

* every literal ``HERMES_GPT_*`` knob name used by a **shipped** module
  (the ``py-modules`` list in ``pyproject.toml``) must appear in
  ``README.md`` or under ``docs/``, or be listed in the reviewed
  ``_UNDOCUMENTED_BACKLOG`` below with a reason;
* the rm-094 named set (fleet identity/URL + runner executables) must be
  documented in ``docs/operator-mode.md`` itself — the operational doc —
  not merely mentioned anywhere;
* the backlog must stay honest: an entry whose knob is later documented
  (or removed from source) fails the guard until the entry is dropped.

Knobs are matched by literal spelling; dynamically composed names
(f-string prefixes ending in ``_``, e.g. ``HERMES_GPT_ENABLE_{flag}``)
cannot be found by any grep and are out of scope for this guard.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"
OPERATOR_MODE = ROOT / "docs" / "operator-mode.md"

_KNOB_RE = re.compile(r"HERMES_GPT_[A-Z0-9_]+")

# The rm-094 batch documents the fleet identity/URL cluster and the runner
# executable overrides (they carry trust/dispatch semantics an operator
# cannot otherwise discover). Everything below is the remaining reviewed
# backlog awaiting the rm-088 registry; grouped by subsystem for review.
# Each entry is a real, source-verified knob that is intentionally not yet
# documented — do not add new knobs here without a reviewer-facing reason.
_UNDOCUMENTED_BACKLOG = frozenset(
    {
        # write-gate overrides (self-describing *_ALLOW_* family, rm-088 scope)
        "HERMES_GPT_ALLOW_CRON_WRITE",
        "HERMES_GPT_ALLOW_PRIVATE_NETWORK",
        "HERMES_GPT_ALLOW_SKILL_WRITE",
        "HERMES_GPT_ALLOW_WRITE",
        "HERMES_GPT_OPERATOR_DENIED_PATHS",
        # codex runner surface
        "HERMES_GPT_CODEX_ALLOWED_ROOTS",
        "HERMES_GPT_CODEX_TOOLSET",
        # fabric deployment topology
        "HERMES_GPT_FABRIC_COORDINATOR_DB",
        "HERMES_GPT_FABRIC_NODE_REGISTRY",
        "HERMES_GPT_FABRIC_PEER_DB",
        "HERMES_GPT_FABRIC_PEER_POLICY",
        "HERMES_GPT_FABRIC_PEER_TOKENS",
        "HERMES_GPT_FABRIC_ROUTING_POLICY",
        # fleet transport detail
        "HERMES_GPT_FLEET_A2A_MODE",
        # process/env plumbing
        "HERMES_GPT_PROFILE",
        "HERMES_GPT_CAPABILITY_CACHE_TTL",
        # swarm tuning knobs
        "HERMES_GPT_SWARM_BOARD_CAP",
        "HERMES_GPT_SWARM_MAX_PARALLEL",
        "HERMES_GPT_SWARM_MAX_STAGES",
        "HERMES_GPT_UI_MAX_CONCURRENT",
    }
)

# rm-094 named set: trust/dispatch semantics that must live in the
# operational doc, not only in source or a pointer.
_REQUIRED_IN_OPERATOR_MODE = (
    "HERMES_GPT_FLEET_PEER_NAME",
    "HERMES_GPT_FLEET_PEER_URL",
    "HERMES_GPT_FLEET_PEER_VERSION",
    "HERMES_GPT_HOST",
    "HERMES_GPT_PORT",
    "HERMES_GPT_PI_EXE",
    "HERMES_GPT_OMX_EXE",
    "HERMES_GPT_OPENCODE_EXE",
)


def _shipped_modules() -> list[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    modules = data["tool"]["setuptools"]["py-modules"]
    assert modules, "pyproject py-modules list is empty; guard cannot scan source"
    return modules


def _source_knobs() -> set[str]:
    knobs: set[str] = set()
    for module in _shipped_modules():
        path = ROOT / f"{module}.py"
        if path.exists():
            knobs |= set(_KNOB_RE.findall(path.read_text(encoding="utf-8")))
    # f-string dynamic prefixes ("HERMES_GPT_ENABLE_" + name) are not knobs
    return {k for k in knobs if not k.endswith("_")}


def _documented_knobs() -> set[str]:
    texts = [README.read_text(encoding="utf-8")]
    texts += [p.read_text(encoding="utf-8") for p in sorted(ROOT.glob("docs/**/*.md"))]
    documented: set[str] = set()
    for text in texts:
        documented |= set(_KNOB_RE.findall(text))
    return documented


def test_every_shipped_env_knob_is_documented_or_reviewed() -> None:
    source = _source_knobs()
    documented = _documented_knobs()
    undocumented = source - documented

    newly_undocumented = sorted(undocumented - _UNDOCUMENTED_BACKLOG)
    assert not newly_undocumented, (
        "HERMES_GPT_* knobs present in shipped modules but absent from "
        "README.md/docs/ and from the reviewed backlog in "
        "test_env_knob_docs.py: "
        f"{newly_undocumented}. Document the knob (default, scope, gate "
        "semantics) in the right operational doc, or add it to the backlog "
        "with a reviewer-facing reason (structural registry: ROADMAP rm-088)."
    )

    stale_backlog = sorted(_UNDOCUMENTED_BACKLOG - undocumented)
    assert not stale_backlog, (
        "Backlog entries in test_env_knob_docs.py that no longer correspond "
        f"to an undocumented shipped knob: {stale_backlog}. Drop them so the "
        "backlog keeps meaning 'intentionally undocumented'."
    )


def test_fleet_and_runner_knobs_are_documented_in_operator_mode() -> None:
    """rm-094 named set: documented in the operational doc itself."""
    text = OPERATOR_MODE.read_text(encoding="utf-8")
    missing = [knob for knob in _REQUIRED_IN_OPERATOR_MODE if knob not in text]
    assert not missing, (
        f"knobs missing from docs/operator-mode.md: {missing}. The fleet "
        "identity/advertised-URL cluster and runner executable overrides "
        "carry trust/dispatch semantics and belong in the operational doc."
    )


def test_readme_points_at_fleet_and_runner_knob_docs() -> None:
    """rm-094: README routes readers to the knob documentation."""
    text = README.read_text(encoding="utf-8")
    for knob in ("HERMES_GPT_FLEET_PEER_NAME", "HERMES_GPT_PI_EXE"):
        assert knob in text, f"{knob} should be named in README's fleet pointer"
    assert "fleet-peer-identity-and-advertised-url" in text
