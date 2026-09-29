#!/usr/bin/env python3
"""Read-only upstream-gap probe for hermes-gpt maintenance-cycle planning (rm-115).

Answers the questions every repository-maintenance cycle re-derives by hand:

* how far is this checkout behind ``<remote>/master`` (and ahead of it);
* is the checkout a fast-forward away or a true merge;
* which tag each side considers newest;
* which upstream pull requests are open (best effort, via ``gh``).

The probe is strictly read-only: it never fetches, pushes, writes refs, or
mutates any repository state. All subprocess calls use fixed argv with
``shell=False``. Network lookups (``git ls-remote``, ``gh``) are best effort:
on timeout, missing binary, or auth failure the corresponding field is
``null`` and the probe still exits 0 with the local-only facts.

Usage::

    python tools/upstream_gap.py [--repo-root PATH] [--remote NAME]
                                 [--branch NAME] [--json] [--timeout N]

Exit status is 0 for a successful probe (including ``null`` best-effort
fields) and 2 for usage/repository errors.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any

DEFAULT_REMOTE = "upstream"
DEFAULT_BRANCH = "master"
DEFAULT_TIMEOUT_S = 20.0


def _run(
    argv: tuple[str, ...], *, timeout: float, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a fixed-argv command with shell=False and captured output."""
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"{' '.join(argv)} exited {proc.returncode}: {proc.stderr.strip()[:400]}"
        )
    return proc


def _git(repo: str, *args: str, timeout: float = DEFAULT_TIMEOUT_S) -> str:
    return _run(("git", "-C", repo, *args), timeout=timeout).stdout.strip()


def _highest_remote_tag(remote: str, timeout: float) -> str | None:
    """Best-effort newest tag advertised by ``remote`` (network)."""
    try:
        proc = _run(("git", "ls-remote", "--tags", remote), timeout=timeout, check=False)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    best: tuple[int, int, int] | None = None
    best_ref = None
    for line in proc.stdout.splitlines():
        _sha, ref = (line.split("\t", 1) + [""])[:2]
        ref = ref.strip()
        if not ref.startswith("refs/tags/v"):
            continue
        if ref.endswith("^{}"):
            continue
        parts = ref[len("refs/tags/v") :].split(".")
        try:
            numeric = tuple(int(p) for p in parts)
        except ValueError:
            continue
        if best is None or numeric > best:
            best, best_ref = numeric, ref[len("refs/tags/") :]
    return best_ref


def _open_pull_requests(remote_url: str, timeout: float) -> list[dict[str, Any]] | None:
    """Best-effort open-PR list via the ``gh`` CLI (absent -> None)."""
    if shutil.which("gh") is None:
        return None
    # remote_url like git@github.com:owner/repo.git or https://github.com/owner/repo.git
    tail = remote_url.rstrip("/").split(":")[-1]
    if tail.endswith(".git"):
        tail = tail[: -len(".git")]
    if "/" not in tail:
        return None
    try:
        proc = _run(
            (
                "gh",
                "api",
                f"repos/{tail}/pulls?state=open&per_page=30",
                "--jq",
                ".[] | {number, title, updated_at}",
            ),
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    try:
        rows = json.loads(proc.stdout or "[]")
    except ValueError:
        return None
    return [
        {
            "number": row.get("number"),
            "title": row.get("title"),
            "updated_at": row.get("updated_at"),
        }
        for row in rows
        if isinstance(row, dict)
    ]


def collect(
    repo: str,
    *,
    remote: str = DEFAULT_REMOTE,
    branch: str = DEFAULT_BRANCH,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Gather the upstream gap for ``repo`` without modifying any state."""
    head = _git(repo, "rev-parse", "HEAD", timeout=timeout)
    tracking = f"{remote}/{branch}"
    remote_head = _git(repo, "rev-parse", tracking, timeout=timeout)
    # left = commits only on HEAD, right = commits only on the remote branch.
    left_right = _git(
        repo, "rev-list", "--left-right", "--count", f"{head}...{remote_head}",
        timeout=timeout,
    )
    ahead_only, behind_by = (int(part) for part in left_right.split())
    is_ancestor = _run(
        ("git", "-C", repo, "merge-base", "--is-ancestor", head, remote_head),
        timeout=timeout,
        check=False,
    )
    try:
        local_tag = _git(repo, "describe", "--tags", "--abbrev=0", timeout=timeout)
    except RuntimeError:
        local_tag = None
    try:
        remote_url = _git(repo, "remote", "get-url", remote, timeout=timeout)
    except RuntimeError:
        remote_url = ""
    return {
        "repo": repo,
        "remote": remote,
        "branch": branch,
        "head": head,
        "remote_head": remote_head,
        "ahead_only": ahead_only,
        "behind_by": behind_by,
        "fast_forward_possible": is_ancestor.returncode == 0,
        "local_tag": local_tag,
        "remote_tag": _highest_remote_tag(remote_url or remote, timeout),
        "open_pull_requests": _open_pull_requests(remote_url, timeout)
        if remote_url
        else None,
        "read_only": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only upstream gap probe (never fetches or mutates state)."
    )
    parser.add_argument("--repo-root", default=".", help="Repository checkout (default: cwd)")
    parser.add_argument("--remote", default=DEFAULT_REMOTE, help="Remote name (default: upstream)")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Remote branch (default: master)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--json", action="store_true", help="Emit JSON (default is text)")
    args = parser.parse_args(argv)
    try:
        report = collect(
            args.repo_root,
            remote=args.remote,
            branch=args.branch,
            timeout=args.timeout,
        )
    except (RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"upstream_gap: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    prs = report["open_pull_requests"]
    print(f"head {report['head'][:12]}  {report['remote']}/{report['branch']} {report['remote_head'][:12]}")
    print(
        f"behind by {report['behind_by']} commit(s), {report['ahead_only']} local-only; "
        f"fast-forward possible: {report['fast_forward_possible']}"
    )
    print(f"tags: local {report['local_tag'] or '-'} / remote {report['remote_tag'] or '-'}")
    if prs is None:
        print("open pull requests: unknown (gh unavailable or not authenticated)")
    else:
        print(f"open pull requests: {len(prs)}")
        for pr in prs:
            print(f"  #{pr['number']} {pr['title']}  (updated {pr['updated_at']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
