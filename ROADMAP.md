# hermes-gpt — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- dependents (changes here affect): agent
- graph: evidence-derived (imports/refs/deploy surfaces); advisory

## Open items

### Ride out transient SQLITE_BUSY on dispatch-critical SQLite writes
- id: `rm-165` | track: reliability | priority: 112.0 | status: candidate
- acceptance: every writable sqlite3.connect site (operator_delegations.py:93, operator_mission_runtime.py:133, hermes_state.py:90, operator_mission_plan.py, operator_mission_budget.py) sets a bounded busy_timeout (token_store.py:376 PRAGMA busy_timeout=15000 precedent) with bounded retry on sqlite3.OperationalError for dispatch-critical writes (delegation state commits, mission runtime progress); reads that today collapse OperationalError into absence (operator_mission_budget.py:441-442 — agent-reported, verify at implement) distinguish locked-vs-absent and retry instead of reporting wrong state; retries are bounded and fail closed with a typed error, never fabricating success; regression tests hold a competing writer and assert the retry and the locked-vs-absent distinction; full suite green on both SDK lanes
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-165 (sibling hermes-agent 58957b1f8f + 6288139749 fixed this exact class 2026-11-25/27 — transient lock contention produced wrong verdicts and lost ticks); busy_timeout census re-verified live at 081a083462 by roadmap cad700e4c4b949ec9c975c536f91fe5b (12 non-test connect modules; token_store.py:376 the only busy_timeout site); proven by new retry/locked-vs-absent tests + full suite green + conductor validation digest recorded in the shipping PR

### Delegation liveness observability: age, bounded progress tail, stall inbox source, scheduled read-only derivation
- id: `rm-167` | track: operator-experience | priority: 111.0 | status: candidate
- acceptance: hermes_delegation_list/get surfaces expose seconds-since-last-activity (max of progress-stream row ts and work-order acceptance mtime — the runner's own liveness reference, operator_hermes_agent_runner.py:830-861); a bounded read-only progress tail (event kind + timestamp only, no prompt/content bodies) is operator-reachable; the owner inbox gains a delegation-stall source for rows running past a warning threshold (bounded, anti-noise, distinct from work_contract_review which covers succeeded-pending-acceptance only — operator_owner_inbox.py:61,19); an opt-in scheduled read-only (apply=False) observation pass exists so dead-worker derivation no longer waits for a manual apply-authority reconcile; no bodies persisted or exposed (delegation data boundary intact); full suite green
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-167; derivation-only-on-manual-reconcile + surface gaps re-verified live at 081a083462 (operator_delegations.py:255-273 exposes no age/staleness); proven by new surface/inbox tests + full suite green + conductor validation digest recorded in the shipping PR

### Operator first-run self-service: hermes-gpt doctor + smoke console commands
- id: `rm-168` | track: operator-experience | priority: 110.0 | status: candidate
- acceptance: [project.scripts] gains doctor and smoke entry points (pyproject.toml:60-63 today registers three); doctor runs the operator_diagnostics.py:233-554 check library against the local Hermes root, prints a human-readable report, exits non-zero on failure, and prints no secrets; doctor also reports the resolved effective value of every HERMES_GPT_* behavior gate with unset-vs-default distinguished (today ~15 gates scattered across README/docs and unreported by /api/me or the env-readable doctor check); smoke launches the server over stdio, performs the MCP handshake, calls safe read tools (hermes_skill_list, hermes_operator_doctor), asserts bounded latency, and exits non-zero with a pointed failure message; README quickstart gains a verification step and docs/operator-mode.md cross-references both commands; tests cover both commands
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-168 (diagnostics are MCP-tools-only — docs/operator-mode.md:484-509; a broken install must stand up a working MCP client, the broken thing, to learn why); check-library + scripts entries re-verified live at 081a083462; proven by new CLI tests + full suite green + conductor validation digest recorded in the shipping PR

### Campaign observability: read-only campaign/generation status surface + owner-inbox sources
- id: `rm-171` | track: operator-experience | priority: 109.0 | status: candidate
- acceptance: a read-only status surface (MCP tool and/or Flight Deck page) reports registered campaigns, current generation/segment phase, parked_owner_gate / parked_autopilot_gate stalls (operator_campaign_controller.py:95-96) with park age, consecutive-failure counts vs max_consecutive_failures, and permanently-stopped campaigns; the owner inbox gains parked and stopped sources (bounded, anti-noise); the surface carries no resume or mutation authority (owner-approval invariant intact); tests pin the surfaced fields against a fixture campaign tree; docs/campaigns.md and docs/README.md campaigns row updated
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-171 (docs/README.md:48 verbatim 'no MCP tools or server wiring'; zero attention/spool emission in the controller; owner inbox has no campaign source); re-verified live at 081a083462; proven by new surface tests + full suite green + conductor validation digest recorded in the shipping PR

### Pin the plan-node cutover decision lattice as a golden + stateful property lane
- id: `rm-166` | track: reliability | priority: 108.0 | status: candidate
- acceptance: the supersession/prebind/late-success/bind decision if-chains (operator_mission_plan.py:1895-2117 hermes_plan_bind_delegation, :1832-1866 _delegation_row_for_mission three-state, :950-1020 plan-node CAS) are extracted into a declarative decision table — inputs (prior-bound delegation state, lineage row check, node state, terminal/verdict/SHA match) to outcomes (PLAN_NODE_ALREADY_BOUND / PLAN_NODE_LINEAGE_MISMATCH / PLAN_NODE_TERMINAL / superseded / validated_retry) — pinned by a golden JSON in the tests_golden_tool_registry.json pattern with a deliberate-regeneration rule; a RuleBasedStateMachine hypothesis lane over bind/dispatch/terminal-verdict/reconcile(apply)/retry/foreign-steal interleavings asserts: at most one LIVE delegation per node, a foreign-mission delegation never binds, approval nodes never auto-advance on worker success, states move only along NODE_TRANSITIONS (:100-112), a superseded delegation never advances a successor node, and CAS mismatch raises; both land before the next cutover batch touches operator_mission_plan.py
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-166; churn evidence fresh at 081a083462 (+596 lines / 7 commits / 8 days into a 2,117-line module — assess run de0e2aed0d96 attempt ce426e18515f4862a2b705a145c4e31c finding F2); property-lane precedent test_delegation_lifecycle_properties.py:18-196; proven by the golden + hypothesis lane red-green on a seeded invariant break + full suite green on both SDK lanes

### Frontier drift-guard family: loader-pin staleness sentinel + dependency-floors audit + frontier canary
- id: `rm-169` | track: reliability | priority: 107.0 | status: candidate
- acceptance: tools/check_dependency_floors.py (sibling to tools/check_package_hygiene.py) audits pyproject floors vs the installed venv vs the CI exact-pin matrix vs live registry latest, emits JSON consumable by doctor/autopilot, and degrades loudly when offline; a nightly sentinel compares the frozen agent-loader pin (ci.yml:148 cca83848ec79, frozen 2026-10-22) against the sibling release-tag frontier and warns visibly when more than N releases behind; an optional non-required nightly frontier-canary job installs the frontier set (mcp 2.3.0, starlette 1.10.0) and runs core + loader-contract tests as warning-not-gate; the sentinel is proven by a test seeding a fake stale pin; plugin-sourced skill-metadata contract tests (operator_skill_resolution.py:239-251 bare-except silent degradation) fold in as a unit with a pinned plugin fixture
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-169 (CI exact pins mcp 1.28.1/2.0.0/1.30.0/2.2.0 under a research-2026-09-20 comment while SDK 2.3.0 shipped 2026-10-02 and the fleet venv already runs 2.3.0; the 2026-10-22 pip-unsatisfiability window was caught only as a red required lane — PR #67); re-verified live at 081a083462; proven by the seeded-pin test + audit output snapshot + full suite green

### Soak-hold forensics: pending-episode breakdown + transient-blip exclusion
- id: `rm-172` | track: reliability | priority: 106.0 | status: candidate
- acceptance: probe_stall_detection_ticks held-window records carry a bounded breakdown (pending episode ids, ages, tick counts, journal-head ts) so 'why is the canary holding' is a one-read diagnosis; the right-edge-pending hold excludes single-tick transient episodes (operator_slo_probe.py:883-888 gains the ticks>1 filter the module's own doctrine :705-707 already applies to the scored denominator) so a self-resolving blip at the journal head no longer flips an otherwise-PASS window to UNKNOWN (:944-948); persistent-episode fail-closed semantics unchanged; a new test covers the single-tick-open-at-head window (either PASS, or a documented decision to keep holding with the rationale in the docstring); the forensics fields are pinned by tests
- evidence: assess run de0e2aed0d96 attempt ce426e18515f4862a2b705a145c4e31c finding F1 (live 2026-11-27, same tree — all four current right-edge tests use >=2-tick episodes) absorbed via research 70b8a4343faa4df585767320b3b03722 candidates.md rm-172; live 23:45:00Z window burn documented in CHANGELOG Unreleased; proven by the new blip test + forensics field tests + full suite green

### Verification-ritual automation bundle: tools/verify.py + golden capture-stamp matrix + doc tool-count guard
- id: `rm-170` | track: operator-experience | priority: 105.0 | status: candidate
- acceptance: tools/verify.py runs the AGENTS.md verification ceremony as one command (smallest-first ordering, full suite under BOTH .venv and .venv-sdk2, tool-inventory + registry-neutrality checks, single summary verdict, golden-regeneration instructions on drift); capture_golden() stamps every interpreter lane it ran under and a meta-test fails when the currently-installed SDK family is absent from captured_under (today the golden records {mcp-2.2.0: true} only, so two-lane regeneration is unprovable — agent-reported, verify at implement); a guard test computes tool counts from tests_golden_tool_registry.json ordered_names and cross-checks every live-doc numeric claim (README.md, docs/autopilot.md, docs/daily-operations.md, docs/mcp-compatibility.md), excluding release notes as historical artifacts
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-170 (ceremony lives in prose; tools/ holds exactly one script; hand-maintained counts in four live docs); re-verified live at 081a083462 (tools/ listing, neutrality-test docstring); proven by the meta-test + count-guard test + full suite green

### Codex CLI minimum-version floor at launch + doctor field
- id: `rm-173` | track: reliability | priority: 102.0 | status: candidate
- acceptance: operator_codex.py gains a declarative CODEX_MIN_VERSION with a typed CODEX_VERSION_TOO_OLD refusal in the launch path (today _probe_codex_version :136-146 returns the version string and it is never compared; resolve_codex_exe :169-215 gates only on path); the floor is env-tunable with invalid values falling back to no-floor with a warning (the stall-ceiling env pattern HERMES_GPT_HERMES_AGENT_STALL_CEILING_SECONDS); doctor reports version-vs-floor; tests use fake version probes for both sides of the floor; docs/codex.md notes the floor and its bump cadence (folded into the rm-169 audit output)
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-173 (codex CLI 0.163.0 -> 0.172.0 in ~6 weeks, npm 2026-11-27; no floor anywhere in ROADMAP.md); probe/gating lines re-verified live at 081a083462; proven by the fake-probe tests + full suite green

### pi client profile: compat smoke + setup guide (Gemini-profile pattern)
- id: `rm-174` | track: operator-experience | priority: 96.0 | status: candidate
- acceptance: an opt-in pi client profile with a compat test mirroring test_gemini_compat.py (against a pinned pi-coding-agent revision — the loader-pin lesson) and a verified setup guide for running the Operator as an MCP server inside pi-coding-agent; default surfaces unchanged and the read-only/dry-run ladder intact; docs gain the profile page alongside gemini-spark.md / codex.md / windows-chatgpt-codex.md; profile-aware session-history guidance where applicable; acceptance mirrors the open Gemini CLI profile item's shape
- evidence: research 70b8a4343faa4df585767320b3b03722 candidates.md rm-174 (docs/ maintains the per-client profile pattern; the roadmap already minted the same pattern for Gemini CLI; pi-coding-agent npm 1.3.0 -> 1.7.0 since October; the surrounding delegation fleet runs inside pi with no profile, compat test, or doc); profile-file pattern re-verified live at 081a083462; proven by the compat test + full suite green

### Adopt upstream skill-loader hardening trio (upstream issue #74 full half)
- id: `rm-081` | track: operator-experience | priority: 115.0 | status: candidate
- acceptance: merged tree reconciles fork+upstream halves into a single resolution authority; loader failure is fail-closed with a test proving a required-but-unloadable skill blocks dispatch; probes use preprocess=False with a test asserting inline_shell side effects never run during validation; fork surfaces (plan create/validate/placement) keep enforcement at parity with upstream's breadth (work contracts/swarm); full suite + upstream's new tests green on both SDK lanes
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Adopt upstream v0.13 Autopilot (9-commit gap; PR #82)
- id: `rm-098` | track: security | priority: 115.0 | status: candidate
- acceptance: the 9 upstream commits merge or cherry-pick onto the fork line with conflicts reviewed line-by-line against fork invariants (Owner Mode break-glass, secret-path denials, default read-only; Autopilot stays default-off at adoption); full suite green in CI shape; CHANGELOG records the catch-up; #83/#84 recorded as follow-on once merged upstream
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Move blocking SQLite off the serving event loop (ui_chat + live-events WS)
- id: `rm-076` | track: reliability | priority: 110.0 | status: in_progress
- acceptance: every blocking SessionDB/live-event-store call reachable from async handlers/WS runs via asyncio.to_thread (or equivalent executor offload); a regression test holds SessionDB._lock in a background thread and asserts a concurrent ui_chat request completes within a bound (no loop starvation); the WS poll path performs no connect-timeout or sqlite work on the loop thread
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Offload /api/me + /api/connection status reads off the serving loop (rm-076 remainder)
- id: `rm-151` | track: security | priority: 105.0 | status: in_progress
- acceptance: both payloads' token-store reads execute off the loop (asyncio.to_thread or the in-file equivalent); regression test holds the token-store path blocked and asserts a concurrent lightweight async handler still completes (a sync TestClient cannot observe this — use the async test pattern rm-076's suite established); payload shapes unchanged; a note lands in docs/ui-security-boundary.md transport-health section that the poll endpoint is off-loop
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Add test coverage for 17 untested module(s)
- id: `rm-002` | track: operator-experience | priority: 100.0 | status: candidate
- signals: reliability.no_tests:backfill_routine_discharge.py, reliability.no_tests:hermes_state.py, reliability.no_tests:tool_registry.py, reliability.no_tests:tools/check_package_hygiene.py, reliability.no_tests:web/src/chat/ActivityCard.tsx (+12 more)
- acceptance: Every module in `['backfill_routine_discharge.py', 'hermes_state.py', 'tool_registry.py', 'tools/check_package_hygiene.py', 'web/src/chat/ActivityCard.tsx', 'web/src/chat/ChatPage.tsx', 'web/src/chat/Composer.tsx', 'web/src/flight/AccountPanel.tsx', 'web/src/flight/ApprovalsPanel.tsx', 'web/src/flight/ContractsPanel.tsx', 'web/src/flight/DeckOverview.tsx', 'web/src/flight/EventHistoryPanel.tsx', 'web/src/flight/FleetPanel.tsx', 'web/src/shared/AccountStatusBanner.tsx', 'web/src/shared/ConnectionStatus.tsx', 'web/src/stores/session-list.ts', 'web/vite.config.ts']` has a corresponding test file with at least one passing test
- evidence: full suite green (python -m pytest -q) at HEAD; conductor validation digest validation:v1:<sha> recorded in the shipping PR

### Refactor 20 high-complexity function(s)
- id: `rm-001` | track: operator-experience | priority: 90.0 | status: candidate
- signals: reliability.complexity_hot:operator_agent_readiness.py::source_protocol, reliability.complexity_hot:operator_autopilot.py::build_summary, reliability.complexity_hot:operator_campaign_controller.py::campaign_controller_tick, reliability.complexity_hot:operator_contract.py::_check_forbidden, reliability.complexity_hot:operator_delegations.py::hermes_delegation_cancel (+15 more)
- acceptance: Each flagged function is decomposed below the branch threshold with behavior locked by characterization tests
- evidence: ast-based branch-count check passes at HEAD (full suite green; conductor validation digest validation:v1:<sha> recorded in the shipping PR)

### Isolate the mission-events long-poll from the shared anyio threadpool
- id: `rm-096` | track: security | priority: 90.0 | status: in_progress
- acceptance: long-poll waits no longer occupy shared threadpool tokens — a dedicated anyio.CapacityLimiter (anyio.to_thread.run_sync(limiter=...) verified in .venv) for wait-bearing endpoints, or an asyncio-native wait bridge; a regression test saturates the shared limiter with 40 holders and asserts a mission-events request still completes; existing mission-events behavior (25s max wait, event delivery, cursor semantics) unchanged
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### ui_ops cron-dispatch semaphore leaks on resolve failure
- id: `rm-131` | track: security | priority: 90.0 | status: in_progress
- acceptance: dispatch-path ordering fixed — resolve root (and any other raising validation) BEFORE acquiring the semaphore, or try/finally the acquire→dispatch span so every exit releases the token; regression test injects a `_resolve_root` failure and asserts (a) a clean error response, (b) semaphore capacity unchanged — a subsequent dispatch is NOT 429-capped — repeated > `_CRON_DISPATCH_LIMIT` times.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Registry and bound for fire-and-forget cron dispatch, with completion audit
- id: `rm-097` | track: security | priority: 88.0 | status: in_progress
- acceptance: cron dispatch goes through a bounded executor with an operator-visible registry (active/finished counts surfaced via doctor or an ops live event); a completion record (success/failure + duration) lands in the audit trail when the run finishes, not at dispatch; a cap-exceeded request is rejected loudly (429-class) like ui_chat; tests cover dispatch, completion-audit ordering, injected-failure audit, and cap rejection
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Adopt next_cursor on empty filtered pages in the WS live-events loop (rm-080 residual)
- id: `rm-095` | track: docs | priority: 85.0 | status: in_progress
- acceptance: the WS loop advances its cursor to the returned next_cursor on empty pages too (or an equivalent watermark adoption), preserving rm-080's snapshot-ordering guarantee (a concurrent insert is delivered or rescanned, never skipped); a regression test asserts an idle filtered WS client advances past N non-matching events without rescanning them; the docs/live-events.md cursor-semantics paragraph holds verbatim
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Python floor bump 3.10->3.11 plus a 3.13 CI lane (dated deadline)
- id: `rm-100` | track: reliability | priority: 75.0 | status: candidate
- acceptance: CI matrix adds a green 3.13 lane (and 3.14 if deps allow); a dated plan lands the 3.11 floor bump with the next fork release (requires-python >=3.11, matrix drops 3.10, tomli conditional removed); CHANGELOG records both
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### cron next-fire + timezone preview at arm time
- id: `rm-132` | track: docs | priority: 72.0 | status: in_progress
- acceptance: hermes_cron_create dry-run plan (and the browser-UI confirm surface) include next-N (>= 3) computed fire times plus the effective timezone name used to resolve them; works for interval, daily-time, weekday, and once schedules; plan does not imply the external scheduler's tz is authoritative (contract documented in docs/operator-mode.md cron section); tests cover each schedule kind including a TZ-set environment.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### MCP spec-revision lineage refresh + SDK 2.3.x lane
- id: `rm-048` | track: docs | priority: 70.0 | status: in_progress
- acceptance: docs/mcp-compatibility.md corrected to describe the revision lineage per SDK family instead of claiming one "latest"; the rm-009 revision assertion parameterized per installed SDK pin (still fails loudly on unexpected revisions); a mcp==2.3.x lane added to CI (or pins refreshed per rm-009's cadence rule) with a spec-delta review note for hermes surfaces; MCP-Auth cross-RFC notes (RFC 9728/9700 now Proposed Standard, draft-ietf-oauth-parallel-refresh adopted) reflected in docs/oauth.md where they touch hermes behavior
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Ship or document a browser-UI build path (web assets absent from wheel/MANIFEST)
- id: `rm-077` | track: docs | priority: 70.0 | status: candidate
- acceptance: EITHER the wheel/sdist carries a prebuilt web/dist (with a package-hygiene assertion), OR README + docs/operator-mode.md document the exact supported build step (npm ci && npm run build / HERMES_GPT_UI_DIR) verified to produce a served UI; tools/check_package_hygiene.py extended to match whichever path is chosen
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### fork distribution identity: local version segments or never-publish
- id: `rm-133` | track: docs | priority: 68.0 | status: candidate
- acceptance: decision recorded FIRST — (a) local version segment (e.g. 0.12.0+codeo1io or +<line-tag>) on fork releases, or (b) explicit never-publish-on-PyPI policy with a private index — in RELEASE_CHECKLIST.md + README; artifact metadata carries line provenance (commit or origin URL) so pip + doctor distinguish codebases; doctor VERSION line gains the line identity (extends operator_diagnostics.py:904); decision + implementation land BEFORE any 0.13-numbered fork release.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Extend skill validation to Work Contract and Swarm dispatch (hermetic #76 semantics)
- id: `rm-054` | track: docs | priority: 65.0 | status: candidate
- acceptance: contract creation and pre-dispatch revalidation fail closed with distinct not_found/unavailable codes and zero mutation on rejection (tests pin the no-mutation path); candidates preview and score share one validation entry point so their verdicts are identical for identical inputs (assess-F7 scenario replayed divergence-free); docs state where validation runs (AGENTS.md docs rules: exact surfaces, explicit gates)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Surface ui_api mount failure as an operator-visible signal
- id: `rm-078` | track: security | priority: 65.0 | status: in_progress
- acceptance: a failed UI mount emits an operator live event AND an audit record (or a doctor WARN) while the server still boots; a test simulates the import failure and asserts the signal fires exactly once; docs/operator-mode.md notes the failure mode
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### fetch-metadata + content-type hardening on browser-UI state changes
- id: `rm-134` | track: operator-experience | priority: 63.0 | status: candidate
- acceptance: state-changing (POST) routes reject Sec-Fetch-Site: cross-site requests and Origin headers outside the allowed set (UI origin + chatgpt.com + issuer), and require Content-Type: application/json on JSON-body routes; the ChatGPT-side origin keeps working (it is in the CORS list today); non-browser MCP clients unaffected; any escape-hatch env documented; tests cover allow/deny/cross-site/preflight cases.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Raise build floor to setuptools>=77 (PEP 639 license string)
- id: `rm-027` | track: compliance | priority: 62.0 | status: in_progress
- acceptance: floor raised to >=77 (or license switched to table form) so declared-floor builds work; sdist+wheel build verified in a --no-isolation environment; no behavior change to isolated CI builds
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-046` | track: docs | priority: 60.0 | status: in_progress
- rider (2026-11-27, run de0e2aed0d96411bb35b77e9c18f4074 roadmap cad700e4c4b949ec9c975c536f91fe5b, from research 70b8a4343faa4df585767320b3b03722): extend the guard from README references to the docs/README.md authority map itself — docs/solutions/ (four incident write-ups) and maintenance-cycle-log.md exist on disk but appear in no map row, and release-notes-v0.16.2.md exists with no v0.16.1/v0.16.2 table row; the guard asserts every docs/ file is mapped (or explicitly historical) and per-row version pins are consistent with pyproject and the on-disk release-notes set
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refreshed or re-labeled as historical; `python -m build` + `twine check dist/*` + tools/check_package_hygiene.py dist/* run with the two docs present
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### v0.13.0 release-readiness batch: publish + deployed-remote rollout
- id: `rm-083` | track: operator-experience | priority: 60.0 | status: candidate
- acceptance: RELEASE_CHECKLIST executed for v0.13.0 (or the next fork version): CHANGELOG sectioned, package built + twine/check_package_hygiene verified, version policy resolved per rm-065, deployed remote rolled forward and verified (operator doctor clean); release notes state distribution channels truthfully (no implied GitHub/PyPI sync)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### live-deployment provenance capture + uncommitted-delta release blocker
- id: `rm-135` | track: docs | priority: 60.0 | status: candidate
- acceptance: provenance-capture doctor check (or deploy-time record) captures the serving process's self-reported version + working-tree state (commit, dirty flag, branch) into a durable operator-visible record; a release/ops rule BLOCKS promoting a build whose live checkout carries uncommitted deltas (or forces an explicit override with the delta recorded); docs/runtime-checkout.md refreshed or re-labeled per AGENTS.md rules as part of the fix.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Correct hermes_mission_usage _24h keys — they previously reported all-time totals
- id: `rm-152` | track: operator-experience | priority: 60.0 | status: in_progress
- acceptance: usage rows joined/filtered by sessions.started_at >= cutoff with the schema-drift fallback the intent comment describes (missing started_at -> fail loud or explicitly-degraded output, never silently all-time); a new test with a stale pre-cutoff usage row asserted EXCLUDED from _24h sums; the baked test updated to a two-window fixture; full test_operator_mission.py green
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### declare the browser-UI agent-runtime cross-project seam
- id: `rm-136` | track: operator-experience | priority: 58.0 | status: candidate
- acceptance: the seam is DECLARED — vendored/stubbed interfaces behind an explicit boundary module, OR a documented contract (which external tree provides them, at what version) + an import-contract test that runs on the clean checkout and fails LOUDLY (never silent IMPORT_UNAVAILABLE) when the declared provider is missing; pyproject/docs name the external requirement; if a degradation path is kept, it is visible in doctor.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Branch protection on codeo1io master (extends rm-008 with red-master evidence)
- id: `rm-038` | track: reliability | priority: 55.0 | status: candidate
- rider (2026-11-27, run de0e2aed0d96411bb35b77e9c18f4074 roadmap cad700e4c4b949ec9c975c536f91fe5b, from research 70b8a4343faa4df585767320b3b03722): channel authorization verifies required checks via check-runs on the exact merge/tag commit, tolerating an unavailable or Pro-gated branch-protection rules endpoint with an explicit unverified state instead of assumed green (sibling pattern hermes-agent 622985bff6) — pairs naturally with this item's protection gap and the gh wrong-repo hazard (always -R codeo1io/hermes-gpt)
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
- id: `rm-052` | track: security | priority: 55.0 | status: in_progress
- acceptance: a CI job or release-checklist step queries PyPI and reports/fails on unacknowledged divergence >=1 minor; RELEASE_CHECKLIST.md references it
- acceptance: /oauth/register rate-limited (per-peer bound); dynamic clients gain TTL with cleanup() eviction; an operator list/purge surface exists; re-import revalidates redirect URIs; the :1206 comment made truthful; tests prove an unauthenticated fill-up cannot permanently exhaust the cap (TTL reclaim), expired clients fail closed at exchange, and the purge round-trip works; RFC 7592 update/delete shape optional stretch
- acceptance: the authorize path validates/encodes client_id before comparison and rejects with 401 JSON `invalid_client` (never a 500, never a redirect to an unvalidated client_id — RFC 6749 forbids redirecting unknown clients); a regression test mints a non-ASCII client_id and asserts the 401 JSON; no traceback in the audit path. (Acceptance wording amended at review-fix 31581701: the implemented 401-JSON contract is stricter than the originally drafted error-redirect wording and is what the review verified.)
- acceptance: docs (gemini-spark and/or an oauth section) state both knobs, their defaults, and the DCR=0 single-client recipe; the docstring describes the actual registry; per docs rules the claims are checked against code before landing
- acceptance: macOS binds the full runtime_roots list (or a comment documents why one root suffices on Darwin) with a unit test covering multi-root env-shebang resolution
- acceptance: authorize success and error redirects include iss=<issuer>; AS metadata advertises authorization_response_iss_parameter_supported: true; tests pin both; docs note added
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Serve the curated skill set via the official MCP Skills extension (read-only)
- id: `rm-082` | track: operator-experience | priority: 55.0 | status: candidate
- acceptance: gated on an SDK support probe passing on both SDK families (same gate pattern as rm-011); additive read-only surface exposing only allowlisted skills via skills/list + skills/get with skill:// resources; hermes_* skill tools remain canonical; safety tests prove no raw skill bodies or side effects leak beyond the existing read-only boundary; a deterministic tools/list ordering assertion (2026-07-28 spec SHOULD) rides this surface's tests
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Declare starlette and anyio as direct dependencies
- id: `rm-099` | track: reliability | priority: 55.0 | status: in_progress
- acceptance: pyproject declares starlette and anyio with bounds consistent with the resolved floor (e.g. starlette>=0.40,<2; anyio>=4,<5) and a comment naming mcp[cli] as the existing transitive source; CI installs green on the declared range; the declaration introduces no version drift (resolver output unchanged before/after)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Document the convergence-shipped OAuth surface and repair the CHANGELOG
- id: `rm-034` | track: security | priority: 52.0 | status: candidate
- acceptance: docs/oauth.md documents all three knobs (name, default, gates, security posture incl. knob-vs-endpoint semantics); CHANGELOG gains a convergence entry and the :12 run-on is fixed; AGENTS.md docs rules (defaults/gates explicit) satisfied
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Evaluate CIMD as the primary client registration path (strategic)
- id: `rm-053` | track: security | priority: 52.0 | status: in_progress
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
- id: `rm-036` | track: operator-experience | priority: 48.0 | status: candidate
- acceptance: conformance note mapping hermes skill surfaces onto the published extension (naming, discovery roots, precedence); PR #20's tests verified against it; upstream #74 outcome recorded when it lands (contract agreed architecture-first per run-684b9786 rm-028)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### SHA-pin the reusable private-leak-sentinel workflow
- id: `rm-043` | track: reliability | priority: 48.0 | status: in_progress
- acceptance: the reusable-workflow reference pins an immutable commit SHA (human-readable branch noted in a comment); a re-pin rotation procedure is documented
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### OpenAPI description generated from the 20-route HTTP surface
- id: `rm-137` | track: operator-experience | priority: 46.0 | status: candidate
- acceptance: an OpenAPI 3 document GENERATED from the route table (not hand-maintained prose), served at a read-only discovery endpoint or shipped in docs, with envelope schemas from the existing ok/err normalization; a contract test fails when a route's shape drifts from the document; the document is marked loopback-default/read-only-gates per product invariants.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Fail-fast on empty/invalid code_challenge at issuance
- id: `rm-018` | track: security | priority: 45.0 | status: in_progress
- acceptance: issue_authorization_code raises on empty/malformed challenge (internal callers get loud errors, not dead credentials); rm-003's empty-challenge-rejected-at-exchange test still passes; no valid flow regresses
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Docs/CHANGELOG truthfulness bundle (rm-027 semantics + walk-bound docstring)
- id: `rm-056` | track: docs | priority: 45.0 | status: in_progress
- rider (2026-11-27, run de0e2aed0d96411bb35b77e9c18f4074 roadmap cad700e4c4b949ec9c975c536f91fe5b, from research 70b8a4343faa4df585767320b3b03722): README quickstart-first restructure — move 'Choose the path you need' and 'Local quickstart' (today ~line 208 of a 506-line file, buried under twelve per-version narrative sections) above the release narrative and compress the narrative into a release-history index; information-architecture only, no behavior change
- acceptance: CHANGELOG Unreleased entry documents the fail-closed semantics with an upgrade note for plans referencing unresolvable skills; the shipped-docs guard (rm-046 remainder) covers any new docs; the F8 docstring corrected to describe directory-count semantics (or the counter fixed to count entries, with a test); AGENTS.md "behavior changes → CHANGELOG" rule satisfied for this and future validation-gate landings
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Harden token/key file staging beyond chmod-after-write
- id: `rm-153` | track: security | priority: 45.0 | status: in_progress
- acceptance: every staged secret file created with restrictive mode AT creation under a unique-adjacent name (in-repo precedent operator_cron.py / operator_workspace.py / operator_job_supervisor.py) or O_EXCL; secrets dirs mkdir with explicit 0o700; fsync of key material before the atomic replace; a umask-0 test asserting final file AND dir modes are 0600/0700; a two-writer test asserting no interleaved or lost staging writes; the token DB reaches 0600 with no observable window (or documents why it cannot)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### cron NL-grammar edges: plural weekdays + property-based invariant lane
- id: `rm-138` | track: reliability | priority: 44.0 | status: in_progress
- acceptance: plural weekday names accepted (or a targeted error naming the singular form); a hypothesis property-based lane in the dev group (declaration comment naming the transitive source per the rm-099 rule) pins the four invariants with a fixed seed for deterministic CI; zero-minute floor coverage rides rm-057.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Updater must verify it found a hermes-gpt checkout before fast-forwarding
- id: `rm-042` | track: reliability | priority: 42.0 | status: in_progress
- rider (2026-11-27, run de0e2aed0d96411bb35b77e9c18f4074 roadmap cad700e4c4b949ec9c975c536f91fe5b, from research 70b8a4343faa4df585767320b3b03722): post-condition half of the same gate — after fast-forwarding, run test_tool_inventory.py plus a doctor probe against the new tree before restarting, reusing the existing fetch-rollback step machinery (updater.py:435-441); on smoke failure roll back and report a typed failure (verify-the-merge at the fleet's single code-entry point; _source_update today reports applied=True with no post-apply checks, updater.py:93-167)
- acceptance: candidate roots are verified as hermes-gpt checkouts (pyproject name / package marker / remote URL) with a loud refusal otherwise; regression test using a foreign git-root fixture
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Single peer_main: dedupe the dead entry point and test the packaged peer CLI
- id: `rm-037` | track: operator-experience | priority: 40.0 | status: candidate
- rider (2026-11-27, run de0e2aed0d96411bb35b77e9c18f4074 roadmap cad700e4c4b949ec9c975c536f91fe5b, from research 70b8a4343faa4df585767320b3b03722): same legacy-surface family — retire the legacy SSE transport path (server.py:4224-4328 --sse flag + _run_legacy_server, reachable only via the legacy CLI dispatch) via a dry-run-first deletion lane: prove no operator/client depends on SSE (audit + dry-run census first), then remove the flag, branch, and its tests; shrinks the surface both SDK lanes and the neutrality combos must carry
- acceptance: one canonical peer_main (dead one removed or repointed with a rationale comment); the packaged entry (g4c peer_main / its serve stack, port 4780) covered by at least one test exercising require-secure-transport and the CLI surface
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Retire fixed-name '.tmp' staging across operator write paths
- id: `rm-154` | track: security | priority: 40.0 | status: in_progress
- acceptance: every staging site uses a unique-adjacent temp name (pid+token or mkstemp) created with restrictive mode and atomically replaced; a repo-wide guard test fails on any NEW fixed-name staging path (scan '.tmp' literals constructed without a uniquifier, mirroring the census command `rg -n "\.tmp" --glob '*.py' -g '!test_*'`); the touched files' existing tests stay green; no behavior change beyond the name
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Profile-aware skill-resolution gate before placement/dispatch
- id: `rm-041` | track: architecture | priority: 38.0 | status: in_progress
- acceptance: placement/dispatch validates that the target profile can actually resolve each referenced skill at execution time (or fails loudly pre-flight); contract agreed architecture-first with upstream before implementation
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Gemini CLI client profile (user-need evidenced by upstream #54)
- id: `rm-049` | track: docs | priority: 35.0 | status: in_progress
- acceptance: opt-in Gemini CLI client profile analogous to Gemini Spark (profile-aware session history + verified setup guide), default surfaces unchanged (read-only/dry-run ladder intact), test file mirroring test_gemini_compat.py; docs/codex.md terminology rules respected (client profile vs delegated worker)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Account-status banner is dead code on auth-configured deployments
- id: `rm-050` | track: security | priority: 35.0 | status: in_progress
- acceptance: EITHER the SPA obtains and attaches credentials (explicit login flow or same-origin cookie session) and /api/me returns payload under configured auth (tested, incl. unauthorized case), OR the banner is scoped/documented as local-mode-only with docs stating the auth-mode limitation
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### SEP-414 trace-context correlation for cross-agent runs
- id: `rm-084` | track: security | priority: 35.0 | status: candidate
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
- id: `rm-079` | track: operator-experience | priority: 30.0 | status: in_progress
- acceptance: filter once at the boundary and pass the filtered set (warning preserved on all paths), or drop the `queried` computation entirely; behavior for allowed/denied mixtures locked by tests on both list paths
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Fix the live-events cursor clamp (dead MAX(seq) query)
- id: `rm-080` | track: reliability | priority: 30.0 | status: in_progress
- acceptance: either implement the intended high-watermark clamp with a test for the skip-ahead case, or delete the MAX(seq) query with a test asserting cursor semantics unchanged; poll-path cost drops by one query
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### doctor ui_cron_dispatch cross-process caveat (in-process-only registry read)
- id: `rm-140` | track: security | priority: 30.0 | status: in_progress
- acceptance: the check's detail text marks it "in-process only" (or reports the serving-process identity it introspected) and docs/operator-mode.md states the caveat; optional follow-on note names the durable-audit-log alternative if cross-process authority is ever needed.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Small reliability bundle: cron zero-interval floor, placement walk reuse, preview parity
- id: `rm-057` | track: performance | priority: 25.0 | status: in_progress
- acceptance: schedule parser rejects or floors zero/negative intervals with a dedicated test; targets/manifest walk memoized per (root, sources) with bounded TTL and invalidation on profile changes (perf probe shows repeat-call reuse); no residual preview/score divergence after rm-054's refactor
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Own the environment-dependent skips plus an autouse audit-override reset
- id: `rm-101` | track: security | priority: 25.0 | status: candidate
- rider (2026-11-27, run de0e2aed0d96411bb35b77e9c18f4074 roadmap cad700e4c4b949ec9c975c536f91fe5b, from research 70b8a4343faa4df585767320b3b03722): timing-bound companions to the skips — desensitize wall-clock-bound tests on hosted runners (acceptance windows, monotonic clocks, right-edge-pending-style holds; 17 test files use sleeps; sibling precedent hermes-agent a797f55204; the live 23:45:00Z journald flush-lag window burn was this class — see rm-172)
- acceptance: each environment-dependent skip carries an owner note or becomes a hard condition; an autouse fixture resets audit-log override state between tests; full suite green with the fixture in place and no ordering-dependent failures
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### subscriptions/listen alignment study (deferred until a push consumer exists)
- id: `rm-014` | track: operator-experience | priority: 20.0 | status: in_progress
- acceptance: revisit when a push-style consumer is required: decide between a listen-stream surface or documenting cursor polling as the hermes-native pattern; no action while all consumers poll
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### CI web-lane npm caching + stale self-hosted comments
- id: `rm-039` | track: performance | priority: 20.0 | status: candidate
- acceptance: actions/setup-node cache enabled for the web job (or a recorded reason not to); stale comments refreshed to match hosted runners
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Reconcile divergent vercel.json configs
- id: `rm-045` | track: docs | priority: 15.0 | status: in_progress
- acceptance: one authoritative config kept (the other deleted or its role documented in the docs/README.md authority map); deploy shape verified once
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Remove or wire the unused dompurify web dependencies
- id: `rm-044` | track: reliability | priority: 12.0 | status: in_progress
- acceptance: dependencies removed (clean install + green web build) or sanitization genuinely wired with a test proving raw HTML is stripped
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

## Closed items

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
- `rm-155` Refresh stale top-level documentation — done

<!-- managed by hermes-roadmap render; do not edit by hand -->
