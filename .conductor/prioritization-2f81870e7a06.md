# Prioritization — repository-maintenance cycle 1, run 2f81870e7a06

- run: 2f81870e7a064432b384a9788e021e68 · attempt: c1f60f3fd9df43b4bb5e2129aadb9148 · 2026-10-01
- ADOPTED 2026-10-01 by re-dispatch attempt fe8a33f63bec43ae818dae92be24604a after provider reap at 02:20Z (matrix written 02:19:55Z, typed result never delivered). Verification legs re-run at adoption: lineage/tree census (HEAD caf60018d2, M ROADMAP.md + this file untracked); all 8 cycle-block ids+priorities vs ROADMAP.md; 14 legacy competitor priorities; every code anchor re-grepped (failure_semantics :908-941 semantic-before-transient; cron :340/:370 zero locks; events :44/:165/:324/:369; hermes_state :215-262/:330-335; server.py:250 + ui_chat.py:214-219 shims; fleet :225-226 read-then-check / :243-248 unbounded POST); independent fleet re-sweep. Corrections: universe is 55 open/candidate (51 candidate + 4 open) + 2 deferred; ROADMAP-dirty siblings now 9/33 hermes-gpt worktrees (10 dirty total; was 53 at 02:17Z); `operator_token_store.py` → `token_store.py` (filename only, :291-319 range correct); zero-collision conclusion unchanged and independently re-confirmed.
- HEAD: caf60018d27e696956774cb27bea61d84cc3a714 (== origin/master); tree carries this run's uncommitted `M ROADMAP.md` (roadmap phase)
- inputs: assess 48664721 (4 findings, 2 empirically repro'd), research 90277d84 (upstream/ecosystem probes), roadmap b5f35948 (ROADMAP.md 911→966: cycle block rm-102..rm-109 + 5 refresh lines)
- skill route: ce-work fence (both markers, /tmp/c1f60f3f-scratch/ce-work-fence-run.log); no ce-prioritize exists; ce-plan rejected (its artifact is a HOW-plan + interactive handoff — wrong shape for a selection decision)

## Cycle constraints

- Remaining phases this cycle: implement → review → tests → validation → landing. CI/push/PR are NOT available; every claim must be provable locally (ruff + pytest + git).
- Fleet interlock: sibling worktrees hold uncommitted `ROADMAP.md` deltas (expected, landing-gate-reconciled; 9 of 33 hermes-gpt worktrees ROADMAP-dirty at adoption 02:25Z, was 53 fleet-wide at 02:17Z); active code drift concentrates on oauth_auth.py/operator_config.py/token_store.py (3b48f76e family) and operator_live_events.py/operator_session.py (099e2bfc family). An independent `git status --porcelain` sweep over all dirty worktrees (adoption re-run: /tmp/fe8a33f6-scratch/fleet-dirty-hermes-gpt.txt) shows **zero** collisions with this batch's surfaces (incl. tools/upstream_delta.py vs sibling b6659410's distinct tools/upstream_gap.py).
- Product invariants (AGENTS.md) must stay untouched: no network-boundary, gate, redaction, or audit-content changes without dedicated cycle scope.

## Universe scan (55 open/candidate items + 2 deferred)

Top competitors by roadmap priority: rm-053 (135, open), rm-102 (130), rm-105 (120), rm-103 (118), rm-081 (115), rm-106 (112), rm-002 (100), rm-104 (96), rm-001 (90), rm-008 (85), rm-010 (70), rm-048 (70), rm-077 (70), rm-028 (68), rm-054 (65), rm-108 (62), rm-083 (60), rm-107 (58), rm-082 (55), rm-052 (55), rm-034 (52), rm-109 (45).

## Scoring (selected candidates)

| item | impact | risk if unfixed | effort | deps | strategic | score |
|---|---|---|---|---|---|---|
| rm-102 verdict withholding | HIGH — every FAILED delegation that returns a verdict is misclassified to the semantic rung → wrong recovery tier on the busiest path (rate-limits) | silent wrong-recovery on operator traffic | S (one ladder reordering + upstream-mutation-checked fix shape, tests exist) | none | core correctness | 9.2 |
| rm-103 cron RMW lock | HIGH — concurrent cron tools or tool-vs-agent-fire silently drop jobs.json writes; fired-state reverts enable double-runs | silent data loss, cross-process | S–M (flock idiom already in-repo ×2; Barrier regression design proven this run) | none | core reliability | 8.9 |
| rm-104 audit tail newest-first | MED-HIGH — Mission Control shows stale/invisible audit activity exactly on busy deployments (>500 records per 5 MiB window) | silent staleness, misleads operators | S (bounded reverse scan; mirrors two sibling readers in the same file) | none | operator trust | 8.4 |
| rm-108 hermes_state tests | MED — shipped shim (server.py:250, ui_chat.py:214-219) with zero tests; lease CAS + silently-ignored filters + wrong exception type | latent regression surface | S (new test file + 2-line behavior fix) | none | test debt (concrete slice of rm-002) | 7.0 |
| rm-109 fleet A2A bounds | MED-LOW — unbounded resp.read() before the byte check; POST path unbounded | memory exhaustion from misbehaving peer | XS (stream-read to cap + test) | none | hardening | 6.8 |
| rm-107 upstream_delta helper | LOW — dev-ex census tool serving NEXT cycle's rm-105 gate | none (tooling absence) | XS | none | enables rm-105 | 6.0 (stretch) |

## SELECTED BATCH — "operator correctness & reliability hardening" (this cycle)

Order = implementation sequence (highest impact first; items are independent, order is review convenience):

1. **rm-102** `operator_failure_semantics.py` + `test_operator_failure_semantics.py` — withhold `dl_verdict` from the semantic rung when run FAILED (:908-941; semantic consumes verdict at :910-915 before the transient rung can see rate-limit tokens). Gate: new tests prove a FAILED+verdict delegation classifies by failure kind, not verdict; existing ladder tests stay green.
2. **rm-103** `operator_cron.py` + `test_operator_cron.py` — RLock + flock around `_read_jobs`/`_write_jobs` (:340/:370) covering all 7 RMW call sites, mirroring `operator_job_supervisor.py:125-131` / `token_store.py:291-319`. Gate: Barrier-interleaving regression (adapted from `/tmp/48664721-scratch/cron_race_repro.py`) asserting both concurrent writes survive.
3. **rm-104** `operator_events.py` + `test_operator_events.py` — newest-first bounded audit scan in `_read_audit_events` (:165-203) matching the cron (:324) / kanban (:369) reader semantics. Gate: >MAX_PER_SOURCE fixture returns the LATEST window (adapted from `/tmp/48664721-scratch/events_tail_repro.py`).
4. **rm-108** `hermes_state.py` + NEW `test_hermes_state.py` — lease acquire/expire/CAS coverage; `list_sessions_rich` honors-or-raises on `search_query/include_archived/include_children/cwd_prefix` (:215-262); `__getattr__` raises `AttributeError` (message-preserving) not `NotImplementedError` (:330-335). Gate: new file green; callers grepped for `except NotImplementedError` on this surface (none expected).
5. **rm-109** `operator_fleet.py` + `test_operator_fleet.py` — stream-bound GET (:225-226 check-before-read) and POST (:243-248, no check today) to `_MAX_REMOTE_BYTES`; fail closed past cap. Gate: oversized-body tests on both paths.

Stretch (only if implement turn has margin): **rm-107** `tools/upstream_delta.py` — `git diff --stat merge-base..upstream/master` census helper, directly serving rm-105's adoption gate next cycle.

Batch shape: 5 source surfaces + 4 existing test files + 1 new test file; est. delta well inside sibling precedent (+100–300 lines); zero product-invariant pressure; all gates local (ruff + focused lanes + full suite under fleet load).

## Exclusions (with reasons — recorded so the next cycle inherits the reasoning)

- **rm-053 (135, open)**: F1 strip-grammar slice is implemented-but-uncommitted by run cbd4463370ee cycle 2 (do-not-reimplement interlock — touching `operator_skill_resolution.py` risks double-landing); the remaining #76-loader-delegation decision is gated on upstream adoption, which this run's research showed is now inside #82 Autopilot v0.13 → rides rm-105.
- **rm-105 (120) + rm-081 (115) + rm-106 (112) + rm-083 (60)**: upstream-adoption/release-train cluster. 9-commit merge (+6653/−14, 32 files) with rebase risk against 53 sibling ROADMAP deltas and one uncommitted skill-resolution slice; rm-081's trio is verifiably inside v0.13 (subsumed); rm-106/rm-083 are sequenced after rm-105 by their own update lines. Needs a dedicated cycle with verbatim gates; rm-107 is this cycle's down-payment.
- **rm-034 (52)**: hard collision — oauth_auth.py/token_store.py/operator_config.py held by 3b48f76e's pending batch.
- **rm-008 (85)/rm-010 (70)/rm-024/rm-063/rm-069**: require gh-admin rights or CI runs — CI prohibited this cycle.
- **rm-002 (100)/rm-001 (90)**: standing programs, not one-cycle batches; rm-108 is this cycle's concrete rm-002 slice.
- **rm-048 (70)/rm-077 (70)/rm-028 (68)/rm-054 (65)/rm-082 (55)/rm-052 (55)**: SDK-probe-gated, design-gated, or mechanical-sweep effort that doesn't fit alongside the correctness theme at this batch size — strong next-cycle candidates in this order.

## Hand-off to implement

- Verify at start: HEAD caf60018d2, `M ROADMAP.md` (uncommitted, from roadmap phase) + this file untracked; no other drift.
- Verify at end: ruff clean on all touched surfaces; each item's gate tests added and green; full suite delta ≈ +15–30 tests, zero regressions; tree carries exactly the batch diff + ROADMAP status updates (flip selected items to `status: candidate (selected cycle 1, run 2f81870e7a06)` — do NOT mark implemented; landing gate owns that).
