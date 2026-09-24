"""Canonical profile-aware skill resolution for Operator placement/plan paths.

Problem (upstream issue #74): before this module, four code paths each
answered "does profile X have skill Y?" differently:

* ``server.skill_roots()`` — global + per-profile skill *roots* (directories);
* ``operator_skills._find_skill_dir`` — recursive ``SKILL.md`` lookup under a
  single profile home;
* ``operator_capability_manifest._list_profile_skills`` — top-level-only
  skills snapshot used for placement targets;
* placement ranking used the manifest snapshot with **no hard gate**, so a
  zero-skill target could win a skill-requiring node.

This module is the single canonical, read-only projection over that state
(no persisted registry; always derived from the live tree):

* ``resolve_skill(name, hermes_root)`` -> ``SkillResolution`` (resolvable,
  found paths, resolving profiles, scope);
* ``profile_skills(profile, hermes_root)`` -> sorted skill names for one
  profile (recursive ``SKILL.md`` walk, same semantics as
  ``operator_skills._find_skill_dir``);
* two-stage validation:
  - stage 1 (plan creation): ``validate_required_skills`` — every declared
    skill must exist *somewhere* (global root or any profile) else
    ``SkillNotFoundError``;
  - stage 2 (placement/assignment, re-run on every placement decision, so
    reassignment revalidates): ``validate_assignee_skills`` — the assignee
    profile must resolve every required skill else
    ``SkillNotResolvableForAssigneeError`` (message lists the profiles that
    *do* resolve it).

Placement hard-filtering itself stays pure: ``operator_placement`` gates on
target["skills"] (manifest snapshot) so scoring remains I/O-free and
deterministic; this module is used for the I/O-ful surfaces around it —
profile-kind targets are enriched with the recursive resolver view at
manifest-load time, so the hard gate and the validator agree on semantics.

Scope note (deliberate): ``server.skill_roots()`` additionally reads a
global ``<HERMES_ROOT>/skills`` root for MCP ``discover_skills``
presentation. This resolver intentionally mirrors the *execution* view
(``operator_skills`` per-profile scoping) instead: a skill shipped only in
the presentation root is advertised but not executable by any profile, and
plan validation fails closed on it rather than green-lighting a plan whose
skills no assignee can run.

Listings cap RESULT SIZE (``MAX_SKILL_ENTRIES_PER_ROOT``) and walks cap
TRAVERSAL (``MAX_WALKED_ENTRIES`` directories visited per root) — a runaway
tree degrades to a partial, deterministic listing instead of hanging.
Within one validation call each root is walked at most once.

Skill names reuse ``operator_skills``' grammar verbatim (single source of
truth): lowercase alphanumerics plus ``.`` ``_`` ``-``, max 64 chars —
anything ``operator_skills`` accepts as a name resolves here too.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import operator_policy as op
import operator_skills

# Grammar is operator_skills' own (dots/underscores allowed, 64-char cap):
# the resolver must accept exactly the names the executor can run — a
# divergent grammar here would make placement reject runnable skills or
# accept unrunnable ones. Single source of truth, imported not copied.
SKILL_NAME_RE = operator_skills._VALID_NAME_RE
MAX_SKILL_NAME_LENGTH = operator_skills._MAX_NAME_LENGTH

# Bounds: MAX_SKILL_ENTRIES_PER_ROOT caps the RESULT SIZE of one root's
# listing; MAX_WALKED_ENTRIES caps TRAVERSAL (directories visited per
# root) so a pathological tree degrades instead of hanging a validation.
MAX_SKILL_ENTRIES_PER_ROOT = 2048
MAX_WALKED_ENTRIES = 50_000
MAX_LISTED_NAMES = 24
SKILL_FILE = "SKILL.md"

# Authority personas are controller-local; they have no skills directory and
# never fail skill resolution (documented pass-through).
CONTROLLER_PERSONAS = ("owner", "tony")

__all__ = [
    "CONTROLLER_PERSONAS",
    "SkillNotFoundError",
    "SkillNotResolvableForAssigneeError",
    "SkillResolution",
    "SkillResolutionError",
    "profile_skills",
    "resolve_skill",
    "validate_assignee_skills",
    "validate_required_skills",
]


class SkillResolutionError(ValueError):
    """Base class for skill-resolution validation failures."""


class SkillNotFoundError(SkillResolutionError):
    """A required skill does not exist in the global root or any profile."""

    def __init__(self, skill: str, available: list[str]) -> None:
        self.skill = skill
        self.available = available
        shown = ", ".join(sorted(available)[:MAX_LISTED_NAMES])
        more = len(available) - min(len(available), MAX_LISTED_NAMES)
        suffix = f" (+{more} more)" if more > 0 else ""
        super().__init__(
            f"skill_not_found: {skill!r} is not defined in the global skills root "
            f"or any profile; available skills: [{shown}{suffix}]"
        )


class SkillNotResolvableForAssigneeError(SkillResolutionError):
    """The skill exists, but the assignee profile cannot resolve it."""

    def __init__(
        self,
        skill: str,
        assignee: str,
        resolvable_profiles: list[str],
        *,
        global_only: bool,
    ) -> None:
        self.skill = skill
        self.assignee = assignee
        self.resolvable_profiles = resolvable_profiles
        self.global_only = global_only
        where = (
            "the global skills root only"
            if global_only
            else "profiles: " + ", ".join(sorted(resolvable_profiles)[:MAX_LISTED_NAMES])
        )
        super().__init__(
            f"skill_not_resolvable_for_assignee: profile {assignee!r} cannot resolve "
            f"skill {skill!r}; the skill is available via {where}"
        )


@dataclass(frozen=True)
class SkillResolution:
    """Read-only projection: where does (did) a skill resolve?"""

    skill: str
    resolvable: bool = False
    found_paths: tuple[str, ...] = field(default_factory=tuple)
    profiles: tuple[str, ...] = field(default_factory=tuple)
    scope: str = ""  # "global" | "profile" | "mixed" | "" (unresolvable)


def validate_skill_name(name: Any) -> str:
    """Validate a skill name with the shared grammar (ValueError on bad).

    Same grammar and length cap as ``operator_skills`` (the executor): a
    name that fails here is a name no profile can run. The grammar is
    enforced on the RAW string — whitespace-padded names are rejected, not
    silently normalized — so a name that passes this gate is byte-identical
    to the name the executor will later validate.
    """
    if not isinstance(name, str):
        raise TypeError("skill name must be a string")
    if len(name) > MAX_SKILL_NAME_LENGTH:
        raise ValueError(
            f"skill name exceeds {MAX_SKILL_NAME_LENGTH} characters: {name!r}"
        )
    if not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(
            "skill name must be lowercase alphanumerics with '.', '_' or '-' "
            f"(max {MAX_SKILL_NAME_LENGTH} chars): {name!r}"
        )
    return name


def _walk_skill_names(root: Path) -> dict[str, Path]:
    """Return {skill name -> observed SKILL.md directory} for one root.

    Recursive, mirroring ``operator_skills._find_skill_dir`` semantics: any
    directory under the root containing ``SKILL.md`` declares a skill named
    after the directory. Bounded two ways — result size
    (``MAX_SKILL_ENTRIES_PER_ROOT``) and traversal
    (``MAX_WALKED_ENTRIES`` directories visited) — and best-effort
    (unreadable trees degrade to empty/partial).
    """
    names: dict[str, Path] = {}
    if not root.is_dir():
        return names
    visited = 0
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()  # deterministic traversal (lexicographic DFS)
            if SKILL_FILE in filenames:
                pdir = Path(dirpath)
                nm = pdir.name
                if SKILL_NAME_RE.fullmatch(nm) and nm not in names:
                    names[nm] = pdir
                if len(names) >= MAX_SKILL_ENTRIES_PER_ROOT:
                    break
            visited += 1
            if visited >= MAX_WALKED_ENTRIES:
                break
    except OSError:
        return names
    return names


def global_skills_root(hermes_root: Path | None) -> Path | None:
    """The global (non-profile) skills root: ``<hermes_root>/skills``."""
    if hermes_root is None:
        return None
    return hermes_root / "skills"


def profile_skills(profile: str, hermes_root: Path | None) -> list[str]:
    """Sorted skill names resolvable inside one profile home."""
    canon = op.validate_profile_name(profile)
    if hermes_root is None:
        return []
    home = op.resolve_profile_home(canon, hermes_root)
    return sorted(_walk_skill_names(home / "skills"))


def _name_maps(
    hermes_root: Path | None,
) -> tuple[dict[str, Path], dict[str, dict[str, Path]]]:
    """Walk every resolution root once: (global map, {profile: map})."""
    global_map: dict[str, Path] = {}
    profile_maps: dict[str, dict[str, Path]] = {}
    if hermes_root is None:
        return global_map, profile_maps
    groot = global_skills_root(hermes_root)
    if groot is not None:
        global_map = _walk_skill_names(groot)
    for profile in op.list_existing_profiles(hermes_root):
        home = op.resolve_profile_home(profile, hermes_root)
        profile_maps[profile] = _walk_skill_names(home / "skills")
    return global_map, profile_maps


def resolve_skill(name: str, hermes_root: Path | None) -> SkillResolution:
    """Resolve one skill name across the global root and every profile.

    Deterministic: paths and profiles are sorted; the first occurrence wins
    per root, and every declaring profile is reported. ``found_paths`` are
    OBSERVED ``SKILL.md`` directories (may be nested), never synthesized.
    """
    skill = validate_skill_name(name)
    found: list[str] = []
    profiles: list[str] = []
    global_hit = False

    global_map, profile_maps = _name_maps(hermes_root)
    gdir = global_map.get(skill)
    if gdir is not None:
        global_hit = True
        found.append(str(gdir))
    for profile in sorted(profile_maps):
        pdir = profile_maps[profile].get(skill)
        if pdir is not None:
            profiles.append(profile)
            found.append(str(pdir))

    scope = (
        "global"
        if global_hit and not profiles
        else "profile"
        if profiles and not global_hit
        else "mixed"
        if global_hit and profiles
        else ""
    )
    return SkillResolution(
        skill=skill,
        resolvable=bool(found),
        found_paths=tuple(sorted(found)),
        profiles=tuple(sorted(profiles)),
        scope=scope,
    )


def validate_required_skills(skills: list[str], hermes_root: Path | None) -> None:
    """Stage 1: every declared skill must exist somewhere (fail closed).

    Walks each resolution root at most once per call (not once per skill).
    """
    global_map, profile_maps = _name_maps(hermes_root)
    for raw in skills:
        skill = validate_skill_name(raw)
        if skill in global_map or any(skill in pm for pm in profile_maps.values()):
            continue
        available: set[str] = set(global_map)
        for pm in profile_maps.values():
            available.update(pm)
        raise SkillNotFoundError(skill, sorted(available))


def validate_assignee_skills(
    profile: str,
    skills: list[str],
    hermes_root: Path | None,
) -> None:
    """Stage 2: the assignee profile must resolve every required skill.

    Controller personas (``owner`` / ``tony``) run with local authority and
    pass through. Re-run on every placement decision, so reassignment of a
    node to a different profile revalidates before any mutation.
    """
    canon = op.validate_profile_name(profile)
    if canon in CONTROLLER_PERSONAS or not skills:
        return
    own = set(profile_skills(canon, hermes_root))
    for raw in skills:
        skill = validate_skill_name(raw)
        if skill in own:
            continue
        res = resolve_skill(skill, hermes_root)
        raise SkillNotResolvableForAssigneeError(
            skill,
            canon,
            list(res.profiles),
            global_only=(not res.profiles and res.resolvable),
        )
