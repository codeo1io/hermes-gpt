# Stewardship request — run 61db9bce246a, cycle 2 (repository-maintenance)

- attempt: 08e7c0aba9cc47e5a5e87fa2d59101b0 (stewardship:stewardship)
- date: 2026-10-01 · skill route: ce-work (router has no stewardship key; decision-artifact
  phase per sibling precedents 43fe0282 a3c84a95 + 6efbf603 652d290c) · fence:
  /tmp/08e7c0ab-scratch/stewardship-ce-work-fence.log (exit 0, `=== skill context ===` …
  `CE_CONTEXT_END` both present) · in-thread artifact authoring, no subagent needed
- Git topology is Conductor's to choose. This document supplies the change-unit decisions
  and rationale only (required evidence: repository/change-unit decisions with rationale).

## Selected batch (from .conductor/prioritization-61db9bce246a.md)

**rm-131** off-load `/api/me` + `/api/connection` token-store reads off the serving event
loop; **rm-132** make `hermes_mission_usage` `_24h` keys actually filter to 24h. Theme:
operator-visible signal correctness. Both P2, S-effort, zero fleet collisions.

## Repository candidate

- implementation site: this worktree `run-61db9bce246a-61db9bce`, branch
  `conductor/run-61db9bce246a`, HEAD caf60018d2 (= integrated lineage; 3 behind
  origin/master 941f4cfc69; the delta touches operator_diagnostics/operator_live_events/
  ui_missions/ui_ops/pyproject/docs — none of the batch files).
- canonical `/work/projects/hermes-gpt`: master @ dce209dfcc, 12 behind origin/master,
  DIRTY `ROADMAP.md` (+137/-70, fleet-owned uncommitted roadmap work — preserve, do not
  clobber or adopt into this batch).

## Dirty state at dispatch (inventory input; preserve as-is)

- worktree: `M ROADMAP.md` (+39/-0, this run's roadmap phase: rm-131..rm-135 mint + digest
  + update notes on rm-046/rm-078/rm-081; footer stays last) + untracked `.conductor/`
  bookkeeping (progress ndjson, prioritization-61db9bce246a.md, this file, carried
  historical artifacts 43fe0282/6efbf603).
- No tracked file other than ROADMAP.md is modified. Nothing here folds into code units.

## Change-unit decisions (rationale)

- **U1 (rm-131)**: `ui_security.py` + `test_ui_security.py` + one-line note in
  `docs/ui-security-boundary.md` + CHANGELOG Unreleased bullet. Self-contained; its only
  runtime dependency (`token_store.py`) is read-only in this unit.
- **U2 (rm-132)**: `operator_mission.py` + `test_operator_mission.py` + CHANGELOG
  Unreleased bullet. Self-contained; corrects a baked-in test alongside the code fix.
- U1/U2 share NO files, NO imports, NO ordering: **two separate change-units** so each
  carries its own tests/gates and can land independently (unrelated subsystems: web
  serving loop vs mission accounting).
- **Read-only boundary**: U1 fixes the CALLER. `token_store.py` is explicitly out of scope
  (fleet triple-hold; see interlock).
- Validation contract (both units): `ruff check .` clean; focused lanes
  `test_ui_security.py` + `test_operator_mission.py` green; then full suite — pre-batch
  baseline = collect-only at implement start (expected 1608 at caf60018d2 per fleet
  reconciliation in run a7e57044's full_tests record: 1614 = 1608 base + that run's +6).
  No network, no CI, no push.
- CHANGELOG.md `## Unreleased` bullets only (house convention from 099e2bfc cycle 5).

## Fleet interlock (fresh sweep 2026-10-01, all 33 worktrees)

Dirty elsewhere now (excluded from this batch, hard boundaries): 041a92f6 @14530e3e79 —
token_store.py, operator_config.py, operator_session.py, operator_swarm.py,
operator_runners.py, codex_config.py, operator_codex.py, fabric_artifacts.py, MANIFEST.in,
pyproject.toml, docs/README.md, test_token_store.py, test_package_docs.py, NEW
atomic_write.py + test_atomic_write.py (that batch IS the rm-134/rm-135/rm-046 fix family);
e13b1c0d @14530e3e79 — same file family + server.py/mcp_compat.py/operator_workspace.py/
oauth_auth.py/test_server.py/test_operator_mission_budget_enforcement.py; b6659410 —
ui_chat.py, operator_live_events.py, server.py, pyproject.toml, tools/upstream_gap.py;
2f81870e — operator_cron.py, operator_failure_semantics.py; bf4db34f @941f4cfc69 + this
run — ROADMAP.md mints only (fleet id frontier now rm-150 unlanded per sibling records;
this run's rm-131..rm-135 meanings are this worktree's ROADMAP — landing gates renumber on
collision, landed-first ids stay).

**All four U1/U2 files (ui_security.py, test_ui_security.py, operator_mission.py,
test_operator_mission.py) are dirty NOWHERE and untouched by the origin/master delta.**

## must_remain_separate hints (mirror of the JSON pairs)

1. U1 unit ⟷ U2 unit (unrelated concerns; no shared surface).
2. token_store.py (any hunk) ⟷ both units — triple-held by siblings; U1 must not modify it.
3. ROADMAP.md (doc drift + conductor-managed status flips) ⟷ code change-units.
4. `.conductor/` bookkeeping (untracked) ⟷ every tracked-file change-unit.
5. web client (`web/src/*`, e.g. connection.ts:9 poller) ⟷ both units — evidence context
   only; server-side fix; sibling rm-077/rm-143 territory.
6. Canonical repo's own dirty ROADMAP.md (+137/-70 @ dce209dfcc) ⟷ this worktree's
   ROADMAP.md (+39/-0 @ caf60018d2) — two different uncommitted roadmap states; do not
   merge or reconcile them in this cycle.

## Notes for the inventory pass

- Expected diff shape at implement end: 4 code/test files + docs/ui-security-boundary.md +
  CHANGELOG.md + ROADMAP.md status flips (conductor-managed) — nothing else tracked.
- Stalls are only observable through an async client; the regression test must use the
  async TestClient pattern (rm-076's established pattern), not sync TestClient.
- rm-132 changes reported numbers: fixture rows need timestamps; the existing
  test_operator_mission.py:569-576 assertions flip from all-time sums to 24h sums.
