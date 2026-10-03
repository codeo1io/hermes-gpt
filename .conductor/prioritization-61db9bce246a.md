# Prioritization — repository-maintenance cycle 2, run 61db9bce246a

- run: 61db9bce246a4150954d3c8ae3ad4d55 · attempt: 0b756ae170bc40e49e15b3838df9481f · 2026-10-01
- HEAD: caf60018d27e696956774cb27bea61d84cc3a714 (origin/master has since moved to 941f4cfc69 = 1a6beeba's rm-095/096/097/099 landing; landing gate owns the rebase — zero file overlap with this batch, verified below); tree carries this run's uncommitted `M ROADMAP.md` (roadmap phase, +39/-0)
- inputs: assess 727758f1 (adopting reaped fbb8862d, 5+1 findings), research 4658b239 (4 candidates + 5 evidence-backed rejections), roadmap 1f3dd585 (minted rm-131..rm-135 + 3 refresh notes on rm-046/rm-078/rm-081)
- skill route: ce-work fence (both markers, /tmp/0b756ae1-scratch/prioritize-ce-work-fence.log); no ce-prioritize exists; ce-plan rejected (its artifact is a HOW-plan + interactive handoff — wrong shape for a selection decision) — same resolution as sibling 2f81870e's cycle-1 matrix at this HEAD

## Cycle constraints

- Remaining phases this cycle: implement → review → tests → validation → landing. CI/push/PR are NOT available; every claim must be provable locally (ruff + pytest + git).
- Product invariants (AGENTS.md) untouched: no network-boundary, gate, redaction, or audit-content changes; both selected items are execution-scheduling and query-filter fixes inside existing read paths.
- Fleet interlock (fresh `git status --porcelain` sweep over ALL sibling worktrees, this attempt, listed in the phase result): dirty code surfaces concentrate on run-041a92f6 (token_store.py, operator_config.py, operator_session.py, operator_swarm.py, operator_runners.py, codex_config.py, operator_codex.py, fabric_artifacts.py, MANIFEST.in, pyproject.toml + NEW atomic_write.py/test_atomic_write.py/test_package_docs.py — an atomic-write + shipped-docs batch in flight), run-e13b1c0d (the same config/token/session/swarm family + oauth_auth.py, server.py, mcp_compat.py), run-2f81870e (operator_cron.py, operator_failure_semantics.py), run-b6659410 (ui_chat.py, operator_live_events.py, server.py, tools/upstream_gap.py). **Zero collisions with this batch's surfaces** (ui_security.py, operator_mission.py, test_ui_security.py, test_operator_mission.py — none dirty anywhere; not touched by the 1a6beeba landing either).
- Fleet id note: my rm-131..rm-135 mint raced bf4db34f's rm-131..rm-140 (different meanings, its worktree at 941f4cfc69) and c5fba76a (self-renumbered away to rm-141..rm-150). Landed-first ids stay; landing gates renumber. Ids below refer to THIS worktree's ROADMAP meanings.

## Universe scan (54 unresolved: 48 candidate + 4 open + 2 deferred; statuses refreshed by CONTENT at HEAD per standing rule, not by label)

Top competitors by roadmap priority: rm-053 (135, open — loader-delegation decision gated upstream), rm-081 (115 — subsumed by v0.13 adoption), rm-131 (105), rm-008 (85), rm-077 (70), rm-048 (70), rm-010 (70), rm-028 (68), rm-054 (65), rm-132 (60), rm-083 (60), rm-046 (60, open), rm-005 (60), rm-038 (55), rm-082 (55), rm-052 (55), rm-015 (55), rm-034 (52), rm-133 (50), rm-055 (50), rm-035 (50), rm-024 (50), rm-006 (50), rm-036 (48), rm-134 (45), rm-011 (45), rm-135 (40), rm-037 (40).

## Scoring (selected candidates)

| item | impact | risk if unfixed | effort | deps | strategic | score |
|---|---|---|---|---|---|---|
| rm-131 off-loop /api/me + /api/connection | HIGH — the browser connection poll (web/src/stores/connection.ts:9) and account banner run synchronous TokenStore.status (token_store.py:1019, sqlite3.connect timeout=15.0 :372) on the event loop; one slow token DB stalls ALL loopbound traffic incl. SSE/WS on the busiest UI surface | silent whole-UI stall under contention; third un-offloaded slice of the rm-076 family | S (wrap the two payloads' status reads in asyncio.to_thread — in-file precedent ui_chat.py:620/:638/:672 — + async stall-regression test; sync TestClient cannot see it) | none | closes the rm-076 remainder family; no behavior change | 9.3 |
| rm-132 _24h keys report all-time | HIGH — hermes_mission_usage tokens_24h/by_profile/estimated_cost_24h_usd (operator_mission.py:1424 unfiltered SELECT) silently report the deployment's FULL history under 24h names; operators over-count daily burn by everything before the window | silent wrong cost signal on a P2 diagnostic surface; test_operator_mission.py:569-576 bakes the bug in (timestamp-less fixture summed as _24h) | S (apply the existing :1404 cutoff via the join the :1422 comment intends, with a loud schema-drift fallback; split the fixture into two windows) | none | fresh first-party finding this run; exact acceptance already written | 9.0 |

## SELECTED BATCH — "operator-visible signal correctness: unblock the serving loop, fix the 24h usage keys" (this cycle)

Order = implementation sequence; items independent:

1. **rm-131** `ui_security.py` + `test_ui_security.py` — me_endpoint :642 / connection_endpoint :646 keep payload SHAPE identical but move the account_status :494 → TokenStore.status chain off the event loop (asyncio.to_thread, mirroring ui_chat.py:620/:638/:672). Gate: new async regression test that blocks the token-store path and asserts a concurrent lightweight async handler still completes; existing test_ui_security.py stays green; ruff clean.
2. **rm-132** `operator_mission.py` + `test_operator_mission.py` — filter the usage query by the existing 24h cutoff (sessions.started_at join per the :1422 intent; fail LOUD on schema drift, never silently all-time). Gate: extend the :569-576 fixture with a pre-cutoff usage row asserted EXCLUDED from _24h sums; recent rows still counted; full test_operator_mission.py green.

Batch shape: 2 source surfaces + 2 existing test files; est. delta small (tens of lines + tests), well inside sibling precedent; zero product-invariant pressure; zero fleet collisions (sweep above); all gates local (ruff + focused lanes + full suite under fleet load). Two focused items is deliberate: both are P2s with fresh first-party evidence from THIS run, and the fleet is saturating every larger surface — a tight, fully-gated batch beats a broad one that rebase-collides at landing.

## Exclusions (with reasons — recorded so the next cycle inherits the reasoning)

- **rm-053 (135, open)** / **rm-054 (65)**: loader-delegation reconciliation gated on upstream PR #76 / v0.13 adoption; strip-grammar slice implemented-pending-commit elsewhere. Rides the adoption cluster.
- **rm-081 (115)**: subsumed by v0.13 adoption (fleet rm-085/098/103/105/116/130 own it; rm-083 blocked on the untagged v0.13.0).
- **rm-008 (85) / rm-010 (70) / rm-024 (50) / rm-038 (55)**: require gh-admin rights or CI runs — prohibited this cycle.
- **rm-046 (60, open)**: HARD COLLISION — run-041a92f6's dirty batch holds MANIFEST.in, pyproject.toml, docs/README.md, test_package_docs.py (+ new atomic_write.py family) right now; this run's F4 refresh note feeds THEIR landing, not a competing implementation.
- **rm-005 (60)**: operator_session.py held dirty by 041a92f6 + e13b1c0d.
- **rm-077 (70)**: web toolchain refresh — L effort, node build path, staged per its own status.
- **rm-048 (70) / rm-036 (48) / rm-082 (55) / rm-011 (45)**: spec/SDK-probe-gated; this run's research re-verified MCP spec still at 2026-07-28 and zero open upstream/fork issues+PRs — no external pull; keep waiting.
- **rm-133 (50)**: first-runner NEXT cycle — its acceptance legs include pushing deployed/master (push prohibited this cycle) and a release-blocker gate that belongs to a landing/ops action; a code-only doctor slice would land the item partially open by construction.
- **rm-134 (45) / rm-135 (40)**: HARD COLLISION, triple-held — 041a92f6's in-flight atomic_write.py batch IS the fixed-name-staging fix across the exact 14-site census (token_store/operator_config/operator_swarm/operator_session/operator_runners/codex_config/operator_codex/fabric_artifacts), e13b1c0d holds the same files, and b6659410's unlanded rm-114 claims the token_store key-perms half; re-implementing here guarantees double-landing.
- **rm-034 (52)**: oauth_auth.py/token_store.py held dirty by e13b1c0d/041a92f6.
- **rm-037 (40)**: peer entry point lives with mcp_compat.py (e13b1c0d dirty).
- **rm-015 (55) / rm-006 (50)**: audit-retention feature work on operator_events.py-family readers — adjacent to 2f81870e's in-flight rm-104 (same file); rebase risk + M effort. Strong next-cycle candidates.
- **rm-028 (68) / rm-035 (50)**: [tool.ruff] config commit — cross-claimed by 099e2bfc rm-120; pyproject.toml is a four-way dirty file this cycle.
- **rm-001 (90) / rm-002 (100)**: standing programs, not one-cycle batches.
- **rm-052 (55) / rm-055 (50) / rm-011+ leftovers**: watch-items and hygiene sweeps that don't outrank the selected P2s at this batch size.

## Hand-off to implement

- Verify at start: HEAD caf60018d2, `M ROADMAP.md` (uncommitted, roadmap phase) + this file untracked; no other drift.
- Verify at end: ruff clean on ui_security.py/operator_mission.py; each item's gate tests added and green; full suite delta ≈ +3–6 tests, zero regressions; tree carries exactly the batch diff + ROADMAP status updates (flip rm-131/rm-132 to `status: candidate (selected cycle 2, run 61db9bce246a)` — do NOT mark implemented; landing gate owns that).

## Outcome (compound 34b85e5e, 2026-10-03 — post-validation, pre-review)

Both selected items implemented + validated; statuses flipped in ROADMAP.md by THIS phase (the hand-off above deferred the flip past implement because it was written pre-validation; fleet compound precedent — run-684b9786's "all four flipped", run-0c8974's "implemented-pending-commit-gate", rm-076's own update bullet — places the post-validation status flip at compound, with the pending gates named so the landing gate still owns final resolution): rm-131 and rm-132 → `implemented (pending review/commit gates …)` + dated implementation-record bullets.

Validation record (consumed, not re-run): targeted impact set `207 passed in 21.83s` / 0 failed (attempt 204198f0, -o addopts= -q -n 8); ruff clean on all 4 changed py files under ambient 0.15.10 AND uv 0.15.22; dispatched full_command VERBATIM via scripts/local_validation_gate.py --shell-command 'python -m pytest -q' → gate exit 0 / completed / 1611 collected / zero F-E / 10 skips / ~241.8s (attempt d2875b62, result-1665710-350413078.json; fresh uv py3.11 venv; mcp 2.3.0 + starlette 1.7.0 resolved — supersedes the research digest's 2026-10-01 "no 2.3.x exists" line, dated update recorded in ROADMAP.md).

Tree at compound end: 7 modified (batch files + ROADMAP.md) + this file and stewardship-request-61db9bce.md untracked; learnings (prevention rules 41-46) and next-cycle context recorded in ROADMAP.md's cycle-2 outcome section.
