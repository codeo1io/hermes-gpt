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
- id: `rm-026` | track: reliability | priority: 110.0 | status: implemented-on-master (verified 2026-09-22, run 6efbf603 roadmap: `git merge-base --is-ancestor 7795aa3ce8 HEAD` true at fork HEAD 5765b571b2; docs/gemini-spark.md in-tree; full serial suite green there incl. the formerly-stale PKCE tests)
- signals: conductor.run-684b9786:research-C1, upstream asimons81/hermes-gpt v0.11.0 released 2026-09-21 (PyPI hermes-gpt==0.11.0 live; CHANGELOG.md@upstream/master); merge-base 9f537106e9..upstream/master 7795aa3ce8 = exactly 5 commits (PRs #69-#73): dual MCP SDK 1.28.1+/2.x support, Codex alias return-signature fixes, opt-in Gemini Spark OAuth client profile (docs/gemini-spark.md), profile-aware session history + Bot Chat tools, Windows-portable token-store lock, security remediation bundle (signed tokens require durable store; revocation retires+advances epoch in one SQLite txn; atomic refresh rotation; ledger watermark pagination; plan-readiness parent checks; controller contract-hash binding), loopback Agent Card + unknown-peer admission, doctor JSON gateway.pid. The remediation bundle is the upstream-canonical fix for the 4 stale-PKCE failures this run's assess reproduced fresh at c1785b22e5 (test_codex_pr63_remediation.py:348,492,812,941) and for rm-018's dropped mint-side question
- acceptance: the 5-commit upstream delta merges with oauth_auth.py/server.py/token_store.py conflicts resolved deliberately (sibling rm-003/rm-016/rm-017 work reconciled by content per the cycle-1 interlock note, not re-implemented); full suite green on the baseline interpreter post-merge; PKCE tests exercise upstream remediation semantics; version/docs line adopts 0.11.0 or a fork-equivalent entry
- evidence: post-merge full-suite run green (serial, HERMES_HTTP_TEST=1, baseline venv); merge commit message records conflict resolution decisions; docs/gemini-spark.md present in-tree

### Bound pyyaml (the last bare runtime dependency)
- id: `rm-027` | track: reliability | priority: 55.0 | status: implemented
- signals: conductor.run-684b9786:research-C4 + run-6d49d1e3 next-cycle note, pyproject.toml [project] dependencies lists `pyyaml` unbounded — the only bare runtime dep left after rm-023; PyPI latest 6.0.3 (2026-09-21 probe); yaml parsing sits on the operator config/skills path
- acceptance: pyproject pins `pyyaml>=6,<7`; CI installs the bounded range green; cap moves become deliberate changelog events (rm-023 policy)
- evidence: pyproject diff + green CI on the bounded range; CHANGELOG note when the cap moves. Cycle-2 implement (2026-09-22, attempt 06181fb4): pyproject.toml:20 now `pyyaml>=6,<7` (tomllib parse ok), CHANGELOG Unreleased entry added; full serial suite delta-zero vs the 5-failure assess baseline. CLOSED 2026-09-22 (run 6efbf603 roadmap): the bound is on master (pyproject.toml:20 `pyyaml>=6,<7` at HEAD 5765b571b2) and that push's CI run (success 01:41Z) validated the bounded range. Residual: the CVE-2026-31132 floor raise (>=6.0.3) is tracked as rm-033

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
- id: `rm-026` | track: compatibility | priority: 115.0 | status: implemented-on-master (verified 2026-09-22, run 6efbf603 roadmap: upstream v0.11.0 tip 7795aa3ce8 is an ancestor of fork HEAD 5765b571b2; PKCE tests green on that push — the local re-binds were superseded by upstream adoption as this item required)
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
- id: `rm-029` | track: maintainability | priority: 22.0 | status: implemented-on-master (verified 2026-09-22, run 6efbf603 roadmap: `git ls-files -s | awk '$1==160000'` = 0 entries at HEAD 5765b571b2)
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

<!-- cycle-3 additions below: run 6efbf6037da942e491b6e0cb037305d3 (assess 495882cf89dc, research ff0062bfa337) — ids continue at rm-032. NOTE: rm-026..rm-029 are each used TWICE above (runs 684b97865efc and fd2bc85ff599 wrote overlapping id ranges before either merged); disambiguate by run prefix and reconcile the ids at the merge gate; from rm-032 on, ids must stay unique -->

## Cycle 3 research digest — run 6efbf603 (2026-09-22)

External evidence probed 2026-09-22 (assess 495882cf + research ff0062bf): upstream asimons81 master is FROZEN at v0.11.0 (7795aa3ce8; PyPI 0.11.0; verified an ancestor of fork HEAD) — rm-026 satisfied, no catch-up pending. Upstream PR #75 (packaging consolidation) is authored FROM this fork's lineage (head conductor/run-634bf4516c83 == fork PR #19, run 634bf4516c83), upstream mergeable_state=blocked with ZERO CI runs on its head sha 3a38d980 — landing fork PR #19 on a green fork master, then rebasing #75, is the path upstream. pyyaml CVE-2026-31132 is fixed in 6.0.3; our `>=6,<7` bound still admits vulnerable 6.0.2. ruff 0.16.8 is current while the dev pin is `>=0.15,<0.16`. Python 3.10 EOL 2026-10-31 confirmed (39 days out). MCP spec revision 2026-07-28 remains the latest published base, but the SKILLS EXTENSION reached published status 2026-09-18 (spec repo commits ddbee69a/406273f8, PR #3372) — skill-resolution semantics are now normative for MCP servers. The only open fork items are our own PRs #19 (packaging) and #20 (rm-028 skill resolution, run edd9fb12b6a4); both wait on a green master.

### Re-green master: remove the private-runtime cron.jobs import from hermes_cron_create
- id: `rm-032` | track: reliability | priority: 130.0 | status: implemented-pending-commit-gate (base guard test landed in tree; master-side repair staged as .conductor/patches/rm-032-cron-repair.patch awaiting the commit gate — origin/master itself is still red until the patch lands)
- signals: conductor.run-6efbf603:assess-critical, origin/master 927680eb20 (converge merge 9a90620d5c, 2026-09-22 03:07Z) added call-time `from cron.jobs import parse_schedule` in hermes_cron_create (operator_cron.py:981 at tip 4b958379d6); cron.jobs exists only in the private Hermes agent runtime (/home/agent/.hermes/hermes-agent/cron/jobs.py) — clean installs get ModuleNotFoundError; all 9 CI test lanes fail 5 cron-create tests (runs 03:07–03:39Z all red; last green push 5765b571b2 01:41Z); reproduced both directions in a detached worktree at origin/master
- acceptance (CORRECTED 2026-09-22 by implement 07e9164d, superseding the research wording above): the landed master tests assert the STRUCTURED schedule dict (test_operator_cron.py cron-create family, incl. test_cron_create_scheduler_contract_model_fields), so persisting RAW strings would fail master's suite — the repair keeps the structured schema via a repo-local self-contained port of parse_schedule (durations, clock times, weekday phrases, 5-6-field cron, ISO once, 'in Nm'), drops the cron.jobs import, and keeps croniter OPTIONAL (not a declared dependency; structural field check when absent). Remaining acceptance: patch lands on master tip; the 5 cron-create tests pass with cron unimportable (PROVEN pre-land); master CI green again (gate-side)
- evidence (pre-review): defect reproduced pre-patch (guard rule-1 FAIL; exactly the 5 CI failures with cron blocked); post-patch test_operator_cron.py 32/32 green with cron BLOCKED and importable; ruff clean; patch applies clean via git apply --check to pristine 4b958379d6; full serial suite at the patched tip 0 FAILED/ERROR (/tmp/rm032-full-07e9164d.log); prevention guard test_no_private_runtime_imports.py green at base and collected in the base full suite
- review record (cb7b68c3 PASS, 3 non-blocking; fixed in review-fix d871caf3 2026-09-22): F1 FIXED — the no-croniter structural branch silently accepted semantically-invalid expressions ('99 99 * * *', '0 9 * * 8', '61 24 32 13 *'); now folds a per-field numeric range check (minute 0-59, hour 0-23, dom 1-31, month 1-12, dow 0-7 — 7 is croniter's Sunday alias; names/wildcards skipped) into that branch; battery: 6/6 invalid rejected and 7/7 valid accepted with croniter BLOCKED, rejection parity with the native private parser with croniter present, cron family 32/32 both directions, ruff clean; regenerated patch (+216/-5) applies clean to pristine 4b958379d6. F2 DOCUMENTED HERE — naive ISO one-shots anchor to the HOST local zone (datetime.now().astimezone().tzinfo) where the native parser anchors to the configured Hermes zone (_hermes_now().tzinfo); identical on UTC hosts, latent wherever host zone != configured zone; also inline-commented in the patch — if zones can diverge in deployment, re-anchor to the configured zone at the gate or next cycle. F3 DEFERRED (next cycle, per reviewer scope): guard PRIVATE_RUNTIME_MODULES bans only 'cron'; enumerate the other non-colliding private-runtime top-levels (/home/agent/.hermes/hermes-agent) into the set — deferred because it edits the guard test, reserved for next cycle. F4 (info): the implement-phase patched-tip log was deleted in cleanup; this review-fix reran the patched-tip full serial suite fresh (/tmp/rv032-fix-full.log) — gate-side CI remains the authoritative closure.

### Land fork PR #19 (packaging consolidation + pyyaml CVE floor) and revive upstream PR #75
- id: `rm-033` | track: reliability | priority: 105.0 | status: implemented-pending-commit-gate (rm-033a slice ONLY: pyproject.toml:20 `pyyaml>=6.0.3,<7` + CHANGELOG CVE-2026-31132 entry, at run base awaiting commit; requirements*.txt deletion + PR #19 landing + upstream PR #75 rebase remain open at the gate)
- signals: conductor.run-6efbf603:research-C1, upstream PR #75 (head = codeo1io branch conductor/run-634bf4516c83 == fork PR #19): delete requirements.txt/requirements-dev.txt (strict-subset duplicates; our requirements.txt:5 bare pyyaml drifts), bound pyyaml>=6.0.3,<7 citing CVE-2026-31132 (fixed 6.0.3; pyproject.toml:20 `>=6,<7` admits vulnerable 6.0.2); upstream mergeable_state=blocked, ZERO CI runs on head 3a38d980; also resolves the assess finding on requirements.txt drift (docs/mcp-compatibility.md:97 cites it as equivalent)
- acceptance: pyproject pyyaml floor raised to >=6.0.3 (CVE note in CHANGELOG); requirements*.txt deleted with docs repointed to pyproject; PR #19 landed on repaired green master; upstream PR #75 rebased onto the landed state with >=1 green upstream run (verify via actions/runs?head_sha=, never by PR number)
- evidence: pyproject diff; green CI on the merge; upstream run URL filtered by head_sha; CHANGELOG CVE entry

### Document the convergence-shipped OAuth surface and repair the CHANGELOG
- id: `rm-034` | track: reliability | priority: 52.0 | status: candidate
- signals: conductor.run-6efbf603:assess-F4, origin/master ships HERMES_GPT_OAUTH_DCR (default-on, gates only metadata advertising — /oauth/register answers regardless, oauth_auth.py:49), HERMES_GPT_OAUTH_PKCE_MODE, and /oauth/register (bounded: chatgpt.com/openai.com HTTPS-only redirects, capacity-capped, public client, PKCE still enforced for dynamic clients :676/:1282) with ZERO coverage in docs/oauth.md (master); CHANGELOG.md:12 run-on merging 0.11.0 blocks; no CHANGELOG entry for the convergence merge; upstream has none of these knobs so no catch-up will ever document them
- acceptance: docs/oauth.md documents all three knobs (name, default, gates, security posture incl. knob-vs-endpoint semantics); CHANGELOG gains a convergence entry and the :12 run-on is fixed; AGENTS.md docs rules (defaults/gates explicit) satisfied
- evidence: grep hits in docs/oauth.md for each knob; rendered CHANGELOG review; docs diff

### Commit a [tool.ruff] rule-set config on ruff 0.16 (extends run-fd2bc85f rm-028)
- id: `rm-035` | track: maintainability | priority: 50.0 | status: candidate
- signals: conductor.run-6efbf603:research-C3, ruff 0.16.8 current on PyPI (2026-09-22) while the dev pin is `>=0.15,<0.16` (pyproject.toml:27) and NO [tool.ruff] config is committed — the enforced rule set is whatever the installed default happens to be; run-fd2bc85f rm-028 measured 524 findings under 0.15 defaults vs 61 under the classic set
- acceptance: a committed [tool.ruff] selects the enforced rule set explicitly; dev pin moves to a 0.16.x line; CI lint job green under the pinned ruff; a finding-count table (classic vs adopted set) with per-class disposition lands in the PR
- evidence: pyproject diff (config + pin); green CI lint run; the disposition table

### Conformance-check skill resolution against the PUBLISHED MCP Skills extension (extends run-684b9786 rm-028 / PR #20)
- id: `rm-036` | track: compatibility | priority: 48.0 | status: candidate
- signals: conductor.run-6efbf603:research-C5, MCP spec moved the Skills extension to published status 2026-09-18 (specification repo commits ddbee69a/406273f8 + PR #3372) while revision 2026-07-28 remains the latest base — skill discovery semantics (server.py skill_roots/discover_skills, operator_skills.py _find_skill_dir) are now normative; fork PR #20 (run edd9fb12b6a4) implements profile-aware resolution per upstream issue #74 (still open, updated 2026-09-21T18:36Z)
- acceptance: conformance note mapping hermes skill surfaces onto the published extension (naming, discovery roots, precedence); PR #20's tests verified against it; upstream #74 outcome recorded when it lands (contract agreed architecture-first per run-684b9786 rm-028)
- evidence: spec-commit citations; conformance-note path; green skill-resolution tests post-PR-#20

### Single peer_main: dedupe the dead entry point and test the packaged peer CLI
- id: `rm-037` | track: maintainability | priority: 40.0 | status: candidate
- signals: conductor.run-6efbf603:assess-F5, operator_fabric.py:2953 defines peer_main (prog hermes-gpt-fabric-peer) that nothing reaches — the packaged console script targets operator_fabric_g4c:peer_main (pyproject.toml:35; operator_fabric_g4c.py:2044); zero test references to peer_main anywhere; docs/operator-mode.md:282 calls the g4c one "the packaged remote endpoint"
- acceptance: one canonical peer_main (dead one removed or repointed with a rationale comment); the packaged entry (g4c peer_main / its serve stack, port 4780) covered by at least one test exercising require-secure-transport and the CLI surface
- evidence: grep shows a single peer_main definition; new tests green; pyproject entry point unchanged

### Branch protection on codeo1io master (extends rm-008 with red-master evidence)
- id: `rm-038` | track: reliability | priority: 55.0 | status: candidate
- signals: conductor.run-6efbf603:assess-F2, 2026-09-22 03:07–03:39Z: the 25-file deployed-line convergence (+1414/−116) landed via DIRECT PUSH with no PR gate, broke all 9 CI lanes (cron.jobs import), and 3 further fix commits were pushed onto already-red master; rm-008's `gh api branches/master/protection` -> 404 still current
- acceptance: master branch protection requires the CI test+lint jobs with linear history; direct pushes restricted to admins; a red push/PR is observed to be rejected once
- evidence: gh api branches/master/protection returns required_status_checks; one observed rejection

### CI web-lane npm caching + stale self-hosted comments
- id: `rm-039` | track: reliability | priority: 20.0 | status: candidate
- signals: conductor.run-6efbf603:assess-F8, .github/workflows/ci.yml:142 omits npm caching justified by a self-hosted-runner rationale that PR #21's move to GitHub-hosted runners made obsolete (stale comment also at :33) — cold npm ci on ephemeral runners every web job
- acceptance: actions/setup-node cache enabled for the web job (or a recorded reason not to); stale comments refreshed to match hosted runners
- evidence: ci.yml diff; green web job showing a cache hit

### Reconcile divergent vercel.json configs
- id: `rm-040` | track: maintainability | priority: 15.0 | status: candidate
- signals: conductor.run-6efbf603:assess-F9, root vercel.json vs site/vercel.json encode different deployment shapes (static-build routes vs outputDirectory '.'); nothing records which is authoritative
- acceptance: one authoritative config kept (the other deleted or its role documented in the docs/README.md authority map); deploy shape verified once
- evidence: diff + authority-map entry; one observed deploy

## Cycle 3 next-cycle context (run 6efbf603)

- **rm-032 (re-green master) gates everything**: PR #19/#20 landing, upstream PR #75 revival, and any new stacking all assume a green master — repair BEFORE landing batches.
- The 5 red master runs (03:07–03:39Z) invalidated the "last green push" invariant trackers relied on — re-derive baselines from 5765b571b2 until master re-greens.
- rm-026..rm-029 are duplicated across the two cycle-2 blocks (runs 684b97865efc vs fd2bc85ff599); reconcile at the merge gate; cycle-3 ids are unique from rm-032.
- **Cycle-1 outcome (pre-review, 2026-09-22, implement 07e9164d + targeted_tests 210c9fa1)**: batch B1 executed end to end at the run base — U1 guard test (test_no_private_runtime_imports.py, green, collected in the full suite), U3 pyyaml CVE floor + CHANGELOG entry, U2 master-side repair staged as .conductor/patches/rm-032-cron-repair.patch (+201/−5 on operator_cron.py only, applies clean to pristine 4b958379d6; cron test family green with cron blocked and importable; patched-tip full serial suite 0 F/E). Full serial suite at the base tree: zero FAILED/ERROR, .pytest_cache/v/cache/lastfailed == {}. NOTHING committed/pushed (delegate policy) — the commit gate must land the patch on the master tip to actually re-green origin/master, then U1/U3 ride the run branch; PR #19 landing and upstream PR #75 rebasing stay gate-side companions. Review outcome is NOT folded here (post-compound by policy).

## Cycle 3 learnings — prevention rules (run 6efbf603, 2026-09-22)

1. **Never import private-runtime modules from repository code** — `cron` exists only in /home/agent/.hermes/hermes-agent on deployed boxes, so the author's environment masks the break while every clean install (all CI lanes) fails. test_no_private_runtime_imports.py now enforces this deterministically: rule 1 bans `cron` imports anywhere (guarded or not); rule 2 requires module-level unguarded imports in shipped py-modules to resolve against repo/stdlib/declared-dependency closure. Keep it in the suite forever.
2. **Ports must be self-contained and check the dependency closure** — the private parser hard-requires croniter, which is NOT a declared dependency of this package; the repo-local port keeps croniter optional (structural field check when absent) so clean installs work either way. Before porting runtime code, enumerate its imports against pyproject dependencies.
3. **Landed tests are the contract, not the plan text** — the roadmap/research wording (persist RAW schedule strings, per upstream) conflicted with master's own merged tests asserting the STRUCTURED dict; a raw-string revert would have re-broken master's suite. Always read the failing tests' assertions at the TARGET tree before authoring a repair; when plan and tests conflict, tests win (AGENTS.md source-of-truth precedence).
4. **py-modules live under `[tool.setuptools].py-modules`, not `[project].py-modules`** — tooling that reads pyproject to derive the shipped surface must use the right key (the guard test tripped on this); also setuptools auto-includes more than the py-modules list, so declared→wheel assertions do not catch script-target-only gaps.
5. **Direct pushes without branch protection shipped red** — the 25-file convergence landed by direct push breaking all 9 lanes, then 3 more commits were pushed onto already-red master. Until rm-038's protection lands, ALWAYS check `gh api repos/codeo1io/hermes-gpt/actions/runs?branch=master&per_page=1` before stacking work on master.
6. **Both-direction detached-worktree proofs are cheap and definitive** — reproducing the defect with the module blocked (clean-install reality) and unblocked (author's reality) took minutes and removed all doubt about provenance; prefer this over inference when a defect depends on the environment.

<!-- managed by hermes-roadmap render; do not edit by hand -->
