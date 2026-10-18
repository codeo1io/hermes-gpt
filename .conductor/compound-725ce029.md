# Compound — run bdf4157b, cycle 1 (attempt 725ce029, 2026-09-22)

Pre-review compound only (fleet rule #6612): everything below uses assess/research/roadmap/prioritize/stewardship/implement/targeted_tests evidence. Review and shipping outcomes happen after this step.

## What landed in ROADMAP.md

- **Status flips → `implemented-pending-review`** with `implemented:` evidence lines: rm-038, rm-040, rm-041, rm-045 (batch B1 "Silent-Failure Hardening", attempt 5f6ceb77, 10 files +328/-47, uncommitted).
- **rm-046 minted** (operator_swarm.py:565 `_save_workflow` fixed-tmp durability — the same pattern rm-038 fixed in cron; cross-checked unclaimed across all sibling ledgers/worktrees before minting, per prevention rule 11).
- **`## Cycle 1 outcome — run bdf4157b` section**: batch record, validation outcome (targeted 106/106; full suite ×2, byte-identical failure set = documented allowlist only), **prevention rules 12–18**, and a concrete **next-cycle context** list.

## Prevention rules added (12–18)

12. Complete shipped partial work by adopting it verbatim (rm-021 helper ← 89865b1281).
13. Derive dependency floors from advisory data (OSV bisection; first zero-advisory release already in the baseline venv), not intuition.
14. Unset `HERMES_GPT_OPERATOR_ALLOWED_PROFILES` is deny-by-default, even for read-only tools.
15. Zero-new-failures claims need a reproducible allowlist (full suite ×2, byte-identical failure set).
16. `http.client` passes bytes header values through — the non-ASCII Authorization test harness trick.
17. Work-order `uv run … -n 8` always substitutes to baseline-venv serial `HERMES_HTTP_TEST=1`; record the substitution in the command string.
18. Same-pattern follow-ups found mid-implement get their own roadmap id at compound time (rm-046), not a scope-creep edit.

## Validation baseline (stable, pre-review)

- Targeted (cron/fabric/runners test files): exit 0, 106/106 — `/tmp/bdf4157b-65967a95-targeted.log`.
- Full serial suite, twice: `[100%]`, failures = exactly 4× test_codex_pr63_remediation.py (stale-PKCE; owner = sibling fd2bc85 repair / rm-030 catch-up) + test_mcp_compat.py metadata (env-dependent). Zero new. Logs: `/tmp/bdf4157b-5f6ceb77-fullsuite.log`, `/tmp/bdf4157b-65967a95-fullsuite.log`.
- test_operator_delegations.py:654 flake did NOT fire in either run; still classified as a real load-timing flake (assess solo-rerun evidence).

## Next cycle (concrete candidates, suggested order)

1. **rm-030 v0.11.0 catch-up** (validated headline: 5 commits / 19 files gap; upstream passes the 4 failing PKCE tests 44/44 on the baseline interpreter) → allowlist shrinks 5→1. rm-037 gated on it.
2. **Review B1** before commit — focus: `_refuse_if_corrupt` double-read in copy/move; dir-fsync best-effort OSError swallow; surrogateescape choice; ci.yml heredoc quoting.
3. **rm-046** swarm write durability (pairs with a B2 reliability batch).
4. **Design decisions due**: rm-039 web-UI auth story; rm-042 token_store PBKDF2 migration.
5. **Fleet ROADMAP merge at the commit gate**: this worktree's ROADMAP.md is the maximal additions-only reconciliation (rm-001..rm-046, 4 sibling namespaces folded) — reconcile, don't re-render (#6611).
6. **requirements.txt:4 hunk is conditional** on sibling 634bf451's rm-029 (file deletion): drop the line-level hunk if that lands first; pyproject stays authoritative.
