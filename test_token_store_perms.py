"""Secret-path permission and atomic-write tests for token_store (rm-086).

Covers: key file / envelope created 0600 from the first byte (no
umask-window), secrets directory created 0700, collision-free temp names
(no shared fixed ``.tmp``/``.new``), and WAL sidecar files clamped to 0600.
"""

from __future__ import annotations

import os
import stat as stat_module

import token_store


def _mode(path) -> int:
    return stat_module.S_IMODE(os.stat(path).st_mode)


def _force_keyfile_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(token_store, "_key_from_env", lambda: None)
    monkeypatch.setattr(token_store, "_key_from_keyring", lambda: None)
    monkeypatch.setattr(token_store, "_store_key_in_keyring", lambda key: False)
    return tmp_path


def test_save_tokens_private_modes_and_no_leftovers(tmp_path, monkeypatch):
    root = _force_keyfile_backend(tmp_path, monkeypatch)
    result = token_store.save_tokens(root, {"access_token": "x"})
    assert result["source"] == "keyfile"

    secrets_dir = root / "secrets"
    assert _mode(secrets_dir) == 0o700
    assert _mode(secrets_dir / "hermes_gpt_token_key") == 0o600
    assert _mode(secrets_dir / "hermes_gpt_tokens.json") == 0o600
    assert not list(secrets_dir.glob("*.tmp"))
    assert not list(secrets_dir.glob("*.new"))


def _install_secret_mode_spies(monkeypatch):
    """Record every secret-path file's mode at the moment it is chmod'ed
    (pre-fix, that is AFTER a umask-default create+write — the exposure
    window) and its mode at rename time (must already be 0600)."""
    observed_at_chmod = []
    observed_at_rename = []
    real_chmod = os.chmod
    real_replace = os.replace

    def _is_secret_path(value) -> bool:
        text = str(value)
        return (
            "hermes_gpt_token_key" in text
            or "hermes_gpt_tokens.json" in text
            or text.endswith((".tmp", ".new"))
        )

    def spy_chmod(path, mode, **kwargs):
        if _is_secret_path(path):
            observed_at_chmod.append(_mode(path))
        real_chmod(path, mode, **kwargs)

    def spy_replace(src, dst):
        if _is_secret_path(src):
            observed_at_rename.append(_mode(src))
        real_replace(src, dst)

    monkeypatch.setattr(os, "chmod", spy_chmod)
    monkeypatch.setattr(os, "replace", spy_replace)
    return observed_at_chmod, observed_at_rename


def test_secret_tmp_files_never_wider_than_0600(tmp_path, monkeypatch):
    root = _force_keyfile_backend(tmp_path, monkeypatch)
    at_chmod, at_rename = _install_secret_mode_spies(monkeypatch)

    token_store.save_tokens(root, {"access_token": "x"})

    # No secret-path file may ever carry group/other bits: not at first
    # chmod observation (pre-fix this catches the umask window), not at
    # rename time.
    assert all(not (mode & 0o077) for mode in at_chmod), at_chmod
    assert at_rename, "save_tokens should have replaced key/envelope files"
    assert all(mode == 0o600 for mode in at_rename), at_rename


def test_keyfile_rotation_stays_private(tmp_path, monkeypatch):
    root = _force_keyfile_backend(tmp_path, monkeypatch)
    token_store.save_tokens(root, {"access_token": "x"})
    at_chmod, at_rename = _install_secret_mode_spies(monkeypatch)

    result = token_store._rotate_active_key(root)

    assert result["outcome"] == "rotated"
    assert result["source"] == "keyfile"
    secrets_dir = root / "secrets"
    assert _mode(secrets_dir) == 0o700
    assert _mode(secrets_dir / "hermes_gpt_token_key") == 0o600
    assert not list(secrets_dir.glob("*.new"))
    assert all(not (mode & 0o077) for mode in at_chmod), at_chmod
    assert all(mode == 0o600 for mode in at_rename), at_rename


def test_connect_chmods_wal_sidecars(tmp_path, monkeypatch):
    root = _force_keyfile_backend(tmp_path, monkeypatch)
    db = token_store._connect(root)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS _probe_rm086 (k TEXT)")
        db.execute("INSERT INTO _probe_rm086 VALUES ('x')")
        secrets_dir = root / "secrets"
        assert _mode(secrets_dir / "hermes_gpt_tokens.db") == 0o600
        # False-PASS guard (review): WAL mode must materialize at least one
        # sidecar, otherwise the clamp assertions below would pass vacuously
        # if a sqlite/WAL behavior change stopped creating them.
        assert (secrets_dir / "hermes_gpt_tokens.db-wal").exists() or (
            secrets_dir / "hermes_gpt_tokens.db-shm"
        ).exists(), "sqlite created no WAL sidecars; 0600 clamp would pass vacuously"
        for suffix in ("-wal", "-shm"):
            sidecar = secrets_dir / f"hermes_gpt_tokens.db{suffix}"
            if sidecar.exists():
                assert _mode(sidecar) == 0o600, sidecar
    finally:
        db.close()
