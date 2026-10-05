"""rm-139: roadmap id-discipline guard (tools/check_roadmap_ids.py).

Proves the guard on the REAL managed board (clean, unique, monotone) and on
synthetic boards that it catches exactly the historical failure classes:
duplicated ids, ids reused across Open/Closed blocks, non-monotone frontier,
status outside the grammar, malformed id lines — plus the next-free-id
computation against a configurable fleet frontier.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
GUARD = REPO_ROOT / "tools" / "check_roadmap_ids.py"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import check_roadmap_ids as guard  # noqa: E402


def _synthetic_board() -> str:
    return """# Roadmap

## Open items

### First
- id: `rm-100` | track: reliability | priority: 110.0 | status: candidate

### Second
- id: `rm-101` | track: reliability | priority: 100.0 | status: in_progress

## Closed items

- `rm-099` Old thing — done
"""


def test_real_board_is_clean_and_next_free_uses_file_max():
    text = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    findings, next_free = guard.validate(text)
    hard = [f for f in findings if not f.startswith("note: ")]
    assert hard == [], hard
    items, _, _ = guard.parse(text)
    assert items, "board parse found no id lines"
    assert next_free == max(item.num for item in items) + 1


def test_fleet_frontier_raises_next_free_id():
    findings, next_free = guard.validate(_synthetic_board(), fleet_frontier=500)
    assert findings == []
    assert next_free == 501


def test_file_above_fleet_frontier_is_a_note_not_a_failure():
    findings, next_free = guard.validate(_synthetic_board(), fleet_frontier=50)
    assert any(f.startswith("note: ") and "rm-101" in f for f in findings)
    assert next_free == 102  # file max wins over the lower frontier
    assert [f for f in findings if not f.startswith("note: ")] == []


def test_duplicate_id_is_caught_and_waivable():
    board = _synthetic_board().replace(
        "### Second", "### Second\n- id: `rm-100` | track: reliability | priority: 105.0 | status: candidate"
    )
    findings, _ = guard.validate(board)
    assert any("duplicate id rm-100" in f for f in findings)
    waived, _ = guard.validate(board, allow_duplicates={100})
    assert not any("duplicate id" in f for f in waived)


def test_closed_block_reuse_is_caught():
    board = _synthetic_board().replace("- `rm-099` Old thing — done", "- `rm-100` Old thing — done")
    findings, _ = guard.validate(board)
    assert any("reused across Open and Closed blocks" in f for f in findings)


def test_non_monotone_priority_is_caught():
    board = _synthetic_board().replace(
        "- id: `rm-101` | track: reliability | priority: 100.0 | status: in_progress",
        "- id: `rm-101` | track: reliability | priority: 120.0 | status: in_progress",
    )
    findings, _ = guard.validate(board)
    assert any("monotone" in f and "rm-101" in f for f in findings)


def test_status_outside_grammar_is_caught():
    board = _synthetic_board().replace("status: candidate", "status: blocked")
    findings, _ = guard.validate(board)
    assert any("status 'blocked' not in grammar" in f for f in findings)


def test_malformed_id_line_is_caught():
    board = _synthetic_board().replace(
        "- id: `rm-100` | track: reliability | priority: 110.0 | status: candidate",
        "- id: `rm-100` | track: reliability | status: candidate",
    )
    _, _, errors = guard.parse(board)
    assert any("priority" in e for e in errors)


def test_cli_end_to_end_on_real_board():
    proc = subprocess.run(
        [sys.executable, str(GUARD), str(REPO_ROOT / "ROADMAP.md"), "--fleet-frontier", "rm-228"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "next free id: rm-229" in proc.stdout
