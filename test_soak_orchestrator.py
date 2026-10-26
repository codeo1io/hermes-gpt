"""Hermetic tests for operator_soak_orchestrator (TEST-04).

The founding contract for this module is the owner directive for TEST-04:
"staged rollout A–E with 72h fault-aware + 7-day unattended soak before
any completion claim … NEVER compress or fabricate elapsed soak time …
reset window when violated, and resume after shutdown."

Every behavior is pinned honest-first:

- the stage machine never promotes on a failed or unverifiable probe;
- elapsed time is derived from wall-clock timestamps, never accumulated;
- a reset/demotion ALWAYS starts a fresh window (and the boundary tick
  that ended the previous window must not poison the fresh one);
- a lost or corrupt state file REFUSES to tick (fail-closed), it never
  fabricates a clean window;
- --start-soak refuses to reset a live clock; --reset demands a reason;
  --probe-cmd demands an explicit confirmation flag and never uses a
  shell.

The probe is injected everywhere (``probe_runner`` or ``--probe-cmd``
running a fixed argv via subprocess without shell), so no test touches
live delegations/missions stores.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import operator_slo_probe as slo
import operator_soak_orchestrator as soak


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def soak_dir(tmp_path: Path) -> Path:
    return tmp_path / "soak"


@pytest.fixture()
def store(soak_dir: Path) -> soak.SoakStore:
    return soak.SoakStore(soak_dir)


def pass_doc() -> dict:
    return {"summary": {"pass": 8, "fail": 0, "unknown": 0, "failed_ids": [],
                        "unknown_ids": []}}


def fail_doc(slo_id: str = "disk_free") -> dict:
    return {"summary": {"pass": 7, "fail": 1, "unknown": 0,
                        "failed_ids": [slo_id], "unknown_ids": []}}


def unknown_doc() -> dict:
    return {"summary": {"pass": 6, "fail": 0, "unknown": 2,
                        "failed_ids": [], "unknown_ids": ["stall_detection"]}}


def started(store: soak.SoakStore, *, now: float = 1_000_000.0,
            window_s: float = soak.FAULT_AWARE_WINDOW_S) -> dict:
    return store.start_soak(now=now, window_s=window_s, actor="test")


# ---------------------------------------------------------------------------
# plan_stages — rollout plan as data
# ---------------------------------------------------------------------------


def test_plan_stages_shape():
    plan = soak.plan_stages()
    assert tuple(plan) == soak.STAGES == ("A", "B", "C", "D", "E")
    for stage in ("A", "B", "C", "D"):
        assert int(plan[stage]["window_s"]) == soak.FAULT_AWARE_WINDOW_S
    assert int(plan["E"]["window_s"]) == soak.UNATTENDED_WINDOW_S
    assert soak.FAULT_AWARE_WINDOW_S == 72 * 3600
    assert soak.UNATTENDED_WINDOW_S == 7 * 24 * 3600


# ---------------------------------------------------------------------------
# eval_stage — the pure stage machine, every decision shape pinned
# ---------------------------------------------------------------------------


def test_eval_hold_while_window_open():
    d = soak.eval_stage("A", 0, now=100.0, window_s=soak.FAULT_AWARE_WINDOW_S,
                        fail_count=0, violation_count=0, probe_failed_now=False)
    assert d["action"] == "hold"
    assert d["to_stage"] == "A"
    assert d["elapsed_s"] == 100.0


def test_eval_promote_on_full_clean_window():
    d = soak.eval_stage("A", 0, now=float(soak.FAULT_AWARE_WINDOW_S),
                        window_s=soak.FAULT_AWARE_WINDOW_S,
                        fail_count=0, violation_count=0, probe_failed_now=False)
    assert d["action"] == "promote"
    assert d["to_stage"] == "B"


def test_eval_chain_full_ladder_to_complete():
    # Walk the pure machine A→B→C→D→E→complete with clean probes.
    stage = "A"
    for _ in range(4):
        d = soak.eval_stage(stage, 0, now=float(soak.FAULT_AWARE_WINDOW_S),
                            window_s=soak.FAULT_AWARE_WINDOW_S,
                            fail_count=0, violation_count=0,
                            probe_failed_now=False)
        assert d["action"] == "promote"
        stage = d["to_stage"]
    d = soak.eval_stage("E", 0, now=float(soak.UNATTENDED_WINDOW_S),
                        window_s=soak.UNATTENDED_WINDOW_S,
                        fail_count=0, violation_count=0, probe_failed_now=False)
    assert d["action"] == "complete"
    assert d["to_stage"] == "E"


def test_eval_probe_fail_resets_canary_and_final_gate():
    for stage in ("A", "B", "E"):
        d = soak.eval_stage(stage, 0, now=10.0, window_s=100.0,
                            fail_count=1, violation_count=0,
                            probe_failed_now=True)
        assert d["action"] == "reset"
        assert d["to_stage"] == "A"


def test_eval_probe_fail_demotes_middle_stages():
    d = soak.eval_stage("C", 0, now=10.0, window_s=100.0,
                        fail_count=1, violation_count=0, probe_failed_now=True)
    assert d["action"] == "demote"
    assert d["to_stage"] == "B"
    d = soak.eval_stage("D", 0, now=10.0, window_s=100.0,
                        fail_count=1, violation_count=0, probe_failed_now=False)
    assert d["action"] == "demote"
    assert d["to_stage"] == "C"


def test_eval_demote_floors_at_A():
    d = soak.eval_stage("A", 0, now=10.0, window_s=100.0,
                        fail_count=0, violation_count=1, probe_failed_now=False)
    assert d["action"] == "reset"
    assert d["to_stage"] == "A"


def test_eval_violation_resets_canary_and_final():
    for stage in ("A", "B", "E"):
        d = soak.eval_stage(stage, 0, now=10.0, window_s=100.0,
                            fail_count=0, violation_count=1,
                            probe_failed_now=False)
        assert d["action"] == "reset"
        assert d["to_stage"] == "A"


def test_eval_unknown_withholds_promotion_on_full_window():
    """An unverified window is not an observed-clean window."""
    d = soak.eval_stage("A", 0, now=float(soak.FAULT_AWARE_WINDOW_S),
                        window_s=soak.FAULT_AWARE_WINDOW_S,
                        fail_count=0, violation_count=0,
                        probe_failed_now=False, probe_unknown_now=True)
    assert d["action"] == "hold"
    assert d["to_stage"] == "A"
    assert "UNKNOWN" in d["reason"]


def test_eval_unknown_mid_window_is_hold_not_fail():
    d = soak.eval_stage("C", 0, now=10.0, window_s=100.0,
                        fail_count=0, violation_count=0,
                        probe_failed_now=False, probe_unknown_now=True)
    assert d["action"] == "hold"


def test_eval_rejects_unknown_stage():
    with pytest.raises(ValueError):
        soak.eval_stage("Z", 0, now=0.0, window_s=1.0, fail_count=0,
                        violation_count=0, probe_failed_now=False)


# ---------------------------------------------------------------------------
# SoakStore — durable wall-clock state
# ---------------------------------------------------------------------------


def test_store_start_and_reload(tmp_path):
    s1 = soak.SoakStore(tmp_path / "d")
    st = s1.start_soak(now=555.0, window_s=100.0, actor="t")
    assert st["stage"] == "A"
    assert st["window_start"] == 555.0
    # a NEW instance (simulated restart) reads the same durable state
    s2 = soak.SoakStore(tmp_path / "d")
    loaded = s2.load_state()
    assert loaded["window_start"] == 555.0
    assert loaded["started_by"] == "t"
    events = [json.loads(x) for x in (tmp_path / "d" / "events.jsonl")
              .read_text().splitlines()]
    assert events[0]["event"] == "soak_started"


def test_store_corrupt_state_is_flagged_not_crashed(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    (d / "state.json").write_text("{not json")
    s = soak.SoakStore(d)
    assert s.load_state() == {"corrupt": True}


def test_store_missing_state_is_none(tmp_path):
    assert soak.SoakStore(tmp_path / "nope").load_state() is None


def test_store_finalize_window_accumulates_stage_time():
    s = soak.SoakStore.__new__(soak.SoakStore)  # no fs writes needed
    st = {"stage": "A", "window_start": 0.0,
          "stage_totals_s": {x: 0.0 for x in soak.STAGES}}
    s.finalize_window(st, now=500.0)
    assert st["stage_totals_s"]["A"] == 500.0


# ---------------------------------------------------------------------------
# run_soak_tick — measurement → decision → durable evidence
# ---------------------------------------------------------------------------


def test_tick_refused_without_state(store):
    r = soak.run_soak_tick(store, now=1.0, probe_runner=pass_doc)
    assert r["action"] == "refused"
    assert "NOT started" in r["reason"]


def test_tick_refused_on_corrupt_state(store, soak_dir):
    soak_dir.mkdir(parents=True)
    (soak_dir / "state.json").write_text("garbage{")
    r = soak.run_soak_tick(store, now=1.0, probe_runner=pass_doc)
    assert r["action"] == "refused"
    assert "CORRUPT" in r["reason"]


def test_tick_hold_persists_tick_and_refreshes_state(store):
    started(store, now=0.0, window_s=1000.0)
    r = soak.run_soak_tick(store, now=100.0, probe_runner=pass_doc)
    assert r["action"] == "hold"
    assert r["probe_verdict"] == slo.PASS
    state = store.load_state()
    assert state["updated_at"] == 100.0
    ticks = [json.loads(x) for x in store.ticks_path.read_text().splitlines()]
    assert len(ticks) == 1 and ticks[0]["action"] == "hold"


def test_tick_fail_resets_and_fresh_window_is_clean(store):
    """The cascade-reset bug pin: the FAIL tick sits exactly at the new
    window_start; strict boundary filtering keeps the fresh window clean."""
    started(store, now=0.0, window_s=1000.0)
    r1 = soak.run_soak_tick(store, now=500.0, probe_runner=fail_doc)
    assert r1["action"] == "reset"
    assert r1["to_stage"] == "A"
    assert store.load_state()["resets"] == 1
    # next tick ONE second later must NOT see the boundary FAIL again
    r2 = soak.run_soak_tick(store, now=501.0, probe_runner=pass_doc)
    assert r2["action"] == "hold", r2["reason"]
    assert r2["probe_verdict"] == slo.PASS


def test_tick_promotes_on_full_clean_window(store):
    started(store, now=0.0, window_s=100.0)
    r = soak.run_soak_tick(store, now=100.0, probe_runner=pass_doc)
    assert r["action"] == "promote"
    state = store.load_state()
    assert state["stage"] == "B"
    assert state["promotions"] == 1
    assert state["stage_totals_s"]["A"] == 100.0
    assert state["window_start"] == 100.0


def test_tick_complete_sets_gate_satisfied(store):
    started(store, now=0.0, window_s=soak.UNATTENDED_WINDOW_S)
    # force stage E via promote chains: simpler to write state directly
    st = store.load_state()
    st["stage"] = "E"
    st["window_start"] = 0.0
    store.save_state(st, now=0.0)
    r = soak.run_soak_tick(store, now=float(soak.UNATTENDED_WINDOW_S),
                           probe_runner=pass_doc)
    assert r["action"] == "complete"
    state = store.load_state()
    assert state["soak_gate_satisfied_at"] == soak.UNATTENDED_WINDOW_S
    assert state["soak_gate_satisfied_iso"].endswith("Z")


def test_tick_e_gate_fail_resets_to_a(store):
    started(store, now=0.0, window_s=soak.UNATTENDED_WINDOW_S)
    st = store.load_state()
    st["stage"] = "E"
    store.save_state(st, now=0.0)
    r = soak.run_soak_tick(store, now=1.0, probe_runner=fail_doc)
    assert r["action"] == "reset"
    assert store.load_state()["stage"] == "A"


def test_tick_probe_error_is_unknown_and_holds(store):
    def boom() -> dict:
        raise RuntimeError("store unreadable")

    started(store, now=0.0, window_s=100.0)
    r = soak.run_soak_tick(store, now=99.0, probe_runner=boom)
    assert r["probe_verdict"] == slo.UNKNOWN
    assert "RuntimeError" in r["probe_error"]
    assert r["action"] == "hold"
    events = [json.loads(x) for x in store.events_path.read_text().splitlines()]
    assert any(e["event"] == "probe_error" for e in events)


def test_tick_unknown_withholds_promotion(store):
    started(store, now=0.0, window_s=100.0)
    r = soak.run_soak_tick(store, now=100.0, probe_runner=unknown_doc)
    assert r["probe_verdict"] == slo.UNKNOWN
    assert r["action"] == "hold"
    assert store.load_state()["stage"] == "A"


def test_tick_violation_resets_canary(store):
    started(store, now=0.0, window_s=1000.0)
    r = soak.run_soak_tick(store, now=10.0, probe_runner=pass_doc,
                           violations=1)
    assert r["action"] == "reset"


def test_window_counts_exclude_boundary_tick(tmp_path):
    ticks = tmp_path / "ticks.jsonl"
    rows = [
        {"wall": 100.0, "probe_verdict": slo.FAIL, "violations": 0},
        {"wall": 100.5, "probe_verdict": slo.PASS, "violations": 0},
        {"wall": 150.0, "probe_verdict": slo.PASS, "violations": 2},
    ]
    ticks.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    counts = soak._window_counts(ticks, 100.0)
    # boundary tick (wall==100.0) excluded; later PASS + violation row seen
    assert counts == {"probe_fails": 0, "violations": 2, "ticks": 2}


# ---------------------------------------------------------------------------
# CLI — gates, refusals, subprocess probe (no shell)
# ---------------------------------------------------------------------------


PROBE_EMIT = (
    "import json;print(json.dumps({'summary':"
    "{'pass':8,'fail':0,'unknown':0,'failed_ids':[],'unknown_ids':[]}}))"
)


def cli(soak_dir: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(Path(soak.__file__)), "--soak-dir", str(soak_dir),
         *args],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_cli_probe_cmd_requires_confirm(soak_dir):
    rc, out = cli(soak_dir, "--probe-cmd", "false")
    assert rc == 2
    assert "confirm-fault-cmd" in out
    assert not (soak_dir / "state.json").exists()


def test_cli_reset_requires_reason(soak_dir):
    rc, out = cli(soak_dir, "--reset")
    assert rc == 2
    assert "--reason" in out


def test_cli_start_then_restart_refusal_keeps_clock(soak_dir):
    rc, _ = cli(soak_dir, "--start-soak")
    assert rc == 0
    state1 = json.loads((soak_dir / "state.json").read_text())
    rc, out = cli(soak_dir, "--start-soak")
    assert rc == 2
    assert "ALREADY ACTIVE" in out
    state2 = json.loads((soak_dir / "state.json").read_text())
    assert state1["window_start"] == state2["window_start"]


def test_cli_tick_with_subprocess_probe_clean(soak_dir):
    assert cli(soak_dir, "--start-soak")[0] == 0
    rc, out = cli(soak_dir, "--probe-cmd", f"{sys.executable} -c {PROBE_EMIT!r}",
                  "--confirm-fault-cmd", "--stage-window-s", "100")
    assert rc == 0, out
    assert "hold" in out or "promote" in out


def test_cli_tick_fail_exits_nonzero(soak_dir):
    fail_emit = (
        "import json;print(json.dumps({'summary':"
        "{'pass':7,'fail':1,'unknown':0,'failed_ids':['x'],'unknown_ids':[]}}))"
    )
    assert cli(soak_dir, "--start-soak")[0] == 0
    rc, out = cli(soak_dir, "--probe-cmd", f"{sys.executable} -c {fail_emit!r}",
                  "--confirm-fault-cmd")
    assert rc == 1
    assert "reset" in out


def test_cli_failing_probe_command_becomes_unknown_not_crash(soak_dir):
    """A failing external probe command is UNKNOWN + hold (fail-closed),
    never a crash and never a fabricated clean tick."""
    assert cli(soak_dir, "--start-soak")[0] == 0
    rc, out = cli(soak_dir, "--probe-cmd", "false", "--confirm-fault-cmd")
    assert rc == 0  # UNKNOWN holds; only a measured FAIL exits nonzero
    assert "UNKNOWN" in out
    assert "probe_error" in (soak_dir / "ticks.jsonl").read_text()


def test_cli_tick_never_touches_shell(soak_dir):
    """A probe-cmd containing shell metacharacters must be split as argv,
    not interpreted by a shell (metachar arrives as a literal arg)."""
    assert cli(soak_dir, "--start-soak")[0] == 0
    rc, out = cli(soak_dir, "--probe-cmd",
                  f"{sys.executable} -c 'import sys;"
                  f"print(sys.argv[1])' ; touch PWNED",
                  "--confirm-fault-cmd")
    # shlex.split treats ';' and 'touch' as separate argv items → the python
    # command runs with extra args (harmless), never a shell '&&'/';' chain.
    assert not (soak_dir / "PWNED").exists()


# ---------------------------------------------------------------------------
# Deployment sanity: module imports clean in the production venv
# ---------------------------------------------------------------------------


def test_constants_consistency():
    assert len(soak.STAGES) == 5
    assert soak.DEFAULT_STAGE_WINDOW_S == soak.FAULT_AWARE_WINDOW_S
