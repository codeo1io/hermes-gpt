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

## Cycle 5 — 2026-10-01 — "Close your own assess findings: OAuth loop, durable doctor signals, knob docs"

Run `0aa75ea44f934b47acd316c4f5882eb5` (repository-maintenance
`c027a743b2df415eb0c9da700b7435b3`, cycle 2) against worktree at `caf60018d2`
(run-0aa75ea44f93-0aa75ea4, branch conductor/run-0aa75ea44f93). Phases: assess →
research → roadmap → prioritize → stewardship → implement → targeted tests →
full tests → compound. All outcomes below are pre-review: the batch is
implemented and locally verified but uncommitted, awaiting the fold and commit
gates. Cycle 4's batch landed at `bb9c68fb`/`80bd0f524d`; this cycle's assess ran
adversarially against that landed state and selected what it missed. Two phases
arrived as 429 envelope re-deliveries whose prior on-disk work was audited and
adopted (assess spool 97dfe594 intact; implement tree audited line-by-line
against the stewardship contract and RED-proven via `git stash` of the source
files), not redone.

### What the cycle did

- **rm-092 (P115)** — closed the rm-076 remainder: the OAuth surface was the
  one remaining on-loop blocking lane (`BearerAuthMiddleware.__call__` — also
  the WS handshake path — `/oauth/token` exchanges, `register_client`'s
  persist hook; a fresh sqlite connection with busy_timeout=15000 per
  authenticated request). All offloaded via `asyncio.to_thread` per the
  rm-076 pattern; static-bearer compare stays on-loop (pure CPU). The
  durable-validation docstring was corrected, not gated: the
  no-in-memory-shortcut design is deliberate cluster revocation correctness.
  Two lock-contention regression tests hold the durable store lock in a
  background thread — both fail against the pre-fix code.
- **rm-093 (P65)** — made the ui_mount health signal durable: the rm-078
  failure record lived in a bounded `audit_tail(limit=50)` scan, so churn
  evicted it and rotation hid it forever (doctor false-PASS while the UI was
  down). Now a persistent `ui-mount-state.json` marker
  (`operator_policy` :1065-1143) is doctor's authority — `failed` written on
  mount failure, `healthy`/`disabled` written at boot clearing stale failure —
  with the audit-tail scan kept only for pre-marker servers' history and a
  `UI_MOUNT_CHECK_UNAVAILABLE` fallback. Four regression tests (churn,
  rotation, marker-without-audit, healthy/disabled states); churn + rotation
  were red pre-fix.
- **rm-094 (P50)** — documented the fleet/runner env knobs
  (`HERMES_GPT_FLEET_PEER_NAME/URL/VERSION`, `HERMES_GPT_HOST/PORT` fallback,
  `HERMES_GPT_PI_EXE/OMX_EXE/OPENCODE_EXE`) in `docs/operator-mode.md` with a
  README pointer, plus `test_env_knob_docs.py`: a drift guard scanning every
  shipped module for literal `HERMES_GPT_*` names, requiring each to be
  documented or on the explicit 20-entry reviewed `_UNDOCUMENTED_BACKLOG`
  (the backlog itself fails when it goes stale). Structural fix stays open as
  rm-088 (typed knob registry).

Verification (pre-review): every one of the 6 new regression tests proven red
pre-fix by stashing only the 4 source files; targeted
`run_repo_impacted_tests.py --mode fast --jobs 8` (50-file selection) exit 0,
1271 passed / 2 skipped in 63.29s (both skips identified and pre-existing:
Windows-only command, HERMES_HTTP_TEST smoke); full gate
(`local_validation_gate.py --shell-command 'python -m pytest -q'`) exit 0
(envelope result-983149-329885774.json; 1612 progress dots, 4 skip marks, zero
FAILED/ERROR lines); `ruff check .` clean; validation digest
`validation:v1:9729ae37…9c53c1` declared verbatim and re-derived
byte-identical after the full gate. 9 files (8 modified +588/−57 and the new
guard test), all uncommitted.

### Prevention rules established

1. **A landed "every X" fix needs a census pin.** rm-076's acceptance said
   EVERY blocking store call; the OAuth lane shipped green underneath it.
   Universality claims in acceptance criteria get a mechanical census
   (grep/import-graph over the claimed surface, ideally a guard test) — an
   example list is not evidence of completeness.
2. **Health evidence must be at least as durable as the condition it
   reports.** A signal derived from a bounded recent-records scan decays with
   ordinary traffic and dies at rotation. Health checks read persistent state
   or probe live, and their tests cover BOTH churn-eviction AND the rotation
   boundary — both were red pre-fix here.
3. **Docs drift is a defect class with a cheap guard.** Scan shipped modules
   for the knob namespace; require each name in docs or on a reviewed backlog
   that itself fails when stale (`test_env_knob_docs.py` is the pattern). The
   guard fires in both directions.
4. **A docstring is a claim.** Build the mechanism or fix the claim in the
   same change — a docstring implying a cache gate that never existed is how
   the next assessment misses the real path (here: the real defect was
   loop-blocking, solved by offload, with the design intent stated plainly).
5. **Audit-and-adopt beats redo for voided prior attempts.** RED-prove prior
   on-disk work via `git stash` of the source files only (the new tests must
   fail against pre-fix code) instead of discarding it. And write the
   phase_result JSON before the final message — the envelope can die while the
   work sits complete (three envelope failures this run).
6. **Sibling runs reimplement the same defect under different ids.** This
   cycle's rm-093 has an unlanded twin (run-a7e57044's rm-087
   UI_MOUNT_FAILURE_MARKER, same base); landing gates dedupe by defect
   content, not id, and the roadmap rider records the twin in place.

### Local toolchain notes (small, reusable)

- Counts recover only with `-o addopts=` — repo `addopts="-q"` stacks with a
  CLI `-q` into `-qq` and suppresses the summary line (reconfirmed at both
  validation gates; standing cycle-3 rule).
- The gate envelope's own digest carries `digest_base: 'unknown'` by
  construction; the fold-gate policy re-derivation over the tree is the
  authoritative identity check — identical digests across two dispatches
  prove the tree unchanged between them (zero-cost identity check, cycle-4
  note).

### Context left for the next cycle

- **Landing duties:** review target = the 9-file implement delta + the
  compound artifacts (ROADMAP riders/flips, CHANGELOG Unreleased bullets,
  this entry); render footer stays last. Land ONE ui_mount durable-marker
  implementation (this run's rm-093 `ui-mount-state.json` vs run-a7e57044's
  rm-087); reconcile run-b665941020's shutdown-bound batch whose server.py
  :3126 lifespan edit abuts this run's :3221-3231 marker hunks; renumber
  sibling rm-085..rm-115 blocks at integration.
- **Headliner unchanged:** upstream Autopilot (PR #82, tip f4151d972, 9
  commits) still unadopted; v0.13.0 still untagged (2026-09-30) — re-probe
  tags. rm-085 + rm-081 should land as ONE catch-up batch.
- **Suggested order:** rm-085/rm-081 catch-up → rm-086 drift probe (fourth
  consecutive hand-probe this week) → rm-088 typed knob registry (rm-094's
  guard + 20-entry backlog is its seed) → rm-087 backup/restore → rm-089
  metrics → rm-090 audit hash chain.
