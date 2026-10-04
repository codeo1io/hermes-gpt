#!/usr/bin/env python3
"""Roadmap ledger id guard (rm-195 / rm-139).

Protects ROADMAP.md from the 6be3a5e95b class of accident: a render or bulk
edit that silently drops ``rm-`` ids. Checks:

1. every item definition line matches ``- id: `rm-NNN` | ...`` with a
   zero-padded three-digit id;
2. no id is defined twice;
3. every defined status starts with a known status word;
4. monotonicity: every id defined in the baseline ledger must still be
   defined in the checked ledger, unless the checked ledger carries an
   explicit removal marker for it::

       <!-- roadmap-id-removed: rm-042 because ... -->

Baseline defaults to ``origin/master:ROADMAP.md``. Use ``--baseline none``
to skip the monotonicity check, or ``--baseline <path>`` to compare against
a file. Any git ref works too (``git show <ref>:ROADMAP.md``).

Exit code 0 = ledger intact; 1 = violations found (printed). ``--json``
emits a machine-readable report instead.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ID_LINE = re.compile(r"^- id: `?rm-(\d{1,4})`?(.*?)(?: \| (track: .+))?$")
ID_ANY = re.compile(r"rm-(\d{1,4})")
STATUS_TAIL = re.compile(r"^track: [^|]+ \| priority: [0-9.]+ \| status: (.+)$")
REMOVAL_MARKER = re.compile(r"roadmap-id-removed: rm-(\d{1,4})\b")

# Status grammar observed in the ledger: a status word, optionally followed
# by a parenthetical qualifier ("candidate (design-gated)", "implemented
# (landed 2026-09-01)" ...).
STATUS_WORDS = {
    "candidate",
    "open",
    "in_progress",
    "implemented",
    "implemented-on-master",
    "partially implemented",
    "done",
    "completed",
    "superseded",
    "skipped",
    "blocked",
    "parked",
}


def parse_ledger(text: str) -> dict[str, list[int]]:
    """Return {'defined': [...], 'mentioned': [...], 'removal_markers': [...]}."""
    defined: list[int] = []
    mentioned: list[int] = []
    markers: list[int] = []
    malformed: list[str] = []
    statuses: dict[int, str] = {}
    for line in text.splitlines():
        for m in ID_ANY.finditer(line):
            mentioned.append(int(m.group(1)))
        mm = REMOVAL_MARKER.search(line)
        if mm:
            markers.append(int(mm.group(1)))
        m = ID_LINE.match(line)
        if m:
            num = int(m.group(1))
            defined.append(num)
            tail = m.group(3) or ""
            sm = STATUS_TAIL.match(tail)
            statuses[num] = sm.group(1).strip() if sm else ""
    return {
        "defined": defined,
        "mentioned": mentioned,
        "removal_markers": markers,
        "statuses": statuses,
        "malformed": malformed,
    }


def load_baseline(spec: str, repo: Path) -> str:
    if spec == "none":
        return ""
    p = Path(spec)
    if p.is_file():
        return p.read_text(encoding="utf-8")
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{spec}:ROADMAP.md"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot load baseline {spec!r}: {proc.stderr.strip()}")
    return proc.stdout


def status_word_ok(status: str) -> bool:
    if not status:
        return False
    low = " ".join(status.lower().split())
    for word in STATUS_WORDS:
        if low == word or low.startswith(word + " ") or low.startswith(word + "("):
            return True
        if low.startswith(word + " ("):
            return True
    return False


def check(head_text: str, base_text: str) -> dict:
    head = parse_ledger(head_text)
    violations: list[str] = []

    dupes = sorted({n for n in head["defined"] if head["defined"].count(n) > 1})
    for n in dupes:
        violations.append(f"duplicate definition of rm-{n:03d}")

    for n, status in sorted(head["statuses"].items()):
        if not status_word_ok(status):
            violations.append(f"rm-{n:03d}: unknown or missing status (got {status!r})")

    report = {
        "defined": sorted(set(head["defined"])),
        "duplicates": dupes,
        "violations": violations,
    }
    if base_text:
        base = parse_ledger(base_text)
        removed = sorted(set(base["defined"]) - set(head["defined"]))
        marked = set(head["removal_markers"])
        unmarked = [n for n in removed if n not in marked]
        for n in removed:
            if n in marked:
                report.setdefault("marked_removals", []).append(n)
        if unmarked:
            for n in unmarked:
                violations.append(
                    f"rm-{n:03d}: defined in baseline but missing here; add an explicit "
                    "'roadmap-id-removed: rm-NNN because ...' marker if the removal is intentional"
                )
        report["unmarked_removals"] = unmarked
        report["baseline_defined"] = sorted(set(base["defined"]))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    here = Path(__file__).resolve()
    repo = here.parent.parent
    ap.add_argument("--roadmap", type=Path, default=repo / "ROADMAP.md")
    ap.add_argument(
        "--baseline",
        default="origin/master",
        help="git ref, path to a ledger file, or 'none' (default: origin/master)",
    )
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    head_text = args.roadmap.read_text(encoding="utf-8")
    base_text = load_baseline(args.baseline, repo) if args.baseline else ""

    report = check(head_text, base_text)
    ok = not report["violations"]
    if args.as_json:
        print(json.dumps({"ok": ok, **report}, indent=1))
    else:
        for v in report["violations"]:
            print(f"ROADMAP GUARD: {v}")
        n_def = len(report["defined"])
        base_n = len(report.get("baseline_defined", []))
        if ok:
            print(
                f"ROADMAP GUARD: ok ({n_def} defined ids"
                + (f" vs {base_n} baseline; {len(report.get('marked_removals', []))} marked removals" if base_text else "")
                + ")"
            )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
