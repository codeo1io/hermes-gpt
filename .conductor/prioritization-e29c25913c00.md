# Prioritization — run e29c25913c00 (2026-09-23, cycle 1)

Pool: 29 open roadmap items (ROADMAP.md @ 4b958379d6 + uncommitted cycle-3 edits, ids rm-001..rm-046 minus implemented/dropped). Inputs: assess 00799971 (findings F1–F10, baseline 1486/5/0), research 7e40e0f7 (candidates C1–C7 + negative results), roadmap ed19196d (statuses reconciled).

Scoring: Impact = proven-defect severity × user breadth; Risk = shipping risk; Effort XS/S/M/L; Dep = external dependency. Selected-batch rule: worktree-implementable end-to-end this cycle, coherent review story, full-suite + targeted validation executable.

## Selected batch — B1 "SDK-1 execution truth & DCR hardening" (6 items, implement order)

| # | item | why now |
|---|------|---------|
| 1 | rm-036 SDK-1 lane on PR fast-lane (XS) | 5-line ci.yml change; makes the whole class CI-visible before the fixes land; guards every future PR |
| 2 | rm-037 loop-safety wrapper (M) | root fix for assess-F2: mcp_compat registration-time wrapper routes sync handlers to a worker thread ONLY when mcp<2 (version-checked at import) — baseline lane (2.2.0) executes byte-identical paths = zero regression risk on the validation lane |
| 3 | rm-035 asyncio.run fix (M) | assess-F1, P115: even with the wrapper, convert hermes_web_extract/hermes_vision_analyze to async def + to_thread so they are correct under BOTH execution models; enabled-path loop-harness regression test (fails pre-fix, passes post-fix) |
| 4 | rm-038 DCR hardening (M) | assess-F3: unauthenticated /oauth/register permanent-capacity bricking (persisted registry, no rate limit/TTL); per-source 429 + registered_at TTL eviction + comment fix + httpx data=→content= |
| 5 | rm-040 OAuth docs truthfulness (S) | same OAuth surface as rm-038; PKCE_MODE/DCR documented, gemini-spark "not advertised" made conditional |
| 6 | rm-041 CHANGELOG Unreleased (S) | AGENTS.md requires entries for user-visible change anyway; Unreleased covers this batch + the four 2026-09-22 deployed-line commits; version stays 0.11.0 (fork rides upstream tags; policy recorded) |

Coherence: one review story — "make the supported mcp 1.x lane actually work (and guarded), harden + document the OAuth DCR surface". Validation: full suite in CI shape (HERMES_HTTP_TEST=1, baseline interpreter mcp 2.2.0) baseline-delta-zero + NEW targeted SDK-1 harness tests run under mcp 1.28.1 (wheels at /tmp/mcp1281-00799971, unique-path isolated venv) + loop-harness repro from /tmp/assess-00799971-asyncioproof.py as the regression seed. Note: this batch makes CI lanes executable-surface changes; per KTD5 the review-fix turn must re-emit validation evidence.

## Excluded (with reason)

| item | reason |
|------|--------|
| rm-039 unstick PR #75, rm-043 rebase PRs #19/#20, rm-044 answer #74 | external GitHub actions (PR/comment classes) — not worktree-implementable; stewardship/shipping-gate scope; rm-044 also blocked on upstream contract |
| rm-042 publish.yml off self-hosted | needs PyPI trusted-publishing/OIDC + maintainer coordination; next cycle |
| rm-033 ruff 0.15 re-baseline | cycle-sized rule-set churn (524 findings); must not mix with defect fixes |
| rm-002 test coverage, rm-001 complexity refactor | legacy big-tent items; fresh proven defects outrank them; revisit when defect queue drains |
| rm-008 required CI checks | org/branch-protection settings — external to the worktree |
| rm-024 Python 3.13/EOL floor | decision window is at EOL (2026-10-31); next cycle is better timed; 3.13 lane can ride the same ci.yml touch if capacity remains |
| rm-028 skill resolution | gated on upstream issue #74 architecture-first contract (rm-044 dependency) |
| rm-042/045/046 small hygiene (tmpdir, docstring) | low priority; natural stretch items if batch lands early — declared out-of-batch otherwise |
| rm-005/006/010/011/012/013/015/019/020/022/025/014 | lower priority than batch per scores; unchanged rationale from earlier cycles |

## Scored pool (priority × recency of evidence)

115 rm-035 · 100 rm-036 · 95 rm-037 · 90 rm-038 · 85 rm-039* · 70 rm-040 · 68 rm-033* · 65 rm-043* · 60 rm-041 · 55 rm-042* · 50 rm-024 · 45 rm-044* · 35 rm-045 · 25 rm-046 · 100 rm-002 (legacy, low urgency per cycle-1 note) · 90 rm-001 (legacy) · 85 rm-008* · 70 rm-010 · 60 rm-005 · 55 rm-015 · 50 rm-006 · 45 rm-011 · 40 rm-025 · 38 rm-028* · 35 rm-012 · 30 rm-013 · 30 rm-019 · 25 rm-020 · 20 rm-014 · 15 rm-022. (* = external/stewardship or separate-cycle scope this cycle)
