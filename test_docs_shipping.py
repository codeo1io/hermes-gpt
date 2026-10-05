"""rm-046: docs-shipping guard.

Every docs/*.md link target reachable from the SHIPPED entry points
(``README.md`` and ``docs/README.md``, both packaged under
``share/hermes-gpt``/``share/hermes-gpt/docs``) must either ship in
``[tool.setuptools.data-files]`` or appear in the explicit
``INTENTIONALLY_UNSHIPPED_DOCS`` allowlist below — an unexplained dead link in
a wheel is the exact drift this guards against (``docs/runtime-checkout.md``
was linked from the shipped docs map while shipping nowhere).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

#: Docs deliberately excluded from wheels, with the reason. Keep this list
#: SHORT: each entry ships a dead link to wheel readers.
INTENTIONALLY_UNSHIPPED_DOCS = {
    # Live host/unit deployment state (which checkout the host's systemd
    # service serves) — operational provenance, not product documentation.
    # Re-labeled "not shipped" in its header and in the docs map.
    "docs/runtime-checkout.md",
    # Historical maintenance-cycle provenance (campaign log). Self-labeled
    # historical; linked from no shipped surface.
    "docs/maintenance-cycle-log.md",
}

#: Relative-link patterns: `](target.md)` / `](docs/target.md)` /
#: `](../target.md)`. Anchors (#) and non-md targets are ignored.
_LINK_RE = re.compile(r"\]\(([^)#\s]+?\.md)\)")


def _load_toml() -> dict:  # type: ignore[no-untyped-def]
    try:
        import tomllib
    except ImportError:  # pragma: no cover - Python 3.10 lane
        import tomli as tomllib  # type: ignore[no-attr-defined]
    with open(REPO_ROOT / "pyproject.toml", "rb") as fh:
        return tomllib.load(fh)  # type: ignore[no-any-return]


def _shipped_docs() -> set[str]:
    data_files = _load_toml()["tool"]["setuptools"]["data-files"]
    return {
        entry
        for entry in data_files.get("share/hermes-gpt/docs", [])
        if entry.startswith("docs/")
    }


def _linked_docs(text: str, *, base: str) -> set[str]:
    """Normalize markdown link targets to repo-relative docs/ paths."""
    out: set[str] = set()
    for target in _LINK_RE.findall(text):
        if target.startswith("http://") or target.startswith("https://"):
            continue
        resolved = (Path(base) / target).resolve()
        try:
            rel = resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            continue  # escapes the repo (not a docs/ target)
        as_posix = rel.as_posix()
        if as_posix.startswith("docs/") and as_posix.endswith(".md"):
            out.add(as_posix)
    return out


def test_allowlist_entries_exist_and_stay_unshipped():
    """A stale allowlist entry would silently mask real shipping drift."""
    shipped = _shipped_docs()
    for entry in INTENTIONALLY_UNSHIPPED_DOCS:
        assert (REPO_ROOT / entry).is_file(), f"allowlisted doc missing: {entry}"
        assert entry not in shipped, (
            f"{entry} now ships — remove it from INTENTIONALLY_UNSHIPPED_DOCS"
        )


def test_shipped_docs_manifest_files_exist():
    for entry in _shipped_docs():
        assert (REPO_ROOT / entry).is_file(), f"data-files entry missing on disk: {entry}"


def test_every_doc_linked_from_shipped_entry_points_ships_or_is_allowlisted():
    shipped = _shipped_docs()
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    docs_map = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    linked = _linked_docs(readme, base=".") | _linked_docs(docs_map, base="docs")
    assert linked, "link extraction found no docs links — the guard went blind"
    unexplained = sorted(
        target for target in linked if target not in shipped and target not in INTENTIONALLY_UNSHIPPED_DOCS
    )
    assert not unexplained, (
        "docs linked from shipped entry points (README.md / docs/README.md) "
        "ship in no wheel and are not allowlisted — add them to "
        "[tool.setuptools.data-files] or to INTENTIONALLY_UNSHIPPED_DOCS "
        f"with a reason: {unexplained}"
    )
    # The known-fixed case must stay fixed: the vNext manifest/ledger guide is
    # linked from README.md and must ship.
    assert "docs/vnext-capability-manifest-and-mission-ledger.md" in shipped
