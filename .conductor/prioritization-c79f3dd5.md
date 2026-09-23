# Prioritization — run 684b97865efc, cycle 1 (attempt c79f3dd5)

Scope: unresolved roadmap items (ROADMAP.md rm-001..rm-031 as extended this cycle) + this run's assess findings. Criteria: impact × risk ÷ effort; dependency-free; completable end-to-end in ONE cycle (implement → tests → review → retest); no content collision with pending sibling PRs (#12 rm-003/004/005/007, #13 rm-016/017/021/023 — both verified open 2026-09-22).

## Disposition of all open items

| id | pri | status | disposition | reason |
|----|-----|--------|-------------|--------|
| rm-026 | 110 | candidate | DEFER (next-cycle headline) | highest value but conflict-heavy exactly where PRs #12/#13 live (oauth_auth.py/server.py/token_store.py); needs siblings merged first for reconcile-by-content |
| rm-002 | 100 | candidate | defer | 14 web test modules — large, not cycle-sized |
| rm-001 | 90 | candidate | defer | 21 complexity refactors — large, characterization-test-heavy |
| rm-008 | 85 | candidate | Conductor gate | branch protection = admin/merge-gate decision, not implementable here |
| rm-010 | 70 | candidate | defer | root-causing CI-load flakes needs 10 consecutive CI runs (CI outside executable scope) |
| rm-005 | 60 | candidate | defer (next-cycle candidate) | independent + valuable, but medium effort and signals not independently re-verified by this run's assess |
| rm-015 | 55 | candidate | defer | operator_policy.py region already reshaped by rm-004 in PR #12 — conflict risk |
| rm-024 | 50 | candidate | defer | acceptance needs green 3.13 CI matrix runs; ci.yml hotspot of both sibling PRs |
| rm-027 | 55 | candidate | **SELECT** | small: pyproject bound; finishes the dep-bounding series #13 started (uvicorn) |
| rm-011 | 45 | candidate | defer | design-gated on SDK probe both families |
| rm-029 | 42 | candidate | **SELECT** | small-medium: sentinel + test + docs; fixes documented-guarantee violation, zero sibling overlap (updater.py untouched by #12/#13) |
| rm-028 | 38 | candidate | defer | hard dependency on rm-026 |
| rm-012 | 35 | candidate | defer | design-note-first, opt-in pilot — next cycle |
| rm-030 | 48 | candidate | **SELECT** | small: one immutable-SHA ref + rotation note; closes mutable public-workflow pin affecting every CI run incl. upstream PR runs |
| rm-013 | 30 | candidate | defer | server.py split — large mechanical refactor, merge-collision hotspot by definition |
| rm-019 | 30 | candidate | defer | design decision (wire vs remove) |
| rm-020 | 25 | candidate | defer | transition-table semantics decision |
| rm-025 | 40 | candidate | defer | v0.10 controller slice — feature-sized, gate/flag design |
| rm-022 | 15 | candidate | defer | low value |
| rm-031 | 12 | candidate | **SELECT** | trivial: remove unused dompurify/@types/dompurify; zero sibling overlap (web/ untouched by both PRs) |
| rm-003/004/007/009/016/017/021/023 | — | implemented (pending merge, PRs #12/#13/a51c) | adopt-by-content | re-implementing would collide; reconciliation is Conductor's merge-gate call |
| rm-018 | — | dropped | closed | blocked by design contract (see item) |
| rm-014 | 20 | deferred | closed until trigger | no push consumer exists |

## Selected batch — cycle 1 "Verified-Fresh Hygiene" (B1)

**rm-029 + rm-030 + rm-027 + rm-031**, implement order by ascending risk: rm-027 → rm-030 → rm-031 → rm-029.

Rationale:
1. **All four are evidence-fresh from THIS run's assess** (not inherited signals): updater.py:49-58/203-206 vs docs/updating.md:19-26; ci.yml:22 mutable @main of public unprotection codeo1io/.github (gh api verified); pyproject pyyaml unbounded (last bare runtime dep after #13's uvicorn); web/package.json:15,28 unused dompurify.
2. **Coherent theme**: supply-chain integrity (rm-030) + updater correctness (rm-029) + packaging/dependency hygiene (rm-027, rm-031) — no scope bleed into the sibling-conflict zone (oauth/server/token_store/audit-policy).
3. **Cycle-sized**: combined effort ≈ one implement session + targeted tests (rm-029 needs a foreign-repo fixture test; rm-027/030/031 are config/docs diffs with build validation). Re-baselining after each is cheap.
4. **Conflict risk bounded**: only pyproject.toml (deps list, adjacent line to #13's uvicorn bound) and ci.yml (line 22 region, disjoint from #12's lanes/#13's lint step) overlap sibling files, both trivially resolvable one-liners; updater.py and web/ are untouched by siblings.
5. **Deferred-with-reason**: rm-026 stays the strategic next-cycle headline once PRs #12/#13 merge (it supersedes the local PKCE repair path — re-implementing PKCE fixes now would be wasted/conflicting work).

Acceptance evidence expected at implement/review: pyproject diff + install-green; ci.yml SHA ref + rotation doc; grep-zero dompurify imports + web build green; updater unit test with foreign git-root fixture proving refusal + docs/updating.md alignment; full-suite serial baseline unchanged-or-better vs /tmp/assess-2bd3be46-fullsuite.log (5 known failures).
