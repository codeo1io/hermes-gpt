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
