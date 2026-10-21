# Campaign lane (compiler → controller → lane)

Current operational guide for the campaign subsystem: compiling maintenance
campaigns into MissionPlans, driving them as a sequence of finite Missions,
and adopting campaigns durably. Design lineage labels (`AUTO-01`…`AUTO-04`,
`SCHED-02`) name the design-era slices these modules implement; this document
is the current contract.

## What a campaign is

A **campaign** is a maintenance effort larger than one Mission. It is declared
in two layers:

- a **campaign document** (`hermes.campaign/v1`, one per segment) — the
  objective, constraints, node structure, and acceptance checks for one
  finite Mission. See `operator_campaign_compiler.CAMPAIGN_SCHEMA`.
- a **campaign manifest** (`hermes.campaign-manifest/v1`) — the ordered
  segments plus inter-segment dependencies. See
  `operator_campaign_controller.MANIFEST_SCHEMA`.

## Compiler (`operator_campaign_compiler`)

`compile_campaign` turns ONE `hermes.campaign/v1` document into ONE canonical
`MissionPlan`. Compilation is deterministic and fails closed: a malformed or
contradictory campaign document is refused with a precise error, never
silently coerced into a runnable plan. The compiler never talks to peers,
never mutates state, and adds no authority of its own.

## Controller (`operator_campaign_controller`)

`campaign_controller_tick` reconciles ONE campaign per tick from its manifest:

- Its only writable surface is the durable per-campaign state document at
  `<data_root>/campaigns/<campaign_id>/state.json` (orchestration state only —
  missions and plans live in their own stores).
- Each segment becomes ONE finite Mission; a segment starts only when its
  manifest dependencies are terminal.
- Every restart re-reads the state document and re-derives every phase from
  observed truth, so a restart never mints a duplicate mission.
- The controller never approves anything: at the approval frontier it stops
  and reports; final Mission approval stays with `hermes_mission_approve`
  (Owner Mode only). It never dispatches past `high_impact` nodes.

### `approval_policy` at campaign mint

The controller stamps each minted MissionSpec's `approval_policy` using
`operator_work_class.effective_approval_policy` (the work-class policy table,
`AUTO-04`):

- `owner` (default): the Mission parks at `awaiting_approval` exactly like a
  hand-minted Mission — no automation change.
- `auto_when_evidence_verified`: the work-class table may DECLARE this policy
  at mint time only for surfaces whose class policy and evidence contract
  allow it; resolution still flows only through the owner-gated
  `hermes_mission_approve` path. A policy that the table refuses, or any
  compile failure, mints with `{"policy": "owner"}` — fail toward more human
  approval, never less. `resolve_owner_gate` itself grants no in-process
  approval authority.

See [`missions.md`](missions.md) for the Mission-side field contract.

## Lane (`operator_campaign_lane`)

The lane owns exactly ONE durable artifact: the ordered registry of campaign
manifests at `<data_root>/campaigns/lane.json` (plus its own lane state at
`<data_root>/campaigns/lane-state.json`). It adds no scheduler, no dispatch
path, and no worker process.

CLI (installed as the `hermes-gpt-campaign-lane` console script):

```
hermes-gpt-campaign-lane register <manifest_path> [--apply] [--confirm] [--hermes-root ROOT]
hermes-gpt-campaign-lane unregister <campaign_id|manifest_path> [--apply] [--confirm] [--hermes-root ROOT]
hermes-gpt-campaign-lane run [--once|--serve] [--max-ticks N] [--max-runtime S] [--idle-poll S] [--apply] [--confirm] [--hermes-root ROOT]
hermes-gpt-campaign-lane status [--hermes-root ROOT]
```

Behavior:

- `register` validates the manifest via ONE dry-run controller tick and fails
  closed — a manifest that does not validate is never registered. `--apply`
  plus `--confirm` are required for the durable write.
- `unregister` removes a campaign from the lane (containment only): the
  campaign's own state, missions, and plans are left untouched.
- `run --once` (default) performs one pass — one tick per campaign — which is
  the intended systemd-timer cadence ("one trigger per family": the lane
  timer is the single trigger). `run --serve` loops with event-cursor
  wakeups, bounded by `--max-ticks` (passes) and `--max-runtime` (seconds);
  at least one pass always runs. A missing or erroring event store degrades
  to the timer without stalling.
- `status` is read-only.
- `--hermes-root` (or `HERMES_HOME`, then `~/.hermes`) selects the data root.

## Installation

The campaign modules ship in the built wheel and sdist
(`operator_campaign_compiler`, `operator_campaign_controller`,
`operator_campaign_lane`, `operator_work_class`), and
`test_shipped_surface.py` fails the suite if a top-level module is dropped
from the `py-modules` list again.
