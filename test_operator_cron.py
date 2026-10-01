"""Tests for operator_cron tools using temp profile homes."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

import operator_policy as op
import operator_cron as oc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def hermes_root(tmp_path: Path) -> Path:
    """A fake Hermes root with a default profile and one named profile."""
    root = tmp_path / "hermes"
    (root / "cron").mkdir(parents=True)
    (root / "profiles" / "hermes-researcher" / "cron").mkdir(parents=True)
    (root / "profiles" / "target-profile" / "cron").mkdir(parents=True)
    return root


@pytest.fixture
def clean_env(monkeypatch):
    """Clear all operator env vars and isolate the audit log."""
    for name in [
        op.OPERATOR_ENABLED_ENV,
        op.OPERATOR_LEVEL_ENV,
        op.OPERATOR_APPLY_MODE_ENV,
        op.OPERATOR_ALLOWED_PROFILES_ENV,
        op.OPERATOR_ALLOWED_PATHS_ENV,
        op.OPERATOR_DENIED_PATHS_ENV,
        op.OWNER_ACK_ENV,
    ]:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def audit_override(tmp_path, monkeypatch):
    log = tmp_path / "audit.jsonl"
    op.set_audit_log_override(log)
    yield log
    op.set_audit_log_override(None)


def _make_job(
    job_id: str = "abc123",
    name: str = "test-job",
    prompt: str = "do the thing",
    schedule: str = "every 30m",
    enabled: bool = True,
    state: str = "scheduled",
    last_run_at: str = "2026-01-01T00:00:00",
    last_status: str = "ok",
    last_error: str = "",
    last_delivery_error: str = "",
    paused_at: str = "",
    paused_reason: str = "",
    fire_claim: str = "",
    repeat_completed: int = 3,
    repeat_times: int = 10,
    next_run_at: str = "2026-01-01T00:30:00",
    skills: list[str] | None = None,
    deliver: str = "telegram",
    workdir: str | None = None,
    model: str | None = None,
    provider: str | None = None,
) -> dict:
    return {
        "id": job_id,
        "name": name,
        "prompt": prompt,
        "schedule": schedule,
        "schedule_display": schedule,
        "enabled": enabled,
        "state": state,
        "last_run_at": last_run_at,
        "last_status": last_status,
        "last_error": last_error,
        "last_delivery_error": last_delivery_error,
        "paused_at": paused_at,
        "paused_reason": paused_reason,
        "fire_claim": fire_claim,
        "next_run_at": next_run_at,
        "skills": skills or [],
        "deliver": deliver,
        "workdir": workdir,
        "model": model,
        "provider": provider,
        "repeat": {"times": repeat_times, "completed": repeat_completed},
    }


def _write_jobs(profile_home: Path, jobs: list[dict], *, shape: str = "list") -> None:
    cron_dir = profile_home / "cron"
    cron_dir.mkdir(parents=True, exist_ok=True)
    path = cron_dir / "jobs.json"
    if shape == "dict":
        payload = {"jobs": jobs}
    else:
        payload = jobs
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_cron_jobs_shape_defaults_to_dict_when_missing(hermes_root, clean_env):
    profile_home = hermes_root / "profiles" / "shape-test"
    profile_home.mkdir(parents=True)
    jobs = [_make_job()]
    oc._write_jobs(profile_home, jobs)
    payload = json.loads((profile_home / "cron" / "jobs.json").read_text())
    assert isinstance(payload, dict)
    assert payload["jobs"][0]["id"] == "abc123"


def test_cron_jobs_shape_round_trips_list_and_dict(hermes_root, clean_env):
    profile_home = hermes_root / "profiles" / "shape-roundtrip"
    cron_dir = profile_home / "cron"
    cron_dir.mkdir(parents=True)

    list_jobs = [_make_job(job_id="list-job")]
    (cron_dir / "jobs.json").write_text(json.dumps(list_jobs, indent=2), encoding="utf-8")
    assert len(oc._read_jobs(profile_home)) == 1
    oc._write_jobs(profile_home, list_jobs)
    list_payload = json.loads((cron_dir / "jobs.json").read_text())
    assert isinstance(list_payload, list)
    assert list_payload[0]["id"] == "list-job"

    dict_jobs = [_make_job(job_id="dict-job")]
    (cron_dir / "jobs.json").write_text(json.dumps({"jobs": dict_jobs}, indent=2), encoding="utf-8")
    assert len(oc._read_jobs(profile_home)) == 1
    oc._write_jobs(profile_home, dict_jobs)
    dict_payload = json.loads((cron_dir / "jobs.json").read_text())
    assert isinstance(dict_payload, dict)
    assert dict_payload["jobs"][0]["id"] == "dict-job"


# ---------------------------------------------------------------------------
# read_only: list / status
# ---------------------------------------------------------------------------


def test_cron_list_default_profile_empty(hermes_root, clean_env, audit_override):
    out = oc.hermes_cron_list(profile="default", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["count"] == 0


def test_cron_list_returns_safe_view_no_raw_prompt(hermes_root, clean_env, audit_override):
    job = _make_job(prompt="SECRET_PROMPT_MARKER do the thing")
    _write_jobs(hermes_root, [job])
    out = oc.hermes_cron_list(profile="default", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["count"] == 1
    job_view = parsed["jobs"][0]
    assert "SECRET_PROMPT_MARKER" not in json.dumps(job_view)
    assert job_view["prompt_len"] > 0
    assert job_view["prompt_sha256"]
    assert job_view["job_id"] == "abc123"
    assert job_view["name"] == "test-job"


def test_cron_status_aggregates(hermes_root, clean_env, audit_override):
    jobs = [
        _make_job(job_id="1", name="a", enabled=True, last_error="boom"),
        _make_job(job_id="2", name="b", enabled=False, last_delivery_error="deliv fail"),
        _make_job(job_id="3", name="c", enabled=True),
    ]
    _write_jobs(hermes_root, jobs)
    out = oc.hermes_cron_status(profile="default", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["jobs_count"] == 3
    assert parsed["enabled_count"] == 2
    assert parsed["disabled_count"] == 1
    assert parsed["jobs_with_errors"] == 1
    assert parsed["jobs_with_delivery_errors"] == 1


# ---------------------------------------------------------------------------
# Profile enforcement
# ---------------------------------------------------------------------------


def test_cron_list_refuses_invalid_profile(hermes_root, clean_env, audit_override):
    out = oc.hermes_cron_list(profile="BAD NAME", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "Invalid profile name" in parsed["error"]


def test_cron_list_refuses_nonexistent_profile(hermes_root, clean_env, audit_override):
    out = oc.hermes_cron_list(profile="does-not-exist", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "does not exist" in parsed["error"]


def test_cron_list_refuses_profile_not_in_allowed_list(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default")
    out = oc.hermes_cron_list(profile="hermes-researcher", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "not in the allowed profiles list" in parsed["error"]


def test_cron_list_allows_star_profiles(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "*")
    out = oc.hermes_cron_list(profile="hermes-researcher", hermes_root=hermes_root)
    parsed = json.loads(out)
    assert parsed["success"] is True


# ---------------------------------------------------------------------------
# Mutation gating
# ---------------------------------------------------------------------------


def test_cron_run_refuses_when_operator_disabled(hermes_root, clean_env, audit_override):
    _write_jobs(hermes_root, [_make_job()])
    out = oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=True, hermes_root=hermes_root
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "disabled" in parsed["error"]


def test_cron_run_refuses_in_read_only_mode(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "read_only")
    _write_jobs(hermes_root, [_make_job()])
    out = oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=True, hermes_root=hermes_root
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "does not satisfy required level" in parsed["error"]


def test_cron_run_dry_run_returns_plan(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    _write_jobs(hermes_root, [_make_job()])
    out = oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=True, hermes_root=hermes_root
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["dry_run"] is True
    assert parsed["plan"]["argv"] == ["hermes", "cron", "run", "abc123"]
    assert parsed["plan"]["shell"] is False


def test_cron_run_direct_mode_invokes_runner(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    _write_jobs(hermes_root, [_make_job()])
    captured = {}

    def fake_runner(argv, timeout=120, workdir=None):
        captured["argv"] = argv
        captured["timeout"] = timeout
        return (0, "ok", "")

    out = oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=False,
        hermes_root=hermes_root, runner=fake_runner,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["dry_run"] is False
    assert parsed["returncode"] == 0
    assert captured["argv"] == ["hermes", "cron", "run", "abc123"]
    assert captured["timeout"] == 1800


def test_cron_run_default_runner_raises_only_cron_timeout_cap(
    hermes_root, clean_env, audit_override, monkeypatch
):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    _write_jobs(hermes_root, [_make_job()])
    captured = {}

    def fake_run_argv(argv, *, timeout=120, workdir=None, timeout_cap=600, **_kwargs):
        captured["timeout"] = timeout
        captured["timeout_cap"] = timeout_cap
        return (0, "ok", "")

    monkeypatch.setattr(oc.op, "run_argv", fake_run_argv)
    parsed = json.loads(oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=False,
        hermes_root=hermes_root,
    ))
    assert parsed["success"] is True
    assert captured["timeout"] == 1800
    assert captured["timeout_cap"] == 7200


def test_cron_run_honors_custom_timeout(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    _write_jobs(hermes_root, [_make_job()])
    captured = {}

    def fake_runner(argv, timeout=120, workdir=None):
        captured["timeout"] = timeout
        return (0, "ok", "")

    parsed = json.loads(oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=False, timeout=3600,
        hermes_root=hermes_root, runner=fake_runner,
    ))
    assert parsed["success"] is True
    assert captured["timeout"] == 3600


def test_cron_run_rejects_out_of_range_timeout(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    _write_jobs(hermes_root, [_make_job()])

    parsed = json.loads(oc.hermes_cron_run(
        profile="default", job_id="abc123", dry_run=True, timeout=10,
        hermes_root=hermes_root,
    ))
    assert parsed["success"] is False
    assert "between 30 and 7200 seconds" in parsed["error"]


def test_cron_run_direct_with_named_profile_uses_p_flag(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    _write_jobs(hermes_root / "profiles" / "hermes-researcher", [_make_job()])
    captured = {}

    def fake_runner(argv, timeout=120, workdir=None):
        captured["argv"] = argv
        return (0, "ok", "")

    out = oc.hermes_cron_run(
        profile="hermes-researcher", job_id="abc123", dry_run=False,
        hermes_root=hermes_root, runner=fake_runner,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert captured["argv"] == ["hermes", "-p", "hermes-researcher", "cron", "run", "abc123"]


# ---------------------------------------------------------------------------
# Copy / move
# ---------------------------------------------------------------------------


def test_cron_copy_dry_run_does_not_mutate(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    _write_jobs(hermes_root, [_make_job()])
    target_home = hermes_root / "profiles" / "hermes-researcher"
    # Target cron dir exists from the fixture but jobs.json is not pre-created.

    out = oc.hermes_cron_copy(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", dry_run=True, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["dry_run"] is True
    # Source and target jobs.json unchanged.
    assert len(json.loads((hermes_root / "cron" / "jobs.json").read_text())) == 1
    assert not (target_home / "cron" / "jobs.json").exists()


def test_cron_copy_resets_runtime_fields(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")

    source_job = _make_job(
        last_run_at="2026-01-01T00:00:00",
        last_status="ok",
        last_error="previous boom",
        last_delivery_error="previous deliv fail",
        fire_claim="claim-xyz",
        paused_at="2026-01-02T00:00:00",
        paused_reason="testing",
        repeat_completed=7,
        repeat_times=10,
        next_run_at="2026-01-03T00:00:00",
        skills=["my-skill"],
        deliver="telegram:-100:5",
        model="claude-sonnet-4",
        provider="anthropic",
    )
    _write_jobs(hermes_root, [source_job])
    target_home = hermes_root / "profiles" / "hermes-researcher"
    _write_jobs(target_home, [])

    out = oc.hermes_cron_copy(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    new_id = parsed["new_target_job_id"]
    target_jobs = json.loads((target_home / "cron" / "jobs.json").read_text())
    assert len(target_jobs) == 1
    new_job = target_jobs[0]
    # Preserved.
    assert new_job["name"] == "test-job"
    assert new_job["prompt"] == "do the thing"
    assert new_job["schedule"] == "every 30m"
    assert new_job["skills"] == ["my-skill"]
    assert new_job["deliver"] == "telegram:-100:5"
    assert new_job["model"] == "claude-sonnet-4"
    assert new_job["provider"] == "anthropic"
    assert new_job["repeat"]["times"] == 10
    # Reset / cleared.
    assert new_job["id"] == new_id
    assert new_job["id"] != "abc123"
    assert "last_run_at" not in new_job or new_job.get("last_run_at") is None
    assert "last_status" not in new_job
    assert "last_error" not in new_job
    assert "last_delivery_error" not in new_job
    assert "fire_claim" not in new_job
    assert "paused_at" not in new_job
    assert "paused_reason" not in new_job
    assert "next_run_at" not in new_job
    # repeat.completed is reset (not preserved).
    assert "completed" not in new_job.get("repeat", {}) or new_job["repeat"].get("completed") in (None, 0)
    # state / enabled reset to defaults.
    assert new_job["state"] == "scheduled"
    assert new_job["enabled"] is True


def test_cron_copy_refuses_duplicate(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")

    source_job = _make_job(name="daily-briefing", schedule="every 30m")
    target_dup = _make_job(
        job_id="existing", name="daily-briefing", schedule="every 30m",
        enabled=True,
    )
    _write_jobs(hermes_root, [source_job])
    _write_jobs(hermes_root / "profiles" / "hermes-researcher", [target_dup])

    out = oc.hermes_cron_copy(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "duplicate" in parsed["error"].lower() or "same name" in parsed["error"].lower()
    # Target unchanged.
    target_jobs = json.loads(
        ((hermes_root / "profiles" / "hermes-researcher") / "cron" / "jobs.json").read_text()
    )
    assert len(target_jobs) == 1


def test_cron_move_dry_run_does_not_mutate(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    _write_jobs(hermes_root, [_make_job()])
    # Target cron dir exists from the fixture but jobs.json is not pre-created.

    out = oc.hermes_cron_move(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", dry_run=True, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["dry_run"] is True
    # Source unchanged.
    assert len(json.loads((hermes_root / "cron" / "jobs.json").read_text())) == 1
    # Target still empty.
    target_jobs = (hermes_root / "profiles" / "hermes-researcher" / "cron" / "jobs.json")
    assert not target_jobs.exists()


def test_cron_move_direct_pauses_source_after_copy(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    _write_jobs(hermes_root, [_make_job()])
    _write_jobs(hermes_root / "profiles" / "hermes-researcher", [])

    pause_calls: list[list[str]] = []

    def fake_runner(argv, timeout=120, workdir=None):
        if "pause" in argv:
            pause_calls.append(argv)
            # Simulate Hermes pause: rewrite source jobs.json to set enabled=False.
            if "cron" in argv and "pause" in argv:
                # Find the source profile from -p flag (or default).
                profile = "default"
                if "-p" in argv:
                    profile = argv[argv.index("-p") + 1]
                src_home = (
                    hermes_root if profile == "default"
                    else hermes_root / "profiles" / profile
                )
                jobs = json.loads((src_home / "cron" / "jobs.json").read_text())
                for j in jobs:
                    if str(j.get("id")) == argv[-1]:
                        j["enabled"] = False
                        j["state"] = "paused"
                _write_jobs(src_home, jobs)
            return (0, "ok", "")
        return (0, "ok", "")

    out = oc.hermes_cron_move(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", pause_source=True, test_run_target=False,
        dry_run=False, hermes_root=hermes_root, runner=fake_runner,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["new_target_job_id"]
    assert pause_calls, "pause was not called"
    # Source is paused after the move.
    source_after = json.loads((hermes_root / "cron" / "jobs.json").read_text())
    assert source_after[0]["enabled"] is False


def test_cron_move_copy_success_pause_failure_returns_partial_failure(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    _write_jobs(hermes_root, [_make_job()])
    _write_jobs(hermes_root / "profiles" / "hermes-researcher", [])

    def fake_runner(argv, timeout=120, workdir=None):
        if "pause" in argv:
            return (1, "", "pause failed")
        return (0, "ok", "")

    out = oc.hermes_cron_move(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", pause_source=True, test_run_target=False,
        dry_run=False, hermes_root=hermes_root, runner=fake_runner,
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert parsed["partial"] is True
    assert parsed["new_target_job_id"]
    assert parsed["pause_result"]["success"] is False
    assert parsed["pause_result"]["returncode"] == 1
    target_jobs = json.loads((hermes_root / "profiles" / "hermes-researcher" / "cron" / "jobs.json").read_text())
    assert len(target_jobs["jobs"] if isinstance(target_jobs, dict) else target_jobs) == 1


def test_cron_move_does_not_pause_source_when_copy_fails(hermes_root, clean_env, audit_override, monkeypatch):
    """If the copy step raises, pause_source must NOT happen."""
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    # Create a duplicate in target so copy refuses — pause should not be called.
    src_job = _make_job(name="dup", schedule="every 30m")
    target_dup = _make_job(job_id="existing", name="dup", schedule="every 30m")
    _write_jobs(hermes_root, [src_job])
    _write_jobs(hermes_root / "profiles" / "hermes-researcher", [target_dup])

    pause_called = []

    def fake_runner(argv, timeout=120, workdir=None):
        if "pause" in argv:
            pause_called.append(argv)
        return (0, "ok", "")

    out = oc.hermes_cron_move(
        source_profile="default", target_profile="hermes-researcher",
        job_id="abc123", pause_source=True, dry_run=False,
        hermes_root=hermes_root, runner=fake_runner,
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert pause_called == [], "pause was called even though copy refused"


# ---------------------------------------------------------------------------
# Cron create
# ---------------------------------------------------------------------------


def test_cron_create_refuses_without_schedule(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    out = oc.hermes_cron_create(
        profile="default", schedule="", prompt="do stuff",
        dry_run=True, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "schedule is required" in parsed["error"].lower()


def test_cron_create_refuses_without_prompt_or_skills(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    out = oc.hermes_cron_create(
        profile="default", schedule="every 30m", prompt="",
        dry_run=True, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is False
    assert "prompt, skills, or script" in parsed["error"].lower()


def test_cron_create_dry_run_returns_plan(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    out = oc.hermes_cron_create(
        profile="default", schedule="every 30m", prompt="run report",
        name="my-job", skills=["report-skill"], deliver="telegram",
        repeat=5, dry_run=True, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["dry_run"] is True
    plan = parsed["plan"]
    assert plan["would_create"] is True
    assert plan["name"] == "my-job"
    assert plan["schedule"] == "every 30m"
    assert plan["prompt_len"] == len("run report")
    assert plan["skills"] == ["report-skill"]
    assert plan["deliver"] == "telegram"


def test_cron_create_direct_writes_job(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    out = oc.hermes_cron_create(
        profile="default", schedule="0 9 * * *", prompt="daily briefing",
        name="daily-brief", dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["dry_run"] is False
    assert parsed["profile"] == "default"
    assert parsed["job_id"]
    job = parsed["job"]
    assert job["name"] == "daily-brief"
    assert job["schedule"] == "0 9 * * *"
    assert job["enabled"] is True

    # Operator-created jobs must persist the same structured schedule schema
    # consumed by the native scheduler; raw strings crash claim/run paths.
    jobs = oc._read_jobs(hermes_root)
    assert jobs[0]["schedule"] == {
        "kind": "cron",
        "expr": "0 9 * * *",
        "display": "0 9 * * *",
    }
    assert job["state"] == "scheduled"

    # Verify the job was written to disk.
    jobs = oc._read_jobs(hermes_root)
    assert len(jobs) == 1
    assert jobs[0]["id"] == parsed["job_id"]
    assert jobs[0]["name"] == "daily-brief"


def test_cron_create_direct_with_named_profile(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OPERATOR_ALLOWED_PROFILES_ENV, "default,hermes-researcher")
    target_home = hermes_root / "profiles" / "hermes-researcher"

    out = oc.hermes_cron_create(
        profile="hermes-researcher", schedule="every 1h",
        prompt="check status", name="health-check",
        dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    assert parsed["profile"] == "hermes-researcher"

    jobs = oc._read_jobs(target_home)
    assert len(jobs) == 1
    assert jobs[0]["name"] == "health-check"


def test_cron_create_scheduler_contract_model_fields(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    out = oc.hermes_cron_create(
        profile="default", schedule="every 30m", prompt="run report",
        name="model-job", model_provider="openai", model_name="gpt-5",
        dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    # Scheduler contract: model_name -> string "model", provider alongside it.
    # (the returned job view is redacted; verify the persisted job dict)
    jobs = oc._read_jobs(hermes_root)
    written = next(j for j in jobs if j["id"] == parsed["job_id"])
    assert written["model"] == "gpt-5"
    assert written["provider"] == "openai"
    assert not isinstance(written["model"], dict)
def test_cron_create_model_only_scheduler_contract(hermes_root, clean_env, audit_override, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    out = oc.hermes_cron_create(
        profile="default", schedule="every 1h", prompt="check status",
        name="model-only", model_name="claude-sonnet-4",
        dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True
    jobs = oc._read_jobs(hermes_root)
    written = next(j for j in jobs if j["id"] == parsed["job_id"])
    assert written["model"] == "claude-sonnet-4"
    assert "provider" not in written
    assert not isinstance(written["model"], dict)


def test_cron_create_schedule_parser_is_selfcontained(hermes_root, clean_env, audit_override, monkeypatch):
    """rm-hermes-gpt-standalone: hermes_cron_create must NOT import hermes-agent's
    cron package. hermes-gpt is a standalone distribution; a module-level or
    function-level ``from cron.jobs import ...`` silently bound the PRODUCTION
    hermes-agent install on the self-hosted box and raised ImportError
    (success=False) everywhere hermes-agent is not installed — which killed all
    9 CI lanes (test_cron_create_*, 2026-09-22). The vendored parser must
    produce the canonical scheduler schema without any hermes-agent import."""
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    # 1) The module's source carries no hermes-agent cron import at all.
    source = inspect.getsource(oc)
    assert "from cron.jobs import" not in source
    assert "from cron import" not in source
    # 2) The vendored parser yields the canonical shapes hermes-agent's
    #    scheduler consumes (kind + minutes / expr / run_at).
    interval = oc._parse_schedule("every 30m")
    assert interval == {"kind": "interval", "minutes": 30, "display": "every 30m"}
    expr = oc._parse_schedule("0 9 * * *")
    assert expr["kind"] == "cron" and expr["expr"] == "0 9 * * *"
    once = oc._parse_schedule("in 30m")
    assert once["kind"] == "once" and once["run_at"]
    # 3) End-to-end: create a job with an every-N schedule on a host that has
    #    no hermes-agent on sys.path (this test env) and confirm the persisted
    #    job carries a structured schedule, not the raw string.
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    out = oc.hermes_cron_create(
        profile="default", schedule="every 30m", prompt="run report",
        name="selfcontained-job", dry_run=False, hermes_root=hermes_root,
    )
    parsed = json.loads(out)
    assert parsed["success"] is True, parsed
    jobs = oc._read_jobs(hermes_root)
    written = next(j for j in jobs if j["id"] == parsed["job_id"])
    assert written["schedule"] == {"kind": "interval", "minutes": 30, "display": "every 30m"}
    assert written["schedule_display"] == "every 30m"



def test_corrupt_jobs_json_backed_up_before_overwrite(hermes_root, clean_env):
    """rm-021: an unparseable jobs.json is preserved as a .corrupt-* sidecar
    instead of being silently destroyed by the next atomic write."""
    jobs_file = oc._jobs_file(hermes_root)
    jobs_file.parent.mkdir(parents=True, exist_ok=True)
    corrupt = b'{"jobs": [truncated'
    jobs_file.write_bytes(corrupt)

    assert oc._read_jobs(hermes_root) == []

    backups = sorted(jobs_file.parent.glob("jobs.json.corrupt-*"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == corrupt

    # Repeated reads of the same corrupt payload do not stack duplicates.
    assert oc._read_jobs(hermes_root) == []
    assert sorted(jobs_file.parent.glob("jobs.json.corrupt-*")) == backups

    # Binary / non-UTF-8 corruption (UnicodeDecodeError, not JSONDecodeError)
    # takes the same recovery path: no crash, payload backed up once.
    binary = b"\x80\x81\x82 not utf8"
    jobs_file.write_bytes(binary)
    assert oc._read_jobs(hermes_root) == []
    binary_backups = sorted(jobs_file.parent.glob("jobs.json.corrupt-*"))
    assert len(binary_backups) == 2
    assert binary_backups[-1].read_bytes() == binary
    assert oc._read_jobs(hermes_root) == []
    assert sorted(jobs_file.parent.glob("jobs.json.corrupt-*")) == binary_backups

    # The next atomic write replaces jobs.json; the corrupt payload survives.
    oc._write_jobs(hermes_root, [{"id": "j1", "name": "fresh"}])
    persisted = json.loads(jobs_file.read_text(encoding="utf-8"))
    assert persisted["jobs"][0]["id"] == "j1"
    assert sorted(jobs_file.parent.glob("jobs.json.corrupt-*")) == binary_backups
    assert oc._read_jobs(hermes_root)[0]["id"] == "j1"


def test_write_jobs_uses_unique_fsynced_staging_file(hermes_root: Path):
    """Concurrent writers never share a staging file, and none is left behind."""
    import operator_cron as cron_mod

    for index in range(3):
        cron_mod._write_jobs(hermes_root, [{"id": f"j{index}", "name": f"job{index}"}])
    jobs_file = hermes_root / "cron" / "jobs.json"
    assert json.loads(jobs_file.read_text(encoding="utf-8"))["jobs"][0]["id"] == "j2"
    assert list(jobs_file.parent.glob("*.tmp")) == []


def test_write_jobs_concurrent_writers_never_interleave_or_corrupt(hermes_root: Path):
    """rm-039 regression (concurrency): eight threads racing _write_jobs on
    the same jobs.json always leave one writer's complete payload — never
    an interleaved, truncated, or JSON-invalid document — and no uniquely
    named staging file survives the race."""
    import threading

    import operator_cron as cron_mod

    writers = 8
    rounds = 5
    barrier = threading.Barrier(writers)
    failures: list[Exception] = []

    def _writer(index: int) -> None:
        try:
            barrier.wait(timeout=10)
            for _ in range(rounds):
                cron_mod._write_jobs(hermes_root, [{"id": f"race-{index}", "name": "race"}])
        except Exception as exc:  # pragma: no cover - asserted below
            failures.append(exc)

    threads = [
        threading.Thread(target=_writer, args=(index,)) for index in range(writers)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not failures
    assert not any(thread.is_alive() for thread in threads)

    jobs_file = hermes_root / "cron" / "jobs.json"
    persisted = json.loads(jobs_file.read_text(encoding="utf-8"))
    ids = [job["id"] for job in persisted["jobs"]]
    # exactly one writer's full payload, atomically replaced — never a mix
    assert ids and len(ids) == 1 and ids[0].startswith("race-"), persisted
    assert not list(jobs_file.parent.glob(".*.tmp")), "staging files leaked"


def test_write_jobs_removes_staging_file_on_failure(hermes_root: Path, monkeypatch):
    import operator_cron as cron_mod

    def _boom(payload, fh, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(cron_mod.json, "dump", _boom)
    with pytest.raises(OSError):
        cron_mod._write_jobs(hermes_root, [{"id": "j1", "name": "x"}])
    assert list((hermes_root / "cron").glob("*.tmp")) == []


# --- run bf4db34f cycle 6: NL-grammar truthfulness (rm-138 + rm-057 floor) ---


def test_parse_schedule_rejects_zero_interval():
    """rm-057 floor slice: zero intervals are rejected loudly, never stored as
    minutes=0 — assess F2 empirically created a real 'every 0m' job."""
    for bad in ("every 0m", "0m", "every 0h", "every 0 days", "0 hours"):
        with pytest.raises(ValueError, match="at least 1 minute"):
            oc._parse_schedule(bad)


def test_parse_schedule_accepts_plural_weekdays():
    """rm-138: plural weekday names map like singulars instead of falling
    through to the misleading interval error ("Invalid duration: 'mondays 9am'"
    — the schedule kind parsed fine; only the grammar table was singular)."""
    expr = oc._parse_schedule("every mondays 9am")
    assert expr["kind"] == "cron"
    assert expr["expr"] == "0 9 * * 1"
    # Every weekday has a plural key mapping to the same dow as the singular.
    for singular, plural, dow in (
        ("sunday", "sundays", "0"), ("monday", "mondays", "1"),
        ("tuesday", "tuesdays", "2"), ("wednesday", "wednesdays", "3"),
        ("thursday", "thursdays", "4"), ("friday", "fridays", "5"),
        ("saturday", "saturdays", "6"),
    ):
        assert oc._WEEKDAY_TO_CRON_DOW[singular] == oc._WEEKDAY_TO_CRON_DOW[plural] == dow
    # Mixed plural/singular lists keep their order-unique dow set.
    mixed = oc._parse_schedule("every tuesdays and fri 8:30am")
    assert mixed["expr"] == "30 8 * * 2,5"


# --- run bf4db34f cycle 6: arm-time fire preview (rm-132) ---


def _preview_for(monkeypatch, hermes_root, schedule):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "cron")
    out = oc.hermes_cron_create(
        profile="default", schedule=schedule, prompt="preview probe",
        dry_run=True, hermes_root=hermes_root,
    )
    return json.loads(out)["plan"]["schedule_preview"]


def test_schedule_preview_interval_daily_weekday_and_once(monkeypatch, hermes_root):
    """rm-132: the dry-run plan previews >=3 computed fire times in the
    effective timezone for every schedule kind the grammar accepts."""
    import datetime as _dt

    pv = _preview_for(monkeypatch, hermes_root, "every 30m")
    assert pv["schedule_kind"] == "interval"
    assert len(pv["times"]) >= 3
    assert pv["timezone"] and "UTC" in pv["timezone"]
    t0, t1 = (_dt.datetime.fromisoformat(t) for t in pv["times"][:2])
    assert 25 <= (t1 - t0).total_seconds() / 60 <= 35

    # Daily cron: every previewed fire sits at minute 0 hour 9 local.
    pv = _preview_for(monkeypatch, hermes_root, "0 9 * * *")
    assert pv["schedule_kind"] == "cron"
    assert len(pv["times"]) >= 3
    assert all(t[11:16] == "09:00" for t in pv["times"])

    # Weekday grammar (the rm-138 plural path) previews through the same key.
    pv = _preview_for(monkeypatch, hermes_root, "every mondays 9am")
    assert pv["schedule_kind"] == "cron"
    assert len(pv["times"]) >= 3

    # One-shot: exactly one fire, labeled as such.
    pv = _preview_for(monkeypatch, hermes_root, "in 30m")
    assert pv["schedule_kind"] == "once"
    assert len(pv["times"]) == 1
    assert "once" in pv["note"]


def test_schedule_preview_declares_tz_environment(monkeypatch, hermes_root):
    """rm-132: with TZ set in the environment the preview declares the zone it
    resolved against — 'once at HH:MM' stops being an implicit tz guess."""
    import time as _time

    if not hasattr(_time, "tzset"):
        pytest.skip("time.tzset unavailable on this platform")
    monkeypatch.setenv("TZ", "UTC")
    _time.tzset()
    try:
        pv = _preview_for(monkeypatch, hermes_root, "every 45m")
    finally:
        monkeypatch.delenv("TZ", raising=False)
        _time.tzset()
    assert "UTC" in pv["timezone"]
    assert len(pv["times"]) >= 3


# --- run bf4db34f cycle 6: property-based grammar invariants (rm-138) ---
# hypothesis is a declared dev-group dependency (pyproject [dependency-groups]
# and [project.optional-dependencies].dev). The lane skips cleanly where the
# package is absent rather than failing the suite.

def test_cron_grammar_property_invariants():
    """rm-138: property-based lane pinning the schedule grammar's truthfulness
    invariants across generated inputs (derandomized: fixed outcome per run)."""
    pytest.importorskip("hypothesis")
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st

    # deadline=None + too_slow suppression keep the lane load-robust on the
    # shared fleet host: input generation here is intrinsically fast, but a
    # CPU-starved worker (suite admitted at workers=1 under load1~24) misses
    # hypothesis's default 200ms/example deadline and 5s data-generation
    # health check without any real invariant violation (proven: run
    # bf4db34f targeted_tests attempt 718e3b7b, FailedHealthCheck.too_slow
    # with 8 draws in 5.46s). Assertions and 100-example coverage unchanged.

    weekdays = st.sampled_from(
        ["sunday", "sundays", "sun", "monday", "mondays", "mon",
         "tuesday", "tuesdays", "tue", "tues", "wednesday", "wednesdays", "wed",
         "thursday", "thursdays", "thu", "friday", "fridays", "fri",
         "saturday", "saturdays", "sat"]
    )
    hours = st.integers(min_value=0, max_value=23)
    minutes = st.integers(min_value=0, max_value=59)

    @settings(max_examples=100, derandomize=True, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(weekday=weekdays, hour=hours, minute=minutes)
    def weekday_grammar_produces_valid_cron(weekday, hour, minute):
        hhmm = f"{hour:02d}:{minute:02d}"
        parsed = oc._parse_schedule(f"every {weekday} {hhmm}")
        assert parsed["kind"] == "cron", parsed
        assert oc._croniter(parsed["expr"]) is not None
        # The fire time the user wrote is the fire time the expr encodes.
        fields = parsed["expr"].split()
        assert fields[0] == str(minute) and fields[1] == str(hour)

    @settings(max_examples=100, derandomize=True, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(minutes=st.integers(min_value=1, max_value=100_000))
    def interval_floor_never_yields_zero(minutes):
        parsed = oc._parse_schedule(f"every {minutes}m")
        assert parsed["kind"] == "interval"
        assert parsed["minutes"] == minutes >= 1  # rm-057 floor invariant

    def zero_intervals_always_rejected():
        # Any zero duration must be rejected loudly, never stored (rm-057).
        for unit in ("m", "h", "d"):
            with pytest.raises(ValueError, match="at least 1 minute"):
                oc._parse_schedule(f"every 0{unit}")

    weekday_grammar_produces_valid_cron()
    interval_floor_never_yields_zero()
    zero_intervals_always_rejected()
