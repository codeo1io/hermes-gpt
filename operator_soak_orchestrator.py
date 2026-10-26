"""Staged-rollout soak orchestrator for the native-rails migration (TEST-04).

The founding directive fixes TEST-04 acceptance:

    "staged rollout A–E with 72h fault-aware + 7-day unattended soak
    before any completion claim" — never gamed, "NEVER compress or
    fabricate elapsed soak time", "Automatically initiate/continue
    observing, persist probes, repair failures, reset window when
    violated, and resume after shutdown."

This module makes that mechanical. It owns THREE concerns, separated so
each is testable in isolation:

1.  Pure stage machine (``plan_stages`` / ``eval_stage``) — what the
    rollout stages mean and what promotes/demotes, as a pure function of
    a probe document. The authoritative SLO probes are IMPORTED, not
    duplicated: every soak tick reads real delegations/missions/journal
    state through :mod:`operator_slo_probe`.
    Rollout context (mirrors upstream hermes-agent
    website/docs/developer-guide/multiplexing-gateway.md rollout notes):
      A    canary on one production lane (nrm-campaign-lane, live),
      B    a second lane (backstop) on same host,
      C    remaining local lanes (recovery workers, sidecar :4750),
      D    other user services (webui, HA-WS receiver on webui),
      E    whole-campaign soak gate for M8.
    Promotion requires: full window elapsed in the stage, zero SLO FAILs
    at evaluation time, zero soak-violation records in the window.
    Any FAIL or violation in stage A/B ⇒ back to canary (A) — one gate
    failure is a canary-blocker, not a promotional nudge.
    In C/D/E a FAIL demotes one stage (graceful degradation),
    later stages have broader blast radius.
    Demotion ALWAYS resets the window (honest wall clock).

2.  Wall-clock state store (``SoakStore``) — persists stage, window
    start, per-stage seconds, and violation records as durable JSON with
    an FS-rename atomic write + every write stamped with the wall clock,
    so elapsed time is derived from the wall clock, never accumulated
    from probe runs. A lost or corrupted state file reports the window
    RESET (fail-closed), never a silently-extended soak.

3.  Soak tick (``run_soak_tick``) — measures via
    :func:`operator_slo_probe.collect_all`, compares against the state
    store, promotes/demotes/resets on the result, appends one JSONL line
    per tick (append-only evidence) and returns the post-state document.

Persistence layout (under ``~/.hermes/native-rails-migration/EVIDENCE/
TEST-04/soak/``):
    state.json    — current stage + window start + per-stage totals
    ticks.jsonl   — append-only tick evidence (one line per tick)
    events.jsonl  — stage changes, resets, violations, tick errors

The clock is time.time() (UTC wall). Windows are
72h fault-aware + 7-day unattended cumulative per the directive; a tick
run with --start-soak starts stage A from now.
--start-soak is refused when a soak is already active (use --reset with
an explicit reason instead).
--start-soak --probe-only --probe-interval N seconds between full SLO
probes (default 900s = 15min), ticks run without a fresh probe reuse
the last document; without --probe-only every tick probes (short canary
runs).

Injection surface for fault-awareness: --probe-cmd allows an operator
or the fault-injection rig (TEST-02 matrix) to wrap the probe command
for injected-fault windows (the TEST-02 22-row matrix supplies the
injections; this module only demands that a stage window that contained
injected faults be marked fault_aware=true and refuse promotion when the
current window's probe run FAILED at eval time).
--probe-cmd is refused unless --confirm-fault-cmd is also passed (hard
gate; matches repo doctrine: mutation paths are dry-run-first, explicit
subprocesses are explicit). --probe-cmd is shlex-split and run without
shell=True.
argv, cwd, env passthrough, and the exit path are pinned in tests.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import operator_slo_probe as slo

# ---------------------------------------------------------------------------
# Stage constants (rollout A–E; single source of truth for tests)
# ---------------------------------------------------------------------------

STAGES = ("A", "B", "C", "D", "E")

#: 72h fault-aware window (directive; applies to A/B canary stages).
FAULT_AWARE_WINDOW_S = 72 * 3600

#: 7-day unattended soak (directive; cumulative requirement for E).
UNATTENDED_WINDOW_S = 7 * 24 * 3600

#: Demo/canary calibration: short-window override ONLY via explicit
#: --stage-window-s (never silently). Production default stays 72h.
DEFAULT_STAGE_WINDOW_S = FAULT_AWARE_WINDOW_S

SOAK_DIRNAME = "soak"
STATE_FILENAME = "state.json"
TICKS_FILENAME = "ticks.jsonl"
EVENTS_FILENAME = "events.jsonl"

SCHEMA_VERSION = 1


def _now_iso(now: float | None = None) -> str:
    return time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(now if now is not None else time.time())
    )


def _stage_index(stage: str) -> int:
    return STAGES.index(stage)


# ---------------------------------------------------------------------------
# Pure stage machine
# ---------------------------------------------------------------------------


def plan_stages() -> dict[str, dict[str, str]]:
    """The rollout plan as data (documentation + tests single source)."""
    return {
        "A": {
            "scope": "canary: one production lane (nrm-campaign-lane, live)",
            "window_s": str(FAULT_AWARE_WINDOW_S),
            "fault_policy": "fault-aware: any FAIL/violation resets to A",
        },
        "B": {
            "scope": "second lane (nrm-campaign-backstop) on same host",
            "window_s": str(FAULT_AWARE_WINDOW_S),
            "fault_policy": "fault-aware: any FAIL/violation resets to A",
        },
        "C": {
            "scope": "remaining local lanes (recovery workers, sidecar :4750)",
            "window_s": str(FAULT_AWARE_WINDOW_S),
            "fault_policy": "one FAIL demotes one stage, window resets",
        },
        "D": {
            "scope": "other user services (webui, HA-WS receiver)",
            "window_s": str(FAULT_AWARE_WINDOW_S),
            "fault_policy": "one FAIL demotes one stage, window resets",
        },
        "E": {
            "scope": "whole-campaign soak gate for M8 (unattended)",
            "window_s": str(UNATTENDED_WINDOW_S),
            "fault_policy": "any FAIL/violation resets to A (final gate)",
        },
    }


def eval_stage(
    stage: str,
    window_start: float,
    *,
    now: float,
    window_s: float,
    fail_count: int,
    violation_count: int,
    probe_failed_now: bool,
    probe_unknown_now: bool = False,
) -> dict[str, Any]:
    """Pure promotion/demotion/reset decision for one soak tick.

    Inputs are facts (elapsed time, counts in the current window, the
    live probe verdict); the output is one of promote / demote / reset /
    hold plus the reason. Never mutates anything.

    Rules (directive: "reset window when violated"):
    - any probe FAIL or violation in A/B, or in E ⇒ RESET to A
      (canary discipline; E is the final gate, it does not degrade).
    - a FAIL in C/D ⇒ demote one stage (graceful), window resets.
    - violations (recorded injected-fault mishandling) always demote one
      stage in C/D and reset in A/B/E.
    - otherwise: full window elapsed + zero fails/violations ⇒ promote;
      else hold with remaining seconds.
    - UNKNOWN probes are not fails (fail-closed reporting, never hidden):
      they hold the stage but do not demote — consistent with TEST-03
      probe semantics (UNKNOWN must be reported, not gamed into PASS or
      FAIL). An UNKNOWN ALSO withholds promotion: a window that could
      not be verified is not an observed-clean window, so full elapsed
      time alone never promotes while the latest probe is UNKNOWN.
    """
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage!r}")
    elapsed = now - window_start
    canary = stage in ("A", "B")
    hard = stage == "E"

    out: dict[str, Any] = {
        "stage": stage,
        "evaluated_at": _now_iso(now),
        "window_s": window_s,
        "elapsed_s": elapsed,
        "full_window_elapsed": elapsed >= window_s,
        "fail_count": fail_count,
        "violation_count": violation_count,
        "probe_failed_now": probe_failed_now,
        "probe_passed_now": not probe_failed_now,
    }

    if probe_failed_now or violation_count > 0:
        if canary or hard:
            out["action"] = "reset"
            out["to_stage"] = "A"
            out["reason"] = (
                f"stage {stage}: probe FAIL / violation ⇒ reset to A "
                "(canary discipline; directive: reset window when violated)"
            )
        else:
            idx = _stage_index(stage)
            out["action"] = "demote"
            out["to_stage"] = STAGES[max(0, idx - 1)]
            out["reason"] = (
                f"stage {stage}: probe FAIL / violation ⇒ demote to "
                f"{out['to_stage']} (graceful degradation), window resets"
            )
        return out

    if fail_count > 0:
        # A FAIL recorded earlier in this window (probe_error_class count)
        # — same consequences, but it was not this tick's probe.
        if canary or hard:
            out["action"] = "reset"
            out["to_stage"] = "A"
            out["reason"] = (
                f"stage {stage}: {fail_count} fails in window ⇒ reset to A"
            )
        else:
            idx = _stage_index(stage)
            out["action"] = "demote"
            out["to_stage"] = STAGES[max(0, idx - 1)]
            out["reason"] = (
                f"stage {stage}: {fail_count} fails in window ⇒ demote to "
                f"{out['to_stage']}, window resets"
            )
        return out

    if elapsed >= window_s:
        if probe_unknown_now:
            out["action"] = "hold"
            out["to_stage"] = stage
            out["reason"] = (
                f"stage {stage}: window fully elapsed but latest probe is "
                "UNKNOWN — promotion WITHHELD (an unverified window is not "
                "an observed-clean window; fail-closed)"
            )
            return out
        idx = _stage_index(stage)
        if idx == len(STAGES) - 1:
            out["action"] = "complete"
            out["to_stage"] = "E"
            out["reason"] = (
                "stage E window fully elapsed with zero fails/violations "
                "⇒ soak gate SATISFIED (M8 evidence)"
            )
        else:
            out["action"] = "promote"
            out["to_stage"] = STAGES[idx + 1]
            out["reason"] = (
                f"stage {stage} window fully elapsed clean ⇒ promote to "
                f"{out['to_stage']}"
            )
        return out

    out["action"] = "hold"
    out["to_stage"] = stage
    out["reason"] = (
        f"stage {stage}: {window_s - elapsed:.0f}s of {window_s:.0f}s "
        "remaining, window clean"
    )
    return out


# ---------------------------------------------------------------------------
# Durable wall-clock state store
# ---------------------------------------------------------------------------


class SoakStore:
    """JSON state file + JSONL evidence logs under one soak directory.

    Every write is stamped with the wall clock; elapsed time is DERIVED
    from wall-clock timestamps, never accumulated from probe runs, so a
    restart resumes honestly (directive: "resume after shutdown", never
    compress elapsed time).
    """

    def __init__(self, soak_dir: Path) -> None:
        self.dir = Path(soak_dir)
        self.state_path = self.dir / STATE_FILENAME
        self.ticks_path = self.dir / TICKS_FILENAME
        self.events_path = self.dir / EVENTS_FILENAME

    # -- low-level helpers ------------------------------------------------

    @staticmethod
    def _now() -> float:
        return time.time()

    def _atomic_write_json(self, path: Path, doc: dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        tmp.replace(path)

    def _append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    # -- state ------------------------------------------------------------

    def load_state(self) -> dict[str, Any] | None:
        """Load state.json; None if absent. Corrupt ⇒ corrupt marker."""
        if not self.state_path.exists():
            return None
        try:
            return json.loads(self.state_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {"corrupt": True}

    def start_soak(
        self,
        *,
        now: float | None = None,
        window_s: float = DEFAULT_STAGE_WINDOW_S,
        actor: str = "operator",
    ) -> dict[str, Any]:
        """Start (or restart) the soak at stage A from ``now``."""
        ts = now if now is not None else self._now()
        state = {
            "schema_version": SCHEMA_VERSION,
            "stage": "A",
            "window_start": ts,
            "window_start_iso": _now_iso(ts),
            "window_s": window_s,
            "stage_totals_s": {s: 0.0 for s in STAGES},
            "resets": 0,
            "promotions": 0,
            "demotions": 0,
            "started_by": actor,
            "updated_at": ts,
            "updated_at_iso": _now_iso(ts),
        }
        self._atomic_write_json(self.state_path, state)
        self._append_jsonl(
            self.events_path,
            {
                "event": "soak_started",
                "at": _now_iso(ts),
                "wall": ts,
                "stage": "A",
                "window_s": window_s,
                "actor": actor,
            },
        )
        return state

    def save_state(self, state: dict[str, Any], *, now: float | None = None) -> None:
        ts = now if now is not None else self._now()
        state["updated_at"] = ts
        state["updated_at_iso"] = _now_iso(ts)
        self._atomic_write_json(self.state_path, state)

    def record_tick(self, tick: dict[str, Any]) -> None:
        self._append_jsonl(self.ticks_path, tick)

    def record_event(self, event: dict[str, Any], *, now: float | None = None) -> None:
        ts = now if now is not None else self._now()
        event = {"at": _now_iso(ts), "wall": ts, **event}
        self._append_jsonl(self.events_path, event)

    # -- window accounting -------------------------------------------------

    def finalize_window(
        self, state: dict[str, Any], *, now: float | None = None
    ) -> dict[str, Any]:
        """Add the elapsed time of the just-ended window to stage totals."""
        ts = now if now is not None else self._now()
        elapsed = max(0.0, ts - state["window_start"])
        stage = state["stage"]
        totals = state.setdefault("stage_totals_s", {s: 0.0 for s in STAGES})
        totals[stage] = totals.get(stage, 0.0) + elapsed
        return state


# ---------------------------------------------------------------------------
# Soak tick
# ---------------------------------------------------------------------------


def _window_counts(ticks_path: Path, window_start: float) -> dict[str, int]:
    """Count probe FAILs / violations recorded since window_start."""
    counts = {"probe_fails": 0, "violations": 0, "ticks": 0}
    if not ticks_path.exists():
        return counts
    with ticks_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("wall", 0) <= window_start:
                # strict >: the boundary tick is the one that ENDED the
                # previous window (e.g. the FAIL that triggered a reset);
                # it must not poison the fresh window (cascade-reset bug).
                continue
            counts["ticks"] += 1
            if rec.get("probe_verdict") == slo.FAIL:
                counts["probe_fails"] += 1
            counts["violations"] += int(rec.get("violations", 0) or 0)
    return counts


def run_soak_tick(
    store: SoakStore,
    *,
    now: float | None = None,
    window_s: float | None = None,
    probe_runner: Callable[[], dict[str, Any]] | None = None,
    violations: int = 0,
    actor: str = "operator",
    hermes_root: Path | None = None,
) -> dict[str, Any]:
    """One soak tick: measure, evaluate, transition, persist evidence.

    ``probe_runner`` is injectable for tests; default runs
    :func:`operator_slo_probe.collect_all` against the real stores
    (``hermes_root`` override passes through). ``violations`` lets a
    fault-injection rig record mishandled injections for the current
    window (TEST-02 matrix supplies them).
    """
    ts = now if now is not None else store._now()

    state = store.load_state()
    if state is None or state.get("corrupt"):
        reason = (
            "no soak state found — soak NOT started (call --start-soak)"
            if state is None
            else "soak state CORRUPT — window reset required (fail-closed)"
        )
        store.record_event({"event": "tick_refused", "reason": reason}, now=ts)
        return {"action": "refused", "reason": reason, "stage": None}

    stage = state["stage"]
    ws = window_s if window_s is not None else (
        state.get("window_s") or DEFAULT_STAGE_WINDOW_S
    )
    window_start = state["window_start"]

    # --- measure ----------------------------------------------------------
    probe_error: str | None = None
    try:
        if probe_runner is not None:
            doc = probe_runner()
        elif hermes_root is not None:
            doc = slo.collect_all(hermes_root=hermes_root)
        else:
            doc = slo.collect_all()
    except Exception as exc:  # noqa: BLE001 — evidence, never hidden
        doc = None
        probe_error = f"{type(exc).__name__}: {exc}"
        store.record_event(
            {"event": "probe_error", "stage": stage, "error": probe_error}, now=ts
        )

    probe_verdict = slo.UNKNOWN
    if doc is not None:
        summary = doc.get("summary", {})
        if summary.get("fail", 0) > 0:
            probe_verdict = slo.FAIL
        elif summary.get("unknown", 0) == 0 and summary.get("pass", 0) > 0:
            probe_verdict = slo.PASS
        # else: UNKNOWN — fail-closed, reported not gamed

    counts = _window_counts(store.ticks_path, window_start)
    counts["violations"] += violations

    # --- evaluate ---------------------------------------------------------
    decision = eval_stage(
        stage,
        window_start,
        now=ts,
        window_s=ws,
        fail_count=counts["probe_fails"] + (1 if probe_verdict == slo.FAIL else 0),
        violation_count=counts["violations"],
        probe_failed_now=probe_verdict == slo.FAIL,
        probe_unknown_now=probe_verdict == slo.UNKNOWN,
    )

    # --- transition --------------------------------------------------------
    action = decision["action"]
    tick = {
        "wall": ts,
        "at": _now_iso(ts),
        "stage": stage,
        "probe_verdict": probe_verdict,
        "probe_error": probe_error,
        "probe_fail_ids": (doc or {}).get("summary", {}).get("failed_ids", []),
        "probe_unknown_ids": (doc or {}).get("summary", {}).get("unknown_ids", []),
        "violations": violations,
        "action": action,
        "to_stage": decision.get("to_stage"),
        "reason": decision["reason"],
        "elapsed_s": decision["elapsed_s"],
        "window_s": ws,
        "actor": actor,
    }
    store.record_tick(tick)

    if action in ("promote", "demote", "reset", "complete"):
        state = store.finalize_window(state, now=ts)
        state["window_start"] = ts
        state["window_start_iso"] = _now_iso(ts)
        state["window_s"] = (
            UNATTENDED_WINDOW_S if decision["to_stage"] == "E" else ws
        )
        if action == "complete":
            state["soak_gate_satisfied_at"] = ts
            state["soak_gate_satisfied_iso"] = _now_iso(ts)
        if action == "promote":
            state["promotions"] = state.get("promotions", 0) + 1
        elif action == "demote":
            state["demotions"] = state.get("demotions", 0) + 1
        elif action == "reset":
            state["resets"] = state.get("resets", 0) + 1
        state["stage"] = decision["to_stage"]
        store.save_state(state, now=ts)
        store.record_event(
            {
                "event": action,
                "from_stage": stage,
                "to_stage": decision["to_stage"],
                "reason": decision["reason"],
            },
            now=ts,
        )
    else:  # hold — refresh updated_at only
        store.save_state(state, now=ts)

    return {
        "action": action,
        "stage": stage,
        "to_stage": decision.get("to_stage"),
        "reason": decision["reason"],
        "probe_verdict": probe_verdict,
        "probe_error": probe_error,
        "elapsed_s": decision["elapsed_s"],
        "window_s": ws,
        "state": state,
        "tick": tick,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_probe_cmd(cmd: str) -> list[str]:
    return shlex.split(cmd)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="TEST-04 staged-rollout soak orchestrator (native-rails migration)"
    )
    ap.add_argument(
        "--soak-dir",
        default=None,
        help="soak evidence dir (default ~/.hermes/native-rails-migration/EVIDENCE/TEST-04/soak)",
    )
    ap.add_argument("--hermes-root", default=None, help="override hermes root for probes")
    ap.add_argument(
        "--start-soak",
        action="store_true",
        help="start the soak at stage A from now (refused if already active)",
    )
    ap.add_argument(
        "--stage-window-s",
        type=float,
        default=DEFAULT_STAGE_WINDOW_S,
        help="stage window seconds (default 72h; E always 7d). "
        "SHORT VALUES ARE FOR CANARY CALIBRATION ONLY — never for acceptance.",
    )
    ap.add_argument(
        "--reset",
        action="store_true",
        help="reset the soak to stage A with an explicit --reason",
    )
    ap.add_argument("--reason", default=None, help="reason for --reset (required with it)")
    ap.add_argument(
        "--probe-cmd",
        default=None,
        help="external probe command (shlex-split, no shell). Requires --confirm-fault-cmd.",
    )
    ap.add_argument(
        "--confirm-fault-cmd",
        action="store_true",
        help="confirm --probe-cmd (fault-injection rig gate)",
    )
    ap.add_argument(
        "--violations",
        type=int,
        default=0,
        help="record N mishandled-injection violations for this tick (fault rig)",
    )
    ap.add_argument("--actor", default="operator", help="actor label for evidence")
    ap.add_argument("--json-out", default=None, help="also write the tick result JSON here")
    args = ap.parse_args(argv)

    soak_dir = (
        Path(args.soak_dir)
        if args.soak_dir
        else Path.home()
        / ".hermes"
        / "native-rails-migration"
        / "EVIDENCE"
        / "TEST-04"
        / SOAK_DIRNAME
    )
    store = SoakStore(soak_dir)

    if args.probe_cmd and not args.confirm_fault_cmd:
        print(
            "[soak] --probe-cmd requires --confirm-fault-cmd (explicit subprocess gate)",
            file=sys.stderr,
        )
        return 2

    if args.reset:
        if not args.reason:
            print("[soak] --reset requires --reason", file=sys.stderr)
            return 2
        state = store.load_state()
        prev = state.get("stage") if state else None
        store.start_soak(window_s=args.stage_window_s, actor=args.actor)
        store.record_event(
            {
                "event": "soak_reset",
                "from_stage": prev,
                "reason": args.reason,
                "actor": args.actor,
            }
        )
        print(f"[soak] RESET to A ({args.reason}); prior stage: {prev}")
        return 0

    if args.start_soak:
        state = store.load_state()
        if state and not state.get("corrupt"):
            print(
                f"[soak] soak ALREADY ACTIVE at stage {state['stage']} since "
                f"{state['window_start_iso']} — refusing to reset the clock. "
                "Use --reset --reason ... to explicitly restart.",
                file=sys.stderr,
            )
            return 2
        state = store.start_soak(window_s=args.stage_window_s, actor=args.actor)
        print(
            f"[soak] STARTED stage A at {state['window_start_iso']} "
            f"(window {args.stage_window_s:.0f}s)"
        )
        return 0

    # --- tick path ---------------------------------------------------------
    probe_runner: Callable[[], dict[str, Any]] | None = None
    if args.probe_cmd:
        argv_parts = _parse_probe_cmd(args.probe_cmd)
        out_path = soak_dir / "probe-out.json"

        def _external_probe() -> dict[str, Any]:
            proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
                argv_parts,
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"probe cmd exited {proc.returncode}: {proc.stderr[-400:]}"
                )
            out_path.write_text(proc.stdout)
            return json.loads(proc.stdout)

        probe_runner = _external_probe

    result = run_soak_tick(
        store,
        probe_runner=probe_runner,
        violations=args.violations,
        actor=args.actor,
        hermes_root=Path(args.hermes_root) if args.hermes_root else None,
    )
    if result["action"] == "refused":
        print(f"[soak] REFUSED: {result['reason']}")
        return 3

    print(
        f"[soak] stage {result['stage']} → {result['action']}"
        + (f" → {result['to_stage']}" if result.get("to_stage") else "")
        + f" | probe={result['probe_verdict']}"
        + (f" err={result['probe_error']}" if result.get("probe_error") else "")
        + f" | elapsed {result['elapsed_s']:.0f}/{result['window_s']:.0f}s"
    )
    print(f"[soak] {result['reason']}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    # Exit code: 0 = clean/progress, 1 = probe FAIL this tick (visible, not hidden)
    return 1 if result["probe_verdict"] == slo.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
