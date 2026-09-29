# Prioritization — run b665941020024956b7fca47ce2b28813, repository-maintenance cycle 1 (2026-10-01)

Scope: the 14 cycle-5 candidates (rm-102..rm-115) minted by this run's research (spool 38da61c9) and roadmap (spool f6f49c5e, uncommitted ROADMAP.md block at HEAD caf60018d2), scored against the 12 assess findings (spool 3a6f12e0). Skill routing: router has no ce-prioritize; narrowest match **ce-plan** (fence `/tmp/b6659410-prioritize-fence.log`, both markers); `subagent` tool not installed → single in-thread pass, disclosed; no in-thread agreement counted as independent.

## Corrected same-defect contest map (fleet state, all first-hand 2026-10-01)

The roadmap block recorded 7 convergences with the maintenance-trio siblings. Two more exist, and one cross-family fact changes selection:

- **rm-106 ≡ 1a6beeba rm-097** ("Registry and bound for fire-and-forget cron dispatch, with completion audit", priority 88, in 1a6beeba's SELECTED batch) — missed by the roadmap audit; ui_ops.py:621, same defect class and acceptance shape.
- **rm-111 ≡ 0aa75ea44 rm-093** ("ui_mount doctor false-PASS: signal decays under churn and rotation") — ALREADY IMPLEMENTED in 0aa75ea44's unlanded worktree delta (operator_diagnostics.py + test_operator_diagnostics.py), and **a7e57044 (family ae18259f:cycle:2) carries a SECOND unlanded implementation** (its rm-087 durable failure marker, server.py:3121/3229 hunks).
- **rm-114's core (key-file write-before-chmod) is fixed in FOUR unlanded sibling deltas** (worktrees run-041a92f, run-3b48f76e, run-a7e57044, run-e13b1c0d — each swaps `tmp.write_bytes(key); os.chmod(0o600)` for an atomic-0o600 pattern; none covers the `-wal`/`-shm` sidecar half). A fifth implementation would compete at the landing gate for no fleet gain.
- Fleet-wide dirty-diff scan (28 worktrees): **no delta touches `ui_chat.py` or `hermes_state.py`** (rm-102 uncontested) and **no delta contains `timeout_graceful_shutdown`** (rm-105 uncontested); server.py dirt in run-a7e57044/run-e13b1c0d sits at :3121–:3229 (ui_mount marker), not the uvicorn sites :3802/:3866.
- Fresh probe this session: upstream tags still top out at v0.12.0 (**v0.13.0 still untagged**), PRs #83/#84/#85 still open → rm-103's gate remains closed.

## Matrix (priority = roadmap-assigned; contest and effort decide the batch)

| id | pri | impact | risk if unfixed | effort | dependencies | contest | verdict |
|---|---|---|---|---|---|---|---|
| rm-102 | 125 | HIGH: one-live-turn invariant lost for turns >300s (max_iterations=60 makes this routine); concurrent turns admitted | silent conversation corruption class | M | none; dead API hermes_state.py:309 already exists to wire | **none fleet-wide** | **SELECT (1)** |
| rm-103 | 95 | strategic (v0.13 Autopilot) | none until tag | L-M (58-file true merge) | v0.13.0 tag + #83/#84 land; #85 conflict on operator_workspace.py | gated; both siblings deferred | DEFER (gate shut, re-probed today) |
| rm-104 | 80 | P2 loop stall (rm-076 remainder) | 15s worst-case loop stall | S | none | **0aa75ea44 rm-092 IMPLEMENTED (unlanded)** | DEFER (owned) |
| rm-105 | 75 | MEDIUM: SIGTERM waits unbounded → SIGKILL skips lease release + audit flush | operator-host reliability | M | uvicorn>=0.30,<1 in range (verified) | **none fleet-wide** | **SELECT (2)** |
| rm-106 | 70 | MEDIUM: unbounded daemon dispatch + duplicate cron runs | resource + double-execution | M | none | 1a6beeba rm-097 SELECTED (implement order 095→096→097) | DEFER (claimed) |
| rm-107 | 65 | P2 threadpool starvation | 25s×40 poll stalls | S-M | none | 1a6beeba rm-096 SELECTED | DEFER (claimed) |
| rm-108 | 60 | P2 packaging brittleness | install breaks on mcp reshuffle | S | none | 1a6beeba rm-099 SELECTED | DEFER (claimed) |
| rm-109 | 55 | dated (3.10 EOL 2026-10-31) | unsupported floor | S (decision) | maintainer call (user-facing drop) | 1a6beeba rm-100 deferred; alias-fix slice lives in rm-110 | DEFER (decision item; revisit before 2026-10-31) |
| rm-110 | 50 | MEDIUM rescan-forever + 3.10 timeout kill | WS stream waste/kill | S | none | 1a6beeba rm-095 SELECTED (its implement order starts here) | DEFER (claimed) |
| rm-111 | 40 | MEDIUM doctor false-PASS | operators trust a dead signal | S | none | **two unlanded implementations** (0aa75ea44 rm-093; a7e57044 rm-087) | DEFER (owned ×2) |
| rm-112 | 35 | LOW docs gap (28/90 knobs) | security-adjacent knobs invisible | S | none | 0aa75ea44 rm-094 IMPLEMENTED (unlanded, test_env_knob_docs.py exists) | DEFER (owned) |
| rm-113 | 30 | MEDIUM assess-F3: authority-map labels v0.8.0 notes "current release record" vs version 0.12.0 | doc-truth violation on the doc-authority entry point | XS | none | none (041a92f's docs/README delta is an env-vars row, old head) | **SELECT (3)** |
| rm-114 | 28 | MEDIUM key-file umask window + WAL sidecars | short world-readable master-key window | S | none | **four unlanded implementations of the core**; sidecar half unclaimed | DEFER (contested; sidecar slice folds onto any in-flight fix at the gate) |
| rm-115 | 20 | DX: every cycle re-derives fork/upstream state by hand; mechanical trigger for rm-103 | duplicated probe cost per cycle | S (new file) | none (read-only git probing) | none | **SELECT (rider, 4)** |

## Selected batch: rm-102 + rm-105 + rm-113, rider rm-115

Implement order **102 → 105 → 113 → 115** (rider independent, droppable without touching the core trio).

Rationale:
1. **Highest uncontested impact.** rm-102 is the cycle's top-priority candidate (125.0, assess HIGH) and rm-105 is the top first-minted MEDIUM (75.0). Both came out of THIS run's fresh assess; no sibling anywhere holds them (fleet-wide dirty-diff scan, not just the trio).
2. **They are one coherent reliability story.** rm-102 keeps the turn lease alive during long turns; rm-105 makes shutdown bounded so the lease-release and audit-flush paths (ui_chat.py:596 finally) actually execute instead of dying to SIGKILL — today, every rm-102-style long turn that meets a restart releases nothing. rm-113 then removes the docs-authority lie the same assess flagged (F3), closing all 3 fresh assess findings' defects this cycle.
3. **Zero same-defect overlap with any sibling claim** (after the corrected 9-convergence map): the landing gate gets a batch it can fold without dedupe, and no run's in-flight work is duplicated — fleet throughput is maximized precisely by taking the uncontested top items.
4. **File friction minimized**: rm-102 (ui_chat.py, hermes_state.py, test_ui_chat.py) touches files no sibling delta holds; rm-105's server.py hunks (:3802/:3866 uvicorn sites + lifespan) do not overlap a7e57044's :3121–:3229 hunks; rm-113 is docs/README.md + maintenance-cycle-log; rm-115 is a new tools/ file.
5. **Effort fits one end-to-end implement cycle**: M + M + XS + S with focused lanes (test_ui_chat.py, test_server.py, docs checks) — the acceptance criteria in ROADMAP.md are already regression-test-shaped (red pre-fix / green post-fix).

Deferred queue (with reasons): rm-103 (gate shut — re-probed 2026-10-01: v0.13.0 untagged, #83/#84/#85 open), rm-104/rm-112 (implemented unlanded by 0aa75ea44), rm-111 (implemented unlanded twice), rm-106/rm-107/rm-108/rm-110 (claimed by 1a6beeba's selected batch, implement pending), rm-109 (user-facing decision, dated revisit before 2026-10-31; 1a6beeba deferred the same defect), rm-114 (four unlanded implementations; sidecar slice rides the gate fold).

Carry-forward corrections for later phases: the ROADMAP.md id-note's convergence list (7) should become 9 (add rm-106~rm-097, rm-111~rm-093) — recorded here, not edited into the roadmap phase's delta; landing gate dedupes on titles+signals anyway.
