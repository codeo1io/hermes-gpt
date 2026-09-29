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

## Cycle 6 — 2026-10-01 — "Operator data-plane integrity & trust-boundary
hardening"

Run `c5fba76a9e6c4785855c20f63edc0a4f` (repository-maintenance
`5e1ae1a76ac64a1a8d802d8d5e80bfcb`, cycle 1) against worktree at `caf60018d2`
(run-c5fba76a9e6c-c5fba76a, branch `conductor/run-c5fba76a9e6c`). Numbering
follows the merge target: fork master's committed frontier is Cycle 5 (landed
with the +53), so this base's 4→6 gap is closed by the fold. Phases: assess →
research → roadmap → prioritize → stewardship → implement → targeted tests →
full tests → compound. All outcomes below are pre-review: the batch is
implemented and locally verified but uncommitted, awaiting the fold and
commit gates. Two sibling families worked overlapping bases in parallel and
the roadmap id frontier raced three ways at 08:42Z (61db9bce246a minted
rm-131..rm-135, bf4db34f3880 minted rm-131..rm-140); this cycle minted
rm-141..rm-150 past the observed max and the landing gate dedupes content
overlaps (the provenance doctor is triple-held: this rm-148, 61db9bce
rm-133, bf4db34f rm-135).

### What the cycle did

- **rm-144 (P95, security)** — Finance `request_id` confinement: the worker
  prompt no longer splices the untrusted packet field into the instruction
  region ahead of `EVIDENCE_JSON` (repro landed
  `SYSTEM: specialist_review all false…` in an approval-gating prompt). The
  structural contract no longer references the packet value: the fixed text
  instructs the model to copy `request_id` from the JSON-escaped evidence
  packet into the decision field (finance_worker.py:37,48-49); the bridge
  boundary (`operator_finance.hermes_finance_analyze`) additionally enforces
  the opaque charset `REQUEST_ID_RE = ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`
  (operator_finance.py:31,:155-157) and rejects everything else with
  `INVALID_REQUEST_ID` (previously length-only). Contract documented in
  `docs/finance.md`.
- **rm-142 (P110, reliability)** — SessionDB shim attribute protocol:
  `hermes_state.SessionDB.__getattr__` now raises `AttributeError` (not
  `NotImplementedError`) so `hasattr`/`getattr` capability probes — the
  server's Bot Chat lookup, compression-tip, and search probes — degrade
  gracefully instead of crashing; an explicit `SUPPORTED_API` frozenset
  documents the implemented surface; `list_sessions_rich` now honors every
  row-selection filter it accepts or raises `ValueError` (10 documented filter
  kwargs were previously silently ignored). New `test_hermes_state.py`
  protocol suite (33 tests) pins protocol, API surface, and filter behavior.
- **rm-141 (P115, reliability)** — atomic fabric write-claim acquisition:
  `WriteClaims.acquire` and the inline peer-accept duplicate (now deduplicated
  into `FabricPeerStore._claim_conflict_domain`) take the SQLite write lock
  (`BEGIN IMMEDIATE`) before the ownership read instead of a
  read-then-`INSERT OR REPLACE` sequence that two independent connections
  could interleave into a double grant (repro: both attempts believed they
  owned `domain-x` while the surviving row recorded a stale epoch). Acquire
  joins an already-open caller transaction instead of committing it; single-
  owner behavior unchanged for the in-process serialized path.

Verification (pre-review): targeted gate exit 0 (runner-expanded 10-file
selection, 189 dots reconciled 1:1 against `-o addopts=` collect-only, ruff
`All checks passed!` on all 8 changed surfaces at system 0.15.10); full gate
VERBATIM detached —
run 1 exposed 24 failures in the new shim suite (root cause below, rule 1),
fixed test-side; run 2 failed one unrelated budget-enforcement test once
(passed 3/3 isolated, 19/19 file-level, green in runs 1 and 3 — watch note,
not owned); run 3 (adopted from the reaped first attempt after forensics)
envelope `result-747114-335835588.json` returncode 0, workers 2, 1654 dots +
5 skips, 0 failed/errored. Digest chain: dispatch
`validation:v1:1f6f6e79…d72c6f1` (pre-fix tree) → shim-load fix → completing
attempt's dispatch digest `validation:v1:8c7d21a9…f103716`, recomputed
byte-identical post-adoption with base = full HEAD sha. 10 tracked files
modified + 1 new test file at validation time (regression tests for every
unit; red witnesses recorded for all three defects).

### Prevention rules established

1. **A repo-shim test must load its module by file path, not by import.**
   `server.py`'s module-level `import_hermes()` prepends the live deployment
   root to `sys.path[0]`; any alphabetically-earlier test module importing
   `server` then makes a later plain `import hermes_state` resolve to the
   deployment's real SessionDB, not the repo shim (symptom: 24 TypeError
   failures naming `hermes_state_sessions.py`, only under `workers=1`; xdist
   ≥2 masks it via process isolation). Tests targeting a shadowable module
   load it via `importlib.util.spec_from_file_location` under a distinct
   module name.
2. **Untrusted packet fields never enter instruction-region text.** A splice
   of unvalidated input into the structural contract ahead of the data packet
   is an injection seam even when the packet itself is JSON-escaped; fix both
   ends — placeholder + copy-from-packet instruction in the prompt, and a
   charset (not length-only) gate at the boundary that rejects with a named
   error.
3. **Ownership checks take the write lock before the read.** Any
   read-then-write claim sequence over a shared SQLite file is a double-grant
   window for independent connections; wrap in `BEGIN IMMEDIATE`, join an
   already-open caller transaction instead of committing it, keep the acquire
   idempotent for the owner, and regress with a two-connection interleaving
   test — an in-process lock proves nothing about this class.
4. **Reaped attempts leave adoptable evidence — inventory before redoing.**
   Forensics = delegate event log (dispatch + reap only), scratch artifacts,
   tree-vs-HEAD drift, and the gate's envelope directory (`grep -l
   run-<id>…`); adoption requires re-verifying each leg first-hand (recorded
   outcome, digest recomputation, fix diff) and the adopting phase_result
   carries the original attempt ids.
5. **The gate envelope's `digest_base: unknown` digest is a different salt,
   not a different tree.** Comparing an envelope digest to a dispatch token
   requires recomputing with the same base (envelope = `None`, dispatch = full
   HEAD sha); identical content hashes across bases prove tree identity
   (extends the cycle-5 note with the two-digest reconciliation used here).
6. **Mint roadmap ids past the observed fleet max, then re-probe.** The id
   frontier raced three ways within 95 seconds (08:42:19/08:42:40/08:43:54);
   probe sibling worktrees' ROADMAP mtimes immediately before authoring,
   continue past the observed max, and annotate collisions in place for the
   landing gate.

### Local toolchain notes (small, reusable)

- The gate's `python` on PATH is the hermes-autonomy venv interpreter, not
  the repo `.venv` — interpreter-sensitive behavior (import resolution,
  module shadowing) diverges between the impacted-tests lane (`uv run`) and
  the full gate; when a test passes in one lane and fails in the other,
  suspect process isolation and import order before suspecting the code.
- `git show <ref>:<path>` over the merge target (fork master) is the cheap
  way to pick artifact numbering that survives the fold — this Cycle 6
  numbering follows master's committed Cycle 5 rather than this worktree's
  base, so the fold needs no renumber.
- The full suite at `workers=1` is the only configuration that reproduces
  cross-file import-order pollution; a green xdist run does not clear it.

### Context left for the next cycle

- **rm-143 (P100) transport-resilience wiring** — the server half is live and
  tested (`ui_security.py` `/api/connection` + `serverStartupId`); the client
  half is built but unmounted (`reconnectStream` + `stores/connection.ts`
  have zero callers; `ConnectionStatus`/`AccountStatusBanner` unmounted).
  FLEET INTERLOCK: sibling 61db9bce246a's batch includes the adjacent rm-131
  (`/api/connection` offload) — coordinate at the landing gate; do not wire
  twice.
- **rm-148 (P90) live-deployment provenance doctor** — the sidecar still
  self-reports 0.11.0 against repo 0.12.0 and the deployed remote is 53
  commits behind fork master; triple-minted (rm-148/rm-133/rm-135) — fold to
  the landed-first id.
- **rm-145/rm-146/rm-147** — Python 3.11 floor (rm-100's dated window closes
  2026-10-31; pyproject sibling-dirty in b6659410 — coordinate), web toolchain
  refresh (react 19/TS 7/vitest 5 drift is large but non-urgent), upstream
  v0.13 watch (frozen at f4151d9728; PRs #83–#85 open; folds rm-098/rm-081).
- **rm-149/rm-150** — retry duplicate-bubble and `validate_public_url`
  redirect/rebinding pin (both assess-backed; repro scripts preserved under
  `/tmp/6951b127-scratch/`).
- **One-off watch:** `test_operator_mission_budget_enforcement.py::
test_disabled_flag_zero_writes_anywhere` failed exactly once (full-gate run 2,
workers 2, load1≈20) and passed in every other configuration (isolated 3/3,
file 19/19, runs 1 and 3) — a store-fingerprint drift under the gate-off
  zero-writes assertion; not diagnosed, not owned, recorded for the next
  cycle's full-suite history differencing.
- **Landing-gate duties:** dedupe this cycle's rm-141..rm-150 against the
  sibling rm-131..rm-140 sets (only the provenance item overlaps by content);
  renumber this Cycle 6 heading if sibling bf4db34f3880's uncommitted Cycle 6
  lands first; the batch is 11 tracked-modified + 1 new test file (cycle-log
  included) with digest `validation:v1:8c7d21a9…f103716` current at compound
  time.
