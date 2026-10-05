# hermes-gpt — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- upstreams (this repo builds on): .github, agent, hermes-infra
- dependents (changes here affect): (host), agent, maestro
- graph: evidence-derived (imports/refs/deploy surfaces); advisory

## Open items

### Autopilot per-task artifacts workspace is never provisioned (dispatch fails or tests mask it)
- id: `rm-282` | track: reliability | priority: 118.0 | status: candidate
- acceptance: the dispatch path provisions `<data>/missions/artifacts/<task_id>` before runner spawn — mkdir with restrictive mode at dispatch, OR workspace semantics split so local backends get a provisioned cwd while remote/A2A peers receive peer-relative artifact paths (never local-absolute); a REAL-dispatch test (no doubled contract->backend handoff, no _observe mkdir masking, no acceptance LAUNCHER doubling) proves the workspace exists on disk at spawn time AND a locally produced artifact inside it passes _check_artifacts; a fleet test proves dispatch to a remote peer carries no local-absolute workspace path; full test_operator_autopilot*.py + test_operator_contract.py green
- evidence: run 77d02b842247 assess 7fecfd02 — live repro /tmp/7fecfd02-assess/repro_artifacts_workspace.py (workspace absent after real scheduler dispatch; _check_artifacts fail-closed artifact_missing) and /tmp/7fecfd02-assess/probe_spawn.py (Popen FileNotFoundError via the spawn cwd); operator_autopilot.py:966 sole construction site (zero production mkdir), operator_runners.py:768 spawns with cwd=str(workspace); masked by tests that mkdir the workspace themselves (test_operator_autopilot_advance.py:36-56, test_operator_autopilot_deliverables.py:54); upstream verified unfixed on master and every open branch (research 1adaa9fa R1)

### Adopt upstream skill-loader hardening trio (upstream issue #74 full half)
- id: `rm-081` | track: reliability | priority: 115.0 | status: candidate
- acceptance: merged tree reconciles fork+upstream halves into a single resolution authority; loader failure is fail-closed with a test proving a required-but-unloadable skill blocks dispatch; probes use preprocess=False with a test asserting inline_shell side effects never run during validation; fork surfaces (plan create/validate/placement) keep enforcement at parity with upstream's breadth (work contracts/swarm); full suite + upstream's new tests green on both SDK lanes
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Move blocking SQLite off the serving event loop (ui_chat + live-events WS)
- id: `rm-076` | track: reliability | priority: 110.0 | status: in_progress
- acceptance: every blocking SessionDB/live-event-store call reachable from async handlers/WS runs via asyncio.to_thread (or equivalent executor offload); a regression test holds SessionDB._lock in a background thread and asserts a concurrent ui_chat request completes within a bound (no loop starvation); the WS poll path performs no connect-timeout or sqlite work on the loop thread
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Offload /api/me + /api/connection status reads off the serving loop (rm-076 remainder)
- id: `rm-151` | track: reliability | priority: 105.0 | status: in_progress
- acceptance: both payloads' token-store reads execute off the loop (asyncio.to_thread or the in-file equivalent); regression test holds the token-store path blocked and asserts a concurrent lightweight async handler still completes (a sync TestClient cannot observe this — use the async test pattern rm-076's suite established); payload shapes unchanged; a note lands in docs/ui-security-boundary.md transport-health section that the poll endpoint is off-loop
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Add test coverage for 16 untested module(s)
- id: `rm-002` | track: reliability | priority: 100.0 | status: candidate
- signals: reliability.no_tests:hermes_state.py, reliability.no_tests:tools/check_package_hygiene.py, reliability.no_tests:web/src/chat/ActivityCard.tsx, reliability.no_tests:web/src/chat/ChatPage.tsx, reliability.no_tests:web/src/chat/Composer.tsx (+11 more)
- acceptance: Every module in ['hermes_state.py', 'tools/check_package_hygiene.py', 'web/src/chat/ActivityCard.tsx', 'web/src/chat/ChatPage.tsx', 'web/src/chat/Composer.tsx', 'web/src/flight/AccountPanel.tsx', 'web/src/flight/ApprovalsPanel.tsx', 'web/src/flight/ContractsPanel.tsx', 'web/src/flight/DeckOverview.tsx', 'web/src/flight/EventHistoryPanel.tsx', 'web/src/flight/FleetPanel.tsx', 'web/src/flight/schemas.ts', 'web/src/shared/AccountStatusBanner.tsx', 'web/src/shared/ConnectionStatus.tsx', 'web/src/stores/session-list.ts', 'web/vite.config.ts'] has a corresponding test file with at least one passing test
- evidence: full suite green (python -m pytest -q) at HEAD; conductor validation digest validation:v1:<sha> recorded in the shipping PR
- update 2026-10-05 (run 77d02b842247 research 1adaa9fa R11): while adding web-module tests, note the lane is one major behind with no vulnerability driver (react ^18.3.1 vs 19.3.0, vite ^8.2.1 vs 8.3.2, vitest ^4.1.10, typescript ~5.6.2) — the refresh rides this coverage work, no dedicated cycle.

### Windows artifact-identity is inert below Python 3.12 (st_birthtime_ns constant 0)
- id: `rm-283` | track: reliability | priority: 100.0 | status: candidate
- acceptance: _artifact_identity prefers st_birthtime_ns on win32 only when the attribute actually exists, falls back to st_ctime_ns on 3.10/3.11 (where it IS creation time and not yet deprecated), and never silently trusts a 0 default (a missing birth time must fail or mark the cross-API comparison absent, not degenerate the tuple); a platform-independent unit test injects synthetic os.stat_result values covering present/absent st_birthtime_ns and asserts the real-Windows absence path (no fabricated attribute on a namespace object); the same-API st_ctime_ns Windows deprecation (semantics change to metadata-change time) is fixed or annotated with a dated plan; with no Windows CI test lane, the synthetic-stat test is the executable proof
- evidence: run 77d02b842247 assess 7fecfd02 N1 + research 1adaa9fa R2 — operator_contract.py:814-820 verified (getattr(s,"st_birthtime_ns",0) under cross_api+win32, else st_ctime_ns); docs.python.org/3/library/os.html live: st_ctime_ns deprecated on Windows since 3.12, st_birthtime_ns is the creation time there — CPython does not expose st_birthtime on win32 before 3.12, so the getattr is a constant 0 and identity degenerates to (dev,ino,size,mtime); mtime is attacker-restorable via utime, weakening the #88 consistent-observation TOCTOU to size+mtime for unpinned digests (autopilot nodes pin no sha256); test_v014_acceptance.py:281+ fabricates the attribute, validating intent not real-Windows absence; repo floor requires-python>=3.10 (pyproject.toml:10)

### Dependency security floors: starlette / anyio / cryptography (OSV-verified live)
- id: `rm-284` | track: reliability | priority: 95.0 | status: candidate
- acceptance: pyproject floors raised to starlette>=1.4, anyio>=4.14.2, cryptography>=50.0.0 with an install-matrix proof that both mcp SDK lanes still resolve cleanly (resolver output diffed before/after, no silent upgrade of unrelated pins); OSV querybatch evidence attached showing 0 vulns at the new floors for the resolved set; rm-099's starlette/anyio direct-declaration bounds updated consistently in the same change; CHANGELOG security note; full suite green on the raised range
- evidence: run 77d02b842247 research 1adaa9fa R5 — api.osv.dev live 2026-10-04: starlette 0.40.0=14 vulns (1.4.0=0), anyio 4.0.0=4 (4.14.2=0), cryptography 42.0.0=15 (50.0.0=0); declared floors (starlette>=0.40,<2 / anyio>=4,<5 / cryptography>=42) admit all of them

### Swarm/codex JSON store: dead locks, fixed tmp name, no fsync
- id: `rm-285` | track: reliability | priority: 92.0 | status: candidate
- acceptance: sw-*.json mutations serialize on the (currently dead) RLock or an equivalent per-file lock; saves use unique-adjacent temp names with file fsync AND parent-dir fsync via one shared atomic-write helper adopted by the other durable state writers (autopilot/cron/workspace/controller/job-supervisor — extends rm-153/rm-154); a two-thread test interleaves load->mutate->save and asserts no lost update — the final human approval gate cannot be reverted by a racing save; test_operator_swarm.py gains the concurrency case
- evidence: run 77d02b842247 assess 7fecfd02 — operator_swarm.py:165 and operator_codex.py:32 define threading.RLock() with zero acquisitions (grep 'with _lock|_lock.acquire|_lock.release' rc=1, re-verified at HEAD); _load_workflow/:550 + _save_workflow/:560-567 do unlocked load->mutate->save with a fixed shared .json.tmp and no fsync; MCP tools run on a thread pool; research 1adaa9fa R6 (zero prior ROADMAP coverage of store durability)

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

### Finance worker request_id quarantine (prompt-injection)
- id: `rm-286` | track: reliability | priority: 85.0 | status: candidate
- acceptance: request_id (and any caller-controlled field) renders only inside the EVIDENCE_JSON quarantine block or is excluded from the INSTRUCTION section entirely; the finance surface validates an identifier charset matching its error text (bounded opaque identifier); an injection test proves a request_id containing instruction-like content cannot alter the worker's instruction parse
- evidence: run 77d02b842247 assess 7fecfd02 — finance_worker.py:90-92 interpolates the caller-bounded request_id into the INSTRUCTION structural contract outside the EVIDENCE_JSON quarantine

### Adopt next_cursor on empty filtered pages in the WS live-events loop (rm-080 residual)
- id: `rm-095` | track: reliability | priority: 85.0 | status: in_progress
- acceptance: the WS loop advances its cursor to the returned next_cursor on empty pages too (or an equivalent watermark adoption), preserving rm-080's snapshot-ordering guarantee (a concurrent insert is delivered or rescanned, never skipped); a regression test asserts an idle filtered WS client advances past N non-matching events without rescanning them; the docs/live-events.md cursor-semantics paragraph holds verbatim
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### SSE stream resume: surface the discarded id: cursor; wire reconnectStream
- id: `rm-287` | track: reliability | priority: 80.0 | status: candidate
- acceptance: readSseStream returns the last id: cursor (replacing the 'void seq;' discard); reconnectStream gains a real caller on the ChatPage error/reconnect path replaying from that cursor against the server ring; a web test proves mid-stream disconnect resumes without duplicate side effects AND retry-after-error does NOT re-send the user message (reconnect distinguishable from a new turn); server replay path (ui_chat.py) unchanged
- evidence: run 77d02b842247 assess 7fecfd02 — web/src/api/client.ts:137 discards the parsed id: cursor ('void seq;'), web/src/api/chat.ts:47 reconnectStream has zero callers; ChatPage error Retry re-sends lastUserMessage (double tool side-effects) while the server-side replay ring already works

### TLS minimum_version floors on both server contexts
- id: `rm-288` | track: reliability | priority: 78.0 | status: candidate
- acceptance: both TLS server contexts set minimum_version explicitly (>= TLSv1_2, consistent with the rm-284 floors); a test asserts the negotiated protocol floor through a wrapped client; docs note the floor; operator_fabric.py and operator_fabric_g4c.py both covered
- evidence: run 77d02b842247 assess 7fecfd02 — operator_fabric.py:2977 and operator_fabric_g4c.py:2068 build ssl.SSLContext(PROTOCOL_TLS_SERVER) with no minimum_version (verified: load_cert_chain only — TLS 1.0/1.1 possible on py3.10/3.11 defaults)

### Python floor bump 3.10->3.11 plus a 3.13 CI lane (dated deadline)
- id: `rm-100` | track: reliability | priority: 75.0 | status: candidate
- acceptance: CI matrix adds a green 3.13 lane (and 3.14 if deps allow); a dated plan lands the 3.11 floor bump with the next fork release (requires-python >=3.11, matrix drops 3.10, tomli conditional removed); CHANGELOG records both
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 research 1adaa9fa R10): the dated deadline has LAPSED — Python 3.10 EOL passed 2026-10-01 (endoflife.date, PEP 619) while requires-python>=3.10 (pyproject.toml:10), the 3.10 CI axis, and the tomli conditional all remain; a security-sensitive loopback server now runs a dead interpreter line as its floor. Interaction with rm-283: st_birthtime_ns exists on Windows only from 3.12, so a 3.11 floor keeps the compat fallback while a future 3.12 floor removes it; fold the py3.10 bare `except TimeoutError` vs asyncio.TimeoutError residue note (docs/maintenance-cycle-log.md) into the bump.

### cron next-fire + timezone preview at arm time
- id: `rm-132` | track: reliability | priority: 72.0 | status: in_progress
- acceptance: hermes_cron_create dry-run plan (and the browser-UI confirm surface) include next-N (>= 3) computed fire times plus the effective timezone name used to resolve them; works for interval, daily-time, weekday, and once schedules; plan does not imply the external scheduler's tz is authoritative (contract documented in docs/operator-mode.md cron section); tests cover each schedule kind including a TZ-set environment.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### MCP spec-revision lineage refresh + SDK 2.3.x lane
- id: `rm-048` | track: reliability | priority: 70.0 | status: in_progress
- acceptance: docs/mcp-compatibility.md corrected to describe the revision lineage per SDK family instead of claiming one "latest"; the rm-009 revision assertion parameterized per installed SDK pin (still fails loudly on unexpected revisions); a mcp==2.3.x lane added to CI (or pins refreshed per rm-009's cadence rule) with a spec-delta review note for hermes surfaces; MCP-Auth cross-RFC notes (RFC 9728/9700 now Proposed Standard, draft-ietf-oauth-parallel-refresh adopted) reflected in docs/oauth.md where they touch hermes behavior
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 research 1adaa9fa R9): exact pins frozen at mcp==1.28.1/2.0.0/1.30.0/2.2.0 (ci.yml:54-56, verified) under a stale 'research 2026-09-20' comment while mcp 2.3.0 is the latest SDK — land the 2.3.0 pin lane + refresh the comment; spec revision still 2026-07-28 (verified live); a2a-sdk 1.2.1 / @a2a-js/sdk 1.3.0 / ruff 0.16.10 unchanged; repo-wide elicitation usage is zero and any future surface stays Owner-gated behind approval nodes (2026-07-28 spec elicitation security rules harvested from the raw dump /tmp/ee2a269c-research/exa_mcp.json).

### Ship or document a browser-UI build path (web assets absent from wheel/MANIFEST)
- id: `rm-077` | track: reliability | priority: 70.0 | status: candidate
- acceptance: EITHER the wheel/sdist carries a prebuilt web/dist (with a package-hygiene assertion), OR README + docs/operator-mode.md document the exact supported build step (npm ci && npm run build / HERMES_GPT_UI_DIR) verified to produce a served UI; tools/check_package_hygiene.py extended to match whichever path is chosen
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 assess 7fecfd02 N2 + research R4): re-proven on the adopted tree — pyproject.toml:128-130 data-files + MANIFEST.in:29 glob an EMPTY web/dist on a pristine clone, so the built wheel (106 entries) and sdist carry 0 web assets; test_ui_static_assets.py:23-33 synthesizes the installed-wheel dirs in tmp_path so the suite cannot catch it; upstream's PUBLISHED hermes-gpt 0.14.0 wheel matches the shape (109 entries, 0 web, 0 docs — /tmp/1adaa9fa-research/upstream_wheel.whl), making the gap user-visible on the public channel; whichever branch of the EITHER is chosen, the CHANGELOG 0.13.0 browser-assets claim and tools/check_package_hygiene.py assertions must match it (see rm-056).

### fork distribution identity: local version segments or never-publish
- id: `rm-133` | track: reliability | priority: 68.0 | status: candidate
- acceptance: decision recorded FIRST — (a) local version segment (e.g. 0.12.0+codeo1io or +<line-tag>) on fork releases, or (b) explicit never-publish-on-PyPI policy with a private index — in RELEASE_CHECKLIST.md + README; artifact metadata carries line provenance (commit or origin URL) so pip + doctor distinguish codebases; doctor VERSION line gains the line identity (extends operator_diagnostics.py:904); decision + implementation land BEFORE any 0.13-numbered fork release.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 research 1adaa9fa R3, PyPI live): upstream published hermes-gpt 0.13.0 (2026-10-03) and 0.14.0 (2026-10-04) — the fork declares the identical name+version (pyproject.toml:5-6), so `pip install hermes-gpt==0.14.0` resolves upstream's build and the fork can never publish under these coordinates; the 'decision lands BEFORE any 0.13-numbered fork release' requirement is now breached by events, not choice — the never-publish / local-version-segment / rename decision BLOCKS any 0.15-numbered release work.

### Extend skill validation to Work Contract and Swarm dispatch (hermetic #76 semantics)
- id: `rm-054` | track: reliability | priority: 65.0 | status: candidate
- acceptance: contract creation and pre-dispatch revalidation fail closed with distinct not_found/unavailable codes and zero mutation on rejection (tests pin the no-mutation path); candidates preview and score share one validation entry point so their verdicts are identical for identical inputs (assess-F7 scenario replayed divergence-free); docs state where validation runs (AGENTS.md docs rules: exact surfaces, explicit gates)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Surface ui_api mount failure as an operator-visible signal
- id: `rm-078` | track: reliability | priority: 65.0 | status: in_progress
- acceptance: a failed UI mount emits an operator live event AND an audit record (or a doctor WARN) while the server still boots; a test simulates the import failure and asserts the signal fires exactly once; docs/operator-mode.md notes the failure mode
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### fetch-metadata + content-type hardening on browser-UI state changes
- id: `rm-134` | track: reliability | priority: 63.0 | status: candidate
- acceptance: state-changing (POST) routes reject Sec-Fetch-Site: cross-site requests and Origin headers outside the allowed set (UI origin + chatgpt.com + issuer), and require Content-Type: application/json on JSON-body routes; the ChatGPT-side origin keeps working (it is in the CORS list today); non-browser MCP clients unaffected; any escape-hatch env documented; tests cover allow/deny/cross-site/preflight cases.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 assess 7fecfd02): SCOPE EXTENDED — also gate the WS handshake (server.py:3187-3190 live_websocket_authorized returns True when unconfigured; operator_live_events.py:353-368 accepts the handshake with no Origin check, then applies read_only policy), closing the browser CSWSH route to the loopback event stream; validate Host/Origin on the oauth pass-through path (oauth_auth.py:1358-1361 passes requests through untouched when no static bearer is configured and OAuth state is None), closing DNS-rebinding to the loopback listener; /api/ops/action (ui_ops.py:832) joins the POST set; default-deny on mismatch documented as compatible with the loopback-default product invariant.

### Raise build floor to setuptools>=77 (PEP 639 license string)
- id: `rm-027` | track: reliability | priority: 62.0 | status: in_progress
- acceptance: floor raised to >=77 (or license switched to table form) so declared-floor builds work; sdist+wheel build verified in a --no-isolation environment; no behavior change to isolated CI builds
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-046` | track: reliability | priority: 60.0 | status: in_progress
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refreshed or re-labeled as historical; `python -m build` + `twine check dist/*` + tools/check_package_hygiene.py dist/* run with the two docs present
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 assess 7fecfd02 N4 + research R4): fresh counts — sdist ships 33/36 tracked docs; maintenance-cycle-log.md, runtime-checkout.md, and vnext-capability-manifest-and-mission-ledger.md ship nowhere (the first two are dependencies of the rm-135/rm-136 refreshes); upstream's PUBLISHED 0.14.0 wheel ships 0 docs, so the gap is user-visible on the public channel too.

### v0.13.0 release-readiness batch: publish + deployed-remote rollout
- id: `rm-083` | track: reliability | priority: 60.0 | status: candidate
- acceptance: RELEASE_CHECKLIST executed for v0.13.0 (or the next fork version): CHANGELOG sectioned, package built + twine/check_package_hygiene verified, version policy resolved per rm-065, deployed remote rolled forward and verified (operator doctor clean); release notes state distribution channels truthfully (no implied GitHub/PyPI sync)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### live-deployment provenance capture + uncommitted-delta release blocker
- id: `rm-135` | track: reliability | priority: 60.0 | status: candidate
- acceptance: provenance-capture doctor check (or deploy-time record) captures the serving process's self-reported version + working-tree state (commit, dirty flag, branch) into a durable operator-visible record; a release/ops rule BLOCKS promoting a build whose live checkout carries uncommitted deltas (or forces an explicit override with the delta recorded); docs/runtime-checkout.md refreshed or re-labeled per AGENTS.md rules as part of the fix.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Correct hermes_mission_usage _24h keys — they previously reported all-time totals
- id: `rm-152` | track: reliability | priority: 60.0 | status: in_progress
- acceptance: usage rows joined/filtered by sessions.started_at >= cutoff with the schema-drift fallback the intent comment describes (missing started_at -> fail loud or explicitly-degraded output, never silently all-time); a new test with a stale pre-cutoff usage row asserted EXCLUDED from _24h sums; the baked test updated to a two-window fixture; full test_operator_mission.py green
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 assess 7fecfd02, at b1dfb2b8ad): SHARPENED — the v0.14 windowing fix is structurally a NO-OP: hermes_state.py:41-43 stores sessions.started_at/last_activity_at as REAL epochs while operator_mission.py:904/:1406/:1417 compare ISO TEXT cutoffs, and sqlite storage-class ordering places every REAL below every TEXT, so every window predicate is always-false; :1437-1440 additionally swallows sqlite3.Error to rows=[]. sessions_7d/sessions_24h/tokens_24h/cost_24h report structural zeros. Correct fix supersedes the acceptance above: unify BOTH sides to epoch REAL (or both to ISO TEXT) — never re-window; add a metric regression test seeding a recent REAL session row and asserting nonzero windows; correct the CHANGELOG 0.14.0 rm-152 bullet (see rm-056). Scope note: ui_chat.py:284 'last_active' is the agent SessionDB interface key and is NOT part of this defect — do not bundle.

### declare the browser-UI agent-runtime cross-project seam
- id: `rm-136` | track: reliability | priority: 58.0 | status: candidate
- acceptance: the seam is DECLARED — vendored/stubbed interfaces behind an explicit boundary module, OR a documented contract (which external tree provides them, at what version) + an import-contract test that runs on the clean checkout and fails LOUDLY (never silent IMPORT_UNAVAILABLE) when the declared provider is missing; pyproject/docs name the external requirement; if a degradation path is kept, it is visible in doctor.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### SHA-pin the hermes-agent CI checkout; nightly drift lane
- id: `rm-289` | track: reliability | priority: 55.0 | status: candidate
- acceptance: the agent-loader job checks out NousResearch/hermes-agent at an immutable SHA for PR/push lanes, with a separate nightly unpinned drift lane that fails loudly (or opens an issue) on tip movement; the comment states the pin policy and last-verified date; a third-party HEAD rename can no longer break a required lane at will
- evidence: run 77d02b842247 research 1adaa9fa R8 — ci.yml:117-145 agent-loader checks out NousResearch/hermes-agent at the default branch with no ref: (verified at HEAD); tip moved repeatedly on 2026-10-04 alone (1298c8e74b morning -> af90026aa0 13:21Z, verified live via api.github.com)

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
- update 2026-10-05 (run 77d02b842247 research 1adaa9fa R7): bilateral convergence is live — upstream feat/gemini-spark-integration (2a50749a06, 7 commits from post-#67 base 9f537106e5) adds the Gemini Spark profile with env names identical to the fork's, but the fork's oauth_auth.py is AHEAD on that file by ~590 lines (DCR knob + docs section, redirect-allowlist isolation, dynamic-client TTL/purge, RFC 9207 iss); pre-stage an adoption conflict map for the next merge and record the back-contribution offer (fork hardening upstream) as the stewardship follow-on extending PR #85's pattern.

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

### Delegations reconcile: double validation per tick + hardcoded legacy_lineage=False
- id: `rm-290` | track: reliability | priority: 50.0 | status: candidate
- acceptance: reconcile validates each manifest once per tick on the non-cacheable path (reuse the computed verdict or restructure so full validation runs only once); legacy_lineage is derived from the row's actual lineage rather than hardcoded False, and legacy rows skip or are explicitly reported instead of raising ValueError mid-reconcile; a test seeds a legacy-lineage row and asserts reconcile completes with an explicit disposition
- evidence: run 77d02b842247 assess 7fecfd02 N7 — operator_delegations.py:1108 hardcodes legacy_lineage = False (surfaced at :1243/:1323); _validate_manifest_impl runs twice per tick when manifests are non-cacheable

### Commit a [tool.ruff] rule-set config on ruff 0.16 (extends run-fd2bc85f rm-028)
- id: `rm-035` | track: reliability | priority: 50.0 | status: candidate
- acceptance: a committed [tool.ruff] selects the enforced rule set explicitly; dev pin moves to a 0.16.x line; CI lint job green under the pinned ruff; a finding-count table (classic vs adopted set) with per-class disposition lands in the PR
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run 77d02b842247 assess 7fecfd02 N8): the cliff is measured — the repo has NO [tool.ruff] section and the range pin is >=0.15,<0.16 (clean at 0.15.22) while ruff 0.16.9 reports 497 findings (top classes BLE001/UP045/TRY004 plus B033 duplicate set members at operator_policy.py:78 — _FALSEY_VALUES lists "0"/"false" twice); land the explicit rule-set selection BEFORE the next pin bump or the lint gate goes red on upgrade day.

### Regenerate .gitleaksignore against HEAD-reachable history and prune foreign refs
- id: `rm-055` | track: reliability | priority: 50.0 | status: candidate
- acceptance: .gitleaksignore regenerated from HEAD-reachable history only — every surviving entry justified by a reachable commit (PR #23's sentinels retained, foreign entries dropped); foreign refs pruned from the shared store with the 9 live heads verified untouched and other runs' working trees unaffected; a gitleaks scan scoped to HEAD-reachable commits reports zero findings; a triage-scope prevention rule added to the cycle learnings
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### job-supervisor _storage_id resolves the same job_id to different paths across OSes
- id: `rm-291` | track: reliability | priority: 48.0 | status: candidate
- acceptance: record paths are OS-independent OR the divergence cannot be hit silently — normalize the job id to one storage form on all platforms (encode the Windows-reserved classes everywhere), or document + test the migration story for records created on one OS and read on another; a test asserts _record_path is identical for the reserved-id classes under both branch polarities (or that a documented migration maps them)
- evidence: run 77d02b842247 assess 7fecfd02 N6 — operator_job_supervisor.py:58-66 _storage_id encodes ':'/trailing-dot/reserved names as ~<sha> only under IS_WINDOWS; POSIX keeps the raw name, so the same job_id resolves to different record/lock paths across OSes (cross-OS record invisibility)

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
- update 2026-10-05 (run 77d02b842247 assess 7fecfd02 N2/N3): three CHANGELOG claims verified false/no-op at the adopted tree — 0.13.0 'release packages include the built browser assets' (clean checkout ships zero web; rm-077), 0.13.0 'CI exercises the Python/MCP matrix on Windows and Linux' (restored fork CI runs ubuntu tests + windows-docs only, caa07747a1), and the 0.14.0 rm-152 windowing bullet (structurally no-op; rm-152); fold their corrections into this bundle or the owning items.

### Harden token/key file staging beyond chmod-after-write
- id: `rm-153` | track: reliability | priority: 45.0 | status: in_progress
- acceptance: every staged secret file created with restrictive mode AT creation under a unique-adjacent name (in-repo precedent operator_cron.py / operator_workspace.py / operator_job_supervisor.py) or O_EXCL; secrets dirs mkdir with explicit 0o700; fsync of key material before the atomic replace; a umask-0 test asserting final file AND dir modes are 0600/0700; a two-writer test asserting no interleaved or lost staging writes; the token DB reaches 0600 with no observable window (or documents why it cannot)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

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
- id: `rm-154` | track: reliability | priority: 40.0 | status: in_progress
- acceptance: every staging site uses a unique-adjacent temp name (pid+token or mkstemp) created with restrictive mode and atomically replaced; a repo-wide guard test fails on any NEW fixed-name staging path (scan '.tmp' literals constructed without a uniquifier, mirroring the census command `rg -n "\.tmp" --glob '*.py' -g '!test_*'`); the touched files' existing tests stay green; no behavior change beyond the name
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

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

### Tracked-artifact and import-path hygiene bundle
- id: `rm-292` | track: reliability | priority: 28.0 | status: candidate
- acceptance: the 212 tracked .conductor/ spool files are untracked (or reduced to an explicit allowlist with rationale); the divergent vercel.json pair is reconciled per rm-045 and the stray one untracked; test_verify.py is made a real test (no hardcoded machine-specific absolute paths) or deleted; the sys.path.insert(0, ...) sites (server.py:196, operator_skills.py:175/:1029, operator_skill_resolution.py:160, finance_worker.py:61) are replaced with sys.path.append or guarded so repeated calls cannot shadow stdlib/vendor modules; each disposition named in the PR
- evidence: run 77d02b842247 assess 7fecfd02 (LOW findings) — 212 tracked .conductor files; vercel.json + test_verify.py tracked; all five sys.path.insert sites verified at HEAD

### Small reliability bundle: cron zero-interval floor, placement walk reuse, preview parity
- id: `rm-057` | track: reliability | priority: 25.0 | status: in_progress
- acceptance: schedule parser rejects or floors zero/negative intervals with a dedicated test; targets/manifest walk memoized per (root, sources) with bounded TTL and invalidation on profile changes (perf probe shows repeat-call reuse); no residual preview/score divergence after rm-054's refactor
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Own the environment-dependent skips plus an autouse audit-override reset
- id: `rm-101` | track: reliability | priority: 25.0 | status: candidate
- acceptance: each environment-dependent skip carries an owner note or becomes a hard condition; an autouse fixture resets audit-log override state between tests; full suite green with the fixture in place and no ordering-dependent failures
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-04 (campaign 5260fbbbcd3a cycle 3, run efe7657638c7, pre-review/uncommitted): implemented as batch rider — conftest.py gains autouse `_reset_audit_log_override` (snapshot/restore of `operator_policy._audit_log_override` around every test, conftest.py:177) and new test_suite_determinism.py pins both acceptance halves: every environment-dependent `skipif` is registered in an inventory guard (`test_environment_dependent_skipif_inventory_is_registered`, test_suite_determinism.py:42 — new environment-dependent skips fail the guard until registered) plus an audit-override leak pair (`test_audit_override_leaks_on_purpose` :64 / `test_audit_override_did_not_leak_from_previous_test` :70); recorded batch validation green at this delta: targeted command RC=0 (/tmp/5dcc0dec-targeted/run1.log) and full gate GATE_RC=0 (envelope result-2088694-354043546.json, digest `validation:v1:162865e8e0aedadbb4b9c06760278e38af343ef5814c42970939b776d2f21629`, 1812 outcomes, 0 failed/0 errored); status flip deferred to the landing gate per campaign convention

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
- `rm-098` Adopt upstream v0.13 Autopilot (9-commit gap; PR #82) — done via the v0.14.0 adoption wave: tree d163cda227 carries the upstream content ancestry-stitched (CHANGELOG 0.13.0 + 0.14.0 sections present) with fork repairs fadabf9e54/caa07747a1/b1dfb2b8ad; full suite 1874 passed / 5 skipped / 0 failed at b1dfb2b8ad and ruff 0.15.22 clean (run 77d02b842247 assess 7fecfd02)

<!-- managed by hermes-roadmap render; do not edit by hand -->
