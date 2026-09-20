# hermes-gpt — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- upstreams (this repo builds on): hermes-infra
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

<!-- cycle-1 additions below: run a51c0f6cb5b04ea9855a3dc3aba88c78 (assess ae925afb81c5, research bcf738fbc5) -->

### Re-green master CI: replace 4 failing + 1 vacuous PKCE-contract tests
- id: `rm-003` | track: reliability | priority: 120.0 | status: implemented
- signals: conductor.run-a51c0f6c:assess-F1, tests stale contract: test_codex_pr63_remediation.py:348,356,492,812,941 issue codes with code_challenge="" then expect exchange success vs oauth_auth.py:477-479 mandatory-PKCE fail-closed (26ed7b4c0d via merge cb8c6fed03 2026-09-13)
- acceptance: the four failing tests (test_revocation_rotates_authorization_code_key, test_post_revocation_fresh_exchange_persists, test_startup_migration_preserves_positive_legacy_epoch, and test_exchange_fails_loud_when_persistence_fails — previously passing vacuously because the empty-challenge gate raised invalid_grant before its injected persistence failure) mint real S256 challenge/verifier pairs and pass; a new test asserts an empty-challenge code is always rejected at exchange (fail-closed contract stays); python -m pytest -q is fully green locally and the next master CI run passes
- evidence: cycle-1 implement (2026-09-21, attempt b2f5ddda): all five stale tests re-bound to real S256 pairs + new empty-challenge-rejected test (test_codex_pr63_remediation.py), full local suite 1438 passed/6 skipped/0 failed (Py3.11) and 1442/2 (Py3.13 uv env); REMAINING for acceptance: green master CI run (review/merge pending) to unblock publish.yml

### POSIX audit-log home, failure surfacing, and bounded retention
- id: `rm-004` | track: reliability | priority: 95.0 | status: implemented
- signals: conductor.run-a51c0f6c:assess-F2+F5, operator_policy.py:46-47,772-783 (Windows-only default, POSIX falls back to package dir; HERMES_HOME ignored), operator_policy.py:874-878 (OSError swallowed -> silent audit loss), operator_policy.py:880-903 + operator_diagnostics.py:1305 + operator_fabric_view.py:523 (full-file parse, no rotation), docs/operator-mode.md:435 documents Windows path only
- acceptance: audit_log_path() resolves under HERMES_HOME/logs on POSIX (normalize_hermes_data_root pattern) with tests; audit write failures become visible via an operator diagnostics counter (tool calls still never break); size-capped rotation with a reverse-read bounded tail; docs/operator-mode.md documents the POSIX path
- evidence: cycle-1 implement (2026-09-21): operator_policy.py dynamic candidate paths (HERMES_HOME -> AppData -> ~/.hermes -> package dir), audit_write_diagnostics() + doctor WARN AUDIT_WRITE_FAILURES, 5 MiB single-generation rotation, 512 KiB bounded tail, rotation-spanning task reconciliation; docs/operator-mode.md documents all four levels; 6 new tests green in both local envs; fabric_view surface untouched this cycle (operator_fabric_view.py:523 still full-parse — fold into next rotation work if it reads audit history)

### Protect master with required CI checks
- id: `rm-008` | track: reliability | priority: 85.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F3, gh api repos/codeo1io/hermes-gpt/branches/master/protection -> 404 "Branch not protected"; merges #66,#67,#5,#7 landed 2026-09-13..20 on red master (4 consecutive failing runs, latest 35480822047)
- acceptance: master branch protection requires the CI workflow's test (and ruff) jobs plus linear history; direct pushes restricted to admins
- evidence: gh api branches/master/protection returns required_status_checks contexts; a red PR cannot be merged (observed once)

### Intentional MCP SDK coverage: pin current lines + protocol-revision assertion
- id: `rm-009` | track: reliability | priority: 80.0 | status: implemented
- signals: conductor.run-a51c0f6c:research-R3, .github/workflows/ci.yml:24-37 exact pins mcp==1.28.1/2.0.0 while 1.30.0+2.2.0 shipped 2026-09-07 (pip index; pyproject admits >=1.28.1,<3); SDK 2.1/2.2 behavior changes unasserted (exception-text hiding #3314, 4MiB OAuth body cap #3336); test_mcp_sdk_migration.py:109-110 already pins 2026-07-28 _meta keys
- acceptance: CI matrix adds explicit mcp==2.2.0 and mcp==1.30.0 lanes (or refreshes pins each cycle); a spec-revision assertion test fails loudly when the installed SDK advertises a protocol revision differing from the one hermes-gpt's tests pin; audit note confirms no hermes tool relies on exception text reaching clients and OAuth endpoint bodies are within 4 MiB
- evidence: cycle-1 implement (2026-09-21): ci.yml adds explicit mcp==2.2.0 and mcp==1.30.0 lanes; test_sdk_protocol_revision_is_deliberate asserts LATEST_PROTOCOL_VERSION=='2026-07-28' under SDK 2 (legacy set under SDK 1) and passes locally on SDK 2.0.0; REMAINING for acceptance: green run on the two new CI lanes + 2.1 behavior-change audit note (exception-text hiding #3314, 4 MiB OAuth body cap #3336)

### Root-cause CI-load-only test failures (rotation fencing, delegation reconcile)
- id: `rm-010` | track: reliability | priority: 70.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F4, CI run 35480822047: test_codex_pr63_remediation.py:1208 test_rotation_and_issuance_are_serialized failed on mcp==2.0.0 lane ("issued token unreadable after concurrent rotation") and test_operator_delegations.py:243 test_mission_completion_rejects_concurrent_reconcile_authority_change[reconcile] IndexError on 3.10 lane; both pass locally on rerun
- acceptance: both tests pass across 10 consecutive CI runs (or under pytest -n 8 load locally); root cause documented (real race fixed, or flaky assertion hardened) — blanket retries/skips do not close this item
- evidence: gh run list showing 10 consecutive green master runs post-fix; a written root-cause note in the PR description or docs

### Session-jobs retention and watcher cleanup hardening
- id: `rm-005` | track: reliability | priority: 60.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F6, operator_session.py:156,193 (only failure paths unlink), session-jobs/*.json|txt grow unboundedly, hermes_session_job_status _reconcile (operator_session.py:278-294) full-globs the dir per call, _watch (operator_session.py:211-228) skips _processes/_active_sessions cleanup if proc.wait raises a non-timeout error -> permanent SESSION_BUSY
- acceptance: retention policy (age/count cap, documented env knob) prunes session-jobs; _watch cleanup runs in finally for all exception types with a regression test that injects a wait error and asserts the session returns to idle
- evidence: pytest regression test for the injected wait error; a test or docs note proving pruning under volume

### Exact money math in the mission budget ledger
### Configurable audit retention with rotation-loss visibility
- id: `rm-015` | track: reliability | priority: 55.0 | status: candidate
- signals: conductor.run-a51c0f6c:review-F2, operator_policy.py:55,843,1009 — single-generation 5 MiB rotation bounds the evidence window for iter_audit_for_task (feeds fabric forbidden-action signals + task reconciliation via operator_fabric.py:1756); records older than two windows vanish silently (false-negative violation signals, not just lost history); caps hardcoded, no operator knob, no rotation-loss indicator
- acceptance: retention cap configurable via operator setting/env; iter_audit_for_task (or its fabric consumer) emits a reconcile-time warning when the archive boundary falls inside a task's lifetime; doctor surfaces rotation-loss state
- evidence: tests covering configurable cap + boundary warning; fabric signal collection proven unchanged when history fits the window

- id: `rm-006` | track: reliability | priority: 50.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F8, operator_mission_budget.py:96-115 (SQLite REAL columns), :270-296 exact spend >= quota crossings, :62-64 caps 1e12; usd/minutes units accumulate binary-float drift
- acceptance: quota/spend/amount stored as integer micro-units (or Decimal with fixed context) with exact comparisons; migration path for existing ledgers; property test asserting identical crossing decisions across orderings of 10k tiny increments
- evidence: property test passes; existing ledger fixtures round-trip through migration unchanged in decision outcomes

### Skip-instead-of-fail for distribution-metadata test
- id: `rm-007` | track: reliability | priority: 40.0 | status: implemented
- signals: conductor.run-a51c0f6c:assess-F7, test_mcp_compat.py:81 test_package_metadata_allows_both_sdk_families raises importlib.metadata.PackageNotFoundError in non-installed checkouts (worktrees, containers) instead of skipping
- acceptance: the test skips with a clear reason when the distribution is not installed and still runs in CI (which installs -e .[dev])
- evidence: cycle-1 implement (2026-09-21): test_mcp_compat.py:81 skips with reason on PackageNotFoundError (bare Py3.11 checkout: 14 passed 1 skipped) and executes+passes when the distribution is installed (Py3.13 uv env: metadata test runs green)

### Speak the official MCP Tasks extension for long-running work (read-only mapping)
- id: `rm-011` | track: compatibility | priority: 45.0 | status: candidate
- signals: conductor.run-a51c0f6c:research-R1, MCP spec 2026-07-28 changelog item 6 (SEP-2663): official io.modelcontextprotocol/tasks extension (tasks/get polling, tasks/update client input, unsolicited handles); hermes job supervisor (upstream issue #57, operator_job_supervisor.py) already implements the same semantics as hermes-private tools
- acceptance: additive read-only mapping: existing job/delegation IDs surface as standard task handles via tasks/get; tasks/update accepts approval inputs only on surfaces that already permit them; hermes_* tools remain canonical; gated on SDK support probe passing on both SDK families
- evidence: integration test showing a generic MCP client polling a hermes job via tasks/get; docs/codex.md + docs/operator-mode.md updated; no change to authority ladder (verified by existing safety tests)

### MRTR (input_required) as the standardized approval handshake
- id: `rm-012` | track: compatibility | priority: 35.0 | status: candidate
- signals: conductor.run-a51c0f6c:research-R2, MCP spec 2026-07-28 changelog item 7 (SEP-2322): InputRequiredResult + retry with inputResponses; hermes dry-run->apply ladder and Owner-Mode confirmations currently express approvals via bespoke confirm=/apply= flags (operator_policy.py, docs/operator-mode.md authority ladder)
- acceptance: design note mapping each mutating surface's approval flow onto MRTR, with an opt-in pilot behind an env gate; direct-mode per-call gates unchanged; safety tests extended to prove a client cannot convert dry-run to apply without the explicit input response
- evidence: design doc + pilot integration test on one surface (e.g. workspace write) showing input_required round-trip; full safety suite green

### Split server.py registration into per-subsystem modules
- id: `rm-013` | track: maintainability | priority: 30.0 | status: candidate
- signals: conductor.run-a51c0f6c:assess-F9, server.py is a 3,856-line module registering 153 hermes_* tools for 20+ operator_* modules; PRs #66 and #67 both rewired server.py (merge-collision hotspot); tool count is CI-pinned (test_server.py) which mitigates drift
- acceptance: registration decomposed per subsystem with zero tool-surface change; test_server tool-count/name snapshot unchanged before/after; import graph documented in docs/design
- evidence: diff shows mechanical moves only; the full suite and tool-count snapshot pass unchanged

### subscriptions/listen alignment study (deferred until a push consumer exists)
- id: `rm-014` | track: compatibility | priority: 20.0 | status: deferred
- signals: conductor.run-a51c0f6c:research-R8, MCP spec 2026-07-28 changelog items 4/9: subscriptions/listen replaces GET stream + resources/subscribe; SSE resumability/Last-Event-ID removed; hermes live events are cursor-poll tools (server.py:1879-1884) with replay, which remains the recovery story
- acceptance: revisit when a push-style consumer is required: decide between a listen-stream surface or documenting cursor polling as the hermes-native pattern; no action while all consumers poll
- evidence: decision note in docs when triggered; otherwise no code change

<!-- managed by hermes-roadmap render; do not edit by hand -->
