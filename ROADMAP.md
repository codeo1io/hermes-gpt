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

<!-- managed by hermes-roadmap render; do not edit by hand -->
