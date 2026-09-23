# Prioritization matrix — run fd2bc85ff599 (cycle 1, base c1785b22e5)

Attempt 87402e789e8c4636bd3d65c7e130e329, 2026-09-22. Inputs: assess db8d3755 (5 deterministic
failures, ruff-524/F821x5, setuptools-floor repro), research 9662e1e8 (upstream 5-commit v0.11.0
delta), roadmap 2e8ee50f (rm-026..rm-029, restored on disk this turn), sibling-branch states
(conductor/run-a51c0f6cb5b0, conductor/run-6d49d1e3979f @89865b1281, PR #12 @808de652c1 green CI),
fleet interlock (run 684b97865efc tracks rm-001/rm-002-class work).

Scores: Impact / Risk-if-deferred / Effort (S<M<L) / Deps (N=none) / Strategic. Select = this cycle.

## Matrix

| Item | Impact | Risk | Effort | Deps | Strategic | Verdict |
|---|---|---|---|---|---|---|
| Green baseline: PKCE re-bind (rm-003 content) | 10 | 9 | S | N | 10 | SELECT |
| Green baseline: mcp_compat skip guard (rm-007 content) | 7 | 6 | S | N | 7 | SELECT |
| Green baseline: token_store dead block (rm-016 content) | 6 | 5 | S | N | 6 | SELECT |
| Build floor setuptools>=77 (rm-027) | 7 | 5 | S | N | 6 | SELECT |
| pyyaml bound (rm-023 remainder) | 5 | 4 | S | N | 5 | SELECT (stretch) |
| Upstream v0.11.0 catch-up (rm-026) | 10 | 8 | L | green baseline | 10 | DEFER — next-cycle headline; #6550 forbids cramming with green-suite batch (conflict-heavy oauth_auth.py/server.py) |
| Lint-gate re-baseline ruff 0.15 (rm-028) | 6 | 4 | M | sibling rm-017 merged | 6 | DEFER — needs committed [tool.ruff] baseline + rule-set decision post-merge |
| Py3.13/3.14 CI lanes (rm-024) | 6 | 4 | S | CI runs (prohibited) | 6 | DEFER — acceptance requires green CI lanes |
| Branch protection (rm-008) | 6 | 4 | S | Conductor infra | 5 | DEFER — engine/owner call, not a worktree batch |
| Gitlinks x12 (rm-029) | 3 | 2 | M | N | 2 | DEFER — CI-neutral (submodules:false), hygiene |
| CI-load flake root-cause (rm-010) | 5 | 4 | M | N | 4 | DEFER — not reproducible serially this run |
| Session-jobs retention (rm-005) | 4 | 3 | M | N | 3 | DEFER |
| Audit retention config (rm-015) | 4 | 3 | M | rm-004 merged | 3 | DEFER |
| Money-math micro-units (rm-006) | 4 | 3 | M | N | 3 | DEFER |
| MCP Tasks mapping (rm-011) / MRTR (rm-012) | 5 | 2 | L | design note | 5 | DEFER — design-gated |
| server.py split (rm-013), topo-sort (rm-022) | 3 | 2 | M | N | 2 | DEFER |
| Lease semantics (rm-019), resume (rm-020) | 3 | 2 | S/M | N | 2 | DEFER |
| D3 hard-block live (rm-025) | 4 | 3 | M | flag plan | 4 | DEFER |
| subscriptions/listen (rm-014) | 2 | 1 | M | push consumer | 2 | DEFER (standing) |
| Complexity refactors (rm-001) / untested modules (rm-002) | 5 | 3 | L | N | 4 | DEFER — sibling run 684b97865efc track; avoid fleet duplication |

## Selected batch — B1 "Truthful Green Baseline"

1. **PKCE test re-bind** (adopt rm-003 content; validated impl exists on conductor/run-a51c0f6cb5b0,
   attempt b2f5ddda; fork-canonical supersede target is PR #12 head 808de652c1):
   test_codex_pr63_remediation.py defs :348/:492/:812/:941 mint real S256 challenge/verifier pairs;
   add a test asserting empty-challenge codes are always rejected at exchange (fail-closed contract
   stays, oauth_auth.py:477-480 untouched).
2. **Skip guard** (adopt rm-007 content): test_mcp_compat.py:81 skips with reason on
   importlib.metadata.PackageNotFoundError; still runs when installed.
3. **Dead-block deletion** (adopt rm-016 content): token_store.py:1097-1141 unreachable tail after
   :1095 return; removes F821 x5; no behavior change.
4. **Build floor** (rm-027): pyproject.toml build-system setuptools >=69 → >=77 (PEP 639 license
   string "MIT"); verified-repro failure at 69.5.1 is the before-state.
5. *(stretch)* **pyyaml bound**: `pyyaml>=6,<7` — last bare runtime dependency.

**Rationale**: (a) Impact — 5 deterministic failures poison every downstream gate's validation
signal; a truthful 0-failure baseline in CI's exact shape is the prerequisite the rm-026 catch-up
acceptance criterion cites. publish.yml is blocked on green. (b) Risk — tests + unreachable-code
deletion + build metadata only; zero runtime behavior change; two sibling implementations already
validated in two environments each (adopt by content). (c) Effort — small; single worktree; local
acceptance needs no CI run (ci prohibited this run). (d) Dependencies — none; explicitly excludes
rm-026 per standing rule (#6550) and rm-028/rm-024 which depend on unmerged sibling gates / CI.

**Acceptance / evidence expectations (for implement)**:
- `HERMES_HTTP_TEST=1 /home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest -q` → exit 0,
  0 FAILED (serial; baseline interpreter mcp 2.0.0/pytest 9.1.1).
- `ruff check --isolated --select F821 .` → 0 findings.
- setuptools==77.x venv: `prepare_metadata_for_build_wheel` succeeds (69.5.1 failure documented).
- Diff touches only: test_codex_pr63_remediation.py, test_mcp_compat.py, token_store.py (dead
  block), pyproject.toml (build floor + optional pyyaml bound); no other runtime surface.
