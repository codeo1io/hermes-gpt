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

<!-- cycle-3 additions (run dfaf334f988c494e8d0df40d18aa57c3, roadmap attempt 3f4f12b86e5e49cead4fe9af72a54e5d, family repository-maintenance:d7b00779f41d4218a24c577e8ecc8034:cycle:3; canonical refresh in campaigns/hermes-gpt-fix-pr63-pkce-test-fixtures-80cce15da948f8b2/ROADMAP.md). Fleet census 2026-10-03 ~10:20Z: materialized max rm-192 (e1e8d7ec on-disk rm-180..188; c34d91cd v2 patch rm-189/190/191; 92395980 campaign-file rm-192). LIVE COLLISIONS for the gate, merge-by-title lowest-mint wins: rm-180/181 (e1e8d7ec vs df059aaeda57 patch — renumber dfaf334f-adjacent df059 pair to rm-193/rm-194; its "rm-192+" target in c34d91cd's note is stale, 192 is taken); rm-191 (ca49ab4b 08:49Z Swarm co-ownership vs c34d91cd 09:57Z packaging-truth — later mint renumbers); rm-185..188 settled e1e8d7ec by on-disk-wins (c34d91cd v1 dups dropped). Pending: cedce0cffda9 M1 sys.path hygiene mint-ready >= rm-193 (park RESOLVED fork-first — upstream #74 closed, insert byte-identical upstream:159-160, zero upstream issues; supersedes c34d91cd digest's "parked" note). THIS MINT: rm-195 only (skips contested 193/194); next free after = rm-196. Fold map for this run's research S1-S7: S1 UI trust middleware -> rm-170 (f65169a1 B1; feed probe /tmp/3a1048c1-assess/probe_csrf.py + starlette GHSA-86qp-5c8j-p5mr Host-validation class + Vite/Django Host-allowlist norms; server.py:3295 has CORS, no TrustedHost). S2 operator file-backup opt-out -> rm-192 EXISTS (92395980, gated by rm-147; fresh: upstream PR #85 sole open upstream item, 4 files +47/-0, default-preserving). S3 mcp 2.3.x -> rm-048 (7 behavior changes; registration-time x-mcp-header failure = startup risk; max_sse_event_size needs httpx2>=2.10; mcp 2.3.0 transitive floors starlette>=0.48@py3.14 / anyio>=4.9 / pydantic>=2.12). S4 floors -> amend rm-180 + rm-173 at merge: anyio>=4 admits 2 OSV findings fixed 4.14.2 (GAP not in rm-180); starlette full-clear 1.3.1 (0.47.2 leaves 1.0.1/1.1.0/1.3.0/1.3.1 classes open); cryptography>=50 confirmed (49 still open); mcp 1.28.1 / uvicorn 0.30.0 clean. S5 -> cedce0cffda9 M1 (do not mint here; probes at /tmp/3a1048c1-assess/ are its regression tests). S6 UI-scoped session store -> rm-136 (ui_chat.py:214-221 writes the agent's live state.db) + start_flow foreign-turn exfil -> rm-119. S7 -> rm-195 below. Evidence refreshes: rm-038 protection still 404; rm-077/083/052 PyPI 0.12.0 vs repo 0.13.0 (518 dl/mo); rm-184/177 a2a-sdk 1.2.1 vs '0.20.5'; rm-185 contamination ACTIVATED at master (#26); rm-162 hermes-agent HEAD eb7e8620324b vs ci.yml:123-135 unpinned; rm-035 ruff 0.16.10 available, dev floor still <0.16; actions/checkout v7.0.1 + setup-python v7.0.0. Implement MUST rebase >= e490130737 (this tree 7 behind / 0 ahead; base caf60018d2); #27 fixed the 3.10 asyncio.TimeoutError class and #26 the plan-artifact-drop class — do NOT reimplement; #28 status-zero-write landed. Landing gate owns status flips; render footer stays last. -->

### Roadmap ledger integrity: restore the 38 render-collapsed ids and guard id monotonicity
- id: `rm-195` | track: reliability | priority: 55.0 | status: candidate
- signals: run dfaf334f988c assess F3 + research S7 (2026-10-03 @ 6be3a5e95b) — commit 6be3a5e95b, an ANCESTOR of origin/master e490130737 (the collapse landed canonically), replaced the 1061-line ROADMAP.md with a 329-line managed render dropping 38 rm- ids (id-set comm: 38 lost, 0 added) and flattening surviving blocks to one-liners (signals/acceptance/evidence fields lost); the footer still says "do not edit by hand" while rm-139 retires the render engine as DEAD, so nothing re-renders the lost content back; every tree forked after 6be3a5e95b (including this one) sees a truncated rm-140 frontier against the true fleet frontier rm-192, inviting low-id collisions. Pre-collapse content recoverable verbatim from `git show 6be3a5e95b^:ROADMAP.md`. No sibling fold map covers this loss (checked c34d91cd v2 digest, 92395980 marker, cedce0cffda9 research, 03ec00ae/ca49ab4b patches).
- acceptance: (a) the 38 dropped ids restored on a post-e490130737 base — verbatim blocks from 6be3a5e95b^ with statuses reconciled to fleet knowledge and every status change annotated with reason+date (preserve completed history); (b) a monotonicity guard riding rm-139's tooling asserts id-set(HEAD ROADMAP.md) is a superset of id-set(origin/master ROADMAP.md), failing on any id removal unless the same change carries an explicit renumber marker; (c) proof the guard fails on a synthetic id-removal of the 6be3a5e95b shape; (d) full test suite green after the restore.
- evidence: restored-ROADMAP diff vs origin/master with id-set comm proof (+38/-0), guard tool + failing-mode output, `git show 6be3a5e95b --stat` (-964 lines), suite log. HAZARD: never run `python -m build` concurrently with pytest (rm-188 class).
- update 2026-10-03: IMPLEMENTED this cycle (run dfaf334f988c implement daf86d8f, pre-review/uncommitted). Restore completed at 60 blocks, not 38 — the guard's definition-based comparison found 22 additional blocks the render flattened to title-only one-liners (10 open-class + 12 closed-class); the ledger's defined-id set is now a superset of every ancestor version. tools/check_roadmap_ids.py + 11 focused tests landed (failing-mode proof vs synthetic collapse included); guard green vs origin/master AND 6be3a5e95b^; `roadmap-guard` CI job added adjacent to the package job.

## Restored items — render-collapse recovery (2026-10-03, run dfaf334f988c)

Commit 6be3a5e95b replaced this ledger with a managed render that dropped ledger truth
entirely. rm-195 restores it below, verbatim from the last ledger version in which each
block existed — 60 blocks total: 38 ids dropped without a trace (no mention left), plus 22
ids whose defining blocks the render flattened away while keeping a title-only one-liner
(counts refined at implementation by tools/check_roadmap_ids.py's definition-based
comparison; statuses are AS-OF each source snapshot). The landing gate owns status flips;
where the fleet has since re-derived the same defect under a newer id, the gate renumbers
or folds by title. Sources: `6be3a5e95b^` (pre-collapse snapshot, 44 blocks) and git
history (16 blocks, recovered from the last commit whose ledger still defined them; source
noted per item). With this section the ledger's defined-id set is a superset of every
ancestor version. tools/check_roadmap_ids.py (this cycle) now fails any future id removal
that is not explicitly marked, and a `roadmap-guard` CI job runs it against origin/master.

### POSIX audit-log home, failure surfacing, and bounded retention
- id: `rm-004` | track: reliability | priority: 95.0 | status: implemented
- signals: conductor.run-a51c0f6c:assess-F2+F5, operator_policy.py:46-47,772-783 (Windows-only default, POSIX falls back to package dir; HERMES_HOME ignored), operator_policy.py:874-878 (OSError swallowed -> silent audit loss), operator_policy.py:880-903 + operator_diagnostics.py:1305 + operator_fabric_view.py:523 (full-file parse, no rotation), docs/operator-mode.md:435 documents Windows path only
- acceptance: audit_log_path() resolves under HERMES_HOME/logs on POSIX (normalize_hermes_data_root pattern) with tests; audit write failures become visible via an operator diagnostics counter (tool calls still never break); size-capped rotation with a reverse-read bounded tail; docs/operator-mode.md documents the POSIX path
- evidence: cycle-1 implement (2026-09-21): operator_policy.py dynamic candidate paths (HERMES_HOME -> AppData -> ~/.hermes -> package dir), audit_write_diagnostics() + doctor WARN AUDIT_WRITE_FAILURES, 5 MiB single-generation rotation, 512 KiB bounded tail, rotation-spanning task reconciliation; docs/operator-mode.md documents all four levels; 6 new tests green in both local envs; fabric_view surface untouched this cycle (operator_fabric_view.py:523 still full-parse — fold into next rotation work if it reads audit history)

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Session-jobs retention and watcher cleanup hardening
- id: `rm-005` | track: reliability | priority: 60.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F6, operator_session.py:156,193 (only failure paths unlink), session-jobs/*.json|txt grow unboundedly, hermes_session_job_status _reconcile (operator_session.py:278-294) full-globs the dir per call, _watch (operator_session.py:211-228) skips _processes/_active_sessions cleanup if proc.wait raises a non-timeout error -> permanent SESSION_BUSY
- acceptance: retention policy (age/count cap, documented env knob) prunes session-jobs; _watch cleanup runs in finally for all exception types with a regression test that injects a wait error and asserts the session returns to idle
- evidence: pytest regression test for the injected wait error; a test or docs note proving pruning under volume

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

- id: `rm-006` | track: reliability | priority: 50.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F8, operator_mission_budget.py:96-115 (SQLite REAL columns), :270-296 exact spend >= quota crossings, :62-64 caps 1e12; usd/minutes units accumulate binary-float drift
- acceptance: quota/spend/amount stored as integer micro-units (or Decimal with fixed context) with exact comparisons; migration path for existing ledgers; property test asserting identical crossing decisions across orderings of 10k tiny increments
- evidence: property test passes; existing ledger fixtures round-trip through migration unchanged in decision outcomes

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Root-cause CI-load-only test failures (rotation fencing, delegation reconcile)
- id: `rm-010` | track: reliability | priority: 70.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F4, CI run 35480822047: test_codex_pr63_remediation.py:1208 test_rotation_and_issuance_are_serialized failed on mcp==2.0.0 lane ("issued token unreadable after concurrent rotation") and test_operator_delegations.py:243 test_mission_completion_rejects_concurrent_reconcile_authority_change[reconcile] IndexError on 3.10 lane; both pass locally on rerun
- acceptance: both tests pass across 10 consecutive CI runs (or under pytest -n 8 load locally); root cause documented (real race fixed, or flaky assertion hardened) — blanket retries/skips do not close this item
- evidence: gh run list showing 10 consecutive green master runs post-fix; a written root-cause note in the PR description or docs

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Configurable audit retention with rotation-loss visibility
- id: `rm-015` | track: reliability | priority: 55.0 | status: candidate
- signals: conductor.run-a51c0f6c:review-F2, operator_policy.py:55,843,1009 — single-generation 5 MiB rotation bounds the evidence window for iter_audit_for_task (feeds fabric forbidden-action signals + task reconciliation via operator_fabric.py:1756); records older than two windows vanish silently (false-negative violation signals, not just lost history); caps hardcoded, no operator knob, no rotation-loss indicator
- acceptance: retention cap configurable via operator setting/env; iter_audit_for_task (or its fabric consumer) emits a reconcile-time warning when the archive boundary falls inside a task's lifetime; doctor surfaces rotation-loss state
- evidence: tests covering configurable cap + boundary warning; fabric signal collection proven unchanged when history fits the window

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Bind all runtime_roots on the macOS confinement path
- id: `rm-058` (orig `rm-051` in run-43fe028246d3 numbering; renumbered at the same integration — landed-first `rm-051` is run-edd9fb12b6a4's repo-wide compile-check item) | track: correctness | priority: 26.0 | status: candidate (run-9e0b97f5d86c `rm-039` folds here at this landing, conflict case 1f53f9e34aa1 — its unique env-shebang hardening rider, `env -S` + trailing-flag parsing on the confinement path, joins this item's acceptance)
- signals: conductor.run-43fe0282:assess-F7, runner_confinement.py:354 — the macOS branch passes only runtime_roots[0] to the helper while Linux binds every root, so the env-shebang interpreter root is dropped on Darwin and the exec-127 fix is Linux-effective only
- acceptance: macOS binds the full runtime_roots list (or a comment documents why one root suffices on Darwin) with a unit test covering multi-root env-shebang resolution
- evidence: unit test green; platform-parity comment in code

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Speak RFC 9207 `iss` in authorization responses (SEP-2468, Final)
- id: `rm-059` (orig `rm-052` in run-43fe028246d3 numbering; renumbered at the same integration — landed-first `rm-052` is run-c1ef27c97ab2's PyPI/repo version drift guard item) | track: compatibility | priority: 66.0 | status: implemented (run 43fe028246d3 cycle 3, 2026-09-23; landed 2026-09-24 at integration b1b99c1422b848a3b738bb5ccaf9107e; plus run-0c8974179349 `rm-035` slice 1 folded here 2026-09-26 at integration 8b2887a65e2f45ffaee16b995cbc37a0 — this merge keeps the candidate's error-response iss tests; its slice 2, the Client ID Metadata Documents design note, folds into the deferred CIMD rm-053 in the run-9e0b97f5d86c block)
- signals: conductor.run-43fe0282:research-R1, SEP-2468 (Status: Final, standards track): MCP authorization servers SHOULD include iss in authorization responses INCLUDING error responses (per RFC 9207) and MUST advertise authorization_response_iss_parameter_supported in AS metadata; oauth_auth.py:1300-1313 redirects carry code/error+state but never iss; the AS metadata block (:1197-1213) lacks the flag
- acceptance: authorize success and error redirects include iss=<issuer>; AS metadata advertises authorization_response_iss_parameter_supported: true; tests pin both; docs note added
- evidence: pytest asserting iss in both redirect classes + the metadata flag; cheapest win while oauth_auth.py is open for rm-055/rm-056

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Merge the stranded fork PRs #19/#20 onto the converged master
- id: `rm-060` (orig `rm-032` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: reliability | priority: 110.0 | status: implemented (run 9e0b97f5d86c cycle 1, 2026-09-23; landed 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1; PRs #19+#20 adopted by content; plus run e29c25913c00 `rm-043` folded here 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0 — the rebase work is fully superseded (PR #20's content landed via its branch, PR #19's content landed at 8aa9ed17), leaving only the truthful-bodies remainder, which rides rm-033 above)
- signals: conductor.run-9e0b97f5:research-R2 — gh pr list codeo1io: #19 (packaging consolidation; same content as upstream PR #75) and #20 (canonical profile-aware skill resolution, operator_skill_resolution.py; the fork half of upstream issue #74) both open with all-green check rollups at open time but mergeable=CONFLICTING/DIRTY vs the converged master; master lacks operator_skill_resolution.py entirely and still tracks requirements.txt + requirements-dev.txt
- acceptance: both PRs rebased with conflicts resolved against master (a93aeb0b1d or later); packaging resolution keeps the converged pyproject + croniter>=2.0,<7 while adopting the manifest deletion + pyyaml>=6.0.3,<7 floor; skill resolution resolution reviewed against placement-ranking tests; full suite green in CI shape post-rebase; #19 merged = CVE floor landed; #20 merged = operator_skill_resolution.py on master; upstream PR #75 head refreshed from the landed state (stewardship)
- evidence: merged PR links; git log on master showing both commits; `ls operator_skill_resolution.py`; pyproject pyyaml line; green CI run on master post-merge

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Dead double-raise in _authenticate_client (merge artifact)
- id: `rm-061` (orig `rm-036` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: maintainability | priority: 30.0 | status: implemented (run 9e0b97f5d86c cycle 1, 2026-09-23; landed 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1)
- signals: conductor.run-9e0b97f5:assess-F3 — oauth_auth.py:1412-1413 two identical consecutive `raise OAuthError("invalid_client", ...)`; second is unreachable; verified verbatim at origin/master tip a93aeb0b1d
- acceptance: one raise deleted; zero behavior change; targeted oauth tests green
- evidence: one-line diff; targeted test run

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Unify the two gateway.pid parsers
- id: `rm-062` (orig `rm-037` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: maintainability | priority: 40.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F5 — operator_diagnostics.py:291 requires isinstance(state_pid, int); operator_workspace.py:150-160 docstring says 'Accept int or numeric string'; mission gateway probes route through the strict copy (operator_mission.py:651) — a string-pid gateway reports not-running in mission while workspace reports running (rm-022 drift class)
- acceptance: one shared reader with a documented pid contract; both call sites consume it; parametrized tests cover int and numeric-string forms for both consumers
- evidence: dedupe diff; new parametrized test green

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### publish.yml runner migration + stale CI comments
- id: `rm-063` (orig `rm-038` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: reliability | priority: 45.0 | status: candidate (2026-09-26 fold, integration 7fd1ba641af2, conflict case 536598c0: run e29c25913c00's same-topic `rm-042` (publish.yml off self-hosted) folds here — its findings that publish.yml:14 still declared self-hosted at its HEAD 4b958379d6 and that test_windows_quotes.sh:41/47 stall on that runner's absence corroborate this item's acceptance; the runner-decision slice remains rm-069)
- signals: conductor.run-9e0b97f5:assess-F6 — publish.yml:14 still runs-on: self-hosted although PR #21 moved CI to GitHub-hosted runners; ci.yml:33/:142 comments still describe the retired self-hosted serial runner — next tag push queues the publish job on infrastructure that no longer exists
- acceptance: publish job moved to ubuntu-latest with the pypi environment + id-token trusted-publishing path verified, OR self-hosting explicitly re-affirmed with recorded rationale; stale comments refreshed; a workflow_dispatch/dry-run validation path documented
- evidence: workflow diffs; validation run or dispatch evidence
- update 2026-10-01 (run bf4db34f:assess-F3, spool debf6abb): sharpened against HEAD 941f4cfc69 — rm-096's dedicated-limiter fix landed for the mission-events long-poll ONLY (ui_missions.py:35 `_MISSION_EVENTS_LIMITER = anyio.CapacityLimiter(...)`, used at :134), while hermes_job_wait still rides the shared default executor via asyncio.to_thread (server.py:2325-2333) with a 120s busy-poll hold (MAX_WAIT_SECONDS=120 at operator_job_supervisor.py:28, time.sleep(0.1) loop :733-751 — ~10 status-file reads/sec for up to 120s, ~5x the hold time of the site rm-096 fixed); the occupancy-bound acceptance stands, unimplemented at this HEAD

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### hermes_job_wait occupancy bound on the shared loop executor
- id: `rm-064` (orig `rm-040` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: reliability | priority: 25.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F10 — operator_job_supervisor.py:28 MAX_WAIT_SECONDS=120; six long-blocking tools now park on the loop's default executor (asyncio.to_thread; capacity min(32, cpu+4)) with no per-tool bound; concurrent long-parks can starve owner_run_command/codex_start; test_server_nonblocking.py pins only 2 of the 6
- acceptance: either a recorded occupancy rationale or a semaphore/bound on concurrent job_wait parks; the nonblocking pin test extended to the full offloaded set
- evidence: diff + extended tests green

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### SEP-2322 multi-round-trip: capability study, then InputRequired approval handshake
- id: `rm-066` (orig `rm-042` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: compatibility | priority: 50.0 | status: candidate (design-gated)
- signals: conductor.run-9e0b97f5:research-R5 — installed mcp 2.2.0 ships SEP-2322 (client driver mcp/client/_input_required.py, DEFAULT_INPUT_REQUIRED_MAX_ROUNDS=10; server handling mcp/server/mcpserver/tools/base.py:93/:170/:181; types in the new top-level mcp_types package); the repo implements and documents none of it (zero grep hits; docs/mcp-compatibility.md stops at the 2026-07-28 stateless note); natural use: interactive human approval for direct operator mutations (dry-run → InputRequired confirm), which must degrade cleanly on the mcp 1.28.1 lane via mcp_compat.HermesMCP
- acceptance: study recorded (wire shape, SDK-2-only constraints, 1.28.1 degradation matrix, client-support reality); if adopted: one operator mutation tool returns InputRequiredResult with a dual-SDK test proving graceful refusal on 1.x; docs/mcp-compatibility.md gains a SEP-2322 section
- evidence: study notes or implementation diff + tests; compat doc diff

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Atomic-write collision hardening + operator tmpdir lifecycle
- id: `rm-067` (orig `rm-039` in run-0c8974179349 numbering; renumbered 2026-09-26 at integration 8b2887a65e2f45ffaee16b995cbc37a0, conflict case 6c00d3b538854a7f8261890e4198eb0e) | track: reliability | priority: 34.0 | status: implemented (partial — the two named sites landed 2026-09-26 with that integration: operator_workspace._atomic_write_text + operator_cron._write_jobs now write unique-tmp + fsync-before-replace, plus the 7-day best-effort tmpdir janitor; remainder open: env-mutation thread-safety, the Windows path, and 12 further fixed-.tmp sites across operator_swarm/config/codex/session/token_store/codex_config/operator_runners; run e29c25913c00 `rm-045` (scope the operator-tmpdir env mutation to the subprocess instead of exporting it) folded here 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0 — it is precisely this item's env-mutation thread-safety remainder)
- signals: conductor.run-0c897417:assess-F7/F9, operator_workspace.py:48 _atomic_write_text writes a fixed '<name>.tmp' sibling (same pattern operator_cron.py:157) — concurrent writers to the same target race on the tmp name with no fsync before replace; operator_workspace.py:951 _ensure_operator_tmpdir mutates the global os.environ from a worker thread (tempfile caching inconsistency), skips Windows, and has no janitor — accumulated temp artifacts are never pruned
- acceptance: unique tmp names (mkstemp-style or uuid suffix) + fsync-before-replace at both sites, with a concurrency regression test; tmpdir creation thread-safe without global env mutation (or a documented lock), with an age-cap janitor and a Windows path; tests cover collision + cleanup
- evidence: concurrency regression test green; full serial suite zero-delta; docs note for any new knob (AGENTS.md rule)

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Untrack site/.vercel metadata + dedupe the gateway-pid JSON parser
- id: `rm-068` (orig `rm-040` in run-0c8974179349 numbering; renumbered at the same integration) | track: maintainability | priority: 16.0 | status: implemented (landed 2026-09-26 at integration 8b2887a65e2f45ffaee16b995cbc37a0: untracked+ignored with on-disk copy kept; single canonical pid parser in operator_workspace, diagnostics delegates; deploy re-proof remains a ci-stage concern)
- signals: conductor.run-0c897417:assess-F8/F10, site/.vercel/project.json commits Vercel orgId/projectId while .gitignore covers only the /.vercel/ root dir; two overlapping vercel.json configs (root builds site/** static routes; site/vercel.json sets outputDirectory "."); operator_workspace.py:122 re-implements the gateway-pid JSON parse that operator_diagnostics.py:254-282 already owns
- acceptance: .vercel metadata untracked (gitignore entry) with deploy proven unaffected (or a documented reason it must be tracked); one canonical gateway-pid parser shared by both call sites with tests
- evidence: git diff (untrack + gitignore) and a deploy/build check; grep shows a single parser; suite green

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Decide the publish.yml runner story (self-hosted vs GitHub-hosted)
- id: `rm-069` (orig `rm-037` in run-0c8974179349 numbering; renumbered 2026-09-26 at integration 8b2887a65e2f45ffaee16b995cbc37a0, conflict case 6c00d3b538854a7f8261890e4198eb0e) | track: reliability | priority: 40.0 | status: candidate (decision item — Git topology is Conductor's call)
- signals: conductor.run-0c897417:assess-F5, publish.yml:14 publish job reverted to runs-on: self-hosted by the deployed merge, partially undoing #21's move of CI off the shared self-hosted box; gh api actions/runners shows 2 self-hosted runners online (2026-09-23) so tags resolve today, but PyPI releases single-depend on shared agent-runners whose retirement strands publish
- acceptance: a recorded decision — GitHub-hosted publish with pypa/gh-action-pypi-publish (trusted publishing/OIDC) or self-hosted with a documented reason + redundancy note; publish.yml matches the decision; the next tag push proves the chosen path end-to-end
- evidence: publish.yml diff + decision note in the PR/commit; green publish run on the next tag (or an equivalent dry-run artifact)

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### PR fast lane needs an SDK-1 sentinel lane
- id: `rm-070` (orig `rm-038` in run-0c8974179349 numbering; renumbered at the same integration — that landing's id line dropped the authored track/priority/status fields; restored here) | track: reliability | priority: 46.0 | status: implemented (landed 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0: the PR fast lane now runs both SDK majors — `mcp>=1.28.1,<2` beside the default `mcp>=2,<3` lane on Python 3.11, .github/workflows/ci.yml — carried by run e29c25913c00's ci.yml diff, which satisfies this item's first acceptance branch; the alternative branch (drop SDK-1 and narrow pyproject) is not taken; that run's same-topic `rm-036` is folded into this landing)
- signals: conductor.run-0c897417:assess-F4, .github/workflows/ci.yml:39 PR fast lane is single-lane (3.11 + mcp>=2,<3) while SDK-1/3.10/3.12 lanes run on push only; pyproject still admits mcp>=1.28.1,<3, so a regression that only breaks the mcp 1.x family (e.g. the anyio.run vs to_thread sync-tool offload split between SDK 1.28.1 and 2.x) merges undetected
- acceptance: the PR fast lane gains a cheap mcp==1.30.0 lane, OR a recorded decision drops SDK-1 support and narrows pyproject to >=2,<3 with a CHANGELOG entry; PRs cannot merge with an untested SDK family either way
- evidence: ci.yml diff; a PR run showing both families green (or the pyproject narrowing + rationale)

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Structured tool output pilot (outputSchema/structuredContent)
- id: `rm-071` (orig `rm-041` in run-0c8974179349 numbering; renumbered at the same integration; its interlock — PR #20's branch rm-032, "MCP 2026-07-28 minor-spec adoption" — is landed rm-048 after that branch was adopted-by-content at the run-9e0b97f5d86c landing) | track: compatibility | priority: 30.0 | status: candidate
- signals: conductor.run-0c897417:research-R3, MCP spec 2026-07-28 tools.mdx:299,:498-505 defines outputSchema + structuredContent (changelog minor #10 loosened schemas to JSON Schema 2020-12 / any JSON value); grep at HEAD: zero structuredContent/outputSchema usage in server.py/mcp_compat.py; NOTE the unmerged PR #20 branch already defines "MCP 2026-07-28 minor-spec adoption and SDK-3.0 proofing" as ITS rm-032 — this item is the hermes-tool-surface slice of that work, adopt/merge with it rather than duplicating
- acceptance: pilot on 2-3 highest-traffic read-only tools (e.g. hermes_web_extract, one workspace read, session status): declare outputSchema and return structuredContent alongside text per spec pairing rules; SDK 1.30.0 parity verified in plan before committing (or gated to SDK-2 lanes); existing clients degrade gracefully (text result still present)
- evidence: schema tests green on both SDK lanes (or the documented gate); inspector/manual log showing structured output; docs note

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### DPoP (RFC 9449) sender-constrained tokens at the hand-rolled AS — design note first
- id: `rm-072` (orig `rm-042` in run-0c8974179349 numbering; renumbered at the same integration) | track: security | priority: 24.0 | status: candidate (design-gated)
- signals: conductor.run-0c897417:research-R2, MCP python-sdk ROADMAP.md:14 tracks DPoP-bound access tokens (SEP-1932) on the client side as unimplemented; hermes-gpt owns its authorization server (oauth_auth.py) so server-side jkt verification can land ahead of SDK client support and close the loop when the SDK ships; today's bearer tokens are replayable across clients
- acceptance: design note first (binding model, jkt thumbprint validation, clock/nonce window, interaction with the existing token epochs/revocation machinery), then implementation behind an opt-in env gate default-off with tests proving a token bound to one client's key is rejected for another; zero behavior change when off
- evidence: design note in docs/design (marked historical-until-adopted per docs rules); opt-in tests green default-off; full suite zero-delta

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Kill asyncio.run() inside sync tool bodies (SDK-1 lane execution)
- id: `rm-073` (orig `rm-035` in run-e29c25913c00 numbering; renumbered 2026-09-26 at integration 7fd1ba641af24f83bd5ff4f626d0cd82, conflict case 536598c0 — the landed-first `rm-035` belongs to run-6efbf603's block) | track: reliability | priority: 115.0 | status: implemented (landed 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0; run e29c25913c00 implement 33e1d93e, 2026-09-23)
- resolution: both tools converted to `async def` awaiting their already-async helpers directly (acceptance said to_thread; the helpers are coroutine fns, so direct await is the correct shape — no extra hop); zero asyncio.run() left in tool bodies (the remaining ones in `build_codex_mcp_server`'s callbacks are a Codex registry bridge, not a tool body — loop-safe via the rm-074 seam, since both SDK lanes execute those bodies off-loop on worker threads); new test_server_sdk1_execution.py drives enabled paths on a live loop + disabled-gate raises; 5 sync call sites in test_server.py updated to asyncio.run(...)
- signals: conductor.run-e29c2591:assess-F1 + research, server.py (run numbering) hermes_web_extract and hermes_vision_analyze called asyncio.run() inside SYNC tool bodies; mcp 1.28.1 executes sync tools directly on the event loop (fastmcp/utilities/func_metadata.py call_fn_with_arg_validation `return fn(**kwargs)`) while mcp 2.0.0+ offloads via anyio.to_thread.run_sync (proven from installed/wheel sources; repro /tmp/assess-00799971-asyncioproof.py — both tools RAISE "asyncio.run() cannot be called from a running event loop" under a running loop); pyproject mcp>=1.28.1,<3 with CI pinning a 1.28.1 lane; tests previously covered only the DISABLED path, so PR CI could not catch this class
- acceptance: both tools converted to `async def` with blocking work off the serving loop (mirroring the six-tool pattern); zero asyncio.run() left in any tool body; a regression test drives an ENABLED web/vision tool through a running-loop harness (fails pre-fix, passes post-fix)
- evidence: diff + loop-harness test green on the baseline interpreter; `grep -n "asyncio.run" server.py` shows no tool-body hits; full suite in CI shape stays green

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Event-loop safety for remaining long-blocking sync tools
- id: `rm-074` (orig `rm-037` in run-e29c25913c00 numbering; renumbered at the same integration) | track: reliability | priority: 95.0 | status: implemented (landed 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0; run e29c25913c00 implement 33e1d93e)
- resolution: decision recorded — the mcp_compat.py normalization branch: module-level _offload_sync_tool (functools.wraps-preserving coroutine wrapper over anyio.to_thread.run_sync) applied by a class-level HermesMCP.add_tool override gated `if not SDK_V2`, covering all ~153 tools at one seam with zero per-tool churn; SDK-2 lanes inherit FastMCP.add_tool untouched (byte-identical). Responsiveness proven under real mcp 1.28.1 via HermesMCP.call_tool: loop max tick gap 0.051s while a 0.6s sync tool runs (SDK1-PROOF-P4); asyncio.run-in-sync-body also succeeds off-loop (P5). The Codex curated registry's `asyncio.run` bridge callbacks (server.py `build_codex_mcp_server`) depend on this seam for their own loop-safety.
- signals: conductor.run-e29c2591:assess-F2, deployed-line merge 9a90620d5c converted only 6 tools; hermes_bot_chat_send (timeout=900 → hermes_session_continue chain), hermes_run_command (30s), hermes_finance_analyze (120s), hermes_release_doctor (180s), fleet tools (10-15s) still stall the whole server (every session + UI + OAuth) on the SDK-1 lane; ~147 of 153 hermes_* tools remain sync
- acceptance: EITHER convert the listed long-waiters to async/to_thread, OR normalize execution once in mcp_compat.py by wrapping sync handlers into a worker-thread call regardless of SDK version — decision recorded; concurrent sessions provably stay responsive while a long waiter runs under SDK-1 semantics
- evidence: diff + a concurrency harness (two sessions: one 900s-class waiter, one quick call) showing the quick call completes during the waiter on mcp 1.28.1 semantics; full suite green on both SDK lanes; landed shape pinned by test_server_sdk1_execution.py

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### runner_confinement docstring truthfulness
- id: `rm-075` (orig `rm-046` in run-e29c25913c00 numbering; renumbered at the same integration) | track: maintainability | priority: 25.0 | status: candidate
- signals: conductor.run-e29c2591:assess-F9, runner_confinement.py:229-249 _env_shebang_interpreter docstring claims PATH resolution "inside the sandbox" but the implementation calls shutil.which on the HOST PATH
- acceptance: docstring states host-PATH resolution precisely (and why that is safe for this step) or the implementation changes with tests; no silent behavioral change
- evidence: docstring diff (or impl diff + tests)

<!-- cycle-4 additions below: run bb9c68fb3ddf4c9fa77ead75cac72f07 (assess c9cc0e6b054d4bbe9e5ab0b0aca3221e, research 50fdc7b7c01642358a2a36323d9f359f) — authored 2026-09-30 against HEAD 14530e3e79; new ids continue at rm-076, unique through rm-075 (fleet invariant), render footer stays last. Pre-existing id-collision datum found while verifying (not introduced here): rm-052/rm-053/rm-055/rm-056/rm-057 each appear on two id lines from different landed runs (run-cbd4463370ee block vs run-43fe028246d3/run-c1ef27c97ab2 renumbered blocks) — each line carries its orig-id/landing annotation, so they are disambiguated in place per the landed-first convention; left untouched to preserve landed history, recorded here for the next integration/prioritize pass -->

*restore source: 6be3a5e95b^ (pre-collapse snapshot) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### pyproject trove classifiers
- id: `rm-085` | track: developer-experience | priority: 14.0 | status: candidate
- signals: conductor.run-e13b1c0d:research-C8, the [project] table has no classifiers while v0.12.0 is a live PyPI package (upstream 43c244a284 marks release notes PUBLISHED on GitHub+PyPI); PyPI facets/filters show nothing for the project
- acceptance: classifiers block (license, Python versions matching requires-python + the CI matrix, OS, topic) added; `python -m build` + `twine check` + `tools/check_package_hygiene.py` green; no version bump
- evidence: pyproject diff + hygiene tool output

- Post-batch refresh (compound d2295761, 2026-09-30): batch B1 "Fail-closed & durable on the shipped runtime" is implemented-pending-commit-gate in the run worktree — rm-077 (ToolError migration across all 11 clean_error raise sites, dual-lane client-path test green on mcp 2.2.0 + 1.30.0), rm-080 (_budget_would_pause fail-closed + 6 regressions), rm-082 (setattr cleanup), and rm-067's fixed-.tmp slice (shared _atomic_write_bytes standard; see rm-067's id note). Pre-review verification: impacted-targeted 47-file selection 1070 passed / 2 skipped; full suite 1612 passed / 2 skipped / 0 failed of 1614 (= assess baseline 1599 + 15 new); SDK-1 lane client-path green. Not selected and still open: rm-076 (pairs with rm-078 next cycle; its 3-way reconciliation must first fold the two unlanded skill-resolution branches run-cbd4463370ee/run-edd9fb12b6a4), rm-079 (design-gated), rm-081, rm-083 + rm-084 (CI cluster; rm-024 is now time-critical — Python 3.10 EOL 2026-10), rm-085. Next-cycle assess must also adjudicate unlanded run-d4c4dc76f3b0 (2026-09-13 "Q3 repair pack", 16 files, token_store overlap with B1's writes). Prevention rules and full cycle context: docs/maintenance-cycle-log.md, 2026-09-30 entry. Review/merge outcomes are NOT folded here — next cycle's assess carries them.

<!-- managed by hermes-roadmap render; do not edit by hand -->

*restore source: 16e3ff7a2f65 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Complete token_store secret-path permissions (sidecars + directory modes)
- id: `rm-086` | track: security | priority: 70.0 | status: candidate
- signals: conductor.run-a7e57044:assess-F2/research-R4 (extends rm-067's open remainder — see its 2026-09-30 update line), token_store.py:378-380 _connect DOES chmod the main DB 0o600 (correcting prior attempt ec010b7b's no-chmod claim) — but sqlite creates the -wal/-shm sidecars at default umask (empirically 0o644, reproduced 2026-09-30: python3 sqlite3 journal_mode=WAL in a tmpdir) and nothing ever chmods them: live ledger pages world-readable between checkpoints; secrets dir created at 5 plain-mkdir sites without 0o700 (:125, :164, :241, :325, :371); envelope/key writes use fixed .tmp + write-then-chmod + os.replace with no fsync (:127-133, :243-249) and the main DB has a create-to-chmod window
- acceptance: -wal/-shm sidecars 0o600 (chmod-at-open, or a recorded journal-mode decision with rationale); secrets dir 0o700 at first creation at all 5 sites; envelope/key/registry writes move to unique-tmp + fsync-before-replace (folding rm-067's token_store slice); a mode-assertion test creates a fresh store under umask 022 and asserts 0o600 on db+sidecars and 0o700 on the dir
- evidence: diff + the mode-assertion test green; rm-067 status line updated to point at this item for its token_store permission slice
- update 2026-10-01: IMPLEMENTED this cycle (run-a7e57044, implement 8765cfb1d27b47969cd4bc165326ddfc, pre-review/uncommitted; code authored by earlier voided deliveries — an ENOSPC abort, then the envelope-aborted re-delivery 43478a157bca49d8b7a2c32db5c76d41, which added the sidecar-creation-moment hardening the ENOSPC delta missed — audited line-by-line, re-verified and delivered by this re-delivery): `_harden_wal_sidecars()` (token_store.py:384) forces 0600 on -wal/-shm at BOTH creation moments — every write-path `BEGIN IMMEDIATE` (:836, :921, :990, :1179) and every `_connect` (:426, self-heal) — because the re-delivery empirically established sqlite materializes sidecars at the first write txn at umask 0644 (PRAGMA alone does not create them) and a lone reader recreates them after the last writer closes; secrets dir 0700 at all 5 mkdir sites (:157, :191, :266, :346, :413); envelope/key writes unique-tmp mkstemp + fsync-before-replace (:125-160, rm-067 slice folded); mode-assertion tests `test_token_store.py::test_fresh_store_permissions_under_umask_022` (0700 dir, 0600 db+sidecars+every secret artifact, no tmp residue, keeper-connection sidecar observation) + `test_store_sidecar_modes_self_heal_on_connect` — both fail pre-fix (sidecars/dir 0644/0755) and pass post-fix

*restore source: 3cbcf4945408 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Correct the maintenance-cycle-log batch stat
- id: `rm-089` | track: docs | priority: 15.0 | status: candidate
- signals: conductor.run-a7e57044:assess-F5, docs/maintenance-cycle-log.md:146 records the landed cycle-4 batch as '14 tracked files changed, +509/-23'; git show 80bd0f524d --numstat at HEAD = 15 files +620/-23 (14 files excluding ROADMAP.md would be +557/-20 — no framing reconciles)
- acceptance: stat corrected (or regenerated from git) with the verification command cited inline; no other prose touched
- evidence: one-line diff; git show --numstat output cited next to the corrected line
- update 2026-10-01: IMPLEMENTED this cycle (run-a7e57044, implement 8765cfb1d27b47969cd4bc165326ddfc, pre-review/uncommitted; code authored by earlier voided deliveries, audited and re-verified by this re-delivery): stat corrected to '15 tracked files changed, +620/−23' with the correction note citing `git show 80bd0f524d --numstat` inline; no other prose touched

*restore source: 3cbcf4945408 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Solutions-runbook staleness: the cron-create dead-jobs fix that never got recorded
- id: `rm-091` | track: docs | priority: 20.0 | status: candidate
- signals: research 0633763a, docs/solutions/mcp-cron-create-dead-jobs.md frontmatter still status:workaround / date_resolved:null for a root cause that appears fixed since PR #22 (2026-09-23): server.py:2017 hermes_cron_create delegates to operator_cron.py:1164 whose vendored parser (:47-58,:172-195) "mirrors the Hermes Agent scheduler contract"
- acceptance: verify end-to-end at HEAD that MCP hermes_cron_create produces a firing job FIRST (if still broken, convert to a defect fix); then flip the frontmatter per its own convention and add a small staleness guard
- evidence: end-to-end verification log (or the fix + test); frontmatter diff; guard test

*restore source: 5f855caa79a8 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### OAuth surface: the remaining on-loop blocking lane (rm-076 remainder; assess F1+F2)
- id: `rm-092` | track: reliability | priority: 115.0 | status: implemented
- signals: run-0aa75ea4:assess-F1/F2 (spool 6d9fbb7ba5a746c6a37271c94ffe6748), oauth_auth.py:1353 async BearerAuthMiddleware.__call__ → validate_bearer_token (:1303-1307) → validate_access_token (:1047) → _durable_access_token_valid (:1013) → token_store.lookup_token (:1032) — a fresh sqlite3.connect per authenticated request (token_store.py:682-707 via _connect :363, synchronous=FULL :375, busy_timeout=15000 :376); docstring :1023-1029 claims cache-miss-only durable resolution but no cache gate exists; WS handshakes share the middleware (server.py:3134/:3173); issuance writes inline too: async def token (:1651) → exchange_authorization_code/exchange_refresh_token (:1680/:1691) → token_store.commit_tokens (:1135), async def register_client (:1523) → _run_persist_hook (:1582-1583) → save_tokens (:1122/:1201); static-bearer mode unaffected (:1305); landed rm-076's acceptance said EVERY blocking store call — the OAuth paths were missed (ui_chat/live-events are correctly offloaded at this HEAD)
- acceptance: all blocking token_store calls reachable from async OAuth middleware/endpoints run via asyncio.to_thread per the rm-076 pattern; the hot path gains the cache gate its docstring claims OR the docstring is corrected; a lock-contention regression test (hold the store lock in a background thread, bound a concurrent authenticated request) times out pre-fix; the WS handshake path covered; the static-bearer lane unchanged
- evidence: offload-only diff; contention regression test green; test_oauth_auth.py + test_server.py targeted green; full suite zero-delta
- update 2026-10-01: IMPLEMENTED this cycle (run 0aa75ea44f93, implement 0b22a5d8, pre-review/uncommitted; the 429-voided prior attempt's on-disk work was audited line-by-line against the stewardship contract and RED-proven via git stash of the 4 source files, not redone): offload-only diff — BearerAuthMiddleware.__call__ resolves the OAuthState revocation lane via asyncio.to_thread (oauth_auth.py:1382-1385; the static-bearer compare stays on-loop as pure CPU; this __call__ is also the WS handshake path), and the /oauth/token exchanges (exchange_authorization_code / exchange_refresh_token, :1696-1716) plus register_client's _run_persist_hook (:1597-1600) are offloaded per the rm-076 pattern; the docstring was CORRECTED, not gated — _durable_access_token_valid (:1017-1025) now states the no-in-memory-shortcut design as deliberate cluster revocation correctness; 2 lock-contention regression tests (test_bearer_middleware_survives_durable_store_lock_contention, test_token_endpoint_exchange_survives_durable_store_lock_contention) hold the durable store lock from a background thread and were red pre-fix; targeted 50-file lane 1271P/2S/0F (attempt b8b4054c), full gate exit 0 (attempt 4e417e1d, envelope result-983149-329885774.json), static-bearer lane unchanged

*restore source: 5f855caa79a8 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### ui_mount doctor false-PASS: rm-078's signal decays under churn and rotation (assess F3+F5)
- id: `rm-093` | track: reliability | priority: 65.0 | status: implemented
- signals: run-0aa75ea4:assess-F3/F5 (spool 6d9fbb7ba5a746c6a37271c94ffe6748), operator_diagnostics.py:573 _check_ui_mount scans only op.audit_tail(limit=50) (:581) for the once-written startup failure record (server.py:3227 via _signal_ui_mount_failure :3090-3126) — 50 ordinary records from normal traffic (operator_events.py:569, ui_ops.py:632/:637) evict the evidence and doctor reports UI_MOUNT_HEALTHY (:605-615) while the UI is down; rotation makes it permanent (audit_tail skips the archived .1 generation, operator_policy.py:997-1006); test_operator_diagnostics.py:695-718 asserts only failure-present=>WARN / failure-absent=>PASS — no churn-eviction or post-rotation coverage (the F5 test gap folds into this item's acceptance)
- acceptance: the ui_mount health state survives audit churn and rotation — a dedicated persistent signal (state file or unbounded/flagged record class) instead of a bounded audit-tail scan, or a mount-time live probe; regression tests cover >50-record churn eviction AND post-rotation invisibility (both red pre-fix); doctor wording stays truthful
- evidence: diff + the two regression tests green; sample doctor output under churn; docs/operator-mode.md failure-mode note updated if the mechanism changes
- update 2026-10-01: IMPLEMENTED this cycle (run 0aa75ea44f93, implement 0b22a5d8, pre-review/uncommitted): durable state marker is doctor's authority — new operator_policy.py block at :1065-1143 (UI_MOUNT_STATE_FILENAME "ui-mount-state.json", ui_mount_state_path / read_ui_mount_state / write_ui_mount_state / record_ui_mount_failure; one helper writes marker AND audit record, both best-effort); server._signal_ui_mount_failure routes through it (:3099-3101) and build_asgi_app writes "healthy" on a successful mount / "disabled" when the UI is off, clearing any stale failure marker (:3221-3231); _check_ui_mount (operator_diagnostics.py:573-635) reads the marker first (UI_MOUNT_FAILED WARN carrying ui_mount_state_path + last_ui_mount_failure_timestamp), keeps op.iter_audit_for_tool("ui_mount") only for pre-marker servers' historical failures, and adds UI_MOUNT_CHECK_UNAVAILABLE when neither source is readable; 4 regression tests (churn-eviction >50 records, post-rotation, marker-failure-without-audit-records, marker healthy/disabled pass) — churn + rotation red pre-fix; docs/operator-mode.md doctor paragraph updated (:506); FLEET NOTE for the landing gate: run-a7e57044 carries an UNLANDED implementation of this same defect as its rm-087 (durable UI_MOUNT_FAILURE_MARKER, server.py @@3121/@@3229 hunks, same base caf60018d2) — dedupe by defect content and land ONE implementation

*restore source: 5f855caa79a8 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Document the fleet + runner env knobs (assess F4; structural fix = rm-088)
- id: `rm-094` | track: docs | priority: 50.0 | status: implemented
- signals: run-0aa75ea4:assess-F4 (spool 6d9fbb7ba5a746c6a37271c94ffe6748), HERMES_GPT_FLEET_PEER_NAME (server.py:3001, verified by peers against expected_card_identity :3051), HERMES_GPT_FLEET_PEER_URL / HERMES_GPT_HOST / HERMES_GPT_PORT (:3005-3008 advertised peer URL fallback), HERMES_GPT_PI_EXE (operator_runners.py:863), HERMES_GPT_OMX_EXE (:1156) — zero occurrences in README.md, docs/**, CHANGELOG.md (recursive grep at caf60018d2); fleet trust attestation and runner-executable overrides are discoverable only from source, contrary to the repo's documentation rules
- acceptance: every knob named above documented with default, scope, and gate semantics in the right operational doc (fleet + runner sections) with a README pointer where appropriate; a small guard (test or doc-drift check) keeps new HERMES_GPT_* knobs from landing undocumented; rm-088 remains the structural registry this defers to
- evidence: docs diff; guard test/check green; recursive grep shows zero undocumented among the named set
- update 2026-10-01: IMPLEMENTED this cycle (run 0aa75ea44f93, implement 0b22a5d8, pre-review/uncommitted): docs/operator-mode.md gains a Fleet peer identity + advertised-URL section (:428-446 — HERMES_GPT_FLEET_PEER_NAME/URL/VERSION with the HERMES_GPT_HOST/PORT fallback and trust-attestation semantics) and a Runner executable overrides section (:723-741 — HERMES_GPT_PI_EXE/OMX_EXE/OPENCODE_EXE), with the README fleet-routing paragraph (:329) pointing at them; new drift guard test_env_knob_docs.py (3 tests) scans every shipped py-module for literal HERMES_GPT_* names and requires each to appear in README/docs or on the explicit 20-entry _UNDOCUMENTED_BACKLOG (which itself fails when an entry becomes documented or leaves source — the backlog stays honest), while the 8-knob named set must live in docs/operator-mode.md itself; red pre-fix (the assess-named knobs had zero doc hits at caf60018d2); rm-088 stays the open structural registry this defers to

*restore source: 5f855caa79a8 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### tools/upstream-gap watch: automate the fork-vs-upstream probe
- id: `rm-115` | track: developer-experience | priority: 20.0 | status: candidate
- signals: conductor.run-b6659410:research-R14 (reasoned, accepted after rejecting vaguer watch ideas), every maintenance cycle re-derives fork/upstream state by hand — this run alone ran six probe commands (ls-remote tip+tags, rev-list count, merge-base, PR list, diff-stat) and sibling runs repeated them same-day; tools/ carries only check_package_hygiene.py; rm-103's adopt-on-tag gate is currently a manual watch
- acceptance: tools/upstream_gap.py (or equivalent) prints distance to upstream master, newest tag, whether the fork tip is an ancestor (ff vs true-merge), open-PR list, and flags when an upstream tag appears that the fork has not adopted — usable as the mechanical trigger for rm-103; documented in docs/maintenance-cycle-log.md or the runbook index; runs read-only against git remotes (no network writes)
- evidence: new tool + sample output captured in a cycle artifact; README/docs pointer; no network mutations (loopback-only posture preserved)

<!-- managed by hermes-roadmap render; do not edit by hand -->

*restore source: e476cd9d7c44 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Adopt upstream v0.13 (9-commit gap incl. Autopilot) as one batch with rm-081
- id: `rm-116` | track: reliability | priority: 120.0 | status: candidate (tag-gated)
- signals: conductor.run-099e2bfc:research-R1, upstream/master 9 commits past merge-base 7795aa3ce8 (re-verified 2026-10-01 at this HEAD: `git rev-list --count HEAD..upstream/master` -> 9); tip f4151d9728 = PR #82 "Autopilot (v0.13) durable, default-off Mission runtime", merged 2026-09-30T03:51Z, 32 files +6653/-14; gap also carries upstream's v0.12.0 release commit 8766e28650 and the skills-loader trio rm-081 already enumerates; v0.13.0 still untagged (tags top out v0.12.0) with release-prep PRs #83/#84 open — moving-target discipline says adopt once the tag lands; same-defect convergences (all unlanded): rm-085 (run-0aa75ea44), rm-098 (run-1a6beeba), rm-103 (run-b6659410) — landing gate folds
- acceptance: re-probe tag + PR state at selection time; once v0.13.0 tags (or a recorded decision accepts the untagged tip), integrate the FULL 9-commit gap as one unit, reconciling rm-081's fork-half skill-resolution authority with upstream's loader-truth half; Autopilot stays default-off with a test proving zero behavior change when off; full suite + upstream's new tests green on both SDK lanes; CHANGELOG records the adoption
- evidence: integration merge record; post-merge `git rev-list --count HEAD..upstream/master` == 0; adopted tests green; CHANGELOG entry

*restore source: 427966aa85f4 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Declare starlette and anyio as direct dependencies
- id: `rm-117` | track: packaging | priority: 90.0 | status: candidate
- signals: conductor.run-099e2bfc:research-R2, 9 first-party modules import starlette/anyio directly (oauth_auth.py, operator_live_events.py, server.py, ui_api.py, ui_chat.py, ui_fabric.py, ui_missions.py, ui_ops.py, ui_security.py) while pyproject dependencies (:15-21, re-verified) declare neither; uv.lock already resolves starlette 1.7.0 — a 1.x major reached only transitively (via mcp/uvicorn/sse-starlette) — and anyio 4.15.1; an undeclared direct import riding a transitive major can break invisibly (starlette already crossed 0.x->1.x under us); PyPI 2026-10-01: starlette 1.7.0 / anyio 4.15.1 current; convergences (unlanded): rm-099 (run-1a6beeba), rm-108 (run-b6659410, adds the lockfile-commit decision) — landing gate folds
- acceptance: pyproject dependencies gain explicit bounded starlette + anyio entries (floors at what the code actually requires, ceilings consistent with the transitive range); lock refresh keeps resolutions inside the bounds; no import-surface change anywhere; full suite green
- evidence: pyproject + uv.lock diffs showing both as direct bounded entries; full-suite exit 0; the 9-module import list unchanged by grep

*restore source: 427966aa85f4 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Python 3.10 EOL (2026-10-31): floor-bump vs keep-and-fix decision; folds the WS idle-break
- id: `rm-118` | track: packaging | priority: 85.0 | status: partially implemented (pending commit gate — guard slice landed 2026-10-01, run 099e2bfc8507 implement c95caab5; recorded keep-vs-bump decision still owed by the 2026-10-31 EOL deadline)
- signals: conductor.run-099e2bfc:research-R3 + assess-F1, Python 3.10 EOL is 2026-10-31 (~30 days out; endoflife.date/api/python.json) while requires-python = ">=3.10" (pyproject.toml:10, re-verified) and CI runs 3.10 in the push matrix (.github/workflows/ci.yml:43) and ALL FOUR SDK-matrix lanes (:56); assess F1 re-verified at this HEAD: operator_live_events.py:395 `await asyncio.wait_for(websocket.receive_text(), timeout=0.5)` is guarded only by bare `except TimeoutError:` (:396) — on py3.10 asyncio.wait_for raises the distinct asyncio.TimeoutError (alias merged in 3.11), so the idle /events/ws stream dies on the first idle poll, and no test covers the idle path (13 tests, zero sleep/wait_for/timeout references); extends landed rm-024 (3.13-lane/3.10-EOL planning item); convergences (unlanded): rm-100 (run-1a6beeba), rm-109 (run-b6659410), plus rm-110's idle-timeout-guard slice (run-b6659410) — landing gate folds
- acceptance: a RECORDED DECISION before the deadline: (a) bump requires-python to >=3.11, drop the 3.10 CI lanes, add a 3.13 lane (mooting F1), CHANGELOG + docs floor mentions updated; OR (b) keep 3.10 and land the one-line guard `except (TimeoutError, asyncio.TimeoutError):` (no-op alias on 3.11+) plus an idle-stream survival test that fails pre-fix under 3.10 semantics; either branch records the deadline date at selection
- evidence: decision note in the PR/commit; pyproject+ci.yml diff (branch a) or guard diff + new test green (branch b); the lane evidence for whichever interpreter the decision test runs on
  - update 2026-10-01: PARTIALLY IMPLEMENTED this cycle (uncommitted, pre-review) — branch-(b) guard slice landed: multi-catch `(TimeoutError, asyncio.TimeoutError)` on the 0.5s idle poll at operator_live_events.py:405, poll bound moved to module constant `_WS_IDLE_POLL_SECONDS` (:46), plus two new tests in test_operator_live_events.py (`test_websocket_idle_poll_catches_asyncio_timeout_error` source-contract red witness + `test_websocket_survives_idle_polls_and_keeps_serving_control_frames` behavioral idle test). NOTE: the implement-phase artifacts keyed this unit "rm-119" (label slip; content maps here — see the Cycle 5 outcome block). REMAINDER: the recorded keep-vs-bump decision (deadline 2026-10-31); if branch (a), the requires-python bump + CI 3.10-lane edits. Validation: impacted targeted lane 85 passed/0 failed (attempt 06af0ce8); full gate 1606 passed / 5 skipped / 0 failed / 0 errors = 1611 at digest validation:v1:4f73ec6825c2a334bd9c50da00c6fe678ba9a4ac248e1fd988b8dfdc0268ed77 (envelope result-2949895, verbatim run adopted by attempt b0dc73eb).

*restore source: 427966aa85f4 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Doctor ui_mount: stateful signal instead of a capped audit tail (folds assess F2+F3)
- id: `rm-119` | track: correctness | priority: 60.0 | status: partially implemented (pending commit gate — exactly-once visibility asserts landed 2026-10-01, run 099e2bfc8507 implement c95caab5; stateful doctor signal + churn-padding test remain open; convergences rm-093/rm-111 fold at the gate)
- signals: conductor.run-099e2bfc:assess-F2+F3, operator_diagnostics.py:581 `_check_ui_mount` judges health solely from `op.audit_tail(limit=50)` (re-verified at this HEAD): the boot-time ui_mount failure is a one-time event, so once it scrolls past the last 50 audit records under normal operator churn, doctor reports PASS/UI_MOUNT_HEALTHY "No recorded UI mount failures." (:613-618) while the UI stays unmounted for the process lifetime — a false PASS in exactly the stale-stat class the landing gate flags; test_ui_ops.py:616-625 asserts presence only (`assert audit_hits`, `assert any(... ui_mount_failed ...)`), so duplicate emissions would still pass; convergences: rm-093 (run-0aa75ea44 — whose implement 0b22a5d8 carries an UNCOMMITTED operator_diagnostics.py delta for this same defect at this same HEAD) and rm-111 (run-b6659410) — landing gate folds/dedupes against that delta first
- acceptance: doctor reads a stateful signal (server-persisted mount status, or an unbounded tool='ui_mount' audit query) instead of the 50-record tail; a churn-padding test drives a ui_mount failure past 50 newer audit records and asserts doctor still WARNs (fails on the current tail scan); the visibility test tightens to exactly-once (len(audit_hits) == 1 and a single matching ui_mount_failed live event); docs/operator-mode.md's failure-mode wording stays truthful
- evidence: diff + churn-padding regression test green; tightened exactly-once assertions green; test_ui_ops.py + test_operator_diagnostics.py lanes green
  - update 2026-10-01: PARTIALLY IMPLEMENTED this cycle (uncommitted, pre-review) — acceptance's test-tightening slice landed: test_ui_ops.py:614-630 now asserts exactly-once (`len(...) == 1`) for both the ui_mount audit hits and the matching ui_mount_failed live events, replacing presence-only asserts; pure hardening — current emission was already exactly-once, no defect found. NOTE: the implement-phase artifacts (and an inline test comment) keyed this rider "rm-121" (label slip; content maps here — see the Cycle 5 outcome block). REMAINDER: the stateful doctor signal (server-persisted mount status or unbounded tool='ui_mount' query replacing operator_diagnostics.py:581's audit_tail(limit=50)) + the churn-padding regression test.

*restore source: 427966aa85f4 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Watch and adopt upstream PR #85 (configurable file backups)
- id: `rm-121` | track: compatibility | priority: 40.0 | status: candidate (watch)
- signals: conductor.run-099e2bfc:research-R5, upstream PR #85 "feat(operator): make file backups configurable" opened/updated 2026-09-30T17:39Z — NEW since the 2026-09-30 sibling probes — 4 files +47/-0, mergeable_state=unstable at probe time; small and config-gated; aligns with the fork-side HERMES_HOME backup/migration capability (rm-087, run-0aa75ea44, unlanded) and rides the upstream-gap watch automation (rm-115, run-b6659410, unlanded)
- acceptance: re-probe PR #85 state at selection; adopt once merged upstream and stable (or record a decision not to wait), reconciling with rm-087's design if that lands first; adopted behavior stays config-gated with zero default change; adopted tests green
- evidence: PR state probe at selection; adoption diff + tests green; CHANGELOG note
  - update 2026-10-01: NOT TOUCHED this cycle — watch item only (PR #85 still open, mergeable_state=unstable, at the 2026-10-01 probe). CORRECTION: the implement-phase artifacts' "rider rm-121" label actually delivered rm-119's exactly-once test-tightening slice; no PR #85 adoption happened (content-based re-mapping recorded in the Cycle 5 outcome block).

*restore source: 427966aa85f4 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Correct the stale cycle-4 landing statistics in the maintenance log (assess F4)
- id: `rm-123` | track: docs | priority: 15.0 | status: candidate
- signals: conductor.run-099e2bfc:assess-F4, docs/maintenance-cycle-log.md:145 (re-verified) still reads "14 tracked files changed, +509/−23" while the landed commit 80bd0f524d is 15 files, +620/-23 (`git show --stat`); a stale statistic in the landed provenance record contradicts the log's own truthfulness rule and was never corrected at landing
- acceptance: the paragraph states the true numbers (15 tracked files, +620/−23) with the derivation command named; a dated one-line correction note records the fix; no other content changes
- evidence: docs diff; `git show --stat 80bd0f524d` output cited beside the corrected sentence

*restore source: 427966aa85f4 (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Chat transcript window: newest-first hydration + keyset paging for GET /messages
- id: `rm-124` | track: correctness | priority: 90.0 | status: candidate
- signals: conductor.run-b6b8792f:assess-F1 + research-R4, ui_chat.py:709 hydrates GET /api/sessions/{id}/messages via db.get_messages(..., limit=MESSAGE_PAGE_LIMIT) WITHOUT latest=True while hermes_state.py:205 emits `ORDER BY timestamp ASC, id ASC LIMIT n` — the OLDEST page; MESSAGE_PAGE_LIMIT=500 (ui_chat.py:75); the handler accepts no paging params (grep offset/after_id/before_id/cursor across ui_chat.py: zero hits); the in-file correct idiom already exists (ui_chat.py:537 latest=True); deterministic repro (600-msg session): as-shipped window = msg-001..msg-500 — the 100 most-recent messages unreachable through the endpoint; test gap: test_ui_chat.py session-resume coverage uses 2-message sessions so window direction is untested
- acceptance: default no-params response returns the NEWEST page (matches the :537 idiom semantics, with an explicit compat note in the UI docs); keyset paging params (before_id/after_id) page backward/forward from a cursor so every message in a >MESSAGE_PAGE_LIMIT session is reachable; a session-level test with >500 messages asserts newest-first default AND gapless newest→oldest paging; the existing resume test is extended past the page limit
- evidence: diff + new paging tests green in test_ui_chat.py; a repro-style assertion that a 600-message session's default response ends at msg-600; docs (operator-mode UI section) note the default-window semantics

*restore source: d02eed2ffdaa (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Adopt upstream v0.13 "Autopilot" (durable default-off Mission runtime)
- id: `rm-130` | track: compatibility | priority: 100.0 | status: candidate (scoping-gated)
- signals: conductor.run-b6b8792f:research-R1, upstream master f4151d9728 = PR #82 "feat: Autopilot (v0.13)" merged 2026-09-30, NOT yet tagged (upstream tags stop at v0.12.0 = c3a537693c66; ancestry verified locally via FETCH_HEAD + tag); v0.12.0...master delta = 7 commits / 46 files / ~8k lines: +operator_autopilot.py (1922 lines), 11 new test files (~3400 lines), operator_mission_plan.py +244, operator_mission_runtime.py +116 (superseded_by), operator_skill_resolution.py grown to 585 lines, operator_contract.py +60, server.py +62 (3 gated tools), ui_missions.py +81, placement/controller/swarm/capability-manifest edits, docs/autopilot.md; the safety shape aligns with fork invariants (default-off HERMES_GPT_AUTOPILOT=1, 137→140 tools only with gate, never dispatches/approves high_impact or approval nodes, stops at awaiting_approval, completes nodes only on observed validated evidence, budget gate requires envelope status `within`); fork divergence is concentrated in exactly these shared modules — operator_skill_resolution.py: fork 324-line rm-041 resolver vs upstream 585 (831-line diff, NOT a file-level merge candidate) and fork CI has no Hermes-Agent checkout lane for loader tests
- acceptance: scoping pass FIRST (conflict map of the 46-file delta vs fork invariants, rm-026-reconciliation style); the adoption lands after the upstream v0.13.0 tag exists (tracking untagged master is defensible for scoping only); HERMES_GPT_AUTOPILOT unset = byte-identical tool surface (upstream pins 137 tools); conflict files reviewed line-by-line against the AGENTS.md product invariants (never approves, never touches secret paths, observed-evidence completion) with an explicit Autopilot-vs-Swarm overlap analysis (Autopilot drives ONE mission; Swarm coordinates many workers); suite green incl. the 11 upstream test files on both SDK lanes; CHANGELOG + docs/autopilot.md adopted with a fork-context note; sequencing vs rm-081 (the skill-loader trio is verifiably inside this delta) and vs rm-083/rm-065 (fork version numbering) decided in the scoping note
- evidence: scoping conflict-map artifact; integration merge record; adopted-tests-green run on both SDK lanes; gate-off tool-surface byte-equality check; CHANGELOG/docs delta

<!-- managed by hermes-roadmap render; do not edit by hand -->

*restore source: d02eed2ffdaa (historical recovery) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*


### Re-green master CI: replace 4 failing + 1 vacuous PKCE-contract tests
- id: `rm-003` | track: reliability | priority: 120.0 | status: implemented
- signals: conductor.run-a51c0f6c:assess-F1, tests stale contract: test_codex_pr63_remediation.py:348,356,492,812,941 issue codes with code_challenge="" then expect exchange success vs oauth_auth.py:477-479 mandatory-PKCE fail-closed (26ed7b4c0d via merge cb8c6fed03 2026-09-13)
- acceptance: the four failing tests (test_revocation_rotates_authorization_code_key, test_post_revocation_fresh_exchange_persists, test_startup_migration_preserves_positive_legacy_epoch, and test_exchange_fails_loud_when_persistence_fails — previously passing vacuously because the empty-challenge gate raised invalid_grant before its injected persistence failure) mint real S256 challenge/verifier pairs and pass; a new test asserts an empty-challenge code is always rejected at exchange (fail-closed contract stays); python -m pytest -q is fully green locally and the next master CI run passes
- evidence: cycle-1 implement (2026-09-21, attempt b2f5ddda): all five stale tests re-bound to real S256 pairs + new empty-challenge-rejected test (test_codex_pr63_remediation.py), full local suite 1438 passed/6 skipped/0 failed (Py3.11) and 1442/2 (Py3.13 uv env); REMAINING for acceptance: green master CI run (review/merge pending) to unblock publish.yml (Folded 2026-09-23 at integration b016efb52596, conflict case b50fde2f: run c1ef27c97ab2's same-topic B1 — the first cycle-1 implementation of these re-binds — landed on master 2026-09-21 via PR #12 squash 6b2abc7808; see the run's landing record below.)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Skip-instead-of-fail for distribution-metadata test
- id: `rm-007` | track: reliability | priority: 40.0 | status: implemented
- signals: conductor.run-a51c0f6c:assess-F7, test_mcp_compat.py:81 test_package_metadata_allows_both_sdk_families raises importlib.metadata.PackageNotFoundError in non-installed checkouts (worktrees, containers) instead of skipping
- acceptance: the test skips with a clear reason when the distribution is not installed and still runs in CI (which installs -e .[dev])
- evidence: cycle-1 implement (2026-09-21): test_mcp_compat.py:81 skips with reason on PackageNotFoundError (bare Py3.11 checkout: 14 passed 1 skipped) and executes+passes when the distribution is installed (Py3.13 uv env: metadata test runs green)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Protect master with required CI checks
- id: `rm-008` | track: reliability | priority: 85.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F3, gh api repos/codeo1io/hermes-gpt/branches/master/protection -> 404 "Branch not protected"; merges #66,#67,#5,#7 landed 2026-09-13..20 on red master (4 consecutive failing runs, latest 35480822047)
- acceptance: master branch protection requires the CI workflow's test (and ruff) jobs plus linear history; direct pushes restricted to admins
- evidence: gh api branches/master/protection returns required_status_checks contexts; a red PR cannot be merged (observed once)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Intentional MCP SDK coverage: pin current lines + protocol-revision assertion
- id: `rm-009` | track: reliability | priority: 80.0 | status: implemented
- signals: conductor.run-a51c0f6c:research-R3, .github/workflows/ci.yml:24-37 exact pins mcp==1.28.1/2.0.0 while 1.30.0+2.2.0 shipped 2026-09-07 (pip index; pyproject admits >=1.28.1,<3); SDK 2.1/2.2 behavior changes unasserted (exception-text hiding #3314, 4MiB OAuth body cap #3336); test_mcp_sdk_migration.py:109-110 already pins 2026-07-28 _meta keys
- acceptance: CI matrix adds explicit mcp==2.2.0 and mcp==1.30.0 lanes (or refreshes pins each cycle); a spec-revision assertion test fails loudly when the installed SDK advertises a protocol revision differing from the one hermes-gpt's tests pin; audit note confirms no hermes tool relies on exception text reaching clients and OAuth endpoint bodies are within 4 MiB
- evidence: cycle-1 implement (2026-09-21): ci.yml adds explicit mcp==2.2.0 and mcp==1.30.0 lanes; test_sdk_protocol_revision_is_deliberate asserts LATEST_PROTOCOL_VERSION=='2026-07-28' under SDK 2 (legacy set under SDK 1) and passes locally on SDK 2.0.0; REMAINING for acceptance: green run on the two new CI lanes + 2.1 behavior-change audit note (exception-text hiding #3314, 4 MiB OAuth body cap #3336)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Speak the official MCP Tasks extension for long-running work (read-only mapping)
- id: `rm-011` | track: compatibility | priority: 45.0 | status: candidate
- signals: conductor.run-a51c0f6c:research-R1, MCP spec 2026-07-28 changelog item 6 (SEP-2663): official io.modelcontextprotocol/tasks extension (tasks/get polling, tasks/update client input, unsolicited handles); hermes job supervisor (upstream issue #57, operator_job_supervisor.py) already implements the same semantics as hermes-private tools; cycle-3 refresh (2026-09-23): MCP roadmap blog (2026-08-22) lists Tasks as an official extension — direction confirmed, priority unchanged
- acceptance: additive read-only mapping: existing job/delegation IDs surface as standard task handles via tasks/get; tasks/update accepts approval inputs only on surfaces that already permit them; hermes_* tools remain canonical; gated on SDK support probe passing on both SDK families
- evidence: integration test showing a generic MCP client polling a hermes job via tasks/get; docs/codex.md + docs/operator-mode.md updated; no change to authority ladder (verified by existing safety tests)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### MRTR (input_required) as the standardized approval handshake
- id: `rm-012` | track: compatibility | priority: 35.0 | status: candidate
- signals: conductor.run-a51c0f6c:research-R2, MCP spec 2026-07-28 changelog item 7 (SEP-2322): InputRequiredResult + retry with inputResponses; hermes dry-run->apply ladder and Owner-Mode confirmations currently express approvals via bespoke confirm=/apply= flags (operator_policy.py, docs/operator-mode.md authority ladder)
- acceptance: design note mapping each mutating surface's approval flow onto MRTR, with an opt-in pilot behind an env gate; direct-mode per-call gates unchanged; safety tests extended to prove a client cannot convert dry-run to apply without the explicit input response
- evidence: design doc + pilot integration test on one surface (e.g. workspace write) showing input_required round-trip; full safety suite green

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Split server.py registration into per-subsystem modules
- id: `rm-013` | track: maintainability | priority: 30.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F9, server.py is a 3,856-line module registering 153 hermes_* tools for 20+ operator_* modules; PRs #66 and #67 both rewired server.py (merge-collision hotspot); tool count is CI-pinned (test_server.py) which mitigates drift
- acceptance: registration decomposed per subsystem with zero tool-surface change; test_server tool-count/name snapshot unchanged before/after; import graph documented in docs/design
- evidence: diff shows mechanical moves only; the full suite and tool-count snapshot pass unchanged

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Remove dead token_store.py block and close the F821 class
- id: `rm-016` | track: maintainability | priority: 75.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21)
- resolution: dead block deleted in worktree run-6d49d1e3979f-6d49d1e3 (implement attempt a90769548e); repo-wide F821 = 0; test_token_store.py green
- signals: conductor.run-6d49d1e3:assess-F2, token_store.py:1097-1145 unreachable dead block referencing undefined hermes_root (ruff F821 at 1097,1103,1107,1113,1137); orphaned status()-shaped body from 89cbfbe232 (#64); live duplicate logic at token_store.py:1020
- acceptance: block deleted (or re-attached deliberately to a real caller with tests); `ruff check --select F821` clean; token-store behavior unchanged (test_token_store.py green)
- evidence: `python3 -m ruff check --select F821 .` exits 0; test_token_store.py passes; diff shows removal only

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Lint gate: drive 61 ruff errors to zero and enforce in CI
- id: `rm-017` | track: reliability | priority: 65.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21)
- resolution: repo-wide ruff 61 -> 0 across 35 files (30 safe autofixes + manual; no unsafe fixes, no blanket noqa; one targeted E402 noqa for the test_package_hygiene.py sys.path bootstrap; `_allowed_message_roles` call kept as a bare statement — it is a raising validation gate, not dead code); CI lint job list replaced with repo-wide `ruff check .`; validated full-suite 1359/1368 with zero regressions
- signals: conductor.run-6d49d1e3:assess-F4, `python3 -m ruff check .` = 61 errors (28 F401, 16 F841, 5 E402, 5 F821, 3 E731, 3 E741, 1 E702); no ruff job enforced in .github/workflows/ci.yml
- acceptance: `ruff check .` exits 0 (auto-fixable set + manual review, no blanket noqa); CI runs ruff as a required job; rm-016 lands first so the F821s disappear by deletion
- evidence: green CI run including the ruff job; commit diff shows no behavior change (full suite green)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Decide plan-node lease semantics (wire or remove)
- id: `rm-019` | track: maintainability | priority: 30.0 | status: candidate
- signals: conductor.run-6d49d1e3:assess-F6, operator_mission_plan.py:941 unconditionally clears plan_nodes.lease_lock/lease_expires but nothing acquires plan-node leases (controller uses controller_pass_lease); views expose always-empty fields (:626-627)
- acceptance: either acquisition wired with tests (fields real) or fields/DTO columns removed end-to-end (schema + views + transitions); no always-empty surface shipped
- evidence: test covering lease acquire/clear round-trip OR diff removing the fields with all view tests green

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Restore pre-pause state on node resume
- id: `rm-020` | track: correctness | priority: 25.0 | status: candidate
- signals: conductor.run-6d49d1e3:assess-F7, operator_mission_plan.py:104 NODE_TRANSITIONS allows paused->{running,blockable,failed} only; a node paused from pending or dispatched can never return to its pre-pause state
- acceptance: paused nodes may transition back to their recorded pre-pause state (or the transition table documents the intentional semantics with a test); no persisted-state migration required
- evidence: unit test pausing from each source state and resuming; docs/operator-mode.md lifecycle section matches

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Warn-and-backup before overwriting corrupt cron jobs.json
- id: `rm-021` | track: reliability | priority: 28.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21; promoted from stretch after rm-018 dropped)
- resolution: operator_cron.py `_read_jobs` splits OSError/JSONDecodeError and backs up unparseable jobs.json to `jobs.json.corrupt-<ts>` (byte-identical dedupe; best-effort; no stdout/stderr noise near MCP stdio — the sidecar's presence is the operator signal) before the next atomic write can destroy it; coverage includes BOTH JSON-syntax corruption and binary/non-UTF-8 corruption (review-fix 711573d0: UnicodeDecodeError added to the recovery except-clause, backup writes the captured payload — no TOCTOU re-read); new test `test_corrupt_jobs_json_backed_up_before_overwrite` in test_operator_cron.py covers both payload classes; whole file green serially; recovery signal documented in docs/operator-mode.md (cron section)
- signals: conductor.run-6d49d1e3:assess-F8, operator_cron.py:105 _read_jobs swallows JSONDecodeError -> [] and the next mutation atomically replaces jobs.json (os.replace at :137), silently destroying a corrupt-but-recoverable file
- acceptance: on parse failure hermes_cron surfaces a visible error (or writes jobs.json.corrupt-<ts> aside) before any overwrite; a file with one bad byte stays recoverable
- evidence: unit test injecting corrupt JSON proving backup+warning; existing cron tests green

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Single topological-sort implementation
- id: `rm-022` | track: maintainability | priority: 15.0 | status: candidate
- signals: conductor.run-6d49d1e3:assess-F9, operator_controller.py:878 _topological_order is O(V*E) while operator_mission_plan.py:313 has a linear Kahn implementation; two algorithms for the same DAG drifting
- acceptance: one shared helper (linear) used by both call sites; MAX_NODES=64 bound keeps current behavior; order-stability tests prove identical outputs on existing fixtures
- evidence: diff removing one implementation; fixture equivalence test green

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Pin/bound uvicorn (floating 0.x dependency)
- id: `rm-023` | track: reliability | priority: 58.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21)
- resolution: pyproject.toml `uvicorn` -> `uvicorn>=0.30,<1`; TOML re-validated; pyyaml is now the only remaining bare runtime dependency (next-cycle candidate)
- signals: conductor.run-6d49d1e3:research-R4, pyproject [project] dependencies list `uvicorn` unbounded; PyPI latest 0.53.0 (2026-09 probes); 0.x minors routinely break ASGI internals; mcp is bounded but uvicorn floats
- acceptance: uvicorn bounded (e.g. >=0.30,<1 with a reviewed upper cap) in pyproject; CI installs the reviewed version; a uvicorn cap move becomes a deliberate changelog event
- evidence: pyproject diff + green CI on the pinned range; CHANGELOG note when the cap moves

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Python 3.13/3.14 CI lanes; plan the 3.10 EOL floor bump
- id: `rm-024` | track: reliability | priority: 50.0 | status: candidate
- signals: conductor.run-6d49d1e3:research-R5, .github/workflows/ci.yml:29 matrix python ['3.10','3.11','3.12']; requires-python >=3.10 (pyproject); Python 3.10 EOL 2026-10 (one month out at 2026-09-21); 3.13/3.14 stable and untested; sibling rm-003 evidence already validated the suite on Py3.13 uv env (1442/2 green); cycle-3 refresh (2026-09-23, endoflife.date): 3.10 EOL is T-38 days (2026-10-31) while the matrix still runs ['3.10','3.11','3.12'] at HEAD 4b958379d6 (ci.yml:38-42) — the closest dated deadline on the roadmap; re-probed 2026-09-23 by run e29c25913c00 research (landing 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0): still no 3.13 lane at its HEAD (ci.yml:39-43), EOL then 5.5 weeks out, PyPI-current mcp 2.2.0 / uvicorn 0.53.0 / cryptography 50.0.1 / anyio 4.15.1 all support the 3.10 floor today; refresh 2026-09-30 (run bb9c68fb3ddf research, pypi.org JSON): matrix STILL ['3.10','3.11','3.12'] at ci.yml:43 — EOL now T-31 days — mcp 2.2.0 / cryptography 50.0.1 unchanged, uvicorn 0.54.0 / ruff 0.16.9 current
- acceptance: CI matrix adds 3.13 (and 3.14 if deps allow) lanes green; a dated plan records the 3.11 floor bump (drops the tomli<3.11 conditional) for the 0.11.0 release
- evidence: green CI matrix run including 3.13; CHANGELOG/release-notes entry at bump time

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Finish the v0.10 controller slice: D3 hard-block + shadow-to-live
- id: `rm-025` | track: feature | priority: 40.0 | status: candidate
- signals: conductor.run-6d49d1e3:research-R6, CHANGELOG 0.10.0 records budget D3 hard-block as flag-default-off wired for a later slice and the controller running in shadow; docs/operator-mode.md + v0.10 slice notes define the live path
- acceptance: D3 hard-block enforced live behind the flag with tests (over-budget iterations blocked, resume path defined); controller promoted from shadow to live with an opt-out; docs updated
- evidence: tests proving block/resume under the flag; ops note recording the first live run; docs diff

<!-- cycle-2 additions below: run 684b97865efc456da2a21dc4259ce30f (assess 2bd3be4650704a3c877a885cecb695d1, research 71c34e3615f44a4d9fd36687be3b468a) — seeded from origin/conductor/run-6d49d1e3979f (89865b1281); this run's worktree base c1785b22e5 predates ROADMAP.md; new ids continue at rm-026, no collision with rm-003..rm-025 pending merge in PR #13. Id renumbering (2026-09-23, integration 0bcfd799f38c, conflict case cee3b12d): this cycle-2 block landed via #17 AFTER run-fd2bc85f's cycle-1 block (#16), which had already taken rm-026..rm-029 — per fleet convention landed-first ids stay, so this block was renumbered: rm-026 (upstream v0.11.0 catch-up, same topic as fd2bc85f's rm-026) is FOLDED into that item below; rm-027→rm-040 (pyyaml bound), rm-028→rm-041 (skill-resolution), rm-029→rm-042 (updater sentinel), rm-030→rm-043 (sentinel SHA-pin), rm-031→rm-044 (dompurify). 2026-09-23 integration f7a1646564b14754962d030251e6caef: run 6efbf603's cycle-3 block (below) lands next and keeps rm-032..rm-039 as written — landed-first ids stay — with its vercel item renumbered rm-040→rm-045 because rm-040 is already taken by the landed pyyaml bound above; the earlier rm-034..039 reservation for the still-unlanded parallel run-edd9fb12 is released — run-edd9fb12 must renumber its pending items to rm-046+ at its landing gate (2026-09-23 integration 8aa9ed17d4d3: rm-046..rm-049 are now taken by run-634bf451's block below; run-edd9fb12 moves to rm-050+). 2026-09-23 branch landing (conflict case d321fccf04f64bb0823685fc80511095, integration item 53a38359bbca): this run's own conductor-landing branch (7544e6407a, candidate commit ad07e47441 = PR #17's head) merged into the integration tree at 4c054dd99d AFTER its batch content had already landed via the #17 squash 6bcfe9bb9a — zero tracked code/config files differ from the pre-merge tree outside this file, CHANGELOG.md, and pyproject.toml. Dispositions: ROADMAP resolves to the landed numbering above (orig rm-027..rm-031 = rm-040..rm-044 verbatim bodies with 'orig id' pointers; orig rm-026 folded into rm-026); CHANGELOG keeps the 0.11.0-section placement of the batch's four entries (byte-identical text already present — no duplicate Unreleased bullets); pyproject keeps `pyyaml>=6.0.3,<7` (rm-033's CVE-2026-31132 floor superseding the branch's `>=6,<7`) alongside `croniter>=2.0,<7`; the only new tracked content from the branch is its .conductor breadcrumb/prioritization records. No roadmap line, changelog entry, or dependency bound lost. -->

(folded 2026-09-23 at integration 0bcfd799f38c: run-684b9786's rm-026 'Catch up upstream v0.11.0 (supersedes the local PKCE test-repair path)' — reliability 110.0, candidate — was the same topic as fd2bc85f's landed-first rm-026 below; its unique signal detail (dual-SDK scope, Windows-portable token-store lock, security remediation bundle as the upstream-canonical fix for the 4 stale-PKCE failures, doctor JSON gateway.pid) is preserved in the target item's resolution line; 2026-09-23 integration f7a1646564b14754962d030251e6caef: run 6efbf603's roadmap carried this folded item forward with its own fresh verification — `git merge-base --is-ancestor 7795aa3ce8 HEAD` true at fork HEAD 5765b571b2, docs/gemini-spark.md in-tree, full serial suite green there incl. the formerly-stale PKCE tests — corroborating the implemented-on-master status on the target item below; the duplicate item is not re-materialized)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Land upstream v0.11.0 (dual SDK support, Gemini Spark profile, security remediation bundle)
- id: `rm-026` | track: compatibility | priority: 115.0 | status: implemented (adopted via #15 28c8754c21 + ancestry merge cd912844b5; independently verified implemented-on-master 2026-09-22 by run 6efbf603's roadmap — upstream v0.11.0 tip 7795aa3ce8 is an ancestor of fork HEAD 5765b571b2, PKCE tests green on that push, the local re-binds superseded by upstream adoption as this item required; see resolution)
- signals: conductor.run-fd2bc85f:research-R1, merge-base 9f537106e9..upstream/master 7795aa3ce8 = exactly 5 commits (#69 Gemini Spark OAuth client profile + verified custom-app setup guide, #70 README OAuth-note consistency, #71 release v0.11.0 — MCP SDK 2 first-class + Bot Chat + security remediation bundle, #72 release notes PUBLISHED with GitHub+PyPI live, #73 hero assets); fork is 0.10.0 while PyPI serves 0.11.0; upstream #71 security bundle (signed tokens require durable store, revocation retires+advances epoch in one SQLite txn, atomic refresh rotation, ledger watermark pagination) supersedes fork-local PKCE repair — catch-up SUPERSEDES local test repair
- acceptance: upstream 5-commit set merged or cherry-picked onto the fork line with oauth_auth.py/server.py conflict resolution reviewed line-by-line; full suite green in CI shape (HERMES_HTTP_TEST=1, serial, baseline interpreter) — including the 4 stale-PKCE tests, which must adopt upstream's remediated contracts rather than local re-binds; security remediation diff explicitly reviewed against fork invariants (Owner Mode break-glass, secret-path denials); version bumped to 0.11.0+ and CHANGELOG records the catch-up
- evidence: merge commit with conflict-resolution notes; green full-suite run post-merge; CHANGELOG diff; release/PyPI links recorded
- resolution (2026-09-23, integration 0bcfd799f38c, conflict case cee3b12d): FOLDED run-684b9786's same-topic rm-026 (reliability 110.0; 'supersedes the local PKCE test-repair path') into this landed-first item. LANDED via #15 (28c8754c21 content adoption) + ancestry merge cd912844b5: pyproject version 0.11.0, CHANGELOG `## 0.11.0 - 2026-09-21` section, docs/gemini-spark.md in-tree, stateless signed auth codes with the fail-closed empty-challenge guard (oauth_auth.py exchange). The B1 S256 re-binds (#16) are retained and adapted to the stateless-signed-code API — module helpers `_s256`/`_PKCE_VERIFIER` plus `test_exchange_rejects_code_without_stored_challenge`; both test files green at this integration on the baseline interpreter (HERMES_HTTP_TEST=1, 2026-09-23). (Folded 2026-09-23 at integration 8aa9ed17d4d3, conflict case 8aa9ed17: run-634bf4516c83's same-topic `rm-030` — written pre-adoption on base c1785b22e5 — is folded here, not re-materialized. Its unique requirement is preserved and still governs: PKCE-semantics reconciliation — the fork default stays fail-closed mandatory, and upstream #69's `require_pkce` opt-out is admissible only inside the Gemini Spark profile contract, with tests.)

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Re-baseline the repo-wide lint gate for ruff 0.15 default rules
- id: `rm-028` | track: maintainability | priority: 68.0 | status: candidate (premise revised 2026-09-23: ruff 0.15.10 with NO committed config returns ZERO findings repo-wide at HEAD 4b958379d6 — `ruff check .` and `ruff check --isolated .` both exit 0; the original 524-finding measurement does not reproduce on 0.15.10 defaults and must be re-attributed (expanded select/preview) before being treated as debt; the residual, real risk is that the enforced rule set is committed nowhere, so a future default change lands silently) (id note 2026-09-24 at integration b1b99c1422b848a3b738bb5ccaf9107e, conflict case 7177f0f2: git auto-adopted run 43fe028246d3's renumbering of this fd2bc85f duplicate to `rm-033`, which collides with landed-first `rm-033` above (run-6efbf603's pyyaml/manifest item) — the landed id `rm-028` is restored; the run's premise revision is kept; 2026-09-26 id note (integration 7fd1ba641af2, conflict case 536598c0): run e29c25913c00's roadmap carried the same rename to `rm-033` on its own earlier branch — the landed id `rm-028` is restored here too, and its observation that the ruff-0 sweep + repo-wide CI lint landed via PR #13 while the committed [tool.ruff] rule-set decision for 0.15 defaults remains open is absorbed by the premise revision above)
- signals: conductor.run-fd2bc85f:assess-F4, rm-017 (sibling) drove `ruff check .` 61->0 under the classic E/F default set and widened CI lint to repo-wide; but ruff 0.15.10 `--isolated` defaults now include UP/I/BLE/TRY/RUF classes — measured 524 findings at c1785b22e5 (server.py 48, token_store.py 21, oauth_auth.py 17, operator_policy.py 17), 184 fixable under 0.15; the post-merge gate will either silently enforce a different (larger) rule set or need a committed config that pins the intended set
- acceptance: a committed [tool.ruff] config declares the enforced rule set explicitly; decision recorded (adopt 0.15 defaults with a staged fix plan, or select the classic set); CI lint job passes under the pinned ruff (dev-extra already pins >=0.15,<0.16 per review-fix 711573d0); no unenforced class without a recorded decision
- evidence: config diff + green lint job; finding-count table before/after (61-era vs 524-era) with the disposition of each new class

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Resolve the 12 unresolved gitlink entries
- id: `rm-029` | track: maintainability | priority: 22.0 | status: implemented (zero 160000 gitlink entries at the integration HEAD verified 2026-09-23 — the 12 entries were resolved during the catch-up landings; CI unaffected, submodules:false; corroborated 2026-09-22 at fork HEAD 5765b571b2 by run 6efbf603's roadmap: `git ls-files -s | awk '$1==160000'` = 0 entries; folded 2026-09-23 at integration 8aa9ed17d4d3, conflict case 8aa9ed17 — run-634bf4516c83's same-topic `rm-026`, an independent parallel implementation that reproduced the 12-entry index state on the same base c1785b22e5 and cleared it (`git rm --cached`, final count 0), corroborates this item from a second run and is folded here, not re-materialized; its commit-message-vs-diff mismatch finding (c1785b22e5's message claimed the gitlink drop while its diff only deleted .gitmodules) is preserved as prevention rule 18 in that run's block below; plus run e29c25913c00's same-topic `rm-034` (renamed from this item on its branch) folded here 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0 — its independent verify at its HEAD 4b958379d6 (`git ls-files -s | awk '$1==160000'` = 0) is a third run's corroboration, and the landed id `rm-029` is restored over that rename)
- signals: conductor.run-fd2bc85f:assess-F9, `git ls-files -s | awk '$1==160000'` = 12 entries at HEAD (8x design-canon-*, 4x review-*) with no .gitmodules; this lineage's last three commits (c1785b22e5..) already fought individual unresolvable gitlinks in CI
- acceptance: either a .gitmodules mapping with resolvable URLs, or the 12 entries replaced by ordinary content/excluded; `git submodule status` resolves everything it lists; CI checkout (submodules:false) unaffected — proven by a green run
- evidence: git submodule status output; green CI run; diff

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Re-green master: remove the private-runtime cron.jobs import from hermes_cron_create
- id: `rm-032` | track: reliability | priority: 130.0 | status: implemented-on-master (resolved 2026-09-23 at integration f7a1646564b14754962d030251e6caef: the repair landed on master via PR #22 a93aeb0b1d 'fix(cron): self-contained schedule parser — drop hermes-agent cron.jobs import' — operator_cron.py carries the repo-local `_parse_schedule` with optional croniter and `croniter>=2.0,<7` is a declared dependency; that landing supersedes this run's staged repair (artifact retained at .conductor/patches/rm-032-cron-repair.patch as the pre-land record); the U1 guard test (test_no_private_runtime_imports.py) lands with this integration and stays in the suite forever)
- signals: conductor.run-6efbf603:assess-critical, origin/master 927680eb20 (converge merge 9a90620d5c, 2026-09-22 03:07Z) added call-time `from cron.jobs import parse_schedule` in hermes_cron_create (operator_cron.py:981 at tip 4b958379d6); cron.jobs exists only in the private Hermes agent runtime (/home/agent/.hermes/hermes-agent/cron/jobs.py) — clean installs get ModuleNotFoundError; all 9 CI test lanes fail 5 cron-create tests (runs 03:07–03:39Z all red; last green push 5765b571b2 01:41Z); reproduced both directions in a detached worktree at origin/master
- acceptance (CORRECTED 2026-09-22 by implement 07e9164d, superseding the research wording above): the landed master tests assert the STRUCTURED schedule dict (test_operator_cron.py cron-create family, incl. test_cron_create_scheduler_contract_model_fields), so persisting RAW strings would fail master's suite — the repair keeps the structured schema via a repo-local self-contained port of parse_schedule (durations, clock times, weekday phrases, 5-6-field cron, ISO once, 'in Nm'), drops the cron.jobs import, and keeps croniter OPTIONAL (not a declared dependency; structural field check when absent; 2026-09-23 integration note: the landed #22 repair satisfied the closure check the other way — declaring `croniter>=2.0,<7` while keeping the lazy optional-import fallback — see status). Remaining acceptance: patch lands on master tip; the 5 cron-create tests pass with cron unimportable (PROVEN pre-land); master CI green again (gate-side)
- evidence (pre-review): defect reproduced pre-patch (guard rule-1 FAIL; exactly the 5 CI failures with cron blocked); post-patch test_operator_cron.py 32/32 green with cron BLOCKED and importable; ruff clean; patch applies clean via git apply --check to pristine 4b958379d6; full serial suite at the patched tip 0 FAILED/ERROR (/tmp/rm032-full-07e9164d.log); prevention guard test_no_private_runtime_imports.py green at base and collected in the base full suite
- review record (cb7b68c3 PASS, 3 non-blocking; fixed in review-fix d871caf3 2026-09-22): F1 FIXED — the no-croniter structural branch silently accepted semantically-invalid expressions ('99 99 * * *', '0 9 * * 8', '61 24 32 13 *'); now folds a per-field numeric range check (minute 0-59, hour 0-23, dom 1-31, month 1-12, dow 0-7 — 7 is croniter's Sunday alias; names/wildcards skipped) into that branch; battery: 6/6 invalid rejected and 7/7 valid accepted with croniter BLOCKED, rejection parity with the native private parser with croniter present, cron family 32/32 both directions, ruff clean; regenerated patch (+216/-5) applies clean to pristine 4b958379d6. F2 DOCUMENTED HERE — naive ISO one-shots anchor to the HOST local zone (datetime.now().astimezone().tzinfo) where the native parser anchors to the configured Hermes zone (_hermes_now().tzinfo); identical on UTC hosts, latent wherever host zone != configured zone; also inline-commented in the patch — if zones can diverge in deployment, re-anchor to the configured zone at the gate or next cycle. F3 DEFERRED (next cycle, per reviewer scope): guard PRIVATE_RUNTIME_MODULES bans only 'cron'; enumerate the other non-colliding private-runtime top-levels (/home/agent/.hermes/hermes-agent) into the set — deferred because it edits the guard test, reserved for next cycle. F4 (info): the implement-phase patched-tip log was deleted in cleanup; this review-fix reran the patched-tip full serial suite fresh (/tmp/rv032-fix-full.log) — gate-side CI remains the authoritative closure.

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Land fork PR #19 (packaging consolidation + pyyaml CVE floor) and revive upstream PR #75
- id: `rm-033` | track: reliability | priority: 105.0 | status: implemented (rm-033a slice landed 2026-09-23 at integration f7a1646564b14754962d030251e6caef: pyproject `pyyaml>=6.0.3,<7` — flooring the #17 `>=6,<7` bound — plus the CHANGELOG CVE-2026-31132 entry; requirements*.txt deletion + PR #19 landing + upstream PR #75 rebase remain open at the gate; 2026-09-23 update at integration 8aa9ed17d4d3, conflict case 8aa9ed17: run-634bf4516c83's `rm-029` (install-manifest consolidation — the content of PR #19) folds here and its batch IS this landing — requirements.txt + requirements-dev.txt deleted, docs/mcp-compatibility.md and README dev-setup repointed to pyproject, .gitignore ps1 negation carried (rm-047 below); only the upstream PR #75 rebase on a green fork master remains open; 2026-09-24 update (run cbd4463370ee research eacc7a85): upstream #75 was rebased to head ff17df19 (2026-09-24T04:46Z) and its FIRST upstream CI run (35957083299) is queued — still pending at probe time; the maintainer's review requires five pre-merge fixes: untrusted-PR code off self-hosted runners (upstream still sees the pre-#21 workflows), build-deps restructure so the PR path still runs package build/twine/hygiene despite a skipped compatibility matrix, the pyyaml floor claim matched to the manifest (our side already carries >=6.0.3,<7), SCOPE REDUCTION from 50 commits/88 files to a focused packaging-only PR with the unrelated runtime/security/CI work separated, and a reviewed-SHA pin for the codeo1io/.github private-leak-sentinel workflow — closure now needs that scoped rework plus fresh green applicable checks, verified by head_sha, never PR number; 2026-09-26 fold (integration 7fd1ba641af2, conflict case 536598c0): run e29c25913c00's same-topic `rm-039` (unstick upstream #75) folds here — its research adds that CVE-2026-31132, cited in the PR #75/#19 bodies, is absent from OSV and GHSA, so the CVE justification must not be propagated into new roadmap/CHANGELOG text even though already-landed text keeps its historical claim)
- signals: conductor.run-6efbf603:research-C1, upstream PR #75 (head = codeo1io branch conductor/run-634bf4516c83 == fork PR #19): delete requirements.txt/requirements-dev.txt (strict-subset duplicates; our requirements.txt:5 bare pyyaml drifts), bound pyyaml>=6.0.3,<7 citing CVE-2026-31132 (fixed 6.0.3; pyproject.toml:20 `>=6,<7` admits vulnerable 6.0.2); upstream mergeable_state=blocked, ZERO CI runs on head 3a38d980; also resolves the assess finding on requirements.txt drift (docs/mcp-compatibility.md:97 cites it as equivalent)
- acceptance: pyproject pyyaml floor raised to >=6.0.3 (CVE note in CHANGELOG); requirements*.txt deleted with docs repointed to pyproject; PR #19 landed on repaired green master; upstream PR #75 rebased onto the landed state with >=1 green upstream run (verify via actions/runs?head_sha=, never by PR number)
- evidence: pyproject diff; green CI on the merge; upstream run URL filtered by head_sha; CHANGELOG CVE entry

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### CHANGELOG hygiene: fused bullet + Unreleased section for the converged features
- id: `rm-065` (orig `rm-041` in run-9e0b97f5d86c numbering; renumbered 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1) | track: docs | priority: 20.0 | status: implemented (run 9e0b97f5d86c cycle 1, 2026-09-23; landed 2026-09-24 at this integration merge, conflict case 1f53f9e34aa1; plus run e29c25913c00 `rm-041` folded here 2026-09-26 at integration 7fd1ba641af2, conflict case 536598c0 — the Unreleased section it called for is landed and gains that merge's three new entries; the fork-version-policy question resolved downstream-first riding upstream, v0.12.0 adopted)
- signals: conductor.run-9e0b97f5:assess-F8 — CHANGELOG.md:12 fused bullet ').- Support MCP Python SDK 2.x'; no Unreleased section for post-0.11.0 user-visible changes (DCR endpoint + knobs, event-loop offload of 6 tools, owner-command TMPDIR routing, JSON gateway.pid handling, croniter dependency at tip, CI runner move)
- acceptance: bullet repaired; Unreleased section enumerates the user-visible converged changes; AGENTS.md release-discipline review list satisfied
- evidence: CHANGELOG diff

*restore source: 6be3a5e95b^ (pre-collapse snapshot, definition-flattened class) — recovered verbatim 2026-10-03 by run dfaf334f988c (rm-195)*

### Sibling-landing sync — origin/master 97321194a8 (baseline drift during run dfaf334f988c)

Imported 2026-10-03 by run dfaf334f988c targeted_tests (attempt 7023656c): between this run's
implement phase (baseline e490130737) and targeted validation, origin/master advanced to
97321194a8 (run 61db9bce terminal-salvage landing + integration merge e40491ed93d5), which
minted the four ids below. Their definition lines are imported verbatim so this tree keeps
the rm-195/rm-139 invariant green: `tools/check_roadmap_ids.py --baseline origin/master`.
The landing-gate rebase onto the advanced master folds this block with master's original
blocks — keep exactly one copy of each id line when resolving.

- id: `rm-151` | track: reliability | priority: 105.0 | status: implemented (run 61db9bce cycle 2, implement 412d1e51, compound 34b85e5e; landed at integration e40491ed93d5 — orig id rm-131 in that run, renumbered at landing because landed rm-131 is the ui_ops cron-dispatch semaphore item; landed-first ids stay)
- id: `rm-152` | track: correctness | priority: 60.0 | status: implemented (run 61db9bce cycle 2, implement 412d1e51, compound 34b85e5e; landed at integration e40491ed93d5 — orig id rm-132 in that run, renumbered at landing because landed rm-132 is the cron next-fire/timezone preview item; landed-first ids stay)
- id: `rm-153` | track: security | priority: 45.0 | status: candidate (orig id rm-134 in run 61db9bce, renumbered at integration e40491ed93d5 because landed rm-134 is the fetch-metadata/content-type hardening item; explicit scope split from sibling b6659410's unlanded rm-114)
- id: `rm-154` | track: security | priority: 40.0 | status: candidate (orig id rm-135 in run 61db9bce, renumbered at integration e40491ed93d5 because landed rm-135 is the live-deployment provenance item)


<!-- managed by hermes-roadmap render; do not edit by hand -->
