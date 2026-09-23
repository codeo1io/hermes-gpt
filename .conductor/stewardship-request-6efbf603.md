# Stewardship request — run 6efbf603, cycle 1, batch B1 (2026-09-22)

Machine-readable copy: phase_result `stewardship_request` in the attempt 652d290c spool JSON.

## Change-unit decisions (rationale)

The batch splits into THREE change-units even though it ships as one coherent cycle:

- **U1 — cron private-runtime guard test (run-branch base).** New repo test
  asserting no repo module may import `cron`/`cron.jobs` (the private Hermes
  agent runtime). Independent of everything else; permanent prevention of the
  exact class that broke master (assess 495882cf: 9 red lanes, 2026-09-22).
  Surfaces: `test_operator_cron.py` (or a new `test_no_private_runtime_imports.py`).
- **U2 — cron repair patch (targets origin/master tip, NOT the run base).**
  The defect (`operator_cron.py:981` `from cron.jobs import parse_schedule`,
  structured-dict persistence) exists only at 4b958379d6 — the run branch base
  5765b571b2 predates the convergence and contains no defect. Therefore the
  repair is authored as `.conductor/patches/rm-032-cron-repair.patch`
  (drop the import; persist upstream-compatible RAW `schedule`/
  `schedule_display` strings; repo-local validation only) and proven in a
  DETACHED temp worktree at 4b958379d6 with `cron` unimportable: full
  `test_operator_cron.py` green including the 5 CI-failing cron-create tests.
  Must remain a separate unit from base edits — conflating a master-tip patch
  with base edits breaks both application paths.
- **U3 — pyyaml CVE floor (run-branch base).** `pyproject.toml:20`
  `>=6,<7` → `>=6.0.3,<7` (CVE-2026-31132 fixed in 6.0.3) + CHANGELOG
  Unreleased entry (:58). Deliberately stops before PR #19's file set.

## must_remain_separate (hints for Conductor's overlap detection)

1. **U2 (master-tip patch) vs all base edits** — different trees, different
   verification harnesses; never one commit.
2. **PR #19 / upstream PR #75 packaging consolidation** (requirements*.txt
   deletion, gitlink drop) — owned by the in-flight PR; folding it in would
   duplicate and conflict with our own lineage's PR at the gate.
3. **rm-034 OAuth-knob docs** — the knob code (DCR, PKCE_MODE,
   /oauth/register) exists only on the master tip; docs must land post-merge,
   not in this batch.
4. **Run-artifacts dirty state** — `ROADMAP.md` (roadmap-phase edit) and
   `.conductor/` (progress/prioritization/patches) are run bookkeeping;
   preserve them separately from implementation units.

## Surfaces (authoritative, verified 2026-09-22)

- `operator_cron.py:981-985` @ origin/master 4b958379d6 (import + ValueError) — U2 target
- `operator_cron.py` hermes_cron_create create-site (structured-dict persistence) @ master — U2 target
- `test_operator_cron.py:610-719` (cron-create family) — U1/U2 verification
- `pyproject.toml:20` — U3
- `CHANGELOG.md:58` (Unreleased) — U3
- new: `test_no_private_runtime_imports.py` (or test_operator_cron.py addition) — U1
- new: `.conductor/patches/rm-032-cron-repair.patch` — U2 artifact

## Repository candidate

`/work/projects/hermes-gpt` (canonical, green base 5765b571b2) and this
worktree `/home/agent/.hermes/conductor-worktrees/hermes-gpt-c122f4fe79/run-6efbf6037da9-6efbf603`.
Topology (branches/worktrees/where the patch applies) is Conductor's decision;
this request takes no position beyond the must-apply-onto fact stated above.

## Out of batch (recorded, not started)

Gate-time companions: master branch protection (rm-038), land PR #19, rebase
upstream PR #75 (verify by head_sha). Next cycle: rm-035 + rm-024 pairing,
rm-034 post-merge docs, rm-036/037/039/040 hygiene.
