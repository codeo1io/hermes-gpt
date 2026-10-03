---
title: "Session turn lease expires mid-turn, admitting a concurrent second turn"
category: ui-chat
date_discovered: 2026-10-01
date_resolved: 2026-10-03
status: resolved
related_commits: []
---

# Session turn lease expires mid-turn

## Symptom

A chat turn that runs longer than the lease TTL (300 s) silently loses the
session turn lease while it is still running. The next turn request can then
acquire a second lease, so two turns run concurrently against one session and
interleave their writes — the "one live turn per session" invariant is lost
with no error surfaced to either turn.

## Root cause

`ui_chat.py` acquired the lease with `ttl_seconds=300.0` but only released it
at turn completion — nothing renewed it. `hermes_state.SessionDB` already
exposed `refresh_session_turn_lease` (the renewal API), but it had **zero
callers** at discovery — the call-site probe
`grep -rn '\.refresh_session_turn_lease(' --include='*.py'` matched no line
(only the definition in `hermes_state.py` exists): a dead renewal API paired
with a live acquire API. Once the TTL
elapsed, the acquire-side expiry path treated the still-running turn's lease
as stale, so a second acquire succeeded.

## Detection

- Dead-renewal check: grep for a **call site**, not the bare name — the bare
  name also matches the definition in `hermes_state.py`, so its exit status
  proves nothing. Use `grep -rn '\.refresh_session_turn_lease(' --include='*.py'`
  (leading dot: method-call sites only). Zero matching lines means the
  renewal API is dead and the invariant loss is live.
- Recurrence probe: with a short lease TTL, a turn that outlives the TTL must
  still hold the lease (`test_ui_chat.py::
  test_turn_outliving_ttl_keeps_lease_and_releases_it` does exactly this with
  a 0.5 s TTL and a 0.8 s turn).
- At runtime, a lost lease logs
  `ui_chat: turn lease lost for session ...; aborting turn` — that line
  firing for a healthy turn means renewal lost a race with takeover/expiry.

## Fix procedure (applied 2026-10-03)

- The turn worker (`ui_chat.py::_run_turn`) starts a daemon renewal thread
  (`_run_lease_renewal`, thread name `ui-chat-lease-<session8>`) and stops and
  joins it in the `finally` block before releasing the lease.
- The renewal loop wakes at `TURN_LEASE_REFRESH_INTERVAL_S`
  (= `TURN_LEASE_TTL_S / 5`, i.e. 60 s — four missed renewals still leave
  headroom) and calls
  `db.refresh_session_turn_lease(session_id, holder, ttl_seconds=TURN_LEASE_TTL_S)`.
- Renewal semantics: `SessionDB.refresh_session_turn_lease` UPDATEs the row
  only where conversation and **holder** match and returns `rowcount > 0`.
  `False` therefore means the lease expired or was taken over → the loop logs
  the loss and routes to the existing cooperative abort path
  (`_request_turn_abort(turn, "turn_lease_lost")`: set `cancel_requested`,
  then `agent.interrupt(hard_cancel=True)`), so the turn closes on the normal
  path instead of running unbounded. A transient store error logs a warning
  and retries on the next interval — it does not abort the turn.
- Regression tests in `test_ui_chat.py`: renewal aborts on loss, tolerates a
  transient store error then aborts on loss, renews until stopped, the renewal
  interval is well under the TTL, and a turn outliving a short TTL keeps the
  lease and releases it.

The fix is the uncommitted cycle-5 delta at `caf60018d2` (repository-maintenance
cycle 1, run worktree; landing gate pending), hence `related_commits: []`.

### Limitation (recorded at review, 2026-10-03)

Bounded shutdown does **not** release an in-flight turn lease: the renewal
daemon threads die at process exit without running their `finally` blocks,
so a lease belonging to a turn interrupted by shutdown persists up to
TTL 300 s post-mortem, and recovery is the acquire-side stale-lease expiry.
This is the honest state of the fix — the claim "leases released at
shutdown" would be false. Shutdown-time lease release is a next-cycle
candidate.

## Prevention

- A TTL'd lease with no renewal caller is a defect, not an optimization: every
  new lease **acquire site** ships with its renewal path and loss semantics,
  plus a short-TTL regression test that proves a long holder keeps the lease.
- Any lease/lock API that can outlive its caller must have at least one live
  caller for each operation (acquire, renew, release) — a definition with zero
  callers is the smell that surfaced here.

## Verification

- Targeted gate `python -m pytest` over the impacted surface: RC=0
  (`/home/agent/.hermes/local-validation-gate/results/result-1745518-350446670.json`,
  ~184 s), plus `ruff check .` clean at the pinned dev version.
- Full gate `python -m pytest -q`: RC=0, 1627 tests, 5 environment skips, 0
  failures (`/home/agent/.hermes/local-validation-gate/results/result-745880-351751581.json`,
  ~251 s).
- Red/green: pre-fix shim (acquire TTL 0.5 s → sleep 0.8 s → second acquire)
  returned `True` (invariant loss demonstrated); post-fix the outliving-TTL
  test holds the lease and releases it on completion.
