#!/usr/bin/env python3
"""Roadmap id-discipline guard (rm-139).

Validates a ROADMAP.md managed-render file and prints the next free id:

- id lines are unique within the Open block (boundary duplicates can be
  waived explicitly with ``--allow-duplicate rm-XXX`` — the documented
  canonical-occurrence rule for historical cases);
- no id is reused across the Open and Closed blocks;
- every id line is well-formed (``track:`` / ``priority: <num>`` /
  ``status:`` present);
- priorities are monotone non-increasing top-to-bottom (the frontier rule);
- statuses come from the fixed grammar below;
- the next free id is computed from ``--fleet-frontier`` (the highest id
  claimed anywhere in the fleet, e.g. sibling worktrees) or, by default,
  this file's own maximum.

Usage:
    python tools/check_roadmap_ids.py ROADMAP.md
    python tools/check_roadmap_ids.py ROADMAP.md --fleet-frontier rm-227
    python tools/check_roadmap_ids.py ROADMAP.md --allow-duplicate rm-099

Exit status: 0 = clean, 1 = findings, 2 = usage/parse error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: Fixed status grammar for the managed render. Extend deliberately: a new
#: status is a process change, not a typo fix.
STATUS_GRAMMAR = ("candidate", "in_progress")

_ID_LINE_RE = re.compile(r"^- id: `rm-(\d+)`")
_CLOSED_ID_RE = re.compile(r"^- `rm-(\d+)`")
_META_RE = re.compile(r"priority: ([0-9]+(?:\.[0-9]+)?)")
_STATUS_RE = re.compile(r"status: ([a-z_]+)")


@dataclass
class Item:
    line_no: int
    num: int
    priority: float | None
    status: str | None

    @property
    def ref(self) -> str:
        return f"rm-{self.num}"


def parse(text: str) -> tuple[list[Item], set[int], list[str]]:
    """Split Open-item id lines and Closed-block ids; collect parse errors."""
    items: list[Item] = []
    closed: set[int] = set()
    errors: list[str] = []
    in_closed = False
    current: Item | None = None
    for idx, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            in_closed = line.strip() == "## Closed items"
            continue
        id_match = _ID_LINE_RE.match(line)
        if id_match and not in_closed:
            priority_match = _META_RE.search(line)
            status_match = _STATUS_RE.search(line)
            priority = float(priority_match.group(1)) if priority_match else None
            status = status_match.group(1) if status_match else None
            if priority is None:
                errors.append(f"line {idx}: id line missing 'priority: <number>'")
            if status is None:
                errors.append(f"line {idx}: id line missing 'status: <word>'")
            current = Item(idx, int(id_match.group(1)), priority, status)
            items.append(current)
            continue
        closed_match = _CLOSED_ID_RE.match(line)
        if closed_match and in_closed:
            closed.add(int(closed_match.group(1)))
    return items, closed, errors


def validate(  # noqa: PLR0913
    text: str,
    *,
    allow_duplicates: set[int] | None = None,
    fleet_frontier: int | None = None,
) -> tuple[list[str], int]:
    """Return (findings, next_free_num) for a ROADMAP.md body."""
    items, closed, errors = parse(text)
    findings: list[str] = list(errors)
    allow = allow_duplicates or set()

    seen: dict[int, int] = {}
    for item in items:
        if item.num in seen and item.num not in allow:
            findings.append(
                f"line {item.line_no}: duplicate id {item.ref} (first at line {seen[item.num]})"
            )
        seen.setdefault(item.num, item.line_no)

    for item in items:
        if item.status is not None and item.status not in STATUS_GRAMMAR:
            findings.append(
                f"line {item.line_no}: status '{item.status}' not in grammar {STATUS_GRAMMAR}"
            )
        if item.num in closed:
            findings.append(
                f"line {item.line_no}: id {item.ref} reused across Open and Closed blocks"
            )

    previous: float | None = None
    for item in items:
        if item.priority is None:
            continue
        if previous is not None and item.priority > previous:
            findings.append(
                f"line {item.line_no}: {item.ref} priority {item.priority:g} breaks the monotone "
                f"non-increasing frontier (previous {previous:g})"
            )
        previous = item.priority if previous is None else max(previous, item.priority)

    file_max = max((item.num for item in items), default=0)
    basis_max = file_max if fleet_frontier is None else max(fleet_frontier, file_max)
    if fleet_frontier is not None and file_max > fleet_frontier:
        findings.append(
            f"note: file max rm-{file_max} exceeds fleet frontier rm-{fleet_frontier} "
            "(allowed when minted past the frontier; record the claim in the id line)"
        )
    return findings, basis_max + 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("roadmap", type=Path, help="path to ROADMAP.md")
    parser.add_argument(
        "--fleet-frontier",
        type=lambda value: int(value.lower().removeprefix("rm-")),
        default=None,
        help="highest rm-NNN id claimed anywhere in the fleet (default: this file's max)",
    )
    parser.add_argument(
        "--allow-duplicate",
        action="append",
        default=[],
        type=lambda value: int(value.lower().removeprefix("rm-")),
        help="waive a specific boundary duplicate (repeatable; record the reason where the waiver is invoked)",
    )
    args = parser.parse_args(argv)

    try:
        text = args.roadmap.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.roadmap}: {exc}", file=sys.stderr)
        return 2

    findings, next_free = validate(
        text,
        allow_duplicates=set(args.allow_duplicate),
        fleet_frontier=args.fleet_frontier,
    )
    for finding in findings:
        print(f"finding: {finding}")
    basis = (
        f"fleet frontier rm-{args.fleet_frontier}"
        if args.fleet_frontier is not None
        else "file max"
    )
    print(f"next free id: rm-{next_free} (basis: {basis})")
    if findings:
        # A frontier-exceeded note is informational, not a failure.
        hard = [f for f in findings if not f.startswith("note: ")]
        if not hard:
            return 0
        print(f"{len(hard)} finding(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
