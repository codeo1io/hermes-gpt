"""Shared atomic-write primitives for hermes-gpt.

Canonical durable-write shape for every state file this package replaces
on disk (token_store secrets, profile config, ``.env``, job and workflow
records):

- the staging file is uniquely named (pid + random token), so concurrent
  writers to the same target never clobber each other's staging file and
  a crashed writer never leaves a *predictable* leftover name;
- it is created with an explicit mode via ``os.open`` (``O_EXCL``), so
  secret material is never world-readable in any window, regardless of
  umask — 0o600 has no group/other bits for a umask to strip;
- it is fsynced before the rename, and the containing directory after,
  so a crash cannot leave a truncated target;
- ``os.replace`` publishes it atomically; a failed write removes its own
  staging file.

``validate`` lets callers verify the staged content before it is
published (codex_config parses the staged TOML first, preserving its
existing validate-then-replace semantics).
"""

from __future__ import annotations

import os
import secrets as _secrets
from pathlib import Path
from typing import Callable

__all__ = ["atomic_write_bytes", "atomic_write_text", "ensure_private_dir"]


def ensure_private_dir(path: Path, *, dir_mode: int = 0o700) -> Path:
    """Create ``path`` (and parents) and strip group/other permission bits.

    Existing intentional restrictions (e.g. 0o500) are preserved: only bits
    more permissive than the caller wants are removed.
    """
    path.mkdir(parents=True, exist_ok=True, mode=dir_mode)
    try:
        st = path.stat()
        if st.st_mode & 0o077:
            os.chmod(path, st.st_mode & ~0o077)
    except OSError:
        pass
    return path


def _staging_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.{os.getpid()}.{_secrets.token_hex(4)}.tmp")


def staging_path(path: Path) -> Path:
    """Unique staging path beside *path* for streaming writers.

    Simple whole-payload writes should use :func:`atomic_write_bytes` /
    :func:`atomic_write_text`; streaming writers that cannot materialize the
    full payload up front open this path themselves, fsync, and
    ``os.replace`` it onto *path*.
    """
    return _staging_path(path)


def atomic_write_bytes(
    path: Path,
    data: bytes,
    *,
    mode: int = 0o600,
    private_dir: bool = False,
    fsync_dir: bool = True,
    validate: Callable[[Path], None] | None = None,
) -> None:
    """Durably replace ``path`` with ``data`` written at ``mode``."""
    parent = path.parent
    if private_dir:
        ensure_private_dir(parent)
    else:
        parent.mkdir(parents=True, exist_ok=True)
    tmp = _staging_path(path)
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        if validate is not None:
            validate(tmp)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    if fsync_dir:
        _fsync_dir(parent)


def atomic_write_text(
    path: Path,
    text: str,
    *,
    mode: int = 0o600,
    private_dir: bool = False,
    fsync_dir: bool = True,
    encoding: str = "utf-8",
    validate: Callable[[Path], None] | None = None,
) -> None:
    """Durably replace ``path`` with ``text`` written at ``mode``.

    The bytes pipeline writes ``\\n`` verbatim on every platform (no
    newline translation), matching ``newline="\\n"`` semantics.
    """
    atomic_write_bytes(
        path,
        text.encode(encoding),
        mode=mode,
        private_dir=private_dir,
        fsync_dir=fsync_dir,
        validate=validate,
    )


def _fsync_dir(path: Path) -> None:
    try:
        dfd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dfd)
    except OSError:
        pass
    finally:
        os.close(dfd)
