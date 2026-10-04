"""Tests for tools/check_roadmap_ids.py (rm-195 / rm-139).

Includes the failing-mode proof: a synthetic id removal shaped like the
6be3a5e95b render collapse MUST fail the guard.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent
TOOL = REPO_ROOT / "tools" / "check_roadmap_ids.py"

spec = importlib.util.spec_from_file_location("check_roadmap_ids", TOOL)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def write_ledger(path: Path, ids):
    """ids: list of (num, status) tuples."""
    lines = ["# Roadmap", "", "## Open items", ""]
    for num, status in ids:
        lines.append(f"### Item rm-{num:03d}")
        lines.append(f"- id: `rm-{num:03d}` | track: reliability | priority: 10.0 | status: {status}")
        lines.append("- signals: synthetic")
        lines.append("")
    lines.append("<!-- managed by hermes-roadmap render; do not edit by hand -->")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_tool(*argv):
    proc = subprocess.run(
        [sys.executable, str(TOOL), *argv],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc


def test_added_ids_pass(tmp_path):
    write_ledger(tmp_path / "base.md", [(1, "candidate"), (2, "in_progress")])
    write_ledger(tmp_path / "head.md", [(1, "candidate"), (2, "in_progress"), (3, "candidate")])
    proc = run_tool("--roadmap", str(tmp_path / "head.md"), "--baseline", str(tmp_path / "base.md"))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_identical_ledger_passes(tmp_path):
    write_ledger(tmp_path / "base.md", [(1, "candidate"), (2, "done")])
    write_ledger(tmp_path / "head.md", [(1, "candidate"), (2, "done")])
    proc = run_tool("--roadmap", str(tmp_path / "head.md"), "--baseline", str(tmp_path / "base.md"))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_synthetic_collapse_removal_fails(tmp_path):
    """Failing-mode proof: losing one id the way 6be3a5e95b did must fail."""
    write_ledger(
        tmp_path / "base.md",
        [(1, "candidate"), (2, "in_progress"), (3, "implemented (landed 2026-09-01)")],
    )
    # head drops rm-002 exactly like the render collapse: no marker, no trace
    write_ledger(
        tmp_path / "head.md",
        [(1, "candidate"), (3, "implemented (landed 2026-09-01)")],
    )
    proc = run_tool("--roadmap", str(tmp_path / "head.md"), "--baseline", str(tmp_path / "base.md"))
    assert proc.returncode == 1
    assert "rm-002" in proc.stdout
    assert "roadmap-id-removed" in proc.stdout


def test_marked_removal_passes(tmp_path):
    write_ledger(tmp_path / "base.md", [(1, "candidate"), (2, "candidate")])
    head = tmp_path / "head.md"
    write_ledger(head, [(1, "candidate")])
    text = head.read_text(encoding="utf-8")
    text = text.replace(
        "<!-- managed by hermes-roadmap render",
        "<!-- roadmap-id-removed: rm-002 because superseded by rm-101 -->\n<!-- managed by hermes-roadmap render",
    )
    head.write_text(text, encoding="utf-8")
    proc = run_tool("--roadmap", str(head), "--baseline", str(tmp_path / "base.md"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 marked removal" in proc.stdout


def test_duplicate_definition_fails(tmp_path):
    p = tmp_path / "head.md"
    write_ledger(p, [(1, "candidate")])
    text = p.read_text(encoding="utf-8")
    text += (
        "\n### Accidental re-mint\n"
        "- id: `rm-001` | track: reliability | priority: 99.0 | status: candidate\n"
        "- signals: duplicate\n"
    )
    p.write_text(text, encoding="utf-8")
    proc = run_tool("--roadmap", str(p), "--baseline", "none")
    assert proc.returncode == 1
    assert "duplicate definition of rm-001" in proc.stdout


def test_unknown_status_fails(tmp_path):
    write_ledger(tmp_path / "head.md", [(1, "frobnicated")])
    proc = run_tool("--roadmap", str(tmp_path / "head.md"), "--baseline", "none")
    assert proc.returncode == 1
    assert "rm-001" in proc.stdout and "unknown or missing status" in proc.stdout


def test_status_qualifiers_pass(tmp_path):
    write_ledger(
        tmp_path / "head.md",
        [
            (1, "candidate (design-gated)"),
            (2, "implemented (landed 2026-09-01)"),
            (3, "partially implemented (pending commit gate)"),
            (4, "superseded"),
        ],
    )
    proc = run_tool("--roadmap", str(tmp_path / "head.md"), "--baseline", "none")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_legacy_parenthetical_id_lines_count(tmp_path):
    """Renumbered legacy blocks like `- id: `rm-058` (orig `rm-051` ...)`
    must count as definitions and parse their status."""
    p = tmp_path / "head.md"
    p.write_text(
        "# Roadmap\n\n"
        "### Item\n"
        "- id: `rm-058` (orig `rm-051` in run-43fe0282 numbering; renumbered at integration)"
        " | track: reliability | priority: 115.0 | status: implemented (landed 2026-09-24)\n"
        "- signals: synthetic legacy block\n",
        encoding="utf-8",
    )
    proc = run_tool("--roadmap", str(p), "--baseline", "none")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 defined ids" in proc.stdout


def test_bare_legacy_id_line_counts(tmp_path):
    p = tmp_path / "head.md"
    p.write_text(
        "# Roadmap\n\n- id: rm-006 | track: customer-experience | priority: 85.0 | status: candidate\n",
        encoding="utf-8",
    )
    proc = run_tool("--roadmap", str(p), "--baseline", "none")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_json_report(tmp_path):
    write_ledger(tmp_path / "base.md", [(1, "candidate"), (2, "candidate")])
    write_ledger(tmp_path / "head.md", [(1, "candidate")])
    proc = run_tool(
        "--roadmap", str(tmp_path / "head.md"),
        "--baseline", str(tmp_path / "base.md"),
        "--json",
    )
    assert proc.returncode == 1
    import json

    report = json.loads(proc.stdout)
    assert report["ok"] is False
    assert report["unmarked_removals"] == [2]


def test_real_repo_ledger_is_a_superset_of_the_collapsed_render():
    """Live proof: the restored ledger must be a superset of 6be3a5e95b's
    collapsed render (the accident this guard exists to prevent)."""
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", "6be3a5e95b:ROADMAP.md"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.skip("commit 6be3a5e95b not reachable in this clone")
    base = proc.stdout
    head = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    report = guard.check(head, base)
    assert not report["violations"], report["violations"]
    base_ids = set(guard.parse_ledger(base)["defined"])
    head_ids = set(report["defined"])
    assert base_ids <= head_ids  # restored ids are present
