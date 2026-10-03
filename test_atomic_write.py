"""Tests for the shared atomic-write primitives (rm-077 / rm-067)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

import atomic_write


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_write_bytes_creates_file_with_requested_mode(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "state.bin"
    atomic_write.atomic_write_bytes(target, b"\x00\x01", mode=0o600)
    assert target.read_bytes() == b"\x00\x01"
    assert _mode(target) == 0o600


def test_write_is_umask_independent_for_secret_modes(tmp_path: Path) -> None:
    old = os.umask(0o022)
    try:
        target = tmp_path / "secret.key"
        atomic_write.atomic_write_bytes(target, b"k" * 32, mode=0o600)
        assert _mode(target) == 0o600
    finally:
        os.umask(old)


def test_staging_file_is_uniquely_named(tmp_path: Path) -> None:
    """Two concurrent writers must not share a staging path (fixed-name clobber)."""
    target = tmp_path / "state.json"
    atomic_write.atomic_write_text(target, "first")
    atomic_write.atomic_write_text(target, "second")
    assert target.read_text(encoding="utf-8") == "second"
    leftovers = [p for p in tmp_path.iterdir() if p.name != target.name]
    assert leftovers == [], "no staging files may remain after a successful write"


def test_failed_write_removes_staging_and_keeps_previous_content(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    atomic_write.atomic_write_text(target, "old")
    with pytest.raises(OSError):
        atomic_write.atomic_write_text(target, "new", validate=lambda _p: (_ for _ in ()).throw(OSError("boom")))
    assert target.read_text(encoding="utf-8") == "old"
    assert [p for p in tmp_path.iterdir() if p.name != target.name] == []


def test_validate_runs_before_publish(tmp_path: Path) -> None:
    seen: list[Path] = []
    target = tmp_path / "cfg.toml"

    def parse(path: Path) -> None:
        seen.append(path)
        assert path.read_text(encoding="utf-8") == "x=1\n"

    atomic_write.atomic_write_text(target, "x=1\n", mode=0o644, validate=parse)
    assert target.read_text(encoding="utf-8") == "x=1\n"
    # validation saw the staging file, not the (not-yet-existing) target
    assert seen and seen[0] != target


def test_private_dir_creates_0700_and_tightens_existing(tmp_path: Path) -> None:
    d = tmp_path / "secrets"
    d.mkdir(mode=0o755)
    target = d / "key"
    atomic_write.atomic_write_bytes(target, b"k", private_dir=True)
    assert _mode(d) == 0o700
    assert _mode(target) == 0o600


def test_private_dir_preserves_tighter_existing_mode(tmp_path: Path) -> None:
    d = tmp_path / "secrets"
    d.mkdir(mode=0o500)
    atomic_write.ensure_private_dir(d)
    assert _mode(d) == 0o500


def test_concurrent_writers_all_publish_a_complete_file(tmp_path: Path) -> None:
    """Adversarial: N threads racing on one target never interleave content."""
    import threading

    target = tmp_path / "shared.json"
    atomic_write.atomic_write_text(target, "init")
    payloads = {f'{{"i": {i}, "pad": "{i * 200}"}}' for i in range(24)}
    barrier = threading.Barrier(len(payloads))

    def writer(text: str) -> None:
        barrier.wait()
        for _ in range(10):
            atomic_write.atomic_write_text(target, text)

    threads = [threading.Thread(target=writer, args=(p,)) for p in payloads]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    final = target.read_text(encoding="utf-8")
    assert final in payloads, "target must hold exactly one writer's payload"
    leftovers = [p for p in tmp_path.iterdir() if p.name != target.name]
    assert leftovers == []
