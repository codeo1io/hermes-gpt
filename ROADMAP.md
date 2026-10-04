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

<!-- cycle-2 additions (run a0f8eb89b52541ad83abf99dc18f6c89, roadmap attempt 1bc41b1bf1424d57950fd6c6291f741e, repository-maintenance:bc96820eb522487fbce7c21f8d8dab57:cycle:2, 2026-10-03 ~11:52Z; insert-only, render footer stays last). MINTED rm-204 ONLY (research cfd58ae4 candidate M1 — the phase's single mint-ready survivor; every other candidate was rejected/deferred with reasons in /tmp/cfd58ae4-research/research-candidates.md §3). FLEET CENSUS at mint 11:52Z (fresh, artifact /tmp/1bc41b1b-scratch/census.txt; supersedes nothing — agrees with 3f9c3f49's 11:49Z census): frontier = rm-203 (minted 11:42:48Z by run-af71b550d158 = attempt a5bcf00e, patch /tmp/a5bcf00e-scratch/ROADMAP.ledger.patch); NO rm-204 entry exists anywhere (worktrees, campaign ledgers, /tmp patches — 'rm-204' strings elsewhere are 'next free' notes); rm-196/rm-197 double-minted (1bbd1dda vs c819e771/422bd614) with DISTINCT titles — all four survive; rm-193 contested by title (74896be4b661 on-disk vs 3f4f12b8 renumber plan); rm-194 RESERVED renumber target; 3f9c3f49 (11:50Z) was a 5d7b82aa re-verify retry, NO new mint; NEXT FREE after this mint = rm-205. Cross-repo rm- prefixes (agenttrace rm-195..238, stonks rm-001..051, dashboard rm-13xxx) are NOT hermes-gpt census members. Standing gates: implement MUST rebase >= e490130737 (this worktree base 30de0067f9 is 3 behind = PRs #26/#27/#28); ledger landing applies in mint order 79b3e882 -> 03ec00ae -> ca49ab4b/c34d91cd -> 92395980 -> 74896be4b661 -> 3f4f12b8 -> 1bbd1dda -> c819e771/422bd614 -> 5d7b82aa -> a5bcf00e -> THIS PATCH, title-collisions lowest-id-wins.

FIXED-AT-MASTER CORRECTIONS (do NOT reopen as new items; assess ran at base 30de0067f9 which predates them): assess finding 'operator_live_events.py:403 bare except TimeoutError (3.10 WS death, master CI 3.10 lanes red — run 37096484558)' is FIXED at origin/master e490130737 by PR #27 (58a70ddd5e: catches asyncio.TimeoutError) — rebase-only, rm-169/151 lane. Upstream merge mission truth (research cfd58ae4 §2, decisive): git merge-base e490130737 2e18846902 = 2e18846902 -> upstream-not-in-fork = 0, the upstream merge is ALREADY SATISFIED at e490130737; fork-not-in-upstream = 137 commits / 328 files -> do NOT retire the fork branch; the campaign ROADMAP 'Conflicted paths' list is a cycle-1 preflight artifact (2026-10-01) and is stale — merge input is empty at current tips; implement must re-fetch both remotes and re-derive conflicts only if upstream moves again.

FOLD MAP for assess 3f25cb8d's 19 findings (all folded, detail /tmp/cfd58ae4-research/research-candidates.md §4 + /tmp/3f25cb8d-assess/findings.json; suite re-proven green at base: 1798 collected RC=0, 3 skips): live-events TimeoutError -> FIXED-at-master (above); transport boundary server.py:3234 -> rm-170; ui_chat.py:747 lease no-renewal + unguarded Thread.start -> rm-172; hermes_state.py:279-303 lease-acquire TOCTOU -> rm-172 (acceptance extension: 3 autocommit statements DELETE/SELECT/UPSERT, not one transaction — cross-process double-acquire); oauth wildcard :1434 -> rm-164 + rm-201; fleet GET bound-after-read operator_fleet.py:221-227 -> rm-183 (acceptance extension: resp.read() loads FULL body BEFORE the _MAX_REMOTE_BYTES check — the cap bounds nothing; fix is chunked read at both GET and POST sites); fleet POST unbounded :246-248 -> rm-183; cron lock-less jobs.json :425 -> rm-171 (+rm-103); phone regex ui_security.py:207 -> rm-174; autopilot log_path DEVNULL :523-535 -> rm-166 (+rm-186 twin); fleet card 0.20.5 server.py:3075/:3117 -> rm-184 (acceptance extension: SECOND stale literal "version": "0.8" at operator_fabric.py:2815 — fix both); README hero absent from sdist (MANIFEST ships no assets AND tools/check_package_hygiene.py:94 blocklists .jpg — shipped README:6 points at an unshippable path) -> rm-077 (+rm-083); ROADMAP render drift -> rm-163/rm-175; tool_end hardcodes ok ui_chat.py:493 -> rm-177; test_verify.py Windows C:\ paths -> rm-161 (+rm-184); .conductor 210 tracked files -> rm-168; no [tool.ruff] -> rm-035 (extension: ruff dev pin >=0.15,<0.16 must bump to adopt 0.16.x); dead reconnectStream chat.ts:47 -> rm-178 (+rm-143); PyPI 0.12.0 vs repo 0.13.0 -> rm-083/rm-052 + rm-133 (upstream has NO v0.13.0 tag/release despite merged content — re-check upstream tag before publishing anything). VERIFIED-CLEAN NEGATIVE RESULTS (scope later phases AWAY): updater.py, operator_export.py, oauth replay-safety (single-use codes + atomic durable rotation), swarm caps + contract fail-closed invariants, finance_worker.py, site/app.js (no XSS), autopilot per-mission file locks, conftest env sandboxing, .conductor contributes 0 pytest tests. -->

### A2A peer transport adopt-vs-build: evaluate a2a-sdk 1.2.x against the four hand-rolled peer surfaces
- id: `rm-204` | track: feature (interop) | priority: 72.0 | status: candidate
- acceptance: written adopt-vs-build design note (rm-072/rm-147 precedent) mapping each of the four hand-rolled A2A surfaces — fabric client `operator_fabric.py:670-690`, fabric agent-card server `operator_fabric.py:2790-2840`, fleet peer client `operator_fleet.py:221-248`, server card `server.py:3072-3134` — to a2a-sdk 1.2.1 client/server-card coverage with an adopt / pin-and-conform / stay-hand-rolled decision recorded in the ledger (and CHANGELOG if deps change). If staying hand-rolled: the rm-177/S4 conformance test (card schema + content-type, `application/a2a+json` per rm-203) becomes the standing guard and this item closes as "decision: stay" with rationale. If adopting: dependency addition follows the rm-099 direct-dep rule; NO weakening of rm-153 bounded-read guarantees (SDK responses wrapped or configured bounded); loopback/read-only invariants preserved; targeted tests for card GET + JSON-RPC POST at both fabric and fleet sites.
- evidence: run a0f8eb89b52541ad83abf99dc18f6c89 research attempt cfd58ae4 candidate M1 (2026-10-03 ~10:05-10:30Z, every channel queried live; artifacts /tmp/cfd58ae4-research/research-candidates.md + base-commit.txt). Signals: zero `a2a` dependency in pyproject.toml (grep = 0) while spec-conformance drift concentrates exactly in the hand-rolled spots — `protocolVersion: "1.0"` literals x5 (operator_fabric.py:2812,:2832; server.py:3072,:3092,:3114) vs published spec v1.0.1 (2026-05-28); plain `application/json` Accept/Content-Type + custom `A2A-Version: 1.0` header (operator_fabric.py:677,:679) vs the v1.0.1 HTTP binding preference for `application/a2a+json`; custom `supportedInterfaces` dialect `{url, protocolBinding, protocolVersion}` (operator_fabric.py:2828-2833) not in the published card schema; stale version literals "0.8" (operator_fabric.py:2815) and "0.20.5" (server.py:3075). Ecosystem: a2a-sdk 1.2.1 (2026-09-30; three releases in ten days; requires_python>=3.10) + official a2a-cli 0.2 on PyPI (announced 2026-10-02) — the maintained-alternative signal. Dedupe (why a new id): rm-153 (body bounds), rm-177 (status/audit truth + S4 conformance), rm-183 (read caps), rm-184 (version literals), rm-203 (content-type binding) each patch symptoms of the hand-roll; none owns the adoption decision — M1 is the umbrella lever that would shrink that surface. Landing note: independent of the upstream-merge resolution; rebase >= e490130737 first.

<!-- managed by hermes-roadmap render; do not edit by hand -->
