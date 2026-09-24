# Stewardship request — run 43fe028246d34268a1258c8505e27755 (cycle 1) · attempt a3c84a9531e24de99854c79a35453879 · 2026-09-23

(Batch B1 "OAuth Registration Trust", selected by the prioritize phase — see .conductor/prioritization-43fe0282.md. This document is the human-readable companion; the authoritative structure is the stewardship_request JSON in the phase_result.)

## Title
OAuth Registration Trust: dynamic-registration lifecycle hardening + authorize input hardening + RFC 9207 `iss` + OAuth knob documentation

## Summary
One coherent security-and-conformance change-unit on the OAuth surface of hermes-gpt, at master-tip code (HEAD 4b958379d6, branch conductor/run-43fe028246d3): (rm-048) make POST /oauth/register safe to expose — per-IP rate limiting, DynamicClient TTL + eviction wired into the existing cleanup() pass, an operator list/purge surface for the registry, redirect-URI re-validation on import, and a truthful comment at the metadata block (currently claims "rate-bounded" with no limiter) — closing the unauthenticated fill-up DoS (64 anonymous POSTs permanently brick ChatGPT-connector onboarding); (rm-049) guard /oauth/authorize client_id resolution so non-ASCII input yields invalid_request instead of a TypeError 500 (the token endpoint already has this guard); (rm-052) implement SEP-2468 (Final): RFC 9207 `iss` parameter in authorization success AND error redirects plus `authorization_response_iss_parameter_supported` in AS metadata; (rm-050) document HERMES_GPT_OAUTH_DCR / HERMES_GPT_OAUTH_PKCE_MODE (currently in zero .md files; DCR=0 is the required recipe for single-client Gemini Spark deployments) and fix the stale OAuthClient docstring. No dependency changes; no Git-topology decisions here.

## Repository candidate
- Primary change-unit root: this conductor worktree `/home/agent/.hermes/conductor-worktrees/hermes-gpt-c122f4fe79/run-43fe028246d3-43fe0282` (has the master-tip OAuth code the batch needs).
- Campaign repository: `/work/projects/hermes-gpt` (canonical checkout — sits on a fleet-owned branch; NOT to be used for this batch's dirty state).

## Surfaces (file:line, current at HEAD 4b958379d6)
- oauth_auth.py:38-39 — OAUTH_PKCE_MODE_ENV / OAUTH_DCR_ENV constants (rm-050 docs reference; no code change expected)
- oauth_auth.py:163 — stale OAuthClient docstring "no dynamic client registration" (rm-050 fix)
- oauth_auth.py:278-296 — client_for_id / compare_digest path (rm-049 guard feeds :1253 resolution)
- oauth_auth.py:297-347 — DynamicClient dataclass + OAuthConfig registry fields incl. max_dynamic_clients (rm-048 TTL/eviction fields)
- oauth_auth.py:371-376 — register fill-up 429 site (rm-048 rate limit + reclaim)
- oauth_auth.py:407-425 — import_dynamic_clients (rm-048 redirect re-validation via _registerable_redirect :318)
- oauth_auth.py:429-433 — cleanup() (rm-048 eviction hook)
- oauth_auth.py:1197-1213 — AS metadata dict: :1201 authorization_endpoint, :1209 registration_endpoint + the false "rate-bounded" comment at :1206; rm-052 adds authorization_response_iss_parameter_supported
- oauth_auth.py:1248-1313 — authorize(): :1251-1255 client resolution (rm-049), :1300-1313 redirect construction (rm-052 iss in success + error redirects)
- oauth_auth.py:1319+ — register_client() route (rm-048 limiter entry point)
- test_oauth_dynamic_registration.py — rm-048 tests (fill-up-then-reclaim, TTL expiry fails closed, purge round-trip, DCR=0 default unchanged)
- test_oauth_auth.py — rm-049 non-ASCII regression + rm-052 iss/metadata tests
- docs/gemini-spark.md:32+ ("## Configuration") — rm-050 env-knob documentation + DCR=0 recipe
- CHANGELOG.md — user-visible entries for rm-048/049/052

## Must remain separate (change-unit separation hints — NOT Git-topology decisions)
1. ["operator_cron.py + test_operator_cron.py + pyproject croniter dep (sibling run 6efbf603's 'Re-Green Master' patch)", "oauth_auth.py + test_oauth_*.py (this batch)"] — the cron repair is owned and already in flight by 6efbf603 (their rm-032); bundling would double-implement and conflict at the gate. This batch must not touch operator_cron.py or the croniter dependency line.
2. ["pyproject.toml pyyaml floor >=6.0.3 (6efbf603 rm-033a slice)", "this batch"] — this batch adds NO dependency changes; keep dep-file churn from the sibling slice out of the OAuth diff.
3. ["ROADMAP.md (this run's uncommitted roadmap extension, +74/-12, from the roadmap phase)", "the oauth_auth.py implementation diff"] — the dirty ROADMAP.md state is a prior phase's documentation artifact; preserve it, but do not fold it into the implementation change-unit (conductor decides where it lands).
4. ["requirements*.txt deletion / README install-path changes (rm-054 remainder, upstream PR #75 interlock)", "this batch"] — deferred packaging concern; different surface, separate gate-time decision.
5. [".conductor/prioritization-43fe0282.md and other .conductor/ artifacts", "any tracked-file change-unit"] — untracked conductor scratch stays out of the shipped diff.

## Notes for Conductor's inventory
- Dirty state in the batch worktree at dispatch: ROADMAP.md modified (+74/-12, sanctioned roadmap-phase deliverable) + untracked .conductor/ (progress ndjson, prioritization, this file). Nothing else.
- Fleet: e29c25913c00 worktree holds its own uncommitted ROADMAP extension (ids rm-035..rm-046 vs this run's rm-047..rm-054); 6efbf603 worktree holds the cron/pyyaml patch. No worktree shows oauth_auth.py drift — this batch is collision-free today.
- Validation contract for the implement phase: full suite serial, HERMES_HTTP_TEST=1, baseline interpreter /home/agent/.hermes/hermes-agent/venv/bin/python3; commit/push only at the gate.
