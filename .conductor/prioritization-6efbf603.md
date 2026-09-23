# Prioritization — run 6efbf603 cycle 1 (2026-09-22)

Scope: unresolved roadmap items at HEAD 5765b571b2 (cycle-3 block rm-032..rm-040 + legacy candidates) and assess findings. Topology constraint that shapes this selection: the run branch base 5765b571b2 PREDATES the 5-commit origin/master convergence — the cron.jobs defect (operator_cron.py:981 at tip 4b958379d6) and the OAuth DCR knobs exist only on master. Implement phases may not merge/commit; repairs targeting master-only code must be delivered as validated patches for the commit gate.

## Scores (impact 1-10 / urgency / effort / risk / dependency)

| item | impact | urgency | effort | risk | depends on | verdict |
|---|---|---|---|---|---|---|
| rm-032 re-green master (cron.jobs import) | 10 | 10 (all 9 CI lanes red; blocks PR #19/#20, upstream #75, any release) | M | low (additive; upstream raw-string contract verified; repro proven both directions in assess) | none — everything depends on IT | **SELECT (head)** |
| rm-033a pyyaml CVE floor slice (>=6.0.3) | 7 (CVE-2026-31132; current bound admits 6.0.2) | high (security floor must not wait for PR #19's upstream dance) | S | very low (2 files) | none | **SELECT (slice)** |
| rm-038 branch protection on master | 8 (3 direct pushes landed onto red master today) | high | S but a repo-settings API action, not code | n/a | gh admin rights; belongs to the governance/commit gate | defer to gate |
| rm-034 OAuth knob docs + CHANGELOG repair | 6 | med | S-M | low | BLOCKED at base: knob code lives only on master tip | defer to post-merge |
| rm-035 [tool.ruff] config on 0.16 | 6 | med | M (524-finding re-baseline decision) | med (rule churn mid-re-green muddies the critical diff) | independent | defer next cycle (pair w/ rm-024 lanes) |
| rm-036 Skills-extension conformance | 5 | low-med | M | med | PR #20 merge + upstream #74 | defer |
| rm-037 peer_main dedupe + peer CLI tests | 4 | low | S-M | low | independent | defer |
| rm-039 npm caching + stale CI comments | 3 | low | S | low | none | defer |
| rm-040 vercel.json reconciliation | 2 | low | S | low | none | defer |
| legacy: rm-024 lanes, rm-010 flake, rm-011/012 MCP ext, rm-013, rm-019/020/022/025 | 2-5 | low | M+ | var | green master | unchanged, outranked |

## Selected batch B1 — "Re-Green Master: cron runtime repair + pyyaml CVE floor"

**rm-032 (full)** + **rm-033a (floor slice only)**.

### Why this batch
- Coherent: one emergency unblocker + one tiny security floor; zero interaction between them; both merge-trivial; combined effort fits a cycle and reviews as one diff.
- rm-032 is the gate for every other item in the file (PR #19/#20 landing, upstream PR #75 revival, rm-034 docs, releases). No other selection can stack until master is green.
- rm-033a cannot ride PR #19 safely (upstream #75 is blocked with zero CI runs; landing date uncontrolled) yet the admitted-vulnerable range is live NOW. Slice stops at pyproject+CHANGELOG to avoid duplicating PR #19's file set (requirements*.txt deletion stays gate-side with PR #19).

### rm-032 implementation shape (for the implement phase)
- Defect is master-only → deliver (1) a repo guard test in the run branch (repo-wide scan failing on any `from cron` / private-runtime import; passes at base; permanent recurrence prevention); (2) the repair as `.conductor/patches/rm-032-cron-repair.patch`: drop the cron.jobs import, persist upstream-compatible RAW `schedule`/`schedule_display` strings (upstream contract verified via git show upstream/master:operator_cron.py — do NOT port the private structured-dict schema); (3) proof by applying the patch in a DETACHED temp worktree at 4b958379d6 with the cron module unimportable (the exact CI condition): full test_operator_cron.py green incl. the 5 named cron-create tests.
- Validation shape: baseline interpreter, serial, HERMES_HTTP_TEST=1 (project rule); base full suite must remain green (batch adds no regressions).

### rm-033a implementation shape
- pyproject.toml:20 `pyyaml>=6,<7` → `pyyaml>=6.0.3,<7`; CHANGELOG Unreleased CVE-2026-31132 entry. No other files.

### Explicitly deferred (rationale above)
rm-038 (gate-side governance: branch protection via gh api at/after the commit gate), rm-034 (post-merge, once the knobs exist on the landed line), rm-035+rm-024 (next cycle pair), rm-036 (PR #20 dependent), rm-037/039/040 (hygiene), all legacy candidates.

### Gate-time companion actions (not batch items, recorded so they are not lost)
- Set master branch protection (rm-038/rm-008) immediately after re-green.
- Land fork PR #19 on the repaired master; rebase upstream PR #75; verify upstream runs by head_sha.
- Reconcile duplicated rm-026..029 ids at merge (roadmap note).
