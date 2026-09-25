"""Tests for v0.7 S5: durable encrypted token storage + OAuth promotion."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import oauth_auth as oa
import operator_oauth as op_oauth
import operator_policy as op
import operator_workspace as operator_ws
import token_store as ts


@pytest.fixture
def hermes_root(tmp_path: Path) -> Path:
    root = tmp_path / "hermes"
    (root / "secrets").mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture(autouse=True)
def clean_token_env(monkeypatch):
    monkeypatch.delenv(ts.MASTER_KEY_ENV, raising=False)
    yield


def _oauth_state() -> oa.OAuthState:
    config = oa.OAuthConfig(
        issuer="https://auth.example.com",
        client_id="client-id",
        client_secret="client-secret-1234567890abcdefghijklmnopqrstuvwxyz-ABCDEF",
        redirect_uris=("https://auth.example.com/mcp",),
        scope="hermes",
    )
    return oa.OAuthState(config)


def test_ciphertext_on_disk_no_plaintext(hermes_root):
    state = _oauth_state()
    state.access_tokens["tok-1234567890abcdef"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": 10**12}
    state.persist_tokens(hermes_root)

    db_path = hermes_root / "secrets" / "hermes_gpt_tokens.db"
    assert db_path.exists()
    raw = db_path.read_bytes()
    assert b"tok-1234567890abcdef" not in raw
    # The row key is a hash, the body is AES-GCM ciphertext.
    assert ts.lookup_token(hermes_root, "access", "tok-1234567890abcdef") is not None


@pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX file modes")
def test_store_file_mode_is_0600(hermes_root):
    state = _oauth_state()
    state.access_tokens["tok-1234567890abcdef"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": 10**12}
    state.persist_tokens(hermes_root)
    mode = os.stat(hermes_root / "secrets" / "hermes_gpt_tokens.db").st_mode & 0o777
    assert mode == 0o600


def test_windows_store_lock_uses_one_byte_region(hermes_root, monkeypatch):
    calls = []

    class FakeMsvcrt:
        LK_NBLCK = 1
        LK_UNLCK = 2

        @staticmethod
        def locking(fd, mode, size):
            calls.append((fd, mode, size))

    monkeypatch.setattr(ts, "_fcntl", None)
    monkeypatch.setattr(ts, "_msvcrt", FakeMsvcrt)

    with ts._StoreLock(hermes_root):
        assert calls[-1][1:] == (FakeMsvcrt.LK_NBLCK, 1)

    assert calls[-1][1:] == (FakeMsvcrt.LK_UNLCK, 1)
    assert ts._store_lock_path(hermes_root).read_bytes() == b"\0"


def test_restart_reload_roundtrip(hermes_root):
    state = _oauth_state()
    state.access_tokens["tok-abc"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": time_far()}
    state.refresh_tokens["ref-xyz"] = {"client_id": "client-id", "scope": "hermes", "expires_at": time_far()}
    state.persist_tokens(hermes_root)

    # Fresh state (simulated restart) restores both stores.
    fresh = _oauth_state()
    summary = fresh.restore_tokens(hermes_root)
    assert summary["present"] is True
    assert summary["restored"] == 2
    assert "tok-abc" in fresh.access_tokens
    assert "ref-xyz" in fresh.refresh_tokens


def time_far() -> float:
    import time

    return time.time() + 3600 * 24 * 30


def test_corrupt_store_fails_closed(hermes_root):
    path = hermes_root / "secrets" / "hermes_gpt_tokens.db"
    path.write_bytes(b"not a sqlite database at all" * 10)
    with pytest.raises(ts.TokenStoreError):
        ts.load_tokens(hermes_root)
    with pytest.raises(ts.TokenStoreError):
        ts.lookup_token(hermes_root, "access", "tok")


def test_revoke_retires_everything_and_rotates_key(hermes_root):
    state = _oauth_state()
    state.access_tokens["tok-abc"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": time_far()}
    state.persist_tokens(hermes_root)
    assert ts.lookup_token(hermes_root, "access", "tok-abc") is not None

    result = ts.revoke_tokens(hermes_root, rotate_key=True)
    assert result["revoked"] is True
    assert result["key_rotated"] is True
    assert result["epoch"] >= 1
    assert ts.lookup_token(hermes_root, "access", "tok-abc") is None
    assert not ts.load_tokens(hermes_root).get("access_tokens")
    assert ts.read_revocation_epoch(hermes_root) >= 1


def test_env_master_key_works(hermes_root, monkeypatch):
    monkeypatch.setenv(ts.MASTER_KEY_ENV, "test-master-key")
    state = _oauth_state()
    state.access_tokens["tok-abc"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": time_far()}
    state.persist_tokens(hermes_root)

    fresh = _oauth_state()
    assert fresh.restore_tokens(hermes_root)["restored"] == 1


def test_status_reveals_no_token_material(hermes_root):
    state = _oauth_state()
    state.access_tokens["tok-secret-value"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": time_far()}
    state.persist_tokens(hermes_root)

    out = json.loads(op_oauth.hermes_oauth_status(hermes_root=hermes_root))
    raw = json.dumps(out)
    assert "tok-secret-value" not in raw
    assert out["store"]["presence"] == "present"
    assert out["store"]["client_count"] >= 1
    assert out["success"] is True


def test_oauth_status_absent(hermes_root):
    out = json.loads(op_oauth.hermes_oauth_status(hermes_root=hermes_root))
    assert out["success"] is True
    assert out["store"]["presence"] == "absent"


def test_oauth_status_audits_changed_false(hermes_root, tmp_path):
    """Proof 3: the read-only status wrapper audits with changed=false and
    never mutates the token store."""
    log = tmp_path / "audit.jsonl"
    op.set_audit_log_override(log)
    try:
        out = json.loads(op_oauth.hermes_oauth_status(hermes_root=hermes_root))
        assert out["success"] is True
        records = [
            json.loads(line)
            for line in log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        status_records = [r for r in records if r["tool"] == "hermes_oauth_status"]
        assert status_records, "no audit record for hermes_oauth_status"
        assert all(r["changed"] is False for r in status_records)
        assert all(r["dry_run"] is True for r in status_records)
    finally:
        op.set_audit_log_override(None)


def test_revoke_requires_owner(hermes_root, monkeypatch):
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    out = json.loads(op_oauth.hermes_oauth_revoke(confirm=True, dry_run=False, hermes_root=hermes_root))
    assert out["success"] is False
    assert out["code"] == "OAUTH_REVOKE_DENIED"


def test_revoke_owner_gated_success(hermes_root, monkeypatch):
    state = _oauth_state()
    state.access_tokens["tok-abc"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": time_far()}
    state.persist_tokens(hermes_root)

    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "owner")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OWNER_ACTIVE_ENV, "1")
    monkeypatch.setenv(op.OWNER_ACK_ENV, op.OWNER_ACK_REQUIRED_VALUE)

    out = json.loads(op_oauth.hermes_oauth_revoke(confirm=True, dry_run=False, hermes_root=hermes_root))
    assert out["success"] is True
    assert out["changed"] is True
    assert not (hermes_root / "secrets" / "hermes_gpt_tokens.json").exists()


def test_revoke_dry_run_does_not_delete(hermes_root, monkeypatch):
    state = _oauth_state()
    state.access_tokens["tok-abc"] = {"client_id": "client-id", "scope": "hermes", "resource": "r", "expires_at": time_far()}
    state.persist_tokens(hermes_root)

    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "owner")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.setenv(op.OWNER_ACTIVE_ENV, "1")
    monkeypatch.setenv(op.OWNER_ACK_ENV, op.OWNER_ACK_REQUIRED_VALUE)

    out = json.loads(op_oauth.hermes_oauth_revoke(dry_run=True, hermes_root=hermes_root))
    assert out["success"] is True
    assert out["dry_run"] is True
    assert ts.lookup_token(hermes_root, "access", "tok-abc") is not None


def test_persist_hook_writes_after_exchange(hermes_root, monkeypatch):
    """Token issuance triggers the persistence hook (S5 server wiring)."""
    state = _oauth_state()
    state.access_tokens.clear()
    state.refresh_tokens.clear()
    monkeypatch.setattr(oa, "_persist_hook", lambda st, kind: st.persist_tokens(hermes_root))

    code = state.issue_authorization_code(
        client_id="client-id",
        redirect_uri="https://auth.example.com/mcp",
        scope="hermes offline_access",
        resource="https://auth.example.com/mcp",
        code_challenge="E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    )
    resp = state.exchange_authorization_code(
        code=code,
        client_id="client-id",
        redirect_uri="https://auth.example.com/mcp",
        code_verifier="dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
    )
    assert resp["access_token"]
    db_path = hermes_root / "secrets" / "hermes_gpt_tokens.db"
    assert db_path.exists()
    assert resp["access_token"] not in db_path.read_bytes().decode("latin-1")
    assert ts.lookup_token(hermes_root, "access", resp["access_token"]) is not None


def test_restore_populates_after_restart(hermes_root):
    """oauth_state_from_env restores durable tokens after a restart (S5)."""
    state = _oauth_state()
    resource = state.config.resource
    state.access_tokens["tok-restart"] = {"client_id": "client-id", "scope": "hermes", "resource": resource, "expires_at": time_far()}
    state.refresh_tokens["ref-restart"] = {"client_id": "client-id", "scope": "hermes", "expires_at": time_far()}
    state.persist_tokens(hermes_root)

    # Simulate a fresh OAuthState restoring from the same root.
    fresh = _oauth_state()
    summary = fresh.restore_tokens(hermes_root)
    assert summary["restored"] == 2
    assert fresh.validate_access_token("tok-restart") is True


# ---------------------------------------------------------------------------
# rm-067 durability regression: unique-tmp + fsync atomic writes
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="POSIX fsync/file-mode semantics")
def test_envelope_write_fsyncs_before_replace(hermes_root, monkeypatch):
    """The durable-write standard requires fsync before the rename."""
    calls: list[int] = []
    real_fsync = os.fsync

    def spying_fsync(fd: int) -> None:
        calls.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(operator_ws.os, "fsync", spying_fsync)
    ts._write_envelope(hermes_root, "kid-regression", {"hello": "world"}, b"k" * 32)

    assert calls, "envelope write did not fsync before replace"
    assert ts.envelope_path(hermes_root).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX fsync/file-mode semantics")
def test_key_file_write_fsyncs_before_replace(hermes_root, monkeypatch):
    """Master-key writes fsync too (crash cannot leave a truncated key)."""
    calls: list[int] = []
    real_fsync = os.fsync

    def spying_fsync(fd: int) -> None:
        calls.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(operator_ws.os, "fsync", spying_fsync)
    ts._write_key_file(hermes_root, b"k" * 32)

    assert calls, "key write did not fsync before replace"
    assert ts.key_file_path(hermes_root).exists()


@pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX file modes")
def test_key_file_mode_is_0600(hermes_root):
    ts._write_key_file(hermes_root, b"k" * 32)
    mode = os.stat(ts.key_file_path(hermes_root)).st_mode & 0o777
    assert mode == 0o600


@pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX file modes")
def test_envelope_file_mode_is_0600(hermes_root):
    ts._write_envelope(hermes_root, "kid-regression", {"hello": "world"}, b"k" * 32)
    mode = os.stat(ts.envelope_path(hermes_root)).st_mode & 0o777
    assert mode == 0o600


def test_failed_envelope_write_leaves_no_staging_file(hermes_root, monkeypatch):
    """A failing write must remove its own staging file and keep the old data."""
    ts._write_envelope(hermes_root, "kid-regression", {"generation": 1}, b"k" * 32)
    before = ts.envelope_path(hermes_root).read_bytes()

    def exploding_replace(src, dst):
        raise OSError("simulated crash between staging and replace")

    monkeypatch.setattr(operator_ws.os, "replace", exploding_replace)
    with pytest.raises(OSError):
        ts._write_envelope(hermes_root, "kid-regression", {"generation": 2}, b"k" * 32)

    staging = [
        p for p in (hermes_root / "secrets").glob(".*.tmp") if p.is_file()
    ]
    assert staging == [], f"staging files leaked: {staging}"
    # The previous envelope survives the failed write, byte-for-byte.
    assert ts.envelope_path(hermes_root).read_bytes() == before


def test_concurrent_envelope_writes_do_not_clobber(hermes_root):
    """Uniquely named staging files: parallel writers all land intact.

    The old fixed ".tmp"/".new" staging names let two processes racing on
    save_tokens clobber each other's staging file and corrupt the envelope.
    """
    import threading

    errors: list[BaseException] = []

    def writer(worker: int) -> None:
        try:
            for i in range(25):
                ts._write_envelope(
                    hermes_root,
                    "kid-regression",
                    {"worker": worker, "i": i},
                    b"k" * 32,
                )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(w,)) for w in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent envelope writes failed: {errors}"
    staging = [
        p for p in (hermes_root / "secrets").glob(".*.tmp") if p.is_file()
    ]
    assert staging == [], f"staging files leaked: {staging}"
    # The final envelope is a complete, parseable envelope — never a torn
    # interleaving of two writers' staging files.
    payload = json.loads(ts.envelope_path(hermes_root).read_text(encoding="utf-8"))
    assert "version" in payload and "ciphertext" in payload


def test_rotation_failure_keeps_previous_key(hermes_root, monkeypatch):
    """A failed rotation reports failure and leaves the old key active."""
    first = ts._rotate_active_key(hermes_root)
    assert first["outcome"] == "rotated"
    old_key = ts.key_file_path(hermes_root).read_bytes()

    def exploding_replace(src, dst):
        raise OSError("simulated crash during rotation")

    monkeypatch.setattr(operator_ws.os, "replace", exploding_replace)
    result = ts._rotate_active_key(hermes_root)

    assert result["outcome"] == "failed"
    assert result["source"] == "keyfile"
    assert ts.key_file_path(hermes_root).read_bytes() == old_key
    staging = [
        p for p in (hermes_root / "secrets").glob(".*.tmp") if p.is_file()
    ]
    assert staging == [], f"staging files leaked: {staging}"
