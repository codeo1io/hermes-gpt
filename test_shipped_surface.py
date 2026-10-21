"""Shipped-surface guard (rm-172).

Fails when a tracked top-level non-test module is missing from the
``py-modules`` allowlist in ``pyproject.toml`` — the exact omission that kept
the campaign/work-class modules out of every built wheel while their tests
stayed green — and when a ``[project.scripts]`` entry targets a module that
is not shipped. Generalizes to docs and web assets later (rm-046 / rm-077)
by adding the corresponding surface lists here.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_EXCLUDED_STEMS = {"conftest"}


def _project_tables() -> tuple[list[str], dict[str, str]]:
    pyproject = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text("utf-8"))
    modules = pyproject["tool"]["setuptools"]["py-modules"]
    scripts = pyproject["project"]["scripts"]
    return modules, scripts


def test_every_top_level_module_is_shipped() -> None:
    modules, _scripts = _project_tables()
    listed = set(modules)
    tracked = {
        path.stem
        for path in _REPO_ROOT.glob("*.py")
        if not path.name.startswith("test_") and path.stem not in _EXCLUDED_STEMS
    }
    missing = sorted(tracked - listed)
    assert not missing, (
        "top-level modules absent from [tool.setuptools] py-modules "
        "(they will not ship in the wheel): " + ", ".join(missing)
    )


def test_shipped_modules_exist_in_checkout() -> None:
    modules, _scripts = _project_tables()
    absent = sorted(name for name in modules if not (_REPO_ROOT / f"{name}.py").is_file())
    assert not absent, "py-modules entries with no module file: " + ", ".join(absent)


def test_console_script_targets_are_shipped_modules() -> None:
    modules, scripts = _project_tables()
    listed = set(modules)
    bad = sorted(
        f"{name} -> {target}"
        for name, target in scripts.items()
        if target.split(":", 1)[0] not in listed
    )
    assert not bad, "console scripts targeting non-shipped modules: " + ", ".join(bad)


def test_campaign_lane_console_script_registered() -> None:
    _modules, scripts = _project_tables()
    assert scripts.get("hermes-gpt-campaign-lane") == "operator_campaign_lane:main"
