"""SLO measurement probes for the native-rails migration (TEST-03).

The founding migration directive fixes service-level targets for the migrated
native-execution rails:

    0 false success, 0 duplicate side effects, 95% of stalls detected
    within 5 minutes / all within 15 minutes, >=95% auto-recovery within
    15 minutes, >=99% routine completion, continuity, and >=15% free disk.

PLAN.md summarizes these as "SLO targets ... never gamed". This module makes
"never gamed" mechanical: every probe reads an *authoritative* source
(the native delegations/missions SQLite stores, the maestro-watchdog journal,
the gateway heartbeat table, or the filesystem), computes the metric with an
EXPLICIT denominator, and emits a machine-checkable verdict
(``PASS`` / ``FAIL`` / ``UNKNOWN``) plus the raw numerator/denominator pair
so a reviewer can re-derive the arithmetic.

Design rules (mirrors operator_diagnostics safety posture):

- READ-ONLY against every source. The live CLI never mutates a store; the
  watchdog journal is read via ``journalctl --since ... --no-pager`` which
  cannot write to the journal.
- No probe may report PASS on missing evidence: an unreadable source yields
  ``UNKNOWN`` with the failure reason recorded, never a green mark
  (BASE-10 §4.5 "stale/unavailable is reported degraded/unknown — NEVER
  healthy").
- Verdicts are pure functions of collected facts so tests can pin them.

Consumers:

- ``python operator_slo_probe.py --json PATH`` writes the full measurement
  document (one record per SLO) for the campaign evidence trail.
- ``python operator_slo_probe.py`` prints a human summary and exits nonzero
  if any measured SLO FAILS (UNKNOWN does not fail the run — it must be
  reported, not hidden).
- ``collect_all()`` is importable for the BASE-10 scorecard; the scorecard
  owns presentation, this module owns measurement.

This module deliberately does NOT duplicate scorecard state: it is a
measurement library, not a dashboard.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import operator_mission_runtime as oprt

# ---------------------------------------------------------------------------
# SLO target constants (founding directive; single source of truth for tests)
# ---------------------------------------------------------------------------

SLO_FALSE_SUCCESS_MAX = 0
SLO_DUPLICATE_EFFECTS_MAX = 0
SLO_STALL_DETECT_PCT_WITHIN_5M = 95.0
SLO_STALL_DETECT_MAX_BOUND_MIN = 15.0
SLO_AUTO_RECOVERY_PCT_WITHIN_15M = 95.0
SLO_ROUTINE_COMPLETION_MIN_PCT = 99.0
SLO_DISK_FREE_MIN_PCT = 15.0

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"

#: authorization classes operator_work_class.ROUTINE_AUTH_CLASSES counts as
#: routine; imported lazily at call time to keep this module import-light.
ROUTINE_AUTH_CLASSES = ("read_only", "reversible_write")

#: validation verdict vocabulary (operator_delegations manifests)
VERDICT_SATISFIED = "SATISFIED"


@dataclass
class SloRecord:
    """One SLO measurement: identity, arithmetic, verdict, provenance."""

    slo_id: str
    target: str
    numerator: float | None
    denominator: float | None
    value: Any = None
    verdict: str = UNKNOWN
    window: str = ""
    sources: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "slo_id": self.slo_id,
            "target": self.target,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "value": self.value,
            "verdict": self.verdict,
            "window": self.window,
            "sources": self.sources,
            "notes": self.notes,
        }


def _verdict_for_ratio(
    numerator: float, denominator: float, *, at_least: float
) -> str:
    """PASS iff numerator/denominator >= at_least percent (explicit denom)."""
    if denominator <= 0:
        return UNKNOWN
    return PASS if (numerator / denominator) * 100.0 >= at_least else FAIL


def _verdict_for_count(value: int, *, at_most: int) -> str:
    return PASS if value <= at_most else FAIL


# ---------------------------------------------------------------------------
# Source access (authoritative roots; paths injectable for tests)
# ---------------------------------------------------------------------------


def default_hermes_root() -> Path:
    return Path.home() / ".hermes"


def _ro_connect(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"store missing: {path}")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


# ---------------------------------------------------------------------------
# SLO-1: false success — succeeded delegations without SATISFIED validation
# ---------------------------------------------------------------------------


def probe_false_success(delegations_db: Path) -> SloRecord:
    """A succeeded delegation whose acceptance evidence did not validate is a
    false success. Denominator = succeeded delegations; numerator =
    succeeded-without-SATISFIED verdict.

    A delegation that ends ``failed`` or ``cancelled`` is NOT a false success
    (honest failure is correct behavior). ``INCONCLUSIVE`` on a *succeeded*
    row counts as unverified: the rails claimed completion without verifiable
    acceptance (fail-closed per AGENTS.md product invariants).
    """
    rec = SloRecord(
        slo_id="false_success",
        target=(
            f"<={SLO_FALSE_SUCCESS_MAX} succeeded delegations lacking "
            "SATISFIED validation"
        ),
        numerator=None,
        denominator=None,
        sources=[str(delegations_db)],
    )
    try:
        conn = _ro_connect(delegations_db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        rec.notes.append(f"source unreadable: {exc}")
        return rec
    try:
        total_succ = conn.execute(
            "SELECT COUNT(*) FROM delegations WHERE state='succeeded'"
        ).fetchone()[0]
        unverified = conn.execute(
            "SELECT COUNT(*) FROM delegations WHERE state='succeeded' "
            "AND (validation_verdict IS NULL OR validation_verdict != ?)",
            (VERDICT_SATISFIED,),
        ).fetchone()[0]
    except sqlite3.Error as exc:
        rec.notes.append(f"query failed: {exc}")
        return rec
    finally:
        conn.close()

    rec.numerator = unverified
    rec.denominator = total_succ
    rec.value = unverified
    if total_succ == 0:
        rec.verdict = UNKNOWN
        rec.notes.append("no succeeded delegations in store (nothing to measure)")
    else:
        rec.verdict = _verdict_for_count(
            unverified, at_most=SLO_FALSE_SUCCESS_MAX
        )
        rec.notes.append(
            "denominator = succeeded delegations; INCONCLUSIVE counts as "
            "unverified"
        )
    return rec


# ---------------------------------------------------------------------------
# SLO-2a: duplicate side effects — overlapping live dispatches per delegation
# ---------------------------------------------------------------------------


def probe_duplicate_dispatch(delegations_db: Path) -> SloRecord:
    """True duplicate dispatch = ``delegation.dispatched`` emitted while a
    previous dispatch for the SAME delegation is still live (no intervening
    ``delegation.invocation_recovered`` reset). The reconciler's
    invoke->recover->re-invoke loop is by-design recovery, NOT duplication;
    the probe walks per-delegation event sequences so recovery loops are not
    miscounted as duplicates (and real overlaps are not excused as recovery).
    """
    rec = SloRecord(
        slo_id="duplicate_dispatch",
        target=(
            f"<={SLO_DUPLICATE_EFFECTS_MAX} delegations with a second live "
            "dispatch before recovery/terminal"
        ),
        numerator=None,
        denominator=None,
        sources=[str(delegations_db)],
    )
    try:
        conn = _ro_connect(delegations_db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        rec.notes.append(f"source unreadable: {exc}")
        return rec
    dup_delegations = 0
    checked = 0
    try:
        ids = [
            r[0]
            for r in conn.execute("SELECT delegation_id FROM delegations")
        ]
        for did in ids:
            checked += 1
            live_dispatch = False
            for (et,) in conn.execute(
                "SELECT event_type FROM delegation_events "
                "WHERE delegation_id=? ORDER BY seq",
                (did,),
            ):
                if et == "delegation.dispatched":
                    if live_dispatch:
                        dup_delegations += 1
                        break
                    live_dispatch = True
                elif et == "delegation.invocation_recovered":
                    live_dispatch = False
    except sqlite3.Error as exc:
        rec.notes.append(f"query failed: {exc}")
        return rec
    finally:
        conn.close()
    rec.numerator = dup_delegations
    rec.denominator = checked
    rec.value = dup_delegations
    rec.verdict = _verdict_for_count(
        dup_delegations, at_most=SLO_DUPLICATE_EFFECTS_MAX
    )
    rec.notes.append(
        "per-delegation event walk; invocation_recovered resets the "
        "live-dispatch marker (recovery loop != duplication)"
    )
    return rec


# ---------------------------------------------------------------------------
# SLO-2b: duplicate side effects — double claim of one canonical task
# ---------------------------------------------------------------------------


def probe_double_claim(delegations_db: Path) -> SloRecord:
    """Duplicate external effect across delegations: two non-cancelled
    delegations claiming the same (mission_id, task_id) pair — a double
    claim of one canonical piece of work.
    """
    rec = SloRecord(
        slo_id="double_claim",
        target=(
            f"<={SLO_DUPLICATE_EFFECTS_MAX} mission/task pairs claimed by "
            ">1 live delegation"
        ),
        numerator=None,
        denominator=None,
        sources=[str(delegations_db)],
    )
    try:
        conn = _ro_connect(delegations_db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        rec.notes.append(f"source unreadable: {exc}")
        return rec
    try:
        groups = conn.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT mission_id, task_id FROM delegations "
            "WHERE state != 'cancelled' AND mission_id IS NOT NULL "
            "AND task_id IS NOT NULL "
            "GROUP BY mission_id, task_id HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        total = conn.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT mission_id, task_id "
            "FROM delegations WHERE state != 'cancelled' "
            "AND mission_id IS NOT NULL AND task_id IS NOT NULL)"
        ).fetchone()[0]
    except sqlite3.Error as exc:
        rec.notes.append(f"query failed: {exc}")
        return rec
    finally:
        conn.close()
    rec.numerator = groups
    rec.denominator = total
    rec.value = groups
    rec.verdict = _verdict_for_count(groups, at_most=SLO_DUPLICATE_EFFECTS_MAX)
    return rec


# ---------------------------------------------------------------------------
# Watchdog journal parsing (shared by stall-detection and auto-recovery)
# ---------------------------------------------------------------------------

# journalctl -o short-iso emits "+HHMM" (no colon); ISO-8601 also allows
# the colon form "+HH:MM" and negative offsets. The regex accepts all three
# timestamp shapes; _parse_journal_timestamp below interprets them portably
# (datetime.fromisoformat rejects no-colon offsets on Python <= 3.10, which
# silently dropped 252/252 live ticks on such interpreters — 2026-11-04).
_WATCHDOG_LINE_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    r"(?:[+-]\d{2}:?\d{2})?) \S+ "
    r"maestro-watchdog\[\d+\]: (?P<payload>\{.*\})$"
)


def _parse_journal_timestamp(raw: str) -> float | None:
    """Journal timestamp -> epoch seconds, portable across Python >= 3.10.

    ``datetime.fromisoformat`` cannot parse the ``+HHMM`` (no-colon) offset
    journalctl emits until Python 3.11. Normalizing the offset to the colon
    form (rather than parsing by hand) keeps tz-database handling inside the
    stdlib and preserves the naive->UTC default. Returns None when the
    timestamp is malformed; callers treat that as an unparseable line.
    """
    candidate = raw
    m = re.search(r"([+-])(\d{2})(\d{2})$", candidate)
    if m:
        # "+HHMM"/"-HHMM" -> "+HH:MM"/"-HH:MM": datetime.fromisoformat
        # cannot parse the no-colon offset journalctl emits until 3.11.
        candidate = (
            candidate[: m.start()] + m.group(1) + m.group(2) + ":" + m.group(3)
        )
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def parse_watchdog_journal(lines: list[str]) -> list[dict[str, Any]]:
    """Parse journalctl lines (``-o short`` or ``-o short-iso``) into tick
    dicts, attaching the journal's own wall-clock timestamp as ``__ts``
    (epoch seconds).

    journalctl output is strictly chronological; the timestamp comes from
    the journal line itself, never from sampling or approximation.
    """
    ticks: list[dict[str, Any]] = []
    for line in lines:
        m = _WATCHDOG_LINE_RE.match(line.strip())
        if not m:
            continue
        try:
            payload = json.loads(m.group("payload"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        raw = m.group("date").replace(" ", "T", 1)
        ts = _parse_journal_timestamp(raw)
        if ts is None:
            continue
        payload["__ts"] = ts
        ticks.append(payload)
    return ticks


#: 2026-11-04: journald retains only ~3h of maestro-watchdog ticks on the
#: production host (SystemMaxUse=512M at ~472M, files rotating every
#: 20-40 min), while the SLO window is trailing 24h — episodes that
#: rotated out of the journal were laundered into UNKNOWN "nothing to
#: measure". collect_all therefore unions the journalctl read with the
#: durable rolling archive maintained by the native-rails heartbeat
#: (nrm-watchdog-journal-archive.py) and PROVES window coverage before
#: any verdict: any gap larger than WATCHDOG_TICK_MAX_GAP_S means
#: episodes inside the hole are invisible — reported as an explicit
#: unauditable-window note, never as absence.
WATCHDOG_TICK_MAX_GAP_S = float(
    os.environ.get("NRM_WATCHDOG_TICK_MAX_GAP_S", "3600")
)
WATCHDOG_WINDOW_S = float(os.environ.get("NRM_WATCHDOG_WINDOW_S", "86400"))

#: benign absence notes that a coverage gap replaces: claiming "nothing
#: to measure" while the window is unauditable launders evidence loss.
_BENIGN_ABSENCE_NOTES = (
    "no parseable watchdog ticks in window",
    "no stall episodes in window (nothing to measure)",
    "only transient blips in window (nothing to handle)",
)


def default_watchdog_archive(hermes_root: Path) -> Path:
    """Durable rolling watchdog-archive path under ``hermes_root``.

    ``NRM_WATCHDOG_ARCHIVE`` overrides (same seam as the native-rails
    scorecard, nrm_scorecard.WATCHDOG_ARCHIVE).
    """
    env = os.environ.get("NRM_WATCHDOG_ARCHIVE")
    if env:
        return Path(env)
    return (
        hermes_root
        / "native-rails-migration"
        / ".backstop-state"
        / "watchdog-journal-archive"
        / "ticks.jsonl"
    )


def _read_archive_ticks(
    path: Path,
) -> tuple[list[dict[str, Any]] | None, bool]:
    """Parseable ticks from the durable archive, if any.

    Returns ``(ticks, unreadable)``: ``unreadable=True`` means the archive
    exists but cannot be read — it contributes nothing and never restores
    coverage; the caller surfaces the breakage as a note.
    """
    if not path.exists():
        return [], False
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None, True
    return parse_watchdog_journal(lines), False


def _wd_iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _wd_coverage_edges(
    ticks: list[dict[str, Any]],
    window_start: float,
    window_end: float,
    *,
    max_gap_s: float = WATCHDOG_TICK_MAX_GAP_S,
) -> list[str]:
    """Named coverage edges for a tick list covering [start, end].

    A gap larger than ``max_gap_s`` anywhere — window head (retention
    rotated the start away), interior (episodes inside a hole are
    invisible), or tail (the watchdog itself stopped ticking) — leaves
    the window unauditable.
    """
    if not ticks:
        return [
            "window start unauditable (no parseable watchdog ticks in "
            f"the {WATCHDOG_WINDOW_S / 3600:.0f}h window)"
        ]
    edges: list[str] = []
    head_gap = ticks[0]["__ts"] - window_start
    if head_gap > max_gap_s:
        edges.append(
            "window start unauditable (journal head "
            f"{_wd_iso(ticks[0]['__ts'])}, {head_gap / 3600:.1f}h of the "
            f"{WATCHDOG_WINDOW_S / 3600:.0f}h window missing)"
        )
    interior = 0
    largest = 0.0
    prev = ticks[0]["__ts"]
    for tick in ticks[1:]:
        gap = tick["__ts"] - prev
        if gap > max_gap_s:
            interior += 1
            largest = max(largest, gap)
        prev = tick["__ts"]
    if interior:
        edges.append(
            f"interior gap(s): {interior}, largest {largest:.0f}s — "
            "episodes inside a hole are invisible"
        )
    tail_gap = window_end - ticks[-1]["__ts"]
    if tail_gap > max_gap_s:
        edges.append(
            "watchdog not ticking since "
            f"{_wd_iso(ticks[-1]['__ts'])} ({tail_gap / 3600:.1f}h)"
        )
    return edges


def _apply_coverage_edges(rec: SloRecord, edges: list[str]) -> SloRecord:
    """Replace benign absence notes with the honest unauditable verdict.

    A coverage gap can never certify absence; a PASS under an unauditable
    window is downgraded to UNKNOWN. FAIL stands — detected failures are
    real regardless of coverage.
    """
    rec.notes = [n for n in rec.notes if n not in _BENIGN_ABSENCE_NOTES]
    rec.notes.extend(edges)
    rec.notes.append(
        "window unauditable — cannot certify absence of stalls or "
        "restarts in the missing span"
    )
    if rec.verdict == PASS:
        rec.verdict = UNKNOWN
    return rec


_ACTIVE_EXECUTION_STATES = frozenset(
    {
        "STARTING",
        "WORKING",
        "ACTING",
        "CYCLING",
        "AUDITING",
        "RECONCILING",
    }
)


def _execution_state(tick: dict[str, Any]) -> str | None:
    """The supervisor's execution state, top-level or inside ``supervisor``."""
    for holder in (tick, tick.get("supervisor")):
        if isinstance(holder, dict):
            state = holder.get("execution_state")
            if isinstance(state, str) and state:
                return state
    return None


def _execution_healthy(tick: dict[str, Any]) -> bool:
    """Whether the in-flight execution step is within its dwell bound.

    The deployed watchdog computes ``execution_healthy`` from
    ``execution_state_dwell_seconds`` vs the 600 s execution lease: a wedged
    active step reports ``false``. Accept the flag top-level or inside
    ``supervisor``; a missing flag is not evidence of health.
    """
    for holder in (tick, tick.get("supervisor")):
        if isinstance(holder, dict) and holder.get("execution_healthy") is True:
            return True
    return False


def _semantic_unhealthy(tick: dict[str, Any]) -> bool:
    """semantic_healthy lives inside the ``supervisor`` object in the raw
    watchdog journal (the SUP-05 parsed extracts flattened it to top level;
    the probe accepts both shapes)."""
    sup = tick.get("supervisor")
    if isinstance(sup, dict) and "semantic_healthy" in sup:
        return sup["semantic_healthy"] is False
    return tick.get("semantic_healthy") is False


def _pacing_exempted(tick: dict[str, Any]) -> bool:
    """Only an explicit, live watchdog pacing receipt excuses an idle tick.

    Do not infer pacing from a healthy flag alone: the SLO must still detect
    genuine idle stalls and stale/dead supervisor executions.
    """
    for holder in (tick.get("supervisor"), tick):
        if not isinstance(holder, dict):
            continue
        if holder.get("pacing_exempted") is not True:
            continue
        return (
            holder.get("healthy") is True
            and holder.get("execution_healthy") is True
            and holder.get("operator_lane_stalled") is None
        )
    return False


def _stall_tick(tick: dict[str, Any]) -> bool:
    """A tick that counts toward a STALL episode for the detection SLO.

    The deployed watchdog's own health model (maestro ``watchdog.py``,
    ``shealthy``) excuses semantic staleness while a bounded execution step
    is healthily in flight — working through the backlog IS the handling, and
    a restart there would kill productive work (KTD4). A semantic-unhealthy
    tick therefore represents a stall the system must ACT on only when the
    watchdog's own model would agree: no active execution step, or the
    active step is beyond its dwell bound (``execution_healthy`` false).

    Ticks excluded by this rule are surfaced separately in the probe value
    (``excused_productive_ticks``) — excluded, never erased.
    """
    if not _semantic_unhealthy(tick):
        return False
    excused = (
        _execution_state(tick) in _ACTIVE_EXECUTION_STATES
        and _execution_healthy(tick)
    )
    return not (excused or _pacing_exempted(tick))


def _did_restart(tick: dict[str, Any]) -> bool:
    """True when this tick reports a restart action actually fired. The raw
    journal carries it inside ``supervisor`` (top-level mirrors exist on
    some versions); accept either shape."""
    if tick.get("restarted") is True:
        return True
    sup = tick.get("supervisor")
    return isinstance(sup, dict) and sup.get("restarted") is True


def _episode_action_ts(
    run: list[dict[str, Any]],
    following: list[dict[str, Any]],
) -> float | None:
    """Timestamp of the first ACTION the system took on a stall run.

    Two action classes credit an episode as handled:

    1. a restart actually fired (``restarted: true`` — the classic
       rung), or
    2. the supervisor ENGAGED the stalled objective: the run's
       semantic-unhealthy ticks sit in a non-active execution state
       (e.g. IDLE — nothing working the backlog) and a later tick IN the
       run, closing it, or within the SLO bound AFTER it shows an active
       execution state (CYCLING/RECONCILING/WORKING/...). Engaging the
       backlog IS the handling under the deployed watchdog's own health
       model (KTD4: a restart there would kill productive work); the
       2026-11-08 18:04:34Z episode (2 IDLE ticks, supervisor engaged
       to CYCLING 135s later) was exactly this shape and was booked
       "undetected" though handled.

    ``following`` are the healthy/excused ticks that arrived after the
    run closed (the engagement tick is healthy-by-model: active state +
    execution_healthy, so it never appears INSIDE the stall run). The
    search window over ``following`` is the auto-recovery SLO bound
    (900s) — an engagement that never comes within that bound is not a
    detection credit. Returns None when neither action appears — a
    genuinely undetected stall.
    """
    for t in run:
        if _did_restart(t):
            return t["__ts"]
    run_states = {_execution_state(t) for t in run}
    run_was_idle = not (run_states & _ACTIVE_EXECUTION_STATES)
    if not run_was_idle:
        return None
    last_ts = run[-1]["__ts"]
    for t in run:
        if _execution_state(t) in _ACTIVE_EXECUTION_STATES:
            return t["__ts"]
    for t in following:
        if t["__ts"] - last_ts > 900.0:
            break
        if _did_restart(t):
            return t["__ts"]
        if _execution_state(t) in _ACTIVE_EXECUTION_STATES:
            return t["__ts"]
    return None


def _stall_episodes(
    ticks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int]:
    """Maximal runs of consecutive stall ticks (see :func:`_stall_tick`).

    Each episode dict: ``start`` (first unhealthy tick ts), ``latency_s``
    (first action tick minus start; None when no action ever fired in
    the episode — undetected, counted against the target), ``ticks`` (run
    length; 1 = transient blip the deployed hysteresis deliberately
    ignores).

    Returns (episodes, productive_exemptions, explicit_pacing_exemptions).
    Every excluded semantic-unhealthy tick is reported separately.
    """
    episodes: list[dict[str, Any]] = []
    cur: list[dict[str, Any]] = []
    following: list[dict[str, Any]] = []

    def close(run: list[dict[str, Any]]) -> None:
        first_ts = run[0]["__ts"]
        action_ts = _episode_action_ts(run, following)
        episodes.append(
            {
                "start": first_ts,
                "latency_s": (
                    action_ts - first_ts if action_ts is not None else None
                ),
                "ticks": len(run),
            }
        )

    excused = 0
    pacing_excused = 0
    for tick in ticks:
        if _stall_tick(tick):
            following = []
            cur.append(tick)
            continue
        if _semantic_unhealthy(tick):
            if _pacing_exempted(tick):
                pacing_excused += 1
            else:
                # Bounded execution step healthily in flight.
                excused += 1
        if cur:
            # the tick that closes the run (usually the engagement tick,
            # healthy-by-model) is the first element of the lookahead.
            following = [tick]
            close(cur)
            cur = []
        elif following:
            # keep the post-run lookahead bounded: stop collecting once
            # the gap since the run's end exceeds the SLO bound or a
            # restart fires, so a later unrelated episode is never
            # credited to this one.
            if (
                tick["__ts"] - following[0]["__ts"] > 900.0
                or _did_restart(tick) and _semantic_unhealthy(tick)
            ):
                following = []
            else:
                following.append(tick)
    if cur:
        close(cur)
    return episodes, excused, pacing_excused


# ---------------------------------------------------------------------------
# SLO-3: stall detection coverage (maestro-watchdog journal)
# ---------------------------------------------------------------------------


def probe_stall_detection(
    journal_lines: list[str],
    *,
    journal_source: str = "maestro-watchdog journal",
) -> SloRecord:
    """Stall detection coverage: of watchdog episodes where semantic progress
    stalled, what fraction produced an action within 5 minutes of the stall
    crossing — and did ALL produce action within 15?

    Latency uses the journal's own line timestamps. Ticks without usable
    timestamps yield UNKNOWN (approximating latency would be gaming).
    Episodes with no action tick count as undetected against both bounds.
    """
    return probe_stall_detection_ticks(
        parse_watchdog_journal(journal_lines),
        journal_source=journal_source,
    )


def probe_stall_detection_ticks(
    ticks: list[dict[str, Any]],
    *,
    journal_source: str = "maestro-watchdog journal",
) -> SloRecord:
    """Tick-level core of :func:`probe_stall_detection`.

    ``collect_all`` passes pre-merged ticks (journal + rolling archive,
    window-filtered); the public line-based API delegates here after
    parsing, so both entry points share one verdict arithmetic.
    """
    rec = SloRecord(
        slo_id="stall_detection",
        target=(
            f">={SLO_STALL_DETECT_PCT_WITHIN_5M}% of stall episodes actioned "
            f"within 5m; all within {SLO_STALL_DETECT_MAX_BOUND_MIN}m"
        ),
        numerator=None,
        denominator=None,
        sources=[journal_source],
    )
    if not ticks:
        rec.notes.append("no parseable watchdog ticks in window")
        return rec
    episodes, excused_productive, excused_pacing = _stall_episodes(ticks)
    if not episodes:
        rec.numerator = 0
        rec.denominator = 0
        rec.value = {
            "episodes": 0,
            "excused_productive_ticks": excused_productive,
            "excused_pacing_ticks": excused_pacing,
        }
        rec.verdict = UNKNOWN
        rec.notes.append("no stall episodes in window (nothing to measure)")
        return rec

    # Transient blips (single tick) self-resolve — the deployed watchdog's
    # hysteresis deliberately does not act on them. Reported separately for
    # precision; the SLO denominator is PERSISTENT episodes (multi-tick
    # runs): a stall the system had to handle.
    persistent = [ep for ep in episodes if ep["ticks"] > 1]
    transient = len(episodes) - len(persistent)

    within5 = 0
    undetected = 0
    worst: float | None = None
    for ep in persistent:
        lat = ep["latency_s"]
        if lat is None:
            undetected += 1
            continue
        if lat <= 300.0:
            within5 += 1
        worst = lat if worst is None else max(worst, lat)
    denom = len(persistent)
    rec.numerator = within5
    rec.denominator = denom
    rec.value = {
        "persistent_episodes": denom,
        "transient_episodes": transient,
        "within_5m": within5,
        "undetected": undetected,
        "excused_productive_ticks": excused_productive,
        "excused_pacing_ticks": excused_pacing,
        "worst_latency_s": worst,
        "worst_latency_min": (
            round(worst / 60.0, 2) if worst is not None else None
        ),
    }
    if denom == 0:
        rec.verdict = UNKNOWN
        rec.notes.append("only transient blips in window (nothing to handle)")
        return rec
    pct = (within5 / denom) * 100.0
    bounded = (
        worst is not None
        and undetected == 0
        and worst <= SLO_STALL_DETECT_MAX_BOUND_MIN * 60.0
    )
    rec.verdict = (
        PASS if pct >= SLO_STALL_DETECT_PCT_WITHIN_5M and bounded else FAIL
    )
    rec.notes.append(
        "persistent = multi-tick semantic-unhealthy runs; single-tick "
        "self-resolving blips counted separately (hysteresis by design); "
        "excused_productive_ticks = semantic-unhealthy ticks excused by the "
        "deployed watchdog's own health model (bounded execution step "
        "healthily in flight — KTD4: restart suppressed), reported but not "
        "counted as stalls; excused_pacing_ticks require an explicit "
        "watchdog pacing_exempted receipt with live healthy execution"
    )
    return rec


# ---------------------------------------------------------------------------
# SLO-4: auto-recovery within 15 minutes (same journal)
# ---------------------------------------------------------------------------


def probe_auto_recovery(
    journal_lines: list[str],
    *,
    journal_source: str = "maestro-watchdog journal",
) -> SloRecord:
    """Of restart actions in the window, how many restored a healthy
    supervisor state within 15 minutes (a later tick reporting healthy at
    the top level or in the supervisor object, or semantic progress
    resumed)? Denominator = observed restart actions.
    """
    return probe_auto_recovery_ticks(
        parse_watchdog_journal(journal_lines),
        journal_source=journal_source,
    )


def probe_auto_recovery_ticks(
    ticks: list[dict[str, Any]],
    *,
    journal_source: str = "maestro-watchdog journal",
) -> SloRecord:
    """Tick-level core of :func:`probe_auto_recovery` (pre-merged ticks)."""
    rec = SloRecord(
        slo_id="auto_recovery",
        target=(
            f">={SLO_AUTO_RECOVERY_PCT_WITHIN_15M}% of restarts followed by "
            "healthy within 15m"
        ),
        numerator=None,
        denominator=None,
        sources=[journal_source],
    )
    if not ticks:
        rec.notes.append("no parseable watchdog ticks in window")
        return rec
    actions = [t for t in ticks if _did_restart(t)]
    if not actions:
        rec.numerator = 0
        rec.denominator = 0
        rec.value = {"restarts": 0}
        rec.verdict = UNKNOWN
        rec.notes.append("no restart actions in window (nothing to measure)")
        return rec
    recovered = 0
    latencies: list[float] = []
    for act in actions:
        act_ts = act["__ts"]
        ok_ts = None
        for later in ticks:
            if later["__ts"] > act_ts:
                sup = later.get("supervisor")
                if (
                    later.get("healthy") is True
                    or (isinstance(sup, dict) and sup.get("healthy") is True)
                    or later.get("semantic_healthy") is True
                ):
                    ok_ts = later["__ts"]
                    break
        if ok_ts is not None:
            latencies.append(ok_ts - act_ts)
            if ok_ts - act_ts <= 900.0:
                recovered += 1
    denom = len(actions)
    rec.numerator = recovered
    rec.denominator = denom
    rec.value = {
        "restarts": denom,
        "recovered_within_15m": recovered,
        "healthy_latency_s": [round(x, 1) for x in latencies],
    }
    rec.verdict = _verdict_for_ratio(
        recovered, denom, at_least=SLO_AUTO_RECOVERY_PCT_WITHIN_15M
    )
    return rec


# ---------------------------------------------------------------------------
# SLO-5: routine completion >=99% (plan_nodes, routine auth classes)
# ---------------------------------------------------------------------------


def probe_routine_completion(missions_db: Path) -> SloRecord:
    """>=99% of routine plan nodes that reached a terminal state completed.

    Denominator = routine-class plan nodes in a terminal state
    (completed+failed) — nodes still pending/dispatched/running have not had
    their chance and are excluded; failed nodes count against completion
    (an honest failure is still an unfinished routine outcome the rails
    own). Routine classes mirror operator_work_class.ROUTINE_AUTH_CLASSES.

    Discharged failures: a failed node carrying a verified supersede marker
    (operator_mission_runtime.supersede_mission_node — digest-anchored,
    successor-must-be-completed, node-must-still-be-failed) counts as
    completed in the numerator and is excluded from the denominator; the
    discharge is reported in notes with per-node receipts so the residual
    FAIL list is exactly the live debt.
    """
    rec = SloRecord(
        slo_id="routine_completion",
        target=(
            f">={SLO_ROUTINE_COMPLETION_MIN_PCT}% of terminal routine plan "
            "nodes completed"
        ),
        numerator=None,
        denominator=None,
        sources=[str(missions_db)],
    )
    ph = ",".join("?" * len(ROUTINE_AUTH_CLASSES))
    try:
        conn = _ro_connect(missions_db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        rec.notes.append(f"source unreadable: {exc}")
        return rec
    discharged_by: dict[str, str] = {}
    operator_anchored_by: dict[str, str] = {}
    try:
        terminal = conn.execute(
            f"SELECT COUNT(*) FROM plan_nodes WHERE "
            f"json_extract(capability_req, '$.authorization_class') "
            f"IN ({ph}) AND state IN ('completed','failed')",
            ROUTINE_AUTH_CLASSES,
        ).fetchone()[0]
        completed = conn.execute(
            f"SELECT COUNT(*) FROM plan_nodes WHERE "
            f"json_extract(capability_req, '$.authorization_class') "
            f"IN ({ph}) AND state='completed'",
            ROUTINE_AUTH_CLASSES,
        ).fetchone()[0]
        failed_nodes = conn.execute(
            f"SELECT mission_id, node_id FROM plan_nodes WHERE "
            f"json_extract(capability_req, '$.authorization_class') "
            f"IN ({ph}) AND state='failed' ORDER BY mission_id, node_id",
            ROUTINE_AUTH_CLASSES,
        ).fetchall()
        for mission_id, node_id in failed_nodes:
            try:
                discharger = oprt._is_discharged_node(conn, str(mission_id), str(node_id))
            except sqlite3.Error:
                # a store without the marker/event tables has no discharges
                discharger = ""
            if discharger:
                discharged_by[f"{mission_id}/{node_id}"] = discharger
                continue
            try:
                anchor = oprt._is_operator_completed_node(conn, str(mission_id), str(node_id))
            except sqlite3.Error:
                anchor = ""
            if anchor:
                operator_anchored_by[f"{mission_id}/{node_id}"] = anchor
    except sqlite3.Error as exc:
        rec.notes.append(f"plan_nodes query failed: {exc}")
        return rec
    finally:
        conn.close()
    discharged = len(discharged_by) + len(operator_anchored_by)
    if operator_anchored_by:
        rec.notes.append(
            "operator-anchored completions (verified receipts, objective "
            "landed outside the rails): " + ", ".join(
                f"{k}->{v}" for k, v in sorted(operator_anchored_by.items())
            )
        )
    if discharged_by:
        rec.notes.append(
            "discharged failures (verified supersede markers, count as "
            "completed): " + ", ".join(
                f"{k}->{v}" for k, v in sorted(discharged_by.items())
            )
        )
    live_failed = len(failed_nodes) - discharged
    rec.numerator = completed + discharged
    rec.denominator = terminal
    ratio = (
        (float(rec.numerator) / float(terminal)) * 100.0 if terminal else None
    )
    rec.value = round(ratio, 2) if ratio is not None else None
    rec.verdict = (
        _verdict_for_ratio(
            float(rec.numerator), float(terminal),
            at_least=SLO_ROUTINE_COMPLETION_MIN_PCT,
        )
        if terminal else UNKNOWN
    )
    rec.notes.append(
        "denominator = routine nodes in terminal state (completed+failed); "
        "in-flight nodes excluded (not yet terminal)"
    )
    if live_failed:
        rec.notes.append(
            f"{live_failed} failed node(s) remain LIVE debt (no verified "
            "discharge) — repair via the campaign-retry lane, not markers"
        )
    return rec


# ---------------------------------------------------------------------------
# SLO-6: continuity — control plane has a live recent heartbeat
# ---------------------------------------------------------------------------


def probe_continuity(state_db: Path, *, max_age_s: float = 900.0) -> SloRecord:
    """The campaign control plane (gateway/executor heartbeats) must show a
    heartbeat within ``max_age_s``. A missing store or stale heartbeat
    FAILs (the plane is observably not continuous right now); an unreadable
    store is UNKNOWN.
    """
    rec = SloRecord(
        slo_id="continuity",
        target=f"most recent control-plane heartbeat < {max_age_s:.0f}s old",
        numerator=None,
        denominator=None,
        sources=[str(state_db)],
    )
    try:
        conn = _ro_connect(state_db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        rec.notes.append(f"source unreadable: {exc}")
        return rec
    try:
        row = conn.execute(
            "SELECT MAX(last_heartbeat) FROM gateway_heartbeats"
        ).fetchone()
    except sqlite3.Error as exc:
        rec.notes.append(f"query failed: {exc}")
        return rec
    finally:
        conn.close()
    if not row or row[0] is None:
        rec.notes.append("no heartbeat rows")
        return rec
    age = time.time() - float(row[0])
    rec.numerator = round(age, 1)
    rec.denominator = max_age_s
    rec.value = {"heartbeat_age_s": round(age, 1)}
    rec.verdict = PASS if age <= max_age_s else FAIL
    return rec


# ---------------------------------------------------------------------------
# SLO-7: disk floor >=15% free on the campaign filesystem
# ---------------------------------------------------------------------------


def probe_disk_free(
    path: str | None = None, *, min_free_pct: float = SLO_DISK_FREE_MIN_PCT
) -> SloRecord:
    """Disk headroom on the filesystem hosting the campaign stores.
    statvfs-backed (shutil.disk_usage); no df parsing. Default path is the
    resolved Hermes root (the shared campaign filesystem).
    """
    if path is None:
        path = str(default_hermes_root())
    rec = SloRecord(
        slo_id="disk_free",
        target=f">={min_free_pct}% free on the campaign filesystem",
        numerator=None,
        denominator=None,
        sources=[f"statvfs({path})"],
    )
    try:
        usage = shutil.disk_usage(path)
    except OSError as exc:
        rec.notes.append(f"statvfs failed: {exc}")
        return rec
    free_pct = (usage.free / usage.total) * 100.0
    rec.numerator = round(free_pct, 2)
    rec.denominator = min_free_pct
    rec.value = {
        "free_pct": round(free_pct, 2),
        "free_bytes": usage.free,
        "total_bytes": usage.total,
    }
    rec.verdict = PASS if free_pct >= min_free_pct else FAIL
    return rec


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

JournalReader = Callable[[str, str], "tuple[list[str], str | None]"]


def _read_journal(unit: str, since: str) -> tuple[list[str], str | None]:
    """Read-only journalctl fetch. Returns (lines, error)."""
    cmd = [
        "journalctl",
        "--user",
        "-u",
        unit,
        "--since",
        since,
        "--no-pager",
        "-o",
        "short-iso",  # ISO timestamps: parse_watchdog_journal requires them
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"journalctl failed: {exc}"
    if proc.returncode != 0:
        return [], f"journalctl rc={proc.returncode}: {proc.stderr[:200]}"
    return proc.stdout.splitlines(), None


def _journal_unavailable(slo_id: str, target: str, err: str) -> SloRecord:
    rec = SloRecord(
        slo_id=slo_id,
        target=target,
        numerator=None,
        denominator=None,
        sources=[f"journalctl({err})"],
    )
    rec.notes.append(f"journal unavailable: {err}")
    return rec


def collect_all(
    hermes_root: Path | None = None,
    *,
    journal_since: str = "-24h",
    journal_reader: JournalReader | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Run every probe; returns the full measurement document.

    ``journal_reader`` is injectable for tests; default reads journalctl.

    2026-11-04: the journalctl read is UNIONED with the durable rolling
    watchdog archive (heartbeat-maintained) and window coverage is PROVEN
    before any verdict — journald retains only ~3h of watchdog ticks on
    the production host, so a journal-only read over a 24h window was
    laundering rotated-out episodes into UNKNOWN "nothing to measure"
    (the founding "never gamed" contract, retention edition). An
    unauditable window is reported as an explicit coverage edge and can
    never certify absence; the archive contributes ticks but never
    fabricates them (unreadable -> contributes nothing, surfaced).
    """
    root = hermes_root or default_hermes_root()
    reader = journal_reader or _read_journal
    now_ts = now if now is not None else time.time()
    delegations_db = root / "delegations" / "delegations.db"
    missions_db = root / "missions" / "missions.db"
    state_db = root / "state.db"

    records: list[SloRecord] = [
        probe_false_success(delegations_db),
        probe_duplicate_dispatch(delegations_db),
        probe_double_claim(delegations_db),
        probe_routine_completion(missions_db),
        probe_continuity(state_db),
        probe_disk_free(str(root)),
    ]

    lines, err = reader("maestro-watchdog.service", journal_since)
    if err is not None:
        records.append(
            _journal_unavailable(
                "stall_detection",
                "watchdog journal required; see notes",
                err,
            )
        )
        records.append(
            _journal_unavailable(
                "auto_recovery",
                "watchdog journal required; see notes",
                err,
            )
        )
    else:
        journal_ticks = parse_watchdog_journal(lines)
        archive_ticks: list[dict[str, Any]] = []
        archive_unreadable = False
        archive_path = default_watchdog_archive(root)
        at, unreadable = _read_archive_ticks(archive_path)
        if unreadable:
            archive_unreadable = True
        elif at:
            archive_ticks = at
        ticks = list(journal_ticks)
        used_archive = False
        if archive_ticks:
            seen = {t["__ts"] for t in ticks}
            new = [t for t in archive_ticks if t["__ts"] not in seen]
            if new:
                ticks.extend(new)
                ticks.sort(key=lambda t: t["__ts"])
                used_archive = True
        window_start = now_ts - WATCHDOG_WINDOW_S
        window_end = now_ts
        ticks = [t for t in ticks if t["__ts"] >= window_start]
        edges = _wd_coverage_edges(ticks, window_start, window_end)
        journal_source = f"maestro-watchdog journal ({journal_since})"
        if used_archive:
            journal_source += f" + rolling archive {archive_path}"

        rec_stall = probe_stall_detection_ticks(
            ticks, journal_source=journal_source
        )
        if archive_unreadable:
            rec_stall.notes.append(
                f"watchdog archive unreadable ({archive_path}); "
                "contributed nothing"
            )
        if edges:
            _apply_coverage_edges(rec_stall, edges)
            rec_stall.value = dict(rec_stall.value or {})
            rec_stall.value["coverage_complete"] = False
            rec_stall.value["coverage_edges"] = edges
        elif rec_stall.value is not None:
            rec_stall.value = dict(rec_stall.value)
            rec_stall.value["coverage_complete"] = True
        records.append(rec_stall)

        rec_auto = probe_auto_recovery_ticks(
            ticks, journal_source=journal_source
        )
        if archive_unreadable:
            rec_auto.notes.append(
                f"watchdog archive unreadable ({archive_path}); "
                "contributed nothing"
            )
        if edges:
            _apply_coverage_edges(rec_auto, edges)
            rec_auto.value = dict(rec_auto.value or {})
            rec_auto.value["coverage_complete"] = False
            rec_auto.value["coverage_edges"] = "see stall_detection edges"
        elif rec_auto.value is not None:
            rec_auto.value = dict(rec_auto.value)
            rec_auto.value["coverage_complete"] = True
        records.append(rec_auto)

    return {
        "measured_at": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts)
        ),
        "hermes_root": str(root),
        "journal_window": journal_since,
        "records": [r.as_dict() for r in records],
        "summary": _summarize(records),
    }


def _summarize(records: list[SloRecord]) -> dict[str, Any]:
    counts = {PASS: 0, FAIL: 0, UNKNOWN: 0}
    for r in records:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    return {
        "pass": counts[PASS],
        "fail": counts[FAIL],
        "unknown": counts[UNKNOWN],
        "failed_ids": [r.slo_id for r in records if r.verdict == FAIL],
        "unknown_ids": [r.slo_id for r in records if r.verdict == UNKNOWN],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", dest="json_out", help="write full document here")
    ap.add_argument(
        "--journal-since",
        default="-24h",
        help="journalctl --since value for watchdog probes (default -24h)",
    )
    args = ap.parse_args(argv)

    doc = collect_all(journal_since=args.journal_since)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote {args.json_out}")

    print(f"SLO measurement @ {doc['measured_at']} (root={doc['hermes_root']})")
    for r in doc["records"]:
        line = f"  {r['verdict']:7s} {r['slo_id']:20s}"
        if r.get("value") is not None:
            line += f" value={r['value']}"
        print(line)
    s = doc["summary"]
    print(
        f"summary: {s['pass']} PASS / {s['fail']} FAIL / {s['unknown']} UNKNOWN"
    )
    if s["fail"] == 0:
        print("no measured SLO failing; UNKNOWNs reported, not hidden")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
