# Stewardship request — run bdf4157b cycle 1 — B1 "Silent-Failure Hardening"

Selected batch (from .conductor/prioritization-4a9d9f1d.md): rm-038 + rm-041 + rm-040 + rm-045.

## Units

### U1 — rm-038 cron jobs.json durability completion (headline)
- operator_cron.py:33 (unused threading import -> real lock), :99 _read_jobs (corrupt read must NOT return []), :122 _write_jobs (fixed shared /tmp path -> unique tmp + os.replace + flock)
- test_operator_cron.py: durability tests (concurrent writers, corrupt-file restore/refuse, atomic replace)
- Base-independent of rm-021's pending backup code (tolerates sidecar absence).

### U2 — rm-041 compare_digest ASCII hardening
- operator_runners.py:1026, operator_fabric.py:1266: compare_digest on raw header bytes raises TypeError on non-ASCII -> 500. Fix: ASCII-safe encode/lower + compare_digest, non-ASCII -> 401.
- test_operator_runners.py, test_operator_fabric.py: non-ASCII token rejection = 401 tests.

### U3 — rm-040 CI py_compile derivation
- .github/workflows/ci.yml:65 step + hand-maintained module list (30/59 shipped modules absent). Fix: derive from installed package (python -c "import ..." loop over py-modules) or compile package dir.
- Evidence: module-vs-list diff in assess 255a600f.

### U4 — rm-045 cryptography floor raise
- pyproject.toml:19 cryptography>=42 -> floor admitting no known OSV GHSA (verify at implement; 50.0.1 current, clean).
- requirements.txt:4 CONDITIONAL — 634bf451 rm-029 removes this file; if absent at implement time, pyproject-only.

## Separation hints
- Same-file distinct hunks across concurrent runs: pyproject.toml cryptography(:19) vs pyyaml(:20, three siblings); ci.yml py_compile(:65+) vs :22 SHA-pin (684b9786).
- Do NOT co-fold with: fd2bc85 PKCE/skip-guard/dead-block/build-floor batch; rm-030 v0.11.0 catch-up (next-cycle headline).
- Ledger artifacts (ROADMAP.md, .conductor/prioritization-*.md) are run history, not code units.

## Exit gate (for implement, not this phase)
Full suite serial HERMES_HTTP_TEST=1 baseline venv; expected pre-existing failures at base: 4x test_codex_pr63_remediation (fd2bc85 territory) + test_mcp_compat metadata (env) — not B1 regressions; delegations flake documented rm-010.
