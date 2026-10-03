"""Unit tests for tools/upstream_delta.py (rm-107).

Fixture-repo based: all git operations run against local paths — the tests
never touch the network (the PyPI probe is skipped via allow_network=False /
--no-network).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


TOOLS_DIR = Path(__file__).resolve().parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import upstream_delta as ud  # noqa: E402


GIT_IDENTITY = [
    "-c",
    "user.name=Test",
    "-c",
    "user.email=test@example.invalid",
]


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *GIT_IDENTITY, *args],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"git {args}: {proc.stderr}"
    return proc.stdout.strip()


def _commit(repo: Path, filename: str, content: str = "x\n") -> str:
    (repo / filename).write_text(content, encoding="utf-8")
    _git(repo, "add", filename)
    _git(repo, "commit", "-m", f"add {filename}")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo_pair(tmp_path: Path):
    """An upstream repo and a working clone that is ahead 2 / behind 1."""
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "-b", "master")
    base = _commit(upstream, "base.txt")

    work = tmp_path / "work"
    subprocess.run(
        ["git", "clone", str(upstream), str(work)],
        capture_output=True,
        text=True,
        check=True,
    )
    _git(work, "remote", "add", "upstream", str(upstream))

    # Upstream advances (work is now behind by one) and tags a release.
    _commit(upstream, "upstream-only.txt")
    _git(upstream, "tag", "v0.12.0")

    _git(work, "fetch", "upstream")
    _commit(work, "local-1.txt")
    head = _commit(work, "local-2.txt")

    return {"upstream": upstream, "work": work, "base": base, "head": head}


def test_collect_delta_counts_ahead_behind_and_merge_base(repo_pair):
    report = ud.collect_delta(
        repo_pair["work"], upstream="upstream", allow_network=False,
        symbols=["base"],
    )
    assert report.head == repo_pair["head"]
    assert report.merge_base == repo_pair["base"]
    assert report.ahead == 2
    assert report.behind == 1
    assert report.upstream_head  # ls-remote HEAD resolved
    assert report.upstream_head != report.head


def test_collect_delta_reports_upstream_tags(repo_pair):
    report = ud.collect_delta(
        repo_pair["work"], upstream="upstream", allow_network=False, symbols=[],
    )
    assert report.tags == ["v0.12.0"]
    assert report.latest_tag == "v0.12.0"


def test_collect_delta_symbol_census(repo_pair):
    (repo_pair["work"] / "surface.py").write_text(
        "def hermes_cron_create():\n    return 1\n\nhermes_cron_create()\n",
        encoding="utf-8",
    )
    _git(repo_pair["work"], "add", "surface.py")
    _git(repo_pair["work"], "commit", "-m", "surface")
    report = ud.collect_delta(
        repo_pair["work"],
        upstream="upstream",
        allow_network=False,
        symbols=["hermes_cron_create", "never_present_anywhere"],
    )
    assert report.symbol_census["hermes_cron_create"] == 2  # def + call site
    assert report.symbol_census["never_present_anywhere"] == 0
    assert report.missing_symbols == ["never_present_anywhere"]


def test_collect_delta_no_network_marks_pypi_skipped(repo_pair):
    report = ud.collect_delta(
        repo_pair["work"], upstream="upstream", allow_network=False, symbols=[],
    )
    assert report.pypi_version == "skipped (--no-network)"


def test_render_text_includes_sections_and_missing(repo_pair):
    report = ud.collect_delta(
        repo_pair["work"],
        upstream="upstream",
        allow_network=False,
        symbols=["never_present_anywhere"],
    )
    text = ud.render_text(report)
    assert "merge-base:" in text
    assert "ahead/behind:    2 / 1" in text
    assert "PyPI latest:     skipped" in text
    assert "MISSING SYMBOLS: never_present_anywhere" in text


def test_main_json_emits_parseable_report(repo_pair, capsys, monkeypatch):
    monkeypatch.chdir(repo_pair["work"])  # --repo defaults to cwd
    rc = ud.main(["--json", "--no-network", "--symbols", "base"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["ahead"] == 2
    assert data["behind"] == 1
    assert data["merge_base"] == repo_pair["base"]
    assert data["pypi_version"] == "skipped (--no-network)"
    # The census counts symbol occurrences in tracked *.py files only —
    # "base" is a tracked FILE name, not a Python symbol: reported missing.
    assert data["symbol_census"] == {"base": 0}
    assert data["missing_symbols"] == ["base"]


def test_main_exit_1_without_upstream_remote(tmp_path, capsys):
    repo = tmp_path / "lonely"
    repo.mkdir()
    _git(repo, "init", "-b", "master")
    _commit(repo, "only.txt")
    rc = ud.main(["--repo", str(repo), "--no-network", "--symbols", ""])
    err = capsys.readouterr().err
    assert rc == 1
    assert "upstream" in err


def test_main_help_documents_exit_codes(capsys):
    with pytest.raises(SystemExit) as exc:
        ud.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "exit codes" in out
    assert "0" in out and "1" in out and "2" in out


def test_tag_sort_key_prefers_higher_patch():
    assert ud._tag_sort_key("v0.13.0") > ud._tag_sort_key("v0.9.7")
    assert ud._tag_sort_key("v0.12.0") < ud._tag_sort_key("v0.12.10")


def test_latest_tag_prefers_version_tags_over_archive_prefixes(repo_pair):
    _git(repo_pair["upstream"], "tag", "archive/feat-something-20260626-211946")
    report = ud.collect_delta(
        repo_pair["work"], upstream="upstream", allow_network=False, symbols=[],
    )
    assert "archive/feat-something-20260626-211946" in report.tags
    assert report.latest_tag == "v0.12.0"


def test_git_error_surface_is_raised(tmp_path):
    with pytest.raises(ud.GitError):
        ud.collect_delta(tmp_path, upstream="upstream", allow_network=False, symbols=[])
