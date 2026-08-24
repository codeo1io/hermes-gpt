from pathlib import Path
import re


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one exact anchor, got {text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_func(path, name, replacement):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    pat = re.compile(rf"^def {re.escape(name)}\(.*?(?=^def |^# -{{5,}}|\Z)", re.M | re.S)
    matches = list(pat.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{path}: expected one function {name}, got {len(matches)}")
    match = matches[0]
    p.write_text(text[:match.start()] + replacement.rstrip() + "\n\n" + text[match.end():], encoding="utf-8")


replace_once(
    "operator_job_supervisor.py",
    'TERMINAL_STATES = frozenset({"completed", "failed", "cancelled", "timed_out"})\n_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")\n',
    'TERMINAL_STATES = frozenset({"completed", "failed", "cancelled", "timed_out"})\nIS_WINDOWS = os.name == "nt"\n_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")\n',
)

p = Path("operator_job_supervisor.py")
text = p.read_text(encoding="utf-8")
if text.count('if os.name == "nt":') != 4:
    raise SystemExit('operator_job_supervisor.py: expected four os.name Windows branches')
p.write_text(text.replace('if os.name == "nt":', 'if IS_WINDOWS:'), encoding="utf-8")

replace_once(
    "operator_job_supervisor.py",
    '''    if Path("/proc").is_dir():
        identity = _procfs_identity(pid)
        if identity is not None:
            return identity
    return _ps_identity(pid)
''',
    '''    # On Linux procfs is authoritative for process existence and identity.
    # If /proc/<pid> vanished, do not fall through to an external ``ps`` probe;
    # that only creates a race and makes tests that stub Popen affect identity.
    if Path("/proc").is_dir():
        return _procfs_identity(pid)
    return _ps_identity(pid)
''',
)

replace_func(
    "test_operator_runners.py",
    "test_runner_cancel_routes_pid_to_tree_cleanup_and_terminalizes_job",
    '''def test_runner_cancel_refuses_unverified_legacy_pid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ws = tmp_path / "ws"
    root = tmp_path / "hermes"
    ws.mkdir()
    root.mkdir()
    _enable_workspace(monkeypatch, ws)
    task_id = "runner-cancel-tree"
    meta_path, _, _ = runners._job_paths(task_id, root)
    runners._atomic_json(meta_path, {
        "schema_version": runners.SCHEMA_VERSION,
        "task_id": task_id,
        "backend": "pi_rpc",
        "state": "running",
        "outcome": "running",
        "workspace": str(ws),
        "pid": 4242,
        "ended_at": None,
    })
    terminated = []
    monkeypatch.setattr(
        runners,
        "_terminate_process_tree",
        lambda target, timeout=5.0: terminated.append((target, timeout)),
    )

    payload = json.loads(
        runners.hermes_runner_cancel(
            task_id,
            backend="pi_rpc",
            confirm=True,
            dry_run=False,
            hermes_root=root,
        )
    )

    assert payload["success"] is False
    assert payload["code"] == "JOB_PROCESS_UNVERIFIABLE"
    assert terminated == []
    stored = json.loads(meta_path.read_text(encoding="utf-8"))
    assert stored["state"] == "running"
    assert stored["outcome"] == "running"''',
)

replace_func(
    "test_operator_runners.py",
    "test_windows_backend_cancel_uses_taskkill_tree_and_marks_cancelled",
    '''def test_backend_cancel_uses_shared_supervisor_and_marks_source_cancelled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    task_id = "runner-cancel-supervised"
    meta_path = tmp_path / "job.json"
    request_path = tmp_path / "request.json"
    log_path = tmp_path / "events.jsonl"
    cancel_path = tmp_path / "cancel.json"
    runners._atomic_json(meta_path, {
        "schema_version": runners.SCHEMA_VERSION,
        "task_id": task_id,
        "backend": "pi_rpc",
        "state": "running",
        "outcome": "running",
        "workspace": str(tmp_path),
        "pid": 4343,
        "ended_at": None,
    })
    monkeypatch.setattr(
        runners,
        "_job_paths",
        lambda task_id, hermes_root=None: (meta_path, request_path, log_path),
    )
    monkeypatch.setattr(
        runners,
        "_cancel_path",
        lambda task_id, hermes_root=None: cancel_path,
    )
    calls = []
    monkeypatch.setattr(
        runners.job_supervisor,
        "request_cancel",
        lambda task_id, hermes_root=None: calls.append((task_id, hermes_root)) or {
            "success": True,
            "changed": True,
            "status": "cancelled",
        },
    )

    result = runners.PiRpcBackend().cancel(task_id, hermes_root=tmp_path)

    assert result["success"] is True
    assert result["state"] == "cancelled"
    assert calls == [(task_id, tmp_path)]
    stored = json.loads(meta_path.read_text(encoding="utf-8"))
    assert stored["state"] == "cancelled"
    assert stored["outcome"] == "cancelled"
    assert stored["ended_at"]''',
)

p = Path("test_operator_job_supervisor.py")
text = p.read_text(encoding="utf-8")
append = r'''


def test_windows_cancel_uses_taskkill_only_after_identity_verification(monkeypatch, tmp_path):
    jobs.register_job(
        "task-win-cancel",
        backend="pi_rpc",
        workspace=tmp_path,
        log_path=tmp_path / "runner-jobs" / "task-win-cancel.jsonl",
        source_record=tmp_path / "runner-jobs" / "task-win-cancel.json",
        hermes_root=tmp_path,
    )
    record_path = tmp_path / "job-supervisor" / "task-win-cancel.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record.update(
        {
            "status": "running",
            "pid": 4343,
            "process_identity": {
                "platform": "windows-cim",
                "start_token": "20260824010101.000000+000",
                "cmdline_sha256": "c" * 64,
            },
        }
    )
    jobs._atomic_json(record_path, record)
    monkeypatch.setattr(jobs, "IS_WINDOWS", True)
    monkeypatch.setattr(jobs, "verify_process", lambda pid, expected: True)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return jobs.subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(jobs.subprocess, "run", fake_run)
    result = jobs.request_cancel("task-win-cancel", hermes_root=tmp_path)

    assert result["success"] is True
    assert result["status"] == "cancelled"
    assert calls == [["taskkill", "/PID", "4343", "/T", "/F"]]
    stored = jobs.get_job("task-win-cancel", hermes_root=tmp_path, reconcile=False)
    assert stored is not None
    assert stored["status"] == "cancelled"
'''
if "def test_windows_cancel_uses_taskkill_only_after_identity_verification" in text:
    raise SystemExit("test_operator_job_supervisor.py: windows test already present")
p.write_text(text.rstrip() + append + "\n", encoding="utf-8")

print("issue #57 CI follow-up anchors applied")
