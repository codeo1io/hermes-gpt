"""Guard tests for shipped-docs truth (rm-046).

The wheel's shipped docs are the source of truth: ``pyproject.toml``
``[tool.setuptools.data-files]["share/hermes-gpt/docs"]``. ``MANIFEST.in``
must include every shipped doc so the sdist never omits one, and must not
carry duplicate include lines. This file pins both invariants so packaging
drift fails fast instead of shipping an incomplete distribution.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def _shipped_docs() -> list[str]:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return sorted(pyproject["tool"]["setuptools"]["data-files"]["share/hermes-gpt/docs"])


def _manifest_includes() -> list[str]:
    lines = (REPO_ROOT / "MANIFEST.in").read_text().splitlines()
    return [line.split(maxsplit=1)[1].strip() for line in lines if line.startswith("include ")]


def test_every_shipped_doc_exists_in_the_repository() -> None:
    missing = [doc for doc in _shipped_docs() if not (REPO_ROOT / doc).is_file()]
    assert not missing, f"pyproject data-files reference missing docs: {missing}"


def test_every_shipped_doc_is_included_in_the_sdist_manifest() -> None:
    includes = set(_manifest_includes())
    missing = [doc for doc in _shipped_docs() if doc not in includes]
    assert not missing, (
        "docs shipped in the wheel but absent from MANIFEST.in would be "
        f"missing from sdists: {missing}"
    )


def test_host_deployment_provenance_never_ships() -> None:
    """docs/runtime-checkout.md carries machine-specific absolute home paths
    (``/home/tony``) that the package-hygiene checker treats as
    release-blocking, so it must stay out of both the wheel and the sdist."""
    includes = set(_manifest_includes())
    shipped = set(_shipped_docs())
    assert "docs/runtime-checkout.md" not in shipped
    assert "docs/runtime-checkout.md" not in includes


def test_manifest_has_no_duplicate_include_lines() -> None:
    includes = _manifest_includes()
    duplicates = sorted({line for line in includes if includes.count(line) > 1})
    assert not duplicates, f"MANIFEST.in carries duplicate include lines: {duplicates}"


def test_shipped_docs_do_not_include_historical_or_host_state() -> None:
    shipped = set(_shipped_docs())
    forbidden = {
        "docs/releases.md",  # historical release history pointer, not runtime docs
    }
    overlap = sorted(shipped & forbidden)
    assert not overlap, f"host/historical docs must not ship in the wheel: {overlap}"


#: docs/*.md link targets reachable from README.md or docs/README.md that are
#: DELIBERATELY unshipped. Every entry carries its reason; a target that is
#: neither shipped nor listed here fails the guard tests below.
INTENTIONALLY_UNSHIPPED_DOC_LINKS = {
    # Host deployment provenance with machine-specific /home/tony paths —
    # pinned unshipped by test_host_deployment_provenance_never_ships until
    # its host-state hygiene is refreshed (rm-046 recorded remainder).
    "docs/runtime-checkout.md",
    # Repo-internal per-problem solutions runbooks: a maintenance surface,
    # not runtime package docs.
    "docs/solutions/README.md",
    # Repository maintenance cycle record: process history, not runtime docs.
    "docs/maintenance-cycle-log.md",
}


_DOC_LINK = re.compile(r"\]\(([^)#\s]+\.md)\)")


def _readme_doc_link_targets() -> set[str]:
    """Every docs/*.md target linked from README.md or docs/README.md.

    README.md links are repo-relative (``docs/foo.md``); docs/README.md
    links are docs-relative (``foo.md``, ``../CHANGELOG.md``) — both are
    resolved against the repo root, and only targets landing under
    ``docs/`` are kept.
    """
    targets: set[str] = set()
    for page in ("README.md", "docs/README.md"):
        text = (REPO_ROOT / page).read_text()
        base = Path(page).parent
        for target in _DOC_LINK.findall(text):
            resolved = (base / target).resolve().relative_to(REPO_ROOT)
            as_posix = resolved.as_posix()
            if as_posix.startswith("docs/") and as_posix.endswith(".md"):
                targets.add(as_posix)
    return targets


def test_every_readme_doc_link_target_ships_or_is_explicitly_unshipped() -> None:
    """rm-046 review fix (2026-10-03, run 041a92f6667d): every docs/*.md link
    reachable from README.md or docs/README.md must ship in the wheel or
    carry an explicitly-rationaled unshipped entry — a README pointing
    readers at a doc the distribution omits is a broken promise."""
    shipped = set(_shipped_docs())
    targets = _readme_doc_link_targets()
    assert targets, "link census came up empty; the parser drifted"
    unshipped = sorted(
        target
        for target in targets
        if target not in shipped and target not in INTENTIONALLY_UNSHIPPED_DOC_LINKS
    )
    assert not unshipped, (
        "docs linked from README.md/docs/README.md but not shipped in the "
        "wheel (add to pyproject data-files, or record the exclusion): "
        f"{unshipped}"
    )


def test_unshipped_doc_allowlist_has_no_stale_or_phantom_entries() -> None:
    """Allowlist hygiene: every exclusion must still be linked (no stale
    entries quietly licensing new gaps) and must exist in the repo."""
    targets = _readme_doc_link_targets()
    stale = sorted(entry for entry in INTENTIONALLY_UNSHIPPED_DOC_LINKS if entry not in targets)
    assert not stale, f"allowlist entries no longer linked from the READMEs: {stale}"
    missing = sorted(
        entry for entry in INTENTIONALLY_UNSHIPPED_DOC_LINKS if not (REPO_ROOT / entry).is_file()
    )
    assert not missing, f"allowlist entries absent from the repository: {missing}"
