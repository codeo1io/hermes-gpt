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
- id: `rm-026` | track: reliability | priority: 72.0 | status: candidate
- signals: conductor.run-634bf451:assess, `git ls-files -s | grep -c '^160000'` == 12 (design-canon-* x8, review-bench, review-compat, review-fixtures, review-qa) with NO .gitmodules and all 12 dirs empty on disk; commit c1785b22e5's message claims it dropped the design-canon-adr002 gitlink but its diff only deleted .gitmodules — the gitlink remains in the index (commit-message/diff mismatch)
- acceptance: all 12 gitlinks removed from the index (git rm --cached) OR a .gitmodules restored with resolvable URLs if any are intentionally real; `git ls-files -s | grep -c '^160000'` == 0; a fresh `git clone --recurse-submodules` does not fail; commit message truthfully states what was removed (supersedes the c1785b22e5 claim)
- evidence: command outputs pre/post; CI unaffected (actions/checkout submodules:false) — green run confirms

### Ship-or-de-reference README-referenced docs; add a shipped-docs guard test
- id: `rm-027` | track: maintainability | priority: 60.0 | status: candidate
- signals: conductor.run-634bf451:assess, docs/runtime-checkout.md and docs/vnext-capability-manifest-and-mission-ledger.md exist in docs/ and are referenced by README.md:36, README.md:343, docs/README.md:28 (the documentation authority map) but are absent from [tool.setuptools.data-files] — installed users get a docs map pointing at files that do not ship; no test guards the shipped-docs list (test_export_docs.py pins only file-export.md; test_package_hygiene.py pins release notes); docs/runtime-checkout.md:18 additionally pins host state ('mcp[cli]>=1.0,<2' vs pyproject's >=1.28.1,<3; /home/tony paths; port 4750)
- acceptance: both docs either added to data-files or de-referenced from README/docs map; NEW guard test asserts every docs/*.md link target in README.md and docs/README.md is in data-files (explicit allowlist for intentionally-unshipped historical docs); runtime-checkout.md refresh or re-label as historical per AGENTS.md documentation rules
- evidence: guard test added and green; `python -m build` + tools/check_package_hygiene.py show the shipped docs set

### Stop .gitignore '*.ps1' from swallowing new example scripts
- id: `rm-028` | track: reliability | priority: 55.0 | status: candidate
- signals: conductor.run-634bf451:assess, .gitignore '*.ps1' rule matches examples/*.example.ps1 (verified: `git check-ignore examples/foo.example.ps1` matches) — the exact pattern pyproject data-files ships; existing examples are tracked only because they predate the rule, so any NEW example .ps1 is invisible to `git add .` yet claimed by data-files
- acceptance: negation rule added (e.g. `!examples/*.ps1`); `git check-ignore examples/foo.example.ps1` exits 1 post-fix; tracked example set unchanged (`git ls-files examples/` identical); packaging still ships them
- evidence: check-ignore probe before/after; ls-files diff empty; data-files listing in the built wheel/sdist

### pyyaml bound (last bare runtime dependency)
- id: `rm-032` | track: reliability | priority: 58.0 | status: candidate (promoted from 6d49 next-cycle context)
- signals: conductor.run-634bf451:research, pyproject dependencies list pyyaml unbounded; PyPI 6.0.3 (2026-08-25) fixed CVE-2026-31132; rm-023 left pyyaml as the only bare runtime dep (uvicorn already >=0.30,<1)
- acceptance: pyyaml bounded `>=6.0.3,<7` in pyproject (and requirements.txt if rm-029 keeps that file); CHANGELOG note; a cap move is a deliberate changelog event
- evidence: pyproject diff; full suite green; CHANGELOG entry

### requirements.txt / pyproject dependency duplication + undeclared psutil
- id: `rm-029` | track: maintainability | priority: 45.0 | status: candidate
- signals: conductor.run-634bf451:assess+research, requirements.txt duplicates the pyproject [project] dependency list (drift risk: it already differs — adds psutil at runtime, which pyproject does not declare) while dev extras live only in pyproject; two sources of truth for the install set
- acceptance: single source of truth — requirements.txt removed (docs point at `pip install .[dev]`) or generated/sync-checked against pyproject by a CI guard; psutil either added to pyproject (if genuinely runtime) or moved to the dev extra after an import-usage audit
- evidence: sync guard green or removal diff; `pip install` equivalence shown; full suite green

### Gemini CLI client profile (user-need evidenced by upstream #54)
- id: `rm-033` | track: compatibility | priority: 35.0 | status: candidate (gated on rm-030)
- signals: conductor.run-634bf451:research, upstream issue #54 (open, 2026-09-12) requests Gemini CLI support; the only open user-need signal on either tracker (fork has no open issues; upstream has no other open issues); rm-030's Gemini Spark profile provides the custom-app OAuth scaffolding to mirror
- acceptance: opt-in Gemini CLI client profile analogous to Gemini Spark (profile-aware session history + verified setup guide), default surfaces unchanged (read-only/dry-run ladder intact), test file mirroring test_gemini_compat.py; docs/codex.md terminology rules respected (client profile vs delegated worker)
- evidence: tests green in-suite; setup guide verified against a real custom app; upstream #54 referenced in the CHANGELOG/PR

Status amendments from this run's evidence (history above preserved): rm-024 gains anyio-5.0.0 evidence (released 2026-09-21; the -n 8 uv-env log already shows anyio BlockingPortal deprecation warnings — 3.13/3.14 lanes will surface more); rm-023's pyyaml follow-on is now formalized as rm-032; rm-018's revisit precondition (sibling rm-003 merge) is unchanged and still unmet at this HEAD.
## Cycle-1 sibling ledger reconciliation — run bdf4157b (2026-09-21)

Provenance: this section was recorded in roadmap attempt c4ead699's phase_result (turn cut off pre-write) and is materialized here by prioritize attempt 4a9d9f1d as a verified prerequisite (fd2bc85ff599 prioritize 87402e78 set the precedent). Base of this file = run-634bf4516c83's ROADMAP.md (rm-001..rm-033, adopted verbatim; additions-only vs seed origin/conductor/run-6d49d1e3979f).

Collision record: FOUR concurrent cycle-1 siblings minted colliding rm-026+ namespaces from the same committed seed (rm-001..rm-025):
- run-634bf451 rm-026..rm-033 — adopted verbatim above (its prioritize batch B1 'Index & Packaging Truthfulness' consumes these ids; implement in flight).
- run-684b9786 rm-026..rm-031 — its rm-026 (v0.11.0 catch-up) == rm-030; its rm-027 (pyyaml) == rm-032; its four UNIQUE items re-aliased below (rm-034..rm-037). Its B1 (updater/SHA-pin/pyyaml/dompurify) maps here to rm-034+rm-035+rm-032+rm-036.
- run-fd2bc85ff599 rm-026..rm-029 (roadmap folded from a repair turn; content = PKCE re-bind / mcp_compat skip guard / token_store dead block / build floor) — content-covered by implemented seed items rm-003/rm-007/rm-016 plus build floor = rm-044 here; no ids preserved.
- run-bdf4157b (this run): new ids rm-034..rm-045 below.

### Adopted aliases (run-684b97865efc re-namespace)
- id: `rm-034` | track: reliability | priority: 60.0 | status: candidate
  - alias: = run-684b9786 rm-029
  - signals: conductor.run-684b9786:assess + run-bdf4157b:assess (live repro), updater.py:49-58 `_find_git_root` walks to first enclosing repo with no hermes-gpt sentinel; updater.py:203-206 updates whatever it found; docs/updating.md:19-26 promises updates apply to the hermes-gpt installation — a venv nested in a foreign repo (standard hermes layout) makes `update --apply` fast-forward the WRONG repository. Reproduced read-only at /tmp/assess-255a-unrelated/proj (check_for_update returned git-mode policy for an unrelated repo).
  - acceptance: ownership sentinel (hermes-gpt marker file/pyproject name match) required before git-mode update; foreign-repo case exits with explicit error naming both paths; tests cover foreign-parent, own-repo, non-repo; docs/updating.md updated
  - evidence: new tests green; repro scenario returns error not NOT_ON_DEFAULT_BRANCH
- id: `rm-035` | track: reliability | priority: 48.0 | status: candidate
  - alias: = run-684b9786 rm-030
  - signals: conductor.run-684b9786:assess, .github/workflows/ci.yml:22 references codeo1io/.github/.github/workflows/private-leak-sentinel.yaml@main; codeo1io/.github is PUBLIC with no branch protection (gh api 2026-09-21: private:false) — a mutable pin silently changes what every CI run scans
  - acceptance: SHA-pinned reference (full commit SHA); upgrade path documented; sentinel workflow unchanged in behavior
  - evidence: ci.yml diff shows @<sha>; CI lint passes
- id: `rm-036` | track: maintainability | priority: 12.0 | status: candidate
  - alias: = run-684b9786 rm-031
  - signals: web/package.json:15,28 declare dompurify + @types/dompurify; no web/src file imports them; chat renders via ReactMarkdown without rehype-raw (web/src/chat/Message.tsx:15)
  - acceptance: dompurify removed from deps (or rehype-raw adopted deliberately with sanitization tests — pick one story); web build + tests green
  - evidence: package.json diff; npm build green
- id: `rm-037` | track: correctness | priority: 38.0 | status: candidate (gated on rm-030)
  - alias: = run-684b9786 rm-028
  - signals: upstream issue #74 (only open upstream issue, 2026-09-21): 'skill exists' != 'the target profile can resolve it at execution time'; cites server.py::skill_roots/discover_skills, operator_skills.py::_find_skill_dir, operator_capability_manifest.py, operator_placement.py; depends on rm-030 (v0.11.0 reshaped capability-manifest surfaces)
  - acceptance: canonical profile-aware resolution order implemented + tested before placement/dispatch; upstream #74 referenced in PR
  - evidence: resolution tests across profiles green

### New items (run-bdf4157b assess 255a600f / research 506459c2)
- id: `rm-038` | track: reliability | priority: 66.0 | status: implemented-pending-review (run-bdf4157b B1, 2026-09-22)
  - signals: conductor.run-bdf4157b:assess, operator_cron.py:129 `_write_jobs` writes via FIXED path /tmp/hermes-cron-jobs.json (cross-process/user collision, predictable tmp path); threading imported at :33 but NO lock anywhere; `_read_jobs` (:99 area) on corrupt JSON returns [] and the next write DURABLY WIPES all cron jobs. rm-021 (pending commit gate, PR #13 head) adds backup-on-corrupt but neither restores nor refuses the wipe, and does not fix the tmp path or add locking.
  - acceptance: (1) unique temp file (tempfile in same dir, os.replace); (2) advisory flock (or lock file) around read-modify-write shared with the cron engine process; (3) corrupt live file NEVER silently becomes empty-write: restore from rm-021's .corrupt-<ts> sidecar when present, else refuse-and-error with operator-visible signal (verify no test asserts wipe semantics first — rm-018 lesson); base-independent: tolerates rm-021 sidecar absence at this HEAD
  - evidence: new tests: concurrent-writer race, corrupt-read-then-write preserves/restores, unique tmp under /tmp collision; whole file + full suite green serially
  - implemented: operator_cron.py in run-bdf4157b B1 (attempt 5f6ceb77, uncommitted, 10 files +328/-47): `_read_jobs_state` returns (jobs, corrupt) and preserves corrupt bytes as `.corrupt-<stamp>` sidecar via rm-021's `_backup_corrupt_jobs` adopted VERBATIM from 89865b1281 (merge-compatible); `_refuse_if_corrupt` gate in all three mutating tools (create/copy/move) — corrupt file never silently becomes an empty write; `_write_jobs`: unique per-writer tmp `<name>.<pid>.<tid>.tmp`, fsync file+dir, in-process `_JOBS_WRITE_LOCK` (threading import now used); OSError-present-but-unreadable also backs up+refuses. 5 new tests (incl. 8-thread concurrent-writer race → exactly one valid payload, no stale tmp); test_operator_cron.py 36/36; full suite ×2 zero new failures
- id: `rm-039` | track: correctness | priority: 45.0 | status: candidate (needs design decision)
  - signals: conductor.run-bdf4157b:assess, oauth_auth.py:875 PUBLIC_PATHS has no /api exemption — auth-configured deployments 401 ALL /api calls including /api/me; web/src/api/client.ts:25 sends no Authorization header anywhere; AccountStatusBanner.tsx:94 reauthHref defaults '#': the four-state account-degradation UX is unreachable dead code in every deployment mode
  - acceptance: decision recorded (exempt read-only /api/health|version|me vs session cookie vs SPA bearer) THEN implemented + tested; banner states reachable or removed; docs updated to match chosen story
  - evidence: tests exercising each auth mode against the chosen exemption/session path; docs reflect behavior
- id: `rm-040` | track: maintainability | priority: 26.0 | status: implemented-pending-review (run-bdf4157b B1, 2026-09-22)
  - signals: conductor.run-bdf4157b:assess, .github/workflows/ci.yml:119 py_compile step uses a hand-maintained list missing 30/59 shipped modules (module-vs-list diff, 2026-09-21); rm-017 (pending PR #13 head) fixed ONLY the ruff lint job to repo-wide
  - acceptance: py_compile derived from py-modules (or the step dropped in favor of ruff+test coverage); guard test asserting every shipped module is compiled-or-linted; no hand list
  - evidence: ci.yml diff; guard test green
  - implemented: ci.yml py_compile step now derives the module list from pyproject `[tool.setuptools] py-modules` (tomllib + py_compile heredoc) — covers all 57 shipped modules vs 29 in the old hand list (assess's 30/59 count used a wider 59-module basis; the derivation makes either count moot); the step script asserts the derived list is non-empty and canaries the shipped count at a literal 57, so a broken derivation or silent count drift fails loudly; py3.10 matrix lanes import the declared tomli backport (`tomli; python_version < '3.11'`) — review round 1 fix, verified green on both 3.11 venv and /usr/bin/python3.10; verified 57/57 compile locally (run-bdf4157b B1 attempt 5f6ceb77, uncommitted)
- id: `rm-041` | track: correctness | priority: 30.0 | status: implemented-pending-review (run-bdf4157b B1, 2026-09-22)
  - signals: conductor.run-bdf4157b:assess, operator_runners.py:1026 and operator_fabric.py:1266 pass raw header strings to hmac.compare_digest — non-ASCII bytes raise TypeError -> 500 instead of 401/403; upstream v0.11.0's oauth B4 fixed its own site, these fork sites remain at this HEAD
  - acceptance: pre-encode to bytes (or validate ASCII) at all three surfaces (incl. any site fixed by rm-030 catch-up — check post-merge); tests with non-ASCII credentials assert 401/403 not 500
  - evidence: tests green incl. non-ASCII regression tests (review round 1); rg sweep re-run: every credential-bearing compare_digest site now compares bytes; the remaining str-form sites (oauth_auth.py:307/:391/:479) hold base64url-decoded bytes or regex-validated ASCII digests, so no raw attacker-controlled str reaches compare_digest
  - implemented: both fork sites fixed in run-bdf4157b B1 (attempt 5f6ceb77, uncommitted): operator_runners.py `_OpenCodeCredentialProxy._forward` and operator_fabric.py `FabricPeerManager.authenticate` encode both sides `utf-8`/`surrogateescape` before `hmac.compare_digest` → clean 401 / FABRIC_PRINCIPAL_AUTH_FAILED instead of TypeError 500; 2 new tests (fabric FabricError path; runners live-relay bytes-header → 401, upstream not hit); the third credential surface (oauth_auth.py `validate_bearer_token`) was NOT covered by upstream B4 — caught as the review-round-1 residual and fixed in-tree (utf-8 encode both sides before compare_digest → non-ASCII bearer is a clean 401, not TypeError 500) with function-level regression tests
- id: `rm-042` | track: reliability | priority: 20.0 | status: candidate (migration design required)
  - signals: conductor.run-bdf4157b:assess, token_store.py:75 env master key derives via single unsalted SHA-256 — offline brute-forceable if envelope leaks; PBKDF2/scrypt with salt+iteration count is a trivial upgrade
  - acceptance: versioned key-derivation (new envelopes PBKDF2/scrypt; legacy SHA-256 read path kept until rotation) or documented decision why env keys need no KDF hardening; migration tests for legacy envelope read
  - evidence: crypto round-trip tests incl. legacy-read; docs note
- id: `rm-043` | track: maintainability | priority: 16.0 | status: candidate
  - signals: conductor.run-bdf4157b:assess, ui_security.py:229 hardcoded _MODEL_PHRASE_RE model shield is a 2024-era list; Titlecase pairs outside the list mangle to [redacted-name] (standing drift trap as models ship)
  - acceptance: shield list externalized (data file keyed by version) or validated allowlist with update path; tests prove unmangled unknown-model pairs
  - evidence: tests with post-list model names green
- id: `rm-044` | track: maintainability | priority: 22.0 | status: candidate (in fd2bc85 B1 as build-floor bump)
  - alias: = run-fd2bc85ff599 rm-029 (content)
  - signals: fd2bc85ff599:assess, pyproject.toml:12 license = "MIT" (PEP 639 string) requires setuptools>=77 (declared floor :2 setuptools>=69 fails to build metadata)
  - acceptance: build floor raised to a setuptools that emits PEP 639 metadata (>=77) or license table form; python -m build green at declared floor
  - evidence: build logs green at floor version
- id: `rm-045` | track: reliability | priority: 24.0 | status: implemented-pending-review (run-bdf4157b B1, 2026-09-22)
  - signals: conductor.run-bdf4157b:research, OSV query 2026-09-22: cryptography 50.0.1 (latest) zero vulns; declared floor cryptography>=42 (pyproject:19, requirements:4) admits GHSA-affected ranges (incl. GCM forgery GHSA class) — bound pending on PR #13 head narrows ceiling but floor stays 42
  - acceptance: floor raised to a clean version (>=46 recommended post-OSV review; exact floor from OSV ranges at implementation time); CHANGELOG note
  - evidence: pip resolve at new floor; OSV query output cited in PR
  - implemented: floor raised to `cryptography>=50` in pyproject.toml:19 AND requirements.txt:4 (run-bdf4157b B1 attempt 5f6ceb77, uncommitted) with live OSV bisection: every release line through 49.0.x carries ≥1 advisory (GHSA-g6cj-pr64-35w5 + PYSEC-2026-3552 tail; GHSA-537c-gmf6-5ccf through 48.x); 50.0.0/50.0.1 are the first zero-advisory releases AND the baseline venv already runs 50.0.1 (suite-proven compatible); CHANGELOG Unreleased entry added. Acceptance's '>=46 recommended' superseded by the bisection — 46/48 are not clean

- id: `rm-046` | track: reliability | priority: 18.0 | status: candidate (minted at compound 725ce029, 2026-09-22; cross-checked unclaimed across all sibling ledgers/worktrees)
  - signals: run-bdf4157b implement 5f6ceb77 finding, operator_swarm.py:565 `_save_workflow` writes via FIXED `path.with_suffix('.json.tmp')` with no fsync — the same shared-tmp pattern rm-038 just fixed in operator_cron.py; lower risk (per-workflow-id filenames under the workflows dir, single-writer context in practice) but two concurrent workflow writes to the same id can truncate each other and a crash can leave an empty record
  - acceptance: mirror rm-038's write pattern (unique per-writer tmp + fsync file/dir) or a shared helper extracted from operator_cron._write_jobs; keep the change surgical — no locking redesign in this unit
  - evidence: new concurrent-save test; test_operator_swarm.py green serially

### Evidence updates (no new id)
- rm-010: third member of the real-thread load-timing flake class confirmed — test_operator_delegations.py:654 test_reconcile_cas_preserves_concurrently_confirmed_cancellation fails under full-suite serial load, passes solo (run-bdf4157b assess 255a600f, 2026-09-21); strengthens rm-010's de-flake/xdist triage.
- rm-030: run-bdf4157b research independently PROVED upstream/master passes test_codex_pr63_remediation.py 44/44 on the baseline interpreter (export /tmp/assess-5064-upstream, HERMES_HTTP_TEST=1 serial, 2026-09-21) — v0.11.0 catch-up directly repairs rm-003's failing quartet; prefer upstream remediation over local test edits, matching rm-030's decision-note acceptance.
- rm-031 (spec lineage): run-bdf4157b research found spec-repo activity through 2026-08-23 and no revision newer than 2026-07-28 — CONFLICTS with rm-031's 2025-06-18 claim; resolve by querying modelcontextprotocol/specification directly at implementation time before editing docs/mcp-compatibility.md.
- rm-023: OSV corroboration (2026-09-22) — pyyaml CVE-2026-31132 motivates rm-032's >=6.0.3 floor; cryptography evidence moved to rm-045.

### Prevention rule 11
- Concurrent sibling cycles minting rm-ids from the same seed must cross-check uncommitted sibling ledgers AND repair-turn-folded roadmap records before allocating ids (four siblings minted colliding rm-026+ namespaces within one hour on 2026-09-21; reconciliation cost exceeded minting cost).

## Cycle 1 outcome — run bdf4157b (2026-09-22; compound, pre-review)

Batch B1 'Silent-Failure Hardening' implemented in worktree run-bdf4157b566b-bdf4157b (attempt 5f6ceb77, 10 files +328/-47, UNCOMMITTED — review/commit are later gates): rm-038 (cron jobs.json durability: corrupt→sidecar+refuse-to-overwrite, unique-tmp+fsync(file+dir)+in-process-lock writes — threading.Lock, no flock, cross-process last-writer-wins unchanged), rm-041 (ASCII-safe compare_digest → 401/AUTH_FAILED not TypeError 500), rm-040 (CI py_compile derived from py-modules, 57/57 vs hand-list 29), rm-045 (cryptography floor 42→50, OSV-bisected). Validation (attempt 65967a95): targeted 3 files 106/106 exit 0; full serial suite ×2 (implement + targeted_tests) reached 100% with a BYTE-IDENTICAL failure set = exactly the documented pre-existing allowlist (4× test_codex_pr63_remediation stale-PKCE — owned by fd2bc85's repair / rm-030 catch-up — plus env-dependent test_mcp_compat metadata test); zero new failures; test_operator_delegations:654 flake did NOT fire in either run (still a real load-timing class member per assess solo-rerun evidence).

### Cycle-2 learnings — prevention rules (run bdf4157b)

12. **Complete shipped partial work by adopting it verbatim.** rm-038 extends shipped rm-021; adopting `_backup_corrupt_jobs` byte-for-byte from commit 89865b1281 makes the completion merge-clean instead of a three-way conflict on the same function.
13. **Derive dependency floors from advisory data, not intuition.** OSV bisection (osv.dev per candidate floor) showed the previously 'recommended' >=46 is still advisory-laden; the correct floor is the first zero-advisory release ALREADY installed in the baseline venv (50.0.1) — compatibility and security evidence in one fact.
14. **Unset `HERMES_GPT_OPERATOR_ALLOWED_PROFILES` is deny-by-default — even for read-only tools.** Cron tests calling hermes_cron_list must set OPERATOR_ENABLED=1 + ALLOWED_PROFILES explicitly (first test run failed on 'Profile not in allowed profiles list').
15. **A zero-new-failures claim needs a REPRODUCIBLE allowlist.** Full suite run twice at the same tree; only a byte-identical failure set earns the 'pre-existing, not a regression' classification.
16. **http.client passes bytes header values through untouched** — the harness trick for testing non-ASCII Authorization paths without urllib quoting them.
17. **Work-order `uv run … -n 8` is always substituted** with the authoritative CI shape (baseline venv, serial, HERMES_HTTP_TEST=1) per fleet rule; record the substitution in the validation command string, not just the summary.
18. **Same-pattern follow-ups found during implement get their own roadmap id at compound time, not a scope creep edit.** operator_swarm.py:565 was spotted mid-B1 and deliberately left untouched (batch surface minimal) → rm-046.

### Next-cycle context (concrete, in suggested order)

1. **rm-030 upstream v0.11.0 catch-up is the validated headline**: only 5 commits / 19 files / +1516 lines from merge-base 9f537106e9, and upstream/master passes test_codex_pr63_remediation.py 44/44 on the baseline interpreter (export /tmp/assess-5064-upstream) — it repairs the 4 failing PKCE tests directly; local PKCE test edits are superseded. rm-037 (skill gate, upstream #74) stays gated on it. Post-merge, expect the allowlist to shrink from 5 to 1 (only test_mcp_compat env case remains).
2. **Review B1 before commit** with focus points from implement: `_refuse_if_corrupt` double-read in copy/move; dir-fsync best-effort OSError swallow; surrogateescape encoding choice; ci.yml heredoc quoting under `run: >-`.
3. **rm-046** (swarm _save_workflow durability, minted above) pairs naturally with any B2 reliability batch.
4. **Design-gated items need their decision phases**: rm-039 (web-UI auth dead-end — pick read-only /api exemption vs session cookie vs SPA bearer), rm-042 (token_store PBKDF2 — migration story required).
5. **Fleet ROADMAP merge at the commit gate**: four sibling ROADMAP variants exist (rm-001..rm-045 reconciled here); this file is the maximal additions-only reconciliation and the natural merge base — reconcile rather than re-render (the footer's 'do not edit by hand' was superseded by the reconciliation, per fleet rule #6611).
6. **requirements.txt:4 cryptography hunk is conditional**: sibling 634bf451's rm-029 deletes requirements.txt; if that lands first, drop our line-level hunk there (pyproject remains authoritative).

<!-- managed by hermes-roadmap render; do not edit by hand -->
