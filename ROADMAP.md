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

### Offload /api/me + /api/connection status reads off the serving loop (rm-076 remainder)
- id: `rm-151` | track: reliability | priority: 105.0 | status: in_progress
- acceptance: both payloads' token-store reads execute off the loop (asyncio.to_thread or the in-file equivalent); regression test holds the token-store path blocked and asserts a concurrent lightweight async handler still completes (a sync TestClient cannot observe this — use the async test pattern rm-076's suite established); payload shapes unchanged; a note lands in docs/ui-security-boundary.md transport-health section that the poll endpoint is off-loop
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

### Correct hermes_mission_usage _24h keys — they previously reported all-time totals
- id: `rm-152` | track: reliability | priority: 60.0 | status: in_progress
- acceptance: usage rows joined/filtered by sessions.started_at >= cutoff with the schema-drift fallback the intent comment describes (missing started_at -> fail loud or explicitly-degraded output, never silently all-time); a new test with a stale pre-cutoff usage row asserted EXCLUDED from _24h sums; the baked test updated to a two-window fixture; full test_operator_mission.py green
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

<!-- cycle-3 additions (run 9037c3156272472abdb533396c66a368, roadmap attempt 8214aaaf86f6475cbacb70daf2b8258d, repository-maintenance:ebb00eda4cbb43c9b2877a78f678d852:cycle:3, 2026-10-03 ~13:29Z; insert-only, render footer stays last; supersedes transport-dead attempt 40e74fd4354f457fb0e935471f6fb6c7 — its typed artifact never landed and the worktree was verified clean at redo, so this attempt redid the phase from scratch). MINTED rm-207 ONLY (assess ff09ba0a finding F03, the single new P2 with no fleet owner after full title census); every other assess finding and all 5 research candidates folded to existing ids below. FLEET CENSUS at mint 13:28Z (artifact /tmp/8214aaaf-fleet-census.txt + re-sweep; first census 13:13Z said frontier rm-204 — the pre-write re-sweep caught sibling 9d66f0863ecf minting rm-205+rm-206 at 13:19Z in run-worktree 9d66f086, patch /tmp/71fae61f-scratch/ROADMAP.ledger.patch): committed-ledger frontier = rm-140 at BOTH base 30de0067f9 and origin/master e490130737; uncommitted worktree frontier = rm-206 (9d66f086 titles: 'Server shutdown lifecycle' + 'ui_chat turn-registry truthfulness' — no title overlap with rm-207); NO rm-207+ id: line exists anywhere (worktrees, campaign ledgers, /tmp patches; cross-repo rm- prefixes agenttrace/stonks/dashboard are NOT hermes-gpt census members); rm-196/rm-197 double-minted with distinct titles (e618b73f rm-197 = private-leak-sentinel pin vs campaign-278d0720 ledger rm-197 = assert invariants — cite by TITLE when landing); NEXT FREE after this mint = rm-208. Landing order append: ... a5bcf00e -> 1bc41b1b -> 71fae61f -> THIS PATCH, title-collisions lowest-id-wins.

FIXED-AT-MASTER CORRECTIONS (do NOT reopen as new items; assess ran at base 30de0067f9 which predates them): F11 (autopilot expected-artifacts completion gate) FIXED at origin/master by PR #26 (40a26a5378, artifacts_present) — rebase-only. F15's 3.10 WS TimeoutError half FIXED by PR #27 (58a70ddd5e, asyncio.TimeoutError catch) — rm-169 lane, rebase-only.

FOLD MAP for assess ff09ba0a's 28 findings (full detail + probes /tmp/ff09ba0a-assess/findings.json; suite re-proven green at base: [100%] 0 FAILED/ERROR per protocol #15805; sdist rc=0 with 0 web/assets entries; ids cited are FLEET ids from the union render, several absent from this file's rm-140 render): F01 P1 real-stack CSRF/Host/Origin proof (probe_realstack_csrf.py: server.build_server()+build_asgi_app(), foreign Origin+Host text/plain POST /api/ops/action -> 200 AND dispatches hermes_cron_create, while /mcp 400s 'Invalid Content-Type header') -> rm-170 (acceptance extension: real-stack ASGI-layer regression test, not a standalone mount; NOTE this render's rm-134 already landed 1bcb40c8 2026-09-29 and is PROVEN-INSUFFICIENT — the landed allowed_hosts/allowed_origins plumbing server.py:3312-3339 wraps the inner mount only, the outer /ui mount stays unguarded). F02 sys.path pollution + agent hermes_state SHADOWING repo module (probe_syspath_pollution.py RESULT=POLLUTION+SHADOW; operator_skill_resolution.py:173-176/:196) -> rm-193 (extension: acceptance must assert repo modules are never shadowed). F03 -> MINT rm-207 below. F04 redaction-config failure drops ALL redactions (pipeline must fail closed) -> rm-174. F05 TitleCase redaction eats dates/money (redact_browser live probe: 'Mission Control Panel' -> '[redacted-name] Panel'; 'order 12345.67 paid' -> 'order [redacted-phone] paid') -> rm-174 (its exact gap). F06 lock-less jobs.json (operator_cron.py:425-431) -> rm-171 (+rm-103). F07 next_run_at None on create -> rm-171. F08 unguarded Thread.start + never-renewed turn lease (ui_chat.py:747-749) -> rm-172 (+rm-200 acquire-atomicity; see also sibling rm-206 turn-registry family). F09 tool_end hardcodes ok (ui_chat.py:493) -> rm-177. F10 fleet POST unbounded read (operator_fleet.py:245-248 resp.read() before cap) -> rm-183 (extension: chunked read at the POST site too). F12 sdist ships 0 web/assets entries AND README hero blocklisted by tools/check_package_hygiene.py:94 -> rm-077 (+rm-083). F13 publish.yml self-hosted runner + mutable action tag -> rm-069 (+rm-165 actions-v7 lane). F14 unpinned hermes-agent checkout (ci.yml:123-131) -> rm-162 (+rm-173; both own agent pinning). F16 stale version literals '0.20.5'/'0.8' (server.py:3075/:3117, operator_fabric.py:2815) -> rm-184. F17 OAuth redirect string-prefix star (oauth_auth) -> rm-164 + rm-201. F18 test_verify.py Windows C:\ asserts -> rm-161 (+rm-184 delete lane). F19 ROADMAP evidence placeholder debt (91 rm-ids, 61 empty evidence stubs) -> rm-175 (+rm-163 render restore). F20 no [tool.ruff] section in pyproject -> rm-035 (extension: ruff dev pin >=0.15,<0.16 must bump to adopt 0.16.x). F21 token_store 0644 interim window (token_store.py:1365-1368 open-before-chmod; sidecars :1380/:1440) -> rm-086 tier-2 remainder ('0600-from-first-byte'). F22 finance request_id charset/length unvalidated at entry (finance_worker.py:297) -> rm-144 (extension). F23 bare asserts under python -O (operator_runners.py:1303, operator_swarm.py:466, operator_live_events.py:221) -> campaign-278d0720 ledger rm-197 'Replace production-path assert invariants with explicit failures (3 sites)' (title-cite; id collides with e618b73f rm-197). F25 ui_ops adapter audit defaults dry_run=True regardless of dispatch mode (ui_ops.py:141/:630) -> rm-177. F26 build-validation grandchild pipe hang (test_package_hygiene.py:170-184; reproduced: >=64KB grandchild stdout fills the pipe, suite stalls until a concurrent suite's child dies ~25min later) -> rm-188. F27 autopilot-limits wall-clock margins fail under concurrent suite load (test_operator_autopilot_limits.py:49-58; 23/23 green isolated) -> rm-188 (extension: poll-based waits/load-safe margins). F28 state.db co-ownership with the deployed agent clone, no lock/schema contract (hermes_state.py:79) -> rm-136 (extension: schema-version assert + single-writer contract). F29 pytest addopts '-q' DX note (pyproject.toml:178) -> optional rider on rm-035, no standalone item.

RESEARCH FOLDS (e63859b8, all sources live-queried 2026-10-03; /tmp/e63859b8-research/candidates.md — every candidate found a fleet owner the research-phase dedupe (its base ROADMAP ends at rm-140) could not see; NO research mint): C1 upstream PR #85 'configurable Operator file backups' (brunocasado 2026-09-30, complete default-preserving contributor work, open, vercel-bot-only comments; upstream/master 2e1884690258 IS ancestor of e490130737, fork 0 commits behind on master) -> rm-147 (watch item refresh: adopt-vs-defer now has a reviewable patch; overlap gate vs rm-087 backup capability stands). C2 A2A spec v1.0.1 (2026-05-28: a2a+json preference #1753, transcoding errors #1627, TaskStatus values #1801; pypi a2a-sdk 1.2.1) -> rm-203 (extension: TaskStatus vocabulary + spec cites; feeds rm-204 adopt-vs-build). C3 OSV floors fresh 2026-10-03 (starlette@0.40->14, cryptography@42->15, anyio@4.0->4; uvicorn@0.30/pyyaml@6.0.3/croniter@2.0/packaging@23 -> 0) -> rm-173 (floor refresh + automated advisory watch). C4 MCP python-sdk v2.3.0 (httpx2>=2.10, x-mcp-header InvalidSignature, empty _meta/params, max_sse_event_size; local 2.2.0) -> rm-048. C5 agent-loader integration contract (COMPAT_MANIFEST.md 1148 moved-lazy names; deployed clone @b8a0339ae9 2026-10-01 behind remote HEAD eb7e8620324b, that commit missing locally) -> rm-162 + rm-173 for the pin/record half; the deploy-probe + state.db schema-assert half -> rm-136 (with F28). C6 Python 3.10 EOL passed 2026-10-01 -> rm-169 (timing confirmation, escalate). C7 absent [tool.ruff] -> rm-035 (confirmation). NEGATIVE RESULTS (scope future phases away): upstream fork has ZERO commits beyond our origin/master except PR #85; codeo1io/hermes-gpt open issues = 0; hermes-agent remote HEAD unchanged since 08:11Z; uvicorn/pyyaml/croniter/packaging/mcp advisory-clean; no x-mcp-header/WithJsonSchema usage in-tree so SDK 2.3.0 registration-strictness cannot break tool registration.

COMPOUND REFRESH (compound attempt f1f472c0ed4f44bc98e1b2808a414657, 2026-10-05, docs/ledger-only — no test execution, all validation facts consumed from the recorded targeted/full envelopes): rm-207 flipped to implemented-validated-uncommitted (both gate envelopes + digest recomputation cited in its status line; zero fixes after implement). FRONTIER CORRECTION for the next mint: this block's 2026-10-03 'NEXT FREE = rm-208' is STALE — live re-census 2026-10-05 observed fleet max rm-216 at first sweep and rm-227 MINUTES LATER (the frontier moved intra-phase while this compound ran — run-40adb5bd1fe8 uncommitted mints rm-214/215/216; rm-217..rm-227 appeared in sibling worktrees between the two sweeps); NEXT FREE = rm-228 as of the final sweep, re-probe live immediately before writing. LESSONS + prevention rules + next-cycle context live in docs/maintenance-cycle-log.md new 'Cycle 13' entry (this tree's committed log frontier was Cycle 8; unintegrated sibling branches hold Cycle 9 d92e1ad3 / 10 e1e8d7ec / 11 dfaf334f / 12 73696bb0 — landing gate renumbers). Collision-partner follow-up: dropped batch partner rm-086 tier-2's duplicate work is committed at 65fb97510f on sibling branch conductor/run-a0f8eb89b525 (pushed, NOT yet in origin/master) — verify its 0600-from-first-byte coverage at integration and flip, do not re-implement. -->

### Operator profile isolation: set_hermes_home_override + HERMES_PROFILE mutations must not bleed across concurrent tool calls
- id: `rm-207` | track: security (profile isolation) | priority: 65.0 | status: implemented-validated-committed (landed on origin/master via conductor-landing b5c409bcb7 merged at 1ac2c592c4, tip pushed 2026-10-04T22:19Z; operator_profile_scope.py + test_operator_profile_isolation.py verified present at HEAD and the module shipped in pyproject py-modules inside hermes_gpt-0.14.0; flipped from implemented-validated-uncommitted by roadmap attempt fe151dc0157742859d42262faf3f64fd 2026-10-06 on assess 9907ac20 independent verification — concurrently flipped by sibling roadmap attempt 54e3a1fa on assess 988c9b7a F7 in the run-1dc1f85f36bd ledger; landing gate takes either). Prior provenance: compound attempt f1f472c0ed4f44bc98e1b2808a414657 recorded the validated outcome 2026-10-05; implement attempt 6903410479fc47b3a5de52cf23b42ec8 2026-10-04, worktree ff'd past the mandated e490130737 to origin/master c43d085121 with the mint preserved +13/0-; selected by prioritize attempt c68637fcdc4249c190fe6e331083455b 2026-10-03 ~15:05Z — batch 'Isolation & secret-path hardening under concurrency'; batch partner rm-086 tier-2 DROPPED as land-once duplicate of sibling run a0f8eb89b525's rm-187/rm-153 token_store work per coordinator-ratified collision escalation; hermes_state.py singleton prong deferred to the rm-105/106 lane per batch terms; VALIDATED 2026-10-04 with ZERO post-implement fixes: targeted attempt 4ae72259d7dc4c3f839888091e750fcd — the runner self-escalated to the authoritative full gate (pyproject.toml in FULL_IMPACT_FILES), envelope ~/.hermes/local-validation-gate/results/result-1988489-359778946.json (rc0, workers 1, 355.3s, 1821 passed + 5 skipped) — and full attempt eb7608b10f4547b8b95f756ce3c00fb3 ran the verbatim full command, envelope result-2896695-361289245.json (rc0, workers 1, 395.6s, IDENTICAL 1821P+5S outcome set = free determinism cross-check); focused 21-file lane 313P/1S (skip test_operator_workspace.py:221 Windows-only; the implement-phase environmental failure test_disabled_skill_rejected PASSED under the gate interpreter); ruff 0.15.22 clean over all 19 changed surfaces; envelope digest validation:v1:4fda5348… == recompute(base=None) and dispatch digest validation:v1:ab9136… == recompute(base=run-original 30de0067f9) — recomputation-verified again at compound 2026-10-05)
- acceptance: the process-global mutations Operator tool bodies use to scope a call to a profile become concurrency-safe for in-process parallel tool calls (sync tools already offload to worker threads on both SDK majors via the rm-074 seam): either a process-wide profile lock so no two tool bodies hold conflicting overrides simultaneously, or thread-scoped context plumbed explicitly instead of mutating shared globals; sites at minimum operator_fabric.py:78/:679/:1611 (set_hermes_home_override contextmanagers)/:1660/:2625/:2794/:2818-2819 (HERMES_PROFILE os.environ writes) and operator_skill_resolution.py:173-176/:196 (resolution under the override); hermes_state module-singleton state (hermes_state.py:79) is invalidated/rebuilt on override enter-exit so handles/caches are never reused across profiles; a regression test interleaves two simulated tool calls with different profiles (threads) and asserts each observes only its own home/profile end-to-end, including subprocess env captured at spawn; no profile-identifying material crosses into audit records (raw-prompt/audit invariants preserved); full pytest suite green at the landing base.
- evidence: run 9037c3156272472abdb533396c66a368 assess attempt ff09ba0a finding F03 (P2) — /tmp/ff09ba0a-assess/probe_skill_profile_bleed.py returns PROFILE_BLEED: True at base 30de0067f9 (two overlapping profiles observe each other's HERMES_PROFILE/home state); full detail /tmp/ff09ba0a-assess/findings.json. Dedupe (why a new id): rm-067's open env-mutation remainder is the _ensure_operator_tmpdir os.environ slice (same mechanism class, different sites and consequence — tmpdir staging, not profile data isolation; may be solved in one pass); rm-041 gates WHICH profile dispatches, not isolation; rm-136 declares the browser-UI agent-runtime seam but owns no in-process fix; rm-193 scopes sys.path only; no fleet title owns profile bleed (title census /tmp/8214aaaf-fleet-census.txt + /tmp/1b2d18ef-scratch/fleet-title-index.txt, re-swept for hermes_home/set_hermes/cross-profile/env-bleed/isolation phrases = 0 owners at 13:28Z). Landing note: rebase >= e490130737 first; aligns with rm-170's UI-boundary work only insofar as both harden the profile trust story — independent files, no ordering dependency.
- implement evidence (attempt 69034104 2026-10-04, base c43d085121): NEW shared-gate module operator_profile_scope.py (profile-keyed Condition gate: same-home holders overlap, different-home holders mutually exclusive, same-thread conflicting nesting raises ProfileScopeConflict instead of deadlocking; no logging, no registry) + operator_skill_resolution._profile_scope delegates via profile_override_scope (degradation contract unchanged) + operator_skills._call_skill_manager wraps its whole set->mutate->reset window in profile_override_gate (fail-closed non-default degradation preserved, covered by test) + pyproject py-modules ships the new module (wheel-built and verified SHIPPED). SITE CORRECTION vs this entry's acceptance cites: operator_fabric.py has ZERO set_hermes_home_override/HERMES_PROFILE hits at both 30de0067f9 and c43d085121 (stewardship forensics confirmed; real in-parent sites were exactly the two gated above; finance_worker.py:57 mutates env only inside its own child process; operator_session/operator_finance build per-call child-env dicts). Regression suite test_operator_profile_isolation.py (11 tests): sampling interleave through both repo paths + structural barrier exclusion + same-profile overlap preserved + nested-conflict raise + subprocess env captured at spawn is profile-pure and parent os.environ never mutated + no profile material in logs. RED PROOF: with the gate neutralized (/tmp/69034104-implement/redproof_plugin.py) the 4 bleed detectors FAIL with cross-profile homes observed, and PASS with the gate (non-vacuous). Focused validation: 64 passed across test_operator_profile_isolation.py + test_operator_skill_resolution.py + test_operator_skills.py + test_hermetic_environment.py + test_operator_session.py, plus ruff clean (pinned 0.15.22) — 1 pre-existing environmental failure test_operator_skill_resolution.py::test_disabled_skill_rejected (real-agent loader path needs httpx; venv has only httpx2) reproduced IDENTICALLY at HEAD with changes stashed, NOT introduced by this work; full-suite green at the landing base remains the landing gate's duty.

<!-- cycle-3 additions (campaign repository-maintenance:952725d79d8f40b48c5ac7f5c16a8540 cycle 3 — run a6a28ffeb5ba401ea8d1b66f4ce6ef32, roadmap attempt fe151dc0157742859d42262faf3f64fd, 2026-10-06; insert-only, render footer stays last; this campaign's first roadmap write on this render). Inputs: this run's assess 9907ac20 (16 findings; /tmp/9907ac20-assess swept by the tmp cleaner — durable envelope /home/agent/.hermes/conductor-delegate-spool/delegate/9907ac202bdd4f9ab1ec4688633f51ef.json) + research c04dded7 (/tmp/c04dded7-research/research-candidates.md + local-server-security.mdx, both still live at write). ZERO MINTS this update: the frontier re-probe at write time found sibling campaign 76d87684220c cycle 3 (run 1dc1f85f36bd, roadmap attempt 54e3a1fa) had just minted rm-318..rm-321 (uncommitted deliverable in worktree run-1dc1f85f36bd-1dc1f85f) from the SAME concurrent discovery pool — their F1/F2 (hygiene FP + skip masking) = this run's A1/A2 independently reproduced here (fresh python -m build, guard exit 1 'operational_metric: 207 profile' in wheel+sdist; fleet venv 23P/3S vs build venv 22P/1F); their F6 (profile READ-side bleed) = B1; their F4 (SDK-1 loop freeze) = B2; their research C2 (MCP local-server-security gap analysis) = this research survivor A. Every other assess finding and all 8 research survivors title-swept to an existing fleet owner below; minting again would only extend the duplicate families the landing gate already must reconcile. NEXT FREE = rm-322 (re-probe live before the next mint — the frontier moved intra-phase twice last cycle and moved once more during this one).

FRONTIER CENSUS at write (live): origin/master 1ac2c592c4 committed id-line max rm-207 (this file's render; committed prose also carries the historical rm-208/rm-228 NEXT-FREE notes — not mints); pushed branch max rm-314 (conductor/run-eaa40f1e21d6 @ c466c0a346); uncommitted worktree max rm-321 (run-1dc1f85f36bd: rm-318 hygiene/skip, rm-319 read-side bleed, rm-320 SDK-1 freeze, rm-321 MCP guide gap analysis); e7ca35a354fd holds rm-315/316/317; c6a4fd9256ab holds rm-299/297; owners whose worktrees are gone live on pushed refs: f65169a1ce22 (rm-169 Python floor + rm-173 advisory watch), e1e8d7ecd932 (rm-184 literals + rm-188 hang/timing class), 74896be4b661 (rm-193 sys.path), c5fba76a9e6c (rm-147 upstream watch), af71b550d158 (rm-203 A2A). rm-322 appears ONLY as the sibling's NEXT-FREE prose; rm-3xx numerals above that are agenttrace (rm-399) / dashboard (rm-382) ledgers — cross-repo, not hermes-gpt census members.

FOLD MAP — assess 9907ac20 (anchors independently re-verified at HEAD 1ac2c592c4): A1 CRITICAL hygiene OPERATIONAL_METRIC_RE false positive (operator_skill_resolution.py:197 'shared rm-207 profile gate' matches tools/check_package_hygiene.py:84-91; master CI red on push 37239574336 + nightly 37303778846 since 10-04T22:19Z) -> rm-318 (cite-by-TITLE 'Restore master CI green: package-hygiene operational-metric false positive + build-absent skip masking'); A2 HIGH build-absent pytest.skip masking (test_package_hygiene.py:184-193) -> rm-318 (its acceptance already demands the loud path); B1 HIGH profile READ-side bleed (server.py:658-691 skill_roots ungated / :877-911 skill_list absolute paths / :913-960 skill_view contents; rm-207 gated mutation side only; zero read-side tests in test_operator_profile_isolation.py) -> rm-319; B2 HIGH SDK-1 contradiction (docs/mcp-compatibility.md:6-7 vs server.py:1065 t=900 sync wait after #30 dropped the rm-074 offload wrapper) -> rm-320 + rm-313 (dated retirement, eaa40f1e21d6); B3 HIGH unconfigured-auth posture (oauth_auth.py:1355-1363 pass-through; server.py:3187-3190 websocket-authorized True; ui_security.py zero origin/host validation) -> rm-134 family — the fix ALREADY EXISTS uncommitted in worktree run-c6a4fd9256ab + branch conductor/run-c6a4fd9256ab-c84039892c: reconcile at landing, do not re-implement — with rm-321 owning the doc-first gap analysis against the merged MCP tutorial (453-line source saved /tmp/c04dded7-research/local-server-security.mdx: guide :322-327 normative Note 'Binding to 127.0.0.1 is not an authentication boundary' + :389-417 checklist; repo cites it NOWHERE today — rider on the rm-134/rm-321 landing: cite it as the normative reference in README/docs/operator-mode.md security prose); B4 HIGH delegation verdict cache (operator_delegations.py:733-763) -> rm-299 (removal exists in the same uncommitted c6a4fd9256ab batch); B5 MED approval_policy dead surface (operator_mission_runtime.py:278-333 typed+persisted, :87 mints, approve :1201-1240 ignores, zero consumers/docs) -> rm-312 + rm-315 (e7ca spec-versioning half); B6 MED ruff 0.16 gate-flip landmine (pinned <0.16 clean; 0.16.10 default selection = 502 findings) -> rm-035 rider; A3 MED autopilot wake-latency timing flake (test_operator_autopilot_wakeup.py:82 asserts < 3.0s wall-clock, observed 4.44s under concurrent sibling pytest -q -n 8 fleets; 5/5 isolated reruns pass 0.76-0.83s; mechanism verified correct — operator_live_events.py:334-336 0.25s condition poll) -> rm-188 extension (suite-load timing-fragility class, same fold as the earlier autopilot-limits margins; remedy: bound keyed off wait_seconds, not a fixed 3.0s wall clock); A4 MED bare-checkout UI-less artifacts (fresh build verified: 0 web members in wheel+sdist; only the CI flight-deck lane builds the bundled-UI wheel CHANGELOG 0.13.0 claims; sdist->wheel cannot reproduce the release artifact; no guard asserts UI assets; runtime degrades gracefully ui_security.py:101-116) -> rm-077 (its EITHER/OR acceptance fork is exactly this) + rm-083 (release-truth half); A5 MED unpinned agent-loader checkout (ci.yml:120-125 no ref: on NousResearch/hermes-agent, pip install -e :131; upstream tip 4787e4d56f 2026-10-06T01:20:46Z with the apps/ monorepo restructure standing; the new MCP guide checklist :395-397 now says 'version is pinned') -> rm-162 + rm-173 (+ the rm-278=289=297=307 pin family); B7 LOWs: stale literals server.py:3075/:3117 '0.20.5' -> rm-184; ci.yml:185 stale self-hosted npm comment -> rm-039; CHANGELOG lacks Unreleased despite #30/#31/rm-207 user-visible -> rm-308; cycle-log Cycle 8->13 renumber -> rm-139; windows axis docs-only (7 skipif marks / 2 files never run on a windows lane) -> rm-100 rider; B8 LOW process-global env family (operator_workspace.py:1100-1102 TMPDIR/TEMP/TMP writes; operator_skills.py:1043 raw sys.path.insert bypassing the _add_sys_path_once helper :173-190) -> rm-193 (sys.path hygiene) + rm-067 (tmpdir lifecycle remainder); rm-207 stale 'uncommitted' status -> flipped in place above (this update).

RESEARCH FOLDS (c04dded7, sources live-queried 2026-10-06T01:10-01:25Z): A MCP 'Local Server Security' tutorial (modelcontextprotocol/specification PR #3072 merged 2026-10-05T20:31Z, commits e85b7ae9/64533d09/8e12bf3c, under the still-current 2026-07-28 revision) -> rm-321 + rm-134 rider as above — upgrades the uncommitted rm-134 batch from internal audit finding to ecosystem-standard violation (evidence input for landing priority); B OSV 5th quiet window + NEW deployment-reality datapoint (fleet venv resolves starlette 1.3.1 / cryptography 50.0.1 / anyio 4.15.1 / mcp 2.2.0 — ALL OSV-clean at DEPLOYED versions; the 14/15/4 floor counts are resolver-theoretical, present in no live deployment) -> rm-306 evidence refinement (reword its driver from incident-response to contract-hardening; >=1.4 defensible-but-not-forced); C agent-loader urgency stays escalated -> rm-162 + rm-173; D pin-strategy refresh (fork tip 7403d41bf4 = fb2ee191b314 + 1 CI-only commit NOT touching hermes_state.py, so the rm-297 regex anchor :1190 is byte-stable; parse apps/shared/src/gateway-contract.openrpc.json at a pinned ref, never regex live upstream Python; the rm-297 test pin swap fb2ee191b314 -> 7403d41bf4 is a one-line SHA swap) -> rm-297 + rm-307; E Python 3.15.0 final imminent (v3.15.0rc3 tagged; 3.14.8 stable; 3.10 EOL passed 2026-10-01; pyproject requires-python >=3.10 at :11) -> rm-169 (add the 3.15 CI lane and make the floor-raise decision in the same change window); F packaging-test truthfulness -> rm-318 (skip-semantics half) + rm-077 (build-fork half); G upstream frozen (asimons81/hermes-gpt f50ded35ad, ~6th consecutive quiet window; PR #85 the only open PR, quiet since 09-30; ZERO open issues on fork AND upstream) -> rm-147; H quiet carries -> rm-048 (mcp 2.3.0 watch), rm-203/204/304 (a2a-sdk 1.2.2), rm-035 (ruff 0.16.10, no 0.17).

REJECTIONS this cycle (do not re-open): npm majors react19/zustand5/ts7/vitest5/rr8 — 4th consecutive rejection (lockfile-gated by web/package-lock.json + npm ci; only movers vite 8.3.2 and MCP TS SDK 1.32.1, both types-only with no in-tree consumer); Operator egress-allowlist capability; org fleet-management surfaces; remote-first hosting pivot (contradicts the local-sidecar product invariant); per-server scoped multi-token store (single-install static bearer + token_store already conforms); fastmcp 4.0.11 (framework swap); rate limiting / public telemetry / elicitation (spec quiet); server.py decomposition / agent code-health ratchet / sqlite busy_timeout (previously rejected, rm-136 owns the sqlite seam).

NEGATIVE RESULTS (scope future phases away): zero new PyPI releases across all 12 probed packages in 24h — quietest window of the campaign; only three ecosystem movers in 24h (MCP spec docs PR #3072; NousResearch/hermes-agent tip + standing restructure; the fork's 1-commit CI move fb2ee191b314 -> 7403d41bf4); verified-clean adversarial probes this assess: no shell=True/eval/exec/pickle/os.system in runtime, SQL parameterized everywhere (fabric_write_guard.py:31/:36 f-SQL is literal-fed only, not injectable), constant-time token compares, single bounded executor, skill_view traversal guarded, hermes_state.py carries NO premature rm-297 projection.

EVIDENCE EXPECTATIONS for the landing gate consuming this file's folds: (1) rm-318's fix rewords operator_skill_resolution.py:197 WITHOUT weakening OPERATIONAL_METRIC_RE and makes the build-absent skip loud — the first master push run after it goes green (37239574336 push + 37303778846 nightly are the red baseline; run the suite in a venv WITH build installed, fleet venvs cannot see these failures); (2) the rm-134 Host/Origin batch lands from run-c6a4fd9256ab's tree (do not re-implement) and its docs rider cites the MCP tutorial as the normative reference; (3) rm-319's regression test adapts the cedce0 probe shape to the READ path (two concurrent clients on different profiles, list/view observe only their own home); (4) reconcile the 9 duplicate-mint families cite-by-TITLE per the sibling cycle-4 directive (autopilot rm-271=282=294=309; floors rm-272=284=295=306; agent pin rm-278=289=297=307; swarm rm-274=285=300; finance rm-276=286=302; SSE rm-275=287=298; TLS rm-277=288=296; verdict cache rm-273=299; elicitation rm-281=305); (5) this update intentionally mints nothing — do not interpret the rm-318..321 citations in this comment as duplicates to renumber; they are cross-ledger references to the run-1dc1f85f36bd deliverable. -->

<!-- cycle-3 prioritize selection (run a6a28ffeb5ba, prioritize attempt 4b7fb9f40e9a4fe7abe526b931e0198a, campaign 952725d79d8f40b48c5ac7f5c16a8540:cycle:3, 2026-10-06; full matrix + scoring + exclusions in .conductor/prioritization-a6a28ffeb5ba.md, gitignored canonical path). SELECTED BATCH 'make green mean green: restore master CI signal + de-flake the suite's one known wall-clock flake' — (1) rm-318 (cross-ledger, cite-by-TITLE 'Restore master CI green: package-hygiene operational-metric false positive + build-absent skip masking', ledger run-1dc1f85f36bd, P128; this run's assess A1+A2 independent reproduction with fresh wheel+sdist build): operator_skill_resolution.py:197 docstring reword breaking the digit+profile adjacency WITHOUT weakening OPERATIONAL_METRIC_RE + unit test pinning the RE (old string matches, rewrite does not, synthetic real metric still matches) + LOUD build-absent path in test_package_hygiene.py:184-193 (env marker or hard failure pointing at pip install build). Gates: in a venv WITH build — python -m build + tools/check_package_hygiene.py dist/* exit 0 + test_package_hygiene.py live-green (3 built-artifact tests RUN); in the fleet venv the skip visible in one line of -rs output; the 'next push run green on all lanes' leg is landing-gate owned (red baseline: 37239574336 push + 37303778846 nightly, last green 37231139500). (2) rm-188 EXTENSION (suite-load timing-fragility class, F27 precedent): test_operator_autopilot_wakeup.py:82 — replace the fixed elapsed < 3.0s wall-clock bound with one keyed off wait_seconds (fixed_overhead + ~2x wait window), preserving the trigger-correctness asserts. Gates: 5/5 isolated passes; full suite green under ambient fleet load (observed 4.44s vs <3.0s under concurrent sibling -n 8 fleets this run); mechanism verified correct — operator_live_events.py:334-336 0.25s poll needs NO change. INTERLOCK (fresh sweep this attempt): ZERO dirty code surfaces fleet-wide — only six ROADMAP.md ledger deliverables dirty (1dc1f85f36bd, 40adb5bd1fe8, bd7f8ef7ddc1, a6a28ffeb5ba, e7ca35a354fd, facc0f13c2ed); run-c6a4fd9256ab's rm-134 batch now lives only on pushed branch conductor/run-c6a4fd9256ab-c84039892c. COLLISION WATCH: sibling campaign 76d87684220c cycle 3 minted rm-318 ~2h before this selection and may implement in parallel — an identical-fix race is a trivial land-once merge (rm-086 tier-drop precedent); do NOT drop the batch for it. EXCLUDED (reasons in matrix): rm-319/rm-320/rm-313 (sibling-active server.py M-effort, next-cycle leaders if untouched); rm-134 + rm-321 docs rider (fix exists on pushed branch — landing-gate owned, re-implementation banned); rm-162/rm-173 + rm-100 + rm-169 (effect visible only in CI runs — landing-gate riders on the rm-318 green work); rm-035 (own window: 502-finding ruff selection triage); rm-077 (M-effort node toolchain, next cycle with this run's fresh build evidence); rm-039/rm-184/rm-308/rm-139 (trivial truth riders for the landing gate); all in_progress labels (owned elsewhere by content); rm-001/rm-002 (standing programs); spec/SDK watch items (no external pull — quietest window of the campaign). HAND-OFF TO IMPLEMENT: verify-at-start HEAD 1ac2c592c4 + only ' M ROADMAP.md' (+ matrix untracked/gitignored); build a /tmp venv WITH build (fleet venv cannot see the 3 built-artifact tests); verify-at-end = all gates above + ruff clean on touched files + tree = batch diff + this run's ROADMAP additions; record implement evidence as an appended note under THIS comment (rm-318/rm-188 have no id-lines in this render — do NOT mint duplicates, do NOT touch sibling ledgers); landing gate owns final status flips + cite-by-TITLE reconciliation. -->

<!-- cycle-3 prioritize REVALIDATION (run a6a28ffeb5ba, prioritize attempt 95b9564a33c64c6596501fea7bda0f16, campaign 952725d79d8f40b48c5ac7f5c16a8540:cycle:3, 2026-10-06 ~09:25Z; supersedes ONLY the rm-318 leg of the 4b7fb9f4 selection comment above — revision section appended to .conductor/prioritization-a6a28ffeb5ba.md). CHANGED FACT since 07:59Z: sibling campaign 76d87684220c cycle 3 (run 1dc1f85f36bd) is LIVE-MID-IMPLEMENT of rm-318 — their worktree carries ' M operator_skill_resolution.py' (mtime 2026-10-06T08:45:38Z; the exact :197 reword 'shared rm-207 profile gate' -> 'shared profile gate (rm-207)', verified THIS attempt against the real guard: OLD string matches OPERATIONAL_METRIC_RE, NEW does not, so their leg-(a) fix is correct; RE-pinning test + skip-loudening legs not yet in their tree = mid-flight, not abandoned). Master CI still RED (re-verified: 37239574336 push 10-04T22:19Z + 37303778846 nightly 10-05T11:34Z, last green 37231139500 #31; origin/master unmoved at 1ac2c592c4). REVISED BATCH 'keep green honest: de-flake the one known wall-clock flake + land-once verification of the CI-green fix': (1) rm-188 EXTENSION (anchor, UNCHANGED from 4b7fb9f4, implement now): test_operator_autopilot_wakeup.py test_event_wakes_the_wait_early_and_moves_the_cursor_to_the_high_water_mark (~:82) — replace the fixed elapsed < 3.0s wall-clock bound with one keyed off the configured wait window, preserving reason=='event' + watermark asserts; gates 5/5 isolated passes + full-suite green under ambient fleet load + ruff clean. NEW interlock condition: re-sweep fleet worktrees BEFORE editing that file — zero dirty test files fleet-wide at this write; if run-1dc1f85f36bd's tree shows it dirty (their cycle-2 lineage owns rm-188 on pushed ref e1e8d7ecd932), re-scope this leg to verification-only and record. (2) rm-318 REVISED implement -> VERIFY-OR-FALLBACK per fleet land-once doctrine (rm-086 coordinator-ratified duplicate drop; this file's own rm-134 re-implementation ban — the maybe-collision of 07:59Z is now a live one, and a duplicate diff on the same two hot files from two concurrent campaigns is pure landing churn): at implement start record a live re-probe (run-1dc1f85f36bd tree + origin/master + conductor refs); while their rm-318 work is present/progressing, DO NOT duplicate — instead run rm-318's local acceptance legs against THEIR tree read-only from a /tmp build venv (python -m build --outdir /tmp/<attempt>/dist + tools/check_package_hygiene.py + test_package_hygiene.py with build present), record per-leg results as landing-gate evidence (this campaign's assess A1/A2 built exactly that venv shape; fleet venvs cannot see these tests — the A2 masking that let red master ship unremarked); touch NO tracked file for this leg. FALLBACK branch (only if their run is demonstrably dead AND nothing landed AND their tree reverted): implement the full rm-318 acceptance here per the 4b7fb9f4 text above. 'Next push run green on all lanes' stays landing-gate owned in every branch. Why not rm-319/rm-320/rm-321 as replacement implement items: same sibling campaign's cycle-3 mints while it is demonstrably mid-implement in this exact discovery pool — rebase risk strictly worse than the dropped duplicate; truth riders (rm-039/184/308/139) remain landing-gate riders. -->

<!-- cycle-3 implement evidence (run a6a28ffeb5ba, implement attempt fee01bccfeb749d88e3ccf04fefeee18, campaign 952725d79d8f40b48c5ac7f5c16a8540:cycle:3, 2026-10-07 ~00:35Z; evidence artifacts under /tmp/fee01bcc-implement/, logs in /tmp/fee01bcc-implement/logs/). U1 rm-188 EXTENSION LANDED in this tree (ADOPTION disclosed: dead prior attempt b71580de made the initial rework 2026-10-06T12:02:55Z — mtime-verified; attempts e92e7364/634a9f40/61a9733d provider-died without tree writes; this attempt verified the adopted edit then refined it: wait_seconds=10.0 bound once so the bound is structurally keyed off the configured window). Change: test_operator_autopilot_wakeup.py test_event_wakes_the_wait_early_and_moves_the_cursor_to_the_high_water_mark — split reason=='event' onto its own assert + replace fixed elapsed<3.0 with elapsed < wait_seconds + autopilot.WAIT_SLICE_SECONDS (slice=1.0, operator_autopilot.py:115 — one-slice overshoot headroom, same idiom as the abort test); watermark assert untouched; timer 0.3s / wait 10.0s untouched. Validation (focused lane per phase budget): 5/5 isolated green; whole file 23/23 green; 3/3 green under 4 concurrent CPU burners (worst single duration 0.46s; assess-era flake was 4.44s vs old <3.0); ruff clean; py_compile ok. Interlock re-sweep before adopt: test_operator_autopilot_wakeup.py dirty in ZERO other fleet worktrees; full-suite-under-ambient-load leg deferred to the full_tests gate per validation budget. U2 rm-318 VERIFICATION branch taken, fallback NOT triggered (re-probe at implement start 2026-10-07T00:33Z: sibling tree run-1dc1f85f36bd-1dc1f85f still carries its 8-file batch +470/-54 mtimes-unchanged since 09:58Z; origin/master unmoved 1ac2c592c4; their spool f926a6b9 attests the batch). Legs run read-only from /tmp/fee01bcc-implement tar copies (sibling tree never written; verified 8 files +470/-54 unchanged after): LEG-A red baseline HEAD tree in build-present venv — 1 FAILED test_wheel_and_sdist_are_hygiene_clean, guard flags '207 profile' in wheel+sdist (master-CI red reproduced, exit 1); LEG-B sibling tree same venv — 55/55 green ZERO skips, 3 built-artifact tests LIVE + 3 new RE-pin tests green (exit 0); LEG-C explicit python -m build per tree — head dist guard exit 1, sibling dist exit 0 CLEAN; LEG-D RE strength probe via their guard — 'processed 42 profiles' + '1,204 profiles' + the OLD :197 docstring all still match, the reword does not (guard unweakened; tools/check_package_hygiene.py byte-identical HEAD vs sibling); LEG-E fresh no-build venv (/tmp/fee01bcc-implement/nobuild-venv, pytest 9.1.1, build absent) — no marker: 3 LOUD failures each naming 'pip install build' (silent skip masking DEAD, exit 1); HERMES_GPT_HYGIENE_ALLOW_BUILD_SKIP=1: 3 explicit skips visible in -rs (exit 0). FACT CORRECTION for the landing gate: /home/agent/.hermes/hermes-agent/venv AND /work/projects/hermes-gpt/.venv both carry build 1.6.1 (installed 2026-10-01T02:27Z) — this run's assess claim 'fleet venvs lack build' is STALE as of this attempt; the local silent-skip masking window is closed for those venvs, CI lanes unaffected (their red was always the A1 false positive). Landing gate owns: first green master push run id after rm-318 lands + cite-by-TITLE reconciliation + status flips; no mints this phase, no sibling-ledger edits. -->

<!-- managed by hermes-roadmap render; do not edit by hand -->
