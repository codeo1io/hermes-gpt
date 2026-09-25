"""Guard tests for shipped-docs truth (rm-046).

The wheel's shipped docs are the source of truth: ``pyproject.toml``
``[tool.setuptools.data-files]["share/hermes-gpt/docs"]``. ``MANIFEST.in``
must include every shipped doc so the sdist never omits one, and must not
carry duplicate include lines. This file pins both invariants so packaging
drift fails fast instead of shipping an incomplete distribution.
"""

from __future__ import annotations

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
