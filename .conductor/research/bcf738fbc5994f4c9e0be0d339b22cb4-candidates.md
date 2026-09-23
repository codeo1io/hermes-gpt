# Research: repository extension candidates — run a51c0f6cb5b04ea9855a3dc3aba88c78, cycle 1

Attempt bcf738fbc5994f4c9e0be0d339b22cb4 · 2026-09-20 · method: ce-ideate
conventions (generate broadly → critique all → survivors with cited evidence;
rejections kept so the bar is visible). All external queries read-only via
`gh api` / `pip index` / `git fetch upstream`.

## Evidence base gathered this phase

1. **Upstream (asimons81/hermes-gpt)**: `git fetch upstream` →
   `git rev-list --count HEAD..upstream/master` = **0**; newest upstream commit
   9f537106e9 (2026-09-15, PR #67) already absorbed. No upstream drift, **0 open
   upstream issues/PRs** → user-need signal must come from standards/ecosystem,
   not upstream trackers. Fork `codeo1io/hermes-gpt` has issues disabled.
2. **Dependencies** (pip index, 2026-09-20): mcp **2.2.0** (also 2.1.0/2.1.1/
   2.0.1 on 08-24/26; 1.30.0 on 09-07), cryptography 50.0.1, uvicorn 0.53.0,
   packaging 26.3, pyyaml 6.0.3, keyring 25.7.0. pyproject floor `mcp>=1.28.1,<3`
   admits all of these. CI (.github/workflows/ci.yml:24-37) tests two *ranges*
   (which now resolve 1.30.0 / 2.2.0) plus two *exact pins* (1.28.1, 2.0.0).
3. **MCP spec 2026-07-28 (GA)** — modelcontextprotocol/modelcontextprotocol
   `docs/specification/2026-07-28/changelog.mdx`: stateless protocol (no
   initialize handshake, `_meta` protocolVersion per request), `server/discover`
   RPC, `subscriptions/listen` replaces GET stream + resources/subscribe,
   ping/logging-setLevel removed, **official Tasks extension
   (`io.modelcontextprotocol/tasks`; poll via `tasks/get`, client input via
   `tasks/update`, unsolicited task handles)**, **MRTR pattern**
   (`InputRequiredResult` + retry with `inputResponses`), required `resultType`
   on all results, SSE resumability/Last-Event-ID removed.
4. **MCP python-sdk release notes** (gh api releases): v2.1.0 (08-24) — handler
   exception text hidden from clients unless `ToolError`, 4 MiB body limit
   extended to SSE + OAuth endpoints, content-block annotation/outputSchema
   changes; v2.2.0 (09-07) + v1.30.0 — cross-origin redirect refusal (client),
   30-min idle session expiry + 10k session cap (**stateless servers exempt**),
   OAuth client issuer check.
5. **Repo alignment facts**: hermes serves streamable HTTP with
   `stateless_http=http` + `json_response=http` (server.py:3232-3233) — exempt
   from 2.2 session expiry/cap; all hermes surfaces already use explicit
   server-minted handles (job_id/mission_id/cursor), matching the 2026-07-28
   handle-based direction; `hermes_live_events_*` is cursor-poll tools, not a
   GET stream; RFC 9728 well-known metadata already implemented
   (oauth_auth.py:877-883); 2026-07-28 `_meta` negotiation already asserted in
   test_mcp_sdk_migration.py:109-110.
6. **In-repo roadmap state** (origin/master ROADMAP.md): rm-002 (tests for 14
   untested web/ modules), rm-001 (refactor 21 complexity-hot functions). v0.10
   slice-1 is "strictly additive and decision-only" (docs/releases/
   v0.10-slice1-release-notes.md:5) — act-authority wiring is the open internal
   direction. Prior assess-phase findings F1-F10 remain open
   (.conductor/review/ae925afb81c54271bef8e449968d0a2a-findings.md).

## Surviving candidates (ranked)

### R1 — Speak the official MCP Tasks extension for long-running work
Map `hermes_job_status`/`hermes_job_wait`, delegation jobs, and (slice-2) the
mission controller's stage executions onto `io.modelcontextprotocol/tasks`
handles: `tasks/get` polling, `tasks/update` for client-side inputs, unsolicited
handles on dispatch. Why: upstream issue #57 built a "server-independent job
supervisor … long-poll status across MCP server restarts" as *hermes-private*
tools; the 2026-07-28 extension makes the same semantics a standard, so generic
MCP clients (Codex, Claude, Flight Deck) could track hermes jobs without
hermes-specific tool knowledge. Guardrails: additive read-only mapping first
(handles wrap existing job_ids; no new authority); keep `hermes_*` tools as the
canonical surface. Effort: medium. Sources: spec changelog item 6 (SEP-2663);
SDK 2.x line supports the extension family (2026-07-28 beta blog
blog/content/posts/2026-06-29-sdk-betas-for-2026-07-28.md); internal anchors
operator_job_supervisor.py, operator_delegations.py.

### R2 — MRTR (`input_required`) as the standardized approval handshake
Use `InputRequiredResult`/`inputResponses` for the existing dry-run→apply ladder
and Owner-Mode confirmations instead of (or alongside) bespoke
`confirm=`/`apply=` flags: a mutating tool in dry-run returns `input_required`
with the proposed diff; the client retries with the confirmation. Why: the
authority ladder (read-only → dry-run → apply) is hermes' core safety contract;
MRTR is the protocol-standard way to express exactly this, and it removes the
"client forgot confirm=True" class of misuse at the protocol layer. Guardrails:
must remain opt-in per surface and dry-run-first; direct-mode gates unchanged;
requires SDK support assertion before any rollout. Effort: medium-high.
Sources: spec changelog item 7 (SEP-2322); internal anchors operator_policy.py
apply-mode plumbing, docs/operator-mode.md authority ladder.

### R3 — SDK floor/verification refresh for the 2.1/2.2 line
CI range lanes already resolve 2.2.0/1.30.0, so compatibility is de facto
exercised — but nothing *asserts* it, and the exact-pin jobs (1.28.1, 2.0.0)
are now two minors behind the current line. Add explicit `mcp==2.2.0` and
`mcp==1.30.0` pin jobs (or refresh pins each cycle) plus a spec-revision
assertion test that fails when the SDK's advertised protocol revision changes
(vs the one test_mcp_sdk_migration.py pins), so 2026-07-28-family changes
surface deliberately. Also fold in the 2.1 behavior-change audit: handler
exception text hiding (hermes returns its own error dicts — verify no tool
relies on exception strings reaching clients), 4 MiB OAuth-endpoint body cap.
Effort: small. Sources: ci.yml:24-37; SDK release notes (gh api); pip index.

### R4 — POSIX audit-log home + bounded retention (from assess F2/F5)
Route `audit_log_path()` through HERMES_HOME/logs on POSIX
(normalize_hermes_data_root pattern), surface audit write failures in
operator diagnostics, add size-capped rotation and a reverse-read tail. Why:
current POSIX fallback writes into the package dir and swallows OSError —
silent audit loss on read-only pip installs; docs only cover the Windows path
(docs/operator-mode.md:435). Effort: small-medium. Sources: operator_policy.py:
46-47,772-783,874-878,880-903; worktree proof logs/hermes_gpt_operator_audit.jsonl.

### R5 — Session-jobs retention + watcher hardening (from assess F6)
Retention policy (age/count cap) for session-jobs/*.json|txt and full-glob
`_reconcile` cost; fix `_watch` cleanup so a non-TimeoutExpired `proc.wait`
error cannot strand a session in SESSION_BUSY. Effort: small. Sources:
operator_session.py:156,193,211-294.

### R6 — Exact money math in the budget ledger (from assess F8)
Integer micro-units (or Decimal) for quota/spend with exact crossing
comparisons; keeps INV-8 hard-block decisions immune to float drift. Effort:
small. Sources: operator_mission_budget.py:62-115,270-296.

### R7 — Governance: protect master with required CI checks (from assess F3)
Branch protection (required "Run full test suite" + ruff jobs) so merges like
#66/#67/#5/#7 can no longer land on a red master. Infra op on
codeo1io/hermes-gpt, zero code. Effort: trivial (needs repo admin).
Sources: gh api branches/master/protection → 404; 4 consecutive failing master
runs since 2026-09-13.

### R8 — subscriptions/listen alignment study (optional, low priority)
When a hermes consumer needs push-style change notification, prefer the
2026-07-28 `subscriptions/listen` stream over reintroducing SSE GET semantics;
note SSE resumability (Last-Event-ID) is removed at that revision, so
cursor-replay tools (`hermes_live_events_since(cursor, replay)`) remain the
recovery story. Decide only when a push consumer exists. Sources: spec
changelog items 4/9; server.py:1879-1884.

## Rejected candidates (with reasons)

- **Adopt RFC 9728 protected-resource/authorization-server metadata** — already
  implemented (oauth_auth.py:877-883). Duplicate.
- **Idle-session expiry / 10k session cap exposure** — hermes runs
  `stateless_http=True` in HTTP mode (server.py:3232), explicitly exempt.
- **Redirect-origin and OAuth-issuer client rules** — client-side SDK behavior;
  hermes is the server/AS; no hermes client surface affected.
- **Drop SDK 1.x support** — 1.x still maintained (1.30.0, 2026-09-07) and the
  dual-family CI is a stated product feature (docs/mcp-compatibility.md).
- **web/ test coverage / complexity refactors** — already ROADMAP items rm-002 /
  rm-001; not new (origin/master ROADMAP.md).
- **cryptography/uvicorn floor bumps** — CI range lanes already install latest
  (cryptography 50.0.1 et al.) continuously; no failure signal.
- **Codex CLI version tracking** — openai/codex releases are an alpha train
  (rust-v0.156.0-alpha.9, 2026-09-20); no stable contract to pin against; docs
  already avoid version claims.
- **Ping/logLevel removal handling** — SDK-transport concern, inherited by
  upgrade; nothing hermes-level to do beyond R3's assertion.

## Sequencing recommendation for the roadmap
R7 (unlock trustworthy CI) → R3 + assess-F1 test repair (re-green, intentional
SDK coverage) → R4/R5/R6 (small reliability batch) → R1 (Tasks extension,
read-only mapping) → R2 (MRTR approval study) → R8 (defer).
