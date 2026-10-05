# Prioritization — repository-maintenance b4801f968fca cycle 3, run c7f77193824c

Base: worktree HEAD c43d085121 (== origin/master at assess time; origin has since moved to
d163cda227 via PR #29, verified by research). Inputs: this run's assess (831640be) + research
(c7c79bc485) + roadmap sync (7fe666eb, which minted rm-228 and recorded 7 update blocks), plus
a fresh code-truth pass over the open stack performed THIS phase (statuses lag code; see
coverage findings).

## Coverage findings (code truth at HEAD c43d085121, verified this turn)

Landed (board status still stale — flip belongs to the landing gate / render, NOT to a new batch):

- rm-076 — ui_chat.py:620/:638/:672/:674/:692-694 asyncio.to_thread + operator_live_events.py:369
  limiter comment; test_ui_ops.py:643 has a read_markers cap test.
- rm-151 — ui_security.py:623 "rm-151: the /api/me and /api/connection payloads are built in
  worker threads".
- rm-095 / rm-080 — operator_live_events.py:278/:285 `next_cursor = max(next_cursor, int(high or 0))`
  (high-watermark clamp implemented as the acceptance's second option).
- rm-131 — ui_ops.py:173 _CRON_DISPATCH_LIMIT + test_ui_ops.py:712 "rm-131: capacity intact".
- rm-132 — operator_cron.py:198 `_schedule_preview` (next-fire preview + effective tz).
- rm-096 — ui_missions.py:125-135 long-poll draws from a dedicated `_MISSION_EVENTS_LIMITER`
  (module comment: shared pool starvation avoided by design).
- rm-097 — ui_ops.py:160-185 "rm-097: bounded, registry-tracked dispatch": BoundedSemaphore,
  _DISPATCH_REGISTRY_LIMIT=50, completion-time audit with real outcome, doctor's ui_cron_dispatch.
- rm-078 — operator_diagnostics.py:646-661 `_check_ui_mount` WARN from ui_mount audit records.
- rm-042 — updater.py:62-66 `_is_hermes_gpt_checkout` + :86-87/:139 dirty-worktree refusal.

Verified still OPEN at HEAD (the actual unresolved stack):

- rm-134 — zero Sec-Fetch-Site/Origin/Content-Type handling in ui_chat.py / ui_ops.py /
  ui_security.py / server.py (grep clean).
- rm-152 — hermes_state.py:42-43 `started_at REAL` / `last_activity_at REAL` vs
  operator_mission.py:904/:1406 ISO-string cutoffs (sessions_7d / _24h windows structurally
  zero; matches the live-proven sibling assess result at master).
- rm-046 — tools/check_package_hygiene.py has no docs-link assertion; 3 of 36 tracked docs
  ship nowhere (runtime-checkout.md — linked from the docs/README authority map —,
  maintenance-cycle-log.md, vnext-capability-manifest.md).
- rm-048 — .github/workflows/ci.yml pins mcp 1.28.1/2.0.0/1.30.0/2.2.0; no 2.3.x lane;
  stale "research 2026-09-20" comment (research verified 2.3.0 safe to adopt now).
- rm-077 — README.md:159/:405 reference release wheels/hygiene; the npm build path for the
  browser UI is still undocumented for operators.
- rm-054 — not re-verified this turn; post-v0.14 the loader landscape changed (needs a fresh
  scope audit before selection).

Cross-campaign collision map (avoid duplicating in-flight/claimed work):

- Sibling run bd7f8ef7ddc1 (worktree at b1dfb2b8ad, uncommitted roadmap diff only, zero code)
  claims rm-217..rm-227: artifacts workspace (N1), dep floors (N2->rm-218), swarm/codex
  concurrency (rm-219), SSE resume (rm-220), finance request_id (rm-221), hermes-agent
  SHA-pin (rm-222), TLS minimum_version (rm-223), repo hygiene (rm-224), MCP elicitation
  (rm-225), A2A smoke (rm-226), ui_chat last-activity (rm-227). NONE of these enter our batch.
- rm-153/rm-154 territory is partially claimed (sibling rm-219 staging rider + a stale dirty
  worktree run-9037c3156272 with skill-resolution files); excluded for collision + risk.
- rm-040/rm-027/rm-099 edit pyproject dependencies — same-file friction with sibling rm-218's
  floor refresh; excluded this cycle.

## Prioritization criteria (per work order)

impact (user/operator-visible defect > posture > breadth), risk (lower wins for a coherent
in-cycle batch; one M-risk item max), effort (S-M per item; cycle-1 discipline "1 M + 2 S"
scaled), dependencies (no design/product gates, no admin/CI-only gates, no unverifiable-here
lanes), strategic value (product invariants: loopback boundary, fail-closed, operator truth).

## Selected batch — "Operator truth + boundary integrity" (5 + 1 optional)

1. rm-152 (reliability, headliner — correctness). Fix REAL-vs-ISO: usage rows filtered by
   sessions.started_at >= epoch cutoff with the schema-drift fallback (missing started_at ->
   fail loud or explicitly degraded, never silently all-time); stale pre-cutoff row asserted
   EXCLUDED from _24h sums; baked test -> two-window fixture; full test_operator_mission.py
   green. Impact HIGH (every dashboard window is structurally zero today — live-proven),
   risk LOW (read-path SQL + existing tests), effort S-M.
2. rm-134 (security, headliner — M). POST routes reject Sec-Fetch-Site: cross-site and Origin
   outside the allowed set (UI origin + chatgpt.com + issuer), require
   Content-Type: application/json on JSON-body routes; ChatGPT origin keeps working; non-browser
   MCP clients unaffected; escape-hatch env documented; tests cover allow/deny/cross-site/
   preflight. Impact HIGH (CSRF/DNS-rebinding class against the loopback-boundary invariant),
   risk M (compat constraints encoded in acceptance), effort M.
3. rm-046 (tooling rider). NEW guard test: every docs/*.md link target in README.md and
   docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical
   docs); the 3 unshipped docs shipped or de-referenced; runtime-checkout.md refreshed or
   re-labeled historical; build + twine + check_package_hygiene green. Impact MED-HIGH
   (authority-map links a doc that ships nowhere), risk LOW, effort S.
4. rm-048 (platform rider). docs/mcp-compatibility.md lineage-per-SDK-family correction;
   rm-009 revision assertion parameterized per installed pin; mcp==2.3.x CI lane (or pins
   refreshed per rm-009 cadence) + spec-delta review note; oauth.md cross-RFC notes; refresh
   the stale ci.yml:47-51 comment date. Impact MED, risk LOW (research verified 2.3.0 safe:
   no httpx dep, zero x-mcp-header consumers), effort S.
5. rm-139 (tooling rider). tools/check_roadmap_ids.py: unique ids, monotone frontier, status
   grammar, next-free-id given a configurable fleet frontier; wired as a test; catches the
   historical duplicate-id cases on this file. Impact MED (this cycle's own rm-217..rm-227
   collision management was done by hand — operationalize it), risk LOW, effort S.
6. Optional XS (explicitly out-of-scope-allowed per campaign convention): rm-079 — filter once
   at the boundary / drop the `queried` computation; mixture behavior locked by tests.

Exit criteria for the batch: all listed acceptance clauses green in-worktree; suite green in
CI shape; CHANGELOG entries where user-visible (rm-152 certainly, rm-134 yes); no tracked-file
drift beyond the batch's intended edits; docs rules honored (exact tool/env names, gates
stated explicitly).

## Deliberately deferred (with rationale)

- rm-076/rm-151/rm-095/rm-096/rm-097/rm-131/rm-132/rm-078/rm-080/rm-042: verified landed
  above — awaiting landing-gate status flips, not work.
- rm-133 (fork/PyPI identity): decision-first owner gate (never-publish vs +local segment);
  escalated by this run's roadmap update; no fork release is imminent (rm-083 blocked), so the
  decision is not cycle-blocking. Do NOT let a delegate pick the policy.
- rm-100 (3.11 floor): ride the 0.15.0 planning wave (roadmap update 2026-10-04).
- rm-077 (UI build path): docs-only + dist-verification is environment-dependent; bundle with
  a release-prep cycle.
- rm-054 (skill validation breadth): needs a fresh post-v0.14 scope audit; next-cycle candidate.
- rm-002/rm-001 (coverage/refactor breadth): churn exclusion per cycle-1 verdict.
- rm-153/rm-154 + sibling-claimed rm-217..rm-227: collision avoidance (see map above).
- rm-052/rm-038/rm-043: CI/admin gates, unverifiable from the delegate environment.

## Carry-forward notes for implement

- rm-152: keep the epoch-key migration question closed (acceptance says persisted-row
  migration NOT required) — the fix is in the query/cutoff domain only.
- rm-134: the allowed-origin set must be derived from the existing CORS allowlist code, not
  a new constant; escape-hatch env needs an exact name in docs.
- rm-048: the CI lane edit is review-only from here (no CI runner) — pair it with the local
  spec-delta note so review has substance.
- rm-139: read the fleet frontier from a CLI arg (default: the landed frontier), never
  hardcoded — sibling boards shift daily.
