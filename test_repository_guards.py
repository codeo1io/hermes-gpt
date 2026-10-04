"""Repository truth guards for hermes-gpt.

Two self-enforcing guards added by campaign repository-maintenance:278d0720
cycle 3 (run d33be0958593, implement attempt 3f7dc0dd):

U2 (rm-197): production modules must not grow new ``assert``-based
invariants. ``python -O`` strips asserts, so a guarded failure silently
becomes an ``AttributeError``/``IndexError`` downstream. Sites that
predate this guard are allowlisted below with removal notes; converting
them is tracked as the rm-197 rider.

U3 (rm-046, guard half): every ``docs/...`` target referenced from
``README.md`` and ``docs/README.md`` must be shipped through the
``[tool.setuptools.data-files]`` tables (verified against the built
wheel: 31 docs + 4 examples under ``share/hermes-gpt``), or be
explicitly allowlisted below with a reason. The ship-or-de-reference
decision for the remaining exceptions is tracked on rm-046 itself.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# --- U2: no new non-test assert invariants in production modules -------------

PRODUCTION_MODULE_GLOBS = ("operator_*.py", "ui_*.py", "server.py")

# Sites predating this guard. Each entry needs a removal note; when a site is
# converted to an explicit failure, delete its entry here.
LEGACY_ASSERT_SITES: dict[str, set[int]] = {
    # rm-197 deferred rider: this file was owned by a live sibling lane when
    # rm-197 landed (runners:1303 and swarm:466 were converted); convert when
    # the live_events lane is free.
    "operator_live_events.py": {221},
}


def test_no_new_production_assert_invariants() -> None:
    violations: list[str] = []
    modules: list[Path] = []
    for pattern in PRODUCTION_MODULE_GLOBS:
        modules.extend(sorted(REPO_ROOT.glob(pattern)))
    assert modules, "guard scope resolved to no modules; update the globs"
    for module in modules:
        for lineno, line in enumerate(
            module.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if re.match(r"^[ \t]+assert\b", line):
                if lineno not in LEGACY_ASSERT_SITES.get(module.name, set()):
                    violations.append(f"{module.name}:{lineno}: {line.strip()}")
    assert not violations, (
        "new assert-based invariant(s) in production modules; use explicit "
        "fail-closed raises instead (python -O strips asserts):\n  "
        + "\n  ".join(violations)
    )


def test_legacy_assert_allowlist_is_exact() -> None:
    """Every allowlisted site must still exist, so the list cannot rot."""
    for name, linenos in LEGACY_ASSERT_SITES.items():
        module = REPO_ROOT / name
        assert module.exists(), f"allowlisted module {name} disappeared"
        lines = module.read_text(encoding="utf-8").splitlines()
        for lineno in sorted(linenos):
            assert re.match(
                r"^[ \t]+assert\b", lines[lineno - 1]
            ), f"{name}:{lineno} no longer holds an assert; remove the stale allowlist entry"


# --- U3: README-referenced docs ship (or are explicitly allowlisted) ---------


_HISTORICAL_DOC_REFS: dict[str, str] = {
    # README:70 — historical design artifacts, deliberately unshipped (the
    # docs authority map marks docs/design/* as historical).
    "docs/design": "historical design docs; deliberately not shipped",
    # docs/README.md:49 — links "examples/" relative to docs/, but the real
    # directory is the repository root examples/ (which ships). Dead link,
    # tracked as a low-severity docs finding; fix in the rm-046 lane.
    "docs/examples": "dead relative link; real dir is top-level examples/ (ships)",
    # docs/README.md:51 — the docs index references itself; the index is not
    # part of the shipped data-files set by design.
    "docs/README.md": "docs index self-reference; index not shipped by design",
}

_LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[^)\s]*)?\)")


def _shipped_doc_targets(pyproject: Path) -> set[str]:
    shipped: set[str] = set()
    in_table = False
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[tool.setuptools.data-files"):
            in_table = True
            continue
        if in_table:
            if stripped.startswith("["):
                break
            for entry in re.findall(r'"([^"]+)"', stripped):
                if entry.startswith("docs/"):
                    shipped.add(entry)
    assert shipped, "no docs shipped under data-files; guard is blind — fix parsing"
    return shipped


def _referenced_doc_targets(source: Path) -> set[str]:
    referenced: set[str] = set()
    base = os.path.dirname(source.name)
    for href in _LINK_RE.findall(source.read_text(encoding="utf-8")):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        if not href.startswith("docs/") and not href.endswith((".md", "/")):
            continue
        resolved = (
            href
            if href.startswith("docs/")
            else os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")
        )
        if resolved.startswith("docs/"):
            referenced.add(resolved)
    return referenced


def test_readme_referenced_docs_ship() -> None:
    shipped = _shipped_doc_targets(REPO_ROOT / "pyproject.toml")
    violations: list[str] = []
    for source_name in ("README.md", "docs/README.md"):
        source = REPO_ROOT / source_name
        assert source.exists()
        for target in sorted(_referenced_doc_targets(source)):
            if target in shipped:
                continue
            if target in _HISTORICAL_DOC_REFS:
                continue
            violations.append(f"{source_name} -> {target} is referenced but not shipped")
    assert not violations, (
        "referenced docs missing from pyproject data-files (add them, "
        "de-reference, or extend _HISTORICAL_DOC_REFS with a reason):\n  "
        + "\n  ".join(violations)
    )
