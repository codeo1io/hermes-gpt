#!/usr/bin/env python3
"""Backfill routine_completion discharge markers from verifiable successor facts.

Run 46 SLO-debt repair lane (shape (a) of the census: supersede semantics).
Every marker write is gated on facts re-checked at write time by
operator_mission_runtime.supersede_mission_node:

- the node is terminal-`failed` (retried-then-failed nodes refuse);
- the successor mission is `completed` (currently or by the time of writing);
- the marker embeds the predecessor objective's SHA-256 digest, which the
  SLO probe re-verifies before honouring anything.

NO marker is written without an evidence_ref pointing at a real receipt.
Only runs with --apply; default is a dry census read.

Families (2026-10-26 census, all 30 failed routine nodes):
  exec06 -002/-003/-005(both nodes) -> successor -007 completed; -007's own
      failed first node is NOT discharged (its retry -r1 landed inside the
      SAME mission: mission-level retries are the rails' own retry lane and
      the node finally completed).
  m3-opencode -001..-005 pin-provenance-backfill -> discharged by the
      completed pin mission msn-m3-pi-dev-006 (same objective chain, PR #199).
  auto05 -001/-002/-003(both) -> NO discharge: no completed successor exists
      (the objective landed OUTSIDE the native rails via PR #203 by the
      operator); live debt until a native retry mission completes or the
      rails record an operator-anchored completion.
  nrm-cleanup -1/-2/-3 -> NO discharge: cleanup-4 completed a DIFFERENT
      objective (M-B1 production-adoption proof), not cleanup pilot tasks.
  resolver-e2e2 evidence-work -> NO discharge: objective never landed.
  promote-verify (12) -> each is discharged by the FIRST completed
      promote-verify mission created after it (per-release verification is
      moot once any later release verified end to end).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import operator_mission_runtime as oprt  # noqa: E402

DB = Path("/home/agent/.hermes/missions/missions.db")

# (mission_id, node_id, successor_mission_id, evidence_ref, reason)
DISCHARGES: list[tuple[str, str, str, str, str]] = [
    *[
        (mid, node, "msn-exec06-opencode-dev-007",
         "/home/agent/.hermes/missions/artifacts/ap-msn-exec06-opencode-dev-007-opencode-dev-hardening-r1-ad2fd07a97c7aeba/m9-merge-receipt.json",
         "hardening objective landed via successor mission -007 (PR #369 merged, CI green)")
        for mid, node in [
            ("msn-exec06-opencode-dev-002", "opencode-dev-hardening"),
            ("msn-exec06-opencode-dev-003", "opencode-dev-hardening"),
            ("msn-exec06-opencode-dev-005", "opencode-dev-hardening"),
            ("msn-exec06-opencode-dev-005", "opencode-dev-hardening-r1"),
        ]
    ],
    *[
        (mid, "pin-provenance-backfill" if mid < "msn-m3-opencode-dev-004" else "pin-provenance-backfill-v4" if mid == "msn-m3-opencode-dev-004" else "pin-provenance-backfill-v5",
         "msn-m3-pi-dev-006",
         "https://github.com/codeo1io/hermes-autonomy/pull/199",
         "pin-provenance objective landed via completed pin mission msn-m3-pi-dev-006 (PR #199 merged)")
        for mid in [
            "msn-m3-opencode-dev-001",
            "msn-m3-opencode-dev-002",
            "msn-m3-opencode-dev-003",
            "msn-m3-opencode-dev-004",
            "msn-m3-opencode-dev-005",
        ]
    ],
]


def _promote_verify_discharges(conn: sqlite3.Connection) -> list[tuple[str, str, str, str, str]]:
    """Per-release verify missions: discharge a failed/draft/cancelled one by
    the first COMPLETED verify mission created after it."""
    rows = conn.execute(
        "SELECT mission_id, created_at FROM missions "
        "WHERE mission_id LIKE 'msn-promote-verify%' AND status != 'completed' "
        "ORDER BY created_at"
    ).fetchall()
    out = []
    for mid, created in rows:
        succ = conn.execute(
            "SELECT mission_id FROM missions WHERE mission_id LIKE 'msn-promote-verify%' "
            "AND status='completed' AND created_at > ? ORDER BY created_at LIMIT 1",
            (created,),
        ).fetchone()
        if succ:
            out.append((
                mid, "verify-convergence", succ[0],
                f"https://github.com/codeo1io/hermes-conductor/actions?query=is%3Asuccess+{succ[0]}",
                "per-release verification mooted by a later completed release verify",
            ))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write markers (default: census only)")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    planned = list(DISCHARGES) + _promote_verify_discharges(conn)
    conn.close()

    written, refused, skipped = [], [], []
    for mission_id, node_id, successor, evidence, reason in planned:
        if not args.apply:
            print(f"WOULD discharge {mission_id}/{node_id} -> {successor}")
            continue
        try:
            out = oprt.supersede_mission_node(
                mission_id, node_id, successor,
                reason=reason, evidence_ref=evidence,
                hermes_root=None,
            )
            (written if out["changed"] else skipped).append(
                f"{mission_id}/{node_id}->{successor}" + (" (idempotent)" if out["idempotent"] else "")
            )
        except oprt.MissionSupersedeError as exc:
            refused.append(f"{mission_id}/{node_id}->{successor}: {exc}")
    if args.apply:
        print(json.dumps({
            "written": written, "idempotent_skipped": skipped, "refused": refused,
        }, indent=1))
    else:
        print(f"census: {len(planned)} candidate discharges (run with --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
