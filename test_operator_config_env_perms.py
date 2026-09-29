"""Permission tests for the .env writer in operator_config (rm-086).

The .env rewrite must land 0600 regardless of umask, must not widen an
existing 0600 file, and must not leave temp files behind.
"""

from __future__ import annotations

import os
import stat as stat_module

import operator_config


def _mode(path) -> int:
    return stat_module.S_IMODE(os.stat(path).st_mode)


def test_env_write_creates_0600_even_with_loose_umask(tmp_path):
    old_umask = os.umask(0o000)
    try:
        env = tmp_path / ".env"
        operator_config._write_env_key(env, "HERMES_GPT_LOG_LEVEL", "debug")
        assert env.read_text().lstrip().startswith("HERMES_GPT_LOG_LEVEL=")
        assert _mode(env) == 0o600, "new .env must be 0600 under a loose umask"
        assert not list(tmp_path.glob("*.tmp"))
    finally:
        os.umask(old_umask)


def test_env_rewrite_does_not_widen_existing_0600(tmp_path):
    env = tmp_path / ".env"
    env.write_text("EXISTING=1\n")
    os.chmod(env, 0o600)

    operator_config._write_env_key(env, "HERMES_GPT_LOG_LEVEL", "debug")

    text = env.read_text()
    assert "EXISTING=1" in text
    assert "HERMES_GPT_LOG_LEVEL=debug" in text
    assert _mode(env) == 0o600, "rewrite must not widen an existing 0600 .env"
    assert not list(tmp_path.glob("*.tmp"))
