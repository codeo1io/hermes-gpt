# Repository Extension Research — upstream verification & candidate evidence

run: 1e8a1adc5d624726b5b150f8a551a82e | phase: research | attempt: 027c728ee42043248a63763a48e9cb20
date: 2026-09-01 | repo: hermes-gpt @ ab42884 (audit/infra-boundary), pyproject 0.8.0, `mcp[cli]>=1.0,<2`
method: ce-ideate router + agent-reach (GitHub backend: `gh api`/`gh release`; web backend: Jina Reader / endoflife.date API). All external claims below were fetched live this run; every item cites its source and date. Research ran in-thread (no subagent tool in this harness).

Relationship to prior artifact: this file VERIFIES and EXTENDS `docs/ideation/2026-09-01-repository-extensions-ideation.md` (7 ranked ideas). It does not replace it — every idea there kept its factual basis under verification; deltas are listed.

---

## 1. Verification of the ideation doc's external claims

| Claim (ideation doc) | Verdict | Live source (fetched 2026-09-01) |
|---|---|---|
| MCP Python SDK v2.0.0 stable 2026-07-28; 2.1.1 current | **Confirmed, extended**: v2.1.1 (2026-08-25) is `Latest`; **v2.0.1 patch (2026-08-26)** and **v1.29.1 (2026-08-24)** also exist | `gh release list -R modelcontextprotocol/python-sdk` |
| v1.x maintenance-only; keep `<2` if unready | **Confirmed verbatim** — release body: "v1.x is in maintenance mode and will only receive security fixes… keep a `<2` upper bound" | v2.0.0 release notes |
| `FastMCP` → `MCPServer`; transport params off constructor; OTel default; 4 MiB limit | **All confirmed** in v2.0.0 notes; v2.1.0 extends 4 MiB to SSE + OAuth endpoints; **v2.1.1 exists specifically to redirect `mcp.server.fastmcp` imports to the migration guide** — the exact ImportError this repo's drifted host env hits at `server.py:663` | v2.0.0 / v2.1.0 / v2.1.1 release notes |
| Tasks extension (SEP-2663) not in SDK | **Confirmed** ("Known gaps: the tasks extension (SEP-2663) is not part of this release"); `modelcontextprotocol/ext-tasks` is active and **locked to the 2026-07-28 spec+schema (commit 2026-08-24, "lock 2026-07-28 specification and schema (#19)")** | v2.0.0 notes; ext-tasks commits |
| 2026-07-28 revision: no handshake, `server/discover`, `subscriptions/listen`, MRT requests | **Confirmed** (v2.0.0: "stateless requests with no handshake, server/discover, subscriptions/listen, multi-round-trip requests"); **same `MCPServer` still serves every 2025-era client with nothing to configure** — key de-risker for this repo's existing ChatGPT-connector users | v2.0.0 notes |
| MCP Apps official extension since 2026-01-26 | **Confirmed and current**: `modelcontextprotocol/ext-apps` at **1.7.5 (2026-07-23)**, still adding supported clients (2026-08-12) | ext-apps commits/releases |
| A2A v1.0 shipped 2026-04-09 under Linux Foundation | **Substance confirmed, date corrected**: tags show **v1.0.0 = 2026-03-12**, **v1.0.1 = 2026-05-28 (Latest)**; repo pushed 2026-08-31 | `gh release list -R a2aproject/A2A` |
| Authorization spec requires OAuth 2.1, RFC 8707, RFC 9207 (iss SHOULD→MUST) | **Confirmed with nuance**: spec source says AS "**MUST** implement OAuth 2.1" (index.mdx:62); `iss` is "**SHOULD** include, **MUST** advertise `authorization_response_iss_parameter_supported=true`" (index.mdx:194) — not upgraded to MUST; client-side validation of recorded issuer is mandatory | `specification/docs/specification/2026-07-28/basic/authorization/index.mdx` (main) |
| Python 3.10 EOL 2026-10-31 | **Confirmed exactly** — 60 days from today; 3.11 EOL 2027-10-31 | endoflife.date/api/python.json |
| Orchestration frameworks consolidated, none own fail-closed delegation | **Directionally confirmed**: openai-agents-python v0.22.0 (2026-08-19, 29.1k★, pushed 2026-08-31); langgraph 40.8k★ (pushed 2026-08-30). Both ship orchestration breadth; neither markets verified-from-observed-state delegation validation | gh api repos/{openai/openai-agents-python, langchain-ai/langgraph} |

## 2. New findings since the ideation doc was written

1. **An official MCP conformance test framework exists and is runnable against any live server** — `modelcontextprotocol/conformance` ("Conformance Tests for MCP", pushed 2026-08-31), `npx @modelcontextprotocol/conformance server --url http://localhost:PORT/mcp`, scenario/suite selection (`--suite auth`). The Python SDK already integrates it ("Bump conformance harness to 0.2.0-alpha.11", v2.1.0 notes). hermes-gpt has no conformance gate today: CI runs its own pytest only (`.github/workflows/ci.yml`).
2. **v2 ships `Resolve(fn)` — the standard primitive for this repo's approval gates.** v2.0.0: "At 2026-07-28 the server can no longer call the client… a `Resolve(fn)` parameter is filled by your function invisibly to the model and can put a question to the user; one tool body serves both eras." This is upstream's own answer to the exact pattern `hermes_job_wait` (120 s in-call block, `server.py:2069-2076`) and the swarm final-approval gate implement by hand today.
3. **v2.1.0 behavior changes that land on this repo verbatim if it migrates**: handler exception text no longer reaches clients (only `Error executing tool <name>`; `ToolError` still passes) — audit-log and user-facing error text must be re-checked; TypedDict `NotRequired` no longer serialized as `null`; SSE message endpoint answers 405 to non-POST.
4. **`v1.29.1` (2026-08-24) is a same-day final sync of the v1 line** — a no-code-change floor bump available *now* (`>=1.28` style pin): fresh installs already resolve 1.29.1 (verified: isolated venv installed mcp 1.29.1), while `docs/mcp-compatibility.md:6` still claims "Verified: 2026-08-15 against `mcp` 1.28.1".
5. **Specification `main` is 142 commits / 169 files ahead of the 2026-07-28 release** — mostly SEP-2663 (tasks) fixes and site content; no new revision tagged yet. Adopting 2026-07-28 now is not immediately stale, and the tasks schema it depends on is now *locked*.
6. **Zero open issues on origin (`asimons81/hermes-gpt`)** — no issue-tracker backlog to mine; user-need signal must come from docs themes (ChatGPT connector, Secure MCP Tunnel, operator/flight-deck, Windows path), the CHANGELOG, and the conductor's roadmap. Tunnel/connector docs are the user-facing growth path (`docs/openai-secure-mcp-tunnel.md`, `docs/cloudflare-tunnel.md`).
7. **Dependency refresh facts** (for the runtime-floor candidate): httpx2 latest 2.12.0; sse-starlette 3.4.8; both unpinned in pyproject today.
8. **Assess-phase defects are roadmap prerequisites, not candidates**: the adversarial assessment (prior phase, artifact `/tmp/ce-code-review/1e8a1adc5d624726b5b150f8a551a82e/adversarial-assessment.md`) proved the new `ui_security` redaction boundary drops PEM/modern token shapes, has quadratic pre-truncation cost (7.75 s CPU for a 32 KB tool result), and mangles capitalized-word text in all Flight Deck payloads. Any candidate that widens browser/UI exposure (ideation idea 3, MCP Apps) is gated on fixing these first.

## 3. Evidence-backed candidates (delta over the ideation doc's 7)

Ideas 1–7 in `2026-09-01-repository-extensions-ideation.md` retained their factual basis (§1). Additions and updates:

### A. (NEW) Official MCP conformance gate in CI — cheap, independent of the v2 migration
**What:** run `@modelcontextprotocol/conformance server --url http://127.0.0.1:PORT/mcp` (plus `--suite auth` against the OAuth-enabled fixture) as a CI job next to pytest.
**Basis:** repo: CI runs only its own pytest (`.github/workflows/ci.yml` test job); `docs/mcp-compatibility.md:10-14` makes protocol claims "asserted at test time by `test_mcp_compat.py`" — a self-written test, i.e. the repo grades its own protocol homework. external: the official framework exists, is SDK-integrated, and targets exactly this (source §2.1, pushed 2026-08-31).
**Rationale:** produces an independent protocol-compliance signal today, on v1, and becomes the acceptance gate that de-risks candidate 1's migration.
**Downsides:** Node in CI (already present for the `web` job); conformance harness is 0.2.0-alpha (SDK bumps it in lockstep).
**Confidence:** 85% · **Complexity:** Low–Medium

### B. (NEW) Adopt `Resolve(fn)` multi-round-trip shape for approval gates when migrating
**What:** when the swarm final approval gate / contract confirmations move to v2, express "ask the human" as a `Resolve` parameter return (`input_required`-style) rather than bespoke tool pairs, keeping the current tools as the stable surface.
**Basis:** repo: `operator_swarm.py:134-147` bounded swarm with final human gate; `server.py:1503-1507` five bespoke polling tools; `server.py:2069-2076` 120 s blocking wait. external: v2.0.0 release notes document `Resolve(fn)` as the intended replacement for server→client calls, "one tool body serv[ing] both eras" (§2.2).
**Rationale:** converts the repo's most proprietary interaction into the SDK-maintained one; pairs with ideation idea 2 (tasks handles).
**Downsides:** v2-only (needs idea 1); behavior must stay correct for 2025-era clients via the era-negotiation path.
**Confidence:** 78% · **Complexity:** Medium

### C. (UPDATE to idea 1) Migration acceptance criteria are now concrete
Bump to `mcp>=2,<3` is validated by: multi-era wire support (2025-era clients served unchanged — protects the ChatGPT connector path), a locked tasks schema in ext-tasks, the official conformance suite (candidate A) as the gate, and the SDK's own migration guide. Must-handle list now includes v2.1.0's handler-exception-text change (§2.3) and the 4 MiB limit on SSE/OAuth endpoints (check `oauth_auth.MAX_TOKEN_REQUEST_BYTES` interplay). Sequencing note: an interim `>=1.28,<2` → 1.29.1 floor bump + manifest refresh is available with zero code change (§2.4).
**Confidence:** 92% (unchanged) · **Complexity:** High

### D. (UPDATE to idea 4) OAuth conformance pack — one correction, two additions
PKCE-both-directions is **already implemented in the uncommitted working tree** (oauth_auth.py:294-300, 605-616, 663-676 — verified fail-closed in the assess phase), so the remaining scope is: emit RFC 9207 `iss` in authorization responses **and** advertise `authorization_response_iss_parameter_supported` (spec: SHOULD include / MUST advertise — index.mdx:194), keep `resource` validation (already enforced at authorize time, oauth_auth.py:604-606), and fix the non-ASCII-credentials 500 (assess M1) so `--suite auth` conformance runs clean. Lower effort than the doc estimated.
**Confidence:** 90% · **Complexity:** Low–Medium

### E. (PREREQUISITE) ui_security redaction hardening before any UI-surface expansion
Not a feature: the three assess-phase highs (secret-shape regression incl. PEM; quadratic cost; PII over-mangling) must be fixed before ideation idea 3 (MCP Apps / `ui://` governance surfaces) widens what crosses the browser boundary. Sources: assess artifact + `operator_policy.py:1042-1058`, `ui_security.py:198/208/264`, in-repo correct order at `operator_mission.py:336`.
**Confidence:** 95% · **Complexity:** Low (order swap) → Medium (shape list)

### Rejected this run (with reasons)
- **FastA2A/agent-card framework adoption**: repo's fabric peer is A2A-shaped but self-hosted (`operator_fabric.py:2802-2840`); swapping to upstream A2A SDKs is a rework with no user-asked pull yet (zero open issues) — revisit when a real cross-vendor peer requirement appears.
- **LangGraph/CrewAI-style graph orchestration inside hermes**: competes on breadth the repo deliberately does not own; differentiator is fail-closed verified delegation (confirmed still unclaimed by both frameworks, §1 last row).
- **Python 3.14 floor jump**: premature; 3.11 floor (idea 7) suffices for the 2026-10-31 EOL deadline, and CI already tests 3.10–3.12.

## 4. Corrections to the prior ideation doc
1. A2A v1.0 tag date is 2026-03-12 (v1.0.1 = 2026-05-28), not 2026-04-09.
2. RFC 9207 `iss`: spec says authorization servers SHOULD include it and MUST advertise support via `authorization_response_iss_parameter_supported`; it has not been upgraded to MUST.
3. Idea 4's PKCE bypass basis (`oauth_auth.py:293-294` `if challenge:` guard) describes HEAD; the current working tree closes it — the doc should be re-read against the tree before any plan phase cites it.

## 5. Source register (all fetched 2026-09-01)
- gh api/release: modelcontextprotocol/python-sdk (v2.0.0, v2.0.1, v2.1.0, v2.1.1, v1.29.1 bodies; tags), specification (releases 2026-07-28…; compare 2026-07-28…main = 142 ahead/169 files), ext-tasks (commits 2026-08-24), ext-apps (1.7.5; client list 2026-08-12), conformance (README, pushed 2026-08-31), a2aproject/A2A (tags v1.0.0/v1.0.1), agentskills/agentskills (pushed 2026-08-09), openai/openai-agents-python (v0.22.0, 29.1k★), langchain-ai/langgraph (40.8k★)
- spec source: `specification/docs/specification/2026-07-28/basic/authorization/index.mdx` @ main (lines 32-62, 176-194)
- endoflife.date/api/python.json (3.10 → 2026-10-31; 3.11 → 2027-10-31)
- PyPI via pip index: mcp (1.29.1 resolves under current pin; 2.1.1 latest), httpx2 2.12.0, sse-starlette 3.4.8
- repo evidence: pyproject.toml:16, server.py:663/1503-1507/2069-2076/2720-2731, operator_swarm.py:134-147, operator_fabric.py:2802-2840, operator_export.py:172-206, docs/mcp-compatibility.md:6-14, .github/workflows/ci.yml, gh issue list asimons81/hermes-gpt (empty)
