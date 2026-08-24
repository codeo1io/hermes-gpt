"""Temporary read-only CI forge for issue #57. Removed before review."""

from __future__ import annotations

import io
from pathlib import Path
import runpy
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The first helper applies the guarded production integration transform.
runpy.run_path(str(ROOT / "test_000_issue57_integrate.py"), run_name="issue57_integration_helper")
# The second helper applies the fail-closed regression/portability repairs.
runpy.run_path(str(ROOT / "tools" / "issue57_fix.py"), run_name="issue57_followup_helper")

files = [
    "operator_runners.py",
    "operator_codex.py",
    "server.py",
    "pyproject.toml",
    ".github/workflows/ci.yml",
    "operator_job_supervisor.py",
    "test_operator_runners.py",
    "test_operator_job_supervisor.py",
]

buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
    for name in files:
        archive.add(ROOT / name, arcname=name)

output = ROOT / "issue57-transformed.tar.gz"
output.write_bytes(buffer.getvalue())
print(f"wrote {output} ({output.stat().st_size} bytes)")
