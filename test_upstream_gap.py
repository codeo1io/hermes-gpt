"""Focused tests for tools/upstream_gap.py (rm-115) against a local fixture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import upstream_gap  # noqa: E402


def _git(repo: str, *args: str) -> str:
    proc = subprocess.run(("git", "-C", repo, *args), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _make_fixture(tmp_path: Path) -> str:
    """A clone with a local 'upstream' bare remote, 2 commits behind and 1 ahead."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(str(origin), "init", "--bare", "--initial-branch=master")
    work = tmp_path / "work"
    work.mkdir()
    _git(str(work), "init", "--initial-branch=master")
    _git(str(work), "config", "user.email", "t@example.com")
    _git(str(work), "config", "user.name", "T")
    (work / "f.txt").write_text("1\n")
    _git(str(work), "add", ".")
    _git(str(work), "commit", "-m", "c1")
    (work / "f.txt").write_text("2\n")
    _git(str(work), "commit", "-am", "c2")
    _git(str(work), "tag", "v0.11.0")
    _git(str(work), "remote", "add", "origin", str(origin))
    _git(str(work), "push", "-q", "origin", "master", "--tags")
    # Upstream advances by two commits (including a newer tag).
    upstream_work = tmp_path / "upstream-work"
    subprocess.run(
        ("git", "clone", "-q", str(origin), str(upstream_work)), check=True, capture_output=True
    )
    _git(str(upstream_work), "config", "user.email", "t@example.com")
    _git(str(upstream_work), "config", "user.name", "T")
    (upstream_work / "g.txt").write_text("x\n")
    _git(str(upstream_work), "add", ".")
    _git(str(upstream_work), "commit", "-m", "u1")
    _git(str(upstream_work), "tag", "v0.12.0")
    (upstream_work / "h.txt").write_text("y\n")
    _git(str(upstream_work), "add", ".")
    _git(str(upstream_work), "commit", "-m", "u2")
    _git(str(upstream_work), "push", "-q", "origin", "master", "--tags")
    # Local clone fetches upstream state and adds one local-only commit.
    _git(str(work), "fetch", "-q", "origin")
    _git(str(work), "remote", "rename", "origin", "upstream")
    (work / "local.txt").write_text("z\n")
    _git(str(work), "add", ".")
    _git(str(work), "commit", "-m", "local-only")
    return str(work)


def test_collect_reports_gap_tags_and_ancestry(tmp_path, monkeypatch):
    repo = _make_fixture(tmp_path)
    # Offline-deterministic: no gh lookups, ls-remote stays local-path.
    monkeypatch.setattr(upstream_gap, "_open_pull_requests", lambda url, timeout: None)
    before = _git(repo, "status", "--porcelain")

    report = upstream_gap.collect(repo, remote="upstream", branch="master")

    assert report["read_only"] is True
    assert report["behind_by"] == 2, report
    assert report["ahead_only"] == 1, report
    assert report["fast_forward_possible"] is False, report  # local-only commit exists
    assert report["local_tag"] == "v0.11.0"
    assert report["remote_tag"] == "v0.12.0"
    assert report["open_pull_requests"] is None
    assert _git(repo, "status", "--porcelain") == before, "probe must not mutate the repo"
    # The remote-tracking ref must be untouched (no implicit fetch).
    assert _git(repo, "rev-parse", "upstream/master") == report["remote_head"]


def test_fast_forward_case_reports_true(tmp_path, monkeypatch):
    repo = _make_fixture(tmp_path)
    monkeypatch.setattr(upstream_gap, "_open_pull_requests", lambda url, timeout: None)
    _git(repo, "reset", "-q", "--hard", "upstream/master^")  # strictly behind
    report = upstream_gap.collect(repo)
    assert report["fast_forward_possible"] is True
    assert report["ahead_only"] == 0


def test_main_json_output_exits_zero(tmp_path, monkeypatch, capsys):
    repo = _make_fixture(tmp_path)
    monkeypatch.setattr(upstream_gap, "_open_pull_requests", lambda url, timeout: None)
    monkeypatch.chdir(repo)
    code = upstream_gap.main(["--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["behind_by"] == 2 and payload["read_only"] is True


def test_open_prs_parses_one_object_per_line(monkeypatch):
    """gh api --jq '.[] | {...}' emits ONE JSON object PER LINE.

    A whole-buffer json.loads raises "Extra data" with two or more objects
    (and iterating a single parsed dict yields its keys), which previously
    surfaced as ``open_pull_requests = None``/empty even with open PRs.
    """
    monkeypatch.setattr(upstream_gap.shutil, "which", lambda name: "/usr/bin/gh")
    stubs = [
        subprocess.CompletedProcess(
            args=(),
            returncode=0,
            stdout=(
                '{"number": 85, "title": "A", "updated_at": "t1"}\n'
                '{"number": 86, "title": "B", "updated_at": "t2"}\n'
            ),
        ),
        subprocess.CompletedProcess(
            args=(),
            returncode=0,
            stdout='{"number": 87, "title": "C", "updated_at": "t3"}\n',
        ),
    ]
    calls = iter(stubs)
    monkeypatch.setattr(
        upstream_gap, "_run", lambda argv, *, timeout, check=False: next(calls)
    )
    two = upstream_gap._open_pull_requests("https://github.com/owner/repo.git", 1.0)
    assert [row["number"] for row in two] == [85, 86]
    one = upstream_gap._open_pull_requests("https://github.com/owner/repo.git", 1.0)
    assert [row["number"] for row in one] == [87]


def test_collect_flags_unadopted_upstream_tag(tmp_path, monkeypatch, capsys):
    repo = _make_fixture(tmp_path)
    monkeypatch.setattr(upstream_gap, "_open_pull_requests", lambda url, timeout: None)
    report = upstream_gap.collect(repo, remote="upstream", branch="master")
    assert report["local_tag"] == "v0.11.0"
    assert report["remote_tag"] == "v0.12.0"
    assert report["upstream_tag_not_adopted"] is True
    assert upstream_gap.main(["--repo-root", repo]) == 0
    assert "upstream tag not adopted: v0.12.0 commit is not contained in HEAD" in (
        capsys.readouterr().out
    )


def test_unadopted_flag_when_tag_object_absent_locally(monkeypatch):
    """An upstream tag the fork never fetched counts as not adopted."""
    monkeypatch.setattr(
        upstream_gap,
        "_run",
        lambda argv, *, timeout, check=False: subprocess.CompletedProcess(
            args=argv, returncode=1, stdout="", stderr=""
        ),
    )
    assert (
        upstream_gap._collect_unadopted_flag("/repo", "v0.13.0", "abc", timeout=1.0)
        is True
    )


def test_collect_no_flag_when_remote_tag_adopted(tmp_path, monkeypatch, capsys):
    repo = _make_fixture(tmp_path)
    monkeypatch.setattr(upstream_gap, "_open_pull_requests", lambda url, timeout: None)
    _git(repo, "reset", "-q", "--hard", "v0.12.0")  # HEAD carries the remote tag
    report = upstream_gap.collect(repo, remote="upstream", branch="master")
    assert report["local_tag"] == "v0.12.0"
    assert report["upstream_tag_not_adopted"] is False
    assert upstream_gap.main(["--repo-root", repo, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["upstream_tag_not_adopted"] is False


def test_main_text_output_and_error_path(tmp_path, monkeypatch, capsys):
    repo = _make_fixture(tmp_path)
    monkeypatch.setattr(upstream_gap, "_open_pull_requests", lambda url, timeout: None)
    assert upstream_gap.main(["--repo-root", repo]) == 0
    text = capsys.readouterr().out
    assert "behind by 2" in text and "fast-forward possible: False" in text
    assert upstream_gap.main(["--repo-root", str(tmp_path / "missing")]) == 2
