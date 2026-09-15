# Kanban task `owner` — consolidated spec (v1.1)

Status: **spec of record** · 2026-09-15 UTC · verified against conductor run
`30c1df938db6`, implement branch `conductor-run-30c1df938db6-implement-1`,
commit `d79e732dc8e` (8 files, +452/−8; `tests/hermes_cli/test_kanban_owner.py`
15/15 pass, re-run this session: `15 passed in 42.54s`).

Supersedes/merges: `owner-spec.md` (t_689baab7 workspace) and the t_016fd044
spec attachment (both ephemeral — this file is the checked-in canonical copy).

## 1. Semantics

`owner` = who is accountable for the outcome (person or team; accepts the
result). `assignee` = the profile whose worker executes it. `created_by` =
immutable intake provenance and the ONLY input to the `_verify_created_cards`
phantom-card guard. The three are independent: reassigning never touches
ownership; transferring ownership never touches assignee, claim state, or
failure counters. Routing-neutral by contract: the dispatcher MUST NOT read
`owner` for claim/dispatch/priority (regression-tested).

## 2. Data model (implemented, verified in kanban_db.py / kanban_db_connect.py)

- Nullable `tasks.owner TEXT`; additive migration via `_LATER_TASK_COLUMNS`;
  `""`/whitespace canonicalized to NULL (`_owner_or_none`).
- Free text — deliberately NOT profile-validated (owners may be teams).
- `create_task(owner=None)` persists `owner = created_by`; explicit owner wins.
- One-shot backfill `UPDATE tasks SET owner = created_by WHERE owner IS NULL`
  fires on FIRST column-add only; a later explicit clear is never resurrected.
- `Task.owner` optional (never in `_TASK_REQUIRED_COLUMNS`).

## 3. API contract

| Surface | Contract | State |
|---|---|---|
| `kanban_create(owner=...)` | MCP schema param, defaults to creating profile | done |
| `set_task_owner(conn, id, owner)` | transfer/clear; settable under a live claim; refused on archived (RuntimeError) or unknown (False); `""`→NULL; appends `owner_transferred {from,to}`; fires task-updated observer `("owner",)` | done (DB layer) |
| `list_tasks(owner=...)` / MCP list `owner` arg | filter by owner | done |
| Transfer surface | CLI `hermes kanban owner <id> <label>` + MCP `kanban_set_owner` | **G1 missing** |

## 4. UI touchpoints

Desktop kanban drawer, i18n strings, types: done (commit `d79e732dc8e`).
CLI `hermes kanban show` `owner:` line (show when set or when it differs from
`created_by`) and owner column in `list` output: **G2 missing**.

## 5. Edge cases

- Unowned task (`owner IS NULL`): read paths should resolve
  `effective_owner = owner ?? created_by ?? None`. **G3 missing** — live DB
  today: 777/795 tasks NULL (mixed-version window: running install's INSERT
  omits `owner`; one-shot backfill already consumed). Recommend implementing
  the read-path fallback rather than re-running backfill — new NULLs keep
  appearing until the owning branch is deployed.
- Transfer while `running`: allowed (metadata-only, next-reader visible).
- Archived: refused. Unknown id: `False`, no event.
- Owner removal: explicit clear → NULL, recorded via `owner_transferred
  {from: X, to: null}`; never auto-restored.
- Mixed-version reconciliation post-deploy (**G4**): one-time guarded
  `UPDATE tasks SET owner = created_by WHERE owner IS NULL AND created_by IS
  NOT NULL`, idempotent behind a fresh one-shot guard; explicit NULLs cleared
  pre-deploy are indistinguishable — accept (documented limitation).
- Permissions: none in v1 — owner does not restrict edits. Notifications:
  task-updated observers only. Both deferred to a v2 card if wanted at all.

## 6. Resolved open questions (from t_016fd044)

1. Event name → **`owner_transferred`** (implementation won; carries from/to).
2. Permissions/notify gating → out of scope v1.
3. Fixture-noise origin of the request cards → handled by t_58dec5f0 /
   t_da696979; probe cards + stranded run 191 cleaned up (verified done).

## 7. Acceptance criteria for remaining work (G1–G4)

1. G1: `hermes kanban owner <id> <label>` and MCP `kanban_set_owner` both call
   `set_task_owner`; tests cover transfer-under-claim, archived refusal,
   unknown id, empty→NULL.
2. G2: `kanban show` prints `owner:` when set or ≠ created_by; list output
   includes owner; round-trip tested.
3. G3: every read surface resolves effective owner via one shared helper
   (`Task.effective_owner`); NULL-owner legacy rows display creator.
4. G4: post-deploy reconciliation runs exactly once; idempotence tested.
5. Regression: dispatcher claim/dispatch byte-identical with owner set/unset.

## 8. Non-goals

Owner-based routing, permission gating on edits, owner-scoped notify filters,
re-running the first-add backfill, profile-validating owner labels.
