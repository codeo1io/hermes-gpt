import json
import subprocess

import updater


def completed(argv, stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


class GitRunner:
    def __init__(self, *, dirty: str = "", updated: bool = False):
        self.dirty = dirty
        self.updated = updated
        self.calls: list[list[str]] = []
        self.rev_calls = 0

    def __call__(self, argv, cwd, timeout):
        self.calls.append(argv)
        if argv[:3] == ["git", "status", "--porcelain"]:
            return completed(argv, self.dirty)
        if argv == ["git", "branch", "--show-current"]:
            return completed(argv, "master\n")
        if argv[:3] == ["git", "symbolic-ref", "--quiet"]:
            return completed(argv, "origin/master\n")
        if argv == ["git", "rev-parse", "HEAD"]:
            self.rev_calls += 1
            return completed(argv, ("b" * 40 if self.updated and self.rev_calls > 1 else "a" * 40) + "\n")
        if argv[:3] == ["git", "ls-remote", "--heads"]:
            return completed(argv, "b" * 40 + "\trefs/heads/master\n")
        if argv[:3] == ["git", "fetch", "--prune"]:
            return completed(argv)
        if argv[:3] == ["git", "merge", "--ff-only"]:
            return completed(argv)
        raise AssertionError(f"Unexpected command: {argv}")


def test_git_update_checks_only_by_default(tmp_path):
    runner = GitRunner()
    result = updater._source_update(root=tmp_path, apply=False, runner=runner)
    assert result["ok"] is True
    assert result["update_available"] is True
    assert result["applied"] is False
    assert result["next_command"] == "hermes-gpt update --apply"
    assert not any(call[1] in {"fetch", "merge"} for call in runner.calls)


def test_git_update_refuses_tracked_changes(tmp_path):
    runner = GitRunner(dirty=" M server.py\n")
    result = updater._source_update(root=tmp_path, apply=True, runner=runner)
    assert result["ok"] is False
    assert result["code"] == "WORKTREE_DIRTY"
    assert len(runner.calls) == 1


def test_git_check_still_reports_an_update_when_tracked_changes_exist(tmp_path):
    runner = GitRunner(dirty=" M server.py\n")
    result = updater._source_update(root=tmp_path, apply=False, runner=runner)
    assert result["ok"] is True
    assert result["update_available"] is True
    assert result["tracked_changes_present"] is True
    assert "apply_blocked_by" in result


def test_git_update_applies_only_a_fast_forward(tmp_path):
    runner = GitRunner(updated=True)
    result = updater._source_update(root=tmp_path, apply=True, runner=runner)
    assert result["ok"] is True
    assert result["applied"] is True
    assert result["current_revision"] == "b" * 40
    assert ["git", "fetch", "--prune", "origin", "master"] in runner.calls
    assert ["git", "merge", "--ff-only", "origin/master"] in runner.calls


def test_pip_update_checks_only_until_apply(monkeypatch):
    calls = []

    def runner(argv, cwd, timeout):
        calls.append(argv)
        if argv[2:4] == ["pip", "index"]:
            return completed(argv, "hermes-gpt (0.5.0)\nAvailable versions: 0.5.0, 0.4.0\n")
        if argv[2:4] == ["pip", "install"]:
            return completed(argv, "Successfully installed hermes-gpt-0.5.0\n")
        raise AssertionError(argv)

    monkeypatch.setattr(updater, "_current_version", lambda source_root: "0.4.0")
    checked = updater._pip_update(apply=False, include_prereleases=False, runner=runner)
    assert checked["ok"] is True
    assert checked["update_available"] is True
    assert checked["applied"] is False
    assert not any(command[3] == "install" for command in calls)

    applied = updater._pip_update(apply=True, include_prereleases=False, runner=runner)
    assert applied["ok"] is True
    assert applied["applied"] is True
    assert applied["restart_required"] is True
    assert any(command[3] == "install" for command in calls)


def test_pip_updater_never_downgrades(monkeypatch):
    def runner(argv, cwd, timeout):
        assert argv[2:4] == ["pip", "index"]
        return completed(argv, "hermes-gpt (0.4.0)\nAvailable versions: 0.4.0\n")

    monkeypatch.setattr(updater, "_current_version", lambda source_root: "0.5.0b2")
    result = updater._pip_update(apply=True, include_prereleases=False, runner=runner)
    assert result["ok"] is True
    assert result["update_available"] is False
    assert result["applied"] is False


def test_update_cli_emits_check_result(monkeypatch, capsys):
    monkeypatch.setattr(updater, "check_for_update", lambda **kwargs: {"ok": True, **kwargs})
    updater.main(["--pre"])
    result = json.loads(capsys.readouterr().out)
    assert result == {"ok": True, "apply": False, "include_prereleases": True}


class TopLevelRunner(GitRunner):
    """GitRunner that first answers ``git rev-parse --show-toplevel`` with a chosen root."""

    def __init__(self, toplevel):
        super().__init__()
        self.toplevel = toplevel

    def __call__(self, argv, cwd, timeout):
        if argv[:2] == ["git", "rev-parse"] and "--show-toplevel" in argv:
            self.calls.append(argv)
            return completed(argv, str(self.toplevel) + "\n")
        return super().__call__(argv, cwd, timeout)


def test_check_for_update_refuses_a_foreign_git_root(tmp_path):
    foreign = tmp_path / "unrelated-repo"
    foreign.mkdir()
    (foreign / "pyproject.toml").write_text('name = "someone-else"\nversion = "1.0.0"\n', encoding="utf-8")
    runner = TopLevelRunner(foreign)
    for apply in (False, True):
        runner.calls.clear()
        result = updater.check_for_update(apply=apply, start=foreign / "site-packages", runner=runner)
        assert result["ok"] is False
        assert result["code"] == "NOT_A_HERMES_GPT_CHECKOUT"
        assert result["repository"] == str(foreign)
        assert runner.calls == [["git", "rev-parse", "--show-toplevel"]]
        assert not any("pip" in " ".join(call) for call in runner.calls)


def test_check_for_update_refuses_a_git_root_without_a_declaring_pyproject(tmp_path):
    bare = tmp_path / "not-a-package-root"
    bare.mkdir()
    runner = TopLevelRunner(bare)
    result = updater.check_for_update(apply=True, start=bare, runner=runner)
    assert result["ok"] is False
    assert result["code"] == "NOT_A_HERMES_GPT_CHECKOUT"


def test_check_for_update_accepts_a_hermes_gpt_checkout(tmp_path):
    checkout = tmp_path / "hermes-gpt"
    checkout.mkdir()
    (checkout / "pyproject.toml").write_text('name = "hermes-gpt"\nversion = "0.10.0"\n', encoding="utf-8")
    runner = TopLevelRunner(checkout)
    result = updater.check_for_update(start=checkout / "site-packages", runner=runner)
    assert result["ok"] is True
    assert result["mode"] == "git"
    assert ["git", "status", "--porcelain", "--untracked-files=no"] in runner.calls
