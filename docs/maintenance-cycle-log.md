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

## 2026-09-30 — run e13b1c0d37ea (ebb00eda cycle 1) — "Fail-closed & durable on the shipped runtime"

Run `e13b1c0d37ea4d1e9ed018aebf1dc4b7` against worktree at merge `14530e3e79`
(fork run merges atop upstream v0.12.0 adoption). Cycle phases: assess → research →
roadmap → prioritize → stewardship → implement → targeted tests (×2) → full tests →
compound. All outcomes below are pre-review: implemented and locally verified, not
yet reviewed, merged, or CI-verified.

### What the cycle did

- **rm-077 (ToolError migration)** — `server.py` `clean_error` now raises the SDK's
  `ToolError` instead of plain `RuntimeError` across all 11 raise sites, restoring
  client-visible failure reasons on the resolved mcp 2.2.0 runtime (SDK 2.1.0 #3314
  stopped forwarding unexpected-handler text). The import is resolved in
  `mcp_compat` per SDK lane; a new `test_server_tool_error_client_path.py` drives a
  real stdio server + `ClientSession` on both lanes and asserts the reason survives
  the round trip. 7 old-contract tests migrated (6 disabled-gate + 1 straggler — see
  prevention rule 1).
- **rm-080 (budget preview fail-closed)** — `operator_controller._budget_would_pause`
  returns True (pause) on unreadable store/row and malformed `policy_json`/spend/quota,
  routing the L2 pass into `enforce_budget_breaker` → `BUDGET_ENFORCE_REJECTED`;
  no-budget-defined still returns False by design. 6 regression tests added.
- **rm-067 fixed-.tmp slice** — durability standard centralized as
  `operator_workspace._atomic_write_bytes` (unique-tmp + fsync-before-rename +
  pre-rename chmod) and ported across token_store (master key / rotation / AESGCM
  envelope), operator_swarm ×2, operator_config, operator_codex, operator_session,
  operator_runners, and codex_config ×2 (validation deliberately kept between write
  and rename there). `fabric_artifacts.py:226/:597` (content-addressed,
  digest-verified blobs) left as the recorded tail.
- **rm-082** — `oauth_auth.py:373` obfuscated `setattr` replaced by a plain typed
  assignment with a rationale comment.
- **Cycle meta** — fresh assess minted rm-076..rm-085 from live sources; prioritize
  selected B1 over rm-076 (reconciliation dependency); ROADMAP carries the post-batch
  refresh and status flips for all four landed items.

Verification (pre-review): impacted-targeted selection (47 files, `-n 8`) **1070
passed / 2 skipped**; full suite **1612 passed / 2 skipped / 0 failed** of 1614
(= assess baseline 1599 + 15 new); SDK-1 lane client-path green on mcp 1.30.0;
ruff clean throughout.

### Prevention rules established

1. **An error-contract migration sweeps every test, not the touched ones.** The
   implement battery missed `test_skill_discovery.py:69` — a suite asserting the old
   `RuntimeError` around a `clean_error`-wrapped path — because it only ran suites it
   knew it had touched. The engine's impacted-tests gate caught it. Rule: when
   changing a raised exception type, grep all of `test_*.py` for
   `pytest.raises(<OldType>)` and classify each hit as same-path (migrate) or
   different-path (leave), recording the audit.
2. **SDK-versioned imports live in `mcp_compat`, never at call sites.** `ToolError`
   is `mcp.server.mcpserver.exceptions` on SDK 2.x but `mcp.server.fastmcp.exceptions`
   on 1.x — and **neither lane exposes `mcp.server.exceptions.ToolError`**, so the
   "obvious" import fails on both. Rule: adopting any per-SDK API goes through the
   compat shim with a live probe on both CI lanes before the change lands.
3. **File persistence is centralized; a fixed staging name is a defect class.** Any
   new durable write must use `operator_workspace._atomic_write_text`/
   `_atomic_write_bytes` (unique-tmp so concurrent writers cannot clobber a shared
   `.tmp`, fsync so a crash cannot persist truncation, pre-rename chmod so secret
   files never appear world-readable). When a write needs validate-before-replace
   (codex_config), keep the validation between write and rename — uniqueness plus
   ordering, never a fixed name. Reviewers: grep for `'.tmp'` / `".tmp"` literals in
   write paths; `fabric_artifacts.py:226/:597` is the recorded open tail.
4. **Corruption fails toward the stricter gate, and "no budget" is a decision, not
   an error.** `_budget_would_pause` returning False on *malformed* budget data
   silently skipped the D3 breaker (assess F2); it now routes corruption into the
   enforcement envelope (`BUDGET_ENFORCE_REJECTED`), while a *defined-absent* budget
   stays False. Rule: for any policy/budget decision helper, distinguish
   "unreadable/malformed" (fail toward enforcement) from "explicitly not configured"
   (honor the configuration), and test both plus the green path.
5. **Trust the gate script's own admission logic.** The local validation gate may
   downgrade `-n 8` to `-n 1` under load (banner records `admitted workers=1
   load1=21.65`); the exit code remains authoritative. Record the admitted command
   as the gate's internal decision — do not re-run to force parallelism. (Related,
   from the 2026-09-21 entry: `addopts = "-q"` means CLI `-q` is `-qq` and hides the
   summary line — count progress marks or run bare pytest for canonical counts.)

### Context left for the next cycle

- **rm-076 + rm-078 pairing is the leading next batch** (upstream skill-resolution
  hardening semantic-merged + the 2026-07-28 spec-delta review). rm-076 carries a
  3-way reconciliation interlock: unlanded branches `run-cbd4463370ee` (v0.12.0
  adoption + skill grammar parity) and `run-edd9fb12b6a4` (canonical
  skill-resolution impl + 442-line test) must fold with upstream `42ec9f10ec`.
- **Adjudicate `run-d4c4dc76f3b0`** (2026-09-13 "Q3 repair pack", 16 files,
  reviewed-ready, verified NOT in HEAD): token_store env-wins key precedence +
  `_delete_keyring_key` + token rotation — it overlaps B1's token_store writes, so
  adopt-by-content vs supersession must be decided before further token_store work.
- **CI-lifecycle cluster:** rm-083 (actions v7) + rm-084 (SDK-1 retirement decision);
  **rm-024 is time-critical** — Python 3.10 reaches EOL 2026-10 while `requires-python`
  stays `>=3.10`.
- **Open unstarted:** rm-079 (RFC 9728/8707, design-gated behind rm-072/rm-055),
  rm-081 (controller_plan O(history) scan), rm-085 (trove classifiers), rm-067's
  env-mutation/Windows remainders, `fabric_artifacts` staging.
- Review/merge/CI outcomes for B1 are deliberately absent here — the next cycle's
  assess carries them forward against the merged head.
