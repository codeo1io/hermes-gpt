#!/usr/bin/env python3
"""One-command upstream census for maintenance/catch-up cycles (rm-107).

Every repository-maintenance cycle re-derives the same probe set by hand:
where HEAD sits relative to ``upstream`` (merge-base, ahead/behind), what
the upstream remote has published (tip + tags), what PyPI currently serves,
and whether the load-bearing symbols the assess census relies on still
exist in this tree. This tool prints that census in one shot so the
evidence is uniform across cycles and reviewers do not have to trust
ad-hoc shell transcripts.

Usage:
    python tools/upstream_delta.py [--json] [--repo PATH] [--upstream NAME]
                                   [--ref REF] [--symbols a,b,c]
                                   [--pypi-project NAME] [--no-network]

Exit codes:
    0  census completed (fields that need network may report
       "unavailable"/"skipped" without failing the run);
    1  repository/git failure — not a git work tree, missing upstream
       remote, or a git subprocess error;
    2  usage error (argparse).

The symbol census counts occurrences of each configured symbol across
tracked ``*.py`` files; a symbol with zero occurrences is reported as
missing. Network probes (PyPI) are skipped under ``--no-network`` and are
never exercised by the unit tests.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_UPSTREAM_REMOTE = "upstream"
DEFAULT_PYPI_PROJECT = "hermes-gpt"
PYPI_TIMEOUT_S = 5.0

# Load-bearing surface the maintenance census historically probes for.
# Extend when a cycle's assess relies on a new symbol; the census exists to
# fail loudly when one of these quietly disappears from the tree.
DEFAULT_SYMBOLS = [
    "hermes_cron_create",
    "hermes_events_query",
    "hermes_events_tail",
    "try_acquire_session_turn_lease",
    "_read_audit_events",
    "build_asgi_app",
    "resolve_profile_home",
    "run_argv",
]


class GitError(RuntimeError):
    """A git subprocess failed or the repository shape is unusable."""


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed (rc={proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout.strip()


def _git_ok(repo: Path, *args: str) -> str | None:
    try:
        return _git(repo, *args)
    except GitError:
        return None


@dataclass
class DeltaReport:
    repo: str
    upstream_remote: str
    ref: str
    head: str = ""
    merge_base: str = ""
    ahead: int = 0
    behind: int = 0
    upstream_head: str = ""
    tags: list[str] = field(default_factory=list)
    latest_tag: str = ""
    pypi_version: str = ""
    symbol_census: dict[str, int] = field(default_factory=dict)
    missing_symbols: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "upstream_remote": self.upstream_remote,
            "ref": self.ref,
            "head": self.head,
            "merge_base": self.merge_base,
            "ahead": self.ahead,
            "behind": self.behind,
            "upstream_head": self.upstream_head,
            "tags": self.tags,
            "latest_tag": self.latest_tag,
            "pypi_version": self.pypi_version,
            "symbol_census": self.symbol_census,
            "missing_symbols": self.missing_symbols,
        }


def _tag_sort_key(tag: str) -> tuple:
    """Sort tags by dotted-numeric groups so v0.13.0 > v0.9.7."""
    return tuple(
        (0, int(part)) if part.isdigit() else (1, 0)
        for part in re.split(r"[.\-+]", tag.lstrip("vV"))
    )


def _fetch_pypi_version(project: str) -> str:
    try:
        with urllib.request.urlopen(
            f"https://pypi.org/pypi/{project}/json", timeout=PYPI_TIMEOUT_S
        ) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        return str(data.get("info", {}).get("version") or "")
    except Exception as exc:  # noqa: BLE001 - report, never crash the census
        return f"unavailable ({type(exc).__name__})"


def _symbol_counts(repo: Path, symbols: list[str]) -> dict[str, int]:
    counts = {name: 0 for name in symbols}
    listing = _git_ok(repo, "ls-files", "*.py")
    files = [line for line in (listing or "").splitlines() if line]
    if not files:
        return counts
    for rel in files:
        try:
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name in symbols:
            counts[name] += text.count(name)
    return counts


def _upstream_tracking_ref(repo: Path, upstream: str) -> str:
    """First existing remote-tracking ref for ``upstream``.

    ``git remote add`` does not create ``refs/remotes/<upstream>/HEAD``
    (only a clone does), so fall back to the conventional default branch
    names exactly like the hand-run census did.
    """
    for candidate in ("HEAD", "master", "main"):
        ref = f"{upstream}/{candidate}"
        if _git_ok(repo, "rev-parse", "--verify", "--quiet", ref):
            return ref
    raise GitError(
        f"no remote-tracking refs found for '{upstream}' (run: git fetch {upstream})"
    )


def collect_delta(
    repo: Path,
    *,
    upstream: str = DEFAULT_UPSTREAM_REMOTE,
    ref: str = "HEAD",
    symbols: list[str] | None = None,
    pypi_project: str = DEFAULT_PYPI_PROJECT,
    allow_network: bool = True,
) -> DeltaReport:
    """Gather the census. Raises GitError (rc=1 surface) on repo problems."""
    symbols = symbols if symbols is not None else list(DEFAULT_SYMBOLS)
    report = DeltaReport(
        repo=str(repo), upstream_remote=upstream, ref=ref
    )

    report.head = _git(repo, "rev-parse", ref)

    upstream_ref = _upstream_tracking_ref(repo, upstream)
    merge_base = _git_ok(repo, "merge-base", ref, upstream_ref)
    if merge_base is None:
        raise GitError(
            f"cannot compute merge-base with '{upstream_ref}' "
            f"(run: git fetch {upstream})"
        )
    report.merge_base = merge_base

    ahead_behind = _git(repo, "rev-list", "--left-right", "--count", f"{ref}...{upstream_ref}")
    left, _, right = ahead_behind.partition("\t")
    # left/right of A...B: left = commits only in A (us, ahead),
    # right = commits only in B (upstream, behind).
    report.ahead = int(left.strip() or 0)
    report.behind = int(right.strip() or 0)

    ls_remote = _git_ok(repo, "ls-remote", upstream)
    if ls_remote is None:
        raise GitError(f"remote '{upstream}' is not configured or unreachable")
    for line in ls_remote.splitlines():
        sha, _, refname = line.partition("\t")
        refname = refname.strip()
        if refname == "HEAD":
            report.upstream_head = sha
        elif refname.startswith("refs/tags/") and not refname.endswith("^{}"):
            report.tags.append(refname[len("refs/tags/") :])
    if report.tags:
        version_tags = [t for t in report.tags if re.match(r"^v?\d", t)]
        report.latest_tag = sorted(version_tags or report.tags, key=_tag_sort_key)[-1]

    report.pypi_version = (
        _fetch_pypi_version(pypi_project) if allow_network else "skipped (--no-network)"
    )

    report.symbol_census = _symbol_counts(repo, symbols)
    report.missing_symbols = [
        name for name in symbols if report.symbol_census.get(name, 0) == 0
    ]
    return report


def render_text(report: DeltaReport) -> str:
    lines = [
        f"repo:            {report.repo}",
        f"HEAD ({report.ref}):  {report.head}",
        f"upstream remote: {report.upstream_remote} (head {report.upstream_head or '?'})",
        f"merge-base:      {report.merge_base}",
        f"ahead/behind:    {report.ahead} / {report.behind}",
        f"tags:            {len(report.tags)} (latest {report.latest_tag or 'none'})",
    ]
    if report.tags:
        lines.append(f"tag list:        {', '.join(report.tags)}")
    lines.append(f"PyPI latest:     {report.pypi_version or 'unknown'}")
    lines.append(f"symbols probed:  {len(report.symbol_census)}")
    if report.missing_symbols:
        lines.append(f"MISSING SYMBOLS: {', '.join(report.missing_symbols)}")
    else:
        lines.append("missing symbols: none")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="upstream_delta",
        description=(
            "Print the maintenance census: HEAD/merge-base/ahead-behind "
            "vs the upstream remote, upstream tags, PyPI latest, and a "
            "missing-symbol census for the configured symbol list."
        ),
        epilog=(
            "exit codes: 0 = census complete; 1 = repository/git failure "
            "(missing remote, no merge-base, git error); 2 = usage error."
        ),
    )
    parser.add_argument("--repo", default=".", help="repository path (default: cwd)")
    parser.add_argument(
        "--upstream", default=DEFAULT_UPSTREAM_REMOTE, help="upstream remote name"
    )
    parser.add_argument("--ref", default="HEAD", help="local ref to measure (default: HEAD)")
    parser.add_argument(
        "--symbols",
        default=",".join(DEFAULT_SYMBOLS),
        help="comma-separated symbol list for the census (default: built-in set)",
    )
    parser.add_argument(
        "--pypi-project", default=DEFAULT_PYPI_PROJECT, help="PyPI project to probe"
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="skip the PyPI probe (report 'skipped'); git remotes may still use network",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    try:
        report = collect_delta(
            repo,
            upstream=args.upstream,
            ref=args.ref,
            symbols=symbols,
            pypi_project=args.pypi_project,
            allow_network=not args.no_network,
        )
    except GitError as exc:
        print(f"upstream_delta: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
