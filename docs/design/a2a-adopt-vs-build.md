# A2A peer transport: adopt a2a-sdk vs stay hand-rolled (decision record)

Status: decision record for roadmap item `rm-204` (adopt-vs-build evaluation).
Recorded: 2026-10-03, cycle 2 of campaign `hermes-gpt-master-55983cbd1ae514b4`,
at repository HEAD `e490130737`. This file is a design/decision artifact under
`docs/design/` (see `docs/README.md` for the documentation authority map); it
is not runtime instructions.

## Question

`hermes-gpt` speaks the A2A peer protocol (agent cards + JSON-RPC over plain
JSON) through **four hand-rolled surfaces**. The `a2a-sdk` package (PyPI
`a2a-sdk`, current 1.2.1; companion `a2a-cli` 0.2) now covers both the client
and server sides of that protocol. Should we adopt the SDK, pin-and-conform,
or stay hand-rolled?

## The four surfaces (as of HEAD `e490130737`)

| Surface | Location | Behavior |
| --- | --- | --- |
| Fabric peer **client** | `operator_fabric.py` `_http_json` (:666-683) | GET agent card / POST JSON-RPC; `Accept: application/json` on every call; `Content-Type: application/json` + `A2A-Version: 1.0` on POSTs; bounded read (`_MAX_BODY`) |
| Fabric **agent card** | `operator_fabric.py` `_PeerHandler.do_GET` (:2797-2838) | Serves `/.well-known/agent-card.json` and `/.well-known/agent.json` — name, `protocolVersion: "1.0"`, `version` (now derived from `versioning.VERSION`), capabilities, default input/output modes `["application/json"]`, one `hermes-fabric-v1` skill, and a **custom `supportedInterfaces` dialect** (`url` / `protocolBinding: JSONRPC` / `protocolVersion: 1.0`) |
| Fleet **peer discovery client** | `operator_fleet.py` `:221-248` | GET-only discovery of peer cards via `_http_get_json` |
| Server **fleet agent card** | `server.py` `:3072-3134` | Fleet card with `HERMES_GPT_FLEET_PEER_VERSION` override |

Protocol shape verified against the A2A spec trail (`a2a-protocol/A2A`):
`protocolVersion` = spec major version; agent cards advertise transport
capabilities (streaming, push); JSON-RPC methods `message/send`,
`message/stream`, `tasks/get`, …; agent identity in cards; p256 jwk
`preferredTransport`. Current spec patch is `v1.0.1` (2026-05-28).

## Decision

**Stay hand-rolled now; pin-and-conform later.** No `a2a-sdk` dependency is
added. Rationale:

1. **Small, audited surface at the security boundary.** All four surfaces are
   loopback-scoped, `shell=False`, fixed-argv, bounded-read, and
   deterministic by design. Adopting the SDK replaces a few hundred audited
   lines with a large transitive dependency tree exactly at the network
   boundary — the same cost class that pushed `mcp 2.3.0` out (see
   `docs/mcp-compatibility.md`): the upgrade was absorbed only after a probe
   cycle, and pinned negotiation semantics had to be re-verified.
2. **The card dialect divergence is intentional.** The custom
   `supportedInterfaces` entry advertises the deterministic plain-JSONRPC
   binding this server actually implements; generic A2A agents that POST
   without the exact declared content type are rejected *before* any agent
   path runs (see `test_operator_fabric.py::
   test_http_peer_rejects_generic_text_before_any_agent_path`). Conforming to
   the SDK's card model would silently drop that early-rejection guarantee.
3. **`protocolVersion` stays `"1.0"`.** The field tracks the protocol major
   version of the binding we actually implement. Bumping it to advertise the
   `v1.0.1` patch would claim spec-patch conformance we have not verified
   (we implement neither `message/stream` SSE transport nor push
   notifications). Recorded here so the literal at `operator_fabric.py:2812`
   and `:2832` is understood as a decision, not an oversight.
4. **Version truth is fixed as part of this record.** The Fabric card's
   `version` field now derives from `versioning.VERSION` instead of the stale
   `"0.8"` literal — the same pattern as the server fleet card
   (`os.environ.get("HERMES_GPT_FLEET_PEER_VERSION", VERSION)`).
5. **Adoption criteria (what would change the decision).** A concrete
   consumer requirement for non-loopback fleet peering, streaming
   (`message/stream`) responses, or extended-card capabilities would justify
   adoption. Any future adoption must follow the `rm-099` direct-dependency
   rule, keep `rm-153`'s bounded read bound on SDK responses (response
   wrapping required either way), and re-run the targeted tests at the fabric
   and fleet sites: agent card GET + JSON-RPC POST rejection + client header
   dialect.

## Standing guards

`test_operator_fabric.py` carries two conformance guards pinned to this
decision:

- `test_agent_card_advertises_real_package_version` — card GET shape (both
  well-known paths), `protocolVersion == "1.0"`, `version == versioning.VERSION`,
  `supportedInterfaces` dialect.
- `test_peer_client_declares_plain_json_a2a_headers` — client sends
  `Accept: application/json` on every call; `Content-Type: application/json`
  + `A2A-Version: 1.0` on JSON-RPC POSTs.

If either guard fails after a dependency change, re-run this evaluation
before weakening the guard: the guards encode the contract, not an
implementation detail.

## Related

- `docs/mcp-compatibility.md` — precedent for pin-and-conform on a peer
  protocol dependency (`mcp 2.3.0`).
- `docs/operator-mode.md` — operational doc for the Operator surfaces that
  host the fabric peer (`operator_fabric`) and fleet peering
  (`operator_fleet`) clients.
- Roadmap items `rm-099` (direct-dep rule), `rm-153` (bounded read),
  `rm-184` (server-card version truth), `rm-204` (this record).
