# hermes-gpt — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- upstreams (this repo builds on): .github, agent, hermes-infra
- dependents (changes here affect): (host), agent, maestro
- graph: evidence-derived (imports/refs/deploy surfaces); advisory

## Open items

### Adopt upstream skill-loader hardening trio (upstream issue #74 full half)
- id: `rm-081` | track: reliability | priority: 115.0 | status: candidate
- acceptance: merged tree reconciles fork+upstream halves into a single resolution authority; loader failure is fail-closed with a test proving a required-but-unloadable skill blocks dispatch; probes use preprocess=False with a test asserting inline_shell side effects never run during validation; fork surfaces (plan create/validate/placement) keep enforcement at parity with upstream's breadth (work contracts/swarm); full suite + upstream's new tests green on both SDK lanes
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-01: cycle-2 research C1 (run-61db9bce, research 4658b239, first-party probes 2026-10-01): the v0.13 window CONTAINS this trio — upstream/master f4151d9728 sits 9 commits past merge-base 7795aa3ce8 (58 files, +11252/-112, incl. test_operator_skill_resolution.py +329), so adopting v0.13 subsumes this item; adoption is separately owned fleet-wide (sibling ids: 0aa75ea4 rm-085; 1a6beeba rm-098; b6659410 rm-103 + 2f81870e rm-105; 099e2bfc rm-116; b6b8792f rm-130) — it resolves with whichever adoption lands first, by fold. Still gated at probe time: upstream tags stop at v0.12.0 (v0.13.0 untagged; PRs #83/#84 open), so rm-083 stays blocked and this item's acceptance rides the adoption batch
- update 2026-10-03 (integration e40491ed93d5): upstream v0.13 HAS landed in this tree (125255c0bc 'adopt upstream v0.13 — Autopilot mission runtime, upstream skill resolution' #25, plus the 736af6ff0b ancestry stitch and the follow-on autopilot commits #26-#28), so the loader trio is carried here — this item now closes by fold against that landed adoption once its fail-closed/parity acceptance legs are verified on the merged tree; no separate implementation

### Adopt upstream v0.13 Autopilot (9-commit gap; PR #82)
- id: `rm-098` | track: reliability | priority: 115.0 | status: candidate
- acceptance: the 9 upstream commits merge or cherry-pick onto the fork line with conflicts reviewed line-by-line against fork invariants (Owner Mode break-glass, secret-path denials, default read-only; Autopilot stays default-off at adoption); full suite green in CI shape; CHANGELOG records the catch-up; #83/#84 recorded as follow-on once merged upstream
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Move blocking SQLite off the serving event loop (ui_chat + live-events WS)
- id: `rm-076` | track: reliability | priority: 110.0 | status: in_progress
- acceptance: every blocking SessionDB/live-event-store call reachable from async handlers/WS runs via asyncio.to_thread (or equivalent executor offload); a regression test holds SessionDB._lock in a background thread and asserts a concurrent ui_chat request completes within a bound (no loop starvation); the WS poll path performs no connect-timeout or sqlite work on the loop thread
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Offload /api/me + /api/connection status reads off the serving loop (rm-076 remainder)
- id: `rm-151` | track: reliability | priority: 105.0 | status: implemented (run 61db9bce cycle 2, implement 412d1e51, compound 34b85e5e; landed at integration e40491ed93d5 — orig id rm-131 in that run, renumbered at landing because landed rm-131 is the ui_ops cron-dispatch semaphore item; landed-first ids stay)
- signals: run-61db9bce assess-F1 — ui_security.py me_endpoint and connection_endpoint were async handlers that called, directly on the serving event loop, me_payload / connection_payload -> account_status -> TokenStore.status (token_store.py), a synchronous sqlite read (sqlite3.connect timeout=15.0) plus execute/fetchall; web/src/stores/connection.ts fetches GET /api/connection as the browser's connection/restart poll, so one slow or contended token DB stalls ALL loopbound traffic (SSE generators, WS pumps) while the operator UI waits on the poll, and /api/me rides the same lane for the account banner; the defect class had already been fixed in sibling code via asyncio.to_thread (in-file precedent ui_chat.py session-DB off-loads) and again on the OAuth token lanes — a third rm-076 remainder slice
- acceptance: both payloads' token-store reads execute off the loop (asyncio.to_thread or the in-file equivalent); regression test holds the token-store path blocked and asserts a concurrent lightweight async handler still completes (a sync TestClient cannot observe this — use the async test pattern rm-076's suite established); payload shapes unchanged; a note lands in docs/ui-security-boundary.md transport-health section that the poll endpoint is off-loop
- evidence: diff + new stall-regression test green; grep exhibit that the me/connection payload call-paths contain no direct sqlite3 calls
- update 2026-10-03: IMPLEMENTED + validated (run 61db9bce, implement 412d1e51, compound 34b85e5e): me_endpoint + connection_endpoint build payloads via asyncio.to_thread (ui_security.py, payload shapes unchanged; TokenStore.status opens its own connection per call, so the off-load is thread-safe); new load-tolerant stall-regression test test_ui_security.py::test_connection_and_me_do_not_stall_event_loop blocks the status read and asserts a concurrent loopbound handler completes — no wall-clock assertion, so it stays stable under fleet load; sensitivity proven by revert tripwire (both off-loads reverted in place -> the test failed with its named message, then restored); docs/ui-security-boundary.md off-loop note + CHANGELOG Unreleased bullet; targeted impact set 207 passed / 0 failed (attempt 204198f0), dispatched full gate exit 0 (attempt d2875b62); landed with this integration

### Add test coverage for 16 untested module(s)
- id: `rm-002` | track: reliability | priority: 100.0 | status: candidate
- signals: reliability.no_tests:hermes_state.py, reliability.no_tests:tools/check_package_hygiene.py, reliability.no_tests:web/src/chat/ActivityCard.tsx, reliability.no_tests:web/src/chat/ChatPage.tsx, reliability.no_tests:web/src/chat/Composer.tsx (+11 more)
- acceptance: Every module in ['hermes_state.py', 'tools/check_package_hygiene.py', 'web/src/chat/ActivityCard.tsx', 'web/src/chat/ChatPage.tsx', 'web/src/chat/Composer.tsx', 'web/src/flight/AccountPanel.tsx', 'web/src/flight/ApprovalsPanel.tsx', 'web/src/flight/ContractsPanel.tsx', 'web/src/flight/DeckOverview.tsx', 'web/src/flight/EventHistoryPanel.tsx', 'web/src/flight/FleetPanel.tsx', 'web/src/flight/schemas.ts', 'web/src/shared/AccountStatusBanner.tsx', 'web/src/shared/ConnectionStatus.tsx', 'web/src/stores/session-list.ts', 'web/vite.config.ts'] has a corresponding test file with at least one passing test
- evidence: full suite green (python -m pytest -q) at HEAD; conductor validation digest validation:v1:<sha> recorded in the shipping PR

### Refactor 20 high-complexity function(s)
- id: `rm-001` | track: reliability | priority: 90.0 | status: candidate
- signals: reliability.complexity_hot:operator_autopilot.py::build_summary, reliability.complexity_hot:operator_contract.py::_check_forbidden, reliability.complexity_hot:operator_delegations.py::hermes_delegation_cancel, reliability.complexity_hot:operator_delegations.py::hermes_delegation_dispatch, reliability.complexity_hot:operator_delegations.py::hermes_delegation_reconcile (+15 more)
- acceptance: Each flagged function is decomposed below the branch threshold with behavior locked by characterization tests
- evidence: ast-based branch-count check passes at HEAD (full suite green; conductor validation digest validation:v1:<sha> recorded in the shipping PR)

### Isolate the mission-events long-poll from the shared anyio threadpool
- id: `rm-096` | track: reliability | priority: 90.0 | status: in_progress
- acceptance: long-poll waits no longer occupy shared threadpool tokens — a dedicated anyio.CapacityLimiter (anyio.to_thread.run_sync(limiter=...) verified in .venv) for wait-bearing endpoints, or an asyncio-native wait bridge; a regression test saturates the shared limiter with 40 holders and asserts a mission-events request still completes; existing mission-events behavior (25s max wait, event delivery, cursor semantics) unchanged
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### ui_ops cron-dispatch semaphore leaks on resolve failure
- id: `rm-131` | track: reliability | priority: 90.0 | status: in_progress
- acceptance: dispatch-path ordering fixed — resolve root (and any other raising validation) BEFORE acquiring the semaphore, or try/finally the acquire→dispatch span so every exit releases the token; regression test injects a `_resolve_root` failure and asserts (a) a clean error response, (b) semaphore capacity unchanged — a subsequent dispatch is NOT 429-capped — repeated > `_CRON_DISPATCH_LIMIT` times.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Registry and bound for fire-and-forget cron dispatch, with completion audit
- id: `rm-097` | track: reliability | priority: 88.0 | status: in_progress
- acceptance: cron dispatch goes through a bounded executor with an operator-visible registry (active/finished counts surfaced via doctor or an ops live event); a completion record (success/failure + duration) lands in the audit trail when the run finishes, not at dispatch; a cap-exceeded request is rejected loudly (429-class) like ui_chat; tests cover dispatch, completion-audit ordering, injected-failure audit, and cap rejection
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Adopt next_cursor on empty filtered pages in the WS live-events loop (rm-080 residual)
- id: `rm-095` | track: reliability | priority: 85.0 | status: in_progress
- acceptance: the WS loop advances its cursor to the returned next_cursor on empty pages too (or an equivalent watermark adoption), preserving rm-080's snapshot-ordering guarantee (a concurrent insert is delivered or rescanned, never skipped); a regression test asserts an idle filtered WS client advances past N non-matching events without rescanning them; the docs/live-events.md cursor-semantics paragraph holds verbatim
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Python floor bump 3.10->3.11 plus a 3.13 CI lane (dated deadline)
- id: `rm-100` | track: reliability | priority: 75.0 | status: candidate
- acceptance: CI matrix adds a green 3.13 lane (and 3.14 if deps allow); a dated plan lands the 3.11 floor bump with the next fork release (requires-python >=3.11, matrix drops 3.10, tomli conditional removed); CHANGELOG records both
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### cron next-fire + timezone preview at arm time
- id: `rm-132` | track: reliability | priority: 72.0 | status: in_progress
- acceptance: hermes_cron_create dry-run plan (and the browser-UI confirm surface) include next-N (>= 3) computed fire times plus the effective timezone name used to resolve them; works for interval, daily-time, weekday, and once schedules; plan does not imply the external scheduler's tz is authoritative (contract documented in docs/operator-mode.md cron section); tests cover each schedule kind including a TZ-set environment.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### MCP spec-revision lineage refresh + SDK 2.3.x lane
- id: `rm-048` | track: reliability | priority: 70.0 | status: in_progress
- acceptance: docs/mcp-compatibility.md corrected to describe the revision lineage per SDK family instead of claiming one "latest"; the rm-009 revision assertion parameterized per installed SDK pin (still fails loudly on unexpected revisions); a mcp==2.3.x lane added to CI (or pins refreshed per rm-009's cadence rule) with a spec-delta review note for hermes surfaces; MCP-Auth cross-RFC notes (RFC 9728/9700 now Proposed Standard, draft-ietf-oauth-parallel-refresh adopted) reflected in docs/oauth.md where they touch hermes behavior
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Ship or document a browser-UI build path (web assets absent from wheel/MANIFEST)
- id: `rm-077` | track: reliability | priority: 70.0 | status: candidate
- acceptance: EITHER the wheel/sdist carries a prebuilt web/dist (with a package-hygiene assertion), OR README + docs/operator-mode.md document the exact supported build step (npm ci && npm run build / HERMES_GPT_UI_DIR) verified to produce a served UI; tools/check_package_hygiene.py extended to match whichever path is chosen
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### fork distribution identity: local version segments or never-publish
- id: `rm-133` | track: reliability | priority: 68.0 | status: candidate
- acceptance: decision recorded FIRST — (a) local version segment (e.g. 0.12.0+codeo1io or +<line-tag>) on fork releases, or (b) explicit never-publish-on-PyPI policy with a private index — in RELEASE_CHECKLIST.md + README; artifact metadata carries line provenance (commit or origin URL) so pip + doctor distinguish codebases; doctor VERSION line gains the line identity (extends operator_diagnostics.py:904); decision + implementation land BEFORE any 0.13-numbered fork release.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Extend skill validation to Work Contract and Swarm dispatch (hermetic #76 semantics)
- id: `rm-054` | track: reliability | priority: 65.0 | status: candidate
- acceptance: contract creation and pre-dispatch revalidation fail closed with distinct not_found/unavailable codes and zero mutation on rejection (tests pin the no-mutation path); candidates preview and score share one validation entry point so their verdicts are identical for identical inputs (assess-F7 scenario replayed divergence-free); docs state where validation runs (AGENTS.md docs rules: exact surfaces, explicit gates)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Surface ui_api mount failure as an operator-visible signal
- id: `rm-078` | track: reliability | priority: 65.0 | status: in_progress
- acceptance: a failed UI mount emits an operator live event AND an audit record (or a doctor WARN) while the server still boots; a test simulates the import failure and asserts the signal fires exactly once; docs/operator-mode.md notes the failure mode
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-09-30: IMPLEMENTED in run-bb9c68fb (implement f216d170, since landed): server._signal_ui_mount_failure emits an audit record + ui_mount_failed live event on mount failure, and hermes_operator_doctor's 'ui_mount' check reads the audit tail (WARN/UI_MOUNT_FAILED); a test simulates the import failure through the full ASGI stack and asserts audit + doctor; docs/operator-mode.md updated
- update 2026-10-01: cycle-2 assess refresh (run-61db9bce, assess 727758f1 finding F5): the implemented doctor signal can FALSE-PASS — _check_ui_mount reads the audit TAIL (operator_diagnostics.py, audit_tail(limit=50)), so >=50 later audit rows bury the ui_mount failure and the check reports UI_MOUNT_HEALTHY over a still-degraded mount; the durable fix is ALREADY minted by siblings — rm-093 (0aa75ea4, implemented in its worktree), rm-111 (b6659410), rm-119 (099e2bfc, partially implemented there; remainder = stateful doctor signal) — so no new id here: land one of those, not a fourth duplicate

### fetch-metadata + content-type hardening on browser-UI state changes
- id: `rm-134` | track: reliability | priority: 63.0 | status: candidate
- acceptance: state-changing (POST) routes reject Sec-Fetch-Site: cross-site requests and Origin headers outside the allowed set (UI origin + chatgpt.com + issuer), and require Content-Type: application/json on JSON-body routes; the ChatGPT-side origin keeps working (it is in the CORS list today); non-browser MCP clients unaffected; any escape-hatch env documented; tests cover allow/deny/cross-site/preflight cases.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Raise build floor to setuptools>=77 (PEP 639 license string)
- id: `rm-027` | track: reliability | priority: 62.0 | status: in_progress
- acceptance: floor raised to >=77 (or license switched to table form) so declared-floor builds work; sdist+wheel build verified in a --no-isolation environment; no behavior change to isolated CI builds
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-046` | track: reliability | priority: 60.0 | status: in_progress
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refreshed or re-labeled as historical; `python -m build` + `twine check dist/*` + tools/check_package_hygiene.py dist/* run with the two docs present
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-01: cycle-2 assess refresh (run-61db9bce, assess 727758f1 [adopting reaped fbb8862d] finding F4, at that run's HEAD caf60018d2): the gap re-counted from the manifest side — MANIFEST.in ships ONLY `include docs/README.md` while docs/README.md links 12 docs the sdist does not ship by rule: cloudflare-tunnel, delegations, file-export, finance, flight-deck-missions, live-events, maintenance-cycle-log, missions, openai-secure-mcp-tunnel, runtime-checkout, session-control, session-history (method: comm of docs/README.md link targets × ls docs/*.md against `^include docs/` MANIFEST lines); the earlier data-files note is the same defect from the other side — the still-open guard should pin the README-links × data-files × MANIFEST triple together, not one list at a time

### v0.13.0 release-readiness batch: publish + deployed-remote rollout
- id: `rm-083` | track: reliability | priority: 60.0 | status: candidate
- acceptance: RELEASE_CHECKLIST executed for v0.13.0 (or the next fork version): CHANGELOG sectioned, package built + twine/check_package_hygiene verified, version policy resolved per rm-065, deployed remote rolled forward and verified (operator doctor clean); release notes state distribution channels truthfully (no implied GitHub/PyPI sync)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### live-deployment provenance capture + uncommitted-delta release blocker
- id: `rm-135` | track: reliability | priority: 60.0 | status: candidate
- acceptance: provenance-capture doctor check (or deploy-time record) captures the serving process's self-reported version + working-tree state (commit, dirty flag, branch) into a durable operator-visible record; a release/ops rule BLOCKS promoting a build whose live checkout carries uncommitted deltas (or forces an explicit override with the delta recorded); docs/runtime-checkout.md refreshed or re-labeled per AGENTS.md rules as part of the fix.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-03 (integration e40491ed93d5, run-61db9bce research C3 FOLDED here): this item also absorbs that run's orig rm-133 ('deployment provenance: make the live sidecar's identity attributable and gated') — same defect, co-discovered the same day; the folded half's extra signals: the live sidecar self-reported serverInfo version 0.12.1 while the serving venv resolved hermes_gpt-0.11.0.dist-info (editable install on a host-local deployed/master 53 commits behind fork master) and no repo ref produces the string '0.12.1' (git log -S negative in both repos) — the live identity was unattributable to any audited source; added acceptance legs: serverInfo version derives from a repo-tracked source of truth, and deployed/master becomes a pushed, tracked ref with a stated refresh policy instead of host-local drift. Sibling c5fba76a rm-148 (unlanded) covers the same doctor-capture half — dedupe by content before implementing

### Correct hermes_mission_usage _24h keys — they previously reported all-time totals
- id: `rm-152` | track: correctness | priority: 60.0 | status: implemented (run 61db9bce cycle 2, implement 412d1e51, compound 34b85e5e; landed at integration e40491ed93d5 — orig id rm-132 in that run, renumbered at landing because landed rm-132 is the cron next-fire/timezone preview item; landed-first ids stay)
- signals: run-61db9bce assess-N1 (the assess's "5+1" fresh finding; the landed cycle-6 maintenance log cross-references the same finding as "61db9bce assess F6") — operator_mission.py read `SELECT * FROM session_model_usage` UNFILTERED while the sibling session count applied the 24h cutoff, and the adjacent comment stated the join/filter intent as unimplemented; tokens_24h / by_profile / estimated_cost_24h_usd therefore reported all-time totals under 24h names, so an operator reading yesterday's token burn saw the deployment's full history; the pre-fix test baked the bug in (its fixture usage rows carried no timestamps and asserted their full sum under the _24h keys); secondary: the unfiltered read loaded every usage row into memory per call
- acceptance: usage rows joined/filtered by sessions.started_at >= cutoff with the schema-drift fallback the intent comment describes (missing started_at -> fail loud or explicitly-degraded output, never silently all-time); a new test with a stale pre-cutoff usage row asserted EXCLUDED from _24h sums; the baked test updated to a two-window fixture; full test_operator_mission.py green
- evidence: diff; new + updated tests green; before/after hermes_mission_usage tool output showing a stale row excluded
- update 2026-10-03: IMPLEMENTED + validated (run 61db9bce, implement 412d1e51, compound 34b85e5e): usage rows JOIN sessions and are windowed by started_at >= the existing cutoff; rows with no resolvable owning session are EXCLUDED from the _24h aggregates (they cannot be windowed); schema drift (no session_id/started_at link) degrades EXPLICITLY to all-time sums with a per-profile ALL-TIME warning appended to the envelope warnings — never silently all-time; test fixture now seeds a stale pre-cutoff usage row; net-new test_usage_24h_window_excludes_stale_sessions + test_usage_schema_drift_falls_back_to_all_time_with_warning, and test_usage_aggregates_across_profiles corrected to windowed expectations; CHANGELOG Unreleased bullet; landed with this integration

### declare the browser-UI agent-runtime cross-project seam
- id: `rm-136` | track: reliability | priority: 58.0 | status: candidate
- acceptance: the seam is DECLARED — vendored/stubbed interfaces behind an explicit boundary module, OR a documented contract (which external tree provides them, at what version) + an import-contract test that runs on the clean checkout and fails LOUDLY (never silent IMPORT_UNAVAILABLE) when the declared provider is missing; pyproject/docs name the external requirement; if a degradation path is kept, it is visible in doctor.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Branch protection on codeo1io master (extends rm-008 with red-master evidence)
- id: `rm-038` | track: reliability | priority: 55.0 | status: candidate
- acceptance: master branch protection requires the CI test+lint jobs with linear history; direct pushes restricted to admins; a red push/PR is observed to be rejected once
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Bound pyyaml (the last bare runtime dependency)
- id: `rm-040` | track: reliability | priority: 55.0 | status: in_progress
- acceptance: pyproject pins `pyyaml>=6,<7`; CI installs the bounded range green; cap moves become deliberate changelog events (rm-023 policy)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Stop .gitignore '*.ps1' from swallowing new example scripts
- id: `rm-047` | track: reliability | priority: 55.0 | status: in_progress
- acceptance: negation rule added; `git check-ignore examples/foo.example.ps1` exits 1 post-fix; tracked example set unchanged (`git ls-files examples/` identical); packaging still ships them
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### PyPI vs repo version drift guard
- id: `rm-052` | track: reliability | priority: 55.0 | status: in_progress
- acceptance: a CI job or release-checklist step queries PyPI and reports/fails on unacknowledged divergence >=1 minor; RELEASE_CHECKLIST.md references it
- acceptance: /oauth/register rate-limited (per-peer bound); dynamic clients gain TTL with cleanup() eviction; an operator list/purge surface exists; re-import revalidates redirect URIs; the :1206 comment made truthful; tests prove an unauthenticated fill-up cannot permanently exhaust the cap (TTL reclaim), expired clients fail closed at exchange, and the purge round-trip works; RFC 7592 update/delete shape optional stretch
- acceptance: the authorize path validates/encodes client_id before comparison and rejects with 401 JSON `invalid_client` (never a 500, never a redirect to an unvalidated client_id — RFC 6749 forbids redirecting unknown clients); a regression test mints a non-ASCII client_id and asserts the 401 JSON; no traceback in the audit path. (Acceptance wording amended at review-fix 31581701: the implemented 401-JSON contract is stricter than the originally drafted error-redirect wording and is what the review verified.)
- acceptance: docs (gemini-spark and/or an oauth section) state both knobs, their defaults, and the DCR=0 single-client recipe; the docstring describes the actual registry; per docs rules the claims are checked against code before landing
- acceptance: macOS binds the full runtime_roots list (or a comment documents why one root suffices on Darwin) with a unit test covering multi-root env-shebang resolution
- acceptance: authorize success and error redirects include iss=<issuer>; AS metadata advertises authorization_response_iss_parameter_supported: true; tests pin both; docs note added
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Serve the curated skill set via the official MCP Skills extension (read-only)
- id: `rm-082` | track: reliability | priority: 55.0 | status: candidate
- acceptance: gated on an SDK support probe passing on both SDK families (same gate pattern as rm-011); additive read-only surface exposing only allowlisted skills via skills/list + skills/get with skill:// resources; hermes_* skill tools remain canonical; safety tests prove no raw skill bodies or side effects leak beyond the existing read-only boundary; a deterministic tools/list ordering assertion (2026-07-28 spec SHOULD) rides this surface's tests
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Declare starlette and anyio as direct dependencies
- id: `rm-099` | track: reliability | priority: 55.0 | status: in_progress
- acceptance: pyproject declares starlette and anyio with bounds consistent with the resolved floor (e.g. starlette>=0.40,<2; anyio>=4,<5) and a comment naming mcp[cli] as the existing transitive source; CI installs green on the declared range; the declaration introduces no version drift (resolver output unchanged before/after)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Document the convergence-shipped OAuth surface and repair the CHANGELOG
- id: `rm-034` | track: reliability | priority: 52.0 | status: candidate
- acceptance: docs/oauth.md documents all three knobs (name, default, gates, security posture incl. knob-vs-endpoint semantics); CHANGELOG gains a convergence entry and the :12 run-on is fixed; AGENTS.md docs rules (defaults/gates explicit) satisfied
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Evaluate CIMD as the primary client registration path (strategic)
- id: `rm-053` | track: reliability | priority: 52.0 | status: in_progress
- acceptance: a design note decides CIMD adoption timing (SDK/tooling maturity, client support) vs bounded DCR; if adopted: client_id_metadata_documents_supported metadata flag, validation, and tests land; rm-055's hardening keeps a slot for it
- acceptance: both PRs rebased with conflicts resolved against master (a93aeb0b1d or later); packaging resolution keeps the converged pyproject + croniter>=2.0,<7 while adopting the manifest deletion + pyyaml>=6.0.3,<7 floor; skill resolution resolution reviewed against placement-ranking tests; full suite green in CI shape post-rebase; #19 merged = CVE floor landed; #20 merged = operator_skill_resolution.py on master; upstream PR #75 head refreshed from the landed state (stewardship)
- acceptance: one raise deleted; zero behavior change; targeted oauth tests green
- acceptance: one shared reader with a documented pid contract; both call sites consume it; parametrized tests cover int and numeric-string forms for both consumers
- acceptance: publish job moved to ubuntu-latest with the pypi environment + id-token trusted-publishing path verified, OR self-hosting explicitly re-affirmed with recorded rationale; stale comments refreshed; a workflow_dispatch/dry-run validation path documented
- acceptance: either a recorded occupancy rationale or a semaphore/bound on concurrent job_wait parks; the nonblocking pin test extended to the full offloaded set
- acceptance: bullet repaired; Unreleased section enumerates the user-visible converged changes; AGENTS.md release-discipline review list satisfied
- acceptance: study recorded (wire shape, SDK-2-only constraints, 1.28.1 degradation matrix, client-support reality); if adopted: one operator mutation tool returns InputRequiredResult with a dual-SDK test proving graceful refusal on 1.x; docs/mcp-compatibility.md gains a SEP-2322 section
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Commit a [tool.ruff] rule-set config on ruff 0.16 (extends run-fd2bc85f rm-028)
- id: `rm-035` | track: reliability | priority: 50.0 | status: candidate
- acceptance: a committed [tool.ruff] selects the enforced rule set explicitly; dev pin moves to a 0.16.x line; CI lint job green under the pinned ruff; a finding-count table (classic vs adopted set) with per-class disposition lands in the PR
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Regenerate .gitleaksignore against HEAD-reachable history and prune foreign refs
- id: `rm-055` | track: reliability | priority: 50.0 | status: candidate
- acceptance: .gitleaksignore regenerated from HEAD-reachable history only — every surviving entry justified by a reachable commit (PR #23's sentinels retained, foreign entries dropped); foreign refs pruned from the shared store with the 9 live heads verified untouched and other runs' working trees unaffected; a gitleaks scan scoped to HEAD-reachable commits reports zero findings; a triage-scope prevention rule added to the cycle learnings
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Conformance-check skill resolution against the PUBLISHED MCP Skills extension (extends run-684b9786 rm-028 / PR #20)
- id: `rm-036` | track: reliability | priority: 48.0 | status: candidate
- acceptance: conformance note mapping hermes skill surfaces onto the published extension (naming, discovery roots, precedence); PR #20's tests verified against it; upstream #74 outcome recorded when it lands (contract agreed architecture-first per run-684b9786 rm-028)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### SHA-pin the reusable private-leak-sentinel workflow
- id: `rm-043` | track: reliability | priority: 48.0 | status: in_progress
- acceptance: the reusable-workflow reference pins an immutable commit SHA (human-readable branch noted in a comment); a re-pin rotation procedure is documented
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### OpenAPI description generated from the 20-route HTTP surface
- id: `rm-137` | track: reliability | priority: 46.0 | status: candidate
- acceptance: an OpenAPI 3 document GENERATED from the route table (not hand-maintained prose), served at a read-only discovery endpoint or shipped in docs, with envelope schemas from the existing ok/err normalization; a contract test fails when a route's shape drifts from the document; the document is marked loopback-default/read-only-gates per product invariants.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Fail-fast on empty/invalid code_challenge at issuance
- id: `rm-018` | track: reliability | priority: 45.0 | status: in_progress
- acceptance: issue_authorization_code raises on empty/malformed challenge (internal callers get loud errors, not dead credentials); rm-003's empty-challenge-rejected-at-exchange test still passes; no valid flow regresses
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Docs/CHANGELOG truthfulness bundle (rm-027 semantics + walk-bound docstring)
- id: `rm-056` | track: reliability | priority: 45.0 | status: in_progress
- acceptance: CHANGELOG Unreleased entry documents the fail-closed semantics with an upgrade note for plans referencing unresolvable skills; the shipped-docs guard (rm-046 remainder) covers any new docs; the F8 docstring corrected to describe directory-count semantics (or the counter fixed to count entries, with a test); AGENTS.md "behavior changes → CHANGELOG" rule satisfied for this and future validation-gate landings
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Harden token/key file staging beyond chmod-after-write
- id: `rm-153` | track: security | priority: 45.0 | status: candidate (orig id rm-134 in run 61db9bce, renumbered at integration e40491ed93d5 because landed rm-134 is the fetch-metadata/content-type hardening item; explicit scope split from sibling b6659410's unlanded rm-114)
- signals: run-61db9bce assess-F2 — token_store.py stages secrets at FIXED names: key file '.hermes_keys.tmp' (write_bytes THEN chmod 0600 then replace — a 0600-before-first-write gap; two concurrent writers interleave on one path; a pre-planted symlink at that name is followed), the rotate branch '<key>.new' with the same pattern, envelope '.hermes_tokens.tmp'; secrets directories are mkdir'd with DEFAULT modes under process umask, so a permissive umask leaves secret dirs group/world-readable; there is no fsync before replace (a crash window can truncate key material); the token DB is create-then-chmod. SCOPE SPLIT — sibling b6659410 rm-114 (unlanded) already owns O_CREAT|0o600-at-creation for the key write plus WAL/-shm sidecar modes; THIS item owns the fixed-name staging names (tmp/.new), directory modes, fsync-before-replace, and the DB create-then-chmod window — do not double-implement rm-114's half
- acceptance: every staged secret file created with restrictive mode AT creation under a unique-adjacent name (in-repo precedent operator_cron.py / operator_workspace.py / operator_job_supervisor.py) or O_EXCL; secrets dirs mkdir with explicit 0o700; fsync of key material before the atomic replace; a umask-0 test asserting final file AND dir modes are 0600/0700; a two-writer test asserting no interleaved or lost staging writes; the token DB reaches 0600 with no observable window (or documents why it cannot)
- evidence: diff + umask/mode and concurrency tests green; ls -l exhibit of staged + final modes under umask 0

### cron NL-grammar edges: plural weekdays + property-based invariant lane
- id: `rm-138` | track: reliability | priority: 44.0 | status: in_progress
- acceptance: plural weekday names accepted (or a targeted error naming the singular form); a hypothesis property-based lane in the dev group (declaration comment naming the transitive source per the rm-099 rule) pins the four invariants with a fixed seed for deterministic CI; zero-minute floor coverage rides rm-057.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Updater must verify it found a hermes-gpt checkout before fast-forwarding
- id: `rm-042` | track: reliability | priority: 42.0 | status: in_progress
- acceptance: candidate roots are verified as hermes-gpt checkouts (pyproject name / package marker / remote URL) with a loud refusal otherwise; regression test using a foreign git-root fixture
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Single peer_main: dedupe the dead entry point and test the packaged peer CLI
- id: `rm-037` | track: reliability | priority: 40.0 | status: candidate
- acceptance: one canonical peer_main (dead one removed or repointed with a rationale comment); the packaged entry (g4c peer_main / its serve stack, port 4780) covered by at least one test exercising require-secure-transport and the CLI surface
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Retire fixed-name '.tmp' staging across operator write paths
- id: `rm-154` | track: security | priority: 40.0 | status: candidate (orig id rm-135 in run 61db9bce, renumbered at integration e40491ed93d5 because landed rm-135 is the live-deployment provenance item)
- signals: run-61db9bce assess-F3 — 14 write sites stage files at predictable fixed '.tmp' names: fabric_artifacts.py (2), operator_swarm.py, operator_config.py (3), codex_config.py (2), operator_codex.py (2), operator_session.py, operator_runners.py, token_store.py (2; that pair moves with rm-153 above) — concurrent writers interleave/last-write-wins and a pre-planted symlink at the known name is followed (same-machine other accounts or sandboxed jobs); the repo ALREADY has the safe unique-name pattern three times (operator_cron.py, operator_workspace.py, operator_job_supervisor.py) but nothing enforces it
- acceptance: every staging site uses a unique-adjacent temp name (pid+token or mkstemp) created with restrictive mode and atomically replaced; a repo-wide guard test fails on any NEW fixed-name staging path (scan '.tmp' literals constructed without a uniquifier, mirroring the census command `rg -n "\.tmp" --glob '*.py' -g '!test_*'`); the touched files' existing tests stay green; no behavior change beyond the name
- evidence: diff across the 13 non-token_store sites; guard test green plus a demonstration it fails on a reintroduced fixed name; before/after census output

### Profile-aware skill-resolution gate before placement/dispatch
- id: `rm-041` | track: reliability | priority: 38.0 | status: in_progress
- acceptance: placement/dispatch validates that the target profile can actually resolve each referenced skill at execution time (or fails loudly pre-flight); contract agreed architecture-first with upstream before implementation
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Gemini CLI client profile (user-need evidenced by upstream #54)
- id: `rm-049` | track: reliability | priority: 35.0 | status: in_progress
- acceptance: opt-in Gemini CLI client profile analogous to Gemini Spark (profile-aware session history + verified setup guide), default surfaces unchanged (read-only/dry-run ladder intact), test file mirroring test_gemini_compat.py; docs/codex.md terminology rules respected (client profile vs delegated worker)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Account-status banner is dead code on auth-configured deployments
- id: `rm-050` | track: reliability | priority: 35.0 | status: in_progress
- acceptance: EITHER the SPA obtains and attaches credentials (explicit login flow or same-origin cookie session) and /api/me returns payload under configured auth (tested, incl. unauthorized case), OR the banner is scoped/documented as local-mode-only with docs stating the auth-mode limitation
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### SEP-414 trace-context correlation for cross-agent runs
- id: `rm-084` | track: reliability | priority: 35.0 | status: candidate
- acceptance: correlation-only scope — accept and echo incoming traceparent into operator audit records and live events for MCP tool calls and delegation/codex dispatch (no full OTel SDK adoption); tests assert presence and passthrough; docs note the convention
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### roadmap id-allocation guard (tools/check_roadmap_ids.py)
- id: `rm-139` | track: reliability | priority: 35.0 | status: candidate
- acceptance: tools/check_roadmap_ids.py validates a given ROADMAP.md — ids unique across id lines (or a documented canonical-occurrence rule for boundary duplicates), monotone frontier, status grammar from a fixed set, no id reused across blocks — and prints the next free id given a configurable fleet frontier; wired as a test or CI check; catches the historical duplicated-id cases when run on this file.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Repo-wide compile check; drift-guard the manual registries
- id: `rm-051` | track: reliability | priority: 30.0 | status: in_progress
- acceptance: CI compiles every tracked *.py (compileall on the package or a generated list — no hand-maintained registry); a drift unit test fails when a tracked root module is missing from py-modules (the one registry that must stay curated)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Remove the misleading operator_events `queried` allowlist indirection
- id: `rm-079` | track: reliability | priority: 30.0 | status: in_progress
- acceptance: filter once at the boundary and pass the filtered set (warning preserved on all paths), or drop the `queried` computation entirely; behavior for allowed/denied mixtures locked by tests on both list paths
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Fix the live-events cursor clamp (dead MAX(seq) query)
- id: `rm-080` | track: reliability | priority: 30.0 | status: in_progress
- acceptance: either implement the intended high-watermark clamp with a test for the skip-ahead case, or delete the MAX(seq) query with a test asserting cursor semantics unchanged; poll-path cost drops by one query
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### doctor ui_cron_dispatch cross-process caveat (in-process-only registry read)
- id: `rm-140` | track: reliability | priority: 30.0 | status: in_progress
- acceptance: the check's detail text marks it "in-process only" (or reports the serving-process identity it introspected) and docs/operator-mode.md states the caveat; optional follow-on note names the durable-audit-log alternative if cross-process authority is ever needed.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Small reliability bundle: cron zero-interval floor, placement walk reuse, preview parity
- id: `rm-057` | track: reliability | priority: 25.0 | status: in_progress
- acceptance: schedule parser rejects or floors zero/negative intervals with a dedicated test; targets/manifest walk memoized per (root, sources) with bounded TTL and invalidation on profile changes (perf probe shows repeat-call reuse); no residual preview/score divergence after rm-054's refactor
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Own the environment-dependent skips plus an autouse audit-override reset
- id: `rm-101` | track: reliability | priority: 25.0 | status: candidate
- acceptance: each environment-dependent skip carries an owner note or becomes a hard condition; an autouse fixture resets audit-log override state between tests; full suite green with the fixture in place and no ordering-dependent failures
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### subscriptions/listen alignment study (deferred until a push consumer exists)
- id: `rm-014` | track: reliability | priority: 20.0 | status: in_progress
- acceptance: revisit when a push-style consumer is required: decide between a listen-stream surface or documenting cursor polling as the hermes-native pattern; no action while all consumers poll
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### CI web-lane npm caching + stale self-hosted comments
- id: `rm-039` | track: reliability | priority: 20.0 | status: candidate
- acceptance: actions/setup-node cache enabled for the web job (or a recorded reason not to); stale comments refreshed to match hosted runners
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Reconcile divergent vercel.json configs
- id: `rm-045` | track: reliability | priority: 15.0 | status: in_progress
- acceptance: one authoritative config kept (the other deleted or its role documented in the docs/README.md authority map); deploy shape verified once
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Remove or wire the unused dompurify web dependencies
- id: `rm-044` | track: reliability | priority: 12.0 | status: in_progress
- acceptance: dependencies removed (clean install + green web build) or sanitization genuinely wired with a test proving raw HTML is stripped
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

## Closed items

- `rm-007` Skip-instead-of-fail for distribution-metadata test — done
- `rm-011` Speak the official MCP Tasks extension for long-running work (read-only mapping) — superseded
- `rm-012` MRTR (input_required) as the standardized approval handshake — superseded
- `rm-013` Split server.py registration into per-subsystem modules — superseded
- `rm-016` Remove dead token_store.py block and close the F821 class — done
- `rm-017` Lint gate: drive 61 ruff errors to zero and enforce in CI — done
- `rm-019` Decide plan-node lease semantics (wire or remove) — superseded
- `rm-020` Restore pre-pause state on node resume — superseded
- `rm-021` Warn-and-backup before overwriting corrupt cron jobs.json — done
- `rm-022` Single topological-sort implementation — superseded
- `rm-023` Pin/bound uvicorn (floating 0.x dependency) — done
- `rm-024` Python 3.13/3.14 CI lanes; plan the 3.10 EOL floor bump — superseded
- `rm-025` Finish the v0.10 controller slice: D3 hard-block + shadow-to-live — superseded
- `rm-026` Land upstream v0.11.0 (dual SDK support, Gemini Spark profile, security remediation bundle) — superseded
- `rm-028` Re-baseline the repo-wide lint gate for ruff 0.15 default rules — superseded
- `rm-029` Resolve the 12 unresolved gitlink entries — superseded
- `rm-030` Account-status banner is dead code on auth-configured deployments — superseded
- `rm-031` Repo-wide compile check; drift-guard the manual registries — superseded
- `rm-032` MCP 2026-07-28 minor-spec adoption and SDK-3.0 proofing — superseded
- `rm-033` Bound pyyaml (last bare runtime dependency) — superseded

<!-- cycle-2 additions: run 61db9bce246a4150954d3c8ae3ad4d55 (repository-maintenance cycle 2; assess 727758f1 = adopted reaped fbb8862d re-verified + 1 new finding, research 4658b239; the same-action prior attempt 04e0b2e6 was reaped with ZERO durable work). Reconciliation at integration e40491ed93d5 (conflict case 71620cebcd8a4f429ac93b4e17297d7b), fleet convention "landed-first ids stay": the run minted rm-131..rm-135 against a frontier of rm-130, but the landed target already carries sibling bf4db34f's rm-131..rm-140 with DIFFERENT meanings, and unlanded sibling c5fba76a holds rm-141..rm-150 — so this block was renumbered past every known claim: orig rm-131 (ui_security status-read off-load, implemented) -> rm-151; orig rm-132 (mission-usage 24h window, implemented) -> rm-152; orig rm-133 (deployment provenance) -> FOLDED into the landed rm-135 above (same defect as that item and as sibling c5fba76a's unlanded rm-148); orig rm-134 (token/key staging hardening) -> rm-153; orig rm-135 (fixed-name .tmp staging) -> rm-154. Code/test comments and docs/ui-security-boundary.md carry the landed ids; the run's own .conductor/ bookkeeping keeps its original numbering as a dated record. The narrative sections below are the campaign-source record re-homed after the landed managed render replaced the long-form ROADMAP (rules 1-40 they reference live in the campaign roadmap history, which this render omits). -->

## Cycle 2 research digest — run 61db9bce246a (2026-10-01; research 4658b239, skill ce-ideate)

Rejections re-verified so no cycle re-probes them: MCP spec revision is still 2026-07-28 (releases API; test_mcp_sdk_migration.py:25 already pins it — rm-048 stays wait); mcp SDK 2.2.0 was PyPI latest at probe time and ci.yml:56 already runs the mcp==2.2.0 lane (see the dated update below); croniter 6.2.4 is within >=2,<7; zero open issues on upstream AND zero open PRs/issues on the fork (gh api) — no user-pull surface for external-facing features this cycle; AG-UI shows no fresh pull signal. NOT re-minted because existing fleet ids own them: upstream v0.13 adoption (window 7795aa3ce8..f4151d9728 = 9 commits / 58 files / +11252/-112, contains the rm-081 loader trio; owned by 0aa75ea4 rm-085, 1a6beeba rm-098, b6659410 rm-103, 2f81870e rm-105, 099e2bfc rm-116, b6b8792f rm-130 — see the rm-081 update above; the adoption has since landed in this tree); Python 3.10 EOL 2026-10-31 floor bump (owned by landed rm-100 plus b6659410 rm-109 and 099e2bfc rm-118, partially implemented there — the DECISION, bump vs tomli-conditional retention [pyproject.toml, ci.yml 3.10 lanes], is the only open act and is due before 2026-10-31); ruff 0.16 dev-dep lane (owned by 099e2bfc rm-120; evidence at probe time: pip index latest 0.16.9 vs the pyproject pin >=0.15,<0.16).

- update 2026-10-03 (compound 34b85e5e, from this cycle's full-validation evidence d2875b62): the mcp line above is superseded as currency — the validation venv built for the full gate (fresh uv python 3.11, `uv pip install -e ".[dev]"`, 2026-10-03) resolved mcp 2.3.0 (requires httpx2) + starlette 1.7.0 and the ENTIRE suite ran green under both (1611 collected, zero F/E), so 2.3.x exists after this digest's 2026-10-01 probe; rm-048's spec-revision wait is unaffected (spec still 2026-07-28 at probe time); a 2.3.0 CI-lane / dependency-floor refresh is next-cycle material — no id minted here, probe the fleet for an existing owner first.

## Cycle 2 outcome — run 61db9bce246a (2026-10-03; pre-review compound 34b85e5e; landed at integration e40491ed93d5 as rm-151 + rm-152)

Batch "operator-visible signal correctness" (rm-151 + rm-152; the two change-units of stewardship request 08e7c0ab — separate units because they share no files, imports, or ordering) implemented in worktree run-61db9bce246a-61db9bce at HEAD caf60018d2, branch conductor/run-61db9bce246a. RM-151 (ui_security.py): me_endpoint + connection_endpoint build their payloads via asyncio.to_thread, moving the account_status -> TokenStore.status chain (synchronous sqlite, connect timeout 15.0) off the serving event loop; payload shapes unchanged; /api/connection is the browser connection store's restart poll (web/src/stores/connection.ts), so the fix un-stalls SSE/WS under a slow token DB. RM-152 (operator_mission.py): the `_24h` usage aggregates are now genuinely windowed (JOIN sessions, started_at >= cutoff), unresolvable rows excluded, schema drift degrading explicitly to labelled ALL-TIME with an envelope warning. Tests: test_ui_security.py +117 (stall regression, revert-tripwire-proven), test_operator_mission.py +72/-3 (stale-row exclusion + drift fallback + corrected windowed expectations; the old fixture had baked the all-time bug in as _24h truth). Riders: 2 CHANGELOG Unreleased bullets, docs/ui-security-boundary.md off-loop note.

Validation (all recorded in prior phase artifacts — no tests re-run at compound): implement focused suites green (41 + 38 dots, exit 0); targeted impact set via run_repo_impacted_tests.py --mode fast escalated to `-o addopts= -q -n 8` over its 9-file set -> `207 passed in 21.83s`, 0 skipped/failed (attempt 204198f0); ruff clean on all 4 changed py files under BOTH the ambient 0.15.10 and uv 0.15.22 — review re-verified zero findings in-tree; the implement log's "18 pre-existing findings" list came from a mis-scoped run that missed the repo ruff config (its no-NEW-findings conclusion held via HEAD parity); dispatched full_command VERBATIM through scripts/local_validation_gate.py --shell-command 'python -m pytest -q' -> gate exit 0, outcome completed, returncode 0, 1611 tests collected, zero F/E, 10 skips, ~241.8s, workers=1 (attempt d2875b62; gate result result-1665710-350413078.json); validation digest re-derived at caf60018d2 and matched the recorded outcome; tracked tree state identical pre/post validation.

### Cycle 2 learnings — prevention rules 41-46 (run 61db9bce246a; the earlier rules are numbered in the campaign roadmap history that the managed render above omits — they remain in force there. Two collisions live in the landed history — run-cbd446's rules 28-32 overlap run-c1ef's 28-34, and run-0c8974's block numbers its rules 1-6 against a "rules 1-10" base — resolve at a future integration, not by renumbering here.)

41. **A reaped delegate session can hold COMPLETE durable work — run the durable-trail check before redoing or dismissing an attempt.** This cycle's assess adopted attempt fbb8862d: its event log showed session_reaped pre-delivery, but its FULL typed phase_result (5 findings, status succeeded) sat in the delegate spool and was re-verified in-tree — an entire phase of findings that would otherwise have been silently redone. Two other reaped attempts (roadmap 04e0b2e6, targeted 7f6e6fc0) had zero durable work (no typed artifact, no /tmp scratch, no tree drift) and were correctly redone. The check is minutes: events/<attempt>.jsonl (reap vs turn completion) x delegate/<attempt>.json x /tmp/<attempt>* scratch x git status.
42. **A regression test is not evidence until it has failed.** Prove sensitivity with a revert tripwire: revert the fix in place, watch the new test fail with its named message, restore, re-run green (this cycle: rm-151's stall test failed on the reverted to_thread off-loads with 'serving event loop stalled by a blocked status read (rm-151)'). A test that has only ever passed guards nothing provably.
43. **Window-aggregate tests must seed out-of-window rows.** rm-152's baked-in test asserted all-time sums under _24h names because every fixture row was timestamp-less and in-window by construction — a fixture where all rows qualify cannot distinguish windowed from all-time semantics. Any test naming a time window carries at least one stale row asserted excluded, plus (where relevant) the explicit degradation path.
44. **Third strike of a defect class = fix the class, not the site.** "Synchronous sqlite on the serving event loop" has now been patched per-surface four times (rm-076 ui_chat + live-events WS, the OAuth token lanes, rm-151 ui_security status reads). The next occurrence should be closed by a repo-wide guard — a scan/test failing on any async handler reaching sqlite3.connect/execute directly — rather than a fifth per-endpoint patch; left as a next-cycle roadmap candidate, not minted here.
45. **Version-currency claims are dated evidence, not standing facts.** Research recorded 'mcp 2.2.0 is PyPI latest (no 2.3.x exists)' on 2026-10-01; the cycle's own full-validation env resolved mcp 2.3.0 + starlette 1.7.0 two days later and the suite ran green under them. Date-stamp currency lines in digests, and re-probe at consumption time — the dated update above carries this one so no reader trusts the stale line.
46. **When the delegate env lacks a skill's tooling, record the capability gap instead of routing around the skill.** No subagent tool was available this cycle, so ce-compound's parallel dispatch degraded to sequential in-thread execution with an explicit INDEPENDENCE_ACCOUNTING note (no independence claimed) — the batch's two change-units share no files, so the loss was zero-risk. Fabricated parallelism or silently skipping the skill both corrupt the record.

### Cycle 2 next-cycle context (run 61db9bce246a, post-compound, landed at integration e40491ed93d5)

- rm-151 + rm-152 are implemented, validated, and landed with this integration (orig ids rm-131/rm-132 in the run's own records; the .conductor/ prioritization and stewardship-request files keep the original numbering as a dated record).
- Open candidates from this block, in roadmap-priority order: rm-153 (token/key staging hardening) and rm-154 (retire fixed-name '.tmp' staging) — both were deferred this cycle for hard collisions: sibling 041a92f6's in-flight atomic_write.py batch owns the 14-site fixed-name staging census, e13b1c0d holds the same family, and b6659410's unlanded rm-114 claims the token_store key-perms half — re-derive collisions live before touching. The third candidate (deployment provenance) folded into the landed rm-135.
- The P1 headliner fleet-wide was upstream v0.13 adoption, and it HAS landed in this tree (125255c0bc + the ancestry stitch, then #26-#28) — rm-081/rm-098 now close by fold against it, subject to their parity checks on the merged tree.
- Fleet id frontier warning for the next roadmap phase (recorded in this run's prioritization matrix): this block's orig rm-131..rm-135 raced sibling bf4db34f's rm-131..rm-140 (different meanings, now landed) and c5fba76a self-renumbered to rm-141..rm-150 — landed-first ids stay; every id below must be resolved by run prefix + content at the landing gate, and the next mint must re-probe live worktrees, not just refs. This block renumbers to rm-151+ at its own landing gate (done above).
- New currency datum from validation (mcp 2.3.0 + starlette 1.7.0, full suite green — see the digest update): consider a 2.3.0 CI lane / floor refresh next cycle; probe the fleet for an existing owner first (the ci.yml:56 mcp==2.2.0 lane predates it).
- Full-suite comparable for the next assess on this lineage: 1611 collected / 10 skips / zero F-E in a fresh uv python-3.11 venv at caf60018d2 + batch diff (gate result result-1665710-350413078.json). Counts are environment-bound — the same-env A/B shape is the comparable artifact, not the absolute number; re-derive the baseline on the merged v0.13 tree before comparing.

<!-- managed by hermes-roadmap render; do not edit by hand -->
