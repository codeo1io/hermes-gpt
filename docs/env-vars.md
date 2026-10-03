# Environment variable reference

Every runtime knob `hermes-gpt` reads, with its exact name, default, and the
module that reads it. This is the generated-from-code reference for the
`HERMES_GPT_*` family; secrets shown here are *names only* — never put secret
values in documentation, issues, or operator records.

Conventions:

- Unless noted, unset means the code default below applies.
- Truthiness: gates read via `env_truthy` accept `1/true/yes/on`
  (case-insensitive); `_env_enabled`/`env_enabled` helpers accept only the
  literal `1`. Absent any of those, the gate is **disabled**.
- Allowlists (`..._ALLOWLIST`, `..._ALLOWED_*`) are comma-separated; **unset
  means allow-all**, setting them restricts to exactly the listed values.
- Most knobs are read once at server start or first use; changing them
  generally requires a restart.

Maintenance: knobs live as module constants (for example
`codex_core.py:39-53`, `operator_runners.py:49-53`), so code greps for env
*names* undercount. Re-derive this table from the constants when adding knobs,
and register every new knob here in the same change (repository rule).

## Server transport and network boundary

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_HOST` | `127.0.0.1` | `server.py` | Listen address. Loopback by default; binding elsewhere is operator-controlled. |
| `HERMES_GPT_PORT` | `4750` | `server.py` | Listen port. |
| `HERMES_GPT_ALLOWED_HOSTS` | empty (loopback only) | `server.py` | Host header allowlist; empty keeps the loopback boundary. |
| `HERMES_GPT_TRUSTED_PROXY_IPS` | empty (none) | `server.py` | IPs trusted to set forwarding headers. Empty = no proxy trust. |
| `HERMES_GPT_BEARER_TOKEN` | empty | `oauth_auth.py` | Static bearer credential for the API surface. |
| `HERMES_GPT_UNSAFE_REMOTE_NOAUTH` | unset (off) | `server.py` | `1` permits unauthenticated remote hosting — unsupported, dangerous, never for public use. |

## OAuth (see `docs/oauth.md` for the full model)

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_OAUTH_ENABLE` | unset (off) | `oauth_auth.py` | Enables the OAuth surface. |
| `HERMES_GPT_OAUTH_DCR` | `1` | `oauth_auth.py` | Dynamic client registration on/off. |
| `HERMES_GPT_OAUTH_CLIENT_ID` | empty | `oauth_auth.py` | Static OAuth client id. |
| `HERMES_GPT_OAUTH_CLIENT_SECRET` | empty | `oauth_auth.py` | Static OAuth client secret. |
| `HERMES_GPT_OAUTH_ISSUER` | empty | `oauth_auth.py` | Token issuer identifier. |
| `HERMES_GPT_OAUTH_REDIRECT_URI` | empty | `oauth_auth.py` | Redirect URI for the code flow. |
| `HERMES_GPT_OAUTH_SCOPE` | `hermes` | `oauth_auth.py` | Scope string requested/issued. |
| `HERMES_GPT_OAUTH_PKCE_MODE` | `required` | `oauth_auth.py` | PKCE enforcement mode. |
| `HERMES_GPT_OAUTH_GEMINI_ENABLE` | unset (off) | `oauth_auth.py` | Enables the Gemini OAuth lineage. |
| `HERMES_GPT_OAUTH_GEMINI_CLIENT_ID` | empty | `oauth_auth.py` | Gemini lineage client id. |
| `HERMES_GPT_OAUTH_GEMINI_CLIENT_SECRET` | empty | `oauth_auth.py` | Gemini lineage client secret. |
| `HERMES_GPT_OAUTH_GEMINI_REDIRECT_URI` | empty | `oauth_auth.py` | Gemini lineage redirect URI. |

## Token store

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_TOKEN_MASTER_KEY` | unset (generated/stored) | `token_store.py` | Overrides the generated per-root master key. Unset is the normal state: a key is generated on first use and stored `0600` in the secrets dir (`0700`). |

## Feature gates (all default off unless noted)

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_ENABLE_WRITE` | `1`-only, off | `server.py` | Master write gate for mutating tools. |
| `HERMES_GPT_ENABLE_MEMORY_WRITE` | `1`-only, off | `server.py` | Memory mutation gate. |
| `HERMES_GPT_ENABLE_TERMINAL` | `1`-only, off | `server.py` | Terminal tool gate. |
| `HERMES_GPT_ENABLE_SESSION_SEARCH` | `1`-only, off | `server.py` | Session search gate. |
| `HERMES_GPT_ENABLE_SESSION_INTERNAL_CONTENT` | `1`-only, off | `server.py` | Exposes internal session content — sensitive. |
| `HERMES_GPT_ENABLE_VISION` | `1`-only, off | `server.py`, `codex_core.py` | Vision tool gate. |
| `HERMES_GPT_ENABLE_WEB` | `1`-only, off | `server.py`, `codex_core.py` | Web fetch/extract gate. |
| `HERMES_GPT_ENABLE_CODEX` | `1`-only, off | `codex_core.py` | Codex CLI worker surface gate. |
| `HERMES_GPT_ENABLE_MCP` | `1`-only, off | `codex_core.py` | MCP bridge gate. |
| `HERMES_GPT_ENABLE_CRON` | `1`-only, off | `codex_core.py` | Cron scheduling gate. |
| `HERMES_GPT_ENABLE_DIAGNOSTICS` | `1`-only, off | `codex_core.py` | Diagnostics surface gate. |
| `HERMES_GPT_ENABLE_CODEX_RUNNER` | `1`-only, off | `codex_core.py`, `operator_codex.py` | Codex runner delegation gate. |
| `HERMES_GPT_ENABLE_FINANCE` | truthy, off | `operator_finance.py` | Finance surface gate. |
| `HERMES_GPT_ENABLE_RUNNER_PLUGINS` | truthy, off | `operator_runners.py` | Runner plugin loading gate. |
| `HERMES_GPT_ENABLE_SESSION_CONTROL` | truthy, off | `operator_session.py` | Session-control tools gate. |

## Write allowlist gates (Codex CLI lane; `1`-only)

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_ALLOW_WRITE` | off | `codex_core.py` | Codex write gate. |
| `HERMES_GPT_ALLOW_CODEX_WRITE` | off | `codex_core.py`, `operator_codex.py` | Codex-owned write gate. |
| `HERMES_GPT_ALLOW_CRON_WRITE` | off | `codex_core.py` | Cron write gate. |
| `HERMES_GPT_ALLOW_SKILL_WRITE` | off | `codex_core.py` | Skill file write gate. |
| `HERMES_GPT_ALLOW_PRIVATE_NETWORK` | off | `codex_core.py` | Permits private-network access from the Codex lane. |

## Codex CLI lane configuration

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_CODEX_EXE` | empty (PATH `codex`) | `operator_codex.py` | Codex executable override. |
| `HERMES_GPT_CODEX_TOOLSET` | `core` | `codex_core.py` | Codex toolset selection. |
| `HERMES_GPT_CODEX_ALLOWED_ROOTS` | unset (none) | `codex_core.py` | Roots the Codex lane may touch; comma-separated. |

## Operator policy and authority

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_OPERATOR_ENABLED` | truthy, off | `operator_policy.py` | Operator surface gate. |
| `HERMES_GPT_OPERATOR_LEVEL` | `read_only` | `operator_policy.py` | Operator level (`read_only`, …). |
| `HERMES_GPT_OPERATOR_APPLY_MODE` | `dry_run` | `operator_policy.py` | Default apply mode; direct mutation requires explicit direct-mode gates. |
| `HERMES_GPT_OWNER_ACK` | empty | `operator_policy.py` | Owner acknowledgement phrase for Owner Mode. |
| `HERMES_GPT_OWNER_ACTIVE` | truthy, off | `operator_policy.py` | Owner Mode activation. |
| `HERMES_GPT_OPERATOR_ALLOWED_PATHS` | unset | `operator_policy.py` | Path allowlist. |
| `HERMES_GPT_OPERATOR_DENIED_PATHS` | unset | `operator_policy.py` | Path denylist. |
| `HERMES_GPT_OPERATOR_ALLOWED_PROFILES` | unset | `operator_policy.py` | Profile allowlist. |
| `HERMES_GPT_MISSION_ALLOWED_SURFACES` | unset = all read-only; empty = all denied | `operator_mission.py` | Mission Control surface allowlist (see repository docs). |
| `HERMES_GPT_CONTROLLER_EXECUTE` | empty | `operator_controller.py` | Controller execution gate. |
| `HERMES_GPT_BUDGET_HARD_BLOCK` | truthy, off | `operator_mission_budget.py` | Hard budget blocking. |
| `HERMES_GPT_PROFILE` | `unknown` | `operator_review.py` | Active profile name. |

## Swarm bounds (value clamped between default and hard cap)

| Variable | Default (hard cap) | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_SWARM_MAX_PARALLEL` | 3 (8) | `operator_swarm.py` | Max parallel stage work. |
| `HERMES_GPT_SWARM_BOARD_CAP` | 4 (16) | `operator_swarm.py` | Board item cap. |
| `HERMES_GPT_SWARM_MAX_STAGES` | 12 (64) | `operator_swarm.py` | Stage count cap. |

## Runner confinement and allowlists

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_ENABLE_RUNNER_CONFINEMENT` | empty (off) | `runner_confinement.py` | Runner sandbox confinement gate. |
| `HERMES_GPT_RUNNER_BACKEND_ALLOWLIST` | unset = all | `operator_runners.py` | Allowed runner backends. |
| `HERMES_GPT_RUNNER_PLUGIN_ALLOWLIST` | unset = all | `operator_runners.py` | Allowed runner plugins. |
| `HERMES_GPT_RUNNER_PROVIDER_ALLOWLIST` | unset = all | `operator_runners.py` | Allowed Pi providers. |
| `HERMES_GPT_RUNNER_MODEL_ALLOWLIST` | unset = all | `operator_runners.py` | Allowed Pi models. |
| `HERMES_GPT_PI_EXE` | unset (PATH) | `operator_runners.py` | Pi runner executable. |
| `HERMES_GPT_OPENCODE_EXE` | unset (PATH) | `operator_runners.py` | OpenCode runner executable. |
| `HERMES_GPT_OMX_EXE` | unset (PATH) | `operator_runners.py` | OMX runner executable. |

## Fleet and fabric

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_FLEET_PEER_NAME` | empty | `server.py` | Local fleet peer name. |
| `HERMES_GPT_FLEET_PEER_URL` | empty | `server.py` | Local fleet peer URL. |
| `HERMES_GPT_FLEET_PEER_VERSION` | `0.20.5` | `server.py` | Advertised peer version. |
| `HERMES_GPT_FLEET_A2A_MODE` | `auto` | `operator_fleet.py` | A2A interop mode. |
| `HERMES_GPT_FLEET_AUTHORITY_MANIFEST` | unset | `operator_fleet.py` | Authority manifest path. |
| `HERMES_GPT_FABRIC_COORDINATOR_DB` | `<root>/coordinator.db` | `operator_fabric.py` | Fabric coordinator DB override. |
| `HERMES_GPT_FABRIC_PEER_DB` | `<root>/peer.db` | `operator_fabric.py` | Fabric peer DB override. |
| `HERMES_GPT_FABRIC_NODE_REGISTRY` | `<root>/fabric-nodes.json` | `operator_fabric.py` | Node registry override. |
| `HERMES_GPT_FABRIC_PEER_POLICY` | `<root>/fabric-peer-policy.json` | `operator_fabric.py` | Peer policy override. |
| `HERMES_GPT_FABRIC_PEER_TOKENS` | empty | `operator_fabric.py` | Fabric peer tokens. |
| `HERMES_GPT_FABRIC_ROUTING_POLICY` | empty | `operator_fabric_router.py` | Fabric routing policy. |

## Workspace, retention, and limits

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_OPERATOR_TMPDIR` | empty (system temp + janitor) | `operator_workspace.py` | Operator scratch dir override. |
| `HERMES_GPT_EVENTS_MAX_AGE_DAYS` | 90 | `operator_events.py` | Event retention window (days). |
| `HERMES_GPT_LIVE_EVENT_RETENTION` | module default | `operator_live_events.py` | Live-event retention. |
| `HERMES_GPT_EVENTS_ALLOWED_SOURCES` | unset | `operator_events.py` | Event source allowlist. |
| `HERMES_GPT_LEDGER_ALLOWED_SOURCES` | unset | `operator_mission_ledger.py` | Ledger source allowlist. |
| `HERMES_GPT_CAPABILITY_ALLOWED_SOURCES` | unset | `operator_capability_manifest.py` | Capability source allowlist. |
| `HERMES_GPT_CAPABILITY_CACHE_TTL` | 60s (clamped 5–3600) | `operator_capability_manifest.py` | Capability cache TTL seconds. |
| `HERMES_GPT_EXPORT_MAX_BYTES` | 4 MiB (hard cap 16 MiB) | `operator_export.py` | Max file-export size. |
| `HERMES_GPT_EXPORT_ALLOWED_EXTENSIONS` | unset | `operator_export.py` | Export extension allowlist. |
| `HERMES_GPT_TOOL_THREAD_LIMIT` | 40 (anyio default) | `mcp_compat.py` | Worker-thread pool size for sync tool offload (both SDK lanes — see [MCP compatibility](mcp-compatibility.md)). Read once per process. Saturation logs a rate-limited warning. |

## UI (Flight Deck)

| Variable | Default | Read in | Meaning |
| --- | --- | --- | --- |
| `HERMES_GPT_UI_ENABLED` | unset (off) | `server.py` | Serves the Flight Deck UI. |
| `HERMES_GPT_UI_DIR` | empty (bundled) | `ui_security.py` | UI static root override. |
| `HERMES_GPT_UI_PROFILE` | empty | `ui_chat.py` | UI chat profile. |
| `HERMES_GPT_UI_MAX_CONCURRENT` | 4 | `ui_chat.py` | Concurrent UI chat sessions. |
| `HERMES_GPT_UI_STALE_LEASE_S` | empty (module default) | `ui_security.py` | Stale lease timeout seconds. |
| `HERMES_GPT_UI_TOOL_PREVIEW_BYTES` | empty (module default) | `ui_security.py` | Tool result preview byte cap. |
