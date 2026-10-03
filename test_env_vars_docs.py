"""Guard test for the environment-variable reference (rm-080).

``docs/env-vars.md`` must stay in sync with the code: every
``HERMES_GPT_*`` knob mentioned in the codebase (test-only knobs excluded)
must be documented, and the reference must not describe knobs that no
longer exist.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
KNOB = re.compile(r"['\"](HERMES_GPT_[A-Z0-9_]+)['\"]")
EXCLUDED_DIRS = (".venv", "site-packages", "build", "dist", ".git")


def _code_knobs() -> set[str]:
    knobs: set[str] = set()
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        knobs.update(KNOB.findall(path.read_text(errors="ignore")))
    return {k for k in knobs if not k.startswith("HERMES_GPT_TEST_")}


def _documented_knobs() -> set[str]:
    text = (REPO_ROOT / "docs" / "env-vars.md").read_text()
    return set(re.findall(r"`(HERMES_GPT_[A-Z0-9_]+)`", text))


def test_every_code_knob_is_documented() -> None:
    missing = sorted(_code_knobs() - _documented_knobs())
    assert not missing, (
        "HERMES_GPT_* knobs read in code but absent from docs/env-vars.md "
        f"(update the reference): {missing}"
    )


def test_reference_documents_no_phantom_knobs() -> None:
    phantom = sorted(_documented_knobs() - _code_knobs())
    assert not phantom, (
        "docs/env-vars.md documents knobs that no code reads: {phantom}".format(
            phantom=phantom
        )
    )
