# infra-boundary audit manifest (2026-09-04)

This manifest is the B1 migration-input record for the hermes-infra boundary
(`hermes-infra` roadmap `.hermes/plans/agent-runner-hermes-boundary.md`, defect
B1). It lists, per repo surface, what the infra-boundary migration moved into
`hermes-infra` ownership and what this repository retains, so the
clean-bootstrap acceptance ("the host can be rebuilt from committed refs
alone") is evaluable from a committed ref of this repository.

Scope: this branch (`audit/infra-boundary`) is the audit carrier. The
migration state below is pinned from live state 2026-09-04; hermes-infra's
`check.sh` is the live verifier for every row (25 PASS / 0 DRIFT at last
measure).

## Surfaces moved to hermes-infra

| surface | hermes-infra ref | evidence |
| --- | --- | --- |
| host policy for this host (agent-runner) | `hosts/agent-runner/policy.json` | service census, unit paths, slice/env refs, managed/unmanaged classification per service id |
| this repo's systemd units (server + sidecar) | policy.json service rows `hermes-gpt-server`, `hermes-gpt-sidecar` | unit paths, `watchdog-managed class (D3)` note; deploy never writes these units |
| credential supply for this repo's services | `hosts/agent-runner/hermes-gpt/env.manifest` + `credentials/` | names-only manifest (never values); pre-repository master preserved under `~/.hermes/config-preserved/hermes-gpt/` with hash recorded in inventory.md |
| network surface register | `hosts/agent-runner/network/` | D7 binding-scope decisions with recorded exceptions (Funnel `/`) |
| deploy / check / rollback | `scripts/deploy.sh`, `scripts/check.sh`, `scripts/rollback.sh` | three-way reconcile live-vs-policy, plan-by-default, `--apply` gated |
| host-state checks | `scripts/check-*.sh` battery | hermetic; tree-battery via CI |

## Surfaces retained by this repository

| surface | retained form | boundary rule |
| --- | --- | ---
| provider/product code (hermes-gpt) | this branch + `local/custom` | product code stays in the product repo; hermes-infra never edits product files |
| unit CONTENT beyond census fields | unit files themselves | hermes-infra census observes; the watchdog owns unit health-restart transport (D3: transport-only, no config repair) |
| audit trail of the boundary itself | `docs/audit-manifest.md` (this file) | this document |

## Pinned external state (2026-09-04)

- hermes-agent `refactor/host-policy-boundary` branch tip 599d02ff15 carries
  commit 5618fcec "fix(auth): drop the HERMES_CLIPROXY_ONLY host policy from
  the product" — the in-product host policy is gone from all three sites
  (auth.py, env_loader.py, model_switch.py); the only remaining
  HERMES_CLIPROXY_ONLY references in that repo are in
  `tests/hermes_cli/test_no_host_provider_policy.py`, a regression test
  asserting the policy is inert. B1's hermes-agent side is closed.
- hermes-infra origin/main: PR #2 merge 9cfcd65; ship branch
  `ops/agent-runner-hermes-boundary` tip 6abd53d (U3+U5+U6 deliverables +
  hermetic battery U39-U58) open as PR #3.
- The hermes-gpt watchdog (`~/.hermes/scripts/hermes-gpt-watchdog.sh`) is
  transport-only per D3: config-repair scope removed; hermes-infra is the sole
  content writer of deployed config.
- `~/.hermes/.env` mode 600 (D4 executed). Funnel `/` on the alexa bridge
  remains a recorded D7 exception.

## Verification

- `hermes-infra/scripts/check.sh`: 25 PASS / 0 DRIFT / 0 ERR (2026-09-04,
  re-verified live during this manifest's authoring).
- Live credential cutover executed via deploy.sh 2026-09-04 03:02 UTC with
  ledger row in `~/.hermes/deploy-ledger.jsonl` (U6); shared-env reference
  removed from the alexa-bridge service, backup retained.

This manifest is committed to `audit/infra-boundary` so B1's "migration inputs
exist only as uncommitted state" defect is closed for this repository: every
migration input is now evaluable from a committed ref.
