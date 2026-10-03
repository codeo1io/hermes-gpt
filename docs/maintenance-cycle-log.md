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

## Cycle 4 — 2026-09-30: trustworthy-state hardening batch (campaign 12c24d07 cycle 1, run 041a92f6667d)

**Run:** 041a92f6667d4952a09bda225728236d (repository-maintenance campaign 12c24d07e02440efb0adc0e7c51d8992, cycle 1)
**Base:** 14530e3e79 (clean tree; integration of run e29c25913c00 — SDK-1 sync-tool offload, native-async web/vision tools, loop-safe Codex bridge)
**Batch:** rm-077 + rm-067-remainder + rm-078 + rm-046 + rm-080, selected by prioritize 34aa4fb0 over the full open ledger with sibling-branch interlocks mapped; stretch rm-079/rm-082 not reached.

**What landed (all pending commit gate — pre-review evidence):**
- **rm-077** — new shared `atomic_write.py` (`atomic_write_text`/`atomic_write_bytes` + `ensure_private_dir`/`staging_path`: unique pid+token staging created 0o600 via `O_CREAT|O_EXCL`, fsync of file and dir with Windows-tolerant guards, `os.replace`); `token_store.py` adopts it at all three secret writes and creates the secrets dir 0o700 at first write — the world-readable window and fixed-`.tmp` stranding path are gone. New dir-mode/file-mode/no-window tests in `test_token_store.py`.
- **rm-067-remainder** — all 12 ledger-listed fixed-`.tmp` sites converted to the shared helper, plus both `fabric_artifacts.py` streaming sites (:226/:597) discovered during adoption; `.env` read-modify-write serialized by `operator_config._EnvFileLock`; grep-verified zero fixed-name `.tmp` writes remain in non-test code. `operator_workspace._atomic_write_text` now delegates to the helper (duplicate implementation removed).
- **rm-078** — `mcp_compat` sync-tool offload now runs through an explicit `anyio.CapacityLimiter` sized by `HERMES_GPT_TOOL_THREAD_LIMIT` (default 40 = anyio's prior implicit default, zero behavior delta) with a rate-limited saturation warning; wiring/parse/warn-rate tests added. Deferred: admission-control queue timeout. *(2026-10-03 independent-review fix, attempt a71cb302: the wrapper had been scoped to the SDK-1 lane only, leaving the default SDK-2 lane on anyio's implicit limiter where the knob is unreachable — `HermesMCP.add_tool` now applies it on both majors, lazy limiter construction is lock-guarded against concurrent double-build, and the knob + backpressure behavior is documented in `docs/mcp-compatibility.md` and `docs/env-vars.md` with both-major coverage tests.)*
- **rm-046** — `test_package_docs.py` shipped-docs guard (wheel data-files ⊆ MANIFEST.in, no duplicate includes, explicit unshipped-allowlist) with `docs/runtime-checkout.md` pinned unshipped until its host-state hygiene is refreshed; MANIFEST.in completed (15 missing doc includes, 3 nonexistent includes corrected). *(2026-10-03 independent-review fix, attempt a71cb302: the recorded acceptance's link-target half landed — the guard now asserts every `docs/*.md` link reachable from `README.md`/`docs/README.md` ships or is an explicitly-rationaled unshipped entry (allowlist: runtime-checkout.md host provenance, solutions/README.md, maintenance-cycle-log.md) plus allowlist stale/phantom hygiene; `docs/vnext-capability-manifest-and-mission-ledger.md` joined data-files + MANIFEST.in, and a stray `include docs/releases.md` line was dropped — the ROADMAP's earlier "MANIFEST completed incl. docs/vnext-…" claim was wrong and is corrected in the rm-046 status.)*
- **rm-080** — `docs/env-vars.md`: 92 non-test `HERMES_GPT_*` knobs with AST-verified defaults and owning module; `test_env_vars_docs.py` pins doc↔code sync in both directions; registered in pyproject data-files, MANIFEST.in, and docs/README.md.

**Validation (pre-review):** targeted gate exit 0 over all 17 changed surfaces; full-suite gate exit 0 (`uv run python -m pytest -q -n 8` through `local_validation_gate.py`, admitted workers=2 under host load) — 1618 passed + 2 skipped, zero F/E marks; `ruff check .` clean.

**Lessons:**
1. **Stale `*.egg-info/SOURCES.txt` poisons in-place sdist builds.** Editing MANIFEST.in and running `python -m build` in-place leaves egg-info residue that silently re-adds removed files to every later sdist; it cost a long bisect during targeted tests (the failure reproduced even on a clean-HEAD tree until the residue was found). Remove `hermes_gpt.egg-info/` — or build from a clean copy — before asserting package contents. `tools/check_package_hygiene.py` builds in-place and shares this latent exposure; it should adopt a clean-copy build.
2. **The engine's impacted-tests gate catches packaging regressions the focused suites miss** — two real failures surfaced only there: `atomic_write` missing from `[tool.setuptools] py-modules` (unimportable in the installed wheel) and host-state hygiene docs entering the sdist.
3. **Env-knob audits need an AST pass, not grep.** Regex undercounts multi-line reads (38 names vs 90) and raw grep overcounts (96, including test-only); the AST pass is the authoritative 92.
4. **Emit before the envelope expires.** The first targeted_tests attempt completed all work but lost its phase_result to the 3600s delegate timeout after exhaustive bisect forensics. Validate, fix, emit — do not spend the clock proving what already passed.

**Next-cycle candidates (concrete, with context):**
- **rm-076 (compatibility 125)** — 3-way skill-resolution reconciliation: the fork's 324-line FS-projection resolver vs upstream master 42ec9f10ec's 585-line loader-probe rewrite (`skill_view(..., preprocess=False)` — never-execute invariant) vs the two unlanded sibling branches (`conductor/run-cbd4463370ee` grammar-parity slice, `conductor/run-edd9fb12b6a4` earlier canonical impl). Build the reconciliation matrix before adopting.
- **Adjudicate the unlanded `conductor/run-d4c4dc76f3b0` "Q3 repair pack"** (2026-09-13, 16 files: token_store env-wins key precedence + `_delete_keyring_key`, ui_security redaction shield, fleet reads, token rotation) — verified NOT in HEAD, disposition unrecorded; adopt-by-content vs supersession. rm-077's landed hunks deliberately stayed off its territory.
- **rm-079** — ruff dev-pin bump to `>=0.16,<0.17` (one line; 0.16.9 current at the 2026-09-30 probe).
- **rm-024** — Python 3.10 EOL was T-31d at cycle time; schedule the floor bump.
- **Narrow remainders** — `_ensure_operator_tmpdir` still sets process-global env from worker threads (rm-045 fold: scope to subprocess argv/env); the Windows tmpdir path; `docs/runtime-checkout.md` host-state refresh then de-allowlist.
