# hermes-gpt — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- upstreams (this repo builds on): hermes-infra; asimons81/hermes-gpt (true git upstream; 4 commits ahead as of 2026-09-21 — v0.11.0)
- dependents (changes here affect): (host)
- graph: evidence-derived (imports/refs/deploy surfaces); advisory

## Open items

### Add test coverage for 14 untested module(s)
- id: `rm-002` | track: reliability | priority: 100.0 | status: candidate
- signals: reliability.no_tests:web/src/chat/ActivityCard.tsx, reliability.no_tests:web/src/chat/ChatPage.tsx, reliability.no_tests:web/src/chat/Composer.tsx, reliability.no_tests:web/src/flight/AccountPanel.tsx, reliability.no_tests:web/src/flight/ApprovalsPanel.tsx (+9 more)
- acceptance: Every module in ['web/src/chat/ActivityCard.tsx', 'web/src/chat/ChatPage.tsx', 'web/src/chat/Composer.tsx', 'web/src/flight/AccountPanel.tsx', 'web/src/flight/ApprovalsPanel.tsx', 'web/src/flight/ContractsPanel.tsx', 'web/src/flight/DeckOverview.tsx', 'web/src/flight/EventHistoryPanel.tsx', 'web/src/flight/FleetPanel.tsx', 'web/src/flight/schemas.ts', 'web/src/shared/AccountStatusBanner.tsx', 'web/src/shared/ConnectionStatus.tsx', 'web/src/stores/session-list.ts', 'web/vite.config.ts'] has a corresponding test file with at least one passing test
- evidence: CI: pytest collects the new test files and they pass

### Refactor 21 high-complexity function(s)
- id: `rm-001` | track: reliability | priority: 90.0 | status: candidate
- signals: reliability.complexity_hot:*, reliability.complexity_hot:operator_contract.py::_check_forbidden, reliability.complexity_hot:operator_delegations.py::hermes_delegation_cancel, reliability.complexity_hot:operator_delegations.py::hermes_delegation_dispatch, reliability.complexity_hot:operator_delegations.py::hermes_delegation_reconcile (+16 more)
- acceptance: Each flagged function is decomposed below the branch threshold with behavior locked by characterization tests
- evidence: ast-based branch-count check passes in CI

### Restore green test suite — update 4 stale PKCE regression tests
- id: `rm-003` | track: reliability | priority: 99.0 | status: implemented (cycle-1 B1, attempt fb695253: all 5 empty-challenge sites fixed — 4 baseline-RED tests (rotates :361, post_revocation :515, exchange_fails_loud :823, startup_migration :985/:996) plus the 5th site in test_outstanding_code_dies_on_revocation, a negative test that had passed only accidentally (PKCE rejection masked its intended revocation-binding assertion); file 44/44, full suite exit 0 ×2; awaiting commit gate)
- signals: test.stale_pkce:test_codex_pr63_remediation.py mints code_challenge="" at lines ~363/515/796/823 and expects successful exchange, contradicting fail-closed mandatory PKCE at oauth_auth.py:477-479 and authorize-side enforcement at oauth_auth.py:982-997; ci.master_red:2026-09-20 run conclusion=failure; upstream master carries the same defect (5 empty-challenge sites)
- acceptance: the 4 tests mint a valid S256 challenge (verifier + _s256(verifier)) or explicitly assert invalid_grant for empty-challenge codes; `python3 -m pytest test_codex_pr63_remediation.py -q` exits 0; full `python3 -m pytest -q` exits 0 modulo environment-dependent skips; if the fail-closed contract is intentionally altered, docs + security note accompany it (default: tests-only change)
- evidence: pytest exit codes captured; green master CI run conclusion after commit/push gate

### Remove 12 dead gitlinks and correct the CI-fix record
- id: `rm-004` | track: reliability | priority: 96.0 | status: implemented (cycle-1 B1, attempt fb695253: 12 gitlinks staged-deleted; index 0×160000, `git submodule status` clean; clone smoke + truthful commit message pending commit gate)
- signals: `git ls-files -s | awk '$1==160000'` returns 12 entries (design-canon-* ×8, review-bench/compat/fixtures/qa ×4); every pin is unresolvable (`git cat-file -t` → missing); HEAD commit c1785b22e5 message claims the design-canon-adr002 gitlink was removed but `git ls-tree HEAD design-canon-adr002` still shows 160000 b0735fc7 (only .gitmodules was deleted); CI checkout uses actions/checkout@v4 default (submodules:false) so the claimed checkout-failure mechanism is unverified
- acceptance: `git ls-files -s | awk '$1==160000'` returns nothing; `git submodule status` exits 0 with no "no submodule mapping" errors; fresh `git clone --recurse-submodules` succeeds; commit message at the commit gate states the actual change (drop 12 unresolvable gitlinks; supersede the incomplete c1785b22e5 claim)
- evidence: command outputs before/after; clone smoke test result

### CI fast-lane — PR gate under 2 minutes, full suite on main + nightly
- id: `rm-005` | track: reliability | priority: 92.0 | status: implemented (cycle-1 B1, attempt fb695253: adopted PR #6's validated diff — nightly schedule, event-conditional PR single-lane, compatibility gated off PRs, npm-cache dropped; CI wall-time evidence pending merge + actions runs)
- signals: ci.wall_2h43m:PR #6 body — single self-hosted runner, 8 matrix lanes execute serially, web job 862s of which 820s was Post setup-node cache-save (warm npm ci is 7s); open PR #6 (+19/-13) implements the split; currently blocked by red base (master CI failed 2026-09-20)
- acceptance: .github/workflows/ci.yml restructured so pull_request events run a bounded <2min gate; push-to-main + nightly run the full matrix; cache-save waste eliminated or trimmed; no reduction in full-matrix coverage
- evidence: workflow diff; post-merge actions runs API shows PR-run duration <2min and main-run conclusions success

### Upstream v0.11.0 catch-up — Gemini Spark profile, Agent Card, gateway.pid fix
- id: `rm-006` | track: customer-experience | priority: 85.0 | status: candidate (next cycle headline)
- signals: upstream asimons81/hermes-gpt commits da39b19e8/3f32c67c8/b87a911cb/b20ab30b4 (2026-09-21) missing from fork HEAD c1785b22e5; PyPI serves hermes-gpt==0.11.0 while repo claims 0.10.0 (README.md:12-21); fork users cannot serve Google Gemini Apps connectors
- acceptance: upstream master merged (or equivalent cherry-picks) resolving oauth_auth.py/server.py conflicts with fork's CI-fix divergence; HERMES_GPT_OAUTH_GEMINI_ENABLE profile present, disabled-by-default with byte-identical single-client behavior, isolated secret + exact-match redirect allowlist; /.well-known/agent-card.json endpoint behind existing auth middleware; docs/gemini-spark.md included; full suite green; README/docs version claims updated to 0.11.0 keeping badge policy
- evidence: merge commit; pytest green; docs diff; connector verification notes carried from upstream release

### MCP SDK 2.2.0 CI lane + metadata-test skip guard
- id: `rm-007` | track: reliability | priority: 75.0 | status: implemented (cycle-1 B1, attempt fb695253: skip-guard in test_mcp_compat.py:81; mcp==2.2.0 floor pin added to full-matrix include; docs/mcp-compatibility.md floor/CI-coverage text updated in review-fix attempt 9a24beca; green 2.2.0 lane evidence pending merge)
- signals: pyproject.toml:16 allows mcp[cli]>=1.28.1,<3 but CI matrix floors are 1.28.1/2.0.0 (PR #66); PyPI mcp latest is 2.2.0 (supports spec 2026-07-28); test_mcp_compat.py::test_package_metadata_allows_both_sdk_families raises PackageNotFoundError on any source checkout without an installed distribution (no skip guard)
- acceptance: CI matrix includes an mcp==2.2.0 lane that runs the wire-level compatibility tests green; metadata test skips cleanly (with reason) when hermes-gpt distribution metadata is absent instead of failing; docs/mcp-compatibility.md floor table updated
- evidence: workflow YAML diff; green matrix run including the 2.2.0 lane

### Land PR #10 (solutions runbooks) and PR #11 (private-leak sentinel)
- id: `rm-008` | track: reliability | priority: 65.0 | status: blocked (needs green CI + maintainer merge)
- signals: open PR #10 (+184/-0, docs/solutions runbooks incl. mcp-cron-create-dead-jobs) and PR #11 (+3/-0, full-history gitleaks sentinel); both branch CI runs failing on the red base (2026-09-20/21)
- acceptance: PR #10 merged with docs/solutions indexed from docs/README.md; PR #11 merged with the sentinel job green on full history
- evidence: merged_at timestamps; green sentinel run URL

### PyPI vs repo version drift guard
- id: `rm-009` | track: reliability | priority: 55.0 | status: candidate
- signals: README.md:12-21 defers to the PyPI badge; PyPI latest_version 0.11.0 vs repo 0.10.0 with no automated check; upstream owns trusted publishing of the name
- acceptance: a CI job or release-checklist step queries PyPI and reports/fails on unacknowledged divergence ≥1 minor; RELEASE_CHECKLIST.md references it
- evidence: job log output showing the delta check

### Upstream the shared PKCE-test and gitlink fixes to asimons81/hermes-gpt
- id: `rm-010` | track: ecosystem | priority: 45.0 | status: candidate (depends on rm-003/rm-004)
- signals: upstream master still carries code_challenge="" at 5 sites (lines 361/515/796/823/975 of its test_codex_pr63_remediation.py); upstream has 0 open issues and historically broken CI visibility
- acceptance: fork→upstream PRs opened for the PKCE test fix and dead-gitlink cleanup; referenced from the fork commit messages
- evidence: upstream PR URLs

### MCP-native subscriptions/listen surface (spec 2026-07-28)
- id: `rm-011` | track: customer-experience | priority: 35.0 | status: candidate (design-first)
- signals: spec 2026-07-28 replaces HTTP GET + resources/subscribe with subscriptions/listen (SEP-2575); repo already ships a bespoke durable live-events cursor + /events/ws; SDK 2.x speaks the new spec via mcp_compat.HermesMCP
- acceptance (if accepted): SDK2-only opt-in subscription surface with subscriptionId tagging proven by a wire test; no behavior change when disabled; mcp-compatibility.md documents it
- evidence: new compatibility test passing on both SDK families where applicable

### Parallel-safe dev tooling — declare pytest-xdist and de-flake the timing/load flake class
- id: `rm-012` | track: reliability | priority: 70.0 | status: candidate (next cycle)
- signals: `uv run python -m pytest -q -n 8` fails twice as written — dev deps are optional-dependencies (pyproject.toml:24-25, needs `--extra dev`) and pytest-xdist is declared nowhere; repo CI runs serially. Under `-n 8`, test_operator_fabric_g4c.py::test_definite_launch_failure_after_cancel_terminalizes_and_allows_retry failed 1-of-2 full parallel runs on the loaded shared runner while passing serially and file-parallel (logs /tmp/tt-204fe351-full*.log, attempt 204fe351); same-class second flake: test_operator_delegations.py::test_concurrent_exact_cancel_coalesces_while_confirmed_cancellation_runs[True] (:1236, 'assert not first.is_alive()') failed in the assess baseline full run (/tmp/pytest_full2.log, attempt 9b7c49f7) while passing 3× serially (review attempt b7ffd53a); third member found during the review-fix retest (attempt 9a24beca): test_codex_pr63_remediation.py::test_rotation_and_issuance_are_serialized (:1221, 'issued token unreadable after concurrent rotation' at :1288) failed 2-of-3 full -n 8 runs under machine load while passing serially, file-parallel, solo, and on the rerun — test is baseline code, untouched by B1's diff (last hunk ends :992)
- acceptance: pytest-xdist listed in dev extras; `uv run --extra dev python -m pytest -q -n 8` exits 0 on three consecutive runs; all three timing-sensitive tests (g4c launch-failure-after-cancel; delegations exact-cancel coalescing; pr63 rotation/issuance fencing) pass under -n 8 on three consecutive runs (timing tolerance, worker pinning, or race elimination); CI optionally adopts a parallel lane if wall-time still hurts
- evidence: pyproject diff; three green -n 8 run logs

### Reconcile open PR #6 after the fast-lane lands
- id: `rm-013` | track: reliability | priority: 60.0 | status: blocked (needs B1 merge + maintainer)
- signals: cycle-1 CU-4 adopted PR #6's diff essentially verbatim (fetched from pull/6.diff) while PR #6 remains open (+19/-13); two copies of the same design will diverge on the next ci.yml edit
- acceptance: after the B1 commit/push/PR gate merges the fast-lane, PR #6 is closed-as-superseded (or rebased to no-op) with a cross-referencing comment; ci.yml has exactly one owner of the matrix-split idiom
- evidence: PR #6 state transition + comment link

## Cycle 1 learnings — prevention rules

1. **Security-contract changes must sweep their tests.** The PKCE-mandatory change (commit 26ed7b4c0d, 2026-08-31) landed without updating test_codex_pr63_remediation.py, leaving 4 tests red for ~3 weeks while a 5th empty-challenge site — a negative test — kept passing only accidentally (PKCE rejection stood in for its intended revocation-binding assertion). Rule: when flipping an auth gate fail-closed, grep the test suite for the old permissive expectation and update in the same commit; make negative tests assert the intended rejection reason.
2. **Gitlink surgery is index surgery.** Deleting .gitmodules alone (c1785b22e5) leaves mode-160000 entries that `git submodule status` still chokes on. Rule: submodule/gitlink removal = `git rm --cached` entries + .gitmodules entry + a commit message stating the actual change; never let a commit message claim an effect verifiable false at its own HEAD.
3. **Single-runner CI needs event-conditional lanes.** 8 serial matrix lanes made the PR gate 2h43m; `cache: npm` on a persistent self-hosted runner is negative value (820s round-trip vs 7s warm npm ci, run 35150442933). Rule: PR = one bounded lane, full matrix on push/nightly; drop actions/cache where the local filesystem already persists.
4. **Adopt validated open-PR diffs, then reconcile the PR.** CU-4 took PR #6's reviewed fromJSON matrix-split verbatim instead of writing a divergent second implementation — and rm-013 now tracks closing that PR so one owner remains.
5. **Re-derive counts by running, not by reading the ticket.** The work order said 4 stale tests; running revealed 5. Rule: batch acceptance is measured against live pytest output, not the planning estimate.
6. **Don't assume parallelism the repo never declared.** `-n 8` needs pytest-xdist (undeclared here; CI is serial) and `uv run` needs `--extra dev` because dev deps are optional-dependencies. Rule: adopt a parallel test command only after declaring the plugin in dev extras and proving stability on a loaded machine.
7. **Source checkouts need skip-with-reason, not failure.** test_mcp_compat.py's metadata test now skips when the distribution isn't installed instead of erroring — assertions stay intact for real installs.

## Cycle log

- 2026-09-21 · run c1ef27c97ab2 (cycle 1): rm-003..rm-011 added from assess (attempt 9b7c49f7fe4b4d4dbf05971c49cbe20e) and research (attempt cd8d31463ed94a4182ddd2f13e419dd5) artifacts; rm-001/rm-002 preserved verbatim from fleet sync 2026-09-20; fleet-context upstream line corrected to include asimons81/hermes-gpt. Cycle-1 implementation batch selected by prioritize (attempt d0b65ae5a34442248984a54d41a6ab87): rm-003, rm-004, rm-007, rm-005 — "Green Suite & Clean Index"; rm-006 deferred to next cycle as headline.
- 2026-09-21 · run c1ef27c97ab2 (cycle 1, compound attempt 5b00a823): B1 implemented in worktree (attempt fb695253) and validated (attempt 204fe351): baseline 6 failures → 0 (4 stale-PKCE red + test_mcp_compat metadata + the delegations cancel flake; /tmp/pytest_full2.log; full `pytest -q` exit 0 ×2 serial; `uv run --extra dev --with pytest-xdist pytest -q -n 8` exit 0 with one transient g4c parallel flake, classified and rerun-green); stale-site truth: 4 red tests + 1 accidentally-passing site, all 5 fixed (review attempt b7ffd53a corrected the narrative); 12 gitlinks staged-deleted; ci.yml fast-lane + mcp==2.2.0 pin in place. Statuses flipped to implemented (pending commit gate — nothing committed yet). New items: rm-012 (pytest-xdist + g4c de-flake), rm-013 (close-as-supersede PR #6). Prevention rules recorded above from cycle evidence only (no review outcomes yet — review/shipping happen after this step).
- 2026-09-21 · run c1ef27c97ab2 (cycle 1, review-fix attempt 9a24beca, completing interrupted attempt bc48b8d4): independent review b7ffd53a APPROVED for the commit gate with 6 doc/accuracy findings — all actionable ones fixed: docs/mcp-compatibility.md CI-coverage/floor text (rm-007 doc clause closed); rm-012 extended to the cancel-timing flake class (adds test_operator_delegations.py:1236); rm-003 status + learning 1 corrected to 4-red/1-accidental; cycle-log baseline count fixed to 6; all four B1 surfaces staged together (index was gitlinks-only — a bare commit would have shipped a red-suite split batch; per-unit commits still preferred at the gate); render trailer reconciled; 12 empty gitlink dirs removed from disk. Review INFO items remain recorded as accepted tradeoffs (nightly/master concurrency sharing; PR-lane matrix deferral; pre-existing ruff errors in pr63, file absent from CI lint list).

<!-- Hand-maintained under conductor run c1ef27c97ab2 since 2026-09-21 (status flips, rm-012/rm-013, prevention rules, cycle log). Fleet renders must seed from this file's current state, not overwrite it. -->
