# Prioritization — run 43fe028246d34268a1258c8505e27755 (cycle 1) · attempt 040c817ad908434884d771195567253e · 2026-09-23

Scope: unresolved roadmap items at HEAD 4b958379d6 (on-disk ROADMAP.md, ids rm-001..rm-054 after this run's roadmap phase) + this run's assess findings. This worktree sits AT the master tip (has the deployed-line merges incl. the OAuth DCR knobs and the cron.jobs defect).

**Fleet constraint that shapes this selection:** sibling run 6efbf603 (worktree run-6efbf6037da9-6efbf603, base 5765b571b2 PREDATING the 5-commit master convergence) has already selected and is implementing batch B1 "Re-Green Master" = the cron runtime repair (their rm-032 ≡ my rm-047, delivered as a validated patch for the commit gate) + the pyyaml >=6.0.3 CVE-floor slice (their rm-033a). Their sheet explicitly DEFERS the OAuth-knob work to post-merge because "knob code lives only on master tip" — which is exactly where THIS run stands. Selecting the cron or pyyaml work here would duplicate a patch already in flight and force avoidable conflicts at both gates (operator_cron.py / pyproject.toml / CHANGELOG.md).

## Scores (impact 1-10 / urgency / effort / risk / dependency)

| item | impact | urgency | effort | risk | deps | verdict |
|---|---|---|---|---|---|---|
| rm-047 cron adopt #22 | 10 | 10 (master CI red, 5 consecutive runs; blocks every merge) | M | low (content already green on origin/master a93aeb0b1d) | none — everything depends on IT | **COVERED by sibling 6efbf603** (their rm-032, patch in flight). This run's gate ADOPTS that patch; do not re-implement. |
| rm-048 OAuth register lifecycle | 9 (unauth remote fill-up DoS bricks ChatGPT-connector onboarding — the 2026-09-06 outage class; false "rate-bounded" comment; 429-forever at cap 64, no TTL/eviction/purge) | 8 | M-H | medium (new lifecycle semantics; must not disturb DCR=0 single-client default) | none (code is at this HEAD) | **SELECT — head** |
| rm-049 authorize non-ASCII 500 | 6 (unauth 500 via TypeError in compare_digest; only remaining attacker-controlled hole) | 7 | S | low | none | **SELECT — rider** |
| rm-052 SEP-2468 `iss` | 7 (spec is FINAL; RFC 9207 issuer claim in authorize success+error redirects + `authorization_response_iss_parameter_supported` metadata flag — client-side redirect-URI confusion defense) | 6 | S-M | low | none | **SELECT — rider** |
| rm-050 OAuth env docs + docstring | 6 (HERMES_GPT_OAUTH_DCR / HERMES_GPT_OAUTH_PKCE_MODE in zero .md files; DCR=0 is required knowledge for Gemini Spark single-client deploys; stale "no dynamic client registration" docstring at oauth_auth.py:163) | 5 | S | low | lands with rm-048/052 behavior | **SELECT — docs rider** |
| rm-054 manifests + pyyaml floor | 6 | 6 | S-M | low | pyyaml floor slice TAKEN by 6efbf603 rm-033a; requirements*.txt deletion interlocks upstream PR #75 + PR #19 | **DEFER remainder to gate/packaging pass** |
| rm-051 macOS confinement roots | 4 | 3 | S | medium — unverifiable on Linux CI (behavioral claim about macOS exec) | needs Darwin verification story | DEFER |
| rm-053 CIMD strategic | 8 strategic | 4 | L | med | explicitly pending rm-048 (this batch keeps its slot-in open) | DEFER (post-rm-048 design note) |
| rm-033 [tool.ruff] config | 6 | 4 | M | med (rule churn muddies review diffs) | independent | DEFER next cycle, pair with rm-024 lanes (consistent w/ sibling's deferral) |
| rm-024 Py3.13 lanes / 3.10 EOL | 6 (EOL T-38 days) | 5 | M | low | needs CI runs (gate-side) | DEFER to gate |
| rm-028 skill resolution | 7 | 3 | L | med | upstream #74; Skills WG chartering | DEFER (track WG) |
| rm-008 branch protection | 8 | high | S (API action) | n/a | gh admin | gate-side governance (already routed there by 6efbf603) |
| rm-001 21 complexity refactors | 5 | 2 | H | high churn | characterization tests first | DEFER (long-standing deferral stands) |
| rm-002 web-UI test coverage (14 modules) | 5 | 3 | M-H | low | different subsystem; not coherent with this batch | DEFER |
| rm-005/006/010/011/012/013/015/019/020/022/025 legacy candidates | 3-6 | 2-4 | M-L | mixed | several superseded by landed work | not selected (lower value-density than B1) |

## Selected batch B1 — "OAuth Registration Trust"

**rm-048 (head) + rm-049 + rm-052 + rm-050 (docs rider)**, implemented in that order.

### Why this batch
- **Coherent:** one core file (oauth_auth.py) + its tests + one docs pass; reviews as a single security-themed diff; every member shares validation surface (test_operator_oauth.py + full suite).
- **Highest value-density available to THIS run:** the only two HIGH assess findings not already owned by a sibling (cron = 6efbf603's), plus a Final-status spec conformance win, plus the docs gap the research phase proved. Unauthenticated remote DoS + unauthenticated 500 + spec-issuer-parameter: all client-facing auth surface.
- **Unblocked & completable end-to-end this cycle:** all four need only code at this HEAD; no CI-run dependency (local validation per project rule; commit/push at the gate); combined effort M — fits implement → review → final_validation.
- **No fleet collision:** 6efbf603's base lacks the OAuth DCR code and their sheet defers their rm-034 docs item post-merge; no other sibling worktree shows oauth_auth.py changes. My rm-050 subsumes their deferred docs item — record at compound gate.
- **Strategic sequencing:** rm-048 keeps the CIMD slot open (rm-053 deferred on it), and its design note (acceptance) is where CIMD adoption gets decided.

### Implementation shape (for the implement phase)
1. rm-048: per-IP fixed-window/token-bucket rate limit on POST /oauth/register (in-process, no new deps); DynamicClient.created_at/expiry + cleanup() pruning + floor reclaim so the 64-cap cannot be bricked anonymously; operator list/purge surface for the registry; import_dynamic_clients re-validates _registerable_redirect; fix the false "rate-bounded" comment (oauth_auth.py:1206). Tests: fill-up-then-reclaim, TTL expiry fails closed at exchange, purge round-trip, DCR=0 default unchanged.
2. rm-049: encode/validate client_id before client_for_id on the authorize path (invalid_request redirect, not 500); regression test with non-ASCII client_id asserting 4xx/redirect+error.
3. rm-052: iss=<issuer> in authorize success AND error redirects (RFC 9207); authorization_response_iss_parameter_supported:true in AS metadata; tests pin both; CHANGELOG entry.
4. rm-050: docs (gemini-spark.md and/or operator-mode/oauth docs) for HERMES_GPT_OAUTH_DCR + HERMES_GPT_OAUTH_PKCE_MODE with the DCR=0 single-client recipe; fix OAuthClient docstring (oauth_auth.py:163).
- Validation: full suite serial, HERMES_HTTP_TEST=1, baseline interpreter (project rule); zero regressions; new tests green.

### Gate-time interlocks (recorded so they are not lost)
- ADOPT sibling 6efbf603's cron patch (their rm-032) at the commit gate rather than re-implementing rm-047; their pyyaml floor slice (rm-033a) covers the rm-054 floor component.
- rm-050 subsumes 6efbf603's deferred rm-034 docs item — reconcile at compound gate.
- Branch protection (rm-008) is a governance action for the gate, not this batch.
