from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

STAGE = "demo-stage"
BASE = "1" * 40
ZERO = "0" * 64


def _module():
    return importlib.import_module("scripts.validate_stage_change_replay")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _identity(root: Path, name: str) -> str:
    value = Path(_git(root, "rev-parse", name))
    if not value.is_absolute():
        value = root / value
    return hashlib.sha256(str(value.resolve()).encode()).hexdigest()


def _evidence(
    gate: str, generation: int, *, event_head: str | None = None
) -> dict[str, object]:
    module = _module()
    base: dict[str, object] = {
        "schema_version": f"repopilot.{module.GATE_ADAPTERS[gate]}",
        "producer": module.GATE_PRODUCERS[gate],
        "generation": generation,
        "stage_id": STAGE,
        "subject_sha256": ZERO,
        "event_head": event_head,
        "status": "PASS",
    }
    if gate == "plan_contract":
        base.update(packet_sha256=ZERO, strict_openspec_pass=True)
    elif gate in {"plan_review", "implementation_review"}:
        base.update(phase="plan" if gate == "plan_review" else "implementation", packet_sha256=ZERO, host_dispatch_verified=True, activation_verified=True)
    elif gate == "authority":
        base.update(authority_record_sha256=ZERO, expected_envelope_sha256=ZERO)
    elif gate == "implementation":
        base.update(manifest_sha256=ZERO, allowed_paths_sha256=ZERO)
    elif gate == "verification":
        base.update(
            command_ids=["pytest", "ruff"],
            required_command_ids=["pytest", "ruff"],
            commands=[
                {"command_id": "pytest", "argv": ["python", "-m", "pytest"], "cwd": ".", "exit_code": 0, "output_sha256": ZERO},
                {"command_id": "ruff", "argv": ["ruff", "check", "."], "cwd": ".", "exit_code": 0, "output_sha256": ZERO},
            ],
        )
    elif gate == "implementation_review":
        base.update(phase="implementation", packet_sha256=ZERO, host_dispatch_verified=True, activation_verified=True)
    elif gate == "archive":
        base.update(
            active_path="openspec/changes/demo-stage",
            archive_path="openspec/changes/archive/2026-08-21-demo-stage",
            strict_all_pass=True,
        )
    elif gate == "post_archive_delivery_review":
        base.update(packet_sha256=ZERO, reviewed_manifest_sha256=ZERO, reviewed_inventory_sha256=ZERO)
    elif gate == "candidate":
        base.update(candidate_oid="1" * 40, expected_parent_oid="2" * 40, single_parent=True, projection_sha256=ZERO)
    elif gate == "merge":
        base.update(candidate_oid="1" * 40, target_premerge_oid="2" * 40, target_postmerge_oid="1" * 40, ff_only=True)
    elif gate == "push":
        base.update(candidate_oid="1" * 40, old_oid="2" * 40, remote_tip="1" * 40, same_endpoint=True, outcome="verified")
    return base


def _context(root: Path) -> dict[str, object]:
    if not (root / ".git").exists():
        _git(root, "init", "-b", "main")
        _git(root, "config", "user.name", "Replay Tests")
        _git(root, "config", "user.email", "replay@example.invalid")
    snapshots = [
        {
            "gate_id": gate,
            "state": "closed" if generation <= 3 else "open",
            "generation": generation,
            "adapter_id": _module().GATE_ADAPTERS[gate],
            "input_sha256": ZERO,
            "live_input_sha256": ZERO,
            "output_sha256": ZERO if generation <= 3 else None,
            "dependency_digests": ([{
                "gate_id": _module().GATE_GRAPH[generation - 2],
                "generation": generation - 1,
                "output_sha256": ZERO,
            }] if generation <= 3 and generation > 1 else []),
            "evidence": _evidence(gate, generation) if generation <= 3 else None,
        }
        for generation, gate in enumerate(_module().GATE_GRAPH, start=1)
    ]
    for index, snapshot in enumerate(snapshots[:3]):
        snapshot["output_sha256"] = _module()._canonical_sha256(snapshot["evidence"])
        if index:
            snapshot["dependency_digests"][0]["output_sha256"] = snapshots[index - 1]["output_sha256"]
    return {
        "schema_version": "repopilot.controller_stage_context/v1",
        "capability": {"name": "provider_neutral.stage_state_cas/v1", "available": False, "provenance": "external_unavailable"},
        "activation_status": "blocked_on_external_host_capability",
        "stage_id": STAGE,
        "planning_base": BASE,
        "workspace_binding": {
            "workspace_id": "host-workspace-1",
            "initial_project_root_sha256": hashlib.sha256(str(root.resolve()).encode()).hexdigest(),
            "git_common_dir_sha256": _identity(root, "--git-common-dir"),
            "worktree_git_dir_sha256": _identity(root, "--git-dir"),
            "stage_id": STAGE,
            "planning_base": BASE,
        },
        "terminal_state": {"status": "open", "push_outcome": "not_attempted"},
        "event_state": {"prior_count": 0, "prior_head": None, "current_count": 0, "current_head": None},
        "receipt_state": {"prior_count": 0, "prior_head": None, "current_count": 0, "current_head": None},
        "gate_snapshots": snapshots,
        "authority_core_sha256": snapshots[2]["output_sha256"],
        "current_authority": {"epoch": 1, "record_sha256": ZERO},
        "expected_archive_path": "openspec/changes/archive/2026-08-21-demo-stage",
        "requested_transition": "initial_implementation_edit",
    }


def _changed_lineage(
    root: Path,
    *,
    receipt_set_mutation: str | None = None,
    changed_fact: str = "verification_evidence",
    completed_gate_ids: list[str] | None = None,
) -> dict[str, object]:
    module = _module()
    context = _context(root)
    for snapshot in context["gate_snapshots"]:
        snapshot.update(state="open", output_sha256=None, dependency_digests=[], evidence=None)
    event = {
        "schema_version": "repopilot.stage_change_event/v1",
        "stage_id": STAGE,
        "sequence": 1,
        "previous_event_sha256": None,
        "host_event_id": "host-event-1",
        "event_kind": (
            "repository_or_git_drift"
            if changed_fact in {
                "planning_baseline", "vcs_endpoint", "target_branch",
                "authorized_remote_tip", "archive_output", "final_delivery_packet",
                "candidate_head", "merge_target_state", "push_outcome_evidence",
            }
            else "agent_technical_correction"
        ),
        "source_reference": "host:controller:bounded-ref",
        "authority_before": {"epoch": 1, "record_sha256": ZERO},
        "authority_requirement": {"later_epoch_required": False, "required_epoch": None},
        "changed_fact_ids": [changed_fact],
        "before_input_snapshot_sha256": ZERO,
        "observed_input_snapshot_sha256": "2" * 64,
        "review_phase": None,
        "review_lineage": None,
        "classification_ceiling": "mechanical_consistency_only",
    }
    event["payload_sha256"] = module._canonical_sha256(event)
    event_path = root / ".harness/change-replay" / STAGE / "events/event-000001.json"
    event_path.parent.mkdir(parents=True)
    event_path.write_text(json.dumps(event, indent=2) + "\n")
    event_head = hashlib.sha256(event_path.read_bytes()).hexdigest()
    completed_gate_ids = completed_gate_ids or []
    derived = module.derive_replay_sets([changed_fact], completed_gate_ids)
    seed_index = module.GATE_GRAPH.index(module.FACT_SEEDS[changed_fact])
    closed_gates = list(module.GATE_GRAPH[:seed_index]) + completed_gate_ids
    for index, gate in enumerate(module.GATE_GRAPH):
        snapshot = context["gate_snapshots"][index]
        if gate not in closed_gates:
            continue
        snapshot["state"] = "closed"
        snapshot["evidence"] = _evidence(gate, index + 1, event_head=event_head)
        snapshot["output_sha256"] = module._canonical_sha256(snapshot["evidence"])
        snapshot["dependency_digests"] = ([] if index == 0 else [{
            "gate_id": module.GATE_GRAPH[index - 1],
            "generation": index,
            "output_sha256": context["gate_snapshots"][index - 1]["output_sha256"],
        }])
    if "authority" in closed_gates:
        context["authority_core_sha256"] = context["gate_snapshots"][2]["output_sha256"]
    gate_evidence = [
        {
            "gate_id": gate,
            "adapter_id": module.GATE_ADAPTERS[gate],
            "report_sha256": module._canonical_sha256(
                context["gate_snapshots"][module.GATE_GRAPH.index(gate)]["evidence"]
            ),
        }
        for gate in completed_gate_ids
    ]
    receipt = {
        "schema_version": "repopilot.stage_replay_receipt/v1",
        "stage_id": STAGE,
        "sequence": 1,
        "previous_receipt_sha256": None,
        "event_count": 1,
        "event_head": event_head,
        "graph_version": module.GRAPH_VERSION,
        "host_snapshot_generation": len(module.GATE_GRAPH),
        "authority": {"epoch": 1, "record_sha256": ZERO},
        "completed_gate_ids": completed_gate_ids,
        "gate_evidence": gate_evidence,
        **{key: derived[key] for key in (
            "invalidated_gate_ids", "preserved_gate_ids",
            "required_replay_gate_ids", "replay_frontier_gate_ids",
        )},
        "claim_level": "mechanical_consistency_only",
    }
    if receipt_set_mutation == "omit":
        receipt["invalidated_gate_ids"] = receipt["invalidated_gate_ids"][:-1]
    receipt_path = root / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt_head = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    context["event_state"] = {"prior_count": 1, "prior_head": event_head, "current_count": 1, "current_head": event_head}
    context["receipt_state"] = {"prior_count": 1, "prior_head": receipt_head, "current_count": 1, "current_head": receipt_head}
    context["changed_fact_ids"] = [changed_fact]
    return context


def _rewrite_receipt(
    root: Path,
    context: dict[str, object],
    mutation: Callable[[dict[str, object]], None],
) -> None:
    path = root / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt = json.loads(path.read_text())
    mutation(receipt)
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    head = hashlib.sha256(path.read_bytes()).hexdigest()
    context["receipt_state"] = {
        "prior_count": 1, "prior_head": head,
        "current_count": 1, "current_head": head,
    }


def _append_event(root: Path, context: dict[str, object], sequence: int) -> str:
    module = _module()
    previous_path = root / ".harness/change-replay" / STAGE / f"events/event-{sequence - 1:06d}.json"
    previous_head = hashlib.sha256(previous_path.read_bytes()).hexdigest()
    event = json.loads(previous_path.read_text())
    event.update(
        sequence=sequence,
        previous_event_sha256=previous_head,
        host_event_id=f"host-event-{sequence}",
        source_reference=f"host:controller:event-{sequence}",
        before_input_snapshot_sha256=event["observed_input_snapshot_sha256"],
        observed_input_snapshot_sha256=f"{(sequence + 1) % 10}" * 64,
    )
    event["payload_sha256"] = module._canonical_sha256(
        {key: value for key, value in event.items() if key != "payload_sha256"}
    )
    path = previous_path.with_name(f"event-{sequence:06d}.json")
    path.write_text(json.dumps(event, indent=2) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("fact", [
    "requirements", "scope", "non_goals", "risk", "allowed_path_rules", "planning_baseline", "plan_subject",
    "authority_record", "action_ceiling", "vcs_endpoint", "target_branch", "authorized_remote_tip",
    "implementation_subject", "workflow_subject", "template_subject", "verification_contract", "verification_evidence",
    "implementation_review_binding", "archive_output", "final_delivery_packet", "candidate_head", "merge_target_state", "push_outcome_evidence",
])
def test_every_fact_has_exact_suffix_prefix_and_frontier(fact: str) -> None:
    module = _module()
    result = module.derive_replay_sets([fact], [])
    seed = module.FACT_SEEDS[fact]
    index = module.GATE_GRAPH.index(seed)
    assert result == {
        "invalidated_gate_ids": list(module.GATE_GRAPH[index:]),
        "preserved_gate_ids": list(module.GATE_GRAPH[:index]),
        "required_replay_gate_ids": list(module.GATE_GRAPH[index:]),
        "replay_frontier_gate_ids": [seed],
        "resume_status": "replay_required",
    }


def test_unknown_duplicate_and_numeric_resume_fail() -> None:
    module = _module()
    for facts in (["unknown"], ["scope", "scope"]):
        with pytest.raises(ValueError):
            module.derive_replay_sets(facts, [])
    with pytest.raises(ValueError):
        module.derive_replay_sets(["scope"], [], declared_resume_step=1)


@pytest.mark.parametrize(("kind", "facts", "phase", "lineage", "valid"), [
    ("direct_user_envelope_change", ["scope", "plan_subject"], None, None, True),
    ("agent_technical_correction", ["implementation_subject"], None, None, True),
    ("agent_technical_correction", ["scope"], None, None, False),
    ("review_remediation", ["plan_subject"], "plan", {"slot_id": "a", "receipt_sha256": ZERO, "finding_ids": ["F1"], "affected_evidence": [ZERO]}, True),
    ("review_remediation", ["plan_subject"], "plan", None, False),
    ("repository_or_git_drift", ["authorized_remote_tip"], None, None, True),
    ("repository_or_git_drift", ["implementation_subject"], None, None, False),
])
def test_event_kind_ceiling(kind: str, facts: list[str], phase: str | None, lineage: dict[str, object] | None, valid: bool) -> None:
    errors = _module().validate_event_classification(kind, facts, review_phase=phase, review_lineage=lineage)
    assert (not errors) is valid


def test_no_change_fixture_is_mechanical_only(tmp_path: Path) -> None:
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=_context(tmp_path), required_action="implement",
    )
    assert report["status"] == "PASS"
    assert report["claim_level"] == "mechanical_consistency_only"
    assert report["human_authorized"] == "external"
    assert report["vcs_pushed"] == "not_proven"
    assert report["requested_action_ready"] is False
    assert report["external_prerequisites_satisfied"] is False
    assert {item["gate_id"] for item in report["external_prerequisites"]} == {
        "host_stage_state", "plan_contract", "plan_review", "authority",
    }


def test_closed_input_change_requires_event(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context["gate_snapshots"][0]["state"] = "closed"
    context["gate_snapshots"][0]["live_input_sha256"] = "2" * 64
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "MATERIAL_CHANGE_EVENT_REQUIRED" in {e["code"] for e in report["errors"]}


@pytest.mark.parametrize("mutation", ["missing_capability", "fake_capability", "alternate_root", "terminal", "unknown_push"])
def test_host_and_terminal_boundaries_fail_closed(tmp_path: Path, mutation: str) -> None:
    context = _context(tmp_path)
    replay_root = tmp_path / ".harness/change-replay" / STAGE
    activate = mutation in {"missing_capability", "fake_capability"}
    if mutation == "fake_capability":
        context["capability"] = {"name": "provider_neutral.stage_state_cas/v1", "available": True, "provenance": "repository_fixture"}
    elif mutation == "alternate_root":
        replay_root = tmp_path / "other"
    elif mutation == "terminal":
        context["terminal_state"] = {"status": "closed", "push_outcome": "verified"}
    elif mutation == "unknown_push":
        context["terminal_state"] = {"status": "delivery_unknown", "push_outcome": "unknown"}
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=replay_root, context=context,
        required_action="implement", activate=activate,
    )
    expected = {"missing_capability": "HOST_STATE_UNAVAILABLE", "fake_capability": "HOST_STATE_UNAVAILABLE", "alternate_root": "REPLAY_ROOT_MISMATCH", "terminal": "NEW_STAGE_REQUIRED", "unknown_push": "PUSH_RECONCILIATION_ONLY"}[mutation]
    assert expected in {e["code"] for e in report["errors"]}


def test_changed_frontier_action_matrix(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context["event_state"] = {"prior_count": 1, "prior_head": ZERO, "current_count": 1, "current_head": ZERO}
    context["changed_fact_ids"] = ["verification_evidence"]
    for action, code in [("implement", "ACTION_BEHIND_REPLAY_FRONTIER"), ("archive", "STAGE_REPLAY_REQUIRED")]:
        report = _module().validate_stage_change_replay(
            project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
            context=context, required_action=action, validate_repository_lineage=False,
        )
        assert code in {e["code"] for e in report["errors"]}


def test_adapter_rejects_arbitrary_pass_and_partial_verification() -> None:
    module = _module()
    assert module.validate_gate_evidence("verification", {"schema_version": "x", "status": "PASS"}, generation=1)
    partial = {"schema_version": "repopilot.verification_bundle/v1", "producer": "validate_verification_bundle", "generation": 1, "command_ids": ["pytest"], "required_command_ids": ["pytest", "ruff"], "commands": [], "subject_sha256": ZERO, "event_head": ZERO, "status": "PASS"}
    assert "VERIFICATION_COMMAND_SET_INCOMPLETE" in {e["code"] for e in module.validate_gate_evidence("verification", partial, generation=1)}


def test_v2_templates_are_dormant_and_non_self_referential() -> None:
    root = Path(__file__).parents[1]
    authority = json.loads((root / ".harness/templates/stage-authority-record-v2.template.json").read_text())
    delivery = json.loads((root / ".harness/templates/stage-delivery-binding-v2.template.json").read_text())
    assert authority["activation_status"] == "blocked_on_external_host_capability"
    assert delivery["pre_candidate"]["construction_policy"] == "single_parent_exact_subject_plus_metadata/v1"
    serialized = json.dumps(delivery)
    assert "candidate_oid" not in serialized and "tree_oid" not in serialized


def test_failure_messages_are_redacted(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context["stage_id"] = "bad\nsecret-token"
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "secret-token" not in json.dumps(report)


@pytest.mark.parametrize("bad", [[{}], ["scope", []], [None], {"scope": 1}, "scope"])
def test_malformed_fact_shapes_never_raise(tmp_path: Path, bad: object) -> None:
    module = _module()
    try:
        module.derive_replay_sets(bad, [])  # type: ignore[arg-type]
    except ValueError:
        pass
    context = _context(tmp_path)
    context["changed_fact_ids"] = bad
    context["event_state"] = {"prior_count": 1, "prior_head": ZERO, "current_count": 1, "current_head": ZERO}
    report = module.validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement", validate_repository_lineage=False,
    )
    assert report["status"] == "FAIL"


@pytest.mark.parametrize("field", ["generation", "dependency_digests", "evidence"])
def test_malformed_snapshot_shapes_are_structured(tmp_path: Path, field: str) -> None:
    context = _context(tmp_path)
    context["gate_snapshots"][0][field] = [] if field != "dependency_digests" else [["unhashable"]]
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert report["status"] == "FAIL"
    assert report["errors"]


@pytest.mark.parametrize("action", ["implement", "archive", "commit", "merge", "push"])
def test_no_change_normal_sequence_rejects_skipped_action(tmp_path: Path, action: str) -> None:
    context = _context(tmp_path)
    if action != "implement":
        report = _module().validate_stage_change_replay(
            project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
            context=context, required_action=action,
        )
        assert "STAGE_SEQUENCE_NOT_READY" in {item["code"] for item in report["errors"]}


def test_workspace_git_identity_mismatch_fails(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context["workspace_binding"]["git_common_dir_sha256"] = "f" * 64
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "WORKSPACE_BINDING_MISMATCH" in {item["code"] for item in report["errors"]}


def test_wrong_adapter_producer_and_subject_fail() -> None:
    evidence = _evidence("plan_contract", 1)
    evidence["producer"] = "arbitrary"
    evidence["subject_sha256"] = "f" * 64
    codes = {item["code"] for item in _module().validate_gate_evidence(
        "plan_contract", evidence, generation=1, expected_stage=STAGE,
        expected_subject_sha256=ZERO, expected_event_head=None,
    )}
    assert {"GATE_ADAPTER_PRODUCER_INVALID", "GATE_EVIDENCE_SUBJECT_MISMATCH"} <= codes


def test_verification_rejects_duplicate_wrong_argv_and_cwd() -> None:
    evidence = {
        "schema_version": "repopilot.verification_bundle/v1", "producer": "validate_verification_bundle",
        "generation": 4, "stage_id": STAGE, "subject_sha256": ZERO, "event_head": ZERO, "status": "PASS",
        "command_ids": ["pytest", "pytest"], "required_command_ids": ["pytest", "ruff"],
        "commands": [{"command_id": "pytest", "argv": "pytest -q", "cwd": "/tmp", "exit_code": 0, "output_sha256": ZERO}],
    }
    codes = {item["code"] for item in _module().validate_gate_evidence(
        "verification", evidence, generation=4, expected_stage=STAGE,
        expected_subject_sha256=ZERO, expected_event_head=ZERO,
    )}
    assert "VERIFICATION_COMMAND_SET_INCOMPLETE" in codes
    assert "VERIFICATION_COMMAND_INVALID" in codes


def test_dependency_generation_change_invalidates_byte_stable_consumer(tmp_path: Path) -> None:
    context = _context(tmp_path)
    snapshot = context["gate_snapshots"][2]
    snapshot["dependency_digests"] = [{"gate_id": "plan_review", "generation": 99, "output_sha256": ZERO}]
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "GATE_DEPENDENCY_MISMATCH" in {item["code"] for item in report["errors"]}


def test_latest_receipt_exact_set_omission_is_rejected(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path, receipt_set_mutation="omit")
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive",
    )
    assert "RECEIPT_EXACT_SET_MISMATCH" in {item["code"] for item in report["errors"]}


def test_event_stage_and_authority_delta_mismatch_are_rejected(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path)
    path = tmp_path / ".harness/change-replay" / STAGE / "events/event-000001.json"
    event = json.loads(path.read_text())
    event["event_kind"] = "direct_user_envelope_change"
    event["changed_fact_ids"] = ["scope"]
    event["authority_requirement"] = {"later_epoch_required": False, "required_epoch": None}
    event["payload_sha256"] = _module()._canonical_sha256({key: value for key, value in event.items() if key != "payload_sha256"})
    path.write_text(json.dumps(event, indent=2) + "\n")
    new_head = hashlib.sha256(path.read_bytes()).hexdigest()
    context["event_state"] = {"prior_count": 1, "prior_head": new_head, "current_count": 1, "current_head": new_head}
    context["changed_fact_ids"] = ["scope"]
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "EVENT_AUTHORITY_DELTA_INVALID" in {item["code"] for item in report["errors"]}


def test_preflight_rejects_unretained_candidate_append(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path)
    context["event_state"]["prior_count"] = 0
    context["event_state"]["prior_head"] = None
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement", cas_mode="preflight",
    )
    assert "CAS_STATE_TRANSITION_INVALID" in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize(("action", "expected"), [
    ("implement", "ACTION_BEHIND_REPLAY_FRONTIER"),
    ("archive", "STAGE_REPLAY_REQUIRED"),
    ("commit", "STAGE_REPLAY_REQUIRED"),
    ("merge", "STAGE_REPLAY_REQUIRED"),
    ("push", "STAGE_REPLAY_REQUIRED"),
])
def test_full_changed_frontier_action_matrix(tmp_path: Path, action: str, expected: str) -> None:
    context = _changed_lineage(tmp_path)
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action=action,
    )
    assert expected in {item["code"] for item in report["errors"]}


def test_changed_exact_frontier_is_consistent_but_not_externally_attested(
    tmp_path: Path,
) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive",
    )
    assert report["status"] == "PASS"
    assert report["requested_action_ready"] is False
    assert report["external_prerequisites"]
    assert report["claim_level"] == "mechanical_consistency_only"


@pytest.mark.parametrize("bad_context", [[], "text", 1, None])
def test_non_object_context_is_structured_failure(tmp_path: Path, bad_context: object) -> None:
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay/invalid",
        context=bad_context,
        required_action="implement",
    )
    assert report["status"] == "FAIL"
    assert "CONTEXT_SCHEMA_INVALID" in {item["code"] for item in report["errors"]}


def test_cli_non_object_context_has_no_traceback(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    context_path = tmp_path / "context.json"
    context_path.write_text("[]\n")
    exit_code = _module().main([
        "--project-root", str(tmp_path),
        "--replay-root", str(tmp_path / ".harness/change-replay/invalid"),
        "--context", str(context_path),
        "--required-action", "implement",
    ])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "CONTEXT_SCHEMA_INVALID" in output
    assert "Traceback" not in output


def test_changed_lineage_without_current_receipt_is_blocked(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path)
    receipt_path = tmp_path / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt_path.unlink()
    context["receipt_state"] = {"prior_count": 0, "prior_head": None, "current_count": 0, "current_head": None}
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive",
    )
    assert "REPLAY_RECEIPT_REQUIRED" in {item["code"] for item in report["errors"]}
    assert report["requested_action_ready"] is False


@pytest.mark.parametrize(
    "lineage",
    [
        {"slot_id": "a", "receipt_sha256": ZERO, "finding_ids": [["F1"]], "affected_evidence": [ZERO]},
        {"slot_id": "a", "receipt_sha256": ZERO, "finding_ids": ["F1"], "affected_evidence": [{}]},
        {"slot_id": "bad\nslot", "receipt_sha256": ZERO, "finding_ids": ["F1"], "affected_evidence": [ZERO]},
    ],
)
def test_review_lineage_malformed_elements_are_structured(lineage: dict[str, object]) -> None:
    errors = _module().validate_event_classification(
        "review_remediation", ["plan_subject"],
        review_phase="plan", review_lineage=lineage,
    )
    assert errors


def test_authority_core_digest_is_distinct_from_authority_record_hash(tmp_path: Path) -> None:
    context = _context(tmp_path)
    assert context["authority_core_sha256"] != context["current_authority"]["record_sha256"]
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert report["status"] == "PASS"


@pytest.mark.parametrize("mutation", ["core_digest", "record_hash"])
def test_authority_gate_cross_binding_fails_closed(tmp_path: Path, mutation: str) -> None:
    context = _context(tmp_path)
    if mutation == "core_digest":
        context["authority_core_sha256"] = "f" * 64
        expected = "GATE_AUTHORITY_CORE_MISMATCH"
    else:
        context["gate_snapshots"][2]["evidence"]["authority_record_sha256"] = "f" * 64
        context["gate_snapshots"][2]["output_sha256"] = _module()._canonical_sha256(context["gate_snapshots"][2]["evidence"])
        context["authority_core_sha256"] = context["gate_snapshots"][2]["output_sha256"]
        expected = "GATE_AUTHORITY_RECORD_MISMATCH"
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert expected in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("capability", [
    {"name": "provider_neutral.stage_state_cas/v1", "available": True, "provenance": "external_unavailable"},
    {"name": "provider_neutral.stage_state_cas/v1", "available": False, "provenance": "repository_fixture"},
    {"name": "provider_neutral.stage_state_cas/v1", "available": False, "provenance": "external_unavailable", "extra": True},
    [],
])
def test_dormant_capability_shape_is_strict(tmp_path: Path, capability: object) -> None:
    context = _context(tmp_path)
    context["capability"] = capability
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "CAPABILITY_STATE_INVALID" in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("terminal", [
    {"status": "closed", "push_outcome": "unknown"},
    {"status": "delivery_unknown", "push_outcome": "verified"},
    {"status": "open", "push_outcome": "verified"},
    {"status": "open", "push_outcome": "not_attempted", "extra": True},
    [],
])
def test_terminal_state_shape_and_combinations_are_strict(tmp_path: Path, terminal: object) -> None:
    context = _context(tmp_path)
    context["terminal_state"] = terminal
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "TERMINAL_STATE_INVALID" in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("state", [[], {}, ["closed"], {"closed": True}])
def test_unhashable_snapshot_state_is_structured(tmp_path: Path, state: object) -> None:
    context = _context(tmp_path)
    context["gate_snapshots"][0]["state"] = state
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert report["status"] == "FAIL"
    assert "GATE_SNAPSHOT_INVALID" in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("bad", [[], {}])
def test_unhashable_public_discriminators_never_raise(tmp_path: Path, bad: object) -> None:
    module = _module()
    assert module.validate_event_classification(bad, ["scope"])
    assert module.validate_event_classification(
        "review_remediation", ["plan_subject"], review_phase=bad,
        review_lineage={"slot_id": "a", "receipt_sha256": ZERO, "finding_ids": ["F1"], "affected_evidence": [ZERO]},
    )
    assert module.validate_gate_evidence(bad, {}, generation=1)
    for keyword in ("required_action", "cas_mode"):
        context = _context(tmp_path)
        arguments = {
            "project_root": tmp_path,
            "replay_root": tmp_path / ".harness/change-replay" / STAGE,
            "context": context,
            "required_action": "implement",
            "cas_mode": "preflight",
        }
        arguments[keyword] = bad
        report = module.validate_stage_change_replay(**arguments)
        assert report["status"] == "FAIL"


@pytest.mark.parametrize("status", [[], {}])
def test_unhashable_terminal_status_is_structured(tmp_path: Path, status: object) -> None:
    context = _context(tmp_path)
    context["terminal_state"] = {"status": status, "push_outcome": "unknown"}
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert "TERMINAL_STATE_INVALID" in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("mutation", ["gap", "delete", "unexpected", "stale_current"])
def test_lineage_gap_delete_extra_and_stale_current_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    context = _changed_lineage(tmp_path)
    event = tmp_path / ".harness/change-replay" / STAGE / "events/event-000001.json"
    if mutation == "gap":
        event.rename(event.with_name("event-000002.json"))
        expected = "LINEAGE_PATH_INVALID"
    elif mutation == "delete":
        event.unlink()
        expected = "EVENT_HOST_STATE_MISMATCH"
    elif mutation == "unexpected":
        event.with_name("fork.json").write_text("{}\n")
        expected = "LINEAGE_PATH_INVALID"
    else:
        context["event_state"]["current_head"] = "f" * 64
        context["event_state"]["prior_head"] = "f" * 64
        expected = "EVENT_HOST_STATE_MISMATCH"
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive",
    )
    assert expected in {item["code"] for item in report["errors"]}


def test_prefix_rewrite_plus_new_head_is_rejected(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path)
    first = tmp_path / ".harness/change-replay" / STAGE / "events/event-000001.json"
    retained_head = hashlib.sha256(first.read_bytes()).hexdigest()
    event = json.loads(first.read_text())
    event["source_reference"] = "host:controller:rewritten"
    event["payload_sha256"] = _module()._canonical_sha256(
        {key: value for key, value in event.items() if key != "payload_sha256"}
    )
    first.write_text(json.dumps(event, indent=2) + "\n")
    new_head = _append_event(tmp_path, context, 2)
    context["event_state"] = {
        "prior_count": 1, "prior_head": retained_head,
        "current_count": 2, "current_head": new_head,
    }
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive", cas_mode="append_event",
    )
    assert "EVENT_PREFIX_REWRITTEN" in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("mutation", ["concurrent", "host_updated_first"])
def test_append_cas_concurrent_and_host_update_before_validation_fail(
    tmp_path: Path, mutation: str
) -> None:
    context = _changed_lineage(tmp_path)
    first_head = context["event_state"]["current_head"]
    second_head = _append_event(tmp_path, context, 2)
    if mutation == "concurrent":
        third_head = _append_event(tmp_path, context, 3)
        context["event_state"] = {
            "prior_count": 1, "prior_head": first_head,
            "current_count": 3, "current_head": third_head,
        }
        expected = "CAS_STATE_TRANSITION_INVALID"
    else:
        context["event_state"] = {
            "prior_count": 2, "prior_head": second_head,
            "current_count": 2, "current_head": second_head,
        }
        expected = "CAS_STATE_TRANSITION_INVALID"
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive", cas_mode="append_event",
    )
    assert expected in {item["code"] for item in report["errors"]}


def test_restart_same_binding_is_stable_and_sibling_or_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    arguments = {
        "project_root": tmp_path,
        "replay_root": tmp_path / ".harness/change-replay" / STAGE,
        "context": context,
        "required_action": "archive",
    }
    first = _module().validate_stage_change_replay(**arguments)
    restarted = _module().validate_stage_change_replay(**arguments)
    assert first["status"] == restarted["status"] == "PASS"

    sibling = tmp_path.parent / f"{tmp_path.name}-sibling"
    sibling.mkdir()
    _git(sibling, "init", "-b", "main")
    sibling_report = _module().validate_stage_change_replay(
        project_root=sibling,
        replay_root=sibling / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "WORKSPACE_BINDING_MISMATCH" in {item["code"] for item in sibling_report["errors"]}

    alias = tmp_path.parent / f"{tmp_path.name}-alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    alias_report = _module().validate_stage_change_replay(
        project_root=alias,
        replay_root=alias / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "WORKSPACE_BINDING_MISMATCH" in {item["code"] for item in alias_report["errors"]}


@pytest.mark.parametrize("mutation", ["stale_graph", "extra_set", "wrong_adapter", "wrong_hash"])
def test_receipt_graph_sets_and_gate_bindings_are_strict(
    tmp_path: Path, mutation: str
) -> None:
    completed = ["verification"] if mutation in {"wrong_adapter", "wrong_hash"} else []
    context = _changed_lineage(
        tmp_path,
        changed_fact="verification_evidence",
        completed_gate_ids=completed,
    )

    def mutate(receipt: dict[str, object]) -> None:
        if mutation == "stale_graph":
            receipt["graph_version"] = "repopilot.stage_gate_graph/v0"
        elif mutation == "extra_set":
            receipt["preserved_gate_ids"] = [*receipt["preserved_gate_ids"], "push"]
        elif mutation == "wrong_adapter":
            receipt["gate_evidence"][0]["adapter_id"] = "arbitrary/v1"
        else:
            receipt["gate_evidence"][0]["report_sha256"] = "f" * 64

    _rewrite_receipt(tmp_path, context, mutate)
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="archive",
    )
    expected = {
        "stale_graph": "RECEIPT_CONTRACT_INVALID",
        "extra_set": "RECEIPT_EXACT_SET_MISMATCH",
        "wrong_adapter": "RECEIPT_GATE_EVIDENCE_INVALID",
        "wrong_hash": "RECEIPT_GATE_EVIDENCE_INVALID",
    }[mutation]
    assert expected in {item["code"] for item in report["errors"]}


def test_implementation_review_remediation_requires_exact_lineage() -> None:
    valid = {
        "slot_id": "impl-a", "receipt_sha256": ZERO,
        "finding_ids": ["IMP-1"], "affected_evidence": [ZERO],
    }
    assert not _module().validate_event_classification(
        "review_remediation",
        ["implementation_subject", "verification_evidence", "implementation_review_binding"],
        review_phase="implementation",
        review_lineage=valid,
    )
    invalid = dict(valid)
    invalid["finding_ids"] = []
    assert _module().validate_event_classification(
        "review_remediation", ["implementation_subject"],
        review_phase="implementation", review_lineage=invalid,
    )


def test_repository_drift_never_adopts_observed_target_as_authority(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path, changed_fact="authorized_remote_tip")
    retained_authority = dict(context["current_authority"])
    report = _module().validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action="implement",
    )
    assert report["status"] == "FAIL"
    assert context["current_authority"] == retained_authority
    assert "authorized_remote_tip" not in report
    # A real target replacement remains an external later-v1/direct-user prerequisite.


@pytest.mark.parametrize("gate", list(_module().GATE_GRAPH))
def test_every_gate_has_one_valid_strict_adapter(gate: str) -> None:
    evidence = _evidence(gate, 7)
    findings = _module().validate_gate_evidence(
        gate, evidence, generation=7, expected_stage=STAGE,
        expected_subject_sha256=ZERO, expected_event_head=None,
        expected_archive_path=(
            "openspec/changes/archive/2026-08-21-demo-stage"
            if gate == "archive"
            else None
        ),
    )
    assert {item["code"] for item in findings} == {
        "EXTERNAL_ADAPTER_ATTESTATION_REQUIRED"
    }


@pytest.mark.parametrize("gate", list(_module().GATE_GRAPH))
@pytest.mark.parametrize("mutation", ["producer", "schema", "essential"])
def test_every_gate_rejects_wrong_adapter_contract(gate: str, mutation: str) -> None:
    module = _module()
    evidence = _evidence(gate, 7)
    if mutation == "producer":
        evidence["producer"] = "arbitrary_pass_writer"
        expected = "GATE_ADAPTER_PRODUCER_INVALID"
    elif mutation == "schema":
        evidence["schema_version"] = "repopilot.arbitrary/v1"
        expected = "GATE_ADAPTER_SCHEMA_INVALID"
    else:
        essential = {
            "plan_contract": "packet_sha256",
            "plan_review": "host_dispatch_verified",
            "authority": "authority_record_sha256",
            "implementation": "manifest_sha256",
            "verification": "commands",
            "implementation_review": "host_dispatch_verified",
            "archive": "archive_path",
            "post_archive_delivery_review": "reviewed_manifest_sha256",
            "candidate": "expected_parent_oid",
            "merge": "ff_only",
            "push": "same_endpoint",
        }[gate]
        del evidence[essential]
        expected = "GATE_EVIDENCE_SCHEMA_INVALID"
    errors = module.validate_gate_evidence(
        gate, evidence, generation=7, expected_stage=STAGE,
        expected_subject_sha256=ZERO, expected_event_head=None,
        expected_archive_path=(
            "openspec/changes/archive/2026-08-21-demo-stage"
            if gate == "archive"
            else None
        ),
    )
    assert expected in {item["code"] for item in errors}


@pytest.mark.parametrize("gate", list(_module().GATE_GRAPH))
def test_cr_b_001_every_gate_rejects_wrong_code_owned_essential_binding(
    gate: str,
) -> None:
    evidence = _evidence(gate, 7)
    if gate == "plan_contract":
        evidence["strict_openspec_pass"] = False
    elif gate in {"plan_review", "implementation_review"}:
        evidence["phase"] = "implementation" if gate == "plan_review" else "plan"
    elif gate == "authority":
        evidence["expected_envelope_sha256"] = "f" * 64
    elif gate == "implementation":
        evidence["manifest_sha256"] = "f" * 64
    elif gate == "verification":
        evidence.update(
            command_ids=["echo"], required_command_ids=["echo"],
            commands=[{
                "command_id": "echo", "argv": ["echo", "PASS"], "cwd": ".",
                "exit_code": 0, "output_sha256": ZERO,
            }],
        )
    elif gate == "archive":
        evidence["archive_path"] = "openspec/changes/archive/other-stage"
    elif gate == "post_archive_delivery_review":
        evidence["packet_sha256"] = "f" * 64
    elif gate == "candidate":
        evidence["candidate_oid"] = evidence["expected_parent_oid"]
    elif gate == "merge":
        evidence["target_postmerge_oid"] = "f" * 40
    else:
        evidence["remote_tip"] = "f" * 40
    errors = _module().validate_gate_evidence(
        gate,
        evidence,
        generation=7,
        expected_stage=STAGE,
        expected_subject_sha256=ZERO,
        expected_event_head=None,
        expected_archive_path=(
            "openspec/changes/archive/2026-08-21-demo-stage"
            if gate == "archive"
            else None
        ),
    )
    assert errors, gate


FRONTIER_FACTS = {
    "implementation": ("implementation_subject", []),
    "archive": ("archive_output", []),
    "candidate": ("final_delivery_packet", ["post_archive_delivery_review"]),
    "merge": ("merge_target_state", []),
    "push": ("push_outcome_evidence", []),
}


@pytest.mark.parametrize("frontier", list(FRONTIER_FACTS))
@pytest.mark.parametrize("action", ["implement", "archive", "commit", "merge", "push"])
def test_all_governed_actions_against_every_mappable_v1_frontier(
    tmp_path: Path, frontier: str, action: str
) -> None:
    module = _module()
    fact, completed = FRONTIER_FACTS[frontier]
    context = _changed_lineage(
        tmp_path, changed_fact=fact, completed_gate_ids=completed
    )
    report = module.validate_stage_change_replay(
        project_root=tmp_path, replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context, required_action=action,
    )
    action_gate = module.ACTION_GATES[action]
    frontier_index = module.GATE_GRAPH.index(frontier)
    action_index = module.GATE_GRAPH.index(action_gate)
    codes = {item["code"] for item in report["errors"]}
    if action_index == frontier_index:
        assert report["status"] == "PASS"
        assert report["requested_action_ready"] is False
        assert report["external_prerequisites"]
    elif action_index < frontier_index:
        assert "ACTION_BEHIND_REPLAY_FRONTIER" in codes
    else:
        assert "STAGE_REPLAY_REQUIRED" in codes


def test_real_host_restart_cas_positive_remains_an_unmet_activation_prerequisite(
    tmp_path: Path,
) -> None:
    # Repository fixtures can prove deterministic recovery only. They cannot
    # supply the external provider-neutral atomic store/restart attestation.
    context = _context(tmp_path)
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="implement",
        activate=True,
    )
    assert "HOST_STATE_UNAVAILABLE" in {item["code"] for item in report["errors"]}
    assert report["activation_status"] == "blocked_on_external_host_capability"


def test_cr_impl_a_p1_001_unrelated_event_cannot_mask_gate_input_drift(
    tmp_path: Path,
) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    context["gate_snapshots"][0]["live_input_sha256"] = "3" * 64
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "GATE_DRIFT_EVENT_BINDING_INVALID" in {
        item["code"] for item in report["errors"]
    }


def test_cr_impl_a_p1_002_first_event_append_is_valid_but_not_action_ready(
    tmp_path: Path,
) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    receipt = tmp_path / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt.unlink()
    context["event_state"]["prior_count"] = 0
    context["event_state"]["prior_head"] = None
    context["receipt_state"] = {
        "prior_count": 0,
        "prior_head": None,
        "current_count": 0,
        "current_head": None,
    }
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
        cas_mode="append_event",
    )
    assert report["status"] == "PASS"
    assert report["requested_action_ready"] is False


def test_cr_impl_a_p1_002_receipt_append_is_valid_but_not_action_ready(
    tmp_path: Path,
) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    context["receipt_state"]["prior_count"] = 0
    context["receipt_state"]["prior_head"] = None
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
        cas_mode="append_receipt",
    )
    assert report["status"] == "PASS"
    assert report["requested_action_ready"] is False


def test_cr_impl_a_p1_003_echo_only_verification_bundle_is_rejected() -> None:
    evidence = _evidence("verification", 5)
    evidence.update(
        command_ids=["echo"],
        required_command_ids=["echo"],
        commands=[{
            "command_id": "echo",
            "argv": ["echo", "PASS"],
            "cwd": ".",
            "exit_code": 0,
            "output_sha256": ZERO,
        }],
    )
    codes = {
        item["code"]
        for item in _module().validate_gate_evidence(
            "verification",
            evidence,
            generation=5,
            expected_stage=STAGE,
            expected_subject_sha256=ZERO,
            expected_event_head=None,
        )
    }
    assert "VERIFICATION_COMMAND_CONTRACT_MISMATCH" in codes


def test_cr_b_001_caller_forged_review_pass_requires_external_attestation() -> None:
    forged = _evidence("plan_review", 2)
    codes = {
        item["code"]
        for item in _module().validate_gate_evidence(
            "plan_review",
            forged,
            generation=2,
            expected_stage=STAGE,
            expected_subject_sha256=ZERO,
            expected_event_head=None,
        )
    }
    assert "EXTERNAL_ADAPTER_ATTESTATION_REQUIRED" in codes


def test_cr_b_007_unknown_push_reconcile_requires_external_host_attestation(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    for snapshot in context["gate_snapshots"]:
        snapshot.update(
            state="open",
            output_sha256=None,
            dependency_digests=[],
            evidence=None,
        )
    context["terminal_state"] = {
        "status": "delivery_unknown",
        "push_outcome": "unknown",
    }
    context["requested_transition"] = "reconcile_unknown_push"
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="reconcile_push",
    )
    assert report["status"] == "PASS"
    assert report["requested_action_ready"] is False
    prerequisites = {
        item["code"]: item for item in report["external_prerequisites"]
    }
    assert "EXTERNAL_PUSH_RECONCILIATION_ATTESTATION_REQUIRED" in prerequisites
    assert prerequisites["EXTERNAL_PUSH_RECONCILIATION_ATTESTATION_REQUIRED"][
        "required_binding"
    ] == "push_gate,candidate_oid,effective_endpoint_sha256,target_branch,event_head"


def test_cr_b_008_real_dated_archive_path_is_mechanically_valid() -> None:
    real_stage = "add-stage-change-replay"
    real_archive_path = (
        "openspec/changes/archive/2026-08-21-add-stage-change-replay"
    )
    evidence = _evidence("archive", 7)
    evidence.update(
        stage_id=real_stage,
        active_path=f"openspec/changes/{real_stage}",
        archive_path=real_archive_path,
    )
    codes = {
        item["code"]
        for item in _module().validate_gate_evidence(
            "archive",
            evidence,
            generation=7,
            expected_stage=real_stage,
            expected_subject_sha256=ZERO,
            expected_event_head=None,
            expected_archive_path=real_archive_path,
        )
    }
    assert codes == {"EXTERNAL_ADAPTER_ATTESTATION_REQUIRED"}


@pytest.mark.parametrize(
    ("archive_path", "expected_archive_path", "expected_code"),
    [
        (
            "openspec/changes/archive/demo-stage",
            "openspec/changes/archive/2026-08-21-demo-stage",
            "ARCHIVE_PATH_BINDING_INVALID",
        ),
        (
            "openspec/changes/archive/2026-8-21-demo-stage",
            "openspec/changes/archive/2026-08-21-demo-stage",
            "ARCHIVE_PATH_BINDING_INVALID",
        ),
        (
            "openspec/changes/archive/2026-08-21-other-stage",
            "openspec/changes/archive/2026-08-21-demo-stage",
            "ARCHIVE_PATH_BINDING_INVALID",
        ),
        (
            "openspec/changes/archive/../2026-08-21-demo-stage",
            "openspec/changes/archive/2026-08-21-demo-stage",
            "ARCHIVE_PATH_BINDING_INVALID",
        ),
        (
            "openspec/changes/archive/2026-08-21-demo-stage",
            None,
            "ARCHIVE_EXPECTED_PATH_INVALID",
        ),
        (
            "openspec/changes/archive/2026-08-21-demo-stage",
            "openspec/changes/archive/2026-13-40-demo-stage",
            "ARCHIVE_EXPECTED_PATH_INVALID",
        ),
    ],
)
def test_cr_b_008_archive_path_mapping_is_strict(
    archive_path: str,
    expected_archive_path: str | None,
    expected_code: str,
) -> None:
    evidence = _evidence("archive", 7)
    evidence["archive_path"] = archive_path
    codes = {
        item["code"]
        for item in _module().validate_gate_evidence(
            "archive",
            evidence,
            generation=7,
            expected_stage=STAGE,
            expected_subject_sha256=ZERO,
            expected_event_head=None,
            expected_archive_path=expected_archive_path,
        )
    }
    assert expected_code in codes


def test_cr_b_008_archive_path_symlink_component_is_rejected(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    external = tmp_path.parent / f"{tmp_path.name}-external-openspec"
    external.mkdir()
    (tmp_path / "openspec").symlink_to(external, target_is_directory=True)
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="implement",
    )
    assert "ARCHIVE_PATH_SYMLINK_FORBIDDEN" in {
        item["code"] for item in report["errors"]
    }


def test_cr_b_003_replay_ancestor_symlink_is_rejected_before_lineage(
    tmp_path: Path,
) -> None:
    _context(tmp_path)
    external = tmp_path.parent / f"{tmp_path.name}-external-harness"
    external.mkdir()
    (tmp_path / ".harness").symlink_to(external, target_is_directory=True)
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "REPLAY_ROOT_SYMLINK_FORBIDDEN" in {
        item["code"] for item in report["errors"]
    }


def test_cr_b_004_invalid_historical_receipt_cannot_hide_behind_valid_latest(
    tmp_path: Path,
) -> None:
    context = _changed_lineage(
        tmp_path,
        changed_fact="archive_output",
        completed_gate_ids=["archive"],
    )
    receipt_dir = tmp_path / ".harness/change-replay" / STAGE / "receipts"
    first_path = receipt_dir / "receipt-000001.json"
    first = json.loads(first_path.read_text())
    first["invalidated_gate_ids"] = first["invalidated_gate_ids"][:-1]
    first_path.write_text(json.dumps(first, indent=2) + "\n")
    first_head = hashlib.sha256(first_path.read_bytes()).hexdigest()
    second = json.loads(first_path.read_text())
    second["sequence"] = 2
    second["previous_receipt_sha256"] = first_head
    second["invalidated_gate_ids"] = list(
        _module().derive_replay_sets(["archive_output"], ["archive"])[
            "invalidated_gate_ids"
        ]
    )
    second_path = receipt_dir / "receipt-000002.json"
    second_path.write_text(json.dumps(second, indent=2) + "\n")
    second_head = hashlib.sha256(second_path.read_bytes()).hexdigest()
    context["receipt_state"] = {
        "prior_count": 2,
        "prior_head": second_head,
        "current_count": 2,
        "current_head": second_head,
    }
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="commit",
    )
    assert "RECEIPT_EXACT_SET_MISMATCH" in {
        item["code"] for item in report["errors"]
    }


def test_cr_b_006_event_sequence_bool_is_rejected(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    event_path = tmp_path / ".harness/change-replay" / STAGE / "events/event-000001.json"
    event = json.loads(event_path.read_text())
    event["sequence"] = True
    event["payload_sha256"] = _module()._canonical_sha256(
        {key: value for key, value in event.items() if key != "payload_sha256"}
    )
    event_path.write_text(json.dumps(event, indent=2) + "\n")
    event_head = hashlib.sha256(event_path.read_bytes()).hexdigest()
    receipt_path = tmp_path / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["event_head"] = event_head
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt_head = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    context["event_state"] = {
        "prior_count": 1,
        "prior_head": event_head,
        "current_count": 1,
        "current_head": event_head,
    }
    context["receipt_state"] = {
        "prior_count": 1,
        "prior_head": receipt_head,
        "current_count": 1,
        "current_head": receipt_head,
    }
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "LINEAGE_PREDECESSOR_INVALID" in {
        item["code"] for item in report["errors"]
    }


def test_cr_b_006_receipt_sequence_bool_is_rejected(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    receipt_path = tmp_path / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["sequence"] = True
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt_head = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    context["receipt_state"] = {
        "prior_count": 1,
        "prior_head": receipt_head,
        "current_count": 1,
        "current_head": receipt_head,
    }
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "LINEAGE_PREDECESSOR_INVALID" in {
        item["code"] for item in report["errors"]
    }


def test_cr_b_006_historical_event_stage_is_validated(tmp_path: Path) -> None:
    context = _changed_lineage(tmp_path, changed_fact="archive_output")
    first_path = tmp_path / ".harness/change-replay" / STAGE / "events/event-000001.json"
    first = json.loads(first_path.read_text())
    first["stage_id"] = "other-stage"
    first["payload_sha256"] = _module()._canonical_sha256(
        {key: value for key, value in first.items() if key != "payload_sha256"}
    )
    first_path.write_text(json.dumps(first, indent=2) + "\n")
    first_head = hashlib.sha256(first_path.read_bytes()).hexdigest()
    second = json.loads(first_path.read_text())
    second.update(
        stage_id=STAGE,
        sequence=2,
        previous_event_sha256=first_head,
        host_event_id="host-event-2",
        source_reference="host:controller:event-2",
        before_input_snapshot_sha256=second["observed_input_snapshot_sha256"],
        observed_input_snapshot_sha256="3" * 64,
    )
    second["payload_sha256"] = _module()._canonical_sha256(
        {key: value for key, value in second.items() if key != "payload_sha256"}
    )
    second_path = first_path.with_name("event-000002.json")
    second_path.write_text(json.dumps(second, indent=2) + "\n")
    second_head = hashlib.sha256(second_path.read_bytes()).hexdigest()
    receipt_path = tmp_path / ".harness/change-replay" / STAGE / "receipts/receipt-000001.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["event_count"] = 2
    receipt["event_head"] = second_head
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    receipt_head = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    context["event_state"] = {
        "prior_count": 2,
        "prior_head": second_head,
        "current_count": 2,
        "current_head": second_head,
    }
    context["receipt_state"] = {
        "prior_count": 1,
        "prior_head": receipt_head,
        "current_count": 1,
        "current_head": receipt_head,
    }
    for snapshot in context["gate_snapshots"]:
        if snapshot["evidence"] is not None:
            snapshot["evidence"]["event_head"] = second_head
            snapshot["output_sha256"] = _module()._canonical_sha256(snapshot["evidence"])
    for index, snapshot in enumerate(context["gate_snapshots"]):
        if snapshot["dependency_digests"]:
            snapshot["dependency_digests"][0]["output_sha256"] = context["gate_snapshots"][index - 1]["output_sha256"]
    context["authority_core_sha256"] = context["gate_snapshots"][2]["output_sha256"]
    report = _module().validate_stage_change_replay(
        project_root=tmp_path,
        replay_root=tmp_path / ".harness/change-replay" / STAGE,
        context=context,
        required_action="archive",
    )
    assert "EVENT_STAGE_MISMATCH" in {item["code"] for item in report["errors"]}
