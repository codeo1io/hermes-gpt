"""Regression: env-shebang workers must run inside the Linux sandbox.

Reproduces the self-hosted CI failure (2026-09-02): a worker script whose
shebang is ``#!/usr/bin/env python3`` resolves its interpreter through PATH
*inside* the bubblewrap sandbox. When PATH points at a toolcache Python
outside the read-only bind set, exec fails with 127 and the worker returns
rc 127 instead of doing its job. ``wrap_argv`` must bind the interpreter's
runtime root proactively.
"""

import shutil
import subprocess
import sys

import pytest

import runner_confinement as confinement


@pytest.mark.skipif(
    not sys.platform.startswith("linux") or shutil.which("bwrap") is None,
    reason="Linux bubblewrap confinement required",
)
def test_env_shebang_worker_runs_with_toolcache_python_first_on_path(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    worker = workspace / "worker"
    worker.write_text(
        "#!/usr/bin/env python3\nimport sys; sys.stdout.write('alive\\n')\n",
        encoding="utf-8",
    )
    worker.chmod(0o755)

    # Pathologically small PATH: a *different* python first, /usr/bin last.
    # This mirrors setup-python putting the toolcache interpreter first.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    real_python = shutil.which("python3")
    assert real_python is not None
    (fake_bin / "python3").symlink_to(real_python)

    wrapped = confinement.wrap_argv([str(worker)], workspace, writable=False)
    result = subprocess.run(
        wrapped,
        capture_output=True,
        text=True,
        env={"PATH": f"{fake_bin}:/usr/bin:/bin"},
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "alive" in result.stdout


def test_env_shebang_interpreter_helper_resolves(tmp_path):
    script = tmp_path / "s"
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    resolved = confinement._env_shebang_interpreter(script)
    if shutil.which("python3"):
        assert resolved is not None and resolved.name.startswith("python")


def test_env_shebang_interpreter_helper_ignores_plain_shebang(tmp_path):
    script = tmp_path / "s"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    assert confinement._env_shebang_interpreter(script) is None
