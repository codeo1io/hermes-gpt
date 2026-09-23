# Stewardship request — cycle-1 batch (attempt 0ee74381f)

Human-readable companion; authoritative JSON is in the delegate spool.

{
  "title": "hermes-gpt cycle-1: re-green CI trust signals (PKCE test contract, SDK coverage) + POSIX audit-evidence integrity",
  "summary": "Implement the prioritize-phase batch 'Restore verifiable truth + safety-evidence integrity' for codeo1io/hermes-gpt (fork of asimons81/hermes-gpt; upstream fully absorbed). Cluster A (anchor, test/CI-only): rm-003 \u2014 rewrite the four stale OAuth tests in test_codex_pr63_remediation.py (:348,492,812,941) that issue authorization codes with empty code_challenge and expect exchange success, contradicting the mandatory-PKCE fail-closed contract (oauth_auth.py:477-479); mint real S256 challenge/verifier pairs and add a new test asserting empty-challenge codes are always rejected \u2014 this re-greens master CI (red since 2026-09-13, run 35480822047) and unblocks the PyPI publish gate. rm-007 \u2014 make test_mcp_compat.py:81 skip with a clear reason when distribution metadata is absent (bare clones/worktrees) instead of failing. rm-009 \u2014 add explicit mcp==2.2.0 and mcp==1.30.0 pin lanes to .github/workflows/ci.yml (:24-37) and a protocol-revision assertion test in test_mcp_sdk_migration.py so SDK/spec drift surfaces deliberately. Cluster B (stretch, runtime code): rm-004 \u2014 route the POSIX audit log under HERMES_HOME/logs (operator_policy.py:46-47,772-783 currently Windows-only default with package-dir fallback), surface audit write failures via operator diagnostics (:874-878 currently swallows OSError \u2192 silent audit loss), add size-capped rotation with bounded reverse-read tail (:880-903 + consumers operator_diagnostics.py:1305, operator_fabric_view.py:523), update docs/operator-mode.md:435, tests in test_operator_policy.py. Runtime PKCE enforcement (oauth_auth.py) must NOT be weakened \u2014 the contract fix is test-side. Both repositories carry uncommitted ROADMAP.md and .conductor/ run telemetry that must be preserved and kept out of code change-units.",
  "repositories": [
    "/work/projects/hermes-gpt",
    "/home/agent/.hermes/conductor-worktrees/hermes-gpt-c122f4fe79/run-a51c0f6cb5b0-a51c0f6c"
  ],
  "surfaces": [
    "test_codex_pr63_remediation.py:348,492,812,941 (rewrite 4 stale PKCE-contract tests) + new empty-challenge-rejected test (rm-003)",
    "test_mcp_compat.py:81 test_package_metadata_allows_both_sdk_families (skip-instead-of-fail guard, rm-007)",
    ".github/workflows/ci.yml:24-37 (sdk matrix: add mcp==2.2.0, mcp==1.30.0 pin lanes, rm-009)",
    "test_mcp_sdk_migration.py:100-120 (add protocol-revision assertion next to existing 2026-07-28 _meta pins, rm-009)",
    "operator_policy.py:46-47,772-783 (audit_log_path: HERMES_HOME/logs on POSIX, no package-dir fallback) (rm-004)",
    "operator_policy.py:874-878 (audit_record: surface OSError via diagnostics counter instead of swallowing) (rm-004)",
    "operator_policy.py:880-903 (audit_tail + rotation: size-capped, bounded reverse read) (rm-004)",
    "operator_diagnostics.py:1305 (audit consumer: bounded tail + diagnostics surfacing) (rm-004)",
    "operator_fabric_view.py:523 (audit consumer: bounded read) (rm-004)",
    "docs/operator-mode.md:435 (document POSIX audit path under HERMES_HOME) (rm-004)",
    "test_operator_policy.py (audit home/failure-surfacing/rotation tests, near existing :370) (rm-004)"
  ],
  "must_remain_separate": [
    [
      "test_codex_pr63_remediation.py (rm-003 OAuth test contract)",
      "operator_policy.py + operator_diagnostics.py + operator_fabric_view.py + docs/operator-mode.md + test_operator_policy.py (rm-004 audit subsystem)"
    ],
    [
      ".github/workflows/ci.yml + test_mcp_sdk_migration.py (rm-009 SDK coverage)",
      "operator_policy.py (rm-004 runtime storage behavior)"
    ],
    [
      "ROADMAP.md (uncommitted roadmap-phase artifact, dirty in both repositories)",
      "all code surfaces of this batch"
    ],
    [
      "oauth_auth.py (runtime PKCE enforcement \u2014 verified correct, must not be weakened)",
      "test_codex_pr63_remediation.py test-side fix"
    ],
    [
      ".conductor/ run telemetry (untracked)",
      "code change-units"
    ]
  ]
}
