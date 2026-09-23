# Independent review — cycle-1 batch "Restore verifiable truth + safety-evidence integrity"

Run a51c0f6cb5b04ea9855a3dc3aba88c78 · attempt b9ad1cde77094ab780b38cef799562cb · 2026-09-21
Scope: full uncommitted diff vs 54f826c0cd (11 files, +464/−55) plus compound artifacts
(ROADMAP.md status flips, docs/maintenance-cycle-log.md, docs/README.md link).
Method: ce-code-review report-only conventions (read-only; no source edits, no commit/push).

## Verdict

**approve_with_findings** — the batch is internally consistent, honestly compounded, and
independently green (full suite re-run below). No high/critical findings. Two medium
consistency/durability findings (F1, F3) sit closest to rm-004's own acceptance text and
are cheap fixes; none block the commit gate, but F1 should land before or immediately
after merge.

## Independently verified (not taken from prior-phase claims)

- **PKCE enforcement untouched and real.** `oauth_auth.py` is not in the diff. Exchange-side
  fail-closed at oauth_auth.py:473-479 (empty stored challenge → `invalid_grant`;
  `hmac.compare_digest(_s256(verifier), challenge)` + `_valid_pkce_verifier`), authorize-side
  S256 gate at oauth_auth.py:982-997. The new negative test
  `test_exchange_rejects_code_without_stored_challenge` (test_codex_pr63_remediation.py:859)
  constructs a challenge-less code via the state API (which the HTTP authorize gate would
  have refused) and asserts exchange fails closed with no tokens minted — it exercises
  exactly the defense-in-depth layer it claims. Module `_CODE_VERIFIER` is 64 chars of
  `[A-Za-z0-9._~-]`, valid RFC 7636 (43-128).
- **Tests re-run from scratch in this worktree:** targeted (5 files) → 228 passed in 17.36s;
  full `python -m pytest` → **1439 passed / 5 skipped / 0 failed** in 189.80s. Reconciles with
  implement's 1438/6: `hermes_gpt.egg-info` exists here so the rm-007 metadata test runs
  instead of skipping. Both configurations green.
- **New CI lanes de-risked by direct SDK inspection** (scratch venv, /tmp/mcpcheck):
  `mcp==1.28.1 → 2025-11-25`, `mcp==1.30.0 → 2025-11-25`, `mcp==2.0.0 → 2026-07-28`,
  `mcp==2.2.0 → 2026-07-28`. All four satisfy `test_sdk_protocol_revision_is_deliberate`
  on their respective lanes, so rm-009's "REMAINING: green lanes" gate is now de-risked to
  matrix-runtime concerns only.
- **ROADMAP flips are honest.** Schema re-validated: 14 items × 7 fields (id/track/priority/
  status/signals/acceptance/evidence), header + managed-footer intact, statuses 4 implemented /
  9 candidate / 1 deferred. rm-003/rm-004/rm-007/rm-009 are `implemented` (not done) with
  explicit REMAINING gates (green master CI; green new lanes + 2.1 behavior-change audit note).
- **ci.yml** parses (yaml.safe_load); new lanes use the existing include pattern.
- **Security boundaries on touched surfaces:** no new shell/eval/pickle/yaml-unsafe paths;
  audit-failure diagnostics store only truncated exception text (200 chars) — no secrets or
  raw prompts; secret-path rules untouched; `test_audit_log_does_not_include_full_prompt_or_content`
  still green. Subprocess argv and constant-time compares untouched by this diff.
- **Cluster separation holds:** cluster A files (test_codex_pr63_remediation.py,
  test_mcp_compat.py, test_mcp_sdk_migration.py, .github/workflows/ci.yml) and cluster B
  files (operator_policy.py, operator_diagnostics.py, their tests, docs/operator-mode.md)
  do not overlap; only compound artifacts (ROADMAP.md, maintenance-cycle-log.md, docs/README.md)
  span both, as expected.

## Findings

- **F1 · medium · operator_policy.py:817** — `_audit_candidate_paths` appends `logs/` to raw
  `HERMES_HOME` without `normalize_hermes_data_root`, unlike every other HERMES_HOME consumer
  (operator_oauth.py:28, operator_contract.py:96, operator_swarm.py:279,
  operator_mission_ledger.py:86, operator_mission_runtime.py:102, operator_live_events.py:76,
  operator_codex.py:41). Install-layout values (`…/hermes-agent`, `…/profiles/<p>`) put the
  audit log in a different tree than tokens/ledgers/contracts, and the rm-004 acceptance text
  itself names the "normalize_hermes_data_root pattern". Fix is 2 lines + a test case.
- **F2 · medium · operator_policy.py:55,843,1009 (consumer operator_fabric.py:1756)** —
  single-generation 5 MiB rotation bounds the evidence window for
  `iter_audit_for_task`, which feeds fabric forbidden-action signal collection and task
  reconciliation. Records older than two windows vanish silently → *missed* violation signals
  (false negatives), not just lost history; no fail-closed indicator, and the caps are
  hardcoded (no operator knob). Documented tradeoff, but the safety-evidence-integrity
  implication is not surfaced anywhere (doctor/audit_tail show nothing about rotation loss).
  Suggest a follow-up roadmap item: configurable cap and/or reconcile-time warning when the
  archive boundary falls inside a task's lifetime.
- **F3 · medium · operator_policy.py:796** — preference is computed only among candidates whose
  parent *exists*; a creatable-but-missing preferred dir loses to an existing lesser one. On a
  fresh POSIX host the audit log lands in the package dir while other state homes default to
  creatable `~/.hermes` (cf. operator_oauth.py:30-38), diverging on first run. Worse on
  upgrade: POSIX hosts whose audit history is in `<pkg>/logs/` (old fallback) silently switch
  to `~/.hermes/logs` once it exists — legacy audit evidence becomes unreadable
  (no migration or legacy-path read). docs/operator-mode.md:439 does disclose the exists-gate,
  but cycle-log prevention rule 2 ("POSIX hosts silently fell back to the package directory")
  is only partially fixed.
- **F4 · low · docs/maintenance-cycle-log.md:22** — names
  `test_authorize_rejects_empty_code_challenge`, which exists nowhere in the codebase; the
  actual added test is `test_exchange_rejects_code_without_stored_challenge`
  (test_codex_pr63_remediation.py:859). The same phantom name appears in the implement-phase
  evidence. Compound-artifact accuracy defect; the roadmap's own acceptance wording
  ("a new test asserts an empty-challenge code is always rejected at exchange") is accurate.
- **F5 · low · ROADMAP.md:31,35** — rm-003 title/acceptance say "4 stale tests" while its
  evidence line says "all five … re-bound". The fifth (`test_exchange_fails_loud_when_persistence_fails`)
  was previously passing *vacuously* (it accepts `invalid_grant`, which the empty-challenge
  gate raised before reaching the injected persistence failure) — worth stating explicitly,
  since it is exactly the "test expects success/placeholder credentials" symptom prevention
  rule 1 warns about, caught by luck of the rewrite rather than by a failing test.
- **F6 · low · test_mcp_compat.py:90** — the metadata assertion loop covers
  ("1.28.1","2.0.0","2.2.0") but CI now also pins `mcp==1.30.0` (ci.yml:44). Add "1.30.0"
  for lane/assertion parity.
- **F7 · low · CHANGELOG.md:3** — the maintained `## Unreleased` section has no entry for the
  user-visible audit-location resolution change, rotation behavior, and doctor
  `AUDIT_WRITE_FAILURES` WARN (repo rule: CHANGELOG when user-visible).
- **F8 · info · test_codex_pr63_remediation.py:27** — comment says "60 chars"; the verifier is
  64 chars. Valid either way; fix the comment when touching the file next.
- **F9 · info · operator_policy.py:59-64** — `_audit_write_failures` never resets (a long-lived
  server WARNs forever after one transient failure — arguably correct: lost evidence stays
  lost) and its `count += 1` is not under `_audit_lock` (benign undercount only).
- **F10 · info · operator_diagnostics.py:507-524** — when write failures are present the
  last-record check is skipped entirely (priority inversion). Deliberate; noting for the record.

## Recommended disposition

Ship the batch (commit gate) with F1 as a pre-merge or immediate post-merge fix (2 lines +
test); F3/F7 small follow-ups in the same window; F2 becomes a roadmap follow-up item
(extend rm-004 or new); F4-F6 are one-line doc/test corrections that can ride any commit.
None of the findings weaken a security boundary, contradict the product invariants, or
invalidate the compounded claims' substance.
