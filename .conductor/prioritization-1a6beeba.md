# Prioritization — run 1a6beeba (family repository-maintenance:00b0db0d:cycle:2)

- attempt: ae22446dbaf647e3a1c08d11a46338a8 (prioritize), 2026-10-01
- worktree: run-1a6beebac21c-1a6beeba @ caf60018d2 (+ uncommitted cycle-5 ROADMAP.md block from phase 7a1a3574)
- inputs: assess spool cce9cf99 (3 fresh findings), research spool 636d3c1e (rm-095..rm-101 candidates + ecosystem probes), ROADMAP.md open pool (94 items, ~40 unresolved)
- skill: ce-plan (router has no prioritize-specific skill; narrowest match for selection-into-implementation-batch); fence complete both markers; subagent passes in-thread, disclosed — not independent corroboration
- copy of this file: /tmp/research-1a6beeba/prioritization-1a6beeba.md

## Fresh gate events resolved this phase (evidence, 2026-10-01)

1. **Upstream PR #76 CLOSED UNMERGED** (api.github.com/repos/asimons81/hermes-gpt/pulls/76: state=closed, merged=false, merged_at=None). This is the gate recorded on rm-053 (priority 135, the file's highest open item): "the #76 loader-delegation reconciliation decision + same-filename merge-order plan remain open until upstream PR #76 lands". The upstream path is dead as-is → the decision is unblocked NOW; the hermetic repo-local resolver wins by default.
2. **rm-053's grammar slice is already landed at HEAD**: operator_skill_resolution.py:51 documents grammar reuse verbatim; :169 `SKILL_NAME_RE.fullmatch`; operator_skills.py:76 `_VALID_NAME_RE.fullmatch` — byte-identical shared grammar, both fullmatch, padded names rejected fail-closed at stage 1. Remaining work is decision-record + status-note only.
3. **Upstream v0.13 still untagged and still moving**: 9-commit gap (tip f4151d972=PR#82 merged 2026-09-30T03:51Z) PLUS two new open PRs (#83 README v0.13.0 candidate 04:47Z, #84 site refresh 04:57Z). Moving-target condition persists.

## Selection matrix (this cycle's actionable pool)

| id | pri | impact | risk | effort | deps/gates | verdict |
|---|---|---|---|---|---|---|
| rm-053 slice | 135 | high — unblocks the file's top open item; decision + status only (grammar slice verified landed) | low (docs/decision; no behavior change) | S | gate resolved TODAY (#76 closed unmerged) | **SELECT (rider)** |
| rm-096 | 90 | high — 25s long-poll pins anyio's shared 40-token threadpool; ≥40 clients starve ALL offloaded handlers + sync routes | med — concurrency plumbing; fix approach verified (anyio.to_thread.run_sync limiter kwarg) | M | none | **SELECT** |
| rm-097 | 88 | high — unbounded fire-and-forget mutating cron dispatch; success-only audit at dispatch time | med — audit-semantics change needs tests+docs | M | none | **SELECT** |
| rm-095 | 85 | high — idle filtered WS clients rescan journal tail every ≤0.5s forever; rm-080 residual; docs overclaim | low — one branch condition + regression test | S | none | **SELECT** |
| rm-100 | 75 | med — 3.10 EOL 2026-10-31 (T-30d); 3.13 lane tested-in-practice (delegate env green) | med — CI matrix + release-gated requires-python bump | M | next fork release; CI runs | DEFER to next cycle — schedule BEFORE 2026-10-31 |
| rm-099 | 55 | med — starlette+anyio direct imports undeclared; install-contract hole | low — two pyproject lines | XS | none | **SELECT (rider)** |
| rm-098 | 115 | high strategic (v0.13 Autopilot) | high — 9-commit conflict review vs fork invariants; upstream STILL moving (+2 open PRs); untagged | L | v0.13.0 tag; sibling rm-085 same topic (gate dedupes) | DEFER — moving target; re-evaluate when v0.13.0 tags |
| rm-081 | 115 | high (skill-loader catch-up) | high — same moving-target condition; gap note already in item | L | same as rm-098 | DEFER with rm-098 |
| rm-101 | 25 | low — env-skip ownership + autouse audit-override fixture | low | S | none | DEFER (P3 hygiene; next cycle filler) |
| older candidates (rm-001..rm-084 remainder, ~30 items) | ≤70 | unknown-fresh — most measured at 2026-09-2x HEADs | — | — | need re-verification vs current HEAD | NOT SELECTED — stale by ≥1 cycle; future assess refresh |

## SELECTED BATCH — "operator async-surface reliability close-out + stale-gate unblock"

**rm-095 + rm-096 + rm-097 + rm-099 + rm-053(decision-slice)**

Coherence: the three code fixes all live in the operator UI's async request path — live-events WS loop (operator_live_events.py) → missions long-poll (ui_missions.py) → ops cron dispatch (ui_ops.py) — same subsystem, same test lanes, ascending effort (S→M→M), all evidence fresh from THIS run's assess (spool cce9cf99), all acceptance criteria already written in the cycle-5 ROADMAP block. rm-099 (pyproject rider) and rm-053's decision record are zero-risk riders unblocked today. No upstream dependency; no cross-family collision (sibling 0aa75ea44's selected batch = OAuth loop-blocking + ui_mount doctor + env-knob docs — different content; landing-gate dedup applies only to deferred rm-098↔rm-085). Cycle capacity matches precedent (cycle-4 landed five items rm-076..080).

Dependency order for implement: rm-095 → rm-096 → rm-097 (shared live-events wait internals inform 096); rm-099 + rm-053 slice independent, any time.

Verification expectations (per item, from the cycle-5 block acceptance):
- rm-095: empty-page cursor adoption; regression test (idle filtered client advances past N non-matching events); docs/live-events.md:40-42 holds verbatim.
- rm-096: long-poll waits off the shared limiter (dedicated anyio CapacityLimiter or asyncio-native bridge); saturation regression (40 holders + mission-events completes); behavior unchanged.
- rm-097: bounded executor + registry + completion/failure audit records (dispatch-time success record replaced); cap rejection loud; tests incl. injected cron failure.
- rm-099: starlette+anyio declared with bounds; CI installs green; no version drift.
- rm-053: decision recorded in the item (hermetic resolver; #76 closed-unmerged cited); merge-order note conditional on any re-proposal; status updated.

## Deferred queue (next cycles)

1. rm-100 — dated: schedule the floor-bump cycle before 2026-10-31 (3.10 EOL).
2. rm-098 + rm-081 — when upstream tags v0.13.0; landing-gate dedup with sibling rm-085.
3. rm-101 — P3 filler.
4. Older stale candidates — refresh via a future assess before selecting.
