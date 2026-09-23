# Fresh adversarial repository assessment — run a51c0f6cb5b04ea9855a3dc3aba88c78, cycle 1

Attempt ae925afb81c54271bef8e449968d0a2a · 2026-09-20 · worktree
`run-a51c0f6cb5b0-a51c0f6c` @ 54f826c0cd (origin/master f8ba2e7862 is +1 docs-only merge: ROADMAP.md).

Method: ce-review persona/severity conventions (P0–P3) applied to a whole-repo
assessment. Full local suite (1,436 collected): **1,426 passed, 5 skipped,
5 failed** (`python -m pytest -q`, /tmp/full_tests3.log). Cross-checked live CI
via read-only `gh` queries. Static adversarial sweep: shell/eval/pickle/bare-
except/yaml/datetime/md5/mutable-default greps (all clean), SQL interpolation
audit, secret-path redaction surface, subprocess argv confinement, packaging
completeness, docs-vs-code spot checks.

## Findings

### F1 — P1 (correctness/test; master CI red for 7 days)
`oauth_auth.py:477-479` (mandatory-PKCE fail-closed, from 26ed7b4c0d 2026-08-31)
vs `test_codex_pr63_remediation.py:356/510/791/818/970` (issue codes with
`code_challenge=""`, then expect a successful exchange with `code_verifier=""`).
Four tests fail deterministically: `test_revocation_rotates_authorization_code_key`
(:348), `test_post_revocation_fresh_exchange_persists` (:492),
`test_exchange_fails_loud_when_persistence_fails` (:812, "strict hook must have
been invoked" — exchange raises before persistence),
`test_startup_migration_preserves_positive_legacy_epoch` (:941). Introduced by
merge `cb8c6fed03` (2026-09-13) which brought the PKCE-mandatory batch under the
newer #64 tests without updating them. Live CI: master runs
35480822047 / 35458420959 / 90aaa… / cb8c6f… all `failure` (2026-09-13 → today),
failing in every matrix lane ("Run full test suite"). Operational impact:
`publish.yml` gates PyPI publish on `uses: ./.github/workflows/ci.yml`, so any
tag pushed today cannot publish. Production code is correct (HTTP authorize
enforces S256 at oauth_auth.py:982-997); the tests encode a stale contract.
Fix: rewrite the four fixtures to mint a real S256 challenge/verifier pair.

### F2 — P2 (reliability/security: audit log mis-located on POSIX, failures swallowed)
`operator_policy.py:46-47,772-783` — default audit path is Windows-only
(`~/AppData/Local/hermes/logs/…`); on POSIX it silently falls back to
`Path(__file__).parent/logs/…` (source dir, or **site-packages** for a pip
install). `audit_record` swallows all `OSError` (`operator_policy.py:874-878`,
"audit failure must never break a tool"), so a read-only POSIX install records
**nothing**, quietly — undermining the "every call is audited" invariant the
budget/mission modules state. `HERMES_HOME` is not consulted (unlike every other
stateful module). Docs document only the Windows path
(docs/operator-mode.md:435). Proof in this worktree: `logs/hermes_gpt_operator_
audit.jsonl` was created in the checkout root by the test run (gitignored via
`.gitignore:25`, i.e., acknowledged litter rather than a designed location).

### F3 — P2 (process/security: unprotected master accepts merges on red CI)
`gh api repos/codeo1io/hermes-gpt/branches/master/protection` → 404 "Branch
not protected". Combined with F1: four merges (#66, #67, #5, #7) landed on a
master whose CI was failing at the time. No required status checks, no required
reviews, on a repo whose product is a security-sensitive local MCP operator
surface. (Fleet/infra op, not a file change.)

### F4 — P2 (test reliability: CI-load-only failures guard security properties)
Run 35480822047 additionally failed, on single lanes only:
`test_codex_pr63_remediation.py::test_rotation_and_issuance_are_serialized`
(:1208, mcp==2.0.0 lane — "issued token unreadable after concurrent rotation";
guards the rotation-vs-issuance fencing security property) and
`test_operator_delegations.py::test_mission_completion_rejects_concurrent_
reconcile_authority_change[reconcile]` (:243, 3.10 lane — IndexError). Both
pass locally on rerun (delegations file 100% green solo). Either real races
surfaced only under self-hosted-runner load or load flakes; the rotation one in
particular deserves root-cause (not blanket retry) because its failure mode is
a credential encrypted under a discarded key.

### F5 — P3 (performance: unbounded append-only audit JSONL + O(n) reads)
No rotation/size cap exists for the audit log. `audit_tail`
(operator_policy.py:880-901) opens and JSON-parses the entire file per call,
materializing every record before slicing the last `limit`; `iter_audit_for_task`
(:903) streams all records; `operator_diagnostics.py:1305` and
`operator_fabric_view.py:523` also full-scan. Every tool call appends ≥1 record
(audit_record, operator_policy.py:794+), so read cost grows monotonically with
use. Local single-user tool → P3, but a reverse-read tail + retention cap is
cheap.

### F6 — P3 (reliability: session-jobs unbounded growth; watcher leak path)
`operator_session.py` — every `hermes_session_continue` writes
`session-jobs/{job}.json` + `{job}.txt` (full CLI output) and nothing ever
removes them (no retention/GC; only failure-path unlinks at :156/:193);
`hermes_session_job_status` runs `_reconcile` (:278-294) globbing the whole dir
on every call. Also `_watch` (:211-228): a non-TimeoutExpired exception from
`proc.wait` would skip the `_processes`/`_active_sessions` cleanup (the pops at
:221/:231 are after the try/finally), leaving the session permanently
"SESSION_BUSY" until process restart.

### F7 — P3 (test portability)
`test_mcp_compat.py:81 test_package_metadata_allows_both_sdk_families` reads
installed distribution metadata (`importlib.metadata.PackageNotFoundError`) and
fails in any non-installed checkout (this worktree, containers, bare clones)
instead of skipping. CI passes only because it installs `-e .[dev]` first.

### F8 — P3 (correctness, minor: float money in budget ledger)
`operator_mission_budget.py` stores `quota/spend/amount` as SQLite REAL and
Python floats (schema :96-115; `_envelope_status` exact `spend >= quota` at
:270-296; caps 1e12 at :62-64). For `usd`/`minutes` units, repeated increments
accumulate binary-float drift (0.1-style), so envelope-crossing decisions can
flip on epsilon. Integer micro-units or Decimal would make INV-8 exact.

### F9 — P3 (maintainability/architecture)
`server.py` is a 3,856-line module defining 153 `hermes_*` tool functions and
the registration/serve surface for 20+ sibling `operator_*` modules. The merged
tool count is CI-pinned (test_server.py, 137 tools at v0.10.0) which mitigates
drift, but the module is past comfortable single-review size; per-subsystem
registration modules would reduce merge collisions (already observable: PR #66
and #67 both rewired server.py).

### F10 — INFO (run scoping)
This worktree HEAD (54f826c0cd) is one merge behind origin/master (f8ba2e7862,
docs-only ROADMAP.md fleet sync, merged 2026-09-20). Fix phases should rebase
onto master first so ROADMAP maintenance doesn't conflict.

## Verified clean (fresh passes that found nothing)

- No `shell=True` in production code (only doc-comment mentions in
  operator_cron.py:15, operator_workspace.py:17, operator_policy.py:16); no
  `eval`/`exec`/`pickle.loads`/unsafe `yaml.load`; zero bare `except:`;
  zero naive `datetime.now()`; no md5/sha1; no mutable default args (greps,
  repo-wide, production files).
- Constant-time comparisons at every token/signature site
  (`hmac.compare_digest`: operator_fabric.py:1266, oauth_auth.py:307/391/479/
  848/1037/1058, operator_runners.py:1026).
- 0600/0700 perms on secret/token/job stores (token_store.py:129,
  operator_codex.py:56-60, operator_job_supervisor.py:71-107, …).
- f-string SQL only with literal identifiers (fabric_write_guard.py:31/36,
  operator_fabric_view.py:73) — no user input reaches interpolation.
- `mcp_compat.py` SDK2 port question: benign — serving uses
  `uvicorn.run(..., port=args.port)` (server.py:3744/3808), so the adapter
  dropping `port` on SDK 2 cannot mis-bind.
- Packaging: py-modules list complete vs root modules (only test_* excluded);
  no phantom entries. CI covers both MCP SDK families × py3.10-3.12, web build,
  PowerShell example parsing, wheel hygiene.
- `updater.py`: ff-only, dirty-worktree gate, default-branch gate, fixed argv,
  no shell. `authorize` endpoint enforces S256 (oauth_auth.py:982-997).
- Docs discipline strong: 33 docs/ files incl. v0.10 release notes + per-surface
  design docs; docs are CI-enforced (test_export_docs.py,
  test_secure_mcp_tunnel_docs.py); CHANGELOG/README honest about PyPI lag.

## Prohibited stages
None touched: no commit, push, PR, CI mutation, or final_validation. Remote
access was read-only (`gh run list/view/api`).
