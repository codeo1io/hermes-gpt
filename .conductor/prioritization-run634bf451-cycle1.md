# Prioritization — run 634bf4516c83, repository-maintenance cycle 1 (2026-09-21)

Scope: unresolved items rm-001..rm-033 in this worktree's ROADMAP.md (seeded from origin/conductor/run-6d49d1e3979f + this run's cycle-1 additions). Two standing constraints applied to every score:

- **C1 (sibling interlock):** rm-003/004/007/009/016/017/021/023 are implemented on unmerged sibling branches (conductor/run-a51c0f6cb5b0, conductor/run-6d49d1e3979f). Re-implementing here duplicates work and multiplies commit-gate conflicts; cross-branch reconciliation is Conductor's call at the merge gates. → excluded from batch selection.
- **C2 (CI availability):** the fork has Actions disabled and the upstream-PR CI path is not yet established for this lineage (zero attributable runs). Items whose acceptance requires observed green CI cannot close this cycle. → CI-dependent items deferred.

## Matrix (impact / risk-of-not-doing / effort / dependency / strategic value → verdict)

| id | impact | risk if deferred | effort | depends on | this cycle? | verdict |
|----|--------|------------------|--------|-----------|-------------|---------|
| rm-030 upstream v0.11.0 catch-up (115) | highest (security remediation + Gemini Spark + SDK range) | grows with every upstream release | L (conflict-heavy: oauth_auth.py, server.py, test_server pin) | none hard; collides with C1 siblings in same files | NO | designated NEXT-cycle headline (roadmap status says so); batching it with anything violates the green-suite/headline split |
| rm-031 spec lineage 2025-06-18 + SDK 2.3 lane (70) | med (stale docs + assertion red on 2.3 lane) | low near-term | M | acceptance needs green mcp==2.3.x CI lane (C2) | NO | defer to the rm-030 cycle where spec lineage lands naturally |
| rm-026 gitlinks + c1785b22e5 record (72) | med-high (broken --recurse-submodules clones; false commit-message record) | low motion | XS | none | **YES** | index hygiene, fully local verification |
| rm-027 shipped-docs drift + guard test (60) | med (installed users get a docs map pointing at unshipped files) | low | M | none | **YES** | packaging truthfulness, local test+build verification |
| rm-028 .gitignore '*.ps1' trap (55) | med (future example scripts silently untracked while data-files claims them) | low | XS | synergy with rm-027 guard test | **YES** | one-line fix + probe, same packaging theme |
| rm-032 pyyaml bound (58) | med (only bare runtime dep; 6.0.3 fixed CVE-2026-31132) | low | XS | rm-029 (where the bound lives) | **YES** | one-line bound + suite |
| rm-029 requirements.txt duplication (45) | med (dual declaration drift; requirements.txt is a strict subset of pyproject deps — corrected: no psutil there; psutil is an undeclared guarded optional import) | low | S | none | **YES** | audit done this phase: psutil is a guarded optional import (operator_workspace.py:172, operator_diagnostics.py:122) → removal path chosen; one live doc ref (docs/mcp-compatibility.md:88) |
| rm-024 Py3.13/3.14 lanes (50) | med (3.10 EOL 2026-10) | rising with EOL date | M | green CI matrix runs (C2) | NO | defer; local 3.13 evidence already recorded |
| rm-010 de-flake CI-load tests (70→deferred) | med | low | M | 10 consecutive green CI runs (C2) | NO | defer |
| rm-008 branch protection (85) | high | med | S | admin/Conductor action, not a code batch | NO | Conductor/operator-owned gate prerequisite |
| rm-005/006/015/019/020/022/025, rm-011/012/013/014, rm-001/002 | low-med | low | S–L | various/design-gated | NO | below batch cut line; unchanged from sibling cycles' ordering |
| rm-033 Gemini CLI profile (35) | med-long-term | low | M | rm-030 | NO | explicitly gated |

## Selected batch — B1 "Index & Packaging Truthfulness" (rm-029 → rm-032 → rm-026 → rm-028 → rm-027)

**Rationale (coherence + end-to-end completable):**
1. **One theme:** everything makes the *shipped artifact and the git index truthful* — users get the docs README promises (rm-027), new example scripts actually track (rm-028), the dependency set has one source of truth (rm-029) with the last bare dep bounded at the CVE-fixed floor (rm-032), and clones stop carrying 12 phantom submodules (rm-026).
2. **Locally completable despite C2:** every acceptance check is local — full suite on the baseline interpreter, new guard test, `git check-ignore` probe, `git ls-files -s | grep -c '^160000'`, `python -m build` + `twine check` + `tools/check_package_hygiene.py`. No CI-observed acceptance in the batch.
3. **Zero overlap with C1 siblings:** touches pyproject.toml, requirements.txt, .gitignore, README/docs data-files refs, a NEW guard test file, and the git index — none of the files the sibling branches rewrote (oauth_auth.py, token_store.py, test files, lint-wide sweep), minimizing commit-gate conflicts.
4. **Effort/risk:** 3×XS + 1×S + 1×M, all low-risk, no behavior changes to runtime code paths (psutil imports stay guarded; only their declaration moves). Total well inside one implement+validate+review cycle.
5. **Strategic sequencing:** leaves the designated headline rm-030 a clean, conflict-minimized field next cycle, and the rm-027 guard test permanently prevents the shipped-docs drift class from regressing.

**In-batch ordering (dependency-driven):** rm-029 first (decides where the pyyaml bound lives), rm-032 second (bound lands in the surviving file), rm-026 + rm-028 next (independent index/.gitignore fixes), rm-027 last (guard test then asserts the final shipped set of docs AND examples, absorbing rm-028's negation into its probes).

**Validation expectations for the implement phase:** new guard test green; `git check-ignore examples/<new>.example.ps1` exits 1; `git ls-files -s | grep -c '^160000'` == 0; gitlinks' empty dirs produce no untracked noise; `python -m build` + `twine check dist/*` + `tools/check_package_hygiene.py dist/*` green with runtime-checkout.md + vnext-capability-manifest-and-mission-ledger.md present in the dist docs set; full suite on baseline interpreter serial with the failure set identical to the 2026-09-21 baseline (4 stale-PKCE + mcp_compat env-dependent) unless a sibling item merges first; CHANGELOG entry for user-visible changes (requirements.txt removal, pyyaml bound, shipped docs).

## Explicitly not selected (with reason recorded for the fold gate)

- rm-030: headline next cycle (roadmap-recorded); conflict-heavy; C1 collision field.
- rm-031, rm-024, rm-010: acceptance requires observed CI (C2).
- rm-008: GitHub admin-side; Conductor-owned prerequisite.
- rm-003/004/007/009/016/017/021/023: sibling-implemented; adopt-by-content is Conductor's reconciliation, not this batch (C1).
- rm-033: gated on rm-030. rm-001/002/005/006/011–015/019/020/022/025: below cut line / design-gated.

## Cycle 1 outcome (post-implement, pre-review — 2026-09-22)

Batch B1 result: rm-029/032/026/028 COMPLETE (pending commit gate); rm-027 PARTIAL (open: data-files +2 docs, runtime-checkout.md re-label, shipped-docs guard test, CHANGELOG entries — gates the commit).
Validation (attempt ae8f85ab, baseline venv mcp 2.0.0, serial, HERMES_HTTP_TEST=1): targeted test_package_hygiene.py 48p/3s exit 0; full suite exactly 4 FAILED (inherited stale-PKCE, sibling rm-003) + 0 ERROR; zero NEW failures vs assess baseline (5 FAILED) — the 5th (test_mcp_compat.py:81 metadata) passed in-suite and solo, confirming env-state dependence per the cycle-1 watch-list. Log: /tmp/targeted-ae8f85ab-full.log.
Deprioritizations unchanged and confirmed correct: rm-030 headline intact; CI-dependent items still blocked (C2); sibling items (C1) untouched by B1 (zero file overlap held).
Roadmap statuses flipped in ROADMAP.md (cycle-1 outcome section + prevention rules 11-15 + next-cycle context additions, run 634bf4516c83).

DEFERRAL RECORD (review finding #5, 2026-09-22): the implement-phase dist validation listed here ("python -m build + twine check + check_package_hygiene with runtime-checkout.md + vnext-capability-manifest-and-mission-ledger.md in the dist docs set") was NOT run — partial rm-027 made it moot — and is explicitly deferred to the commit gate, after the rm-027 remainder lands.
REVIEW-FIX RECORD (attempt cf265a76, 2026-09-22): findings #1/#2 fixed (requirements-dev.txt deleted; README dev setup -> pip install -e ".[dev]"), #3 roadmap corrected, #4 CHANGELOG Unreleased entries landed, #5 deferral recorded. #6 engine-side only.
