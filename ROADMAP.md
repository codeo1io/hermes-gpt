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

### Adopt upstream v0.13 Autopilot (9-commit gap; PR #82)
- id: `rm-098` | track: reliability | priority: 115.0 | status: candidate
- acceptance: the 9 upstream commits merge or cherry-pick onto the fork line with conflicts reviewed line-by-line against fork invariants (Owner Mode break-glass, secret-path denials, default read-only; Autopilot stays default-off at adoption); full suite green in CI shape; CHANGELOG records the catch-up; #83/#84 recorded as follow-on once merged upstream
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### Move blocking SQLite off the serving event loop (ui_chat + live-events WS)
- id: `rm-076` | track: reliability | priority: 110.0 | status: in_progress
- acceptance: every blocking SessionDB/live-event-store call reachable from async handlers/WS runs via asyncio.to_thread (or equivalent executor offload); a regression test holds SessionDB._lock in a background thread and asserts a concurrent ui_chat request completes within a bound (no loop starvation); the WS poll path performs no connect-timeout or sqlite work on the loop thread
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

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

### v0.13.0 release-readiness batch: publish + deployed-remote rollout
- id: `rm-083` | track: reliability | priority: 60.0 | status: candidate
- acceptance: RELEASE_CHECKLIST executed for v0.13.0 (or the next fork version): CHANGELOG sectioned, package built + twine/check_package_hygiene verified, version policy resolved per rm-065, deployed remote rolled forward and verified (operator doctor clean); release notes state distribution channels truthfully (no implied GitHub/PyPI sync)
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

### live-deployment provenance capture + uncommitted-delta release blocker
- id: `rm-135` | track: reliability | priority: 60.0 | status: candidate
- acceptance: provenance-capture doctor check (or deploy-time record) captures the serving process's self-reported version + working-tree state (commit, dirty flag, branch) into a durable operator-visible record; a release/ops rule BLOCKS promoting a build whose live checkout carries uncommitted deltas (or forces an explicit override with the delta recorded); docs/runtime-checkout.md refreshed or re-labeled per AGENTS.md rules as part of the fix.
- evidence: campaign-recorded in hermes-gpt ROADMAP.md

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

## Cycle 2 refresh (attempt 71fae61f179840e5a4630cf76b15a1c5, repository-maintenance:12c24d07e02440efb0adc0e7c51d8992:cycle:2, 2026-10-03 ~13:15Z)

<!-- census marker at mint time: rm-205 + rm-206 minted HERE (next free after = rm-207). Fresh fleet census 2026-10-03 ~13:1xZ (all hermes-gpt worktrees, campaign ledgers, /tmp ledger patches, delegate spool; NO rm-205/rm-206 entry anywhere — every 'rm-205' string found is a 'next free' note in 1bc41b1b's marker/ledger): frontier = rm-204 (run-a0f8eb89b525 roadmap attempt 1bc41b1b, 11:52Z, patch /tmp/1bc41b1b-scratch/ROADMAP.ledger.patch). Fleet ledger claims known at census: committed rm-140 @ e490130737 (canonical checkout left clean — landing applies the patch stack); worktree mints rm-141 (run-c5fba76a9e6c), rm-151..159 (run-ce3efdb4b6a3), rm-160..168 (run-9b1770fc3065), rm-169..179 (run-f65169a1ce22), rm-180..189 (run-e1e8d7ecd932 on-disk), rm-193 (run-74896be4b661), rm-196..rm-200 (run-e618b73f8389, patch c819e771/422bd614), rm-196/rm-197 double-minted vs run-d33be0958593 (1bbd1dda) with DISTINCT titles ('UI chat ingress bounds + SessionDB retention' / 'private-leak-sentinel workflow pin' vs 'Baseline security headers CSP/nosniff' / 'production asserts') — all four survive, merge by title lowest-id-wins; patch mints rm-180/181 (79b3e882; df059aaeda57 title-collides — renumber at gate), rm-185..190 (03ec00ae), rm-189..191 (ca49ab4b / c34d91cd v2), rm-192 (92395980), rm-195 (dfaf334f988c via 3f4f12b8), rm-201 (run-facc0f13c2ed), rm-202+rm-203 (run-af71b550d158), rm-204 (run-a0f8eb89b525). rm-194 = RESERVED renumber target (3f4f12b8 plan); rm-193 slot contested by title (74896be4b661 on-disk vs 3f4f12b8 renumber plan). Cross-repo rm- prefixes (agenttrace rm-195..238, stonks rm-001..051, dashboard rm-13xxx, hermes-agent campaign cycle ids c1-A*/R*/L*) are NOT hermes-gpt census members. Landing gate: apply ledger patches in mint order 79b3e882 -> 03ec00ae -> ca49ab4b/c34d91cd -> 92395980 -> 74896be4b661 -> 3f4f12b8 -> 1bbd1dda -> c819e771/422bd614 -> 5d7b82aa -> a5bcf00e -> 1bc41b1b -> THIS PATCH; title collisions lowest-id-wins. -->

### Server shutdown lifecycle: bounded graceful drain + turn-lease release + child-process cleanup on restart
- id: `rm-205` | track: reliability | priority: 66.0 | status: candidate
- signals: this run's research (attempt 1b2d18ef, mint-ready candidate M1, /tmp/1b2d18ef-scratch/research-candidates.md section 2). Restart is the SANCTIONED upgrade flow — updater.py:209 tells the user "Hermes GPT was updated. Restart any running Hermes GPT or Codex MCP process." — yet nothing at the application level owns what an in-flight turn experiences at that moment: (1) both `uvicorn.run(...)` sites (server.py:3864, server.py:3928) pass no `timeout_graceful_shutdown` and install no signal handler (uvicorn default None — verified in the installed 0.41.0 config.py:218), so long-lived WS live-events / SSE connections hold shutdown open with no bound and real restarts either hang on connected clients or are killed hard; (2) every chat turn runs on a daemon=True thread (ui_chat.py:760-772), and on process exit daemon threads are frozen mid-execution so `_run_turn`'s finally (ui_chat.py:596) never runs — the turn lease is not released and recovery is only the 300 s TTL expiry (ui_chat.py:748): Mission Control "busy" misreports for up to 5 minutes after every restart-mid-turn; (3) turns drive agent/Codex child processes (operator_session.py:200 daemon thread; killpg paths exist per-operation in operator_runners/operator_policy) but nothing ties child reaping to SERVER shutdown. No fleet title owns shutdown/drain/SIGTERM (rm-067 = tmpdir lifecycle; rm-172 = lease renewal + Thread.start guard; rm-196 = request-body ingress caps + SessionDB retention; rm-206 below = steady-state gate/reap) — MCP's stable 2026-07-28 revision made the server stateless at the protocol layer, which raises, not lowers, the bar for application-level turn lifecycle hygiene.
- acceptance: (a) both `uvicorn.run` sites pass an explicit, bounded, documented `timeout_graceful_shutdown`, and the SIGTERM path closes WS live-events / SSE streams with a terminal event rather than truncation; (b) in-flight turn leases are released or explicitly marked interrupted at shutdown (registry of live turn threads + best-effort release, or a documented + tested shortened-TTL reliance for the shutdown window) — no silent 300 s "busy" ghost after restart; (c) processes this server spawned are reaped on shutdown (bind the existing per-op killpg paths to the shutdown path); (d) regression tests: simulated SIGTERM with a live WS connection plus an in-flight turn asserts bounded shutdown, a terminal SSE/WS event, and a free lease; (e) docs/operator-mode.md restart/upgrade section states what in-flight turns experience.
- evidence: line reads at base 0670f4cfc2 (server.py:3864,:3928; ui_chat.py:596,:748,:760-772; updater.py:209; operator_session.py:200; installed uvicorn 0.41.0 config.py:218); fleet title sweep over 156 ids (/tmp/1b2d18ef-scratch/fleet-title-index.txt); implement adds the (d) tests as regression seeds.

### ui_chat turn-registry truthfulness: hung turns must still count against the gate, stale turns must be reaped, agent calls need a watchdog
- id: `rm-206` | track: reliability | priority: 64.0 | status: candidate
- signals: this run's assess (attempt 854045a2, finding F2, /tmp/854045a2-assess/findings.md). ui_chat.py:181-185 `_active_turn_count` counts only `not t.done and (now - t.started_at) < TURN_RETENTION_S` (TURN_RETENTION_S = 1800.0 at :70): a turn whose agent call hangs keeps its daemon thread alive (launched :761-771, no timeout/join) but STOPS counting toward `HERMES_GPT_UI_MAX_CONCURRENT` (default 4, env at :64, gate checked at :743-744) — repeated hangs grow threads unbounded while the gate reports spare capacity. ui_chat.py:187-192 `_prune_turns` removes ONLY done turns, so not-done turns are never reaped, bounded solely by the session-keyed overwrite (:161) while each Turn holds up to TURN_EVENT_RING_MAX = 4096 ring events (:74). `_run_turn` (:568-599) handles Exception/ImportError but a hang never returns, so the finally-block lease release (:596-599) never runs. Distinct from rm-172 (lease renewal + unguarded Thread.start), rm-200 (lease-acquire atomicity), rm-196 (body caps + SessionDB retention) and rm-205 (shutdown window) — none owns the steady-state gate/reap/watchdog truth of the in-memory turn registry.
- acceptance: (a) the concurrency gate counts every live (not-done) turn regardless of age, or hung turns are reaped so count and reality agree — regression test: turns older than TURN_RETENTION_S that are still not-done keep the gate refusing (429) at max concurrent; (b) provably abandoned not-done turns (thread finished without done=True, or watchdog timeout) are reaped with a terminal SSE event so clients see failure instead of silence; (c) an explicit configurable watchdog bound on the agent-call leg of `_run_turn` converts a hang into a failed turn (lease released via the existing finally); (d) full suite green plus the new tests; no weakening of the 429 gate, lease semantics, or the bounded-replay invariant.
- evidence: line reads at base 0670f4cfc2 (ui_chat.py:64,:70,:74,:161,:181-192,:743-744,:761-771,:568-599); this run's full-suite log /tmp/854045a2-assess/pytest-full2.log (baseline for the new tests); implement must re-verify anchors after rebasing >= e490130737 — sibling run-b66594102002 has ui_chat.py live-dirty (turn-lease +83) in this cycle, coordinate at the landing gate.

### Cycle 2 refresh notes (no new ids; fold map + evidence refreshes for the landing gate)
- fold map for this run's assess (854045a2, F1-F6 + K1-K3, /tmp/854045a2-assess/findings.md; all anchors read at base 0670f4cfc2): F1 fixed-name `.tmp` staging + no fsync in operator_runners.py:79-91 (`_atomic_json` :85; callers :738/:753/:788/:854/:1497 — worker watcher loop AND request-thread cancel path can write the same meta file), operator_session.py:63-69 (:67), operator_codex.py:54-60 + :89-95 -> **rm-067** (its recorded fixed-.tmp slice names exactly these modules; the 2026-09-30 compound note claims run-e13b1c0d37ea implement 7446017d landed the slice via operator_workspace._atomic_write_bytes, but all three modules still stage through fixed `.with_suffix('.tmp')` AT THIS BASE — the landing gate must verify that patch actually lands or re-open the sites; canonical in-repo contrast: operator_autopilot.py:193-210 / operator_job_supervisor.py:71-77 pid+nonce+fsync). F5 operator_controller.py:2229-2238 heartbeat direct `write_text` (no tmp/replace/fsync; `_read_heartbeat` already fail-safe on decode error) -> **rm-067** acceptance extension (NEW site for its enumerated list). F3 strict-redactor false positives, live-proven at HEAD ("Payment of 1234.5678 USD due 2026-10-03" -> "[redacted-phone]" twice; "Version 2.13.1 of httpx shipped 2026-09-24" -> date eaten; "The Mission Control Panel shows GREEN" -> "[redacted-name] [redacted-name]") from ui_security.py:207 (any >=8-char dotted/dashed digit run eats money and bare dates) + :216 (bare TitleCase pair) -> **rm-174** acceptance extension: the item's scope is the whole redaction-correctness class (decimal money, bare dates, TitleCase pairs), not only ISO timestamps; NOTE sibling 61db9bce/efe owns the rm-170/174 implement with ui_security.py live-dirty this cycle — coordinate. F4 no request-body size caps anywhere (rg Content-Length|MAX_BODY|body_size -> no body-cap middleware; ui_chat.py:717 `await request.json()` and the oauth/UI JSON routes buffer unbounded bodies) -> **rm-196** (e618b73f8389 title "UI chat ingress bounds + SessionDB retention", acceptance arm (a) IS the body cap; extension: cover EVERY request.json() site including the oauth_auth UI routes, not only /api/chat). F6 ruff pin `>=0.15,<0.16` (pyproject.toml:36/:53) vs latest 0.16.10, plus NO [tool.ruff] section anywhere in the repo -> **rm-035** (1bc41b1b already extended the pin bump; new arm: declare an explicit [tool.ruff] selection so lint scope is explicit, not implicit). K1 finance request_id charset gap (operator_finance.py:144-150 length-only validation; finance_worker.py:92-93 interpolation) -> **rm-144** (implemented pending the landing gate; fix absent at this 3-behind base — rebase, do NOT reimplement). K2 `is_loopback_host("::ffff:127.0.0.1")` -> False (server.py:122-123, live-proven) plus zero Sec-Fetch-Site/Origin enforcement repo-wide -> **rm-170** (already strengthened to P1 by e618's assess; this adds the IPv4-mapped-IPv6 miss re-proof). K3 operator_skill_resolution.py:159-160 process-global sys.path insert never restored -> **rm-193** (74896be4b661 resolved the upstream-first park and minted it fork-first; still present at this base — re-verify at implement, no new id).
- research evidence-refresh folds (attempt 1b2d18ef, full detail /tmp/1b2d18ef-scratch/research-candidates.md section 3; all external queries 12:06-12:20Z; no new ids): **rm-048** — MCP 2026-07-28 revision went STABLE (2026-07-28T16:47:49Z; prior stable 2025-11-25): sessions/Mcp-Session-Id removed from Streamable HTTP; `initialize` handshake removed (SEP-2575 per-request `_meta` versioning); `server/discover` is a MUST-implement RPC; HTTP GET + `resources/subscribe`/`unsubscribe` replaced by the `subscriptions/listen` opt-in stream; `ping`/`logging/setLevel`/`notifications/roots/list_changed` removed; SDK 2.3.0 (10-02) speaks BOTH revisions so the 2.3.x CI lane can actually exercise 2026-07-28; `x-mcp-header` with an invalid signature now fails at registration (was a silent drop). **rm-014** subscriptions/listen — the alignment target is now spec-frozen STABLE text (deferral gate unchanged: still no push consumer). **CIMD strategic study item** — the 2026-07-28 authorization section deprecates RFC 7591 Dynamic Client Registration in favor of Client ID Metadata Discovery: the study is now an adoption-track question with spec momentum behind one answer. **SEP-414 trace-context item** — mcp 2.3.0 hard-requires opentelemetry-api>=1.28.0, so the OTel API is already in-tree on the 2.3 lane (cost drop); in-repo seed finance_worker.py:88-96 hand-rolled request_id. **SSE parser hardening item** — SDK 2.3.0 ships a native `max_sse_event_size` (needs httpx2>=2.10): prefer the SDK-native bound where the stream is SDK-mediated. **rm-180/rm-173 floors/watch** — OSV re-run 12:15Z: starlette==0.40 -> 14 advisories, cryptography==42 -> 15, anyio==4.0 -> 4 (PYSEC-2026-4024/4025), all other pins clean; mcp 2.3.0's tree pulls httpx2>=2.10 + pydantic>=2.12 + opentelemetry-api — the floor/watch surface must include that new transitive set when the 2.3 lane lands. **rm-100/rm-169 Python lanes** — 3.10 EOL PASSED 2026-10-01 (3.11 -> 2027-10-31, latest 3.14.8); mcp 2.3.0 requires starlette>=0.48 only on py>=3.14 (pin interaction to check on the 3.14 lane). **rm-135/rm-148/rm-173/rm-162 agent-loader pin** — hermes-agent HEAD moved AGAIN c8301ea6c9 (09:25Z) -> 1cb26bf24 (11:53:14Z); deployed clone b8a0339ae9 now 3+ days behind: unpinned-loader drift demonstrated at 2.5-hour cadence — strengthens pin-over-record. **rm-083/rm-077/rm-184 release truth** — upstream still has NO v0.13.0 tag/release (content merged, no tag); only PR #85 (file backups, 240223e04) open, patch-less; PyPI 0.12.0 vs repo 0.13.0 unchanged.
- suite truth at this base (attempt 854045a2, /tmp/854045a2-assess/pytest-full2.log): `python -m pytest -q -n 8` -> 1848 outcomes, exactly 1 failure = test_operator_autopilot_status.py::test_building_the_summary_writes_nothing — STALE BASE, fixed at master by PR #28 ("test(autopilot): make the status zero-write snapshot checkpoint-invariant"); do not reopen.
- base-currency + rebase warning: this worktree's base 0670f4cfc2 sits on merge-base 30de0067f9 and is 3 behind e490130737 on the graph (= origin/master minus PRs #27+#28; the local Stage4 commit 0670f4cfc2 carries #26's plan-artifact content as a divergent SHA, so the rebase replaces it with #26's merged commit); #27 fixed the 3.10 asyncio.TimeoutError class and #28 the autopilot status test — implement phases MUST rebase >= e490130737 before landing rm-205/rm-206 or touching ui_chat/server anchors; #26's artifacts_present default keeps the rm-185 contamination lane active at this base.

<!-- managed by hermes-roadmap render; do not edit by hand -->
