from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"

SHELL_FENCE_RE = re.compile(r"```(?:ba|z)?sh(?:ell)?\s*$")
PIP_INSTALL_RE = re.compile(r"\bpip\b.*\binstall\b")
REQUIREMENT_FLAG_RE = re.compile(r"(?:-r|--requirement)(?:\s+|=)(\S+)")


def _shell_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if current is None:
            if SHELL_FENCE_RE.search(line):
                current = []
        elif line.strip() == "```":
            blocks.append("\n".join(current))
            current = None
        else:
            current.append(line)
    return blocks


def _requirement_paths(block: str) -> list[str]:
    paths: list[str] = []
    for line in block.splitlines():
        if PIP_INSTALL_RE.search(line):
            paths.extend(REQUIREMENT_FLAG_RE.findall(line))
    return paths


def _dev_section(text: str) -> str:
    assert "## Development and verification" in text, (
        "README lost its development section"
    )
    return text.split("## Development and verification", 1)[1].split("\n## ", 1)[0]


def test_readme_pip_requirement_targets_exist() -> None:
    text = README.read_text(encoding="utf-8")
    missing = [
        path
        for block in _shell_blocks(text)
        for path in _requirement_paths(block)
        if not (ROOT / path).exists()
    ]
    assert not missing, (
        f"README pip commands reference missing requirement files: {missing}"
    )


def test_readme_dev_block_installs_editable_dev_extra() -> None:
    dev = _dev_section(README.read_text(encoding="utf-8"))
    assert 'python -m pip install -e ".[dev]"' in dev
    assert "-r requirements" not in dev


def test_requirement_matcher_ignores_plain_installs_and_flags_missing() -> None:
    assert _requirement_paths('python -m pip install -e ".[dev]"') == []
    assert _requirement_paths("pip install hermes-gpt") == []
    assert _requirement_paths("pip install -r nonexistent-requirements.txt") == [
        "nonexistent-requirements.txt"
    ]
