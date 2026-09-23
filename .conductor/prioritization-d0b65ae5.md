# Prioritization — run c1ef27c97ab2, cycle 1

Attempt d0b65ae5a34442248984a54d41a6ab87 · 2026-09-21
Inputs: ROADMAP.md (rm-001..rm-011), assess artifacts (attempt 9b7c49f7), research artifacts (attempt cd8d3146).
Scales: impact/strategic 1–5 (5 highest); risk 1–5 (5 riskiest); effort 1–5 (5 largest).

## Matrix

| item | summary | impact | risk | effort | deps | strategic | verdict |
|---|---|---|---|---|---|---|---|
| rm-003 | Fix 4 stale PKCE tests | 5 | 1 | 1 | none | 5 | **SELECT** |
| rm-004 | Remove 12 dead gitlinks + truthful record | 4 | 1 | 1 | none | 4 | **SELECT** |
| rm-007 | mcp 2.2.0 CI lane + metadata skip guard | 3 | 2 | 2 | rm-003 (green proof) | 4 | **SELECT** |
| rm-005 | CI fast-lane (<2min PR gate) | 4 | 3 | 2 | rm-003 (red base defeats it) | 4 | **SELECT** |
| rm-006 | Upstream v0.11.0 catch-up (Gemini Spark, Agent Card) | 5 | 4 | 4 | rm-003/4/5 (green CI to land on) | 5 | DEFER → next-cycle headline |
| rm-008 | Merge PRs #10/#11 | 3 | 1 | 1 | green CI + maintainer merges (outside delegate scope) | 3 | DEFER (auto-unblocks post-green) |
| rm-009 | PyPI drift guard | 2 | 1 | 2 | none | 3 | DEFER |
| rm-010 | Upstream shared fixes to asimons81 | 4 | 1 | 2 | rm-003 + rm-004 landed in fork | 4 | DEFER (follow-up after batch) |
| rm-011 | MCP-native subscriptions/listen | 3 | 3 | 4 | design decision (SDK2-only) | 3 | DEFER (design-first) |
| rm-002 | Web module test coverage ×14 | 3 | 2 | 4 | none | 2 | DEFER (large mechanical, non-blocking) |
| rm-001 | Complexity refactor ×21 | 3 | 3 | 5 | characterization tests first | 2 | DEFER |

## Selected batch — B1 "Green Suite & Clean Index"

**Scope:** rm-003 → rm-004 → rm-007 → rm-005, in that dependency order.

1. **rm-003** — update the 4 stale PKCE tests in `test_codex_pr63_remediation.py` to mint valid S256 challenges (tests-only; the fail-closed contract at oauth_auth.py:477-479 stays).
2. **rm-004** — `git rm --cached` the 12 unresolvable gitlinks (staged at the commit gate; commit message supersedes the inaccurate c1785b22e5 claim).
3. **rm-007** — skip-guard the package-metadata test; add mcp==2.2.0 matrix lane to ci.yml.
4. **rm-005** — restructure ci.yml per PR #6's measured pattern (PR gate <2min; full matrix on main + nightly; kill the 820s cache-save waste).

**Rationale**
- *Coherence:* every item restores a truthful green signal or removes an untruthful one — suite, index, CI shape. No product behavior changes; all AGENTS.md safety invariants untouched (no auth, policy, or transport changes).
- *Impact:* red master CI (2026-09-20) currently blocks PRs #6/#10/#11 and masked the v0.11.0 drift. B1 is the keystone: green CI re-enables every downstream item including next cycle's rm-006.
- *Risk:* minimal — tests-only edits, index-only removals, workflow-only restructure. Local verification possible without CI (pytest, git ls-files/submodule status, yaml lint).
- *Effort:* small diffs (PR #6 analog is +19/-13); completable end-to-end within this cycle's implement→commit gates.
- *Dependencies:* rm-003 precedes rm-005 (a fast-lane on a red base proves nothing); rm-007's lane proof rides the same CI fix.
- *Strategic value:* highest ratio in the set; also prepares rm-010 (the same fixes go upstream).

**Deferred with reasons** (see matrix): rm-006 needs its own merge+review cycle against conflicting oauth_auth.py/server.py — rushing it into this batch would compromise both; rm-008 requires maintainer-side PR merges; rm-009/011/002/001 are lower value-per-effort or externally sequenced.

**Acceptance carried into implement/commit gates** (from ROADMAP.md): pytest file + full suite green; `git ls-files -s | awk '$1==160000'` empty; `git submodule status` clean; workflow diff matches PR #6 targets; CI-run proof deferred to the ci/final_validation gates per prohibition list.
