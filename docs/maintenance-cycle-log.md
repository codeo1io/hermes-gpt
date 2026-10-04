# Maintenance cycle log

> Historical provenance for repository-maintenance cycles. This log records what each
> cycle changed, the prevention rules it established, and the context it left for the
> next cycle. It is not runtime documentation: for current behavior read the code, the
> tests, and the [current operational docs](README.md). Roadmap state lives in the
> root [`../ROADMAP.md`](../ROADMAP.md) (fleet-sync artifact rendered by hermes-roadmap).

## Cycle 1 — 2026-09-21 — "Restore verifiable truth + safety-evidence integrity"

Run `a51b0f6cb5b04ea9855a3dc3aba88c78` against worktree at `54f826c0cd`
(`origin/master` `f8ba2e7862` is a docs-only merge ahead). Cycle phases: assess →
research → roadmap → prioritize → stewardship → implement → targeted tests → compound.
All outcomes below are pre-review: the batch was implemented and locally verified but
not yet reviewed, merged, or CI-verified.

### What the cycle did

- **rm-003 (P120)** — bound the five stale OAuth tests in
  `test_codex_pr63_remediation.py` to a real S256 challenge/verifier pair
  (`oauth_auth._s256`) so each exercises its stated contract instead of dying at the
  PKCE gate, and added `test_exchange_rejects_code_without_stored_challenge` to pin the
  fail-closed contract positively. Runtime `oauth_auth.py` was not weakened.
- **rm-007** — `test_mcp_compat.py:81` now skips with a reason when the distribution
  is not installed instead of erroring.
- **rm-009** — `.github/workflows/ci.yml` gained explicit `mcp==2.2.0` and
  `mcp==1.30.0` lanes, and `test_mcp_sdk_migration.py` gained
  `test_sdk_protocol_revision_is_deliberate` (fails loudly if the installed SDK
  advertises a protocol revision other than the one the tests pin).
- **rm-004** — `operator_policy.py` audit log: dynamic per-call path resolution
  (`HERMES_HOME/logs` → Windows `AppData\Local\hermes` → POSIX `~/.hermes` → package
  dir last resort), counted-and-surfaced write failures
  (`audit_write_diagnostics()` + doctor `WARN AUDIT_WRITE_FAILURES`), 5 MiB
  single-generation rotation, 512 KiB byte-bounded tail, task reconciliation that
  spans the rotation archive. Documented in `operator-mode.md` → Audit behavior.

Verification at end of implement: full suite **1438 passed / 6 skipped / 0 failed**
(system Python 3.11) and **1442 passed / 2 skipped** (fresh uv env, CPython 3.13,
distribution installed — the metadata test runs instead of skipping there).

### Prevention rules established

1. **Hardening changes ship their own positive fail-closed test.** PR #64's tests
   predated the PKCE-mandatory hardening in content but merged after it; nothing
   failed inside the PR's own context because the contradiction only appears against
   current master. From now on: an enforcement change (e.g. mandatory PKCE) must land
   in the same change as a test asserting the rejected-by-default case, so later
   tests cannot silently assume lenient behavior. Symptom to watch for: a test that
   "expects exchange success" while minting placeholder credentials.
2. **Resolve state paths per call, never as import-time platform constants.** The old
   `AUDIT_LOG_HERMES_PATH` baked Windows' layout into a module constant, so POSIX
   hosts silently fell back to the package directory and ignored `HERMES_HOME`.
   Pattern: `_audit_candidate_paths()` — environment first, then platform homes,
   package dir last, evaluated at call time so tests/embedded deployments take effect
   immediately.
3. **Best-effort must not mean invisible.** Swallowing `OSError` on audit writes was
   correct (a tool call must never break on audit persistence) but silent loss of
   evidence is a defect. Pattern: count failures in a module-level diagnostics dict,
   expose an accessor (`audit_write_diagnostics()`), and surface it in
   `hermes_operator_doctor` as `WARN`.
4. **Append-only files need bounded readers and a rotation story.** Full-file parses
   of an append-only JSONL grow without bound on long-lived hosts. Pattern: size-capped
   rotation keeping exactly one `.1` archive, byte-bounded reverse-read tails (drop the
   potentially partial first line), and task reconciliation that iterates archive +
   active so one rotation does not lose per-task evidence.
5. **Environment-absent is a skip, not a failure.** Tests that depend on the
   distribution being installed (metadata checks) must `pytest.skip(...)` on
   `PackageNotFoundError`; a red test in a bare checkout is CI-forensics noise that
   masks real regressions.
6. **Pin lanes age; assert the contract, not the pin.** Exact CI pins drift while
   `pyproject` ranges admit untested versions. Pattern: explicit lanes for every
   shipped SDK version plus a protocol-revision assertion that fails with guidance
   when the installed SDK advertises a different revision.

### Local toolchain notes (small, reusable)

- `pyproject.toml` sets `addopts = "-q"`, so `pytest -q` at the CLI is `-qq` and hides
  the summary line — run bare `python -m pytest` for canonical output; the exit code
  is still trustworthy.
- A uv-based full run needs `uv run --extra dev --with pytest-xdist python -m pytest
  -n 8` (pytest lives in the `dev` extra; pytest-xdist is not a project dependency).
  Candidate: add `pytest-xdist` to the `dev` extra so the canonical command runs
  unmodified.
- Two-environment verification (bare system Python vs uv env with the distribution
  installed) caught a skip-vs-run divergence in `test_mcp_compat.py` and is cheap:
  it exercises both the non-installed and installed code paths of metadata tests.

### Context left for the next cycle

- **rm-008 (branch protection on master)** is sequenced immediately after the first
  green master CI run following this batch's merge; master is currently unprotected
  (`gh api .../branches/master/protection` → 404).
- **rm-010 (CI-load-only failures)** needs a history of green runs to differ against;
  its two symptoms are token-rotation-vs-issuance fencing and a delegation-reconcile
  `IndexError` (test line ~1208).
- **Next reliability batch candidates:** rm-005 (session-jobs retention + `_watch`
  hardening — the `_processes`/`_active_sessions` leak was still observable as
  teardown noise during this cycle's full-suite runs) and rm-006 (integer/Decimal
  budget money; the ledger still uses REAL/floats with exact `>=` quota crossing).
- **rm-004 residual:** `operator_fabric_view.py:523` still reads audit history with a
  full parse; fold into future audit-rotation work if that surface needs history.
- **Compatibility track:** rm-011 (official MCP Tasks extension mapping) and rm-012
  (MRTR approval handshake) are research-backed by the MCP 2026-07-28 spec GA; both
  are additive and gated on the SDK pin lanes from rm-009 being green first.
- **Rebase note (assess F10):** the campaign checkout `/work/projects/hermes-gpt` sits
  one docs-only merge behind `origin/master`; rebase before the next implement phase.

## Cycle 4 — 2026-09-30 — "Serving-loop correctness + fail-loud operator signals"

Run `bb9c68fb3ddf4c9fa77ead75cac72f07` (repository-maintenance
`029a8a7e970d4317997a96e5dab638eb`, cycle 1) against worktree at `14530e3e79`.
Phases: assess → research → roadmap → prioritize → stewardship → implement →
targeted tests → full tests → compound. All outcomes below are pre-review: the
batch is implemented and locally verified but uncommitted, awaiting the fold and
commit gates. Two sibling runs of the same campaign (run-041a92f6667d,
run-e13b1c0d37ea) worked the same base in parallel; this cycle's batch was chosen
to be disjoint from both (serving/UI surface vs their threads/state and
error-contract batches).

### What the cycle did

- **rm-076 (P110)** — offloaded every blocking sqlite/`SessionDB._lock` call
  reachable from async handlers off the single serving loop: `ui_chat.py`
  sessions/messages/chat-post handlers (asyncio.to_thread, the in-file
  extraction-helper pattern) and `operator_live_events.py`'s WS poll
  `read_since` (connect timeout=5 + two queries, previously every ≤0.5s per
  idle client on the loop). A lock-contention regression test holds
  `SessionDB._lock` in a background thread while a concurrent request must
  complete inside a bound — it times out against the pre-fix code.
- **rm-080** — replaced the tautological cursor clamp
  `max(next, min(high, next))` with a real high-watermark advance; the MAX(seq)
  is now read BEFORE the page query so a concurrent insert is delivered or
  rescanned, never skipped.
- **rm-078** — a failed `ui_api` mount (explicitly-enabled UI) now emits an
  audit record + `ui_mount_failed` live event while the server still boots, and
  `hermes_operator_doctor` reports a `ui_mount` WARN from the audit tail.
- **rm-079** — `operator_events` now applies the source allowlist once at the
  boundary for BOTH `hermes_events_query` and `hermes_events_tail` (truthful
  `sources_queried`, warnings on both paths); `_collect` stays the enforcement
  point.

Verification (pre-review): targeted uv run of the 10 changed surfaces
144/144/0/0; the engine's full gate (`local_validation_gate.py --shell-command
'uv run python -m pytest -q -n 8'`) exit 0 with 0 failed/errored and 2
pre-existing environment skips; ruff clean. 14 tracked files changed,
+509/−23, including 11 new regression tests.

### Prevention rules established

1. **Async handlers own no blocking store.** Any sqlite/lock/timeout-bound call
   reachable from an async handler or WS loop runs via `asyncio.to_thread`
   (the in-file extraction-helper pattern is the reference). Symptom class: a
   shared lock with a 5s busy timeout plus sync TestClient tests that can
   never observe the stall. Enforce with a contention regression test (hold
   the lock in a thread, bound a concurrent request), not just green suites.
2. **Paginate against a pre-read watermark.** In snapshot-per-connection
   stores, read the high watermark BEFORE the page query: a late-arriving
   higher seq is then delivered or rescanned instead of skipped forever.
   Tautological clamps (`max(x, min(h, x))`) hide as dead queries — a clamp
   must change the value in at least one tested case or be deleted.
3. **Fail-loud extends to mounting, not just calls.** Cycle-1 rule 3 ("best
   effort must not mean invisible") applies to surface assembly: an
   explicitly-enabled surface that fails to attach must produce an audit
   record + live event + doctor check, never an eprint only.
4. **Validate new tests in the project lane, not the ambient interpreter.** A
   test importing `httpx` passed under the ambient Python but failed the uv
   gate (httpx is not a project dependency). Test helpers are dependency-free
   (raw ASGI calls) or uv-declared.
5. **Audit-reading tests must pin the audit override.**
   `set_audit_log_override` leaks across tests sharing an xdist worker
   (mission/swarm fixtures), while the events audit reader resolves
   `<hermes_root>/logs` independently — pin the override in try/finally or the
   test depends on worker scheduling. Follow-up candidate: an autouse reset
   fixture.
6. **Parallel campaign runs mint ids independently.** Three sibling runs each
   allocated `rm-076`+ on the same base; the landing gate must dedupe by scope
   and renumber before integration. Roadmap blocks carry run-ids and
   orig-id annotations so collisions are detectable in place.

### Local toolchain notes (small, reusable)

- The conductor validation gate self-throttles under system load (admitted
  workers=1 at load1=21.74) — a slow-but-green full gate is still a valid full
  pass; do not re-run for speed alone.
- Neither conductor validation script prints a digest; the digest is a
  manifest hash. Identical digests across two dispatches proves the tree
  unchanged between them — useful as a zero-cost identity check.
- The impacted-tests runner (`run_repo_impacted_tests.py --mode fast`) is the
  correct focused lane and honors the uv venv; ambient `python -m pytest` is
  not equivalent (rule 4).

### Context left for the next cycle

- **Upstream adoption is the headliner (rm-081, P115):** upstream/master is 8
  commits past merge-base `7795aa3ce8`, including the issue-#74 full half
  (explicit-load resolution, fail-closed loader errors, `preprocess=False`
  probes; `operator_skill_resolution.py` delta 546+/285−). PR #76 closed
  unmerged — master is the sole carrier. Both sibling runs minted equivalent
  items; none selected it (L effort, 3-way reconciliation). rm-054/rm-036
  fold into it; rm-053 closes with it.
- **rm-079 residual:** the same allowlist-indirection pattern exists at
  `operator_mission_ledger.py:623` and `operator_capability_manifest.py:483`.
- **Packaging pair:** rm-077 (browser-UI build path, collides with sibling
  041a92f6's pyproject/MANIFEST work — coordinate at the landing gate) and
  rm-083 (v0.13.0 release-readiness; deployed remote is 47 commits behind;
  blocked on rm-065/rm-069 policy).
- **Landing-gate duties:** renumber the three sibling `rm-076`+ sets; reconcile
  the pre-existing duplicate id lines recorded in the cycle-4 ROADMAP header;
  apply the server.py cross-run separation hint when integrating the sibling
  ToolError hunks.
- **Candidate hardening:** autouse fixture resetting `set_audit_log_override`;
  additive py3.13 CI lane (ci edits were prohibited in-cycle); the two
  environment-dependent skips in the full suite remain unowned.

## Cycle 5 — 2026-10-01 — "Operator async-surface reliability close-out +
stale-gate unblock"

Run `1a6beebac21c4907ad8195fc9c5e90fa` (repository-maintenance
`00b0db0d136e4dfe9a9bff361e8c362d`, cycle 2) against worktree at `caf60018d2`
(run-1a6beebac21c-1a6beeba, branch `conductor/run-1a6beebac21c`). Phases:
assess → research → roadmap → prioritize → stewardship → implement → targeted
tests → full tests → compound. All outcomes below are pre-review: the batch is
implemented and locally verified but uncommitted, awaiting the fold and commit
gates. Sibling families worked the same base in parallel (0aa75ea44f93 holds an
uncommitted cycle-5 block minting rm-085..rm-094; this cycle's ids start at
rm-095 and the landing gate dedupes content overlaps — upstream v0.13 adoption
is held by both).

### What the cycle did

- **rm-095 (P85)** — the live-events WS loop now adopts `read_since`'s
  watermark on empty filtered pages (cursor adoption moved above
  `if events:`), so an idle topic/kind-filtered client no longer rescans the
  non-matching journal tail from a stale cursor every ≤0.5 s poll; rm-080's
  delivered-or-rescanned-never-skipped guarantee is preserved and
  `docs/live-events.md`'s cursor-semantics paragraph now holds verbatim.
- **rm-096 (P90)** — the mission-events long-poll
  (`/api/ops/missions/{mission_id}/events`, 25 s max wait) no longer parks
  tokens on anyio's shared 40-token default threadpool limiter: it runs through
  a dedicated `anyio.CapacityLimiter(40)` via `anyio.to_thread.run_sync(limiter=...)`,
  so 40 concurrent long-polls can no longer starve every other offloaded
  handler and sync route. Behavior unchanged.
- **rm-097 (P88)** — `hermes_cron_run` dispatch through
  `POST /api/ops/action` is now bounded (cap 4; cap-exceeded requests get 429
  RATE_LIMITED like the chat turn gate), registry-tracked (active/finished in
  the 202 body), audited at COMPLETION with the real outcome + duration
  (previously a success-marked record at dispatch time), and observable via
  `hermes_operator_doctor`'s new `ui_cron_dispatch` check (stuck-run WARN).
  docs/operator-mode.md + docs/flight-deck-coverage.md updated.
- **rm-099 (P55)** — pyproject declares `starlette>=0.40,<2` and `anyio>=4,<5`
  as direct dependencies (both were direct imports resolved only transitively
  via mcp[cli]) with the transitive-source comment; resolved set unchanged.
- **rm-053 (decision-slice)** — stale gate closed: upstream PR #76 is closed
  unmerged (2026-10-01 probe) and the skill-name grammar slice it gated landed
  at HEAD; gate text removed from the roadmap entry.

Verification (pre-review, repo .venv, tests-first red→green with a red witness
at each defect site): targeted_command exit 0 — the runner self-escalated to
the authoritative full gate (pyproject.toml in FULL_IMPACT_FILES; envelope
result-739098, returncode 0, workers 2, 377 s; count recovery `1610 passed, 5
skipped, 1 warning in 238.09s`); focused 4-file lane `116 passed, 1 warning in
11.23s`; full_command VERBATIM exit 0 (envelope result-1529618, returncode 0,
workers 1 admitted at load1=31.31, ~457 s; count recovery `1610 passed, 5
skipped, 1 warning in 261.35s`); ruff `All checks passed!` at both gates;
validation digest `validation:v1:4a1f4beb1ad6e848a678594cb0c6526255ff43fda34e4b2cc99cf998838ec608`
declared verbatim and recomputation-verified byte-identical. 12 tracked files
changed, +664/−12, including new regression tests for every unit.

### Prevention rules established

1. **Watermark adoption is an empty-page concern.** Advance the cursor on the
   pages you did NOT deliver; a loop that only advances when events arrive
   rescans the tail forever for exactly its quietest (idle, filtered) clients.
   Keep the truncated-page stop so no event is skipped; test the idle-filtered
   client advances past N non-matching events without rescanning.
2. **anyio's default limiter is a global budget, not a default.** Every
   `run_in_threadpool` call without `limiter=` shares one 40-token pool; a
   wait-bearing offload parks tokens it doesn't need (the rm-076 loop-stall
   class relocated into the pool). Wait-bearing endpoints get a dedicated
   CapacityLimiter, proven by a saturation test that parks all 40 default
   tokens.
3. **Fire-and-forget dispatch manufactures false audit trails.** A success
   record written at dispatch time is a guarantee of a wrong trail for every
   failed/wedged run — evidence integrity, not just reliability. Mutating
   long-runners ship bound + registry + completion-time audit (real outcome +
   duration) + doctor visibility together.
4. **Every directly-imported distribution is a declared dependency.** Diff
   import roots against `[project]` dependencies; undeclared transitive
   resolution is an install-time contract gap. New declarations name their
   transitive source and leave the resolved set unchanged.
5. **Stale gates name their re-verify trigger.** rm-053 closed in one probe
   because its gate text recorded the concrete signal to re-check (PR #76
   merge state); gates that record only the blocking fact rot into research
   projects.

### Local toolchain notes (small, reusable)

- The gate's own result envelope carries `digest_base: unknown` — its digest
  is NOT the engine's validation digest. Declare the dispatch digest and, when
  tree identity matters, recompute via
  `hermes_conductor.validation_policy.validation_digest(<full HEAD sha>, repo)`
  (a short sha or 'unknown' base yields a different, non-matching digest).
- Repo addopts `-q` stacks with CLI `-q` into `-qq`, which suppresses even the
  summary line — counts need `python -m pytest -o addopts= -q` (cycle-3 rule 5,
  still true in cycle 5).
- Under fleet load the admission gate may spend its whole 900 s resource-wait
  window before pytest starts (observed: a foreground 900 s tool ceiling
  killed the run with an empty log and no envelope; the detached rerun
  admitted workers=1 at load1=31.31 and passed). Run the verbatim gate command
  detached and poll by PID; a slow-but-green gate is still a valid full pass
  (cycle-4 note, mechanism now identified).
- `run_repo_impacted_tests.py` self-escalates to the authoritative full gate
  when pyproject.toml is in the changed set (FULL_IMPACT_FILES) — a targeted
  dispatch can therefore carry full-gate evidence; read the gate's envelope
  rather than the runner's exit code alone.

### Context left for the next cycle

- **rm-098 (P115) upstream v0.13 Autopilot adoption** (9-commit gap, tip
  f4151d972; no v0.13 tag yet; PRs #83/#84 open docs/site-only) — FLEET
  INTERLOCK: sibling 0aa75ea44f93 holds the same topic as its uncommitted
  rm-085; landing gate dedupes, do not implement twice; rm-081 folds into it
  (issue #74 closed 2026-09-29).
- **rm-100 (P75) Python 3.10 EOL 2026-10-31** — next cycle lands inside the
  window; dated floor-bump decision (3.11 floor, 3.13 lane, tomli conditional
  removal) rides the next release batch (CI edits prohibited in-cycle).
- **rm-101 (P25)** — own the two environment-dependent skips
  (test_operator_export.py:129, test_operator_policy.py:711) and add the
  autouse `set_audit_log_override` reset fixture (cycle-4 rule 5 follow-up).
- **Landing-gate duties:** reconcile this cycle's rm-095..rm-101 ids against
  sibling 0aa75ea44f93's uncommitted rm-085..rm-094 block (landed-first wins)
  and the sibling b6659410/099e2bfc candidate sets at integration; the 12-file
  batch (+664/−12) is uncommitted with digest
  `validation:v1:4a1f4beb…ec608` current at compound time.

## Cycle 6 — 2026-10-01 — "Cron arm-to-dispatch truthfulness close-out"

Run `bf4db34f3880424f976254e81cf56fe0` (repository-maintenance
`63b87a5f9bf14df0b678cdd43a2ee395`, cycle 2) against worktree at `941f4cfc69`
(run-bf4db34f3880-bf4db34f, branch `conductor/run-bf4db34f3880` = canonical
master `dce209dfcc` + 12 conductor run-merges, including cycle 5's landing
`d1f252ec2e`). Phases: assess → research → roadmap → prioritize → stewardship →
implement → targeted tests → compound. All outcomes below are pre-review: the
batch is implemented and locally verified but uncommitted, awaiting review and
the fold/commit gates. Sibling families worked the same base in parallel and
minted roadmap ids concurrently this morning (61db9bce `d863b69e`, c5fba76a
`5e1ae1a7`) — see Landing-gate duties below; this cycle minted rm-131..rm-140
at 08:42:40Z off the then-frontier rm-130 and raced both.

### What the cycle did

- **rm-131 (P90)** — closed the fresh-landing semaphore leak from cycle 5's
  rm-097: `ui_ops.py` long-running dispatch now runs EVERYTHING between
  semaphore `acquire()` and thread `.start()` (the `_resolve_root()` call and
  the registry insert) inside the failure handler that pops the registry entry,
  releases the token and returns a clean 500 INTERNAL. Previously a raising
  `_resolve_root()` leaked one token per failure (limit 4) until every
  long-running `hermes_cron_run` 429'd until restart. Red witness → green
  (limit+2 injected failures, then a recovered dispatch accepted 202).
- **rm-132 (P72)** — `hermes_cron_create` dry-run plans now carry
  `schedule_preview {schedule_kind, timezone "<name> (UTC±HH:MM)", times[>=3]}`
  via new `_schedule_preview()` (interval arithmetic; cron kinds through the
  existing lazy croniter import; once-schedules a single labeled fire time).
  Converts the whole parser-edge class into a pre-arm confirmation; tz contract
  documented in `docs/operator-mode.md` "Schedule grammar and fire-time
  preview".
- **rm-057 floor slice + rm-138 (P44)** — `_interval_schedule` rejects
  minutes<1 with a dedicated "at least 1 minute" message (the fallthrough was
  restructured so the message is not swallowed by the generic error);
  `_WEEKDAY_TO_CRON_DOW` gains all seven plural weekday keys; a hypothesis
  dev-group property lane (derandomized, 100+100 examples) pins
  weekday-grammar→cron-expr croniter-validity, the floor, zero-rejection and
  per-kind preview. DEVIATION recorded at implement: rm-138's acceptance named
  a `_format_schedule` round-trip invariant — no such function exists
  (speculatively written acceptance); the four pinned invariants cover the same
  intent. rm-057's manifest-walk memoization slice remains open.
- **rm-140 (P30)** — the doctor `ui_cron_dispatch` check now declares its
  in-process scope in the PASS detail (plus `scope='in-process'` in the
  payload) and `docs/operator-mode.md` states the caveat with the
  durable-audit-log alternative for cross-process authority.
- **Adopted from a reaped same-phase attempt (718e3b7b)** — the targeted-tests
  attempt reaped mid-turn left a real 7-line fix in-tree (property lane
  `deadline=None` + `suppress_health_check=[HealthCheck.too_slow]`), verified
  against the implement batch reconstruction and adopted rather than redone;
  the verbatim gate run it never performed was redone from scratch.
- **Disposition of this run's assess findings** — F1 (semaphore leak) → rm-131
  implemented; F2 (zero-interval floor) → rm-057 slice implemented; F3
  (job_wait occupancy) → rm-063 refreshed, still open; F4 (doctor cross-process
  caveat) → rm-140 implemented; F5 (plural weekdays) → rm-138 implemented.
  Five of five triaged, four closed pre-review.

### Validation record (pre-review)

targeted_command verbatim (detached `setsid`/`nohup` wrapper,
`/tmp/a8ed99d3-scratch/`): the runner classified `pyproject.toml` as shared
build/test configuration and self-escalated to the authoritative full gate via
its own `--fallback-command` — envelope `result-356086-335547330.json`,
returncode 0, outcome completed, workers 3, 162 s; dot-count **1617 passed +
5 skipped = 1622, 0 failed**, exactly implement's collect-only 1622 (assess
baseline 1615 + 7 net-new); the 5 skips are the standing platform-gated set.
Declared digest `validation:v1:8e40bd12…d1fbfd2` — recomputed byte-identical
BEFORE and AFTER the run via `validation_policy.validation_digest(full HEAD)`,
and unchanged at compound time because this phase touches only non-executable
surfaces (`ROADMAP.md`, this log), which the digest excludes by construction.
Static: ruff clean on all seven changed surfaces under both system ruff 0.15.10
and `uvx ruff@0.15.22`.

### Prevention rules established

1. **Every acquire→release span must cover everything that can raise inside
   it.** rm-131's leak was a semaphore acquired before a `_resolve_root()` call
   whose exception escaped past the release (the `except` guarded only
   `.start()`). Fix pattern: resolve/validate first, then acquire; or wrap the
   entire span so every exit releases. The regression-test pattern that
   actually catches this: inject the failure MORE times than the limit, then
   assert a subsequent dispatch still succeeds.
2. **A batch that touches `pyproject.toml` runs the full suite in the targeted
   phase.** `run_repo_impacted_tests.py` hard-classifies pyproject.toml as
   shared build/test configuration and self-escalates through its own
   `--fallback-command` (the authoritative full gate). Budget for full-suite
   timing (162–340 s fleet-observed) and remember addopts `-q` stacking
   suppresses pytest's summary line — reconcile counts by dot-count.
3. **Property lanes under fleet load need load-robust settings from day one.**
   The cron property lane flaked as `FailedHealthCheck.too_slow` (8 draws,
   5.46 s) under load1≈24 before `deadline=None` +
   `suppress_health_check=[HealthCheck.too_slow]` + `derandomize=True` were
   added (the adopted 718e3b7b delta). Any future hypothesis lane starts with
   those settings.
4. **Name the interpreter when reconciling skip counts.** `importorskip` makes
   skips interpreter-dependent: the hermes-agent venv `python3` has no
   hypothesis, while the gate's `python` resolves to
   `/work/projects/hermes-autonomy/.venv` (hypothesis since 2026-10-01T10:32Z).
   The same tree showed "136 passed, 1 skipped" under one and 137 passed under
   the other.
5. **In-process introspection checks must declare their scope.** A check built
   on process-local state (rm-140's registry read) reads as 0/0 + PASS from any
   other process. Scope declaration belongs in the check's detail text AND its
   docs paragraph; audit-log-backed checks are the contrast class.
6. **A reaped attempt's absent envelope is not evidence of no work.** Check
   per-file mtimes inside the reap window and reconstruct candidate deltas from
   the implement batch diff before redoing; adopt verified durable work — the
   engine derives the dispatch digest after the reap, so adopted work is
   already inside a verbatim-declarable digest (prove it by recomputation, as
   done here pre- and post-run).
7. **Roadmap id minting must re-probe live and mint past the OBSERVED fleet
   max.** This cycle minted rm-131..rm-140 at 08:42:40Z off the then-frontier
   rm-130; siblings minted rm-131..rm-135 (61db9bce, 08:43:54Z) and
   rm-131..rm-140 (c5fba76a, 08:42:19Z, renumbered to rm-141..rm-150 on
   observing the race) within two minutes. The observed fleet frontier is now
   rm-150 (all unlanded); the next roadmap phase anywhere continues at rm-151+.
   rm-139 (`tools/check_roadmap_ids.py`) mechanizes exactly this and is now
   justified by an observed incident, not a hypothetical.

### Local toolchain notes (small, reusable)

- Gate runs detached (`setsid`/`nohup` wrapper) survive delegate reaps; the
  gate admitted at workers=3 under load1≈17–38 and writes envelopes under
  `~/.hermes/local-validation-gate/results/`.
- `.hypothesis/` self-ignores (its own `.gitignore` containing `*`), so the
  hypothesis constants cache never dirties a census; `.pytest_cache/` is
  `.gitignore:13`.
- ruff parity: system 0.15.10 vs `uvx ruff@0.15.22` agreed (clean/clean) on
  all seven changed surfaces.

### Context left for the next cycle

- **Still-candidate items minted here:** rm-133 fork distribution identity
  (DECISION-GATED: local version segment vs never-publish — must precede any
  0.13-numbered fork release), rm-134 fetch-metadata + content-type hardening
  on browser-UI POSTs, rm-135 live-deployment provenance capture +
  uncommitted-delta release blocker, rm-136 browser-UI agent-runtime
  cross-project seam, rm-137 OpenAPI description from the 20-route HTTP
  surface, rm-139 roadmap id-allocation guard (elevate: rule 7's incident),
  plus the refreshed rm-063 (job_wait occupancy) and rm-098 (upstream v0.13
  adoption) which stay open. rm-057's manifest-walk memoization slice rides
  the next batch.
- **Cross-family topics for the next assess to re-derive, not re-mint** (held
  in sibling uncommitted blocks): write-claim atomicity, SessionDB shim
  capability contract, web transport-resilience client wiring, finance
  request_id confinement, validate_public_url redirect/rebinding pin, py3.11
  floor (c5fba76a rm-141..rm-150); `hermes_mission_usage` 24h-vs-all-time
  totals (61db9bce assess F6, defect-class).
- **Landing-gate duties:** this cycle's batch is uncommitted with digest
  `validation:v1:8e40bd12…d1fbfd2` current at compound time; fold id
  collisions landed-first-wins — rm-131..rm-135 collide with sibling 61db9bce's
  block (different content); the provenance topic is triple-held (rm-135 here,
  61db9bce rm-133, c5fba76a rm-148); upstream remains frozen at tip
  `f4151d9728` (9 commits ahead, no v0.13 tag; PR #85 touches
  `operator_workspace.py` — check it before any backup-related work).

## Cycle 8 — 2026-10-04 — "Operator write-path defaults you can trust"

Run `efe7657638c74fa4a5e929f0ecd6cea1` (repository-maintenance
`5260fbbbcd3a4f408340d2759420dec7`, campaign
`hermes-gpt-conductor-run-dbf82ae4683a-a501872d8ba07e19`, cycle 3) against
worktree run-efe7657638c7 at `e490130737` (rebased fast-forward from the
assessed base `30de0067f9` at implement, zero conflicts — batch files
untouched by #26/#27/#28). Phases: assess → research → roadmap → prioritize →
stewardship → implement → targeted tests → full tests → compound. All outcomes
below are pre-review: the batch is implemented and locally verified but
uncommitted. Heading numbering note (re-verified 2026-10-04 by attempt
f9f233f9): the committed log ends at Cycle 6 and Cycle 7 exists nowhere on
disk — an earlier pass recorded an uncommitted `## Cycle 7 — 2026-10-03` in
sibling 9b1770fc3065, whose worktree now ends at Cycle 6; sibling
2f81870e7a06 still holds a date-headed `## Cycle 2026-10-03` entry and
sibling d92e1ad3 an uncommitted `## Cycle 9 — 2026-10-04` (same line-491
append anchor as this entry). This entry stays Cycle 8; renumber/fold at
the landing gate.

### What the cycle did

- **Batch lead — operator file-backup configurability (fleet id `rm-192`,
  this run's mint, ships as the insert-only ledger patch
  `/tmp/92395980-scratch/ROADMAP.ledger.patch`, unlanded).** Upstream PR #85
  (asimons81/hermes-gpt, brunocasado, still open/patch-less per research
  2026-10-03) was adopted by SHAPE and hardened: env const
  `HERMES_GPT_OPERATOR_FILE_BACKUPS` (`operator_workspace.py:70`) gates the
  shared `_backup_file` helper (`:115-116`) covering the four workspace/owner
  write tools; `operator_config.py:234-241` DELEGATES to the same helper
  (replacing a private duplicate that left the four profile-config writers
  ungated) — one gate, eight direct-write sites. Parse is fail-closed
  (`_file_backups_enabled`, `:76`): unset = backups ON (default unchanged);
  recognized false set `{0,false,no,off,disabled, ""}` case-insensitive;
  any unrecognized value keeps backups ON and stamps a `backup_warning`
  naming the value on direct-write tool results. Docs:
  `docs/operator-mode.md` "Optional file backups" (8 tools listed), README
  pointer, CHANGELOG "Unreleased" entry. Tests: 7 new in
  `test_operator_workspace.py` (incl. `test_file_backups_unrecognized_value_fails_closed`
  `:873`, owner-parity `:861`, empty-string `:911`, case-insensitive `:927`)
  plus the delegation drift-guard in `test_operator_config.py`. Live
  delegation probe: `=0` → `_backup_file()` returns None; `'fals'` → backup
  created + warning contains "fail-closed".
- **Batch rider — own the environment-dependent skips + autouse audit-override
  reset (`rm-101`).** `conftest.py:177` autouse `_reset_audit_log_override`
  snapshots/restores `operator_policy._audit_log_override` around every test
  (a fixture dying between set and teardown could previously leak the
  process-global override into every later test's audit records — same
  ordering-hazard family as the fleet's test_server-before-test_gemini_compat
  pollution). New `test_suite_determinism.py` pins both halves: the
  skipif-inventory guard (`:42` — every environment-dependent `skipif`
  registered; new skips fail until registered) and the audit-leak regression
  pair (`:64`/`:70`). rm-101's tracked ROADMAP block carries the dated update;
  status flip deferred to the landing gate.
- **Assess/research substrate (consumed, not re-derived):** assess found
  A1-A19 at `30de0067f9` on a green full-suite baseline; research root-caused
  10 consecutive master CI failures (2026-10-01→10-03) to the py3.10
  `asyncio.TimeoutError`-vs-`TimeoutError` class (fixed by #27
  `58a70ddd5e`) plus a 3.12/mcp>=2 lane flake (green at `e490130737`, run
  37107958208); upstream drift 0; PR #85 open; dependency lanes verified
  0-vuln at starlette 1.7.0 / cryptography 50.0.2 / anyio 4.15.1 /
  uvicorn 0.54.0 / mcp 2.3.0; Python 3.10 EOL passed 2026-10-01.

### Prevention rules

1. **Adopting an upstream patch's shape does not adopt its safety posture.**
   PR #85's gate `raw is not None and not op.is_truthy(raw)` is fail-OPEN for
   a loss-prevention default: `is_truthy` (`operator_policy.py:81`) treats
   anything unrecognized as falsey, so a typo'd env value silently DISABLES
   backups. Any gate guarding a destructive-adjacent default must parse
   recognized-true/recognized-false explicitly and fail toward the safe side
   on unrecognized input, surfacing the offending value — pinned by
   `test_file_backups_unrecognized_value_fails_closed`.
2. **Census for duplicate helpers before gating "the shared one".** The
   upstream PR gated only `operator_workspace._backup_file`;
   `operator_config.py` carried a private duplicate covering four more write
   tools, which would have stayed ungated. `git grep` the helper name
   repo-wide before claiming one-gate coverage; keep the delegation +
   drift-guard test so the duplicate cannot regrow.
3. **Write conftest/global-state hooks from source, not memory.** The first
   autouse attempt guessed `_AUDIT_LOG_OVERRIDE`; the real process-global is
   `operator_policy._audit_log_override` (`:70`). Read the owning module
   before snapshotting a global in a fixture.
4. **Environment-dependent skips are a determinism surface.** A new `skipif`
   silently changes what "green" means per host. Register it in the
   skipif-inventory guard (owner note or hard condition, per rm-101
   acceptance) or the suite fails it.
5. **Read the prior attempt's event log before any durable write.** This run
   reaped two prior attempts (research `8a91ba4b` at ~100 s; compound
   `7735f749` at 3.4 s — zero work). One `cat` of the `.jsonl` distinguishes
   "nothing happened" from "durable writes exist to verify", and prevents
   double-applied append-only edits.
6. **Validation records claim currency — later phases must supersede.** The
   envelope below is current at compound time. Any phase that touches
   executable surfaces after this point (e.g. a review-fix pass) must refresh
   the shipped validation records and explicitly supersede this envelope —
   never leave a stale envelope as the final state.

### Validation record (current at compound)

- Targeted (work-order command, 10 changed surfaces): RC=0 first run, zero
  fixes (`/tmp/5dcc0dec-targeted/run1.log`); ruff over the 10 surfaces clean.
- Full gate (verbatim `local_validation_gate.py --shell-command 'python -m
  pytest -q'`): GATE_RC=0, envelope
  `/home/agent/.hermes/local-validation-gate/results/result-2088694-354043546.json`,
  digest `validation:v1:162865e8e0aedadbb4b9c06760278e38af343ef5814c42970939b776d2f21629`,
  single admitted run, dot-grid 1807 passed + 5 skipped = 1812 outcomes,
  0 failed / 0 errored, tree unchanged (8 M + 1 ??) across the phase.
- Caveat (known fleet nuance): the envelope's `digest_base` is `unknown`
  (standalone local-validation-gate write); the authoritative equality check
  is recomputing `validation_digest` from an installed conductor release at
  the review/final gates.

### Local toolchain notes

- The compound phase ran under an explicit no-test constraint: all validation
  facts above are consumed from the recorded targeted/full phase evidence,
  not re-executed.
- Compound's own delta is docs/ledger-only (repo ROADMAP.md rm-101 dated
  update, this log entry, campaign-roadmap 'Cycle 3 outcome' append) — no
  executable surface changed after the full gate, so the envelope above
  stays current. The ce-compound `docs/solutions/` sink was deliberately
  NOT used: fleet precedent (9b1770fc3065; d92e1ad3 cycle 2) treats
  docs/solutions/ as a live-system ops-runbook contract — the reusable
  lessons live in this entry instead. (Correction by attempt f9f233f9,
  2026-10-04: reaped attempt 8bbf0930 had described a solutions runbook +
  index row it never wrote before dying; this entry now matches the tree.)

### Context left for the next cycle

- **Fleet frontier:** this run minted `rm-192` (campaign board + ledger
  patch, unlanded); siblings hold rm-181/190/191-max patches and uncommitted
  renders. Next mint re-censuses live (worktree greps + delegate spool), not
  from this log.
- **Landing-gate flips already proven stale-open:** `rm-081` + `rm-098`
  (content satisfied at master via #25 `125255c0bc`; upstream drift 0 incl.
  #82/#83/#84) — flip, do not re-implement.
- **Unselected pool for the next assess/prioritize:** A1 boundary findings
  (WS foreign-Origin accepted at `operator_live_events.py:402-403`;
  text/plain + foreign-Origin dispatch; foreign-Host GET 200), A2 residue
  beyond #27's live-events fix (`ui_ops.py:700`, `ui_chat.py:748/761/490`,
  `operator_autopilot.py:523/530-559/1824-1827`,
  `operator_job_supervisor.py:457-469/511-540`,
  `operator_cron.py:425-447/1271-1283`, `ui_security.py:207`,
  `oauth_auth.py:1430-1439` — bare `except TimeoutError` missing py3.10's
  distinct `asyncio.TimeoutError`; a 3.11-floor bump may fold the class since
  3.10 EOL'd 2026-10-01), A12 (sdist ships zero docs assets), research S1-S5
  folds (`rm-077`/`rm-083`, `rm-177`, `rm-048` + `rm-173`), the
  0-vuln dependency lanes above, `rm-038` branch protection (human/admin
  lane), `rm-139` id-guard (owned by dfaf334f's `rm-195`).
- **Upstream back-contribution candidate:** propose the fail-closed parse
  (rule 1) as an amendment/comment on PR #85 before upstream lands the
  fail-open gate verbatim.
- **Docs-truth note (corrected by attempt f9f233f9):** an earlier compound
  pass claimed `docs/solutions/README.md` indexes a missing runbook — false
  on verification: `runner-cancel-workspace-authority.md` IS tracked at HEAD
  `e490130737` (`git ls-files docs/solutions/` + `git show HEAD:…` both
  confirm). The surviving gap is real but smaller: `docs/solutions/` has no
  pointer from `docs/README.md`'s authority map or AGENTS.md
  (discoverability gap for a live-system ops-runbook directory).

### Landing-gate duties

- Fold the stacked ledger patches in mint order (79b3e882, 03ec00ae,
  ca49ab4b, this run's `/tmp/92395980-scratch/ROADMAP.ledger.patch`),
  resolving rm-180..191 collisions by title; status flips: this batch
  (`rm-101`, `rm-192`) and the stale-open `rm-081`/`rm-098`.
- Delta at compound: 10 M + 1 ?? (implement's 8 M — CHANGELOG.md, README.md,
  conftest.py, docs/operator-mode.md, operator_config.py,
  operator_workspace.py, test_operator_config.py, test_operator_workspace.py
  — plus compound's repo ROADMAP.md and this log; untracked:
  test_suite_determinism.py; docs/solutions/ untouched). CHANGELOG
  "Unreleased" + `docs/operator-mode.md` + README ride the batch; supersede
  the validation envelope only if a later phase edits executable surfaces.

## Cycle 13 — 2026-10-05 — "Concurrency isolation for Operator profile scoping"

Run `9037c3156272472abdb533396c66a368` (repository-maintenance
`ebb00eda4cbb43c9b2877a78f678d852`, cycle 3, campaign
`hermes-gpt-fix-ci-fast-lane-59762166ca1fd70a`) against worktree
run-9037c3156272-9037c315 (branch `conductor/run-9037c3156272`): assessed at
`30de0067f9` (clean tree; then-`origin/master` `e490130737` carried #26/#27/#28
unlanded), implemented at `c43d085121` (fast-forwarded past the mandated
`e490130737` to `origin/master`; the run's ROADMAP mint survived the ff via
stash/ff-only/pop, content-identical, insert-only +14/0- against the new HEAD).
Phases: assess → research → roadmap → prioritize → stewardship → implement →
targeted tests → full tests → compound. All outcomes below are pre-review: the
batch is implemented and locally verified but uncommitted, awaiting review and
the fold/commit gates. Two earlier same-phase attempts died transport-dead
(roadmap `40e74fd4`; stewardship `bc0f426e` at +1.7 s) leaving nothing durable
— both phases were redone from scratch after envelope forensics. Numbering
note: this tree's committed log frontier was Cycle 8; unintegrated sibling run
branches hold Cycle 9 (d92e1ad3 "Swarm state co-ownership"), 10 (e1e8d7ec
"Supply-chain & perimeter truth"), 11 (dfaf334f "Canonical ledger truth
repair"), 12 (73696bb0 "Repo & release truth closure"). This entry mints Cycle
13 past the observed max (cycle-6 rule 7 discipline); renumber/fold at the
landing gate.

### What the cycle did

- **Batch lead — rm-207 "Operator profile isolation" (fleet id minted this
  cycle, priority 65; assess ff09ba0a finding F03 P2, probe
  `PROFILE_BLEED: True` at base).** New shared-gate module
  `operator_profile_scope.py` (134 lines): a profile-keyed Condition gate where
  same-home holders overlap, different-home holders are mutually exclusive, and
  same-thread conflicting nesting raises `ProfileScopeConflict` instead of
  deadlocking; no logging, no registry, no audit-material capture (raw-prompt
  and audit invariants preserved). `operator_skill_resolution._profile_scope`
  (:193-204) now delegates through `profile_override_scope` (degradation
  contract unchanged), and `operator_skills._call_skill_manager` (:218-240)
  wraps its whole set→mutate→reset window in `profile_override_gate` (the
  fail-closed non-default degradation is preserved and covered by a test).
  `pyproject.toml` ships the new module via py-modules (wheel-built and
  verified SHIPPED). Regression suite `test_operator_profile_isolation.py`
  (11 tests, 475 lines): sampling interleave through both repo paths,
  structural-barrier exclusion, same-profile overlap preserved, nested-conflict
  raise, subprocess env captured at spawn is profile-pure, parent `os.environ`
  never mutated, no profile material in logs. RED PROOF: with the gate
  neutralized (`/tmp/69034104-implement/redproof_plugin.py`) the four bleed
  detectors FAIL with cross-profile homes observed and PASS with the gate.
  SITE CORRECTION recorded in the ledger entry: rm-207's acceptance cited
  `operator_fabric.py` sites that have ZERO mechanism hits at both bases — the
  real in-parent sites were exactly the two gated above (see prevention rule 1).
- **Batch partner rm-086 tier-2 (secret-path writes 0600-from-first-byte, F21)
  — DROPPED, not implemented.** The mandated dispatch-time dirty-file scan
  caught sibling run-a0f8eb89b525 holding an uncommitted
  `token_store.py` (+75/−30) implementing exactly that acceptance; escalated
  to the coordinator per the prioritization batch terms and ratified as a
  land-once duplicate. The sibling batch is now committed at `65fb97510f` on
  branch `conductor/run-a0f8eb89b525` (pushed to origin/fork/codeo1io, NOT yet
  in `origin/master`).
- **Deferred by batch terms:** the `hermes_state.py:79` module-singleton prong
  (invalidate/rebuild handles on override enter-exit) belongs to the
  rm-105/106 lane (sibling 2f81870e's files); the new module deliberately does
  not touch it.
- **Substrate consumed, not re-derived:** assess ff09ba0a's 28 findings (1 P1
  F01 real-stack CSRF/Host/Origin proof via `server.build_server()` +
  `build_asgi_app()`; 12 P2; 15 P3; 6 new this attempt; suite re-proven green
  at base, sdist rc=0 with 0 web/assets entries) and research e63859b8's 5
  candidates + 2 confirmations + 5 negative results were ALL folded to
  existing fleet ids by the roadmap phase — this cycle minted exactly one id
  (rm-207). Full fold map: run-worktree `ROADMAP.md` cycle-3 additions block.

### Validation record (current at compound)

- Targeted (work-order command verbatim from repo root):
  `run_repo_impacted_tests.py` classified `pyproject.toml` (a FULL_IMPACT_FILES
  entry) among the 19 changed surfaces and self-escalated to the authoritative
  full gate — envelope `result-1988489-359778946.json` (returncode 0, workers
  1, 355.3 s); progress-char recount over all 26 percent lines: 1821 passed +
  5 skipped = 1826 outcomes, 0 failed / 0 errored. Focused 21-file lane: 313
  passed + 1 skipped (`test_operator_workspace.py:221`, Windows-only) in
  98.56 s; the implement-phase environmental failure
  `test_operator_skill_resolution.py::test_disabled_skill_rejected` PASSED
  under the gate interpreter (see rule 5).
- Full (authoritative command verbatim, gate wrapper,
  GATE_EXIT=0 via PIPESTATUS): envelope
  `result-2896695-361289245.json` — outcome completed, returncode 0, workers
  1, 395.6 s, starvation_escape false; identical dot-grid 1821 passed + 5
  skipped = 1826, 0 failed / 0 errored, tree unchanged across the phase. The
  targeted-fallback and full runs produced the IDENTICAL outcome set ~6.5 h
  apart on the same tree — consumed here as a zero-cost determinism proof
  (rule 4).
- Static: ruff (pinned 0.15.22) clean over all 19 changed surfaces, rc=0.
- Digests (recomputation-verified via `hermes_conductor.validation_policy`
  from release `be15abcc2e…`): envelope digest
  `validation:v1:4fda5348…bbe5` == recompute(base=None); dispatch digest
  `validation:v1:ab9136…4bf1` == recompute(base=run-original
  `30de0067f9…`) — NOT base=current HEAD `c43d085121` (rule 3). Recomputed
  again BEFORE and AFTER this compound phase's edits (ROADMAP.md status flip +
  this log entry): both equalities still hold — the validation digest excludes
  the ledger/docs surfaces this phase touched, so the two envelopes above
  remain current at compound time. Nothing executable has changed since the
  full gate; supersede the envelopes only if a later phase edits executable
  surfaces.
- Zero fixes were needed in targeted/full: the implemented tree is exactly
  what was validated.

### Prevention rules established

1. **Grep the mechanism, not the finding's file list, before implementing.**
   rm-207's acceptance cited seven `operator_fabric.py` sites with ZERO
   `set_hermes_home_override`/`HERMES_PROFILE` occurrences at either base —
   the assess finding's site inventory was stale against the tree, and the
   real mutation sites were `operator_skill_resolution._profile_scope` and
   `operator_skills._call_skill_manager`. Before implementing any
   site-enumerating acceptance, re-derive the site list with a repo-wide grep
   of the mechanism name and record the correction in the ledger entry (as
   done here), so the next reader does not re-chase ghost sites.
2. **The collision scan belongs at dispatch time, not only at prioritization
   time.** The prioritize-phase sweep (~15:05Z 10-03) verified `token_store.py`
   dirty-NOWHERE; by implement dispatch (~02:49Z 10-04) the sibling's
   uncommitted batch sat on exactly that file. A clean prioritization scan
   proves nothing hours later under a concurrently-minting fleet: re-run the
   dirty-file sweep at dispatch, and when a collision appears, escalate and
   drop the duplicate (land-once) rather than merge two implementations of one
   acceptance.
3. **The validation digest's base is the run's original dispatch base, and it
   survives in-run rebases.** After this run ff'd `30de0067f9` → `c43d085121`,
   recomputing `validation_digest(HEAD)` did NOT reproduce the dispatch digest
   — only `validation_digest(<run-original base>)` did, while the gate
   envelope's own digest equals `recompute(base=None)` (its `digest_base:
   "unknown"` is the standalone-gate write, not tree drift; cycle-5 note,
   sharpened). Pass the base explicitly and take it from the work order, not
   from the current HEAD.
4. **A batch that touches `pyproject.toml` buys a free determinism proof.**
   The targeted runner's FULL_IMPACT_FILES escalation makes the targeted phase
   run the full suite, so targeted and full validate the same tree twice. When
   the two outcome sets are identical (here 1821P+5S twice, hours apart),
   record the equality as the determinism evidence instead of re-running for
   speed or doubt — a slow-but-green gate twice is a feature (extends cycle-4's
   toolchain note into a rule).
5. **Environmental failure triage: stash-reproduce first, then probe the
   interpreter.** `test_disabled_skill_rejected` failed in the repo `.venv`
   during implement; reproducing it identically at HEAD with the batch stashed
   proved it pre-existing, and it passed under the gate interpreter
   (`/home/agent/.local/bin/python`, which has httpx+httpx2 — the repo `.venv`
   has only httpx2, and the real-agent loader path needs httpx). Attribute an
   environmental failure only after both steps; record which interpreter
   makes it pass.
6. **Insert-only ledger mints survive a mandated ff via stash → ff-only →
   pop.** The run's uncommitted ROADMAP mint rode through the
   `30de0067f9` → `c43d085121` ff content-identical; the proof obligation is
   numstat against the NEW head (insert-only preserved, +14/0-; later compound
   edits kept it +16/0-). Do not hand-rebase a ledger patch when stash/ff/pop
   can carry it.

### Local toolchain notes (small, reusable)

- Gate envelopes live under `~/.hermes/local-validation-gate/results/`; the
  digest recomputation pattern is `sys.path.insert(release/src)` →
  `hermes_conductor.validation_policy.validation_digest(base, repo)` with the
  base passed EXPLICITLY (full 40-hex sha string; `None` reproduces the
  envelope's own digest, a short sha does neither).
- The two-interpreter split (gate `python` at `/home/agent/.local/bin/python`
  vs repo `.venv/bin/python`) changes httpx/httpx2 availability and therefore
  which tests skip vs run — name the interpreter whenever a skip count is
  cited (extends cycle-6 rule 4 with the httpx/httpx2 instance).
- Under fleet load the gate admitted workers=1 both times (load1≈18.8 at
  targeted); 355–396 s full suites are normal in that lane.
- Compound ran under an explicit no-test constraint: every validation fact
  above was consumed from the recorded phase envelopes, never re-executed.

### Context left for the next cycle

- **rm-207 awaits review + fold/commit** (this phase's prohibited set):
  uncommitted delta at compound = 4 M + 2 ?? — `ROADMAP.md` +16/0-,
  `operator_skill_resolution.py` +10/−9, `operator_skills.py` +41/−29,
  `pyproject.toml` +1/0, new `operator_profile_scope.py` (134 lines) and
  `test_operator_profile_isolation.py` (475 lines), plus compound's own
  `docs/maintenance-cycle-log.md` (this entry).
- **rm-086 tier-2 / rm-187 verification duty:** the land-once duplicate is
  committed at `65fb97510f` (`conductor/run-a0f8eb89b525`, pushed, not yet in
  `origin/master`). At integration, verify the 0600-from-first-byte acceptance
  against that batch and flip rm-086's tier-2 remainder satisfied — do not
  re-implement.
- **Fleet frontier (re-census before minting, live):** ids moved rm-207 → rm-216 at
  this compound's first sweep and → rm-227 MINUTES LATER at the final sweep —
  the frontier moved intra-phase while this entry was being written (observed
  holders: run-40adb5bd1fe8 uncommitted rm-214 ISO-vs-REAL windowing, rm-215
  upstream v0.13/v0.14 adoption gap, rm-216 ui_chat `last_active` key; plus
  rm-217..rm-227 appearing in sibling worktrees between sweeps). NEXT FREE =
  rm-228 as of the final sweep; the run ledger's 2026-10-03 "next free rm-208"
  note is superseded (a COMPOUND REFRESH annotation now says so in place).
  Live incident for cycle-6 rule 7: a census older than minutes is already
  stale — sweep, write, and re-verify the max immediately before the mint.
- **Cycle-log numbering:** unintegrated siblings hold Cycles 9–12; the next
  compound phase continues past 13 or folds at the landing gate.
- **Open pool from this cycle's prioritization (20-item table,
  `/tmp/c68637fc-scratch/prioritized-batch.md`, none selected besides the
  batch):** headline **rm-170** (P1, assess F01 — the landed rm-134
  allowed_hosts/allowed_origins guard is PROVEN-INSUFFICIENT: it wraps the
  inner mount only, the outer `/ui` mount stays unguarded; the extension needs
  a real-stack ASGI-layer regression, not a standalone mount), then rm-193
  (sys.path pollution + agent `hermes_state` shadowing), rm-174 (redaction
  fail-closed + TitleCase over-redaction), rm-171 (cron jobs.json locking +
  next_run_at), rm-172 (+rm-200 turn-lease atomicity), rm-183 (fleet POST
  unbounded read), rm-136 (+F28 schema/single-writer), rm-144 (finance
  request_id confinement), rm-175 (ROADMAP evidence-stub debt), rm-077
  (packaging asymmetry).
- **Watch items carried from research folds:** upstream PR #85 backup
  configurability adopt-vs-defer now has a reviewable patch (rm-147; cycle 8
  hardened the same shape as rm-192 — reconcile the two at review), MCP SDK
  2.3.0 lane (rm-048), OSV floor refresh starlette/cryptography/anyio
  (rm-173), py3.10 EOL floor decision (rm-169), `hermes_state.py:79` prong
  (rm-105/106).
- **Research negatives (scope discipline, re-verify before relying):** fork
  has 0 commits beyond `origin/master` except PR #85; codeo1io/hermes-gpt open
  issues = 0; uvicorn/pyyaml/croniter/packaging/mcp advisory-clean; no
  x-mcp-header/WithJsonSchema usage in-tree (SDK 2.3.0 registration
  strictness cannot break tool registration).

### Landing-gate duties

- Fold this run's +16/0- ROADMAP insert with the sibling ledger patches in
  mint order; flip rm-207 to landed once review passes; cite rm-196/rm-197 by
  TITLE (double-minted ids).
- Reconcile the cycle-log numbering (this Cycle 13 vs unintegrated sibling
  Cycles 9–12) and the frontier correction (rm-228 next free as of compound's
  final sweep; rm-217–rm-227 minted by siblings intra-phase).
- Supersede `result-1988489-359778946.json` / `result-2896695-361289245.json`
  only if a later phase edits executable surfaces (cycle-8 rule 6); the
  compound delta is ledger/docs-only and digest-excluded (verified by
  recomputation before and after).
