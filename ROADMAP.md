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
- update 2026-10-03 (run e1e8d7ec research): mcp 2.3.0 released 2026-10-02 (PyPI JSON verified live; requires_python >=3.10) — this item's mcp==2.3.x-lane acceptance is now satisfiable and due; ci.yml:53-56 exact pins remain 1.28.1/2.0.0/1.30.0/2.2.0 (2026-09-07 vintage); pin-refresh scope consolidated into `rm-180` below (with the cryptography/starlette floor corrections)

### Ship or document a browser-UI build path (web assets absent from wheel/MANIFEST)
- id: `rm-077` | track: reliability | priority: 70.0 | status: candidate
- acceptance: EITHER the wheel/sdist carries a prebuilt web/dist (with a package-hygiene assertion), OR README + docs/operator-mode.md document the exact supported build step (npm ci && npm run build / HERMES_GPT_UI_DIR) verified to produce a served UI; tools/check_package_hygiene.py extended to match whichever path is chosen
- evidence: campaign-recorded in hermes-gpt ROADMAP.md
- update 2026-10-03 (run e1e8d7ec research): the decision this item gates is live in production — PyPI hermes-gpt still serves 0.12.0 (verified live) while the deployed operator runs 0.13.0+ (deployed checkout /home/agent/.local/src/hermes-gpt at 40a26a5378, describe v0.10.0-160-g40a26a5; canonical master now e490130737); pair with `rm-184` (fleet-card version literal) and the sibling fork-distribution decision rm-133 before any 0.13-numbered release

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

<!-- cycle-3 additions below: run e1e8d7ecd9324758bde91488537229b8 (assess b7837e73 ce-code-review mode:agent, artifacts /tmp/e1e8d7ec-assess + /tmp/compound-engineering/ce-code-review/20261003-051829-9743a493; research 249549b0 ce-ideate, /tmp/249549b0-research; roadmap f32188fb ce-work discipline, in-thread — no subagent tool in the delegate harness, disclosed, no independent-corroboration claims) authored 2026-10-03 against worktree HEAD 30de0067f9 (family repository-maintenance:e21b49a23c0749f083bc58c732391bd7:cycle:3). Fleet id census at mint (2026-10-03 07:1xZ, live): this tree's max id rm-140; sibling uncommitted blocks — run-ce3efdb4b6a3 rm-151..rm-162, run-9b1770fc3065 rm-163..rm-168 (its rm-169/rm-162 strings are text references, not id lines), run-f65169a1ce22 rm-169..rm-179 — fleet frontier rm-179, so new ids here start at rm-180; no on-disk id reused; render footer stays last. Canonical moved during this run: 58a70ddd5e (#27) landed rm-169's (a) catch — the 3.10 asyncio.TimeoutError fix — at master, and e490130737 (#28) landed an autopilot test; this worktree predates both (rebase at implement). -->

### Correct the sibling supply-chain floors: cryptography needs >=50 (not 49), starlette >=0.47.2, mcp pin refresh, hermes-agent checkout pin
- id: `rm-180` | track: reliability | priority: 95.0 | status: candidate
- signals: run e1e8d7ec research 2026-10-03 (OSV API, live): cryptography 44.0.0–49.0.0 carry GHSA-g6cj-pr64-35w5 / CVE-2026-69247 (HIGH CVSS:4.0 AV:N — Bleichenbacher oracle via distinguishable pkcs7-decrypt errors and timing; fixed ONLY in 50.0.0) while pyproject.toml:20 floors cryptography>=42; sibling rm-173 (run-f65169a1ce22, uncommitted) floors cryptography>=49 — 49.0.0 is inside the vulnerable range, so that floor is stale at mint and needs >=50 on merge; starlette floor >=0.40 (pyproject.toml:28) permits CVE-2025-54121 (multipart DoS; fixed 0.47.2; the resolver's current 1.7.0 is clean, the floor is the exposure); mcp 2.3.0 released 2026-10-02 (PyPI JSON verified) while ci.yml:53-56 exact pins remain 1.28.1/2.0.0/1.30.0/2.2.0 (2026-09-07 vintage) and rm-048's acceptance already requires a mcp==2.3.x lane; the NousResearch/hermes-agent checkout at ci.yml:120-121 has NO ref and their HEAD moved again this morning (bd0affe5e5, 2026-10-03T04:22Z — lane floats with their default branch); actions/checkout@v4 + setup-python@v5 vs latest v7.0.1/v7.0.0 (2026-07-20, verified live)
- acceptance: (a) cryptography floor >=50.0.0 with a comment naming GHSA-g6cj-pr64-35w5; (b) starlette floor >=0.47.2; (c) mcp exact-pin lane refreshed to 2.3.0 (satisfies rm-048's lane acceptance) with a spec-delta review note per rm-048; (d) hermes-agent checkout pinned to an explicit ref; (e) actions/checkout v7.0.1 + actions/setup-python v7.0.0; (f) landing gate reconciles this item's floors as superseding sibling rm-173's (>=49) values — no edit to the sibling tree
- evidence: pyproject.toml + ci.yml diff; OSV /v1/query re-run showing the new floors clean; green matrix on the refreshed lanes

### Complete the B4 non-ASCII token guard at the last unguarded site (validate_bearer_token)
- id: `rm-181` | track: reliability | priority: 70.0 | status: candidate
- signals: run e1e8d7ec assess-F10 — oauth_auth.py:1303-1307 validate_bearer_token feeds the raw Authorization header value to hmac.compare_digest without an ASCII guard; a non-ASCII bearer raises TypeError('comparing strings with non-ASCII characters is not supported') (runtime-proven 2026-10-03) and BearerAuthMiddleware (oauth_auth.py:1340+) has no except around the call, so a crafted non-ASCII bearer returns an unhandled 500 on every protected path in token-configured deployments (noise/log spam, no bypass); the identical B4 class was already fixed at oauth_auth.py:1444-1447 (authorize — 'Mirrors the B4 token-endpoint guard') and oauth_auth.py:1607+ (_authenticate_client) — the bearer path is the missed third site
- acceptance: isascii() early-reject (or TypeError guard) in validate_bearer_token mirroring the :1444 fix; regression test posting a non-ASCII bearer expecting 401 (not 500); existing auth tests stay green
- evidence: oauth_auth.py diff + new test; before/after curl-level repro captured in the implement phase result

### Regenerate .gitleaksignore from THIS repo's real findings (cross-repo copy-paste)
- id: `rm-182` | track: reliability | priority: 60.0 | status: candidate
- signals: run e1e8d7ec assess-F9 — 245 of 247 entries in .gitleaksignore reference paths that do not exist in this repository (tests/run_agent/*, tests/hermes_cli/*, tests/gateway/*, tests/agent/*, tests/tui_gateway/*, website/docs/* — the NousResearch/hermes-agent layout); an exists-check over every entry run 2026-10-03 found only AGENTS.md and README.md present; the file was committed by 72e743d7fe as 'ci: repo-local .gitleaksignore' — the allowlist was never generated from this tree, so it masks whatever this repo's real gitleaks output is
- acceptance: .gitleaksignore regenerated from this repo's actual gitleaks scan (removed if the real output is empty); a CI validation step asserts every allowlisted path exists in the tree (fails on dead entries, catching future cross-repo pastes); entry count drops to the validated set with the scan log archived
- evidence: gitleaks scan log + regenerated file; CI green with the new validation step

### Bound the fleet POST response read
- id: `rm-183` | track: reliability | priority: 55.0 | status: candidate
- signals: run e1e8d7ecd assess-F6 — operator_fleet.py:247 `_http_post_json` returns json.loads(resp.read().decode("utf-8")) with no size cap while the GET helper in the same file reads bounded; a hostile or compromised fleet peer can exhaust this process's memory with an oversized A2A response body
- acceptance: POST body read bounded by the same cap pattern as the GET helper; unit test with an oversized mocked peer response proving the cap trips; suite green
- evidence: operator_fleet.py diff + new test

### Repo truth micro-batch: drop dead test_verify.py, fix the fleet-card version literal
- id: `rm-184` | track: reliability | priority: 50.0 | status: candidate
- signals: run e1e8d7ecd assess-F16/F13 — test_verify.py builds C:\ Windows paths (test_verify.py:6), contains zero test functions, and is referenced by nothing (dead tracked scaffolding); server.py:3075 and :3117 default the fleet Agent Card version to '0.20.5' — no such release of this package exists — while versioning.VERSION is already imported at server.py:58 and pyproject.toml is 0.13.0; .conductor untracking is sibling rm-168 and is NOT duplicated here
- acceptance: test_verify.py deleted (or converted to a real cross-platform test if implement determines it guarded real behavior); fleet-card version default becomes versioning.VERSION; no remaining repo references to '0.20.5'; suite green
- evidence: diff + grep for the literal

<!-- cycle-3 refresh: attempt 41318c98983a4152a16c5fc2614744e7 (2026-10-03, same run e1e8d7ecd932, roadmap phase re-issued by the engine after attempt f32188fb; ce-work discipline in-thread). What changed since the 07:1xZ census: (1) FLEET ID COLLISION — run-df059aaeda574c589ff0d8c543ddc03a (campaign repository-maintenance:35ddabe6, roadmap attempt 79b3e882, 08:15Z) minted rm-180 "Consolidate the eleven per-module sqlite _connect helpers" and rm-181 "Dead-code census: retire or wire the seven zero-caller helpers" as a PATCH-ONLY ledger (/tmp/79b3e882-scratch/ROADMAP.ledger.patch, never applied to its own clean worktree), colliding with THIS tree's on-disk rm-180 (supply-chain floors) / rm-181 (B4 bearer). Resolution per the sibling's own marker: the landing gate merges sibling roadmap patches BY TITLE and renumbers the loser keeping titles; this tree's ids stand (on disk since 08:02Z and visible to worktree censuses, the sibling's are patch-only), so the gate renumbers df059aaeda57's pair to the next free ids at merge time — rm-189+ per the 08:35Z census, re-check at gate. (2) Fresh census 2026-10-03T08:35Z: fleet on-disk frontier rm-184 = THIS tree; run-f65169a1ce22 rm-179 (mtime 06:54Z), run-9b1770fc3065 rm-168, run-ce3efdb4b6a3 rm-162 unchanged; canonical /work/projects/hermes-gpt clean at e490130737, max committed id rm-140; no new sibling mints since 08:02Z. Ids rm-185..rm-188 minted below are collision-free against all five worktree ROADMAPs + the df059 patch, and title-level dedupe confirms no sibling item covers shared-workspace evidence contamination, the controller artifact twin, the token_store create-mode window, or the hygiene-test grandchild deadlock. (3) Digest correction: assess-F4 (autopilot stop dropped in the worker spawn window, operator_job_supervisor.py:519-527 vs operator_autopilot.py:1786-1790) maps to sibling rm-166 (durable cancel marker) — fold into its signals at merge, no new id. (4) Evidence extension for sibling rm-174: its acceptance should additionally cover the bare TitleCase name-pair heuristic at ui_security.py:216 (\b[A-Z][a-z]{1,30}\s+[A-Z][a-z]{1,30}\b → [redacted-name], which redacts ordinary English — "Mission Control Panel" → "[redacted-name] Panel", proven live by run-9037c3156272 assess ff09ba0a in operator status text) alongside rm-174's :207 phone/ISO patterns; fold a no-false-positive-English-title test into rm-174 at merge. -->

### Mission-scoped artifact evidence: shared workspace + basename-only matching lets nodes complete on foreign/stale evidence
- id: `rm-185` | track: correctness | priority: 92.0 | status: candidate
- signals: sibling run-73696bb0d3b1 assess 97df30ad (2026-10-03, runtime-PROVEN both cross-mission — mission B's node completed with mission A's file still present — and within-mission — node a2 completed on a1's same-named file — by /tmp/97df30ad-assess/probe_shared_workspace.py, reusable as a regression test; worktree at 40a26a5378 post-#26): every autopilot mission dispatches into ONE shared workspace (operator_autopilot.py:960 workspace=data_root/missions at 40a26a5378, operator_runners.py:661 workspace=workspaces[0]; the same shared-root design exists at THIS pre-#26 head at operator_autopilot.py:525 workspace=_data_root(hermes_root)) while every non-approval plan node declares the IDENTICAL default artifact basenames (operator_mission_plan.py:622 return ["work-contract.json", "evidence.json"]) and contract evidence matching resolves BY BASENAME with no mission namespace (operator_contract.py:599/:832 at this head; :799-830 at 40a26a5378); #26 (e490130737 lineage, NOT yet in this worktree) turned artifacts_present on by default, ACTIVATING this class at rebase time, and min_bytes is hardcoded 0 so empty files satisfy the check
- acceptance: artifact evidence is mission-scoped end to end — dispatch uses a per-mission workspace directory (or per-mission evidence subpath); contract evidence resolution keys on (mission, node, basename) instead of basename alone, with foreign and stale same-named files demonstrably NOT satisfying completion; plan-declared min_bytes honored (evidence.json defaults to a nonempty floor, not the hardcoded 0); probe_shared_workspace.py adapted as the regression test asserting both the cross-mission and within-mission contamination probes fail closed post-fix; test_operator_contract.py + test_operator_autopilot.py green
- evidence: operator_autopilot.py + operator_runners.py + operator_mission_plan.py + operator_contract.py diffs; adapted-probe output before (contamination PROVEN) and after (BLOCKED); contract/autopilot suite results

### Mirror the landed autopilot artifact contract in the controller reconcile path (twin defect)
- id: `rm-186` | track: correctness | priority: 85.0 | status: candidate
- signals: sibling run-af71b550d158 assess 3863d054 (2026-10-03, runtime-proven by /tmp/3863d054-scratch/probe_controller_artifacts.py; worktree at 40a26a5378): #26 fixed ONLY the autopilot twin — operator_controller.py _l2_work_contract still hardcodes `expected_artifacts: []` (:1510) and `artifacts_present: False` (:1515), BOTH verified present at THIS worktree's head too (2026-10-03), while plan nodes declare work-contract.json/evidence.json (operator_mission_plan.py:622): a controller-executed L2 node (hermes_controller_reconcile, server.py:2663; HERMES_GPT_CONTROLLER_EXECUTE=1) completes with artifact validation skipped, violating the product invariant "Work Contract completion is validated from observed state and fails closed when evidence is missing"; fix shape = the landed autopilot mirror (operator_autopilot.py:952-967 post-#26) + _read_node_requirement selecting expected_artifacts (operator_placement.py:842-862)
- acceptance: controller-path work contracts carry the plan node's declared artifacts; reconcile fails closed when declared evidence is missing; probe_controller_artifacts.py adapted as a regression test; controller + contract suites green
- evidence: operator_controller.py diff + new regression test; before/after probe output

### token_store: write secrets with 0600 from creation (close the umask-then-chmod window)
- id: `rm-187` | track: security | priority: 62.0 | status: candidate
- signals: sibling run-9037c3156272 assess ff09ba0a (2026-10-03): three write sites do tmp.write_bytes/write_text under the process umask and only then os.chmod(tmp, 0o600) — _write_key_file (token_store.py:122-133), the envelope write (:242-249), and the third site (:160-168) — so key/token bytes are briefly group/world-readable on disk; _secrets_dir's mkdir (parents=True, exist_ok=True, no explicit mode) leaves the directory at default umask; the correct primitive already exists in-file at token_store.py:326 (os.open(..., O_CREAT|O_RDWR, 0o600))
- acceptance: every secret-file write creates with mode 0o600 at open time (fd-based os.open write or equivalent — no write-then-chmod); _secrets_dir created with explicit 0o700 (idempotent for existing dirs); a test asserts the on-disk mode of each secret file immediately after creation under a restrictive test umask; token-store suite green
- evidence: token_store.py diff + new mode-assertion test; ls -l of a fresh hermes_root secrets dir captured in the implement result

### test_package_hygiene builds must die with their grandchildren (full-suite hang class)
- id: `rm-188` | track: reliability | priority: 58.0 | status: candidate
- signals: sibling run-9037c3156272 assess ff09ba0a F26 (2026-10-03, reproduced live): a full suite froze 43+ min at ~81% — the built_artifacts fixture (test_package_hygiene.py, subprocess.run python -m build, timeout=300) and the guard call in test_wheel_and_sdist_are_hygiene_clean (:195, timeout=120) kill only the direct child on timeout, while build's pip/setuptools GRANDCHILDREN inherit the stdout/stderr pipes, so communicate() blocks forever (classic grandchild-pipe deadlock); trigger confirmed: any concurrent python -m build (fleet lesson: never build while the suite runs) blows the budget under load and the lane hangs to the runner timeout; secondary same-track signal, distinct root cause: test_operator_autopilot_limits::test_real_worker_ends_a_run_that_is_out_of_time_with_nothing_in_flight failed once under load (23/23 focused green)
- acceptance: every subprocess.run in test_package_hygiene.py starts its child in a new session (start_new_session=True) with the timeout path killing the whole process group (os.killpg) or build output redirected to files so no pipe can be inherited-held; a deterministic regression test spawns a child that spawns a pipe-holding grandchild and asserts the timeout path returns within a bound; suite green
- evidence: test diff + new regression test timing out cleanly; no repeat of the freeze across subsequent full-suite runs


## Cycle 3 research digest — run e1e8d7ec (2026-10-03)

Research (ce-ideate, /tmp/249549b0-research): 28 raw candidates → 13 survivors → dedupe against sibling uncommitted mints rm-163..rm-179 and this file's rm-001..rm-140 → 5 new mints above (rm-180..rm-184), 8 covered by siblings (S1 trust middleware → rm-170, strengthen: CSRF probe re-proven at 30de0067f9 with /tmp/e1e8d7ec-assess/probe_csrf.py, reusable as its regression test; S2 3.10 retirement → rm-169, whose (a) catch is now LANDED at canonical 58a70ddd5e #27 — remainder is lane retirement + requires-python; S3 ROADMAP truth+guard → rm-175; S5 cron lock+next_run_at+schema → rm-171 (swarm-RMW re-read at HEAD still owed, sibling evidence predates the upstream merge); S6 turn-lease+Thread.start → rm-172 (fold ui_chat.py:493 tool_end status propagation into its scope); S7 redaction+audit → rm-174 + rm-177; S8 Flight Deck+reconnect → rm-176 + rm-178; S10 drift sentinel → rm-179, which can absorb rm-182's path-validation step on merge), 3 cuts (OAuth wildcard re-hardening — no fresh evidence at HEAD after canonical's B4 fixes; MCP/A2A spec upgrades — no movement: spec 2026-07-28, A2A v1.0.1; GitHub-issues enablement — owner policy), 1 conditional (upstream asimons81 PR #85 file-backups still OPEN 2026-10-03 — adopt only after upstream merge). Fleet census: frontier rm-179 held by run-f65169a1ce22 (mtime 06:54Z); canonical /work/projects/hermes-gpt clean at e490130737 (2 ahead of this worktree); no id collisions detected (9b1770's rm-169/rm-162 are references only).

Refresh (attempt 41318c98983a4152a16c5fc2614744e7, 2026-10-03): the phase was re-issued by the engine after f32188fb — the prior mint above is preserved verbatim; this pass adds rm-185..rm-188, all from runtime-proven evidence that postdates the 07:1xZ census: sibling run-73696bb0d3b1 assess 97df30ad (shared-workspace artifact-evidence contamination — the first fleet proof that #26's artifacts_present default ACTIVATES a contamination class), sibling run-af71b550d158 assess 3863d054 (the controller-path twin of #26, probe-confirmed), sibling run-9037c3156272 assess ff09ba0a (token_store umask-then-chmod window; F26 full-suite grandchild-pipe hang). Also recorded in the refresh marker above: the df059aaeda57 rm-180/rm-181 patch-only collision (gate renumbers per the sibling's own by-title rule — no renumbering performed in this tree), assess-F4 → sibling rm-166, and the rm-174 ui_security.py:216 name-pair extension. Canonical unchanged (clean e490130737); this worktree still predates #26/#27/#28 — rebase before implement.

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

<!-- managed by hermes-roadmap render; do not edit by hand -->
