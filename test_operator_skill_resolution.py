"""Canonical profile-aware skill resolution (rm-027): resolver + two-stage
validation + placement hard gate.

Stage 1 (plan create): a declared skill that exists nowhere is rejected with
``skill_not_found``. Stage 2 (placement): an assignee profile that cannot
resolve a required skill is rejected with ``skill_not_resolvable_for_assignee``
(message lists where the skill *is* available). The pure scoring core
additionally hard-filters zero-skill targets when skills are required, while
Fabric-style targets (skills=[]) stay placeable for skill-less requirements.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import operator_mission_plan as plan
import operator_mission_runtime as mission
import operator_placement as pl
import operator_policy as op
import operator_skill_resolution as sres
import operator_skills


@pytest.fixture
def skills_root(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "hermes"
    op.set_audit_log_override(tmp_path / "audit.jsonl")
    monkeypatch.setenv(op.OPERATOR_ENABLED_ENV, "1")
    monkeypatch.setenv(op.OPERATOR_LEVEL_ENV, "workspace")
    monkeypatch.setenv(op.OPERATOR_APPLY_MODE_ENV, "direct")
    monkeypatch.delenv(op.OWNER_ACTIVE_ENV, raising=False)
    monkeypatch.delenv(op.OWNER_ACK_ENV, raising=False)
    # Global skill.
    _g = root / "skills" / "global-skill" / "SKILL.md"
    _g.parent.mkdir(parents=True)
    _g.write_text("# g\n")
    # Profile dev: one top-level skill, one nested (rglob semantics).
    for rel in ("code-review", "grouping/nested-review"):
        p = root / "profiles" / "dev" / "skills" / rel / "SKILL.md"
        p.parent.mkdir(parents=True)
        p.write_text("# s\n")
    # Profile qa exists but has no skills.
    (root / "profiles" / "qa").mkdir(parents=True, exist_ok=True)
    (root / "profiles" / "qa" / "config.yaml").write_text("model: m\n")
    return root


# ---------------------------------------------------------------------------
# Resolver (read-only projection)
# ---------------------------------------------------------------------------


def test_resolve_profile_skill_reports_profiles_and_paths(skills_root: Path):
    res = sres.resolve_skill("code-review", skills_root)
    assert res.resolvable is True
    assert res.profiles == ("dev",)
    assert res.scope == "profile"
    assert any("profiles/dev/skills" in p for p in res.found_paths)


def test_resolve_nested_skill_uses_recursive_walk(skills_root: Path):
    # operator_skills._find_skill_dir semantics: any dir containing SKILL.md.
    assert "nested-review" in sres.profile_skills("dev", skills_root)


def test_resolve_global_skill_is_shared_by_default_profile(skills_root: Path):
    # Canonical semantics: the default profile's home IS the hermes root, so
    # global-root skills resolve for the default profile too (mirrors
    # operator_skills._find_skill_dir("default", ...)).
    res = sres.resolve_skill("global-skill", skills_root)
    assert res.resolvable is True
    assert res.scope == "mixed"  # global root + default profile alias
    assert res.profiles == ("default",)
    assert any(p.startswith(str(skills_root / "skills")) for p in res.found_paths)


def test_resolve_unknown_skill_unresolvable(skills_root: Path):
    res = sres.resolve_skill("does-not-exist", skills_root)
    assert res.resolvable is False
    assert res.scope == ""
    assert res.found_paths == ()


def test_resolve_invalid_name_rejected(skills_root: Path):
    with pytest.raises(ValueError):
        sres.resolve_skill("Not Valid", skills_root)


# ---------------------------------------------------------------------------
# Two-stage validation
# ---------------------------------------------------------------------------


def test_stage1_unknown_skill_lists_available(skills_root: Path):
    with pytest.raises(sres.SkillNotFoundError) as ei:
        sres.validate_required_skills(["code-review", "ghost"], skills_root)
    assert "ghost" in str(ei.value)
    assert "code-review" in str(ei.value)  # actionable: what exists


def test_stage1_known_skills_pass(skills_root: Path):
    sres.validate_required_skills(["code-review", "global-skill"], skills_root)


def test_stage2_assignee_without_skill_names_resolvers(skills_root: Path):
    with pytest.raises(sres.SkillNotResolvableForAssigneeError) as ei:
        sres.validate_assignee_skills("qa", ["code-review"], skills_root)
    assert ei.value.assignee == "qa"
    assert ei.value.skill == "code-review"
    assert "dev" in str(ei.value)  # profiles that DO resolve it


def test_stage2_global_skill_unresolvable_for_qa_names_default(skills_root: Path):
    with pytest.raises(sres.SkillNotResolvableForAssigneeError) as ei:
        sres.validate_assignee_skills("qa", ["global-skill"], skills_root)
    # The default profile shares the global root, so it is the resolver named.
    assert "default" in str(ei.value)


def test_stage2_controller_personas_pass_through(skills_root: Path):
    sres.validate_assignee_skills("owner", ["code-review"], skills_root)
    sres.validate_assignee_skills("tony", ["ghost-skill-actually-unresolvable"], skills_root)


def test_stage2_owning_profile_passes(skills_root: Path):
    sres.validate_assignee_skills("dev", ["code-review"], skills_root)


# ---------------------------------------------------------------------------
# Pure placement gate
# ---------------------------------------------------------------------------


def _target(eid: str, **kw):
    base = {
        "entity_id": eid,
        "kind": kw.pop("kind", "profile"),
        "name": kw.pop("name", eid.split(":")[-1]),
        "authorization_ceiling": "reversible_write",
        "allowed_profiles": kw.pop("allowed_profiles", ["dev"]),
        "enabled": True,
        "reachable": True,
        "identity_configured": True,
    }
    base.update(kw)
    return base


def _req(**kw):
    base = {
        "profile": "dev",
        "skills": [],
        "authorization_class": "reversible_write",
    }
    base.update(kw)
    return base


def test_hard_filter_zero_skill_target_rejected_when_skills_required():
    v = pl.score_targets(
        _req(skills=["code-review"]),
        [
            _target("profile:dev", skills=["code-review"]),
            _target("profile:qa", skills=[]),
            _target("fabric:node-a", kind="fabric_node", features=["fabric-execute"]),
        ],
    )
    assert v["filter_optouts"]["profile:qa"] == ["required_skills_missing"]
    assert v["filter_optouts"]["fabric:node-a"] == ["required_skills_missing"]
    assert v["candidate_set"][0]["entity_id"] == "profile:dev"


def test_hard_filter_no_skills_requirement_keeps_fabric_placeable():
    v = pl.score_targets(
        _req(),
        [
            _target("profile:dev", skills=["code-review"]),
            _target("fabric:node-a", kind="fabric_node", features=["fabric-execute"]),
        ],
    )
    ids = {c["entity_id"] for c in v["candidate_set"]}
    assert ids == {"profile:dev", "fabric:node-a"}


# ---------------------------------------------------------------------------
# Stage 1 through hermes_plan_create
# ---------------------------------------------------------------------------


def _seed_mission(root: Path, mid: str = "msn-skills") -> None:
    spec = {
        "schema": mission.MISSION_SPEC_SCHEMA,
        "mission_id": mid,
        "title": "t",
        "objective": "o",
        "owner_profile": "default",
        "acceptance_criteria": ["a"],
        "context_refs": [],
        "skills": [],
        "final_approval_required": True,
    }
    out = json.loads(
        mission.hermes_mission_create(
            json.dumps(spec), confirm=True, dry_run=False, hermes_root=root
        )
    )
    assert out["success"] is True, out


def _dag(mid: str, profile: str, skills: list[str]) -> str:
    return json.dumps(
        {
            "schema": plan.PLAN_SCHEMA,
            "mission_id": mid,
            "version": 1,
            "decomposition": "operator-provided",
            "objective": "o",
            "nodes": [
                {
                    "node_id": "a",
                    "kind": "single",
                    "owner": profile,
                    "parents": [],
                    "objective": "node objective",
                    "capability_req": {
                        "profile": profile,
                        "skills": skills,
                        "authorization_class": "reversible_write",
                    },
                    "budget": {"est_minutes": 5, "est_tokens": 100},
                    "expected_artifacts": ["evidence.json"],
                }
            ],
        }
    )


def test_plan_create_rejects_unknown_skill_with_code(skills_root: Path):
    _seed_mission(skills_root)
    out = json.loads(
        plan.hermes_plan_create(
            "msn-skills",
            _dag("msn-skills", "dev", ["ghost-skill"]),
            confirm=True,
            dry_run=False,
            hermes_root=skills_root,
        )
    )
    assert out["success"] is False
    assert out["code"] == "SKILL_NOT_FOUND"
    assert "ghost-skill" in out["safe_message"]
    assert "code-review" in out["safe_message"]  # actionable listing


def test_plan_create_accepts_resolvable_skills(skills_root: Path):
    _seed_mission(skills_root)
    out = json.loads(
        plan.hermes_plan_create(
            "msn-skills",
            _dag("msn-skills", "dev", ["code-review", "global-skill"]),
            confirm=True,
            dry_run=False,
            hermes_root=skills_root,
        )
    )
    assert out["success"] is True, out


def test_plan_create_dry_run_also_fails_closed(skills_root: Path):
    _seed_mission(skills_root)
    out = json.loads(
        plan.hermes_plan_create(
            "msn-skills",
            _dag("msn-skills", "dev", ["ghost-skill"]),
            confirm=False,
            dry_run=True,
            hermes_root=skills_root,
        )
    )
    assert out["success"] is False
    assert out["code"] == "SKILL_NOT_FOUND"


# ---------------------------------------------------------------------------
# Stage 2 through hermes_placement_score (assignment + reassignment)
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_db(skills_root: Path) -> Path:
    """missions.db with msn-skills + two nodes: a (dev, ok) and b (qa, fails)."""
    _seed_mission(skills_root)
    path = mission._db_path(skills_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    nodes = [
        ("a", "dev", ["code-review"]),
        ("b", "qa", ["code-review"]),
    ]
    now = "2026-01-01T00:00:00+00:00"
    with plan._connect(path, write=True) as db:
        plan._begin_write(db)
        db.execute(
            "INSERT INTO mission_plans(mission_id, plan_json, version, status, plan_sha256, decomposition, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "msn-skills",
                json.dumps({"nodes": [{"node_id": n, "kind": "single", "owner": p} for n, p, _ in nodes]}),
                1,
                "approved",
                "0" * 64,
                "test",
                now,
                now,
            ),
        )
        for node_id, profile, skills in nodes:
            db.execute(
                "INSERT INTO plan_nodes(mission_id, node_id, contract_sha256, capability_req, budget, deps, state, lease_lock, lease_expires, epoch, failure_kind, retries, created_at, updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "msn-skills",
                    node_id,
                    "0" * 64,
                    json.dumps(
                        {
                            "profile": profile,
                            "skills": skills,
                            "authorization_class": "reversible_write",
                        }
                    ),
                    json.dumps({"est_minutes": 5, "est_tokens": 100}),
                    "[]",
                    "pending",
                    "",
                    "",
                    0,
                    "",
                    0,
                    now,
                    now,
                ),
            )
        db.commit()
    return path


def test_placement_score_resolving_profile_succeeds(seeded_db: Path, skills_root: Path):
    out = json.loads(
        pl.hermes_placement_score("msn-skills", "a", hermes_root=skills_root)
    )
    assert out["classification"] == pl.CLASS_ASSIGNED


def test_placement_score_assignee_without_skill_rejected(
    seeded_db: Path, skills_root: Path
):
    out = json.loads(
        pl.hermes_placement_score("msn-skills", "b", hermes_root=skills_root)
    )
    assert out["success"] is False
    assert out["code"] == "SKILL_NOT_RESOLVABLE_FOR_ASSIGNEE"
    assert "qa" in out["safe_message"]
    assert "dev" in out["safe_message"]  # where it IS resolvable
    # Reassignment semantics: every re-run of the placement surface
    # revalidates, so repeated scoring keeps failing closed (no mutation).
    again = json.loads(
        pl.hermes_placement_score("msn-skills", "b", hermes_root=skills_root)
    )
    assert again["code"] == "SKILL_NOT_RESOLVABLE_FOR_ASSIGNEE"
    # Fail-closed means no placement decision was recorded (write-mode connect
    # initializes the table; assert it stays empty).
    with pl._connect(pl._db_path(skills_root), write=True) as db:
        rows = db.execute("SELECT * FROM placement_decisions").fetchall()
    assert rows == []


# ---------------------------------------------------------------------------
# Review-fix regressions (attempt e5f4ae67): grammar parity, observed
# found_paths, recursive placement view, plan_validate stage-1
# ---------------------------------------------------------------------------


def test_grammar_parity_with_operator_skills(skills_root: Path):
    # operator_skills' grammar (dots/underscores, cap 64) is imported
    # verbatim; anything the executor accepts resolves here.
    for rel in ("web.search", "data_viz", "kb-translate.v2"):
        p = skills_root / "profiles" / "dev" / "skills" / rel / "SKILL.md"
        p.parent.mkdir(parents=True)
        p.write_text("# s\n")
    assert sres.SKILL_NAME_RE is operator_skills._VALID_NAME_RE
    names = sres.profile_skills("dev", skills_root)
    for rel in ("web.search", "data_viz", "kb-translate.v2"):
        assert rel in names
    assert sres.resolve_skill("web.search", skills_root).resolvable is True


def test_name_longer_than_executor_cap_rejected(skills_root: Path):
    # operator_skills caps names at 64 chars; the resolver must not accept a
    # name the executor would reject.
    with pytest.raises(ValueError):
        sres.resolve_skill("a" * 65, skills_root)


def test_found_paths_report_observed_directories(skills_root: Path):
    # found_paths must be OBSERVED SKILL.md dirs (nested walk), never the
    # fabricated root/name join.
    res = sres.resolve_skill("nested-review", skills_root)
    assert res.resolvable is True
    assert res.found_paths == (
        str(skills_root / "profiles" / "dev" / "skills" / "grouping" / "nested-review"),
    )


def test_placement_target_view_is_recursive(skills_root: Path):
    # Dead-zone regression: a nested-only skill must keep a capable profile
    # target placeable (manifest-load enriches with the resolver walk).
    targets = pl.load_manifest_targets(skills_root)
    dev = [t for t in targets if t["kind"] == "profile" and t["name"] == "dev"]
    assert dev, "expected a profile target for dev"
    assert "nested-review" in dev[0]["skills"]
    verdict = pl.score_targets(
        _req(profile="dev", skills=["nested-review"]), targets
    )
    assert verdict["candidate_set"], "nested-skill target must stay placeable"


def test_plan_validate_rejects_unresolvable_skill(skills_root: Path, monkeypatch):
    # validate consumes stage-1 too, so validate and create cannot disagree.
    monkeypatch.setenv("HERMES_HOME", str(skills_root))
    out = json.loads(plan.hermes_plan_validate(_dag("msn-skills", "dev", ["ghost-skill"])))
    assert out["success"] is False
    assert out["code"] == "SKILL_NOT_FOUND"


def test_plan_validate_accepts_resolvable_plan(skills_root: Path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(skills_root))
    out = json.loads(plan.hermes_plan_validate(_dag("msn-skills", "dev", ["nested-review"])))
    assert out["success"] is True
    assert out["valid"] is True


# --- rm-053 F1: grammar parity between resolver and executor -----------------
#
# assess F1 (run cbd4463370ee): the resolver used to strip skill names before
# validating them, so a whitespace-padded declaration passed stage 1 + stage 2
# and only failed later at the executor (operator_skills), which validates the
# raw string. The fix removes the strip (fail-closed at the earliest gate) and
# aligns both validators on the same pattern with the same match mode, so the
# two grammars are byte-identical.

_PADDLED_NAMES = [
    " padded-skill",
    "padded-skill ",
    " padded-skill ",
    "\tpadded-skill",
    "padded-skill\n",
    "padded skill",
    "Padded-Skill",
]

_VALID_NAMES = ["padded-skill", "a", "global-skill", "dev-nested.nested_review-1"]


@pytest.mark.parametrize("name", _PADDLED_NAMES)
def test_grammar_parity_rejects_padded_and_cased_names(name: str):
    # Both validators must reject: neither may accept what the other rejects.
    with pytest.raises(ValueError):
        sres.validate_skill_name(name)
    with pytest.raises(ValueError):
        operator_skills._validate_skill_name(name)


@pytest.mark.parametrize("name", _VALID_NAMES)
def test_grammar_parity_accepts_valid_names_unchanged(name: str):
    # The resolver returns the name UNCHANGED (no silent normalization).
    assert sres.validate_skill_name(name) == name
    assert operator_skills._validate_skill_name(name) == name


def test_resolver_no_longer_strips_before_validating():
    # Regression guard for the exact assess-F1 mechanics: stripping would have
    # turned " padded-skill " into a resolvable "padded-skill" here.
    with pytest.raises(ValueError, match="padded-skill"):
        sres.validate_skill_name(" padded-skill ")


def test_plan_validate_rejects_padded_skill_declaration(skills_root, monkeypatch):
    # End to end: a padded declaration now fails closed at stage 1 (schema
    # validation), instead of passing validation and failing at dispatch time.
    monkeypatch.setenv("HERMES_HOME", str(skills_root))
    out = json.loads(plan.hermes_plan_validate(_dag("msn-padded", "dev", [" padded-skill"])))
    assert out["success"] is False
