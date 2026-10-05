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

### Autopilot per-task artifacts workspace is never provisioned (dispatch fails or tests mask it)
- id: `rm-294` | track: reliability | priority: 112.0 | status: candidate
- acceptance: a provisioning site creates the per-task artifacts workspace (missions/artifacts/<task-id>) before dispatch — today the only mkdir on that path tree is the missions.db parent (mission_runtime:131); a regression test dispatches against a pristine data root and asserts the workspace exists OR the dispatch fails loudly with a provisioning error (never a silent missing-cwd dispatch); operator_autopilot.py:966 allowed_scope and operator_runners.py:768 cwd=str(workspace) both resolve to a directory the server guarantees; test fixtures stop pre-creating the workspace so the suite cannot mask the gap
- evidence: run c6a4fd9256ab assess 43fab8e4 at d163cda227 — operator_runners.py:768 `cwd=str(workspace)`; operator_autopilot.py:966 artifacts allowed_scope; `grep -rn 'artifacts' --include='*.py' . | grep -E 'mkdir|makedirs|parents=True'` exits 1 (zero provisioning sites); artifacts under /tmp/43fab8e4-assess/; fleet equivalents rm-271 (run 27b7fb9ea997) / rm-282 (run 77d02b842247) — reconcile at landing

### Move blocking SQLite off the serving event loop (ui_chat + live-events WS)
- id: `rm-076` | track: reliability | priority: 110.0 | status: in_progress
- acceptance: every blocking SessionDB/live-event-store call reachable from async handlers/WS runs via asyncio.to_thread (or equivalent executor offload); a regression test holds SessionDB._lock in a background thread and asserts a concurrent ui_chat request completes within a bound (no loop starvation); the WS poll path performs no connect-timeout or sqlite work on the loop thread
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Offload /api/me + /api/connection status reads off the serving loop (rm-076 remainder)
- id: `rm-151` | track: reliability | priority: 105.0 | status: in_progress
- acceptance: both payloads' token-store reads execute off the loop (asyncio.to_thread or the in-file equivalent); regression test holds the token-store path blocked and asserts a concurrent lightweight async handler still completes (a sync TestClient cannot observe this — use the async test pattern rm-076's suite established); payload shapes unchanged; a note lands in docs/ui-security-boundary.md transport-health section that the poll endpoint is off-loop
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Dependency security floors: starlette / anyio / cryptography (OSV-verified live)
- id: `rm-295` | track: reliability | priority: 104.0 | status: candidate
- acceptance: pyproject floors raised — starlette >=1.4 (0.40.0 carries 14 OSV advisories; 1.4.0 and 1.7.0 clean), anyio >=4.14.2 (4.0.0 carries 4 incl. PYSEC-2026-4024/4025), cryptography >=50.0.0 (42.0.0 carries 15; 50.0.0/50.0.2 clean) — with the co-resolution proof recorded in the PR: BOTH CI SDK lanes (mcp 1.28.1 pins starlette>=0.27; mcp 2.3.0 pins starlette>=0.27 + anyio>=4.9) resolve the raised floors green; rm-099's declared direct-dep bounds adopt the same targets; a dated OSV re-probe note rides the PR
- evidence: run c6a4fd9256ab research aeb501e6 C2 — api.osv.dev querybatch 2026-10-05 (starlette 0.40.0=14/1.4.0=0/1.7.0=0; cryptography 42.0.0=15/50.0.0=0/50.0.2=0; anyio 4.0.0=4/4.14.2=0) + PyPI requires_dist for mcp 1.28.1/2.3.0 (floor co-resolution); /tmp/aeb501e6-research/osfv.json; fleet equivalents rm-272 / rm-284

### Add test coverage for 16 untested module(s)
- id: `rm-002` | track: reliability | priority: 100.0 | status: candidate
- signals: reliability.no_tests:hermes_state.py, reliability.no_tests:tools/check_package_hygiene.py, reliability.no_tests:web/src/chat/ActivityCard.tsx, reliability.no_tests:web/src/chat/ChatPage.tsx, reliability.no_tests:web/src/chat/Composer.tsx (+11 more)
- acceptance: Every module in ['hermes_state.py', 'tools/check_package_hygiene.py', 'web/src/chat/ActivityCard.tsx', 'web/src/chat/ChatPage.tsx', 'web/src/chat/Composer.tsx', 'web/src/flight/AccountPanel.tsx', 'web/src/flight/ApprovalsPanel.tsx', 'web/src/flight/ContractsPanel.tsx', 'web/src/flight/DeckOverview.tsx', 'web/src/flight/EventHistoryPanel.tsx', 'web/src/flight/FleetPanel.tsx', 'web/src/flight/schemas.ts', 'web/src/shared/AccountStatusBanner.tsx', 'web/src/shared/ConnectionStatus.tsx', 'web/src/stores/session-list.ts', 'web/vite.config.ts'] has a corresponding test file with at least one passing test
- evidence: full suite green (python -m pytest -q) at HEAD; conductor validation digest validation:v1:<sha> recorded in the shipping PR

### TLS minimum_version floors on both server contexts
- id: `rm-296` | track: reliability | priority: 96.0 | status: candidate
- acceptance: both server TLS contexts declare a documented minimum — the explicit TLSv1_2 floor today at operator_fabric.py:2977-2979 and operator_fabric_g4c.py:2068-2070 is raised or explicitly justified with a dated rationale comment; a contract test fails if either context is constructed without an explicit minimum_version; docs state the floor per surface; pairs with the rm-295 dependency floors
- evidence: run c6a4fd9256ab assess 43fab8e4 (sed anchors verified at d163cda227) + research aeb501e6 C2; fleet equivalents rm-277 / rm-288

### Pin the hermes-agent CI checkout and contract-test the consumed SessionDB interface
- id: `rm-297` | track: reliability | priority: 94.0 | status: in_progress
- acceptance: ci.yml:121-127 hermes-agent checkout pins a dated immutable ref (comment carrying the tip it moved from); a contract test asserts the row keys/columns the fork consumes from the agent SessionDB — the undocumented `last_active` alias (`rt.activity AS last_active`, agent hermes_state_sessions.py:1235, consumed at ui_chat.py:284) and the mirrored schema at hermes_state.py:38-46 — against that pin, refreshed deliberately; the local vendored checkout (behind at ca9be0a616) is refreshed or its role documented
- evidence: run c6a4fd9256ab research aeb501e6 C3 — agent main moved twice in two days (af90026aa → 8567d8a243, pushed 2026-10-04T17:23Z) while ci.yml:121-127 checks out UNPINNED; raw.githubusercontent fetch verified the alias intact at tip; fleet equivalents rm-278 / rm-289
- update 2026-10-05 (run c6a4fd9256ab implement 62726aaa): contract-test half LANDED (scoped per prioritize 58d9c703; ci.yml ref-pin deferred to the ci gate) — new test_agent_session_contract.py pins the `last_active` row alias across all three sides: agent provider SQL (`AS last_active` regex scan of the agent checkout when present via HERMES_GPT_AGENT_SOURCE|/home/agent/.hermes/hermes-agent, skip-with-reason when absent; alias verified live at agent fb2ee191b314 — line moved 1235→1190 with two more f-string sites at :1324/:1336, hence the regex pin not a line pin), the local shim (hermes_state.py `list_sessions_rich` now projects `last_activity_at AS last_active` — the shim previously emitted NO last_active key, so ui_chat silently fell back to started_at), and the consumer (ui_chat._serialize_session maps last_active → last_activity_at with started_at fallback); remaining half: ci.yml:121-127 dated immutable pin + deliberate refresh discipline

### Refactor 20 high-complexity function(s)
- id: `rm-001` | track: reliability | priority: 90.0 | status: candidate
- signals: reliability.complexity_hot:operator_autopilot.py::build_summary, reliability.complexity_hot:operator_contract.py::_check_forbidden, reliability.complexity_hot:operator_delegations.py::hermes_delegation_cancel, reliability.complexity_hot:operator_delegations.py::hermes_delegation_dispatch, reliability.complexity_hot:operator_delegations.py::hermes_delegation_reconcile (+15 more)
- acceptance: Each flagged function is decomposed below the branch threshold with behavior locked by characterization tests
- evidence: ast-based branch-count check passes at HEAD (full suite green; conductor validation digest validation:v1:<sha> recorded in the shipping PR)

### Isolate the mission-events long-poll from the shared anyio threadpool
- id: `rm-096` | track: reliability | priority: 90.0 | status: in_progress
- acceptance: long-poll waits no longer occupy shared threadpool tokens — a dedicated anyio.CapacityLimiter (anyio.to_thread.run_sync(limiter=...) verified in .venv) for wait-bearing endpoints, or an asyncio-native wait bridge; a regression test saturates the shared limiter with 40 holders and asserts a mission-events request still completes; existing mission-events behavior (25s max wait, event delivery, cursor semantics) unchanged
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Registry and bound for fire-and-forget cron dispatch, with completion audit
- id: `rm-097` | track: reliability | priority: 88.0 | status: in_progress
- acceptance: cron dispatch goes through a bounded executor with an operator-visible registry (active/finished counts surfaced via doctor or an ops live event); a completion record (success/failure + duration) lands in the audit trail when the run finishes, not at dispatch; a cap-exceeded request is rejected loudly (429-class) like ui_chat; tests cover dispatch, completion-audit ordering, injected-failure audit, and cap rejection
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Client stream resilience: adopt the server replay cursor, wire reconnectStream, stop Retry double-sends
- id: `rm-298` | track: reliability | priority: 86.0 | status: candidate
- acceptance: pure-client — the SSE consumer stores the last `id:` seq (replacing the `void seq;` discard at web/src/api/client.ts:137) and reconnectStream (web/src/api/chat.ts:47, zero call sites today) is called with it on drop so ChatPage's error Retry resumes the stream instead of re-sending lastUserMessage (no duplicated tool side-effects — a test pins one user turn → one assistant turn across a forced disconnect+retry); startStreaming clears per-turn `activities` (web/src/stores/conversation.ts:55); NO server protocol change (server replay already correct at ui_chat.py:604-623)
- evidence: run c6a4fd9256ab assess 43fab8e4 + research aeb501e6 C5 — wc/grep at d163cda227: client.ts:137, chat.ts:47 zero call sites, conversation.ts:55, ChatPage.tsx Retry button; server replay ui_chat.py:604-623 + GET /api/chat/stream :823; fleet equivalents rm-275 / rm-287

### Adopt next_cursor on empty filtered pages in the WS live-events loop (rm-080 residual)
- id: `rm-095` | track: reliability | priority: 85.0 | status: in_progress
- acceptance: the WS loop advances its cursor to the returned next_cursor on empty pages too (or an equivalent watermark adoption), preserving rm-080's snapshot-ordering guarantee (a concurrent insert is delivered or rescanned, never skipped); a regression test asserts an idle filtered WS client advances past N non-matching events without rescanning them; the docs/live-events.md cursor-semantics paragraph holds verbatim
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Validation verdict cache returns stale SATISFIED after fresh validation runs (delegations)
- id: `rm-299` | track: reliability | priority: 82.0 | status: in_progress
- acceptance: EITHER the verdict cache becomes load-bearing-sound — the fresh validation verdict is never masked by a cached one (operator_delegations.py:1131-1135 today overwrites the fresh verdict with the cached verdict after the full validation run trusted at :1207) with a test seeding a stale cache entry and asserting a changed artifact yields the fresh verdict; OR the cache is removed with the zero-work-saved disposition recorded (full validation already ran before the cache was consulted); the key=(relpath, mtime_ns, size) truncation (2000 entries, clear-at-256) and the sound _manifest_cacheable fence (:719-726) are preserved or retired with it
- evidence: run c6a4fd9256ab assess 43fab8e4 (anchors operator_delegations.py:679-753/:1131-1135/:1207 verified at d163cda227) carrying sibling research 389c9f6b RC4; fleet equivalent rm-273
- update 2026-10-05 (run c6a4fd9256ab implement 62726aaa): REMOVAL branch chosen and LANDED — the delegation-side verdict cache (_VALIDATION_VERDICT_CACHE, _validation_verdict_cached, _manifest_cacheable, ~74 lines at old operator_delegations.py:679-753) is deleted with the zero-work-saved disposition: the caller at old :1128-1136 already ran the FULL live validation (`validation = contract_mod._validate_manifest_impl(...)`) and then overwrote its verdict with the cached one, so the cache saved no validation work and could only mask a fresh verdict; consumer now uses the live result directly (validation['verdict']); review-state and audit-tail masking fence retired WITH it (their only consumer was the cache, zero remaining callers fleet-wide); regression test test_operator_delegations.py::test_reconcile_validation_verdict_is_never_served_stale seeds SATISFIED then degrades the live validator and asserts the next reconcile reports the fresh NEEDS_WORK verdict

### Python floor bump 3.10->3.11 plus a 3.13 CI lane (dated deadline)
- id: `rm-100` | track: reliability | priority: 75.0 | status: candidate
- acceptance: CI matrix adds a green 3.13 lane (and 3.14 if deps allow); a dated plan lands the 3.11 floor bump with the next fork release (requires-python >=3.11, matrix drops 3.10, tomli conditional removed); CHANGELOG records both
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run c6a4fd9256ab research aeb501e6 C7): the dated deadline has LAPSED — Python 3.10 EOL passed 2026-10-01 (endoflife.date live; 3.11 EOL 2027-10-31) while requires-python>=3.10 (pyproject.toml:10), the 3.10 CI axis, and the `tomli; python_version < '3.11'` conditional all remain — a security-sensitive loopback server's floor interpreter line is dead; land the >=3.11 bump at the 0.15.0 boundary with a CHANGELOG deprecation note

### cron next-fire + timezone preview at arm time
- id: `rm-132` | track: reliability | priority: 72.0 | status: in_progress
- acceptance: hermes_cron_create dry-run plan (and the browser-UI confirm surface) include next-N (>= 3) computed fire times plus the effective timezone name used to resolve them; works for interval, daily-time, weekday, and once schedules; plan does not imply the external scheduler's tz is authoritative (contract documented in docs/operator-mode.md cron section); tests cover each schedule kind including a TZ-set environment.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### MCP spec-revision lineage refresh + SDK 2.3.x lane
- id: `rm-048` | track: reliability | priority: 70.0 | status: in_progress
- acceptance: docs/mcp-compatibility.md corrected to describe the revision lineage per SDK family instead of claiming one "latest"; the rm-009 revision assertion parameterized per installed SDK pin (still fails loudly on unexpected revisions); a mcp==2.3.x lane added to CI (or pins refreshed per rm-009's cadence rule) with a spec-delta review note for hermes surfaces; MCP-Auth cross-RFC notes (RFC 9728/9700 now Proposed Standard, draft-ietf-oauth-parallel-refresh adopted) reflected in docs/oauth.md where they touch hermes behavior
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run c6a4fd9256ab research aeb501e6 C4): exact pins still frozen at mcp 1.30.0/2.2.0 under the stale 'research 2026-09-20' comment (ci.yml:47-51 verified) while mcp 2.3.0 shipped 2026-10-02 — refresh to 1.30.0/2.3.0 + datestamp; the range lane silently resolves 2.3.0 so the exact lane no longer tests the current release deliberately; review note before any 2.x floor raise: mcp 2.3.0 chains httpx2>=2.10.0 (a fork package of httpx — new dependency-of-dependency surface); mcp 2.x `subscriptions=False` surface-reduction available for the server construction

### Ship or document a browser-UI build path (web assets absent from wheel/MANIFEST)
- id: `rm-077` | track: reliability | priority: 70.0 | status: candidate
- acceptance: EITHER the wheel/sdist carries a prebuilt web/dist (with a package-hygiene assertion), OR README + docs/operator-mode.md document the exact supported build step (npm ci && npm run build / HERMES_GPT_UI_DIR) verified to produce a served UI; tools/check_package_hygiene.py extended to match whichever path is chosen
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run c6a4fd9256ab assess 43fab8e4 + research aeb501e6 C6): re-proven at d163cda227 — clean-checkout distributions ship ZERO browser assets (web/dist gitignored at .gitignore:20 so MANIFEST.in:29 + pyproject data-files glob nothing) while CHANGELOG.md:16 claims 'release packages include the built browser assets' (false) and 'CI exercises the Python/MCP matrix on Windows and Linux' (also false — all 6 test lanes ubuntu-latest; the single windows-latest job at ci.yml:198 only parses two PowerShell examples); whichever branch of the EITHER is chosen, build web/dist in the release job and make the CHANGELOG + tools/check_package_hygiene.py assertions match it (see rm-056)

### fork distribution identity: local version segments or never-publish
- id: `rm-133` | track: reliability | priority: 68.0 | status: candidate
- acceptance: decision recorded FIRST — (a) local version segment (e.g. 0.12.0+codeo1io or +<line-tag>) on fork releases, or (b) explicit never-publish-on-PyPI policy with a private index — in RELEASE_CHECKLIST.md + README; artifact metadata carries line provenance (commit or origin URL) so pip + doctor distinguish codebases; doctor VERSION line gains the line identity (extends operator_diagnostics.py:904); decision + implementation land BEFORE any 0.13-numbered fork release.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run c6a4fd9256ab assess 43fab8e4 + research aeb501e6 C1, ESCALATED): pip-mode `hermes-gpt update --apply` resolves the PUBLIC PyPI name (updater.py:160-176 `_pip_latest_version`/`_pip_update` on PACKAGE_NAME) and upstream now owns `hermes-gpt` at 0.14.0 (uploaded 2026-10-04T01:16:02Z, PyPI live) while the fork declares the same name+version (pyproject.toml:5-6) — the fork's own updater substitutes upstream code into a fork install; the 'decision lands BEFORE any 0.13-numbered fork release' requirement is breached by events, not choice; the (a)/(b)/(c) decision now BLOCKS any 0.15-numbered release work; minimum hardening (c) = pip-mode preflight refusing to install when the resolved distribution's project_url/home_page is not the fork's (extends rm-042's verify-checkout rule into pip mode)

### Swarm/codex JSON store: dead locks, fixed tmp name, no fsync
- id: `rm-300` | track: reliability | priority: 67.0 | status: candidate
- acceptance: the declared RLocks are actually held (operator_swarm.py:165 `_lock = threading.RLock()` with `with _lock` count 0 in operator_swarm.py AND operator_codex.py — persistence writes race today) or removed with a rationale; JSON writes use a unique-adjacent temp name (extends rm-154 off this exact site) atomically replaced with a directory fsync so a crash cannot lose or tear the store; a two-writer test asserts no interleaved or lost writes
- evidence: run c6a4fd9256ab assess 43fab8e4 — `grep -c 'with _lock' operator_swarm.py operator_codex.py` → 0/0 at d163cda227; RLock at operator_swarm.py:165; fleet equivalents rm-274 / rm-285

### Extend skill validation to Work Contract and Swarm dispatch (hermetic #76 semantics)
- id: `rm-054` | track: reliability | priority: 65.0 | status: candidate
- acceptance: contract creation and pre-dispatch revalidation fail closed with distinct not_found/unavailable codes and zero mutation on rejection (tests pin the no-mutation path); candidates preview and score share one validation entry point so their verdicts are identical for identical inputs (assess-F7 scenario replayed divergence-free); docs state where validation runs (AGENTS.md docs rules: exact surfaces, explicit gates)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Surface ui_api mount failure as an operator-visible signal
- id: `rm-078` | track: reliability | priority: 65.0 | status: in_progress
- acceptance: a failed UI mount emits an operator live event AND an audit record (or a doctor WARN) while the server still boots; a test simulates the import failure and asserts the signal fires exactly once; docs/operator-mode.md notes the failure mode
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### fetch-metadata + content-type hardening on browser-UI state changes
- id: `rm-134` | track: reliability | priority: 63.0 | status: in_progress
- acceptance: state-changing (POST) routes reject Sec-Fetch-Site: cross-site requests and Origin headers outside the allowed set (UI origin + chatgpt.com + issuer), and require Content-Type: application/json on JSON-body routes; the ChatGPT-side origin keeps working (it is in the CORS list today); non-browser MCP clients unaffected; any escape-hatch env documented; tests cover allow/deny/cross-site/preflight cases.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run c6a4fd9256ab implement 62726aaa): core gate LANDED as a Host/Origin default-deny boundary in oauth_auth.py — new pure helpers (host_is_loopback/_host_label/boundary_allowed_hosts/host_is_allowed/origin_is_allowed/boundary_denial, BOUNDARY_STATE_CHANGING_METHODS) run FIRST in BearerAuthMiddleware.__call__ before auth and before the unconfigured pass-through: non-loopback/non-allow-listed Host → 421 host_not_allowed (HTTP/2 :authority honored; DNS-rebind defense holds even with NO bearer/OAuth configured); state-changing methods with a non-loopback, non-allow-listed Origin (incl. the `null` origin) → 403 origin_not_allowed; no Origin header (non-browser MCP clients) unaffected. allowlist = loopback ∪ bind host/port ∪ HERMES_GPT_ALLOWED_HOSTS (pre-existing env, now shared with the MCP transport list read from FastMCP `_hermes_http_options` at server.py build_asgi_app, env fallback for older SDKs) ∪ OAuth issuer. WebSocket handshakes gated identically at the TOP of server.live_websocket_authorized (before its unconfigured early-return, which previously left the default-config CSWSH hole — caught during implement). Defense-in-depth route-level re-assertion via new ui_security.origin_trusted on ui_chat POST /api/chat, /api/chat/stop and ui_ops POST /api/ops/action. Tests: 12 boundary tests in test_oauth_auth.py + CSWSH trio in test_server.py + origin-gate pairs in test_ui_chat/test_ui_ops; two direct-construction tests moved to loopback base_url (testserver Host is correctly denied now). Docs: docs/oauth.md Host/Origin boundary section + docs/cloudflare-tunnel.md shared-allowlist rider + CHANGELOG Unreleased entry. NOT yet delivered from the original acceptance: Sec-Fetch-Site: cross-site rejection and the mandatory Content-Type: application/json on JSON-body routes — folded as a small follow-up under this id
- update 2026-10-05 (run c6a4fd9256ab assess 43fab8e4 + research aeb501e6, SCOPE EXTENDED): beyond fetch-metadata/content-type — gate the loopback Origin/Host surface: the WS handshake accepts unconfigured peers (server.py:3187-3192 `live_websocket_authorized` returns True when oauth_state is None and no static bearer — CSWSH route to the event stream), the oauth middleware passes requests through untouched when unconfigured (oauth_auth.py:1359-1361 — DNS-rebinding route to the loopback listener), and browser-UI POSTs at ui_chat.py:718/:793 + ui_ops.py:832 sit behind no Origin check; default-deny on mismatch is compatible with the loopback-default product invariant (anchors verified at d163cda227)

### Raise build floor to setuptools>=77 (PEP 639 license string)
- id: `rm-027` | track: reliability | priority: 62.0 | status: in_progress
- acceptance: floor raised to >=77 (or license switched to table form) so declared-floor builds work; sdist+wheel build verified in a --no-isolation environment; no behavior change to isolated CI builds
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-046` | track: reliability | priority: 60.0 | status: in_progress
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refreshed or re-labeled as historical; `python -m build` + `twine check dist/*` + tools/check_package_hygiene.py dist/* run with the two docs present
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-05 (run c6a4fd9256ab assess 43fab8e4 + research aeb501e6 C6): three referenced-but-unshipped docs confirmed at d163cda227 — maintenance-cycle-log.md, runtime-checkout.md, vnext-capability-manifest-and-mission-ledger.md (README.md:395, README.md:83, docs/README.md:30) — the first two are dependencies of the rm-135/rm-136 refreshes; ship them via data-files or de-reference per this item's EITHER

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
- update 2026-10-05 (run c6a4fd9256ab assess 43fab8e4): re-proven live on the adopted v0.14 tree — /tmp/43fab8e4-assess/probe_fresh.py shows the ISO-text cutoff matches ZERO rows while an epoch cutoff matches one (hermes_state.py:41-42 stores started_at REAL; operator_mission.py:904/:1410-1417 compare ISO TEXT — sqlite storage-class ordering places every REAL below every TEXT, so every window predicate is always-false and the _24h/_7d windows report structural zeros); corrected fix direction: unify BOTH sides to epoch REAL (or both to ISO TEXT) with a metric regression test seeding a recent REAL row and asserting nonzero windows. CORRECTION propagated: ui_chat.py:284's `last_active` key is the agent SessionDB interface alias (`rt.activity AS last_active`) and is NOT part of this defect — do not bundle a ui_chat change (its contract test is rm-297)

### token_store Windows lock loop has no timeout (msvcrt path can hang)
- id: `rm-301` | track: reliability | priority: 59.0 | status: candidate
- acceptance: the Windows msvcrt lock loop (token_store.py:307-313 `while True:` with no bound) gains a timeout/deadline with a loud failure path (stuck or poisoned lock → explicit error, never an indefinite hang); a unit test simulates a held lock and asserts the timeout fires; POSIX and Windows paths keep identical happy-case semantics
- evidence: run c6a4fd9256ab assess 43fab8e4 — token_store.py:307-313 verified at d163cda227; no equivalent minted on any sibling board (fleet-new this pass)

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
- update 2026-10-05 (run c6a4fd9256ab research aeb501e6 C2): the "resolved floor" this item's bounds must track is now proven co-resolvable — mcp 1.28.1 pins starlette>=0.27 and mcp 2.3.0 pins starlette>=0.27 + anyio>=4.9, so the rm-295 floors (starlette>=1.4, anyio>=4.14.2) install green in BOTH CI SDK lanes; declare the direct deps with those bounds (cross-ref rm-295)

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

### Finance worker request_id quarantine (prompt-injection carrier)
- id: `rm-302` | track: reliability | priority: 47.0 | status: candidate
- acceptance: the request_id echoed into the finance decision prompt (finance_worker.py:88-96 — a caller-controlled value interpolated into the instruction block) is quarantined: validated against a strict format and/or carried out-of-band so prompt content cannot ride it; a red-team test injects tool-invoking text via request_id and asserts the output stays a valid finance.decision/v1 JSON with no tool use; docs state the trust boundary
- evidence: run c6a4fd9256ab assess 43fab8e4 — finance_worker.py:88-96 verified at d163cda227; fleet equivalents rm-276 / rm-286

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
- update 2026-10-05 (run c6a4fd9256ab assess 43fab8e4): two CHANGELOG 0.13.0 claims verified false at the adopted tree and foldable here — 'release packages include the built browser assets' (clean checkout ships zero web; rm-077) and 'CI exercises the Python/MCP matrix on Windows and Linux' (ci.yml:198 windows job parses 2 PowerShell examples only); plus the 0.14.0 rm-152 windowing bullet needs the structural no-op correction (see rm-152's update this cycle)

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
- update 2026-10-05 (run c6a4fd9256ab research aeb501e6 C1): the git-mode verify-checkout rule above now has a pip-mode sibling hole — updater.py:160-176 resolves the public PyPI name, so upstream's 0.14.0 substitutes into fork installs; fold the pip preflight (refuse when the resolved distribution's project_url/home_page is not the fork's) into this item or rm-133's option (c)

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

### Tracked-artifact and dead-scratch hygiene bundle
- id: `rm-303` | track: reliability | priority: 34.0 | status: in_progress
- acceptance: test_verify.py (ZERO test functions — a committed manual curl script with hardcoded C:/Users/asimo paths, collected by pytest) is deleted or gated behind an explicit manual marker; the byte-duplicated assets/ + site/assets/ trees (2x 7.1MB = 14.2MB tracked, differing in exactly ONE file — v0.8.0 vs v0.7.0 readme-hero) collapse to one source of truth; the 212 tracked .conductor/ run-bookkeeping files are untracked (fleet precedent a462f5e5bb) with .gitignore coverage; root scratch (x-post-v0.4.0.md) removed or relocated; repo-size delta cited in the PR
- evidence: run c6a4fd9256ab assess 43fab8e4 + research aeb501e6 C9 — grep/du/diff at d163cda227: `grep -c 'def test_' test_verify.py` → 0 (5 'asimo' literals); du -sh assets site/assets → 7.1M/7.1M with a one-file listing diff; `git ls-files .conductor/` → 212; fleet equivalents rm-280 / rm-292
- update 2026-10-05 (run c6a4fd9256ab implement 62726aaa): scoped half LANDED (per prioritize 58d9c703 U4) — test_verify.py (zero test functions, pytest-collected manual curl script with C:/Users/asimo paths) and x-post-v0.4.0.md (root-scratch marketing draft for v0.4.0, current 0.14.0) git-rm'd; no packaging/docs references existed (MANIFEST.in, pyproject, docs/README, README all clean). Remaining under this id: assets/ vs site/assets/ 14.2MB dedup (one-file diff) and the 212 tracked .conductor/ files (canonical a462f5e5bb already untracks forward; history retention is the fork-level question)

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
- update 2026-10-04 (campaign 5260fbbbcd3a cycle 3, run efe7657638c7, pre-review/uncommitted): implemented as batch rider — conftest.py gains autouse `_reset_audit_log_override` (snapshot/restore of `operator_policy._audit_log_override` around every test, conftest.py:177) and new test_suite_determinism.py pins both acceptance halves: every environment-dependent `skipif` is registered in an inventory guard (`test_environment_dependent_skipif_inventory_is_registered`, test_suite_determinism.py:42 — new environment-dependent skips fail the guard until registered) plus an audit-override leak pair (`test_audit_override_leaks_on_purpose` :64 / `test_audit_override_did_not_leak_from_previous_test` :70); recorded batch validation green at this delta: targeted command RC=0 (/tmp/5dcc0dec-targeted/run1.log) and full gate GATE_RC=0 (envelope result-2088694-354043546.json, digest `validation:v1:162865e8e0aedadbb4b9c06760278e38af343ef5814c42970939b776d2f21629`, 1812 outcomes, 0 failed/0 errored); status flip deferred to the landing gate per campaign convention

### Declare the targeted A2A spec revision + conformance baseline test
- id: `rm-304` | track: reliability | priority: 22.0 | status: candidate
- acceptance: the fabric (operator_fabric.py, operator_fabric_g4c.py) DECLARES its targeted A2A spec revision (v1.0.1, 2026-05-28 — no spec-version reference exists in docs today) in docs + a module constant; a baseline conformance test pins the declared surfaces against that revision (agent-card fields, task lifecycle states, auth schemes) so the next fabric feature has a diffable baseline; rides rm-279's smoke lane when that lands (fleet)
- evidence: run c6a4fd9256ab research aeb501e6 C10 — a2aproject/A2A releases live (v1.0.1 2026-05-28, v1.0.0 2026-03-12); python a2a-sdk 1.2.1 / npm @a2a-js/sdk 1.3.0; in-repo grep finds no spec-version reference; fleet kin rm-279 (conformance smoke lane)

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

### MCP elicitation consent surface (EXPLORATORY watch, Owner-gated)
- id: `rm-305` | track: reliability | priority: 10.0 | status: candidate
- acceptance: WATCH ONLY — mcp 2.x ships elicitation TYPES (ElicitRequest/Form/Url/Tasks in mcp.types) with ZERO server-side elic* API on MCPServer; no repo action until the SDK exposes a server API AND an explicit Owner decision is recorded; any future surface routes through the fabric and MUST NOT bypass the Owner-only approval invariant; docs/mcp-compatibility.md records the SDK capability boundary when touched
- evidence: run c6a4fd9256ab research aeb501e6 C8 (mcp types probe re-confirmed type-level only; MCP spec latest tag 2026-07-28); repo-wide elicitation usage zero; fleet equivalent rm-281

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
- `rm-098` Adopt upstream v0.13 Autopilot (9-commit gap; PR #82) — done via the v0.14.0 adoption wave: HEAD d163cda227 (PR #29 squash cf04a2f956, tree-identical ancestry stitch vs upstream/master) carries the upstream content; full suite 1879 collected, exit 0, 0 failures at this HEAD (run c6a4fd9256ab assess 43fab8e4, /tmp/43fab8e4-assess/full2.log)
- `rm-131` ui-ops cron-dispatch semaphore leak on resolve failure — done at HEAD: fix at ui_ops.py:750-779 (try/except across the acquire→dispatch span with `_dispatch_semaphore.release()` in the handler) + regression test test_ui_ops.py:683-712 (injects raising `_resolve_root`, asserts clean 500 + released capacity); content-verified and status refreshed 2026-10-05 (run c6a4fd9256ab prioritize 58d9c703; sibling verification 77d02b842247 aab77b84 agrees)

<!-- managed by hermes-roadmap render; do not edit by hand -->
