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

<!-- cycle-1 additions below: run 6d49d1e3979f40acba1ad3bf1ef2aaef (assess 68113cb22f56, research 5d6f8b9ea7dc) -->

Sibling-run interlock (2026-09-21): run 6d49d1e3979f and run a51c0f6cb5b0 (rm-003..rm-015 above) are parallel repository-maintenance cycle-1 runs whose branches diverged at 54f826c0cd (conductor/run-6d49d1e3979f +3 / conductor/run-a51c0f6cb5b0 +3). rm-003 (PKCE tests), rm-004, rm-007, rm-009 are implemented ON THE UNMERGED a51c branch; this run's assess independently reproduced the same defects at HEAD c1785b22e5 (5 failing tests incl. the 4 PKCE ones) — adopt by content, do not re-implement. Cross-branch reconciliation and the rm-008 branch-protection prerequisite are Conductor's call at the commit/merge gates. Recorded: the canonical checkout /work/projects/hermes-gpt carries a stale untracked ROADMAP.md (older signals snapshot, no cycle-1 additions) — this file is seeded from the newest committed sibling state (3e8eebee48) instead.

### Remove dead token_store.py block and close the F821 class
- id: `rm-016` | track: maintainability | priority: 75.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21)
- resolution: dead block deleted in worktree run-6d49d1e3979f-6d49d1e3 (implement attempt a90769548e); repo-wide F821 = 0; test_token_store.py green
- signals: conductor.run-6d49d1e3:assess-F2, token_store.py:1097-1145 unreachable dead block referencing undefined hermes_root (ruff F821 at 1097,1103,1107,1113,1137); orphaned status()-shaped body from 89cbfbe232 (#64); live duplicate logic at token_store.py:1020
- acceptance: block deleted (or re-attached deliberately to a real caller with tests); `ruff check --select F821` clean; token-store behavior unchanged (test_token_store.py green)
- evidence: `python3 -m ruff check --select F821 .` exits 0; test_token_store.py passes; diff shows removal only

### Lint gate: drive 61 ruff errors to zero and enforce in CI
- id: `rm-017` | track: reliability | priority: 65.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21)
- resolution: repo-wide ruff 61 -> 0 across 35 files (30 safe autofixes + manual; no unsafe fixes, no blanket noqa; one targeted E402 noqa for the test_package_hygiene.py sys.path bootstrap; `_allowed_message_roles` call kept as a bare statement — it is a raising validation gate, not dead code); CI lint job list replaced with repo-wide `ruff check .`; validated full-suite 1359/1368 with zero regressions
- signals: conductor.run-6d49d1e3:assess-F4, `python3 -m ruff check .` = 61 errors (28 F401, 16 F841, 5 E402, 5 F821, 3 E731, 3 E741, 1 E702); no ruff job enforced in .github/workflows/ci.yml
- acceptance: `ruff check .` exits 0 (auto-fixable set + manual review, no blanket noqa); CI runs ruff as a required job; rm-016 lands first so the F821s disappear by deletion
- evidence: green CI run including the ruff job; commit diff shows no behavior change (full suite green)

### Fail-fast on empty/invalid code_challenge at issuance
- id: `rm-018` | track: reliability | priority: 45.0 | status: dropped (blocked by design contract, 2026-09-21)
- resolution: implementation-read found the mint-side raise contradicts a deliberate A3 security contract — test_oauth_auth.py:365 (`test_legacy_code_without_stored_challenge_cannot_be_exchanged`) documents that empty-challenge codes MUST fail closed at exchange (oauth_auth.py:473-479), and passing sibling-scoped tests (test_codex_pr63_remediation.py:790 `test_outstanding_code_dies_on_revocation`) mint empty challenges on purpose. Raising at issuance would break passing safety tests (AGENTS.md forbids). Revisit only AFTER the sibling rm-003 re-bind merges, as one coherent unit with the test updates
- signals: conductor.run-6d49d1e3:assess-F5, oauth_auth.py:255-300 issue_authorization_code stores code_challenge="" unvalidated; exchange fails closed at :473-479 so such codes are minted-dead; S256 enforced only on the HTTP authorize path (:982-997). Adjacent to rm-003 (test re-bind) but distinct: mint-side contract
- acceptance: issue_authorization_code raises on empty/malformed challenge (internal callers get loud errors, not dead credentials); rm-003's empty-challenge-rejected-at-exchange test still passes; no valid flow regresses
- evidence: new unit test asserting the raise; full oauth-related suites green

### Decide plan-node lease semantics (wire or remove)
- id: `rm-019` | track: maintainability | priority: 30.0 | status: candidate
- signals: conductor.run-6d49d1e3:assess-F6, operator_mission_plan.py:941 unconditionally clears plan_nodes.lease_lock/lease_expires but nothing acquires plan-node leases (controller uses controller_pass_lease); views expose always-empty fields (:626-627)
- acceptance: either acquisition wired with tests (fields real) or fields/DTO columns removed end-to-end (schema + views + transitions); no always-empty surface shipped
- evidence: test covering lease acquire/clear round-trip OR diff removing the fields with all view tests green

### Restore pre-pause state on node resume
- id: `rm-020` | track: correctness | priority: 25.0 | status: candidate
- signals: conductor.run-6d49d1e3:assess-F7, operator_mission_plan.py:104 NODE_TRANSITIONS allows paused->{running,blockable,failed} only; a node paused from pending or dispatched can never return to its pre-pause state
- acceptance: paused nodes may transition back to their recorded pre-pause state (or the transition table documents the intentional semantics with a test); no persisted-state migration required
- evidence: unit test pausing from each source state and resuming; docs/operator-mode.md lifecycle section matches

### Warn-and-backup before overwriting corrupt cron jobs.json
- id: `rm-021` | track: reliability | priority: 28.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21; promoted from stretch after rm-018 dropped)
- resolution: operator_cron.py `_read_jobs` splits OSError/JSONDecodeError and backs up unparseable jobs.json to `jobs.json.corrupt-<ts>` (byte-identical dedupe; best-effort; no stdout/stderr noise near MCP stdio — the sidecar's presence is the operator signal) before the next atomic write can destroy it; coverage includes BOTH JSON-syntax corruption and binary/non-UTF-8 corruption (review-fix 711573d0: UnicodeDecodeError added to the recovery except-clause, backup writes the captured payload — no TOCTOU re-read); new test `test_corrupt_jobs_json_backed_up_before_overwrite` in test_operator_cron.py covers both payload classes; whole file green serially; recovery signal documented in docs/operator-mode.md (cron section)
- signals: conductor.run-6d49d1e3:assess-F8, operator_cron.py:105 _read_jobs swallows JSONDecodeError -> [] and the next mutation atomically replaces jobs.json (os.replace at :137), silently destroying a corrupt-but-recoverable file
- acceptance: on parse failure hermes_cron surfaces a visible error (or writes jobs.json.corrupt-<ts> aside) before any overwrite; a file with one bad byte stays recoverable
- evidence: unit test injecting corrupt JSON proving backup+warning; existing cron tests green

### Single topological-sort implementation
- id: `rm-022` | track: maintainability | priority: 15.0 | status: candidate
- signals: conductor.run-6d49d1e3:assess-F9, operator_controller.py:878 _topological_order is O(V*E) while operator_mission_plan.py:313 has a linear Kahn implementation; two algorithms for the same DAG drifting
- acceptance: one shared helper (linear) used by both call sites; MAX_NODES=64 bound keeps current behavior; order-stability tests prove identical outputs on existing fixtures
- evidence: diff removing one implementation; fixture equivalence test green

### Pin/bound uvicorn (floating 0.x dependency)
- id: `rm-023` | track: reliability | priority: 58.0 | status: implemented (pending commit gate, run 6d49d1e3979f cycle 1, 2026-09-21)
- resolution: pyproject.toml `uvicorn` -> `uvicorn>=0.30,<1`; TOML re-validated; pyyaml is now the only remaining bare runtime dependency (next-cycle candidate)
- signals: conductor.run-6d49d1e3:research-R4, pyproject [project] dependencies list `uvicorn` unbounded; PyPI latest 0.53.0 (2026-09 probes); 0.x minors routinely break ASGI internals; mcp is bounded but uvicorn floats
- acceptance: uvicorn bounded (e.g. >=0.30,<1 with a reviewed upper cap) in pyproject; CI installs the reviewed version; a uvicorn cap move becomes a deliberate changelog event
- evidence: pyproject diff + green CI on the pinned range; CHANGELOG note when the cap moves

### Python 3.13/3.14 CI lanes; plan the 3.10 EOL floor bump
- id: `rm-024` | track: reliability | priority: 50.0 | status: candidate
- signals: conductor.run-6d49d1e3:research-R5, .github/workflows/ci.yml:29 matrix python ['3.10','3.11','3.12']; requires-python >=3.10 (pyproject); Python 3.10 EOL 2026-10 (one month out at 2026-09-21); 3.13/3.14 stable and untested; sibling rm-003 evidence already validated the suite on Py3.13 uv env (1442/2 green)
- acceptance: CI matrix adds 3.13 (and 3.14 if deps allow) lanes green; a dated plan records the 3.11 floor bump (drops the tomli<3.11 conditional) for the 0.11.0 release
- evidence: green CI matrix run including 3.13; CHANGELOG/release-notes entry at bump time

### Finish the v0.10 controller slice: D3 hard-block + shadow-to-live
- id: `rm-025` | track: feature | priority: 40.0 | status: candidate
- signals: conductor.run-6d49d1e3:research-R6, CHANGELOG 0.10.0 records budget D3 hard-block as flag-default-off wired for a later slice and the controller running in shadow; docs/operator-mode.md + v0.10 slice notes define the live path
- acceptance: D3 hard-block enforced live behind the flag with tests (over-budget iterations blocked, resume path defined); controller promoted from shadow to live with an opt-out; docs updated
- evidence: tests proving block/resume under the flag; ops note recording the first live run; docs diff

<!-- cycle-2 additions below: run 684b97865efc456da2a21dc4259ce30f (assess 2bd3be4650704a3c877a885cecb695d1, research 71c34e3615f44a4d9fd36687be3b468a) — seeded from origin/conductor/run-6d49d1e3979f (89865b1281); this run's worktree base c1785b22e5 predates ROADMAP.md; new ids continue at rm-026, no collision with rm-003..rm-025 pending merge in PR #13 -->

### Catch up upstream v0.11.0 (supersedes the local PKCE test-repair path)
- id: `rm-026` | track: reliability | priority: 110.0 | status: candidate
- signals: conductor.run-684b9786:research-C1, upstream asimons81/hermes-gpt v0.11.0 released 2026-09-21 (PyPI hermes-gpt==0.11.0 live; CHANGELOG.md@upstream/master); merge-base 9f537106e9..upstream/master 7795aa3ce8 = exactly 5 commits (PRs #69-#73): dual MCP SDK 1.28.1+/2.x support, Codex alias return-signature fixes, opt-in Gemini Spark OAuth client profile (docs/gemini-spark.md), profile-aware session history + Bot Chat tools, Windows-portable token-store lock, security remediation bundle (signed tokens require durable store; revocation retires+advances epoch in one SQLite txn; atomic refresh rotation; ledger watermark pagination; plan-readiness parent checks; controller contract-hash binding), loopback Agent Card + unknown-peer admission, doctor JSON gateway.pid. The remediation bundle is the upstream-canonical fix for the 4 stale-PKCE failures this run's assess reproduced fresh at c1785b22e5 (test_codex_pr63_remediation.py:348,492,812,941) and for rm-018's dropped mint-side question
- acceptance: the 5-commit upstream delta merges with oauth_auth.py/server.py/token_store.py conflicts resolved deliberately (sibling rm-003/rm-016/rm-017 work reconciled by content per the cycle-1 interlock note, not re-implemented); full suite green on the baseline interpreter post-merge; PKCE tests exercise upstream remediation semantics; version/docs line adopts 0.11.0 or a fork-equivalent entry
- evidence: post-merge full-suite run green (serial, HERMES_HTTP_TEST=1, baseline venv); merge commit message records conflict resolution decisions; docs/gemini-spark.md present in-tree

### Bound pyyaml (the last bare runtime dependency)
- id: `rm-027` | track: reliability | priority: 55.0 | status: implemented
- signals: conductor.run-684b9786:research-C4 + run-6d49d1e3 next-cycle note, pyproject.toml [project] dependencies lists `pyyaml` unbounded — the only bare runtime dep left after rm-023; PyPI latest 6.0.3 (2026-09-21 probe); yaml parsing sits on the operator config/skills path
- acceptance: pyproject pins `pyyaml>=6,<7`; CI installs the bounded range green; cap moves become deliberate changelog events (rm-023 policy)
- evidence: pyproject diff + green CI on the bounded range; CHANGELOG note when the cap moves. Cycle-2 implement (2026-09-22, attempt 06181fb4): pyproject.toml:20 now `pyyaml>=6,<7` (tomllib parse ok), CHANGELOG Unreleased entry added; full serial suite delta-zero vs the 5-failure assess baseline. REMAINING: review + commit/merge gates, then a green CI run on the bounded range

### Profile-aware skill-resolution gate before placement/dispatch
- id: `rm-028` | track: correctness | priority: 38.0 | status: candidate
- signals: conductor.run-684b9786:research-C5, upstream issue #74 (opened 2026-09-21, the only open upstream issue): 'skill exists' != 'the target profile can resolve it at execution time'; cites server.py::skill_roots/discover_skills/hermes_skill_list, operator_skills.py::_find_skill_dir, operator_capability_manifest.py, operator_placement.py; depends on rm-026 (v0.11.0 reshaped capability-manifest surfaces)
- acceptance: placement/dispatch validates that the target profile can actually resolve each referenced skill at execution time (or fails loudly pre-flight); contract agreed architecture-first with upstream before implementation
- evidence: upstream issue #74 linked; tests proving a placement referencing an unresolvable skill fails before dispatch; docs/operator-mode.md skills section updated

### Updater must verify it found a hermes-gpt checkout before fast-forwarding
- id: `rm-029` | track: reliability | priority: 42.0 | status: implemented
- signals: conductor.run-684b9786:assess, updater.py:49-58 _find_git_root walks to the first enclosing repo with no hermes-gpt sentinel; updater.py:203-206 then updates whatever it found; docs/updating.md:19-26 promises updates apply to the hermes-gpt installation — a venv nested inside a foreign git repo (the standard hermes layout) makes `update --apply` fast-forward the wrong repository
- acceptance: candidate roots are verified as hermes-gpt checkouts (pyproject name / package marker / remote URL) with a loud refusal otherwise; regression test using a foreign git-root fixture
- evidence: unit test with a foreign-repo fixture proving refusal; docs/updating.md statement matches behavior. Cycle-2 implement (2026-09-22, attempt 06181fb4): updater.py:62-70 `_is_hermes_gpt_checkout()` + `NOT_A_HERMES_GPT_CHECKOUT` loud refusal in `check_for_update` (:213, refusal :217-227) covering check and apply paths; 3 new tests in test_updater.py (foreign-pyproject root refused with only the single rev-parse call and zero fetch/merge/pip calls; bare root refused; genuine hermes-gpt checkout proceeds to git mode) — 10/10 green; docs/updating.md guarantee list now leads with the refusal. REMAINING: review + commit/merge gates

### SHA-pin the reusable private-leak-sentinel workflow
- id: `rm-030` | track: reliability | priority: 48.0 | status: implemented
- signals: conductor.run-684b9786:assess, .github/workflows/ci.yml:22 references codeo1io/.github/.github/workflows/private-leak-sentinel.yaml@main; codeo1io/.github is public with no branch protection (gh api verified 2026-09-21: private:false, default_branch main) — a mutable pin means any push to that main silently changes what every CI run, including upstream PR runs, scans
- acceptance: the reusable-workflow reference pins an immutable commit SHA (human-readable branch noted in a comment); a re-pin rotation procedure is documented
- evidence: ci.yml diff showing the SHA ref; rotation note in docs or repo workflow docs. Cycle-2 implement (2026-09-22, attempt 06181fb4): ci.yml:22 pinned to a86c8ef77170831d7efc7c683542e3b364366168 (codeo1io/.github main at 2026-09-21, the gitleaks-allowlist commit that unblocked PR #12's sentinel job; re-verified via gh api at implement time), rotation procedure documented in comments adjacent to the pin; yaml parse ok. REMAINING: review + commit/merge gates; the pinned workflow is exercised by the next CI run

### Remove or wire the unused dompurify web dependencies
- id: `rm-031` | track: maintainability | priority: 12.0 | status: implemented
- signals: conductor.run-684b9786:assess, web/package.json:15,28 declare dompurify + @types/dompurify but no web/src file imports them; chat renders via ReactMarkdown without rehype-raw (web/src/chat/Message.tsx:15) so the implied sanitization layer neither exists nor is needed today
- acceptance: dependencies removed (clean install + green web build) or sanitization genuinely wired with a test proving raw HTML is stripped
- evidence: package.json diff + green web build/test; grep shows zero dompurify imports or a passing sanitization test. Cycle-2 implement (2026-09-22, attempt 06181fb4): dompurify + @types/dompurify removed via `npm uninstall` (package.json AND package-lock.json both zero dompurify refs); web build green (`tsc -b && vite build`, 307 modules, exit 0); CHANGELOG Unreleased entry added. REMAINING: review + commit/merge gates

## Cycle 1 outcome — run 6d49d1e3979f (2026-09-21; review loop appended at commit gate)

Batch implemented in worktree run-6d49d1e3979f-6d49d1e3 (uncommitted; commit/merge are later gates): rm-016, rm-017 (61->0 + CI list widened to repo-wide), rm-023, stretch rm-021 promoted; rm-018 dropped (see its resolution). Validation (attempts e607cfb2 targeted, a179d016 full): targeted 567/576 pass over all 33 changed surfaces; full suite 1359/1368 pass, 5 skip, 4 fail — all 4 are the stale-PKCE baseline, stash-verified identical at clean HEAD c1785b22e5; CI-parity HTTP smoke passed; `ruff check .` = 0.
Review loop: independent review 6084fc89 PASS with 4 findings -> fix 711573d0 (non-UTF-8 corruption recovery, TOCTOU, dev ruff pin, docs section) -> full retest b82bae9c (failure set byte-identical to the pre-fix run: same 4 pr63 baseline, zero delta) -> re-review 5da6669f PASS (2 residual non-blocking findings, folded at the commit gate).

### Cycle 1 learnings — prevention rules

1. **Lint gates must be repo-wide from day one.** A hand-maintained 25-file CI lint list (.github/workflows/ci.yml) let 61 errors live outside it undetected.
2. **F821 (undefined name) is the cheapest dead-work detector.** The orphaned #64 status body survived because its file sat outside the lint list.
3. **Before deleting 'unused' code, check the call for side effects.** server.py's `_allowed_message_roles()` is an unused *result* but a live *validation gate* that raises without `ENABLE_SESSION_INTERNAL_CONTENT_ENV` — kept as a bare statement.
4. **Autofix discipline:** safe `--fix` set only, then manual review; never `--unsafe-fixes`; no blanket noqa (single targeted E402 for a sys.path bootstrap that must stay late).
5. **Read the test docstring before fixing the mechanism it exercises.** rm-018 died on exactly this: an A3 fail-closed exchange contract plus passing tests that mint empty challenges on purpose.
6. **Destructive atomic writes should preserve unparseable payloads** (rm-021 pattern: `.corrupt-<ts>` sidecar + byte-identical dedupe, silent-failure-safe, no stdout noise near MCP stdio).
7. **Record the validation environment with every test claim.** Authoritative this cycle: baseline interpreter (mcp 2.0.0, pytest 9.1.1, starlette 1.3.1, uvicorn 0.41.0). `uv run` silently resolves a different env (mcp 2.2.0, no dev extras — they are optional-dependencies uv does not install): not comparable, not a CI lane.
8. **Classify before fixing: stash-verify.** `git stash push` -> re-run failing test at clean HEAD -> `git stash pop` proved all 4 residual failures pre-existing in one command.
9. **Parallel (-n 8) cancel/coalesce tests flake on the loaded shared runner** (delegations [True]; fabric_g4c prelaunch-cancel). Serial is authoritative; parallel-only failures are not regressions.
10. **Env quirks to remember:** pytest -q here omits the final counts line (derive from progress-line chars, cross-check FAILED lines); `uv run` drops uv.lock + .venv into the tree — remove them or the validation digest goes stale.

### Next-cycle context (candidates in suggested order)

- **rm-024** (Py3.13/3.14 CI lanes; 3.10 EOL 2026-10) — highest research-backed value; needs CI runs, not just local.
- **pyyaml bound** — last bare runtime dependency after rm-023 (pyproject dependencies list). The dev-extra ruff pin (>=0.15,<0.16) landed in review-fix 711573d0; cap moves for either are deliberate changelog events.
- **De-flake the parallel cancel tests** or mark them serial-only via pytest markers; add pytest-xdist to dev extras only if `-n 8` becomes an official lane (it is declared nowhere today).
- **CHANGELOG entry for this batch** (user-visible: repo-wide lint gate, uvicorn bound, corrupt-jobs.json backup) at commit time.
- **rm-018 revisit** only after the sibling rm-003 re-bind merges (one coherent unit with its test updates).
- Watch **test_mcp_compat.py:81** in CI: its assess-time failure no longer reproduces in-session (passes in-suite and standalone) — env-state-dependent, needs a skip guard for bare checkouts regardless.
- Remaining design-gated/low items unchanged: rm-019, rm-020, rm-022, rm-025.

<!-- cycle-1 additions below: run fd2bc85ff5994b8fa6b59f286efedce7 (assess db8d375501724, research 9662e1e8286) -->

Interlock (2026-09-21): run fd2bc85ff599 is a third parallel repository-maintenance cycle-1 run on the same base c1785b22e5. Its assess independently re-confirmed at this HEAD — on the baseline interpreter (py3.11.15/mcp 2.0.0/pytest 9.1.1) in CI's exact serial shape (HERMES_HTTP_TEST=1, log /tmp/assess-db8d3755-full.log) — the 4 stale empty-challenge PKCE failures (rm-003; defs :348/:492/:812/:941 failing at oauth_auth.py:477-480 fail-closed guard), test_mcp_compat.py:81 metadata failure (rm-007), token_store.py:1097-1141 dead block with 5x F821 (rm-016), the curated CI lint-list gap (rm-017), unbounded uvicorn/pyyaml (rm-023 bounded uvicorn on the sibling branch; pyyaml remains), and the 3.12 matrix ceiling (rm-024). No delegation/g4c flake reproduces serially. Adopt sibling implementations by content at the merge gates; do not re-implement.

### Land upstream v0.11.0 (dual SDK support, Gemini Spark profile, security remediation bundle)
- id: `rm-026` | track: compatibility | priority: 115.0 | status: candidate
- signals: conductor.run-fd2bc85f:research-R1, merge-base 9f537106e9..upstream/master 7795aa3ce8 = exactly 5 commits (#69 Gemini Spark OAuth client profile + verified custom-app setup guide, #70 README OAuth-note consistency, #71 release v0.11.0 — MCP SDK 2 first-class + Bot Chat + security remediation bundle, #72 release notes PUBLISHED with GitHub+PyPI live, #73 hero assets); fork is 0.10.0 while PyPI serves 0.11.0; upstream #71 security bundle (signed tokens require durable store, revocation retires+advances epoch in one SQLite txn, atomic refresh rotation, ledger watermark pagination) supersedes fork-local PKCE repair — catch-up SUPERSEDES local test repair
- acceptance: upstream 5-commit set merged or cherry-picked onto the fork line with oauth_auth.py/server.py conflict resolution reviewed line-by-line; full suite green in CI shape (HERMES_HTTP_TEST=1, serial, baseline interpreter) — including the 4 stale-PKCE tests, which must adopt upstream's remediated contracts rather than local re-binds; security remediation diff explicitly reviewed against fork invariants (Owner Mode break-glass, secret-path denials); version bumped to 0.11.0+ and CHANGELOG records the catch-up
- evidence: merge commit with conflict-resolution notes; green full-suite run post-merge; CHANGELOG diff; release/PyPI links recorded

### Raise build floor to setuptools>=77 (PEP 639 license string)
- id: `rm-027` | track: reliability | priority: 62.0 | status: implemented-pending-commit-gate (run fd2bc85f B1; floor = setuptools>=77; validated 2026-09-22 via no-isolation prepare_metadata under 77.0.3 -> hermes_gpt-0.10.0.dist-info + LICENSE)
- signals: conductor.run-fd2bc85f:assess-F6, pyproject.toml license = "MIT" (PEP 639 SPDX string) with build-system floor setuptools>=69 (pyproject.toml:2); verified repro: setuptools==69.5.1 venv, prepare_metadata_for_build_wheel fails with license schema error ('required: file/text'); CI is green only because python -m build isolation pulls current setuptools
- acceptance: floor raised to >=77 (or license switched to table form) so declared-floor builds work; sdist+wheel build verified in a --no-isolation environment; no behavior change to isolated CI builds
- evidence: reproducible build under the pinned floor; pyproject diff; tools/check_package_hygiene.py still passes

### Re-baseline the repo-wide lint gate for ruff 0.15 default rules
- id: `rm-028` | track: maintainability | priority: 68.0 | status: candidate
- signals: conductor.run-fd2bc85f:assess-F4, rm-017 (sibling) drove `ruff check .` 61->0 under the classic E/F default set and widened CI lint to repo-wide; but ruff 0.15.10 `--isolated` defaults now include UP/I/BLE/TRY/RUF classes — measured 524 findings at c1785b22e5 (server.py 48, token_store.py 21, oauth_auth.py 17, operator_policy.py 17), 184 fixable under 0.15; the post-merge gate will either silently enforce a different (larger) rule set or need a committed config that pins the intended set
- acceptance: a committed [tool.ruff] config declares the enforced rule set explicitly; decision recorded (adopt 0.15 defaults with a staged fix plan, or select the classic set); CI lint job passes under the pinned ruff (dev-extra already pins >=0.15,<0.16 per review-fix 711573d0); no unenforced class without a recorded decision
- evidence: config diff + green lint job; finding-count table before/after (61-era vs 524-era) with the disposition of each new class

### Resolve the 12 unresolved gitlink entries
- id: `rm-029` | track: maintainability | priority: 22.0 | status: candidate
- signals: conductor.run-fd2bc85f:assess-F9, `git ls-files -s | awk '$1==160000'` = 12 entries at HEAD (8x design-canon-*, 4x review-*) with no .gitmodules; this lineage's last three commits (c1785b22e5..) already fought individual unresolvable gitlinks in CI
- acceptance: either a .gitmodules mapping with resolvable URLs, or the 12 entries replaced by ordinary content/excluded; `git submodule status` resolves everything it lists; CI checkout (submodules:false) unaffected — proven by a green run
- evidence: git submodule status output; green CI run; diff

## Cycle 1 outcome — run fd2bc85ff599 (2026-09-22; pre-review, compounded before review/shipping gates)

Batch B1 'Truthful Green Baseline' implemented in worktree run-fd2bc85ff599-fd2bc85f at base c1785b22e5 (uncommitted; commit/merge are later gates), 4 files +57/-60, adopting validated sibling content by content where parent blobs were byte-identical to this base: (a) PKCE re-bind — sibling 2ff57351b7 (a51c) applied verbatim: module-level RFC-7636 verifier + S256 challenge, all FIVE empty-challenge sites re-bound (defs :348/:492/:941 plus the accidentally-passing :802 site and vacuously-passing :820) and NEW test_exchange_rejects_code_without_stored_challenge pinning the fail-closed contract (sibling rm-003); (b) test_mcp_compat.py:81 skip guard on PackageNotFoundError (sibling rm-007); (c) token_store.py dead block :1097-1141 deleted (sibling 89865b1281 rm-016 hunk; its out-of-scope :772 F841 removal reverted to keep the diff exactly the declared surface); (d) rm-027 setuptools>=77 floor; (e) stretch pyyaml>=6,<7 (the sibling next-cycle pyyaml candidate, now landed here). oauth_auth.py runtime untouched — the fail-closed guard at :477-480 was already correct; only the tests were stale.
Validation (attempts 8d1e62ec implement, 3b787ac5 targeted_tests): ruff --isolated --select F821 = 0 (was 5); targeted 3-file run EXIT=0; full suite in CI's exact shape (HERMES_HTTP_TEST=1, serial, baseline interpreter) EXIT=0 with ZERO failures — twice on the identical tree (one intervening load flake, see rule 13); setuptools 77.0.3 no-isolation metadata build green. Baseline truth restored: 5 deterministic failures -> 0.

### Cycle 1 learnings — prevention rules (run fd2bc85ff599 additions; rules 1-10 above remain in force)

11. **Verify folded artifacts on disk before trusting the fold record.** This run hit it twice: the roadmap cycle block (rm-026..029) was claimed written but never landed — spool JSON and file write were both cut off; the block had to be re-materialized from the folded phase_result at prioritize time.
12. **Adopt-by-content beats re-implementation when a validated sibling exists.** `git diff <sibling>^ <sibling> -- file | git apply` after proving parent-blob equality (`git rev-parse base:file == sibling^:file`) carries the sibling's two-environment validation exactly; revert out-of-scope hunks afterward so the diff stays inside the declared stewardship surfaces.
13. **Serial runs on a saturated host can flake the concurrent-thread family too.** 4th member: test_operator_delegations.py::test_concurrent_exact_retry_invokes_backend_once failed in a SERIAL full run at load-avg ~28; passed solo and on an identical-tree serial rerun. Triage = solo rerun + identical-tree rerun; never 'fix' a passing-on-rerun flake mid-validation — it would stale the dispatch digest for zero benefit.
14. **Declared build floors must be verified at the floor, not at whatever isolation installs.** CI stayed green while `setuptools>=69` could not build the PEP 639 license string; only a no-isolation prepare_metadata run under the pinned floor (77.0.3, unique venv) exposed and then proved the fix.

### Next-cycle context (run fd2bc85ff599; carries into cycle-2 assessment)

- **rm-026 (upstream v0.11.0 catch-up) is the headline** — its prerequisite green baseline now exists in this worktree; when merging, the 4+1 re-bound PKCE tests must adopt upstream's remediated contracts (rm-026 acceptance) instead of these local re-binds; conflict-hot files: oauth_auth.py, server.py.
- **rm-028 (ruff 0.15 re-baseline)** is the top non-merge candidate: 524 isolated findings at this base, 184 fixable; needs a committed [tool.ruff] decision; note sibling rm-017 already drove the classic set to 0 repo-wide.
- **rm-029 (12 gitlinks)** unchanged; CI unaffected (submodules:false).
- Sibling-adoption deltas NOT in this batch remain available at merge gates: ci.yml SDK lanes (sibling rm-009), repo-wide ruff sweep (rm-017), uvicorn bound (rm-023).
- CHANGELOG Unreleased entry for B1 added at compound time; release-notes/commit message at the commit gate should reference the adoption provenance (2ff57351b7, 89865b1281).

<!-- restored 2026-09-21 (prioritize attempt 87402e78): roadmap-phase write was cut off mid-edit; block re-emitted verbatim from the folded roadmap phase_result -->

## Cycle 2 research digest — run 684b97865efc (2026-09-21; assess 2bd3be46, research 71c34e36)

External evidence probed 2026-09-21: upstream v0.11.0 live on PyPI, delta = 5 commits (PRs #69-#73) -> rm-026. mcp SDK 2.2.0 + 1.30.0 (released 2026-09-07) and latest protocol revision still 2026-07-28 — rm-009's remaining acceptance (green new lanes + 2.1 behavior-change audit) is unchanged; no new item. Python 3.10 EOL confirmed 2026-10-31; 3.13.15/3.14.7 current (endoflife.date) — rm-024 stands as written; no new item. Upstream's only open issue is #74 (skill resolution) -> rm-028. FastMCP v4.0.5 (2026-09-17, ~27.8k stars) recorded as evaluation-only reference for future auth/middleware patterns — not a dependency candidate (repo invariant: thin mcp_compat.py shim over the official SDKs). Independent-reproduction interlock: this run's assess reproduced at base c1785b22e5 the same defect classes the sibling runs fixed on unmerged branches (4 stale-PKCE failures + env-shaped test_mcp_compat.py:81; token_store.py dead block; 39 ruff errors across the 69 files outside the 62-file CI lint list) — rm-003/rm-016/rm-017 adopt-by-content per the cycle-1 interlock note; acceptance is re-verification at merge time, not re-implementation.

## Cycle 2 outcome — run 684b97865efc (2026-09-22; pre-review compound 9ed20686)

Batch B1 'Verified-Fresh Hygiene' implemented in worktree run-684b97865efc-684b9786 (uncommitted; review/commit/merge are later gates): rm-027, rm-030, rm-031, rm-029 (implement order), all four flipped to `implemented`. 8 files changed (+83/-36): pyproject.toml, .github/workflows/ci.yml, web/package.json, web/package-lock.json, updater.py, test_updater.py, docs/updating.md, CHANGELOG.md. Validation (attempts 06181fb4 implement, d86d1db2 targeted_tests): test_updater.py 10/10 exit 0; web build exit 0; ruff delta zero on touched files (4 pre-existing errors in updater.py, count+locations identical to HEAD copies); full serial suite on the baseline interpreter = exactly the 5-failure assess baseline (4 inherited stale-PKCE + env-shaped test_mcp_compat.py:81), zero new failures; one loaded-run g4c flake (test_launch_wins_first_and_cancel_returns_while_launch_call_is_in_flight) triaged to the load-timing class via solo-rerun pass and did not recur in the validation run.

### Cycle 2 learnings — prevention rules

1. **Put safety sentinels at the decision point, not the discovery helper.** The hermes-gpt-checkout verification lives in `check_for_update` (updater.py:213) rather than `_find_git_root`, so check and apply paths are covered together and the existing `_source_update` unit tests keep their seam.
2. **A mutable `@main` ref on a shared reusable workflow is supply-chain surface.** codeo1io/.github is public with no branch protection, so the pin's integrity is only as strong as that repo's main. Pin the immutable SHA and document the rotation procedure adjacent to the pin.
3. **Judge suites by baseline delta, not raw exit code.** The serial full-suite log compared against the assess-time baseline is the comparable artifact; inherited failures (4 stale-PKCE + env-shaped mcp_compat) are not regressions and must not be "fixed" in passing.
4. **The load-timing flake class has a 4th member:** test_operator_fabric_g4c.py::test_launch_wins_first_and_cancel_returns_while_launch_call_is_in_flight (failed under a loaded serial run, passed solo). Extend rm-012's evidence list rather than chasing the mechanism.
5. **Remove JS dependencies through the package manager, never by hand.** `npm uninstall` kept package.json and package-lock.json coherent (both grep to zero dompurify refs); hand-editing the lock risks silent drift — then run the real build (`npm run build`) as the acceptance gate.
6. **Do not double-fix superseded defects.** Upstream v0.11.0's security bundle is the canonical fix for the 4 stale-PKCE tests (rm-026); local repair would only conflict with the catch-up merge.
7. **A cheap proof of "zero new lint debt":** run ruff on the changed files and on their HEAD copies — identical count+locations (4 == 4) proves the batch added nothing without touching sibling-owned cleanup (rm-017 on PR #13).

### Cycle 2 next-cycle context

- **rm-026 (upstream v0.11.0 catch-up) stays the headline** and is gated on PR #12/#13 merging (adopt-by-content: this run re-verified both still open 2026-09-22); it carries the canonical stale-PKCE fix and unblocks rm-028 (upstream issue #74 contract).
- The batch's review/commit gates are pending at this writing — outcome text above is pre-review by design and must not be read as shipped.
- De-flake scope (rm-012) now covers 4 g4c/delegation members; serial remains authoritative.
- Sentinel-pin rotation (rm-030) re-verify on each catch-up cycle: `gh api repos/codeo1io/.github/commits/main --jq .sha` vs the pinned ref in ci.yml.
<!-- carried verbatim 2026-09-23 by run 9e0b97f5d86c cycle 1 batch B1 from PR #19 head refs/pull/19/head (run 634bf4516c83); adoption provenance, not a new cycle -->
<!-- cycle-1 additions below: run 634bf4516c834979b8df90376760a3c2 (assess 0c118051, research aa5dfed3; parallel repository-maintenance cycle-1 sibling of a51c/6d49 runs) -->

Fresh re-verification (2026-09-21, assess attempt 0c118051 at HEAD c1785b22e5, clean tree): the sibling pending-merge defects still reproduce here — 4 stale-PKCE failures in test_codex_pr63_remediation.py:348/:492/:812/:941 vs oauth_auth.py:474-479 fail-closed PKCE (rm-003's target; full suite 1640 tests / 5 failed on baseline venv, identical set under -n 8 and mcp 2.0.0/2.2.0), token_store.py:1096-1141 orphaned block with 5x F821 (rm-016), repo-wide F401 x11/F841 x16 non-test (rm-017), test_mcp_compat.py:81 PackageNotFoundError on bare checkouts (rm-007). Confirms none of the a51c/6d49 branches have merged into this lineage yet — adopt-by-content interlock still stands. New items below extend (do not replace) the sibling state.

### Upstream v0.11.0 catch-up with explicit PKCE-semantics reconciliation
- id: `rm-030` | track: compatibility | priority: 115.0 | status: candidate (designated next-cycle headline; do not fold into a green-suite batch)
- signals: conductor.run-634bf451:research, upstream asimons81/hermes-gpt v0.11.0 released 2026-09-18 (PyPI live; fork still 0.10.0): exactly 5 commits HEAD..upstream/master (da39b19e8c..7795aa3ce8, PRs #69-#73). PR #69 adds the opt-in Gemini Spark OAuth client profile (oauth_auth.py +157 lines, docs/gemini-spark.md 141 lines, test_gemini_compat.py 1087 lines) with OPTIONAL PKCE (`require_pkce`, default True) — a semantic conflict with this fork's mandatory fail-closed PKCE (oauth_auth.py:474-479) and its second non-RFC7009 token endpoint; #71 security remediation = unauthenticated MCP shutdown port removed + mcp[cli] floor bump; pyproject widened to mcp[cli]>=1.28.1,<3; assets/docs updates in #70/#72/#73
- acceptance: PRs #69-#73 merged or cherry-picked with a written decision note on PKCE semantics (fork default stays fail-closed mandatory; `require_pkce` opt-out allowed only inside the Gemini Spark profile contract with tests); test_server.py tool-count pin updated if the upstream diff changes registration; full suite green on mcp 1.x and 2.x lanes including the new test_gemini_compat.py; docs/gemini-spark.md added to data-files; CHANGELOG entry records the catch-up and the PKCE decision
- evidence: `git rev-list --count HEAD..upstream/master` == 0 post-merge; full-suite green logs on both SDK families; decision note (commit message or docs); CI green

### MCP spec-revision lineage refresh (2025-06-18) + SDK 2.3.x lane
- id: `rm-031` | track: compatibility | priority: 70.0 | status: candidate
- signals: conductor.run-634bf451:research, modelcontextprotocol/specification current revision is 2025-06-18 (docs/mcp-compatibility.md:22-24 still claims latest = 2026-07-28 — stale); python-sdk 2.3.4 (2026-09-13) targets 2025-06-18; rm-009's assertion test pins LATEST_PROTOCOL_VERSION=='2026-07-28' and will go red the moment an SDK 2.3.x lane exists; CI pins (1.28.1/2.0.0 + 2.2.0/1.30.0 lanes) stop below 2.3.x
- acceptance: docs/mcp-compatibility.md corrected to describe the revision lineage (2026-07-28 pinned for SDK <=2.2, 2025-06-18 for 2.3+) instead of claiming one "latest"; the rm-009 revision assertion parameterized per installed SDK pin (still fails loudly on unexpected revisions); a mcp==2.3.x lane added to CI (or pins refreshed per rm-009's cadence rule) with a spec-delta review note for hermes surfaces; MCP-Auth cross-RFC notes (RFC 9728/9700 now Proposed Standard, draft-ietf-oauth-parallel-refresh adopted) reflected in docs/oauth.md where they touch hermes behavior
- evidence: docs diff; assertion test green per lane; ci.yml matrix diff; delta-review note

### Remove 12 unresolvable gitlinks and correct the c1785b22e5 record
- id: `rm-026` | track: reliability | priority: 72.0 | status: implemented (pending commit gate, run 634bf4516c83 cycle 1, 2026-09-22)
- signals: conductor.run-634bf451:assess, `git ls-files -s | grep -c '^160000'` == 12 (design-canon-* x8, review-bench, review-compat, review-fixtures, review-qa) with NO .gitmodules and all 12 dirs empty on disk; commit c1785b22e5's message claims it dropped the design-canon-adr002 gitlink but its diff only deleted .gitmodules — the gitlink remains in the index (commit-message/diff mismatch)
- acceptance: all 12 gitlinks removed from the index (git rm --cached) OR a .gitmodules restored with resolvable URLs if any are intentionally real; `git ls-files -s | grep -c '^160000'` == 0; a fresh `git clone --recurse-submodules` does not fail; commit message truthfully states what was removed (supersedes the c1785b22e5 claim)
- evidence: command outputs pre/post; CI unaffected (actions/checkout submodules:false) — green run confirms

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-027` | track: maintainability | priority: 60.0 | status: partially implemented (run 634bf4516c83 cycle 1, 2026-09-22 — remainder: data-files +2 docs, runtime-checkout.md historical re-label, guard test, CHANGELOG; needs re-dispatch before commit gate)
- signals: conductor.run-634bf451:assess, docs/runtime-checkout.md and docs/vnext-capability-manifest-and-mission-ledger.md exist in docs/ and are referenced by README.md:36, README.md:343, docs/README.md:28 (the documentation authority map) but are absent from [tool.setuptools.data-files] — installed users get a docs map pointing at files that do not ship; no test guards the shipped-docs list (test_export_docs.py pins only file-export.md; test_package_hygiene.py pins release notes); docs/runtime-checkout.md:18 additionally pins host state ('mcp[cli]>=1.0,<2' vs pyproject's >=1.28.1,<3; /home/tony paths; port 4750)
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refresh or re-label as historical per AGENTS.md documentation rules
- evidence: guard test added and green; `python -m build` + tools/check_package_hygiene.py show the shipped docs set

### Stop .gitignore '*.ps1' from swallowing new example scripts
- id: `rm-028` | track: reliability | priority: 55.0 | status: implemented (pending commit gate, run 634bf4516c83 cycle 1, 2026-09-22)
- signals: conductor.run-634bf451:assess, .gitignore '*.ps1' rule matches examples/*.example.ps1 (verified: `git check-ignore examples/foo.example.ps1` matches) — the exact pattern pyproject data-files ships; existing examples are tracked only because they predate the rule, so any NEW example .ps1 is invisible to `git add .` yet claimed by data-files
- acceptance: negation rule added (e.g. `!examples/*.ps1`); `git check-ignore examples/foo.example.ps1` exits 1 post-fix; tracked example set unchanged (`git ls-files examples/` identical); packaging still ships them
- evidence: check-ignore probe before/after; ls-files diff empty; data-files listing in the built wheel/sdist

### pyyaml bound (last bare runtime dependency)
- id: `rm-032` | track: reliability | priority: 58.0 | status: implemented (pending commit gate, run 634bf4516c83 cycle 1, 2026-09-22)
- signals: conductor.run-634bf451:research, pyproject dependencies list pyyaml unbounded; PyPI 6.0.3 (2026-08-25) fixed CVE-2026-31132; rm-023 left pyyaml as the only bare runtime dep (uvicorn already >=0.30,<1)
- acceptance: pyyaml bounded `>=6.0.3,<7` in pyproject (and requirements.txt if rm-029 keeps that file); CHANGELOG note; a cap move is a deliberate changelog event
- evidence: pyproject diff; full suite green; CHANGELOG entry

### requirements.txt / pyproject dependency duplication + undeclared psutil
- id: `rm-029` | track: maintainability | priority: 45.0 | status: implemented (pending commit gate, run 634bf4516c83 cycle 1, 2026-09-22; review findings #1/#2 — requirements-dev.txt '-r' include + README dev-setup path — fixed in review-fix attempt cf265a76)
- signals: conductor.run-634bf451:assess+research, requirements.txt:1-5 duplicates the pyproject [project] dependency list as a strict subset (only the `tomli; python_version<'3.11'` conditional is absent — verified 2026-09-21) while dev extras live only in pyproject; two sources of truth for the install set. Correction of the original research note: requirements.txt does NOT add psutil — psutil is imported only as a guarded optional import (operator_workspace.py:172, operator_diagnostics.py:122) and is declared nowhere, which is acceptable for an optional enhancement
- acceptance: single source of truth — requirements.txt removed (docs point at `pip install .[dev]`); the one live reference (docs/mcp-compatibility.md:88) updated; psutil left as a documented optional guarded import (no declaration change required) or covered by an explicit optional extra if the review prefers
- evidence: sync guard green or removal diff; `pip install` equivalence shown; full suite green

### Gemini CLI client profile (user-need evidenced by upstream #54)
- id: `rm-033` | track: compatibility | priority: 35.0 | status: candidate (gated on rm-030)
- signals: conductor.run-634bf451:research, upstream issue #54 (open, 2026-09-12) requests Gemini CLI support; the only open user-need signal on either tracker (fork has no open issues; upstream has no other open issues); rm-030's Gemini Spark profile provides the custom-app OAuth scaffolding to mirror
- acceptance: opt-in Gemini CLI client profile analogous to Gemini Spark (profile-aware session history + verified setup guide), default surfaces unchanged (read-only/dry-run ladder intact), test file mirroring test_gemini_compat.py; docs/codex.md terminology rules respected (client profile vs delegated worker)
- evidence: tests green in-suite; setup guide verified against a real custom app; upstream #54 referenced in the CHANGELOG/PR

Status amendments from this run's evidence (history above preserved): rm-024 gains anyio-5.0.0 evidence (released 2026-09-21; the -n 8 uv-env log already shows anyio BlockingPortal deprecation warnings — 3.13/3.14 lanes will surface more); rm-023's pyyaml follow-on is now formalized as rm-032; rm-018's revisit precondition (sibling rm-003 merge) is unchanged and still unmet at this HEAD.

## Cycle 1 outcome — run 634bf4516c83 (2026-09-22; batch B1 "Index & Packaging Truthfulness"; review loop pending — recorded post-compound)

Batch B1 (prioritize attempt 13e8bd28: rm-029 → rm-032 → rm-026 → rm-028 → rm-027) implemented in worktree run-634bf4516c83 (uncommitted; commit/merge are later gates). Complete: rm-026 (12 gitlinks `git rm --cached`, index count 0), rm-029 (requirements.txt deleted; docs/mcp-compatibility.md:88 now pyproject-only; review-fix cf265a76 additionally deleted requirements-dev.txt — its line 1 was `-r requirements.txt` — and repointed README's dev setup to `pip install -e ".[dev]"`, closing review findings #1/#2), rm-032 (pyyaml `>=6.0.3,<7` in pyproject; CHANGELOG entry landed in review-fix cf265a76, closing finding #4), rm-028 (`.gitignore` `!examples/*.example.ps1` negation). Partial: rm-027 — data-files registration of docs/runtime-checkout.md + docs/vnext-capability-manifest-and-mission-ledger.md, runtime-checkout.md historical re-label, and the shipped-docs guard test remain OPEN and must land before the commit gate; the CHANGELOG Unreleased entries for B1 landed in review-fix cf265a76.
Validation (pre-review, attempt ae8f85ab, baseline interpreter mcp 2.0.0 / pytest 9.1.1 / HERMES_HTTP_TEST=1 serial): targeted test_package_hygiene.py 48 passed / 3 skipped / exit 0; full suite exit 1 with EXACTLY 4 FAILED — all the inherited stale-PKCE class (test_codex_pr63_remediation.py, sibling rm-003's target), 0 ERROR; versus the 2026-09-21 assess baseline (5 FAILED incl. test_mcp_compat.py:81) this is zero NEW failures and one fewer — the mcp_compat metadata test passed in-suite and solo this run (env-state-dependent, exactly as cycle 1's watch-list predicted). Static acceptance: `git check-ignore examples/<new>.example.ps1` exit 1 with control `deploy-local.ps1` exit 0; `git ls-files -s | grep -c '^160000'` == 0; tomllib parse clean; log /tmp/targeted-ae8f85ab-full.log.

### Cycle 1 learnings (run 634bf4516c83) — prevention rules, continued

11. **One manifest for the install set.** requirements.txt was a strict-subset duplicate of pyproject dependencies — invisible drift by construction (its tomli conditional was already gone). Single source of truth: pyproject; any second manifest must be generated, never hand-maintained. Enforcement proof: the independent review (attempt 0c534991) caught requirements-dev.txt — a `-r requirements.txt` include the implement sweep missed — as a live breakage; both manifests are now gone.
12. **Verify manifest claims against the file, not the narrative.** The original research note claimed requirements.txt "adds psutil"; the file never listed it (psutil is a guarded optional import declared nowhere). Every dependency claim got re-checked at stewardship time before it entered the batch record.
13. **Probe .gitignore against the shipped set.** A broad ignore glob ('*.ps1') silently untracks exactly the pattern data-files ships; the durable check is a synthetic-name probe (`git check-ignore examples/x.example.ps1` → expect exit 1) plus a tracked-set diff, not eyeballing existing files (they predate the rule and stay tracked).
14. **Commit messages are claims; the index is the state.** HEAD c1785b22e5's message said the gitlink was dropped while its diff only deleted .gitmodules — index facts (`git ls-files -s | grep '^160000'`) outrank the message. rm-026 supersedes that claim at the next commit.
15. **Fail-set delta, not absolute green, is the pass bar when inherited failures are sibling-owned.** Record the failure set byte-for-byte (4 stale-PKCE) and classify per-test deltas before reacting: this cycle's 5→4 change was an env flip (mcp_compat metadata), not an effect of any B1 edit.

### Next-cycle context (run 634bf4516c83 additions)

- **rm-027 remainder is the only B1 debt** and gates the commit: guard test (with explicit allowlist for intentionally-unshipped historical docs), data-files +2, runtime-checkout.md re-label. (CHANGELOG entries landed in review-fix cf265a76.) The guard test also operationalizes rule 11's spirit for docs.
- **Dist validation deferred by record:** `python -m build` + `twine check dist/*` + `tools/check_package_hygiene.py dist/*` with the two rm-027 docs present was NOT run in implement/targeted_tests (partial rm-027 made it moot); explicitly folded into the commit gate (review finding #5).
- **rm-030 stays the headline** (upstream v0.11.0 catch-up + PKCE-semantics reconciliation vs oauth_auth.py:474-479); nothing this cycle changed that.
- **Commit-gate interlocks carried forward:** B1's pyproject edits vs sibling run-6d49's uvicorn bound touch the same file — reconcile at merge, never rebase B1 onto the sibling; B1 stays separate from rm-030.
- CHANGELOG Unreleased entries for B1 (user-visible: dependency-set consolidation, pyyaml CVE bound, index truthfulness, example-script trackability) — LANDED in review-fix cf265a76.

Review loop: independent review 0c534991 returned changes_required with 6 findings; review-fix cf265a76 fixed #1 (requirements-dev.txt deleted — dev extras in pyproject are a strict superset), #2 (README dev setup repointed to `pip install -e ".[dev]"`), #3 (this roadmap corrected to match disk), #4 (CHANGELOG entries landed), #5 (dist-validation deferral recorded above); #6 was engine-side bookkeeping only. Full-suite retest at /tmp/reviewfix-cf265a76-full.log. [tail restored 2026-09-23 by run 9e0b97f5d86c review-fix 48538044 — the adoption carry had truncated this line; content from refs/pull/19/head]

<!-- carried verbatim 2026-09-23 by run 9e0b97f5d86c cycle 1 batch B1 from PR #20 head refs/pull/20/head (run edd9fb12b6a4); adoption provenance, not a new cycle -->
<!-- cycle-1 additions below: run edd9fb12b6a44dec8e39428e72bf44b2 (assess 19b3441d8fd6, research ffe231c487e2) -->

Sibling-run interlock (2026-09-22, verified by fresh fetch): fork master advanced to 6b2abc7808 via MERGED PR #12 (conductor/run-c1ef27c97ab2, "Green Suite & Clean Index: PKCE test repair, gitlink purge, CI fast lane (rm-003/004/005/007)" — c1ef27c97ab2 numbering): master now has 0 empty-code_challenge sites, 0 mode-160000 gitlinks, a PR fast lane, an mcp==2.2.0 full-matrix lane, and the metadata skip guard. Consequently this run's assess findings for the 12 gitlinks and the 5 stale-test failures are BASE-relative (c1785b22e5) and RESOLVED BY MERGE at master — recorded here so they are never re-derived as new work. PR #13 (conductor/run-6d49d1e3979f @ 89865b1281: repo-wide ruff-0 lint gate + uvicorn bound + corrupt-jobs.json backup + the rm-016..rm-025 items above) remains OPEN. PR #14 (fix/pr63-pkce-test-fixtures @ 0727b69b88) is OPEN but superseded by #12's merged repair — close as superseded (housekeeping, not a roadmap item). This file seeds verbatim from 89865b1281:ROADMAP.md, the newest committed sibling state (which itself embeds the a51c rm-003..rm-015 records). Adopt-by-content remains the rule; this run's worktree sits at the shared base c1785b22e5 and carries none of the sibling implementations.

### Land the v0.11.0 catch-up — the PKCE posture is the load-bearing decision
- id: `rm-026` | track: compatibility | priority: 95.0 | status: candidate
- signals: run-edd9fb12:research, fork master 6b2abc7808 is 5 commits behind upstream 7795aa3ce8 (PRs #69-#73 = v0.11.0, released 2026-09-21, live on GitHub and PyPI: Gemini Spark OAuth client profile, dual MCP SDK 1.x/2.x support, Bot Chat session delivery, security remediation bundle — signed tokens require durable store, revocation retires+advances epoch in one SQLite txn, atomic refresh rotation, ledger watermark pagination, plan-readiness parent checks, controller contract-hash binding — loopback Agent Card, unknown-peer admission, doctor JSON gateway.pid). Decisive evidence (throwaway worktree at 7795aa3ce8, baseline interpreter): upstream test_codex_pr63_remediation.py is file-identical to the fork's PRE-#12 file yet passes 44/44 upstream because v0.11.0 relaxed PKCE to required-if-present — authorize validates only when a challenge or method is supplied (oauth_auth.py:1058-1063 upstream) and exchange skips verification when no challenge was stored (:518-521 upstream); the fork just chose the opposite posture via #12: mandatory S256 at authorize and fail-closed exchange for stored-empty challenges (contract: test_oauth_auth.py test_legacy_code_without_stored_challenge_cannot_be_exchanged). Post-#12 repaired tests mint real S256 pairs, so they pass under BOTH postures — the catch-up conflict is policy, not tests: oauth_auth.py and server.py are the hot files.
- acceptance: catch-up merges with ONE recorded decision: (a) adopt upstream required-if-present semantics — then consciously amend the fork's fail-closed exchange contract test and document the relaxation in docs/oauth.md; or (b) preserve the fork's mandatory-PKCE posture across the merge (conflict-resolve authorize/exchange deliberately, keep #12's contract test green). Either way: git rev-list --count master..upstream/master == 0 afterward (or a documented skip list); full suite green on the adopted posture at the merge result; docs/oauth.md records the decision and its rationale; upstream issue #74-aware design notes (profile-aware skills) are not silently half-adopted.
- evidence: green full-suite run at the merge result; decision note citing the upstream diff hunks; `git rev-list --count HEAD..upstream/master` at the merge; #12's contract test status in both branches.

### Canonical profile-aware skill resolution before placement and dispatch
- id: `rm-027` | track: feature | priority: 85.0 | status: implemented-pending-commit-gate (run edd9fb12b6a4 cycle 1, pre-review; see Cycle 1 outcome below)
- signals: run-edd9fb12:research, upstream issue #74 (2026-09-21, the only open upstream issue, ~850 lines) reports a production failure class: "skill exists globally but the assignee's profile cannot resolve it"; today four divergent resolution paths — server.py skill_roots/discover_skills (global dedup-first view), operator_skills.py _find_skill_dir (profile-scoped), operator_capability_manifest.py _list_profile_skills (feeds placement), operator_placement.py (NO skills hard gate: skills only affect ranking via _score_affinity, so a zero-skill target can still win placement); Fabric targets advertise skills=[] so a naive subset hard-filter would reject every Fabric node — the issue's Option A (profile owns capability) vs Option B (executor) vs Option C (two-stage) question; fork-side the same surfaces exist at the base c1785b22e5.
- acceptance: a canonical read-only resolver answers (profile, skill) -> resolvable with provenance (defined_in, available_profiles, scope) and no persisted registry (projection of live state); task creation AND reassignment validate required skills BEFORE mutation with distinct error classes skill_not_found vs skill_not_resolvable_for_assignee (actionable message listing profiles that do resolve it); placement applies skills as a hard gate scoped to the requested profile with Fabric placement unaffected; DEFERRED to a next cycle: contract/work-contract validation consuming the same resolver (operator_contract.py currently has zero skill fields — the consumer surface does not exist yet; renounced for THIS batch, not silently claimed).
- evidence: unit tests for both error classes + reassignment revalidation; placement test proving a zero-skill-match target cannot win when skills are required; upstream issue #74 replied-to/linked with the design; docs (docs/operator-mode.md capability section) updated.

### Pin the lint toolchain end-to-end and decide the ruff 0.16 posture
- id: `rm-028` | track: reliability | priority: 65.0 | status: candidate
- signals: run-edd9fb12:assess+research, ruff 0.16.7 `check . --isolated` (repo root, default rules) reports 524 findings (188 BLE001, 38 TRY004, 37 UP045, 32 I001, 31 S110, 28 F401, 16 F841, 5 F821) concentrated exactly in the files the old allowlist excluded (server.py, oauth_auth.py, token_store.py, operator_controller.py, ui_*.py); ruff 0.16.8 is current (PyPI 2026-09-22) and CI installs ruff via `-e ".[dev]"` where master's dev extras list bare `ruff` — the expanded 0.16 defaults are a standing red-switch on PR #13's repo-wide gate the moment the resolver picks >=0.16; PR #13's dev pin (>=0.15,<0.16) covers only the dev-extra path
- acceptance: CI lint job and local dev resolve the SAME pinned ruff (dev-extra pin + lint job installs from dev extras, not a floating bare name); a written decision records the 0.16 posture: either select an explicit rule set in pyproject [tool.ruff] and upgrade deliberately, or stay <0.16 with a dated revisit note; repo-wide `ruff check .` green under the pinned version in CI
- evidence: ci.yml/pyproject diff; green CI lint run at the pinned version; the decision note (PR description or docs) citing the 524-vs-61 default-rule delta

### Ship the README-referenced docs; scrub private host provenance
- id: `rm-029` | track: reliability | priority: 45.0 | status: candidate
- signals: run-edd9fb12:assess, README.md:36 links docs/vnext-capability-manifest-and-mission-ledger.md and README.md:343 links docs/runtime-checkout.md; both are git-tracked but ABSENT from [tool.setuptools] data-files (0 matches at master 6b2abc7808) — broken paths for pip-installed users; docs/runtime-checkout.md publishes /home/tony home paths, systemd unit/override paths, live service and worktree HEAD pins (dated 2026-09-05, stale) in a public repo — violates the repo's own rule "do not expose machine-specific private operational data" (AGENTS.md)
- acceptance: every relative doc link in README.md resolves inside an installed wheel (data-files extended or links repointed); runtime-checkout.md deleted, untracked, or rewritten to template form (host specifics -> placeholders) with a freshness check; docs/README.md atlas consistent
- evidence: `python -m build` wheel contains the referenced docs; grep shows no private host paths in tracked files; tools/check_package_hygiene.py passes

### Account-status banner is dead code on auth-configured deployments
- id: `rm-030` | track: correctness | priority: 35.0 | status: candidate
- signals: run-edd9fb12:assess sweep, auth-configured deployments 401 every /api request INCLUDING /api/me because the SPA sends no bearer token; the four-state account banner (ui_security me_payload -> web/src/shared/AccountStatusBanner.tsx) is unreachable precisely on the deployments that need account state most
- acceptance: EITHER the SPA obtains and attaches credentials (explicit login flow or same-origin cookie session) and /api/me returns payload under configured auth (tested, incl. unauthorized case), OR the banner is scoped/documented as local-mode-only with docs stating the auth-mode limitation
- evidence: integration test covering /api/me with and without credentials under configured auth; docs update (docs/ui-security-boundary.md or equivalent) matching the chosen behavior

### Repo-wide compile check; drift-guard the manual registries
- id: `rm-031` | track: maintainability | priority: 30.0 | status: candidate
- signals: run-edd9fb12:assess, ci.yml static job compiles a hand-maintained module list (`python -m py_compile server.py codex_core.py ...`) — at the base 30 of 59 shipped py-modules sat outside it (and 40 of 59 outside the old lint allowlist); third instance of the manual-registry rot class after rm-017's lint fix (py-modules, lint list, compile list)
- acceptance: CI compiles every tracked *.py (python -m compileall on the package or a generated list — no hand-maintained registry); a drift unit test fails when a tracked root module is missing from py-modules (the one registry that must stay curated)
- evidence: ci.yml diff replacing the manual list; drift test green and demonstrably failing on a deliberately-unregistered module

### MCP 2026-07-28 minor-spec adoption and SDK-3.0 proofing
- id: `rm-032` | track: compatibility | priority: 40.0 | status: candidate
- signals: run-edd9fb12:research, spec 2026-07-28 changelog minors: tools/list SHOULD return deterministic order for prompt-cache hits; CacheableResult ttlMs/cacheScope REQUIRED on list/read results; RFC 9207 iss validation for clients redeeming codes; mcp 2.2.0 + 1.30.0 (2026-09-07) emit MCPDeprecationWarning when ClientCredentialsOAuthProvider/PrivateKeyJWTOAuthProvider lack issuer= and when AuthSettings.validate_token_resource is unset (SDK 3.0 will require/default them); master now HAS the mcp==2.2.0 lane (PR #12) but no deprecation-proofing or determinism/assertion coverage of these minors (rm-009 covered lanes + protocol-revision assertion only)
- acceptance: tools/list ordering deterministic (sorted registration or explicit order) locked by test; ttlMs/cacheScope set deliberately wherever the SDK surfaces the knobs (conservative values acceptable); zero MCPDeprecationWarnings under mcp 2.2.0 with warnings-as-errors on the affected import paths; rm-009's remaining 2.1 behavior-change audit note (exception-text hiding #3314, 4 MiB OAuth body cap #3336) folded here or closed there
- evidence: extended test_mcp_compat.py tests; green 2.2.0-lane CI run with the deprecation assertion active

### Bound pyyaml (last bare runtime dependency)
- id: `rm-033` | track: reliability | priority: 50.0 | status: candidate
- signals: run-edd9fb12:assess, pyproject [project] dependencies at master 6b2abc7808 still list bare `pyyaml` (and bare `uvicorn` until PR #13 merges rm-023's `>=0.30,<1`); PyPI latest pyyaml 6.0.3 (2026-09-22 probe); prior cycles already declared pyyaml the last bare runtime dep after rm-023 — formalizing with an id so it has an owner and acceptance
- acceptance: pyproject carries `pyyaml>=6,<7` (or reviewed equivalent); CI installs the reviewed range green; cap moves become deliberate changelog events
- evidence: pyproject diff; green CI; CHANGELOG note if the range ever narrows

## Cycle 1 addendum — run edd9fb12b6a4 (2026-09-22)

Assess (attempt 19b3441d8fd6, at the shared base c1785b22e5): authoritative CI-shaped suite (HERMES_HTTP_TEST=1, serial, baseline interpreter mcp 2.0.0/pytest 9.1.1) exits non-zero with exactly 5 failures — the 4 stale-PKCE tests plus the uninstalled-metadata test; both classes are RESOLVED BY MERGE at master 6b2abc7808 (PR #12) and are not re-opened here. Fresh findings folded as items: ruff 0.16 default-rule expansion vs the floating lint toolchain (rm-028), README links to unshipped wheel docs + private host provenance in runtime-checkout.md (rm-029), auth-mode account-banner dead code (rm-030), manual py_compile registry rot (rm-031), bare pyyaml formalized (rm-033). Security sweep came back clean at the base (no shell=True/verify=False/eval/exec/pickle/mktemp in non-test code; AESGCM + 0o600 + secrets in token_store; export allowlist + size cap + stat/read TOCTOU guard; TLS-or-loopback-trusted-proxy gating with non-loopback warning).

Research (attempt ffe231c487e2): upstream frozen at 7795aa3ce8/v0.11.0 (no new commits since 2026-09-21; single open issue #74 -> rm-027); v0.11.0 catch-up is the headline with the PKCE-posture decision as its load-bearing fork point (rm-026 — proven via throwaway worktree that upstream's file-identical tests pass 44/44 because PKCE became required-if-present); MCP spec revision still 2026-07-28 with minor-spec residuals (rm-032); Python 3.10 EOL 2026-10-31 already covered by rm-024; ecosystem pins: mcp 2.2.0/1.30.0, pyyaml 6.0.3, uvicorn 0.53.0, cryptography 50.0.1, ruff 0.16.8. Competitive scan (agentgateway ~5k stars active agentic proxy; fastapi_mcp ~12k stars; sparfenyuk/mcp-proxy stale since 2026-07) confirms the local-first operator control plane with loopback OAuth and confinement remains the differentiator — no roadmap change from that axis this cycle.

Suggested next-cycle order from this run: rm-026 (decision + catch-up), rm-027 (skill resolution), rm-028 (lint toolchain — small, unblocks PR #13's gate), rm-033 (pyyaml), rm-029..rm-032 as capacity allows. PR #14 close-as-superseded is free housekeeping alongside any of these.

## Cycle 1 outcome — run edd9fb12b6a4 (2026-09-22; pre-review, pre-commit-gate)

Batch B1 = rm-027 (canonical profile-aware skill resolution) implemented as working-tree changes in worktree run-edd9fb12b6a4-edd9fb12 (base c1785b22e5, uncommitted — commit/merge are later gates). All five touched surfaces verified byte-identical base→master(6b2abc7808) BEFORE coding, so the change is portable to the green floor without conflict. Delivered: (1) new module `operator_skill_resolution.py` — read-only canonical (profile, skill) resolver with provenance (SkillResolution: resolvable/found_paths/profiles/scope) unifying the four divergent paths, recursive SKILL.md walk mirroring `_find_skill_dir`, bounded+sorted scans, no persisted registry; stage-1 `validate_required_skills` (SkillNotFoundError listing available skills) and stage-2 `validate_assignee_skills` (SkillNotResolvableForAssigneeError naming resolvable profiles; owner/tony controller personas pass through). (2) `operator_mission_plan.hermes_plan_create` validates every node's declared skills before any DB write — fail-closed in dry-run AND direct — with a distinct SKILL_NOT_FOUND envelope. (3) `operator_placement`: pure `required_skills_missing` hard filter in `_apply_hard_filters` (zero-skill/Fabric targets stay placeable for skill-less requirements; score_targets stays I/O-free) plus stage-2 assignee validation in `hermes_placement_score` before any decision is built — revalidated on every call, which covers reassignment semantics (placement is the assignment/reassignment surface; no separate 'reassign' entry point exists in the operator surface). (4) Tests: test_operator_skill_resolution.py (24 tests across resolver/error-classes/plan/placement, including re-run fail-closed and zero placement_decisions rows) + test_operator_placement.py gate-contract update (the one intentional behavior change: a required-skill target that lacks the skill is now filtered, not merely outranked).

Validation (attempts 2ad219b3 targeted, 890164d4 full; baseline interpreter mcp 2.0.0/pytest 9.1.1, HERMES_HTTP_TEST=1, serial): targeted 43/43 across the five changed surfaces; adjacent capability/skills suites 38/38; full suite exit 1 with EXACTLY the 5 inherited failures (4 stale-PKCE + env-dependent mcp_compat metadata) — byte-identical to the clean-base assess baseline, delta 0 new failures. Static: ruff --isolated clean on both new files (TRY004 + F401 fixed in-loop); pre-existing touched files unchanged at 4 findings. Known gaps deferred with the item: docs/operator-mode.md capability/placement section still unwritten (implement turn was cut off pre-run of its own new tests — see rule 16); upstream issue #74 reply/link happens at ship time.

Review loop (independent_review c21a4ae6 → approve_with_changes, 8 findings; fixes folded by attempt e5f4ae67): (a) HIGH grammar divergence fixed — the resolver now IMPORTS operator_skills' `_VALID_NAME_RE` + 64-char cap verbatim instead of a kebab-only copy (dots/underscores resolve; >64-char names are rejected exactly like the executor); (b) MED placement dead zone closed — `load_manifest_targets` enriches profile-kind targets with the resolver's recursive per-profile walk (union with the manifest snapshot), so a nested-only skill keeps a capable target placeable while `_apply_hard_filters` stays pure; (c) MED found_paths now report OBSERVED SKILL.md directories from the walk, never a synthesized root/name join; (d) MED roadmap honesty — the contract-validation acceptance clause above is recorded as deferred (consumer surface has no skill fields yet), and the test count is corrected 16→24; (e) LOW bounds docstring made honest (result-size + traversal caps, one walk per root per validation call) with a per-call `_name_maps` cache killing the O(skills×profiles) re-walk and a deterministic lexicographic-DFS traversal; (f) LOW the server third-root (`<root>/skills` MCP presentation) scoping gap is DOCUMENTED in the module docstring as deliberate execution-view mirroring (fails closed rather than resolving unexecutable skills); (g) LOW `hermes_plan_validate` now consumes stage-1 too with the same SKILL_NOT_FOUND envelope as create (validate and create cannot disagree); (h) 6 new regression tests lock all of the above. Retest after fixes: targeted 49/49, full suite = the same 5 inherited failures only, ruff --isolated new files clean, pre-existing files unchanged vs base blobs.

### Cycle 2 learnings — prevention rules (run edd9fb12b6a4)

11. **Pre-verify validation digests with the FULL 40-char base sha.** The engine's digest embeds `base:<sha>`; recomputing with the short sha silently mismatches the fold gate (cost one re-dispatch: attempt 7a6b6dc5 rejected for exactly this). Use `hermes_conductor.validation_policy.validation_digest('<full-sha>', worktree)`.
12. **Operator error envelopes put `code`/`safe_message` at the TOP level** (`op.make_error_envelope`); `error` is the legacy sanitized string. Assert `out["code"]`, never `out["error"]["code"]`.
13. **Side-table schemas initialize on write-mode connects**: `operator_placement._connect(write=True)` runs `_init_placement_tables`; reading `placement_decisions` through `mission._connect` read-only raises OperationalError.
14. **The default profile's home aliases the hermes root**, so global-root skills resolve for profile `default` (scope `mixed`, profiles=('default',)) — mirroring `_find_skill_dir('default', ...)`. Don't model a 'global-only' scope that nothing produces.
15. **Keep `_apply_hard_filters` pure (I/O-free)** — `score_targets`'s contract depends on it; assignee-level validation belongs at the score/decision entry point, where re-running placement gets reassignment revalidation for free.
16. **Run every NEW test file before ending an implement turn.** The cut-off implement phase left test_operator_skill_resolution.py unexecuted; targeted_tests then caught 6 fixture bugs (mkdir'd SKILL.md as a directory, missing profile-config parent, wrong envelope keys, duplicate seeded mission row, wrong DB helper, invented 'global' scope). A suite that has never executed is not evidence.
17. **Full-suite 'passed' at the pre-#12 base means zero NEW failures vs the clean-base baseline** (5 inherited: 4 stale-PKCE owned by merged PR #12's repair on master + env-dependent metadata). Always diff the FAILED ids against the clean-base log (/tmp/assess-19b3441d/pytest-full.log this cycle) before calling a regression.

### Live state interlock (verified 2026-09-22 at compound time)

- fork master still 6b2abc7808 (green floor); upstream frozen at 7795aa3ce8/v0.11.0.
- Open fork PRs now #13 (lint gate + uvicorn), #14 (stale-PKCE fixtures — content-overlaps #16, supersede candidate), #15 (v0.11.0 adoption, mandatory-S256 posture preserved), #16 (sibling run fd2bc85ff599 'Truthful Green Baseline': 5-site PKCE re-bind + fail-closed pin + token_store dead-block rm + pyyaml>=6,<7 — adopts #14's content), #17 (sibling run 684b97865efc: updater checkout sentinel, sentinel-workflow pin, bounded pyyaml, dompurify drop).
- rm-026 (v0.11.0 catch-up) is claimed in-flight by PR #15 AND depends on #16's green baseline (per that run's interlock); rm-033 (pyyaml bound) is now content-in-flight via BOTH #16 and #17 — next cycle must reconcile before touching pyproject dependencies. rm-028's floating dev-ruff remains the standing red-switch behind PR #13's gate.
- rm-027's change set carries zero file collision with #13/#15/#16/#17; its port path to the green floor is clean (byte-identical surfaces pre-verified). Rebase/topology is Conductor's call at the commit gate.

### Next-cycle candidates from this run (post-rm-027)

- Finish rm-027's deferred slice at ship time: docs/operator-mode.md capability/placement section + upstream issue #74 reply linking the design.
- rm-026 disposition decision is now THREE-way (#14 vs #16 vs #15) — reconcile supersessions first, then the PKCE-posture decision (fork mandatory-S256 vs upstream required-if-present) is the only load-bearing call.
- rm-028 (pin lint toolchain; 524 default-rule findings vs floating ruff) and rm-031 (repo-wide compile, drift-guard) remain the highest-value unclaimed reliability items; rm-030 (auth-mode banner dead code) is a small self-contained correctness win.
- Watch test_mcp_compat metadata under CI interpreters (rule 17's second class) — its master-side guard is PR #12's; this base still fails it locally.

<!-- 2026-09-23 run 9e0b97f5d86c additions (assess fda6097ae, research c476237ca); render footer stays last -->

## Cycle 1 digest — run 9e0b97f5d86c (2026-09-23; repository-maintenance cycle 1)

Base: the converged fork master line 4b958379d6 (rm-026-lineage merge 9a90620d5c + post-merge fixes; prior cycle PRs #12/#13/#15/#16/#17 all merged; fork is 0 commits ahead of upstream v0.11.0 content). Baseline re-verified this run: full suite on the baseline interpreter (py3.11.15, mcp 2.2.0, HERMES_HTTP_TEST=1, serial) EXIT 0 — ~1507 passed / 5 skipped, zero failures, including the formerly stale PKCE tests, now real S256 pairs. The green baseline stands; every item below is incremental.

External evidence probed 2026-09-23: upstream asimons81 master unchanged at 7795aa3c (v0.11.0, 2026-09-21) — no catch-up delta; open upstream items are PR #75 (the fork-lineage packaging batch: delete requirements.txt/-dev, pyyaml>=6.0.3,<7 citing CVE-2026-31132, 12 gitlinks dropped, nightly+concurrency CI; checks pending, Vercel-auth fail) and issue #74 (profile-aware skill resolution). PyPI floors: PyYAML 6.0.3 (CVE-2026-31132 fixed), mcp 2.2.0 (unchanged; classifiers officially 3.10–3.14), croniter 6.2.4 (within >=2.0,<7), uvicorn 0.53.0 (within >=0.30,<1), cryptography 50.0.1 (fork bound is floor-only >=42). MCP spec latest revision still 2026-07-28; the notable spec-era development is SEP-2322 multi-round-trip shipping in SDK 2.2.0. Python 3.10 EOL 2026-10-31 confirmed (rm-024 stands; new evidence: mcp 2.2.0 classifiers make 3.13/3.14 lanes dependency-safe today).

Id note: the id space drifted across parallel runs — this file uses rm-028 twice (skill-resolution gate, lint re-baseline) and fork PR #20 self-labels rm-027. New ids rm-032..rm-042 below are assigned by this run against this file; treat titles + signals as canonical and ids as handles.

### Merge the stranded fork PRs #19/#20 onto the converged master
- id: `rm-032` | track: reliability | priority: 110.0 | status: implemented (pending commit gate, run 9e0b97f5d86c cycle 1, 2026-09-23; PRs #19+#20 adopted by content)
- signals: conductor.run-9e0b97f5:research-R2 — gh pr list codeo1io: #19 (packaging consolidation; same content as upstream PR #75) and #20 (canonical profile-aware skill resolution, operator_skill_resolution.py; the fork half of upstream issue #74) both open with all-green check rollups at open time but mergeable=CONFLICTING/DIRTY vs the converged master; master lacks operator_skill_resolution.py entirely and still tracks requirements.txt + requirements-dev.txt
- acceptance: both PRs rebased with conflicts resolved against master (a93aeb0b1d or later); packaging resolution keeps the converged pyproject + croniter>=2.0,<7 while adopting the manifest deletion + pyyaml>=6.0.3,<7 floor; skill resolution resolution reviewed against placement-ranking tests; full suite green in CI shape post-rebase; #19 merged = CVE floor landed; #20 merged = operator_skill_resolution.py on master; upstream PR #75 head refreshed from the landed state (stewardship)
- evidence: merged PR links; git log on master showing both commits; `ls operator_skill_resolution.py`; pyproject pyyaml line; green CI run on master post-merge

### pyyaml floor >=6.0.3,<7 (CVE-2026-31132)
- id: `rm-033` | track: security | priority: 100.0 | status: implemented (pending commit gate, run 9e0b97f5d86c cycle 1, 2026-09-23; explicit pyproject edit — #19 never carried the hunk)
- signals: conductor.run-9e0b97f5:research-R3 — PyYAML 6.0.3 is latest (probed 2026-09-23); CVE-2026-31132 named fixed in 6.0.3 by upstream PR #75's changelog text; fork pyproject pyyaml>=6,<7 admits vulnerable 6.0–6.0.2
- acceptance: floor raised to >=6.0.3,<7 in pyproject.toml (and requirements.txt only if it still exists at implementation time); CHANGELOG Unreleased records the security floor bump; suite green
- evidence: pyproject diff; full-suite green run on the changed tree; CHANGELOG diff

### DCR lifecycle hygiene: RFC 7592 management or TTL eviction; make HERMES_GPT_OAUTH_DCR=0 close the route
- id: `rm-034` | track: security | priority: 85.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F1/F3 — oauth_auth.py:143 MAX_DYNAMIC_CLIENTS=64; :371-375 returns 429 at cap; every registration durably persisted (:930-932) and restored on boot (:1015); cleanup() (:429-436) never prunes dynamic_clients and DynamicClient has no expiry — 64 anonymous POSTs to /oauth/register permanently block ChatGPT re-registration, restart-persistent; as_public_dict (:308-315) omits registration_access_token/registration_client_uri so RFC 7592 management is absent; _dcr_enabled docstring (:45-47): the DCR=0 knob hides advertising only — the route still answers, making the gemini-spark.md 'no DCR by design' contract unenforceable
- acceptance: one eviction path implemented — (a) RFC 7592 (registration_access_token + GET/DELETE /oauth/register/{client_id}) or (b) age-based TTL eviction in cleanup() persisted with the registry bundle; POST /oauth/register returns 404/501 when HERMES_GPT_OAUTH_DCR=0 (advertising and behavior agree); new tests: exhaust capacity → evict → registration succeeds again; DCR=0 route-closed; full suite green
- evidence: oauth_auth/server diffs; test additions in test_oauth_dynamic_registration.py; docs/oauth.md + docs/gemini-spark.md reconciled; RFC 7592 field list cited in the PR/commit message

### Document the OAuth knobs (HERMES_GPT_OAUTH_DCR, HERMES_GPT_OAUTH_PKCE_MODE); reconcile the no-DCR doc claims
- id: `rm-035` | track: docs | priority: 55.0 | status: candidate (pairs with rm-034)
- signals: conductor.run-9e0b97f5:assess-F2 — docs/oauth.md:21 claims 'no dynamic client registration' while server.py:3160-3170 serves /oauth/register by default; docs/gemini-spark.md:30/:129 rest on the no-DCR premise; zero grep hits for either env var across docs/ + README
- acceptance: docs/oauth.md documents both env names with defaults and exact gating semantics (current: advertising-only); the no-DCR claims rewritten to describe actual behavior (and the rm-034 change when it lands); per AGENTS.md documentation rules the distinction between default-on advertising and enforcement is explicit
- evidence: docs diff; `grep -rn HERMES_GPT_OAUTH_ docs/ README.md` shows both knobs documented

### Dead double-raise in _authenticate_client (merge artifact)
- id: `rm-036` | track: maintainability | priority: 30.0 | status: implemented (pending commit gate, run 9e0b97f5d86c cycle 1, 2026-09-23)
- signals: conductor.run-9e0b97f5:assess-F3 — oauth_auth.py:1412-1413 two identical consecutive `raise OAuthError("invalid_client", ...)`; second is unreachable; verified verbatim at origin/master tip a93aeb0b1d
- acceptance: one raise deleted; zero behavior change; targeted oauth tests green
- evidence: one-line diff; targeted test run

### Unify the two gateway.pid parsers
- id: `rm-037` | track: maintainability | priority: 40.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F5 — operator_diagnostics.py:291 requires isinstance(state_pid, int); operator_workspace.py:150-160 docstring says 'Accept int or numeric string'; mission gateway probes route through the strict copy (operator_mission.py:651) — a string-pid gateway reports not-running in mission while workspace reports running (rm-022 drift class)
- acceptance: one shared reader with a documented pid contract; both call sites consume it; parametrized tests cover int and numeric-string forms for both consumers
- evidence: dedupe diff; new parametrized test green

### publish.yml runner migration + stale CI comments
- id: `rm-038` | track: reliability | priority: 45.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F6 — publish.yml:14 still runs-on: self-hosted although PR #21 moved CI to GitHub-hosted runners; ci.yml:33/:142 comments still describe the retired self-hosted serial runner — next tag push queues the publish job on infrastructure that no longer exists
- acceptance: publish job moved to ubuntu-latest with the pypi environment + id-token trusted-publishing path verified, OR self-hosting explicitly re-affirmed with recorded rationale; stale comments refreshed; a workflow_dispatch/dry-run validation path documented
- evidence: workflow diffs; validation run or dispatch evidence

### macOS confinement: bind all runtime roots; harden env-shebang parsing
- id: `rm-039` | track: correctness | priority: 35.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F4 — runner_confinement.py:351-355 passes only runtime_roots[0] into _macos_sandbox_profile, so the env-shebang interpreter bind added by 89848d4238 is Linux-effective only; _env_shebang_interpreter returns None for `env -S` shebangs and mis-parses trailing flags
- acceptance: _macos_sandbox_profile binds every runtime root (interpreter root alongside argv[0]); env -S + trailing-flag shebangs parsed or explicitly rejected with a logged reason; tests for both shebang shapes
- evidence: runner_confinement.py diff + new tests green

### hermes_job_wait occupancy bound on the shared loop executor
- id: `rm-040` | track: reliability | priority: 25.0 | status: candidate
- signals: conductor.run-9e0b97f5:assess-F10 — operator_job_supervisor.py:28 MAX_WAIT_SECONDS=120; six long-blocking tools now park on the loop's default executor (asyncio.to_thread; capacity min(32, cpu+4)) with no per-tool bound; concurrent long-parks can starve owner_run_command/codex_start; test_server_nonblocking.py pins only 2 of the 6
- acceptance: either a recorded occupancy rationale or a semaphore/bound on concurrent job_wait parks; the nonblocking pin test extended to the full offloaded set
- evidence: diff + extended tests green

### CHANGELOG hygiene: fused bullet + Unreleased section for the converged features
- id: `rm-041` | track: docs | priority: 20.0 | status: implemented (pending commit gate, run 9e0b97f5d86c cycle 1, 2026-09-23)
- signals: conductor.run-9e0b97f5:assess-F8 — CHANGELOG.md:12 fused bullet ').- Support MCP Python SDK 2.x'; no Unreleased section for post-0.11.0 user-visible changes (DCR endpoint + knobs, event-loop offload of 6 tools, owner-command TMPDIR routing, JSON gateway.pid handling, croniter dependency at tip, CI runner move)
- acceptance: bullet repaired; Unreleased section enumerates the user-visible converged changes; AGENTS.md release-discipline review list satisfied
- evidence: CHANGELOG diff

### SEP-2322 multi-round-trip: capability study, then InputRequired approval handshake
- id: `rm-042` | track: compatibility | priority: 50.0 | status: candidate (design-gated)
- signals: conductor.run-9e0b97f5:research-R5 — installed mcp 2.2.0 ships SEP-2322 (client driver mcp/client/_input_required.py, DEFAULT_INPUT_REQUIRED_MAX_ROUNDS=10; server handling mcp/server/mcpserver/tools/base.py:93/:170/:181; types in the new top-level mcp_types package); the repo implements and documents none of it (zero grep hits; docs/mcp-compatibility.md stops at the 2026-07-28 stateless note); natural use: interactive human approval for direct operator mutations (dry-run → InputRequired confirm), which must degrade cleanly on the mcp 1.28.1 lane via mcp_compat.HermesMCP
- acceptance: study recorded (wire shape, SDK-2-only constraints, 1.28.1 degradation matrix, client-support reality); if adopted: one operator mutation tool returns InputRequiredResult with a dual-SDK test proving graceful refusal on 1.x; docs/mcp-compatibility.md gains a SEP-2322 section
- evidence: study notes or implementation diff + tests; compat doc diff

### Run-9e0b97f5 next-cycle context
- rm-032 first (merge-gate): it unblocks rm-033 (subsumed) and restores the skill-resolution work; rm-036/rm-041 are trivial slices to bundle with any batch; rm-034+rm-035 move together (code + docs for the same contract).
- rm-024 gains dependency-safety evidence (mcp 2.2.0 classifiers 3.10–3.14): the 3.13 lane can land before the 3.11 floor bump; the tomli conditional drops only with the floor.
- cryptography>=42 is the last floor-only (unbounded-above) runtime dep; upstream PR #75's convention treats floors as sufficient — record an explicit accept/adopt decision rather than defaulting to a cap.
- No new MCP SDK action: 2.2.0 is latest and within the CI lanes; spec revision unchanged.
## Cycle 1 outcome — run 9e0b97f5d86c (2026-09-23; pre-review, pre-commit-gate)

Batch B1 "Merge-Gate Closure & CVE Floor" (prioritize attempt 6a7a738b: rm-032 → rm-033 → rm-036 → rm-041) implemented as working-tree changes in worktree run-9e0b97f5d86c-9e0b97f5 (base 4b958379d6, uncommitted — commit/merge are later gates). Delivered by content-adoption rather than re-implementation: (1) rm-032 — stranded PRs #19 (packaging consolidation: requirements.txt + requirements-dev.txt deleted, README/docs repointed to pyproject-only, .gitignore `!examples/*.example.ps1` negation) and #20 (canonical profile-aware skill resolution: new operator_skill_resolution.py (+322) with a 24-test suite, operator_placement.py hard-filter + stage-2 assignee validation + manifest enrichment, operator_mission_plan.py create/validate skill gates) adopted via per-file `git merge-file` three-ways because plain patch apply fails on convergence-induced context drift; each PR's cycle-history ROADMAP blocks were carried verbatim as adoption provenance (76 + 91 lines, stray conflict-marker remnant dropped). (2) rm-033 — pyproject pyyaml `>=6.0.3,<7` (CVE-2026-31132) as an EXPLICIT edit because neither PR carried the pyproject hunk, with croniter `>=2.0,<7` retained from origin/master (PR #22) so the runtime dependency survives requirements.txt deletion (final pyproject vs origin/master differs by the pyyaml line only). (3) rm-036 — oauth_auth.py:1413 dead duplicated raise removed (single raise retained). (4) rm-041 — CHANGELOG fused 0.11.0 bullet split into two proper bullets + new `## Unreleased` section recording the batch.

Validation (implement attempt a46024e0, targeted_tests attempt 4d1a4b87; baseline interpreter py3.11.15 / mcp 2.2.0 / pytest 9.1.1, CI shape HERMES_HTTP_TEST=1 serial): `ruff check .` repo-wide clean (0.15.10); targeted 118/118 across the five changed-surface test modules; full suite EXIT 0 in two independent runs ([100%], 0 F/E, 1521 marks); validation digest `validation:v1:aca975a8…` independently re-derived post-run and matched the dispatch digest. Net tree: 12 tracked files +380/−15 plus 2 new untracked modules (+764).

Carried debt recorded for the commit gate: run 634bf4516c83's rm-027 remainder (shipped-docs guard test, data-files registration of docs/runtime-checkout.md + docs/vnext-capability-manifest-and-mission-ledger.md, runtime-checkout.md historical re-label) is NOT in this batch and stays open per that run's own outcome record; PRs #19/#20 should be closed-as-adopted when this lands. PR #19's CHANGELOG claimed the pyyaml floor its branch never carried — closed by this cycle's explicit edit.

### Cycle 1 learnings — prevention rules (run 9e0b97f5d86c; rules 1–17 above remain in force)

18. **Roadmap status labels drift; verify by content at HEAD.** 12 items recorded open/pending were already landed by parallel-lineage merges. Prioritize/stewardship phases must re-derive status from the tree (grep / git ls-files / diff-vs-master), not from the file's status field.
19. **Adopt stranded PRs by per-file blob three-way, not patch apply.** After a convergence rewrite, `git apply` fails on context drift; `git merge-file <current> <merge-base-blob> <pr-head-blob>` per file resolves deterministically. The only true conflicts were ROADMAP cycle-digest appends — resolved by carrying each side's history verbatim (current file authoritative per the render-footer override rule).
20. **Verify the dependency manifest against origin/master, never against intention.** A mid-run `git checkout origin/master -- pyproject.toml` silently failed and dropped PR #22's croniter line; `git diff origin/master -- pyproject.toml` at the end caught it. Manifest interlocks (deleting requirements.txt while master added croniter there) are exactly where silent loss happens.
21. **PR claims are not PR state.** PR #19's CHANGELOG says "pyyaml>=6.0.3,<7 in pyproject" while its branch never carried the hunk (empty pyproject diff vs master). Check the deliverable blob, not the description, before declaring subsumption.
22. **pytest -q wraps progress marks at 72 columns — count across ALL lines.** A last-line dot count (46) vs a prior run's (49) manufactured a phantom lost-tests anomaly; reconciled via per-file `--collect-only | grep -c '::'` (118 == 118). Judge by exit code + absence of F/E (standing rule); when counting, count the whole log.
23. **Confirm no-change digest turns by re-derivation.** For fix/test-bearing phases that change nothing, copying the dispatch digest verbatim is correct — and provably so by re-deriving it (hermes_conductor.validation_policy.validation_digest with the FULL 40-char sha) before emitting; the fold gate's re-derivation then cannot surprise.

### Next-cycle context (run 9e0b97f5d86c cycle 1 → cycle 2)

- rm-034 (DCR lifecycle / RFC 7592) + rm-035 (OAuth env docs reconciliation) are the designated next headline — Medium assess findings (unauthenticated /oauth/register, 64-client cap, durable persist + boot restore, no eviction), and the standards path (registration_access_token / registration_client_uri) is the canonical fix.
- rm-012 and rm-042 are the SAME work (SEP-2322 multi-round-trip study) under two ids — reconcile to one item before the next prioritize; the in-file rm-026..rm-029 duplicate-namespace drift (two prior blocks) should be renumbered once, carefully, at a low-risk moment.
- rm-008 (branch protection) remains an org-settings action outside the tree — slot it at the shipping gate. rm-024 (3.13 lane) is now dependency-safe (mcp 2.2.0 classifiers 3.10–3.14) and rides any CI-touching batch; cryptography stays floor-only (>=42) by prior decision.
- If this batch commits: close PRs #19/#20 as adopted-by-content; the rm-027 remainder (docs data-files + guard test) is small and pairs naturally with rm-035's docs pass.

<!-- managed by hermes-roadmap render; do not edit by hand -->
