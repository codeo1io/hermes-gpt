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

## Cycle 5 — 2026-10-01 — "Idle-path survival + failure-path ownership"

Run `099e2bfc85074660ab5c0d1632636d24` (repository-maintenance `a473a4bd71834bacbe05498e3ca5f03f`, cycle 1) against worktree run-099e2bfc8507-099e2bfc at `caf60018d2`. Phases: assess → research → roadmap → prioritize → stewardship → implement → targeted tests → full tests → compound. All outcomes below are pre-review: the batch is implemented and locally verified but uncommitted, awaiting the fold and commit gates. Sibling campaign: 26 fleet worktrees share this base; the batch was selected against a fleet-wide dedupe scan so no sibling's unlanded hunk is duplicated (the cycle-4 rule-6 discipline).

### What the cycle did

- **rm-118 guard slice (P85, partial)** — the `/events/ws` idle poll now catches `(TimeoutError, asyncio.TimeoutError)`: on Python 3.10 `asyncio.wait_for` raises the still-distinct `asyncio.TimeoutError` (alias merged only in 3.11), so every idle browser client's live-events stream died on the first 0.5s poll; the poll bound moved to `_WS_IDLE_POLL_SECONDS`. Two new tests: a behavioral idle test (client silent through several poll cycles, control frames still served) and a source-contract test — the 3.11-visible red witness for the 3.10-only class split. Assess F1 / research R3; the keep-vs-bump floor DECISION remains owed by the 2026-10-31 EOL deadline (acceptance branch (a) not taken).
- **rm-122 (P25, full)** — `hermes_session_continue` no longer strands a session when the post-spawn metadata persist fails: `_save` is wrapped; on `(OSError, ValueError)` the child is terminated via the module's own `_terminate` idiom, the output file is closed and unlinked, the session key is released, and a redacted `SESSION_PERSIST_FAILED` envelope returns — previously an unwatched child with no timeout enforcement, a leaked fd, and permanent `SESSION_BUSY` until restart. Failure-injection regression test (monkeypatched `_save`), red pre-fix at exactly operator_session.py:194. Assess F5.
- **rm-119 test-tightening slice (P60, partial)** — the ui_mount visibility test now asserts exactly-once (`len(...) == 1`) for both the audit hits and the `ui_mount_failed` live events instead of presence-only; current emission was already exactly-once (pure hardening, no defect). The stateful doctor signal + churn-padding test remain open (assess F2+F3 core; convergences rm-093/rm-111 unlanded in siblings).
- **Evidence/discipline phases** — assess audited the prior run's 5 findings line-by-line at this HEAD (after three envelope-failure attempts; root cause = phase_result written to the wrong spool variant); fresh 2026-10-01 research (upstream 9-commit gap, v0.13 still untagged, PR #85 new, deps OSV-clean, py3.10 EOL 2026-10-31) became roadmap candidates rm-116..rm-123 minted past the fleet ceiling rm-115; prioritize deselected rm-117/rm-120/rm-123 as already-implemented-unlanded in siblings and deferred rm-116 (tag-gated) / rm-118's decision (dated); stewardship fixed unit boundaries before code.
- **Label-slip correction (recorded for the review gate)** — the prioritize→implement artifacts keyed the WS guard unit "rm-119" and the exactly-once rider "rm-121"; the roadmap block assigns the guard to rm-118 branch (b) and the exactly-once tightening to rm-119's acceptance, while rm-121 (upstream PR #85 watch) was never touched. Content-based re-mapping is unambiguous and is recorded on each item's dated update rider in ROADMAP.md.

Verification (pre-review; recorded outcomes, NOT re-run at compound): focused lanes 70 passed (15+6+49) at implement-green; the engine's impacted targeted lane 85 passed / 0 failed / 0 skipped over the 5 changed surfaces (attempt 06af0ce8); the engine's full gate (`local_validation_gate.py --shell-command 'python -m pytest -q'`, be98fe17 release path, run VERBATIM detached) exit 0: 1606 passed / 5 skipped / 0 failed / 0 errors = 1611 at tree digest `validation:v1:4f73ec68...ed77` (envelope result-2949895; adopted by the fold-cured retry b0dc73eb after a declaration-only rejection); ruff clean on all 5 changed surfaces. Batch = 5 files +122/-7, disjoint from every sibling's unlanded hunks; ROADMAP.md's cycle-5 block rides separately per stewardship's must_remain_separate.

### Prevention rules established

1. **Exception-class identity is interpreter-dependent.** `except TimeoutError:` around an `asyncio` primitive silently misses on Python 3.10, where `asyncio.TimeoutError` is still a distinct class (alias merged in 3.11). While `requires-python >=3.10`, every such catch must be the multi-catch `(TimeoutError, asyncio.TimeoutError)`, and a source-contract test is the only witness that survives on a 3.11+ dev host — behavioral idle tests cannot see the split.
2. **Own the child before the fallible persist.** Any spawn→register→persist sequence has a fallible middle; the failure path must fully unwind (terminate the child with the module's own idiom, close AND unlink the artifact, release the registry key) and return a typed envelope. Enforce with failure injection (monkeypatch the persist to raise) asserting the complete unwind — the orphan signature is unwatched child + permanent busy + leaked fd.
3. **Presence-only asserts pass vacuously on duplicates.** Once emission is believed single-shot, tighten signal tests to exactly-once counts (`len(hits) == 1` per channel); `assert hits` cannot detect double-emission regressions. (ui_mount visibility, this cycle.)
4. **Re-key rm-ids against the live roadmap block at every phase.** A one-id label slip in prioritize ("rm-119"=WS guard, "rider rm-121"=exactly-once) propagated through stewardship/implement/test evidence and would have mis-mapped at the review gate. Every phase that cites an rm-id re-greps the block for that id's title before writing it — the same re-grep-before-write discipline as roadmap edits.
5. **Validation declarations are byte-exact contracts.** The fold gate compares the evidence command string to the dispatch command verbatim: annotations appended into the field are a mismatch even when the run itself was verbatim and green. Evidence prose belongs in evidence_refs; and when a rejection is declaration-only and the tree digest still matches, adopt the existing green record instead of re-running (re-runs only re-expose load flakes).

### Local toolchain notes (small, reusable)

- The full gate ran VERBATIM detached (a setsid wrapper holding the command byte-for-byte) at fleet load1≈53 and self-admitted workers=2 in ~375s — a detached launch + PID poll beats any foreground ceiling; the wrapper's `.exit` file and the results-dir envelope are the durable proof.
- `python -m pytest -q` under this repo's pyproject addopts stacking prints no summary line — count the progress lines (dots + 's' marks per `[ NN%]` line) to recover pass/skip tallies; grep `FAILED|ERROR` for the zero-failure witness.
- `hermes_conductor.validation_policy.validation_digest(full HEAD sha, repo)` recompute is a zero-cost tree-identity check: it reproduces the dispatch digest byte-for-byte over the uncommitted tree, proving an earlier gate run covers the current tree exactly (the adopt-don't-rerun basis) — re-run at compound to prove doc-only edits did not disturb the validated executable tree.
- Count-bearing focused runs: `.venv/bin/python -m pytest -o addopts= <files>` (addopts stacking otherwise hides counts).

### Context left for the next cycle

- **rm-118 decision (dated, 2026-10-31):** the guard slice already landed this cycle (uncommitted); the recorded keep-3.10-vs-bump decision is still owed — if bump, requires-python + CI 3.10-lane edits + a 3.13 lane.
- **rm-119 remainder:** stateful ui_mount signal + churn-padding doctor test (convergences rm-093 uncommitted delta in run-0aa75ea44, rm-111 in run-b6659410 — fold at the gate).
- **rm-116 tag-gated upstream v0.13 adoption (P120):** 9-commit gap, tip f4151d9728, v0.13.0 STILL untagged, PRs #83/#84 open, #85 (config backups) new+unstable — re-probe at selection; convergences rm-085/rm-098/rm-103.
- **rm-117 / rm-123:** deselected as already-implemented-unlanded in siblings (1a6beeba's rm-099 pyproject deps; a7e57044's log-stat fix — which will edit the stale `:145` row in place while this cycle-5 entry appends after it) — verify at the landing gate rather than re-doing.
- **Flake candidate (unowned):** `test_operator_mission_budget_enforcement.py::test_gate_not_direct_refuses` failed once in a fleet full run under load (WAL-checkpoint residue suspected; refused path is zero-write by construction; 40/40 + 19/19 isolation passes) — harden the fingerprint snapshot or tolerate checkpoint-equivalent WAL moves.
- **Fleet id frontier:** sibling roadmaps have minted through rm-130 (unlanded); the next roadmap phase anywhere in this fleet must re-probe live and continue at rm-131+; this run's landing gate must reconcile the two numbering families (rm-116..rm-123 here vs rm-124..rm-130 in siblings) in the renumber pass that also owns the pre-existing duplicate rm-052..rm-057 headers.
- **Landing-gate duties:** fold the convergence sets named in the cycle-5 digest header; carry the label-slip correction (above) into the review mapping; the pre-existing duplicate rm-id headers still await the renumber pass.
