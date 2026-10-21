# hermes-gpt — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- dependents (changes here affect): agent
- graph: evidence-derived (imports/refs/deploy surfaces); advisory

## Open items

### Fleet task->agent registry: correct home resolution, scoping, and contract fallback
- id: `rm-156` | track: reliability | priority: 115.0 | status: candidate
- acceptance: `_task_agent_registry_path` resolves the default home WITHOUT `op.default_home` (it does not exist on operator_policy — AttributeError today) using the operator_runners.py:68 idiom; registry is root-scoped with the dispatch path threading hermes_root to the write site (operator_fleet.py:987) and FleetBackend.cancel honoring its own hermes_root; the read-modify-write map is bounded (prune/TTL); the contract's own agent field is the fallback on registry miss so cancel never returns RUNNER_CANCEL_UNOBSERVABLE for a pre-registry or lost-registry row; the `except Exception: pass` in both helpers replaced by loud logging; audit records name the resolved agent id; tests include a HERMES_HOME-unset reproduction and a cancel test that does NOT monkeypatch `_peer_for_task` (the gap that let the AttributeError ship); an evaluation note decides whether A2A v1.0.0 `tasks/{id}` + `tasks/list` becomes the authoritative peer-side observation instead of the local side table
- evidence: assess a8d76146 attempt 5ba8694e F1/F4/F5/F12 (hasattr(op,'default_home')==False + AttributeError repro); re-verified live at e49aef26e8 2026-10-21 — assess 4156539d9688 attempt f755ead9 F1 (dynamic repro with HERMES_HOME unset; registry write succeeds with HERMES_HOME set; call site operator_fleet.py:990 passes no hermes_root; swallow sites :1051/:1067; registry still root-unscoped/unbounded) and CHANGELOG Unreleased (dc65b41892) acknowledging "the known rm-156 fleet-registry defect"; research 4156539d9688 R3 (a2a-python v1.2.3 as conformance reference)

### Adopt upstream skill-loader hardening trio (upstream issue #74 full half)
- id: `rm-081` | track: reliability | priority: 115.0 | status: candidate
- acceptance: merged tree reconciles fork+upstream halves into a single resolution authority; loader failure is fail-closed with a test proving a required-but-unloadable skill blocks dispatch; probes use preprocess=False with a test asserting inline_shell side effects never run during validation; fork surfaces (plan create/validate/placement) keep enforcement at parity with upstream's breadth (work contracts/swarm); full suite + upstream's new tests green on both SDK lanes
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Adopt upstream v0.13 Autopilot (9-commit gap; PR #82)
- id: `rm-098` | track: reliability | priority: 115.0 | status: candidate
- acceptance: the 9 upstream commits merge or cherry-pick onto the fork line with conflicts reviewed line-by-line against fork invariants (Owner Mode break-glass, secret-path denials, default read-only; Autopilot stays default-off at adoption); full suite green in CI shape; CHANGELOG records the catch-up; #83/#84 recorded as follow-on once merged upstream
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Move blocking SQLite off the serving event loop (ui_chat + live-events WS)
- id: `rm-076` | track: reliability | priority: 110.0 | status: in_progress
- acceptance: every blocking SessionDB/live-event-store call reachable from async handlers/WS runs via asyncio.to_thread (or equivalent executor offload); a regression test holds SessionDB._lock in a background thread and asserts a concurrent ui_chat request completes within a bound (no loop starvation); the WS poll path performs no connect-timeout or sqlite work on the loop thread
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Offload /api/me + /api/connection status reads off the serving loop (rm-076 remainder)
- id: `rm-151` | track: reliability | priority: 105.0 | status: in_progress
- acceptance: both payloads' token-store reads execute off the loop (asyncio.to_thread or the in-file equivalent); regression test holds the token-store path blocked and asserts a concurrent lightweight async handler still completes (a sync TestClient cannot observe this — use the async test pattern rm-076's suite established); payload shapes unchanged; a note lands in docs/ui-security-boundary.md transport-health section that the poll endpoint is off-loop
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Autopilot wakeup suite must be deterministic on clean master
- id: `rm-157` | track: reliability | priority: 105.0 | status: candidate
- acceptance: root cause named and fixed for BOTH observed flakes (event-flood woke=0 under -n 4; cursor high-water-mark sequential failure; green/FAIL/green across 3 sequential runs) — either the worker legitimately goes tick-bound under flood (then the test's wake-count band is corrected and the debounce contract documented) or the live-events long-poll misses slice-window events (then `_wait_for_wakeup`'s wait/slice budget is fixed); the file passes 10 consecutive runs sequentially AND under -n 4 in the hermetic env with no skips added
- evidence: assess a8d76146 attempt 5ba8694e F2 + pytest-full.log (1911P/5S/1F, woke=0); 2026-10-21 at e49aef26e8: 23P sequentially AND under -n 4 (single green data point, not a clearance — assess 4156539d9688 attempt f755ead9)

### Chat turn exclusivity: refresh the turn lease and key the turn registry by turn_id
- id: `rm-165` | track: reliability | priority: 100.0 | status: candidate
- acceptance: the turn lease is refreshed on activity inside `_run_turn`/`_execute_turn` (the dead `SessionDB.refresh_session_turn_lease` API, hermes_state.py:309-320, becomes load-bearing) OR `_handle_chat_post` gains a per-session `_active_turn(session_id)` check alongside the acquire, so a >300 s turn can never lose exclusivity to a second POST /chat; a regression test drives one turn past the 300 s TTL with a tool loop and asserts a concurrent POST is refused; the turn registry is keyed by turn_id (not session_id only) so `_register_turn` (ui_chat.py:161) never replaces a running turn's Turn object — its SSE replay ring and stop semantics stay reachable; the TURN_RETENTION_S=1800 promise (ui_chat.py:70) holds for the previous turn's buffer until the window elapses (reconnect with the old turn_id still replays inside 30 min)
- evidence: assess ae5d6905880a attempt d0610511 N1+N2 (ui_chat.py:748 acquire-only ttl=300; refresh API 0 callers repo-wide; dynamic repro: A acquires -> TTL expiry -> B acquires while A still running -> A release None; registry keyed by session_id only); re-verified at e49aef26e8 2026-10-21 — refresh_session_turn_lease still 0 callers, ui_chat.py:158-162 `_register_turn` still replaces the running Turn (assess 4156539d9688 attempt f755ead9 F4)

### Add test coverage for 16 untested module(s)
- id: `rm-002` | track: reliability | priority: 100.0 | status: candidate
- signals: reliability.no_tests:hermes_state.py, reliability.no_tests:tools/check_package_hygiene.py, reliability.no_tests:web/src/chat/ActivityCard.tsx, reliability.no_tests:web/src/chat/ChatPage.tsx, reliability.no_tests:web/src/chat/Composer.tsx (+11 more)
- acceptance: Every module in ['hermes_state.py', 'tools/check_package_hygiene.py', 'web/src/chat/ActivityCard.tsx', 'web/src/chat/ChatPage.tsx', 'web/src/chat/Composer.tsx', 'web/src/flight/AccountPanel.tsx', 'web/src/flight/ApprovalsPanel.tsx', 'web/src/flight/ContractsPanel.tsx', 'web/src/flight/DeckOverview.tsx', 'web/src/flight/EventHistoryPanel.tsx', 'web/src/flight/FleetPanel.tsx', 'web/src/flight/schemas.ts', 'web/src/shared/AccountStatusBanner.tsx', 'web/src/shared/ConnectionStatus.tsx', 'web/src/stores/session-list.ts', 'web/vite.config.ts'] has a corresponding test file with at least one passing test
- evidence: full suite green (python -m pytest -q) at HEAD; conductor validation digest validation:v1:<sha> recorded in the shipping PR

### Ship the campaign subsystem: py-modules parity, lane entry point, and a shipped-surface guard
- id: `rm-172` | track: reliability | priority: 98.0 | status: candidate
- acceptance: pyproject.toml's [tool.setuptools] py-modules (lines 66-127) gains operator_campaign_compiler, operator_campaign_controller, operator_campaign_lane, and operator_work_class — the wheel built at HEAD (hermes_gpt-0.14.0, sha256 b360de8057fc7aba5a62401cc2567075324220c553e48778a9965ca810c4105d, 107 members) provably ships NONE of the four while shipping operator_autopilot/operator_runners, so ~1,700 lines of merged reviewed feature (#43/#44/#47/#48) are checkout-only; [project.scripts] (pyproject.toml:60-62) gains the operator_campaign_lane.main() entry so the lane CLI and its systemd-timer cadence design are reachable from an install; a shipped-surface guard (new test or a tools/check_package_hygiene.py check — it has no parity check today) fails when a tracked top-level non-test module is missing from py-modules, and the same guard generalizes to README-referenced docs (rm-046) and built web assets (rm-077) so checkout content != install content can never land silently again; python -m build + twine check + tools/check_package_hygiene.py green with the four modules present in the wheel
- evidence: assess 4156539d9688 attempt f755ead9 F2 + wheel-build.log + wheel-members-campaign-probe.txt (four modules shipped: False; grep .github/ -> no CI lane references operator_campaign_lane); research 4156539d9688 R9 (unified shipped-surface guard)

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

### Adopt next_cursor on empty filtered pages in the WS live-events loop (rm-080 residual)
- id: `rm-095` | track: reliability | priority: 85.0 | status: in_progress
- acceptance: the WS loop advances its cursor to the returned next_cursor on empty pages too (or an equivalent watermark adoption), preserving rm-080's snapshot-ordering guarantee (a concurrent insert is delivered or rescanned, never skipped); a regression test asserts an idle filtered WS client advances past N non-matching events without rescanning them; the docs/live-events.md cursor-semantics paragraph holds verbatim
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Fleet peers config fallback must honor HERMES_HOME (single home-resolution idiom)
- id: `rm-166` | track: reliability | priority: 85.0 | status: candidate
- acceptance: `_load_hermes_config`'s fallback (operator_fleet.py:201) resolves the config via `os.environ.get("HERMES_HOME", Path.home()/".hermes")` — the operator_runners.py:68 idiom — instead of the hardcoded `Path.home()/".hermes"`, and the docstring claim "reads the same default config the CLI would" becomes true under HERMES_HOME (hermes_cli.config resolves via get_hermes_home today); a test pins both resolution paths (HERMES_HOME set/unset) so a configured peer stays visible to standalone Autopilot workers in home-overridden deployments; the fix names the same resolution authority rm-156 mandates for the registry path — one idiom, both sites
- evidence: code at HEAD 146e4cff56: operator_fleet.py:177-209 (fallback hardcodes home; introduced by #37 5d926938a6 for the UNKNOWN_AGENT loop); hermes_cli.config resolves via get_hermes_home() honoring HERMES_HOME — divergence verified 2026-10-19; fallback re-verified still hardcoded at e49aef26e8 (2026-10-21)

### A2A v1.0.x conformance sweep (fleet peers)
- id: `rm-159` | track: reliability | priority: 78.0 | status: candidate
- acceptance: the hand-rolled fleet client (operator_fleet.py:271) negotiates per spec for 1.0.x peers — prefers application/a2a+json (v1.0.1) with the application/json fallback documented; a recorded decision covers peer auth against v1.0.0's modernized OAuth (PKCE/device-code; implicit/password removed) for remote a2a_agents, adopted or explicitly deferred with rationale; card consumption pinned by a fixture test against a v1.0.x card (capabilities moves, 'canceled' spelling — tolerated at operator_runners.py:719); hand-rolled client vs official a2a-sdk decision recorded in docs with the loopback-first invariant intact
- acceptance: a2a-python v1.2.3 (2026-10-19) is adopted as the reference conformance suite for fleet peer messages (agent card, task lifecycle, cancellation semantics — the exact surface where rm-156's registry defect lives); HERMES_GPT_FLEET_PEER_VERSION's default is DERIVED from the package version instead of the hardcoded '0.20.5' at server.py:3075/:3117 (package is 0.14.0; env override undocumented) with the env documented — retires the two per-release literal-update sites
- evidence: research a8d76146 attempt 0c63bc25 C2 (a2aproject/A2A v1.0.0 + v1.0.1 changelogs; pypi a2a-sdk 1.2.2, fetched 2026-10-18); research 4156539d9688 R3 (A2A spec v1.0.1 2026-05-28 is the latest spec tag; a2a-python v1.2.3 2026-10-19, weekly cadence); assess 4156539d9688 F5 (both '0.20.5' literals verified at HEAD e49aef26e8)

### Python floor bump 3.10->3.11 plus a 3.13 CI lane (dated deadline)
- id: `rm-100` | track: reliability | priority: 75.0 | status: candidate
- acceptance: CI matrix adds a green 3.13 lane (and 3.14 if deps allow); a dated plan lands the 3.11 floor bump with the next fork release (requires-python >=3.11, matrix drops 3.10, tomli conditional removed); CHANGELOG records both
- acceptance: the decision cites the 2026-10-18 ecosystem evidence — starlette 1.8.0 and hypothesis 6.170.1 require >=3.11, so 3.10 installs resolve to older components (the resolver split is documented whichever way the decision goes); the fleet itself runs 3.13.15 while ci.yml's matrix stops at 3.12
- acceptance: the dated deadline has ARRIVED — Python 3.10 reached end-of-life 2026-10-01 (endoflife.date, verified 2026-10-19) while requires-python stays ">=3.10" and ci.yml still carries a 3.10 lane (matrix ["3.10","3.11","3.12"]; a lone 3.14 lane exists at :131, no 3.13 lane); the bump decision cites the passed EOL date and lands the floor with the next fork release or records why it rides one release past EOL
- acceptance: the decision cites 2026-10-21 evidence — CPython 3.15.0 is FINAL (3.16.0a1 already begun) so the matrix pre-adds a 3.15 allow-list lane; publish.yml already publishes on 3.11 (:28) while requires-python stays >=3.10, i.e. the publish lane assumes a floor the package metadata does not declare
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- evidence: research ae5d6905880a attempt ccfc0f98 research.md RC-2 (endoflife.date/api/python.json: 3.10 eol 2026-10-01, 3.11 eol 2027-10-31)
- evidence: research 4156539d9688 attempt 4bd9b2f3 R8 (gh api python/cpython tags verified 2026-10-21: v3.15.0 final, v3.16.0a1 present; publish.yml:28 3.11 publish lane read)

### MCP SDK 1 loop-freeze regression: sync tool bodies lost the add_tool offload
- id: `rm-320` | track: reliability | priority: 72.0 | status: candidate
- acceptance: on MCP Python SDK 1 runtimes (inside the declared mcp[cli]>=1.28.1,<3 range; 1.30.0 is the last 1.x) synchronous tool bodies receive no offload since the mcp_compat.py `add_tool` shim removal — EITHER an SDK-1-scoped offload is restored (or the SDK-1 lane explicitly accepts the blocking semantics with the server documented as SDK-2-recommended), OR SDK 1 support is formally deprecated (range narrowed, docs/mcp-compatibility.md + CHANGELOG updated); an SDK 1 lane test pins whichever contract is chosen; this item's id honors CHANGELOG.md's committed "rm-320 loop-freeze regression" citation, which has been dangling since the uncommitted rm-3xx-era ledger
- evidence: CHANGELOG.md Unreleased (committed) mcp_compat shim-removal entry names rm-320 explicitly; research 4156539d9688 R1 (v1.30.0 2026-09-07 still in declared range, no removal announced)

### cron next-fire + timezone preview at arm time
- id: `rm-132` | track: reliability | priority: 72.0 | status: in_progress
- acceptance: hermes_cron_create dry-run plan (and the browser-UI confirm surface) include next-N (>= 3) computed fire times plus the effective timezone name used to resolve them; works for interval, daily-time, weekday, and once schedules; plan does not imply the external scheduler's tz is authoritative (contract documented in docs/operator-mode.md cron section); tests cover each schedule kind including a TZ-set environment.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### MCP spec-revision lineage refresh + SDK 2.3.x lane
- id: `rm-048` | track: reliability | priority: 70.0 | status: in_progress
- acceptance: docs/mcp-compatibility.md corrected to describe the revision lineage per SDK family instead of claiming one "latest"; the rm-009 revision assertion parameterized per installed SDK pin (still fails loudly on unexpected revisions); a mcp==2.3.x lane added to CI (or pins refreshed per rm-009's cadence rule) with a spec-delta review note for hermes surfaces; MCP-Auth cross-RFC notes (RFC 9728/9700 now Proposed Standard, draft-ietf-oauth-parallel-refresh adopted) reflected in docs/oauth.md where they touch hermes behavior
- acceptance: the lineage map names BOTH new stable revisions — 2025-11-25 (SEP-991 CIMD, OIDC AS discovery, 403-for-invalid-Origin) and 2026-07-28 (stateless overhaul: initialize/Mcp-Session-Id removal, server/discover MUST, subscriptions/listen, required resultType/MRTR, SSE resumability removal, tasks->io.modelcontextprotocol/tasks extension, SEP-414 trace-context _meta, ttlMs/cacheScope) — with the per-family SDK support stated; SDK 2.3.0 shipped 2026-10-02 so the lane is currently missing, not hypothetical; docs/oauth.md notes the 2026-07-28 client-side RFC 9207 iss validation MUST
- acceptance: the 2.3.x lane is still missing as of 2026-10-19 (ci.yml SDK matrix pins mcp==1.28.1/2.0.0/1.30.0/2.2.0) and the lane's certification pins the three SDK 2.2/2.3 behavior changes touching hermes surfaces: same-origin-only client redirects (#3397), 30-min idle stateful Streamable HTTP session expiry (#3395 — assert a client re-initializes on 404 against the server.py streamable_http_app), and x-mcp-header annotation validation at registration (#3620 — the repo registers none, so assert the full tool registration stays green under 2.3.0)
- acceptance: SDK 2.3.0 (2026-10-02) floor/behavior specifics join the certification — httpx2>=2.10 floor reconciled with our declared ranges; empty _meta/params no longer sent and ctx.meta None-safety on our tool surfaces; a recorded subscriptions=False decision (we serve no push consumers — cross-ref rm-014); max_sse_event_size + get_tool_input_schema evaluated for the streamable-http surface; the fleet venv still runs mcp 2.2.0 so the lane is the only place 2.3.x is exercised
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- evidence: research ae5d6905880a attempt ccfc0f98 research.md RC-3 (modelcontextprotocol/python-sdk releases v2.2.0/v2.3.0 notes; PyPI mcp 2.3.0 2026-10-02)
- evidence: research 4156539d9688 attempt 4bd9b2f3 R1 (v2.3.0 release body captured verbatim in candidates.md R1; v1.30.0 confirmed last 1.x, still in range)

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

### fetch-metadata + content-type hardening on browser-UI state changes
- id: `rm-134` | track: reliability | priority: 63.0 | status: candidate
- acceptance: state-changing (POST) routes reject Sec-Fetch-Site: cross-site requests and Origin headers outside the allowed set (UI origin + chatgpt.com + issuer), and require Content-Type: application/json on JSON-body routes; the ChatGPT-side origin keeps working (it is in the CORS list today); non-browser MCP clients unaffected; any escape-hatch env documented; tests cover allow/deny/cross-site/preflight cases.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### CHANGELOG/docs for the campaign subsystem; resolve the dangling PLAN.md design refs
- id: `rm-173` | track: reliability | priority: 62.0 | status: candidate
- acceptance: CHANGELOG Unreleased gains entries for the campaign subsystem landings (compiler/controller/lane #43/#44/#47, work-class owner-approval policy table #48, confined pi_rpc staged agent dir #46 / operator_runners.py:390-449, plan-node execution selector honored #92, attachment-state heartbeat dedupe #41 — none have any CHANGELOG/docs trace today); docs/ gains a campaign operational doc (surfaces, gates, lane/timer cadence) linked from the docs/README.md authority map, and MissionSpec.approval_policy is documented; the dangling "PLAN.md AUTO-02/AUTO-03/SCHED-02" references (operator_campaign_controller.py:1/:7, operator_campaign_lane.py:1/:3/:35 — no PLAN.md exists repo-wide) are landed, repointed, or removed
- evidence: assess 4156539d9688 attempt f755ead9 F3 (grep docs/*.md README.md -> zero campaign references; find -> 0 PLAN.md)

### CHANGELOG Unreleased + operational-surface docs for the recovery wave
- id: `rm-164` | track: reliability | priority: 62.0 | status: candidate
- acceptance: the CHANGELOG slice is DONE (Unreleased landed dc65b41892, scoped to fleet/SDK claims with upgrade semantics); remaining: docs/ covers fleet-task-agents.json (location, scoping after rm-156, role in cancel observation) and the cancel-observation semantics; stale literals refreshed or derived — server.py:3075/:3117 '0.20.5' rides rm-159's package-version derivation, operator_fabric.py:2815 card 'version': '0.8' derived or updated (both literals verified at HEAD 2026-10-21); campaign-wave CHANGELOG entries ride rm-173; AGENTS.md release-discipline review list satisfied
- evidence: assess a8d76146 attempt 5ba8694e F10; CHANGELOG dc65b41892 landed slice; assess 4156539d9688 attempt f755ead9 F5 (literals re-verified at e49aef26e8)

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-046` | track: reliability | priority: 60.0 | status: in_progress
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refreshed or re-labeled as historical; `python -m build` + `twine check dist/*` + tools/check_package_hygiene.py dist/* run with the two docs present
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### v0.13.0 release-readiness batch: publish + deployed-remote rollout
- id: `rm-083` | track: reliability | priority: 60.0 | status: candidate
- acceptance: RELEASE_CHECKLIST executed for v0.13.0 (or the next fork version): CHANGELOG sectioned, package built + twine/check_package_hygiene verified, version policy resolved per rm-065, deployed remote rolled forward and verified (operator doctor clean); release notes state distribution channels truthfully (no implied GitHub/PyPI sync)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### live-deployment provenance capture + uncommitted-delta release blocker
- id: `rm-135` | track: reliability | priority: 60.0 | status: candidate
- acceptance: provenance-capture doctor check (or deploy-time record) captures the serving process's self-reported version + working-tree state (commit, dirty flag, branch) into a durable operator-visible record; a release/ops rule BLOCKS promoting a build whose live checkout carries uncommitted deltas (or forces an explicit override with the delta recorded); docs/runtime-checkout.md refreshed or re-labeled per AGENTS.md rules as part of the fix.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Dev-dependency major bounds (pytest 9, twine 7 are current majors)
- id: `rm-160` | track: reliability | priority: 60.0 | status: candidate
- acceptance: dev groups bound pytest (<10) and twine (<8) in both [project.optional-dependencies] and [dependency-groups] so a fresh `pip install -e ".[dev]"` cannot resolve to untested majors (PyPI 2026-10-18: pytest 9.1.1, twine 7.0.0 while ruff is hard-pinned <0.16); adoption notes per major mirror rm-035's ruff approach; CI green on the bounded range; the ruff note records that 0.17.1 is current so the rm-035 config lands on a current major
- evidence: research a8d76146 attempt 0c63bc25 C7 (pypi JSON fetches 2026-10-18) + pyproject.toml dev groups

### declare the browser-UI agent-runtime cross-project seam
- id: `rm-136` | track: reliability | priority: 58.0 | status: candidate
- acceptance: the seam is DECLARED — vendored/stubbed interfaces behind an explicit boundary module, OR a documented contract (which external tree provides them, at what version) + an import-contract test that runs on the clean checkout and fails LOUDLY (never silent IMPORT_UNAVAILABLE) when the declared provider is missing; pyproject/docs name the external requirement; if a degradation path is kept, it is visible in doctor.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Hermetic local validation gate as the default merge check
- id: `rm-161` | track: reliability | priority: 58.0 | status: candidate
- acceptance: tools/run_local_gate.sh (or a make target) encodes the hermetic invocation — TMPDIR outside any git repo (the delegate default TMPDIR inside .hermes poisons test_codex_config project-mode tests: poisoned run 1890P/5F, hermetic rerun 1895P/0F), result-count derivation independent of the xdist summary quirk, build + tools/check_package_hygiene.py + twine check — one command on any checkout; GitHub Actions is RE-ENABLED (actions/permissions {enabled:true, allowed:all} verified 2026-10-21; full_tests lane green gh run 39387080814, 2026-10-20) so the gate is the fast pre-push mirror of CI rather than the sole merge check; a cheap pre-merge emptiness check (`git diff HEAD^ --stat`) guards the duplicate-merge debris class (#34 was a zero-delta child of #33)
- evidence: assess a8d76146 attempt 5ba8694e F8; fleet hermetic-TMPDIR constraint (run ea4e4e4c1f8f, 2026-10-12); gh api repos/codeo1io/hermes-gpt/actions/permissions -> {"allowed":"all","enabled":true} verified 2026-10-21

### pi runner 1.2/1.3 contract lane for the staged agent dir: schema-validate and sanitize
- id: `rm-178` | track: reliability | priority: 58.0 | status: candidate
- acceptance: the staged settings.json/models.json copied by `_stage_ephemeral_pi_agent_dir` (operator_runners.py:390-449) are validated against the published pi.dev/schemas (pi 1.2.0+) so silent staging drift becomes a test failure; staged settings are SANITIZED — sessionShareDestination and share-related keys stripped so a confined runner can never inherit gist/radius upload destinations from the operator's agent dir; a fleet-profile note records the kimi-coding models.json /v1 override break (pi 1.3.0); the staged-dir TTL (6h) vs max pi_rpc dispatch timeout (<=3600s clamp, no reap-on-complete) relationship re-asserted by test
- evidence: research 4156539d9688 attempt 4bd9b2f3 R6 (pi 1.3.0 local == npm latest, published 2026-10-15; CHANGELOG 1.2.0/1.3.0 sections read: schemas, sessionShareDestination auto/gist/radius, kimi /v1); operator_runners.py:394/:844/:1322 verified assess 4156539d9688

### Skill-loader public-name contract: pin _is_skill_disabled and plugin-sourced skill semantics
- id: `rm-171` | track: reliability | priority: 55.0 | status: candidate
- acceptance: a public-names-only stub contract test pins find_all_skills/sort_skills AND `_is_skill_disabled` against upstream HEAD fixtures — operator_skill_resolution.py:253 still calls the private `_is_skill_disabled` (upstream skills_tool.py:198) while the loader entrypoint got the dual-name `_find_all_skills_fn` shim (e1fa056ac5), i.e. exactly the rename class that broke every PR on 2026-10-18; our skill resolution is verified to treat upstream plugin-sourced skills (tools/skills_tool_plugin.py, consumed inside find_all_skills :294-300) as first-class, including disable/enable precedence
- evidence: assess 4156539d9688 attempt f755ead9 F6; research 4156539d9688 R4 (upstream skills_tool.py names verified 2026-10-21: find_all_skills :277 public, sort_skills :285 public, _is_skill_disabled :198 private)

### Branch protection on codeo1io master (extends rm-008 with red-master evidence)
- id: `rm-038` | track: reliability | priority: 55.0 | status: candidate
- acceptance: master branch protection requires the CI test+lint jobs with linear history; direct pushes restricted to admins; a red push/PR is observed to be rejected once
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

### Delegation recovery-path truthfulness bundle
- id: `rm-162` | track: reliability | priority: 52.0 | status: candidate
- acceptance: the dead stale_invocation clause is removed or made load-bearing with a characterization test (operator_delegations.py ~:1300); invocation_recovered's from_state reflects the true prior state (reserved+invoking shape-1, not hardcoded 'reconciling', :1419); the idempotent zombie-reconcile early-return audits its durable `_write_run` as changed (or documents the write) at operator_autopilot.py ~:495-510; the cross-module event literals ('delegation.dispatched' :1033, 'delegation.dispatch_ambiguous' :1079) are pinned by a drift test matching `_invocation_possibly_submitted`'s set, and the guard gains its first direct unit test
- evidence: assess a8d76146 attempt 5ba8694e F7/F12/F9; partial landing noted — CHANGELOG Unreleased (dc65b41892) records crash-window recovery covering 'reconciling + invoking' pinned in test_operator_delegations.py; remaining bullets re-verified before close (stale_invocation still present at :1198/:1207/:1299 at e49aef26e8)

### Pin the agent-loader CI lane to an upstream SHA with a scheduled bump
- id: `rm-179` | track: reliability | priority: 52.0 | status: candidate
- acceptance: the agent-loader CI lane installs a PINNED upstream commit instead of upstream HEAD, with a weekly scheduled bump job whose red is deliberate and bisectable (bump PR cites the upstream delta); the 2026-10-18 _find_all_skills->find_all_skills rename broke EVERY PR precisely because the lane installs HEAD by design (fixed on master by the e1fa056ac5 dual-name shim; the name guard rides rm-171); upstream is daily-cadence (2026-10-20 alone: plugin-catalog re-pins, terminal plugin hooks e166392fec, completion-child lock fixes 04cf0eb9a8/3ca0639e89)
- evidence: research 4156539d9688 attempt 4bd9b2f3 R5 (gh api NousResearch/hermes-agent commits?since=2026-09-21, verified 2026-10-21)

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
- acceptance: the adoption-timing decision cites MCP 2025-11-25 SEP-991 (Client ID Metadata Documents now a RECOMMENDED registration mechanism); the client redemption path audits/implements RFC 9207 iss validation per the 2026-07-28 client-side MUST (server metadata already advertises it at oauth_auth.py:1399-1406 per SEP-2468)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Validation-verdict cache signature completeness + epoch edge guards
- id: `rm-163` | track: reliability | priority: 50.0 | status: candidate
- acceptance: `_validation_scope_signature` is no longer blind past the 2000-entry walk cutoff (full-enumeration content hash, or an explicit truncation-invalidates policy that cannot reuse a stale verdict) and .git churn is excluded from the signature; ordered_time rejects (or safely floors) ms-precision epochs and calendar-digit integers (operator_delegations.py:622-633) with tests for both producer shapes; a stale-verdict regression test pins the past-cutoff workspace-change case
- evidence: assess a8d76146 attempt 5ba8694e F6/F13

### Commit a [tool.ruff] rule-set config on ruff 0.16 (extends run-fd2bc85f rm-028)
- id: `rm-035` | track: reliability | priority: 50.0 | status: candidate
- acceptance: a committed [tool.ruff] selects the enforced rule set explicitly; dev pin moves to a 0.16.x line; CI lint job green under the pinned ruff; a finding-count table (classic vs adopted set) with per-class disposition lands in the PR
- acceptance: ruff 0.17.1 is current (PyPI 2026-10-19) while this item targets the 0.16.x line — the config commit lands on 0.17.x instead (or records why it pins 0.16), keeping the lint gate on a current major as rm-160 requires
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- evidence: research ae5d6905880a attempt ccfc0f98 research.md RC-5

### Regenerate .gitleaksignore against HEAD-reachable history and prune foreign refs
- id: `rm-055` | track: reliability | priority: 50.0 | status: candidate
- acceptance: .gitleaksignore regenerated from HEAD-reachable history only — every surviving entry justified by a reachable commit (PR #23's sentinels retained, foreign entries dropped); foreign refs pruned from the shared store with the 9 live heads verified untouched and other runs' working trees unaffected; a gitleaks scan scoped to HEAD-reachable commits reports zero findings; a triage-scope prevention rule added to the cycle learnings
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Mutual exclusion for campaign controller state and phase driving
- id: `rm-174` | track: reliability | priority: 48.0 | status: candidate
- acceptance: read-modify-write of campaigns/<id>/state.json and segment driving are guarded by a file lock (flock) or a declared single-writer rule so a systemd-timer tick racing a manual `run --once --apply` cannot double-drive a segment (today: spurious failed hermes_plan_create action when both ticks adopt the same mission, double event bursts, last-writer-wins on state.json — _save_state is an atomic replace with no lock, operator_campaign_controller.py:224-229); the mission_create/autopilot_start read-then-adopt idempotency is covered by a race test proving exactly one adoption under two concurrent ticks
- evidence: assess 4156539d9688 attempt f755ead9 F8

### Conformance-check skill resolution against the PUBLISHED MCP Skills extension (extends run-684b9786 rm-028 / PR #20)
- id: `rm-036` | track: reliability | priority: 48.0 | status: candidate
- acceptance: conformance note mapping hermes skill surfaces onto the published extension (naming, discovery roots, precedence); PR #20's tests verified against it; upstream #74 outcome recorded when it lands (contract agreed architecture-first per run-684b9786 rm-028)
- acceptance: the published-extension target is docs/extensions/skills in the MCP monorepo (2026-10-18 snapshot) and the conformance map cites its current text; rm-082's serving surface re-baselines against the same snapshot
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
- id: `rm-153` | track: reliability | priority: 45.0 | status: in_progress
- acceptance: every staged secret file created with restrictive mode AT creation under a unique-adjacent name (in-repo precedent operator_cron.py / operator_workspace.py / operator_job_supervisor.py) or O_EXCL; secrets dirs mkdir with explicit 0o700; fsync of key material before the atomic replace; a umask-0 test asserting final file AND dir modes are 0600/0700; a two-writer test asserting no interleaved or lost staging writes; the token DB reaches 0600 with no observable window (or documents why it cannot)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Refresh stale top-level documentation
- id: `rm-155` | track: reliability | priority: 43.0 | status: candidate
- signals: reliability.stale_doc:README.md
- acceptance: Docs regenerated/updated; staleness detector reports 0 signals
- evidence: inference.stale_docs returns [] for the repo

### Confine register_campaign manifest paths to operator-configured roots
- id: `rm-175` | track: reliability | priority: 42.0 | status: candidate
- acceptance: manifest_path (operator_campaign_lane.py:213 — `Path(...).expanduser().resolve()` then read_text under require_level("workspace")) is confined to an operator-configured roots allowlist — absolute/expanduser escapes rejected — OR the file-existence/JSON-structure oracle is documented and the gate raised (CampaignLaneError currently echoes raw read/validation failure detail for arbitrary absolute paths); tests cover in-root allow, out-of-root deny, and the error shape
- evidence: assess 4156539d9688 attempt f755ead9 F9

### Updater must verify it found a hermes-gpt checkout before fast-forwarding
- id: `rm-042` | track: reliability | priority: 42.0 | status: in_progress
- acceptance: candidate roots are verified as hermes-gpt checkouts (pyproject name / package marker / remote URL) with a loud refusal otherwise; regression test using a foreign git-root fixture
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Track the MCP Tasks & Events WG: map mission/delegation/live-event surfaces to the emerging vocabulary
- id: `rm-180` | track: reliability | priority: 40.0 | status: candidate
- acceptance: a design note maps hermes missions/delegations/live-events onto the emerging MCP Tasks/Events vocabulary with an incremental-adoption path (no rewrite) — the Tasks & Events WG formed 2026-10-16 with the Agents WG converted to an Interest Group, and a progressive-disclosure charter landed 2026-10-13, i.e. the spec is formalizing exactly our domain; a lightweight watch check flags WG deliverables touching our surfaces; rm-011's superseded tasks mapping is revisited only if the WG ships normative text
- evidence: research 4156539d9688 attempt 4bd9b2f3 R2 (modelcontextprotocol commits 9d896a8e 2026-10-16, 80041ab0 2026-10-20, 5ea99602 2026-10-13)

### Single peer_main: dedupe the dead entry point and test the packaged peer CLI
- id: `rm-037` | track: reliability | priority: 40.0 | status: candidate
- acceptance: one canonical peer_main (dead one removed or repointed with a rationale comment); the packaged entry (g4c peer_main / its serve stack, port 4780) covered by at least one test exercising require-secure-transport and the CLI surface
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Retire fixed-name '.tmp' staging across operator write paths
- id: `rm-154` | track: reliability | priority: 40.0 | status: in_progress
- acceptance: every staging site uses a unique-adjacent temp name (pid+token or mkstemp) created with restrictive mode and atomically replaced; a repo-wide guard test fails on any NEW fixed-name staging path (scan '.tmp' literals constructed without a uniquifier, mirroring the census command `rg -n "\.tmp" --glob '*.py' -g '!test_*'`); the touched files' existing tests stay green; no behavior change beyond the name
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Campaign-lane serve-mode wakeup: replace the O(campaigns x segments) 1s poll fanout
- id: `rm-176` | track: reliability | priority: 38.0 | status: candidate
- acceptance: `_wait_for_lane_wakeup` (operator_campaign_lane.py:438) collapses the per-mission `hermes_live_events_since` fanout — today every WAIT_SLICE_SECONDS=1.0 slice queries live events for every registered campaign's mission ids, bounding at MAX_CAMPAIGNS(32) x MAX_SEGMENTS(24) ~ 768 sqlite queries/sec sustained while idle — into a single per-store high-watermark probe (or one query per campaign per slice); an idle-serve probe test asserts the per-slice query count; wakeup-latency behavior (<=1 slice) unchanged
- evidence: assess 4156539d9688 attempt f755ead9 F7

### Profile-aware skill-resolution gate before placement/dispatch
- id: `rm-041` | track: reliability | priority: 38.0 | status: in_progress
- acceptance: placement/dispatch validates that the target profile can actually resolve each referenced skill at execution time (or fails loudly pre-flight); contract agreed architecture-first with upstream before implementation
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Codex runner capability floor + flags-stability test
- id: `rm-181` | track: reliability | priority: 36.0 | status: candidate
- acceptance: operator_codex.py's version probe (the {"path","source","version","reason","skipped"} dict, :176) gains a minimum-version gate and a flags-stability test for the sandbox/exec argv we pass, so an ambient codex upgrade (weekly stable cadence; rust-v0.163.0 current, 2026-10-15; no floor enforced today) degrades to a clear RUNNER_UNAVAILABLE-style message instead of an argv mismatch; the floor is documented in docs/codex.md
- evidence: research 4156539d9688 attempt 4bd9b2f3 R7 (openai/codex releases verified 2026-10-21)

### Distinguish declared-owner from compile-failure approval downgrades in the audit record
- id: `rm-177` | track: reliability | priority: 35.0 | status: candidate
- acceptance: `_mint_mission`'s except-Exception fallback (operator_campaign_controller.py:562 — approval_policy = {"policy":"owner"} on ANY compile failure) records WHY owner was chosen (declared vs compile-failed) in the campaign audit record; a compiler-regression injection test proves the silent de-automation is operator-visible, so a compiler regression cannot quietly de-automate every preauthorized campaign
- evidence: assess 4156539d9688 attempt f755ead9 F10

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
- acceptance: the implementation note cites the now-normative 2026-07-28 minor-changes text (traceparent/tracestate/baggage `_meta` conventions) as the conformance target instead of the SEP issue thread
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

### User-need channel: enable GitHub issues or document the intentional alternative
- id: `rm-182` | track: reliability | priority: 20.0 | status: candidate
- acceptance: EITHER GitHub issues are enabled on codeo1io/hermes-gpt (disabled, verified 2026-10-21: the issues user-need channel is maintainer-authored only) so inbound user-need signal has a channel, OR README/CONTRIBUTING documents the intentional alternative channel; until then roadmap user-need evidence stays self-referential
- evidence: research 4156539d9688 attempt 4bd9b2f3 R10

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
- `rm-027` Raise build floor to setuptools>=77 (PEP 639 license string) — done
- `rm-028` Re-baseline the repo-wide lint gate for ruff 0.15 default rules — superseded
- `rm-029` Resolve the 12 unresolved gitlink entries — superseded
- `rm-030` Account-status banner is dead code on auth-configured deployments — superseded
- `rm-031` Repo-wide compile check; drift-guard the manual registries — superseded
- `rm-032` MCP 2026-07-28 minor-spec adoption and SDK-3.0 proofing — superseded
- `rm-033` Bound pyyaml (last bare runtime dependency) — superseded
- `rm-040` Bound pyyaml (the last bare runtime dependency) — done
- `rm-099` Declare starlette and anyio as direct dependencies — done
- `rm-131` ui_ops cron-dispatch semaphore leaks on resolve failure — done
- `rm-138` cron NL-grammar edges: plural weekdays + property-based invariant lane — done
- `rm-152` Correct hermes_mission_usage _24h keys — they previously reported all-time totals — done
- `rm-158` Corrupt validation manifest must fail closed per-node, not wedge the mission tick — done
- `rm-167` Adopt upstream #91: fleet builtin profile ceilings for the new peers — done

<!-- managed by hermes-roadmap render; do not edit by hand -->
