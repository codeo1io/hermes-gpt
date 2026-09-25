# OAuth and bearer authentication

Hermes GPT remains local-first. Remote Operator or Owner access is supported only when the HTTP endpoint is carried over HTTPS and protected with either a static bearer token or the built-in confidential-client OAuth boundary described here.

## Security model

The built-in authorization server is intentionally narrow:

- one statically configured confidential client by default, plus optional additional named client profiles (see [Additional clients](#additional-clients-gemini-spark-profile));
- a bounded registry of dynamically registered **public** clients for the
  ChatGPT apps flow — never confidential clients, never secrets (see
  [Dynamic client registration](#dynamic-client-registration-chatgpt-apps-flow));
- exact HTTPS redirect-URI allowlisting;
- client authentication on every authorization-code and refresh exchange;
- **mandatory PKCE (RFC 7636): every authorization request must carry a
  valid `code_challenge` with `code_challenge_method=S256`, and every
  authorization-code exchange must present the matching verifier** — a code
  without a stored S256 challenge can never be exchanged, so a stolen or
  intercepted code is useless without the verifier. `HERMES_GPT_OAUTH_PKCE_MODE`
  selects the policy: `required` (default) rejects every challenge-less
  authorization request, while `optional` lets a **confidential** client
  authorize without a challenge (its secret is still enforced at the token
  endpoint). Public and dynamically registered clients always require PKCE
  in both modes;
- one configured Hermes resource scope (required on every issued token) plus the connector compatibility scopes `openid` and `offline_access`;
- one-hour HMAC-signed access tokens (verifiable by any origin that shares the confidential client secret);
- 30-day refresh tokens with rotation and replay rejection;
- signed, five-minute stateless authorization codes plus bounded process-memory replay, access-token, and refresh-token stores;
- every authorization redirect — success responses and error responses
  alike — carries the issuer identifier as the `iss` query parameter
  (RFC 9207), and the authorization-server metadata advertises
  `authorization_response_iss_parameter_supported`, so a client can bind
  an issued code (or an authorization error) to exactly this authorization
  server;
- no user accounts, no OpenID Provider claims, and no plaintext token
  database: tokens (and the dynamic-client registry) live only in the
  encrypted durable store described below.

`openid` is accepted because ChatGPT may add it even with OIDC disabled. Hermes GPT does not advertise OpenID Provider metadata and does not issue ID tokens; `/.well-known/openid-configuration` is served as a public 404 (not an auth challenge) so clients that probe OIDC discovery with OIDC disabled do not mistake the connector for disconnected. Configure the ChatGPT connector with OIDC disabled.

The client secret is the credential that prevents an arbitrary network caller
from exchanging an authorization code. Confidential clients authenticate with
`client_secret_post` or `client_secret_basic`. Secretless (public-client,
token endpoint auth method `none`) authorization-code exchanges are accepted
**only** when they carry a PKCE verifier that matches the S256 challenge
stored in the authorization code — the verified challenge is the client
authentication, so `none` never bypasses it. Do not expose an OAuth-enabled
endpoint until a strong client secret is configured.

## Generate a client secret

Generate a fresh URL-safe secret. Do not reuse a Hermes, GitHub, gateway, or provider credential.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The result must contain 43 to 128 URL-safe characters. Store it in a service-owned secret environment source, not in the repository, shell history, documentation, or command-line arguments.

## Required OAuth configuration

```text
HERMES_GPT_OAUTH_ENABLE=1
HERMES_GPT_OAUTH_ISSUER=https://mcp.example.com
HERMES_GPT_OAUTH_CLIENT_ID=chatgpt-client
HERMES_GPT_OAUTH_CLIENT_SECRET=<43-to-128-character-generated-secret>
HERMES_GPT_OAUTH_REDIRECT_URI=https://chatgpt.com/connector/oauth/<exact-callback-id>
HERMES_GPT_OAUTH_SCOPE=hermes
```

Multiple exact redirect URIs may be comma-separated. Wildcards are not accepted. The issuer must use HTTPS except for an explicitly loopback-only test server.

Two optional knobs tune client-facing authorization behavior:

```text
HERMES_GPT_OAUTH_PKCE_MODE=required
HERMES_GPT_OAUTH_DCR=1
```

- `HERMES_GPT_OAUTH_PKCE_MODE` — `required` (default) or `optional`. `required` rejects every authorization request that arrives without an S256 `code_challenge`; `optional` additionally accepts requests without PKCE for clients that cannot supply one. Any other value fails startup validation.
- `HERMES_GPT_OAUTH_DCR` — dynamic client registration (RFC 7591) is advertised and served by default: `registration_endpoint` appears in the authorization-server metadata and `POST /oauth/register` answers. Set `0` (or `false`/`off`/`no`) to stop advertising `registration_endpoint` for single confidential-client deployments (for example the Gemini Spark custom-app profile); the `/oauth/register` route itself keeps answering, and registrations remain bounded by a per-source rate window, a 64-client capacity, and a 7-day client TTL.

The built-in OAuth boundary is available only with streamable HTTP (`--http`);
legacy SSE is rejected when OAuth is enabled so discovery and resource binding
cannot disagree.

Authenticated `remote` mode also requires one of these transport boundaries:

- direct TLS using both `--cert` and `--key`; or
- a loopback bind behind a trusted HTTPS reverse proxy, with every local proxy
  address explicitly listed in `HERMES_GPT_TRUSTED_PROXY_IPS`.

Wildcard, non-IP, and non-loopback trusted-proxy entries are rejected. Forwarded
headers are ignored unless this explicit loopback-proxy mode is active.

For a local HTTPS-terminating proxy, set:

```text
HERMES_GPT_TRUSTED_PROXY_IPS=127.0.0.1,::1
```

Then start the remote safety profile only after the configuration validates:

```bash
hermes-gpt --http --host 127.0.0.1 --port 4750 --profile remote
```

Keep the process loopback-bound and terminate HTTPS in a deliberately configured trusted proxy or private tunnel. The public issuer must resolve to that exact server.

## Additional clients (Gemini Spark profile)

One statically configured confidential client remains the default. An opt-in **Gemini Spark client profile** can be registered alongside it for Google's consumer Gemini Apps "Custom apps for Spark" connector:

```text
HERMES_GPT_OAUTH_GEMINI_ENABLE=1
HERMES_GPT_OAUTH_GEMINI_CLIENT_ID=gemini-spark-client
HERMES_GPT_OAUTH_GEMINI_CLIENT_SECRET=<43-to-128-character-generated-secret>
HERMES_GPT_OAUTH_GEMINI_REDIRECT_URI=https://oauth-redirect.googleusercontent.com/r/<exact-google-callback>
```

- The profile is off unless `HERMES_GPT_OAUTH_GEMINI_ENABLE` is exactly `1`; enabling it without all three `HERMES_GPT_OAUTH_GEMINI_*` values fails startup validation with a `ValueError` naming the missing variables.
- `HERMES_GPT_OAUTH_GEMINI_REDIRECT_URI` accepts one or more exact HTTPS URIs, comma-separated, parsed exactly like the primary redirect URI. Wildcards are not accepted.
- Both clients share the issuer, the resource, and the one configured `HERMES_GPT_OAUTH_SCOPE`; each keeps its own secret and its own exact-match redirect allowlist, and a client can only redirect to, or authenticate with, its own credentials.
- Set `HERMES_GPT_OAUTH_DCR=0` for the no-advertised-DCR contract this profile's manual Client ID/Secret path expects (see [Gemini Spark custom app](gemini-spark.md)).
- The primary `HERMES_GPT_OAUTH_CLIENT_ID` / `_CLIENT_SECRET` / `_REDIRECT_URI` values are unchanged and keep working.

Setup, callback discovery, verification, and rollback: [Gemini Spark custom app](gemini-spark.md).

## Dynamic client registration (ChatGPT apps flow)

`POST /oauth/register` implements RFC 7591 dynamic client registration for
the ChatGPT "apps flow" connector, which discovers
`registration_endpoint` in `/.well-known/oauth-authorization-server`,
registers an ephemeral client, and then authorizes with PKCE only:

- **public clients only**: `token_endpoint_auth_method` must be `none`;
  confidential methods are refused and **no client secret is ever issued** —
  PKCE plus the redirect allowlist is the binding control;
- **redirect allowlist**: 1 to 8 redirect URIs, each an absolute HTTPS URL
  whose host is exactly `chatgpt.com`, `chat.openai.com`, or `openai.com`
  (exact-host match — subdomains such as `app.sandbox.chatgpt.com` are
  *rejected*), re-checked at authorization time;
- **bounded and self-healing**: the registry holds at most 64 clients
  (`MAX_DYNAMIC_CLIENTS`). Registrations carry a 7-day TTL
  (`DYNAMIC_CLIENT_TTL_SECONDS`); `cleanup()` evicts expired registrations
  (each new registration runs it first), and an expired client is treated as
  unknown even before eviction, so an unauthenticated caller can exhaust the
  registry only temporarily — never permanently. A connector whose client
  expired simply re-registers;
- **rate-bounded**: each peer (client IP) may register at most 5 times per
  60 seconds (`REGISTER_RATE_LIMIT` / `REGISTER_RATE_WINDOW_SECONDS`, held
  in process memory, so it resets on restart). Exceeding it returns
  `429 temporarily_unavailable` with no partial state; the capacity cap and
  the TTL above stay the durable bounds;
- **operator surfaces**: the registry can be inventoried with
  `OAuthState.list_dynamic_clients()` (client id, redirect URIs,
  registration/expiry stamps, and an `expired` flag for not-yet-reclaimed
  entries) and one entry removed with
  `OAuthState.purge_dynamic_client(client_id)` (idempotent; a purged client
  fails closed immediately). These are Python-level calls today — see
  [OAuth behavior knobs](gemini-spark.md#oauth-behavior-knobs);
- **persistence with revalidation**: the registry persists in the same
  encrypted durable token store as the tokens (surviving restarts). On
  restore, every persisted entry is revalidated at live-registration
  parity — `dyn-` client-id prefix, 1–8 allowlisted HTTPS redirect
  URIs, TTL, capacity — so a tampered store payload cannot smuggle in a
  client (or redirect) that `/oauth/register` would refuse (the raw list
  is capped at 8 entries pre-dedupe, so import is never looser).
  Entries persisted before TTLs existed are granted a fresh TTL on
  import, not immortality; duplicated ids are skipped, first wins.
- **metadata gate**: `HERMES_GPT_OAUTH_DCR` controls whether the discovery
  doc advertises `registration_endpoint`. Default `1` (advertise); `0`,
  `false`, `off`, or `no` removes it from the metadata so DCR-probing
  clients stop trying. The register endpoint itself still answers — the knob
  is the compat/advertising switch. Set it to `0` when running the Gemini
  Spark custom-app profile, whose platform contract is "no DCR".

## ChatGPT connector values

Configure the connector using values derived from the issuer:

```text
MCP URL:               https://mcp.example.com/mcp
Authorization endpoint:https://mcp.example.com/oauth/authorize
Token endpoint:        https://mcp.example.com/oauth/token
Client ID:             chatgpt-client
Client secret:         the generated confidential-client secret
Token auth method:     client_secret_post or client_secret_basic
                      (public clients: `none`, which then requires PKCE)
Default scope:         hermes offline_access
OIDC:                  disabled
```

ChatGPT may add `openid` to the authorization request. `offline_access` is required for refresh-token issuance. A connector authorized before refresh discovery was available must be disconnected and connected once so discovery and authorization run again.

## Token lifecycle

An authorization-code exchange returns an access token with `expires_in=3600`. If `offline_access` was granted, it also returns a refresh token. A successful refresh returns a new access token and rotates the refresh token; replaying the old refresh token fails with `invalid_grant`.

Access tokens are HMAC-SHA256 signed with a key derived from the confidential
client secret. Clustered origins that share the same issuer, client id, client
secret, and resource can validate a ChatGPT bearer issued by another origin
**only when that token is still present in the shared encrypted durable token
store**. A valid signature alone is never sufficient: in server mode the
durable store is the revocation authority, so `hermes_oauth_revoke` removes
access and refresh tokens everywhere at once: the envelope is deleted, a
durable revocation epoch is advanced (fencing off any clustered peer that
still holds pre-revocation tokens in memory and would otherwise re-persist
them), and the live process drops its caches and rotates the
authorization-code signing key. Issuance merges into the shared envelope
rather than replacing it, so one origin's issuance never evicts another
origin's valid tokens. Opaque legacy access tokens
remain valid on the issuing origin via the in-memory/durable store until they
expire. Rotating the client secret invalidates every signed access token.

Authorization codes are short-lived signed values. Only used-code replay state,
access tokens, and refresh tokens are held in process memory. Since v0.7,
issued access and refresh tokens are also persisted to an **encrypted durable
token store** so a server restart does not invalidate credentials:

- store: `<hermes_data>/secrets/hermes_gpt_tokens.db` (0600, SQLite WAL) —
  one transactional store; each row is AES-256-GCM ciphertext keyed by
  sha256(token value), so no token material is stored in plaintext. A
  flock-serialized mutation lock (`hermes_gpt_tokens.db.lock`) orders
  issuance, rotation, and revocation across processes. The dynamic-client
  registry persists here too (client ids, redirect URIs, registration and
  expiry timestamps only — no secrets, because dynamic clients have none);
- retirement tombstones: rotated/revoked token hashes stay retired forever
  (past their original expiry), so a stale peer cache can never resurrect
  them; the revocation epoch lives in the store's metadata and is advanced
  on every revocation;
- legacy upgrade: pre-SQLite JSON artifacts (`hermes_gpt_tokens.json`,
  `hermes_gpt_token_ledger`, `hermes_gpt_token_epoch`) are migrated into
  the store in one transaction at first use, preserving retirement marks
  and the revocation epoch fail-closed, then removed;
- key management precedence: OS keyring (`keyring` lib) → key file
  `<hermes_data>/secrets/hermes_gpt_token_key` (0600, created on first use) →
  env `HERMES_GPT_TOKEN_MASTER_KEY` (CI/test only, weakest — documented);
- no token material is ever written to the audit log or any MCP response;
  `hermes_oauth_status` reports presence/expiry only;
- explicit revocation: `hermes_oauth_revoke` (owner + direct + confirm)
  retires every token and advances the epoch in one transaction, then — under
  the same mutation lock — drops the live process's caches, rotates the
  authorization-code key, and optionally rotates the ACTIVE master key
  (keyring overwrite or key-file regeneration; an env-managed key is
  reported as not rotated with a note to rotate it externally).

The durable store is **subject to legal review before shipping** (ADR-001,
risk R4). On hosts without a keyring service the key-file fallback keeps the
key beside the ciphertext under the same 0600 directory; treat that directory
as secret-bearing.

## Static bearer alternative

For clients that directly support a preconfigured bearer credential, set:

```text
HERMES_GPT_BEARER_TOKEN=<strong-random-token>
```

Static bearer authentication remains compatible with OAuth access tokens. Never put the bearer value in a URL, repository, log, prompt, or Operator audit record.

## Failure behavior

Hermes GPT fails closed when:

- OAuth is enabled but required configuration is missing;
- an enabled additional client profile (for example the Gemini Spark profile) is missing required configuration;
- the client secret is absent, malformed, or incorrect;
- the redirect URI, resource, grant type, or scope is unsupported;
- PKCE is supplied with a method other than S256 or the verifier does not match;
- an authorization code or refresh token is unknown, expired, used, or replayed;
- a refresh request attempts to increase scope;
- the dynamic-client registry is full (`/oauth/register` answers
  `429 temporarily_unavailable`) — this is bounded, not permanent: expired
  registrations are evicted by their TTL on the next registration/cleanup;
- a bounded credential store is full.

Operator and Owner policy remains independent from transport authentication. Authenticating a connector does not activate mutations, direct mode, or Owner Mode.
