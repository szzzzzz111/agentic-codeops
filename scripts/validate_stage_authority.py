"""Validate RepoPilot stage authority without claiming human identity.

The record is a deterministic content binding.  Live user authority, reviewer
dispatch provenance, and Git mutations remain controller-owned facts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from scripts.validate_independent_review import validate_review_set
except ModuleNotFoundError:  # Direct `python scripts/...` execution.
    from validate_independent_review import validate_review_set

SCHEMA_VERSION = "repopilot.stage_authority/v1"
REPORT_SCHEMA = "repopilot.stage_authority_validation/v1"
ACTIONS = ("plan", "implement", "commit", "archive", "merge", "push")
V2_ACTIONS = ("plan", "implement", "archive", "commit", "merge", "push")
EPOCH_NAME = re.compile(r"^epoch-([0-9]{4})\.json$")
SAFE_STAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SAFE_REMOTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OID = re.compile(r"^[0-9a-f]{40}$")

TOP_FIELDS = {
    "schema_version",
    "stage_id",
    "authority_epoch",
    "supersedes_record_sha256",
    "authority_source",
    "scope",
    "scope_sha256",
    "planning_baseline",
    "action_ceiling",
    "vcs_target",
}
SOURCE_FIELDS = {"kind", "host_reference"}
SCOPE_FIELDS = {
    "risk",
    "summary",
    "allowed_path_rules",
    "non_goals",
    "active_allowed_files_sha256",
}
PATH_RULE_FIELDS = {"exact", "prefixes"}
BASE_FIELDS = {"commit"}
TARGET_FIELDS = {
    "remote_name",
    "effective_fetch_url_sha256",
    "effective_push_url_sha256",
    "target_branch",
    "authorized_remote_tip",
}
DELIVERY_FIELDS = {
    "schema_version",
    "stage_id",
    "authority_epoch",
    "authority_record_sha256",
    "reviewed_manifest",
    "reviewed_diff",
    "implementation_review_set",
    "final_harness_files",
}
ARTIFACT_BINDING_FIELDS = {"path", "sha256"}
REVIEW_SET_BINDING_FIELDS = {"path", "sha256", "packet_sha256"}
REVIEW_METADATA_NAMES = {
    "reviewed-change-manifest.json",
    "reviewed-change.diff",
    "review-set.json",
}
V2_AUTHORITY_FIELDS = TOP_FIELDS | {
    "activation_status",
    "trigger_change",
    "claim_level",
}
V2_DELIVERY_FIELDS = {
    "schema_version",
    "activation_status",
    "stage_id",
    "authority_epoch",
    "authority_record_sha256",
    "replay_state",
    "final_review_packet",
    "pre_candidate",
    "claim_level",
}
V2_EVENT_FIELDS = {
    "schema_version", "stage_id", "sequence", "previous_event_sha256",
    "host_event_id", "event_kind", "source_reference", "authority_before",
    "authority_requirement", "changed_fact_ids",
    "before_input_snapshot_sha256", "observed_input_snapshot_sha256",
    "review_phase", "review_lineage", "classification_ceiling", "payload_sha256",
}
V2_RECEIPT_FIELDS = {
    "schema_version", "stage_id", "sequence", "previous_receipt_sha256",
    "event_count", "event_head", "graph_version", "host_snapshot_generation",
    "authority", "completed_gate_ids", "gate_evidence", "invalidated_gate_ids",
    "preserved_gate_ids", "required_replay_gate_ids", "replay_frontier_gate_ids",
    "claim_level",
}
V2_GATE_GRAPH = (
    "plan_contract", "plan_review", "authority", "implementation",
    "verification", "implementation_review", "archive",
    "post_archive_delivery_review", "candidate", "merge", "push",
)
V2_FACT_SEEDS = {
    **{name: "plan_contract" for name in (
        "requirements", "scope", "non_goals", "risk", "allowed_path_rules",
        "planning_baseline", "plan_subject",
    )},
    **{name: "authority" for name in (
        "authority_record", "action_ceiling", "vcs_endpoint", "target_branch",
        "authorized_remote_tip",
    )},
    **{name: "implementation" for name in (
        "implementation_subject", "workflow_subject", "template_subject",
        "verification_contract",
    )},
    "verification_evidence": "verification",
    "implementation_review_binding": "implementation_review",
    "archive_output": "archive",
    "final_delivery_packet": "post_archive_delivery_review",
    "candidate_head": "post_archive_delivery_review",
    "merge_target_state": "merge",
    "push_outcome_evidence": "push",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: object) -> str:
    data = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(data)


def _error(errors: list[dict[str, str]], code: str, message: str) -> None:
    errors.append({"code": code, "message": message})


def _strict_fields(
    value: object,
    expected: set[str],
    errors: list[dict[str, str]],
    location: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _error(errors, "SCHEMA_INVALID", f"{location} must be an object")
        return {}
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        _error(
            errors,
            "UNKNOWN_FIELD",
            f"{location} contains unsupported fields: {', '.join(unknown)}",
        )
    if missing:
        _error(
            errors,
            "MISSING_FIELD",
            f"{location} is missing fields: {', '.join(missing)}",
        )
    return value


def _canonical_path(value: object, *, prefix: bool = False) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        return False
    if value.startswith("/") or (prefix and not value.endswith("/")):
        return False
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        return False
    expected = f"{path.as_posix()}/" if prefix else path.as_posix()
    return expected == value


def _path_traverses_symlink(root: Path, relative: str) -> bool:
    cursor = root
    for part in PurePosixPath(relative).parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _canonical_branch(value: object) -> bool:
    if not isinstance(value, str) or not value or value == "@":
        return False
    if (
        value.startswith("/")
        or value.endswith(("/", "."))
        or "//" in value
        or "@{" in value
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(marker in value for marker in ("..", "~", "^", ":", "?", "*", "[", " "))
    ):
        return False
    return all(
        component and not component.startswith(".") and not component.endswith(".lock")
        for component in value.split("/")
    )


def _dormant_lineage_state(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "prior_count", "prior_head", "current_count", "current_head",
    }:
        return False
    for prefix in ("prior", "current"):
        count = value.get(f"{prefix}_count")
        head = value.get(f"{prefix}_head")
        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
            or (count == 0 and head is not None)
            or (
                count > 0
                and (
                    not isinstance(head, str)
                    or SHA256.fullmatch(head) is None
                )
            )
        ):
            return False
    return value["prior_count"] <= value["current_count"]


def _authority_envelope(record: Mapping[str, Any]) -> dict[str, object]:
    return {
        key: record.get(key)
        for key in (
            "stage_id", "scope", "planning_baseline", "action_ceiling", "vcs_target",
        )
    }


def _v2_envelope_delta(
    old: Mapping[str, Any], new: Mapping[str, Any]
) -> list[str]:
    facts: set[str] = set()
    old_scope = old.get("scope") if isinstance(old.get("scope"), Mapping) else {}
    new_scope = new.get("scope") if isinstance(new.get("scope"), Mapping) else {}
    if old_scope.get("risk") != new_scope.get("risk"):
        facts.add("risk")
    if old_scope.get("summary") != new_scope.get("summary"):
        facts.add("scope")
    if old_scope.get("allowed_path_rules") != new_scope.get("allowed_path_rules"):
        facts.add("allowed_path_rules")
    if old_scope.get("non_goals") != new_scope.get("non_goals"):
        facts.add("non_goals")
    if old_scope.get("active_allowed_files_sha256") != new_scope.get("active_allowed_files_sha256"):
        facts.add("allowed_path_rules")
    if old.get("planning_baseline") != new.get("planning_baseline"):
        facts.add("planning_baseline")
    if old.get("action_ceiling") != new.get("action_ceiling"):
        facts.add("action_ceiling")
    old_target = old.get("vcs_target") if isinstance(old.get("vcs_target"), Mapping) else {}
    new_target = new.get("vcs_target") if isinstance(new.get("vcs_target"), Mapping) else {}
    if any(
        old_target.get(field) != new_target.get(field)
        for field in (
            "remote_name", "effective_fetch_url_sha256", "effective_push_url_sha256",
        )
    ):
        facts.add("vcs_endpoint")
    if old_target.get("target_branch") != new_target.get("target_branch"):
        facts.add("target_branch")
    if old_target.get("authorized_remote_tip") != new_target.get("authorized_remote_tip"):
        facts.add("authorized_remote_tip")
    return sorted(facts)


def validate_dormant_v2_interface(
    *,
    stage_cohort: str,
    activation_requested: bool,
    authority_record: object,
    delivery_binding: object,
    superseded_v1_authority: object = None,
    trigger_event: object = None,
    current_event_state: object = None,
    current_receipt_state: object = None,
    current_replay_receipt: object = None,
) -> dict[str, Any]:
    """Inspect prospective v2 shapes without selecting a cohort or authorizing work."""

    errors: list[dict[str, str]] = []
    if activation_requested:
        _error(errors, "HOST_STATE_UNAVAILABLE", "external host activation state is unavailable")
    if stage_cohort != "v2":
        _error(errors, "COHORT_SELECTION_FORBIDDEN", "caller cannot select or reinterpret a stage cohort")
    v1_shape_errors: list[dict[str, str]] = []
    if isinstance(superseded_v1_authority, dict):
        _validate_record_shape(superseded_v1_authority, v1_shape_errors)
    else:
        v1_shape_errors.append({"code": "SCHEMA_INVALID", "message": "v1 authority is absent"})
    if v1_shape_errors:
        _error(errors, "V2_SUPERSEDED_AUTHORITY_INVALID", "superseded v1 authority is not a strict v1 record")
    if not isinstance(authority_record, dict):
        _error(errors, "V2_AUTHORITY_SCHEMA_INVALID", "dormant v2 authority is invalid")
        authority_record = {}
    trigger = authority_record.get("trigger_change")
    if (
        set(authority_record) != V2_AUTHORITY_FIELDS
        or
        authority_record.get("schema_version") != "repopilot.stage_authority/v2"
        or authority_record.get("activation_status")
        != "blocked_on_external_host_capability"
        or not isinstance(trigger, dict)
        or set(trigger)
        != {
            "event_count",
            "event_head",
            "previous_authority_record_sha256",
            "required_later_epoch",
        }
    ):
        _error(errors, "V2_AUTHORITY_SCHEMA_INVALID", "dormant v2 authority trigger is invalid")
    elif (
        not isinstance(trigger.get("event_count"), int)
        or isinstance(trigger.get("event_count"), bool)
        or trigger.get("event_count", -1) < 0
        or (
            trigger.get("event_count") == 0
            and any(
                trigger.get(field) is not None
                for field in (
                    "event_head",
                    "previous_authority_record_sha256",
                    "required_later_epoch",
                )
            )
        )
        or (
            trigger.get("event_count", 0) > 0
            and (
                not isinstance(trigger.get("event_head"), str)
                or SHA256.fullmatch(trigger.get("event_head", "")) is None
                or not isinstance(trigger.get("previous_authority_record_sha256"), str)
                or SHA256.fullmatch(
                    trigger.get("previous_authority_record_sha256", "")
                )
                is None
                or not isinstance(trigger.get("required_later_epoch"), int)
                or isinstance(trigger.get("required_later_epoch"), bool)
            )
        )
    ):
        _error(errors, "V2_TRIGGER_CHANGE_INVALID", "dormant v2 trigger binding is invalid")
    stage_id = authority_record.get("stage_id")
    epoch = authority_record.get("authority_epoch")
    source = authority_record.get("authority_source")
    scope = authority_record.get("scope")
    baseline = authority_record.get("planning_baseline")
    target = authority_record.get("vcs_target")
    if (
        not isinstance(stage_id, str)
        or SAFE_STAGE.fullmatch(stage_id) is None
        or not isinstance(epoch, int)
        or isinstance(epoch, bool)
        or epoch < 1
        or not isinstance(source, dict)
        or set(source) != SOURCE_FIELDS
        or source.get("kind") != "host_direct_user_instruction"
        or not isinstance(source.get("host_reference"), str)
        or not source.get("host_reference", "").strip()
        or not isinstance(scope, dict)
        or set(scope) != SCOPE_FIELDS
        or authority_record.get("scope_sha256") != _canonical_sha256(scope)
        or not isinstance(baseline, dict)
        or set(baseline) != BASE_FIELDS
        or not isinstance(baseline.get("commit"), str)
        or OID.fullmatch(baseline.get("commit", "")) is None
        or authority_record.get("action_ceiling") not in V2_ACTIONS
        or not isinstance(target, dict)
        or set(target) != TARGET_FIELDS
        or authority_record.get("claim_level") != "mechanical_consistency_only"
    ):
        _error(errors, "V2_AUTHORITY_BINDING_INVALID", "dormant v2 authority binding is invalid")
    if isinstance(epoch, int) and not isinstance(epoch, bool) and isinstance(trigger, dict):
        supersedes = authority_record.get("supersedes_record_sha256")
        if (
            (epoch == 1 and (supersedes is not None or trigger.get("event_count") != 0))
            or (
                epoch > 1
                and (
                    not isinstance(supersedes, str)
                    or SHA256.fullmatch(supersedes) is None
                    or trigger.get("event_count", 0) < 1
                    or trigger.get("previous_authority_record_sha256") != supersedes
                    or trigger.get("required_later_epoch") != epoch
                )
            )
        ):
            _error(errors, "V2_AUTHORITY_LINEAGE_INVALID", "dormant v2 epoch and trigger lineage differ")
    v1_hash = (
        _canonical_sha256(superseded_v1_authority)
        if isinstance(superseded_v1_authority, dict)
        else None
    )
    v1_epoch = (
        superseded_v1_authority.get("authority_epoch")
        if isinstance(superseded_v1_authority, dict)
        else None
    )
    if (
        not isinstance(v1_epoch, int)
        or isinstance(v1_epoch, bool)
        or not isinstance(epoch, int)
        or isinstance(epoch, bool)
        or epoch != v1_epoch + 1
        or authority_record.get("supersedes_record_sha256") != v1_hash
        or not isinstance(trigger, dict)
        or trigger.get("previous_authority_record_sha256") != v1_hash
    ):
        _error(errors, "V2_SUPERSEDED_AUTHORITY_INVALID", "v2 authority does not exactly supersede the supplied v1 authority")
    if isinstance(scope, dict):
        rules = scope.get("allowed_path_rules")
        if (
            not isinstance(scope.get("risk"), str)
            or scope.get("risk") not in {"low", "medium", "high"}
            or not isinstance(scope.get("summary"), str)
            or not scope.get("summary", "").strip()
            or not isinstance(rules, dict)
            or set(rules) != PATH_RULE_FIELDS
            or not isinstance(rules.get("exact"), list)
            or any(not _canonical_path(item) for item in rules.get("exact", []))
            or rules.get("exact") != sorted(set(rules.get("exact", [])))
            or not isinstance(rules.get("prefixes"), list)
            or any(not _canonical_path(item, prefix=True) for item in rules.get("prefixes", []))
            or rules.get("prefixes") != sorted(set(rules.get("prefixes", [])))
            or not isinstance(scope.get("non_goals"), list)
            or any(not isinstance(item, str) or not item.strip() for item in scope.get("non_goals", []))
            or not isinstance(scope.get("active_allowed_files_sha256"), str)
            or SHA256.fullmatch(scope.get("active_allowed_files_sha256", "")) is None
        ):
            _error(errors, "V2_SCOPE_INVALID", "dormant v2 scope is invalid")
    if isinstance(target, dict) and (
        not isinstance(target.get("remote_name"), str)
        or SAFE_REMOTE.fullmatch(target.get("remote_name", "")) is None
        or any(
            not isinstance(target.get(field), str)
            or SHA256.fullmatch(target.get(field, "")) is None
            for field in ("effective_fetch_url_sha256", "effective_push_url_sha256")
        )
        or not _canonical_branch(target.get("target_branch"))
        or not isinstance(target.get("authorized_remote_tip"), str)
        or OID.fullmatch(target.get("authorized_remote_tip", "")) is None
    ):
        _error(errors, "V2_TARGET_INVALID", "dormant v2 target is invalid")

    event_valid = isinstance(trigger_event, dict) and set(trigger_event) == V2_EVENT_FIELDS
    if event_valid:
        event_payload = {
            key: value for key, value in trigger_event.items() if key != "payload_sha256"
        }
        authority_before = trigger_event.get("authority_before")
        requirement = trigger_event.get("authority_requirement")
        expected_delta = _v2_envelope_delta(
            superseded_v1_authority
            if isinstance(superseded_v1_authority, Mapping)
            else {},
            authority_record,
        )
        event_valid = (
            trigger_event.get("schema_version") == "repopilot.stage_change_event/v1"
            and trigger_event.get("stage_id") == stage_id
            and isinstance(trigger_event.get("sequence"), int)
            and not isinstance(trigger_event.get("sequence"), bool)
            and trigger_event.get("sequence", 0) > 0
            and trigger_event.get("event_kind") == "direct_user_envelope_change"
            and isinstance(trigger_event.get("host_event_id"), str)
            and bool(trigger_event.get("host_event_id"))
            and isinstance(trigger_event.get("source_reference"), str)
            and bool(trigger_event.get("source_reference"))
            and isinstance(authority_before, dict)
            and authority_before == {"epoch": v1_epoch, "record_sha256": v1_hash}
            and isinstance(requirement, dict)
            and requirement == {"later_epoch_required": True, "required_epoch": epoch}
            and trigger_event.get("changed_fact_ids") == expected_delta
            and trigger_event.get("before_input_snapshot_sha256")
            == _canonical_sha256(_authority_envelope(superseded_v1_authority))
            and trigger_event.get("observed_input_snapshot_sha256")
            == _canonical_sha256(_authority_envelope(authority_record))
            and trigger_event.get("review_phase") is None
            and trigger_event.get("review_lineage") is None
            and trigger_event.get("classification_ceiling") == "mechanical_consistency_only"
            and trigger_event.get("payload_sha256") == _canonical_sha256(event_payload)
        )
    if not event_valid:
        _error(errors, "V2_TRIGGER_EVENT_INVALID", "v2 trigger event does not bind the exact old/new authority envelope")
    event_head = _canonical_sha256(trigger_event) if isinstance(trigger_event, dict) else None
    if (
        not isinstance(trigger, dict)
        or trigger.get("event_count") != (
            trigger_event.get("sequence") if isinstance(trigger_event, dict) else None
        )
        or trigger.get("event_head") != event_head
    ):
        _error(errors, "V2_TRIGGER_EVENT_INVALID", "v2 trigger projection differs from the supplied event")
    if isinstance(trigger_event, dict) and trigger_event.get("changed_fact_ids") != _v2_envelope_delta(
        superseded_v1_authority if isinstance(superseded_v1_authority, Mapping) else {},
        authority_record,
    ):
        _error(errors, "V2_ENVELOPE_DELTA_INVALID", "v2 event does not declare the exact old/new envelope delta")

    if not _dormant_lineage_state(current_event_state):
        _error(errors, "V2_EVENT_STATE_INVALID", "current v2 event state is invalid")
    elif (
        current_event_state.get("current_count")
        != (trigger_event.get("sequence") if isinstance(trigger_event, dict) else None)
        or current_event_state.get("current_head") != event_head
    ):
        _error(errors, "V2_EVENT_STATE_INVALID", "current v2 event state differs from the trigger event")
    if not _dormant_lineage_state(current_receipt_state):
        _error(errors, "V2_RECEIPT_STATE_INVALID", "current v2 receipt state is invalid")

    receipt_valid = (
        isinstance(current_replay_receipt, dict)
        and set(current_replay_receipt) == V2_RECEIPT_FIELDS
    )
    if receipt_valid:
        completed = current_replay_receipt.get("completed_gate_ids")
        changed_facts = trigger_event.get("changed_fact_ids") if isinstance(trigger_event, dict) else None
        receipt_valid = (
            current_replay_receipt.get("schema_version") == "repopilot.stage_replay_receipt/v1"
            and current_replay_receipt.get("stage_id") == stage_id
            and isinstance(current_replay_receipt.get("sequence"), int)
            and not isinstance(current_replay_receipt.get("sequence"), bool)
            and current_replay_receipt.get("sequence", 0) > 0
            and current_replay_receipt.get("event_count")
            == (trigger_event.get("sequence") if isinstance(trigger_event, dict) else None)
            and current_replay_receipt.get("event_head") == event_head
            and current_replay_receipt.get("graph_version") == "repopilot.stage_gate_graph/v1"
            and isinstance(current_replay_receipt.get("host_snapshot_generation"), int)
            and not isinstance(current_replay_receipt.get("host_snapshot_generation"), bool)
            and current_replay_receipt.get("host_snapshot_generation", 0) > 0
            and current_replay_receipt.get("authority")
            == {"epoch": epoch, "record_sha256": _canonical_sha256(authority_record)}
            and isinstance(completed, list)
            and all(isinstance(item, str) and item in V2_GATE_GRAPH for item in completed)
            and len(completed) == len(set(completed))
            and isinstance(current_replay_receipt.get("gate_evidence"), list)
            and len(current_replay_receipt.get("gate_evidence", [])) == len(completed)
            and isinstance(changed_facts, list)
            and bool(changed_facts)
            and all(isinstance(item, str) and item in V2_FACT_SEEDS for item in changed_facts)
            and current_replay_receipt.get("claim_level") == "mechanical_consistency_only"
        )
        if receipt_valid:
            seed_index = min(
                V2_GATE_GRAPH.index(V2_FACT_SEEDS[item]) for item in changed_facts
            )
            required = list(V2_GATE_GRAPH[seed_index:])
            preserved = list(V2_GATE_GRAPH[:seed_index])
            replayed = [gate for gate in required if gate in completed]
            remaining = required[len(replayed):]
            receipt_valid = (
                replayed == required[:len(replayed)]
                and current_replay_receipt.get("invalidated_gate_ids") == required
                and current_replay_receipt.get("preserved_gate_ids") == preserved
                and current_replay_receipt.get("required_replay_gate_ids") == required
                and current_replay_receipt.get("replay_frontier_gate_ids") == remaining[:1]
            )
    if not receipt_valid:
        _error(errors, "V2_RECEIPT_LINEAGE_INVALID", "current v2 receipt does not bind exact replay lineage")
    receipt_head = (
        _canonical_sha256(current_replay_receipt)
        if isinstance(current_replay_receipt, dict)
        else None
    )
    if _dormant_lineage_state(current_receipt_state) and (
        current_receipt_state.get("current_count")
        != (
            current_replay_receipt.get("sequence")
            if isinstance(current_replay_receipt, dict)
            else None
        )
        or current_receipt_state.get("current_head") != receipt_head
    ):
        _error(errors, "V2_RECEIPT_STATE_INVALID", "current v2 receipt state differs from the supplied receipt")

    if not isinstance(delivery_binding, dict):
        _error(errors, "V2_DELIVERY_SCHEMA_INVALID", "dormant v2 delivery is invalid")
        delivery_binding = {}
    replay = delivery_binding.get("replay_state")
    pre_candidate = delivery_binding.get("pre_candidate")
    if (
        set(delivery_binding) != V2_DELIVERY_FIELDS
        or
        delivery_binding.get("schema_version")
        != "repopilot.stage_delivery_binding/v2"
        or delivery_binding.get("activation_status")
        != "blocked_on_external_host_capability"
        or not isinstance(replay, dict)
        or set(replay)
        != {"event_count", "event_head", "receipt_count", "receipt_head"}
        or not isinstance(pre_candidate, dict)
        or set(pre_candidate)
        != {
            "expected_parent_oid",
            "review_packet_sha256",
            "reviewed_manifest_sha256",
            "reviewed_inventory_sha256",
            "review_metadata_and_tail_paths",
            "construction_policy",
        }
    ):
        _error(errors, "V2_DELIVERY_SCHEMA_INVALID", "dormant v2 delivery fields are invalid")
    else:
        for count_field, head_field in (
            ("event_count", "event_head"),
            ("receipt_count", "receipt_head"),
        ):
            count = replay.get(count_field)
            head = replay.get(head_field)
            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
                or (count == 0 and head is not None)
                or (
                    count > 0
                    and (
                        not isinstance(head, str)
                        or SHA256.fullmatch(head) is None
                    )
                )
            ):
                _error(errors, "V2_REPLAY_HEAD_INVALID", "dormant v2 replay head is invalid")
        paths = pre_candidate.get("review_metadata_and_tail_paths")
        if (
            not isinstance(pre_candidate.get("expected_parent_oid"), str)
            or OID.fullmatch(pre_candidate.get("expected_parent_oid", "")) is None
            or any(
                not isinstance(pre_candidate.get(field), str)
                or SHA256.fullmatch(pre_candidate.get(field, "")) is None
                for field in (
                    "review_packet_sha256",
                    "reviewed_manifest_sha256",
                    "reviewed_inventory_sha256",
                )
            )
            or not isinstance(paths, list)
            or not paths
            or any(not _canonical_path(item) for item in paths)
            or paths != sorted(set(paths))
            or pre_candidate.get("construction_policy")
            != "single_parent_exact_subject_plus_metadata/v1"
            or (
                isinstance(stage_id, str)
                and paths != _review_metadata_paths(stage_id)
            )
            or "candidate_oid" in json.dumps(delivery_binding, sort_keys=True)
            or "tree_oid" in json.dumps(delivery_binding, sort_keys=True)
        ):
            _error(errors, "V2_PRE_CANDIDATE_INVALID", "dormant v2 pre-candidate binding is invalid")
        final_packet = delivery_binding.get("final_review_packet")
        if (
            delivery_binding.get("stage_id") != stage_id
            or delivery_binding.get("authority_epoch") != epoch
            or delivery_binding.get("authority_record_sha256")
            != _canonical_sha256(authority_record)
            or delivery_binding.get("claim_level") != "mechanical_consistency_only"
            or not isinstance(final_packet, dict)
            or set(final_packet) != ARTIFACT_BINDING_FIELDS
            or not _canonical_path(final_packet.get("path"))
            or not isinstance(final_packet.get("sha256"), str)
            or SHA256.fullmatch(final_packet.get("sha256", "")) is None
            or not isinstance(trigger, dict)
            or replay.get("event_count") != trigger.get("event_count")
            or replay.get("event_head") != trigger.get("event_head")
            or not _dormant_lineage_state(current_event_state)
            or not _dormant_lineage_state(current_receipt_state)
            or replay.get("event_count") != current_event_state.get("current_count")
            or replay.get("event_head") != current_event_state.get("current_head")
            or replay.get("receipt_count") != current_receipt_state.get("current_count")
            or replay.get("receipt_head") != current_receipt_state.get("current_head")
        ):
            _error(errors, "V2_CROSS_BINDING_INVALID", "dormant v2 authority and delivery bindings differ")
    return {
        "schema_version": "repopilot.stage_authority_v2_dormant_validation/v1",
        "status": "PASS" if not errors else "FAIL",
        "claim_level": "mechanical_consistency_only",
        "activation_status": "blocked_on_external_host_capability",
        "action_order": list(V2_ACTIONS),
        "mutation_authorized": False,
        "errors": errors,
    }


def _read_json(path: Path, errors: list[dict[str, str]]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _error(errors, "RECORD_UNREADABLE", "authority record is not valid UTF-8 JSON")
        return {}
    if not isinstance(value, dict):
        _error(errors, "SCHEMA_INVALID", "authority record must be an object")
        return {}
    return value


def run_bounded(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    max_output_bytes: int,
    mutation_capable: bool,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Run fixed argv with disabled prompting and bounded output/time."""

    if (
        not argv
        or timeout_seconds <= 0
        or max_output_bytes <= 0
        or not isinstance(mutation_capable, bool)
    ):
        return {
            "status": "FAIL",
            "code": "PROCESS_ARGUMENT_INVALID",
            "stdout": "",
            "stderr": "",
            "shell": False,
        }
    git_subcommand = _git_subcommand(argv)
    if git_subcommand == "push" and not mutation_capable:
        return {
            "status": "FAIL",
            "code": "PROCESS_INTENT_MISMATCH",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "shell": False,
        }
    if mutation_capable and os.name != "nt":
        return {
            "status": "FAIL",
            "code": "PROCESS_ISOLATION_UNAVAILABLE",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "shell": False,
        }
    child_env = dict(env or os.environ)
    child_env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_ASKPASS": "/usr/bin/false",
            "SSH_ASKPASS": "/usr/bin/false",
        }
    )
    popen_options: dict[str, Any] = {}
    if os.name == "posix":
        popen_options["start_new_session"] = True
    elif os.name == "nt":  # pragma: no cover - exercised by Windows verification
        create_suspended = 0x00000004
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | create_suspended
        )
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            **popen_options,
        )
    except OSError:
        return {
            "status": "FAIL",
            "code": "PROCESS_START_FAILED",
            "stdout": "",
            "stderr": "",
            "shell": False,
        }

    assert process.stdout is not None
    assert process.stderr is not None
    windows_job = _create_windows_kill_job(process)
    windows_ready = windows_job is not None and _resume_windows_process(process.pid)
    if os.name == "nt" and not windows_ready:  # pragma: no cover - Windows only
        cleanup_ok = _terminate_process_tree(process, windows_job=windows_job)
        return {
            "status": "FAIL",
            "code": (
                "PROCESS_ISOLATION_FAILED"
                if cleanup_ok
                else "PROCESS_CLEANUP_FAILED"
            ),
            "returncode": process.returncode,
            "stdout": "",
            "stderr": "",
            "shell": False,
        }

    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    buffer_lock = threading.Lock()
    overflow = threading.Event()
    read_failed = threading.Event()
    total_output = 0

    def drain(stream: Any, stream_name: str) -> None:
        nonlocal total_output
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    return
                with buffer_lock:
                    remaining = max(0, max_output_bytes - total_output)
                    buffers[stream_name].extend(chunk[:remaining])
                    total_output += len(chunk)
                    if total_output > max_output_bytes:
                        overflow.set()
        except (OSError, ValueError):
            read_failed.set()

    readers = [
        threading.Thread(target=drain, args=(process.stdout, "stdout")),
        threading.Thread(target=drain, args=(process.stderr, "stderr")),
    ]
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + timeout_seconds
    failure_code: str | None = None
    while process.poll() is None:
        if overflow.is_set():
            failure_code = "PROCESS_OUTPUT_LIMIT"
            break
        if read_failed.is_set():
            failure_code = "PROCESS_READ_FAILED"
            break
        if time.monotonic() >= deadline:
            failure_code = "PROCESS_TIMEOUT"
            break
        overflow.wait(0.01)

    if failure_code is None and process.returncode != 0:
        failure_code = "PROCESS_NONZERO"
    if failure_code is None and _process_group_exists(process.pid):
        failure_code = "PROCESS_DESCENDANT_LINGERED"
    if failure_code is None and windows_job is not None:
        active_processes = _windows_job_active_processes(windows_job)
        if active_processes is None:
            failure_code = "PROCESS_CLEANUP_FAILED"
        elif active_processes:
            failure_code = "PROCESS_DESCENDANT_LINGERED"

    if failure_code is not None:
        cleanup_ok = _terminate_process_tree(process, windows_job=windows_job)
        if not cleanup_ok:
            failure_code = "PROCESS_CLEANUP_FAILED"
    elif windows_job is not None:
        _close_windows_job(windows_job)

    for reader in readers:
        reader.join(timeout=2)
    if any(reader.is_alive() for reader in readers):
        failure_code = "PROCESS_CLEANUP_FAILED"
    elif overflow.is_set() and failure_code is None:
        failure_code = "PROCESS_OUTPUT_LIMIT"
    elif read_failed.is_set() and failure_code is None:
        failure_code = "PROCESS_READ_FAILED"

    try:
        stdout = bytes(buffers["stdout"][:max_output_bytes]).decode("utf-8")
        stderr = bytes(buffers["stderr"][:max_output_bytes]).decode("utf-8")
    except UnicodeDecodeError:
        stdout = ""
        stderr = ""
        if failure_code is None:
            failure_code = "PROCESS_OUTPUT_ENCODING_INVALID"

    status = "PASS" if failure_code is None and process.returncode == 0 else "FAIL"
    code = failure_code or ("OK" if status == "PASS" else "PROCESS_NONZERO")
    if mutation_capable and status == "FAIL":
        status = "UNKNOWN"
        code = "UNKNOWN_PUSH_OUTCOME"
    return {
        "status": status,
        "code": code,
        "returncode": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "shell": False,
    }


def _git_subcommand(argv: Sequence[str]) -> str | None:
    if not argv or Path(argv[0]).name.lower() not in {"git", "git.exe"}:
        return None
    value_options = {
        "-C",
        "-c",
        "--config-env",
        "--exec-path",
        "--git-dir",
        "--namespace",
        "--super-prefix",
        "--work-tree",
    }
    index = 1
    while index < len(argv):
        token = argv[index]
        if token in value_options:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None


def _terminate_process_tree(
    process: subprocess.Popen[bytes], *, windows_job: int | None = None
) -> bool:
    """Terminate the isolated process group and reap its leader before return."""

    if os.name == "posix":
        cleanup_ok = True
        for group_signal, timeout in ((signal.SIGTERM, 0.5), (signal.SIGKILL, 2.0)):
            try:
                os.killpg(process.pid, group_signal)
            except ProcessLookupError:
                break
            except OSError:
                cleanup_ok = False
                break
            try:
                process.wait(timeout=min(timeout, 0.2))
            except subprocess.TimeoutExpired:
                pass
            group_deadline = time.monotonic() + timeout
            while time.monotonic() < group_deadline:
                if not _process_group_exists(process.pid):
                    break
                time.sleep(0.01)
            if not _process_group_exists(process.pid):
                break
    else:  # pragma: no cover - exercised by Windows verification
        cleanup_ok = _terminate_windows_job(windows_job)
        if windows_job is None:
            cleanup_ok = _taskkill_process_tree(process.pid)
        if process.poll() is None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        if windows_job is not None:
            cleanup_ok = cleanup_ok and _wait_windows_job_empty(windows_job, 2)
            _close_windows_job(windows_job)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        return False
    if os.name == "posix":
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return cleanup_ok
        except OSError:
            return False
        return False
    return cleanup_ok and process.poll() is not None


def _process_group_exists(process_group_id: int) -> bool:
    if os.name != "posix":
        return False
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def _create_windows_kill_job(process: subprocess.Popen[bytes]) -> int | None:
    """Assign the child to a kill-on-close Job Object on Windows."""

    if os.name != "nt":
        return None
    import ctypes  # pragma: no cover - Windows only
    from ctypes import wintypes  # pragma: no cover - Windows only

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("per_process_user_time_limit", ctypes.c_longlong),
            ("per_job_user_time_limit", ctypes.c_longlong),
            ("limit_flags", wintypes.DWORD),
            ("minimum_working_set_size", ctypes.c_size_t),
            ("maximum_working_set_size", ctypes.c_size_t),
            ("active_process_limit", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority_class", wintypes.DWORD),
            ("scheduling_class", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("read_operation_count", ctypes.c_ulonglong),
            ("write_operation_count", ctypes.c_ulonglong),
            ("other_operation_count", ctypes.c_ulonglong),
            ("read_transfer_count", ctypes.c_ulonglong),
            ("write_transfer_count", ctypes.c_ulonglong),
            ("other_transfer_count", ctypes.c_ulonglong),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("basic_limit_information", BasicLimitInformation),
            ("io_info", IoCounters),
            ("process_memory_limit", ctypes.c_size_t),
            ("job_memory_limit", ctypes.c_size_t),
            ("peak_process_memory_used", ctypes.c_size_t),
            ("peak_job_memory_used", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return None
    info = ExtendedLimitInformation()
    info.basic_limit_information.limit_flags = 0x00002000
    configured = kernel32.SetInformationJobObject(
        job,
        9,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    process_handle = getattr(process, "_handle", None)
    assigned = process_handle is not None and kernel32.AssignProcessToJobObject(
        job, process_handle
    )
    if not configured or not assigned:
        kernel32.CloseHandle(job)
        return None
    return int(job)


def _windows_job_active_processes(job: int) -> int | None:
    if os.name != "nt":
        return 0
    import ctypes  # pragma: no cover - Windows only
    from ctypes import wintypes  # pragma: no cover - Windows only

    class BasicAccountingInformation(ctypes.Structure):
        _fields_ = [
            ("total_user_time", ctypes.c_longlong),
            ("total_kernel_time", ctypes.c_longlong),
            ("this_period_total_user_time", ctypes.c_longlong),
            ("this_period_total_kernel_time", ctypes.c_longlong),
            ("total_page_fault_count", wintypes.DWORD),
            ("total_processes", wintypes.DWORD),
            ("active_processes", wintypes.DWORD),
            ("total_terminated_processes", wintypes.DWORD),
        ]

    info = BasicAccountingInformation()
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
    ]
    queried = kernel32.QueryInformationJobObject(
        job,
        1,
        ctypes.byref(info),
        ctypes.sizeof(info),
        None,
    )
    return int(info.active_processes) if queried else None


def _resume_windows_process(process_id: int) -> bool:
    if os.name != "nt":
        return True
    import ctypes  # pragma: no cover - Windows only
    from ctypes import wintypes  # pragma: no cover - Windows only

    class ThreadEntry(ctypes.Structure):
        _fields_ = [
            ("size", wintypes.DWORD),
            ("usage", wintypes.DWORD),
            ("thread_id", wintypes.DWORD),
            ("owner_process_id", wintypes.DWORD),
            ("base_priority", wintypes.LONG),
            ("priority_delta", wintypes.LONG),
            ("flags", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.OpenThread.restype = wintypes.HANDLE
    kernel32.Thread32First.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ThreadEntry),
    ]
    kernel32.Thread32Next.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ThreadEntry),
    ]
    kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    invalid_handle = ctypes.c_void_p(-1).value
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000004, 0)
    if snapshot == invalid_handle:
        return False
    entry = ThreadEntry()
    entry.size = ctypes.sizeof(entry)
    found = bool(kernel32.Thread32First(snapshot, ctypes.byref(entry)))
    resumed = False
    while found:
        if entry.owner_process_id == process_id:
            thread = kernel32.OpenThread(0x0002, False, entry.thread_id)
            if thread:
                resumed = kernel32.ResumeThread(thread) != 0xFFFFFFFF
                kernel32.CloseHandle(thread)
            break
        found = bool(kernel32.Thread32Next(snapshot, ctypes.byref(entry)))
    kernel32.CloseHandle(snapshot)
    return resumed


def _terminate_windows_job(job: int | None) -> bool:
    if os.name != "nt" or job is None:
        return False
    import ctypes  # pragma: no cover - Windows only
    from ctypes import wintypes  # pragma: no cover - Windows only

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    return bool(kernel32.TerminateJobObject(job, 1))


def _wait_windows_job_empty(job: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        active_processes = _windows_job_active_processes(job)
        if active_processes == 0:
            return True
        if active_processes is None:
            return False
        time.sleep(0.01)
    return False


def _close_windows_job(job: int) -> None:
    if os.name != "nt":
        return
    import ctypes  # pragma: no cover - Windows only
    from ctypes import wintypes  # pragma: no cover - Windows only

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle(job)


def _taskkill_process_tree(process_id: int) -> bool:
    if os.name != "nt":
        return False
    try:  # pragma: no cover - Windows fallback only
        completed = subprocess.run(
            ["taskkill", "/PID", str(process_id), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def reconcile_push_outcome(
    *,
    project_root: str | Path,
    effective_push_url: str,
    expected_effective_push_url_sha256: str,
    target_branch: str,
    expected_target_branch: str,
    candidate_head: str,
    authorized_old_tip: str,
) -> dict[str, Any]:
    """Query and classify only the host-bound endpoint and exact target ref."""

    if (
        _sha256(effective_push_url.encode("utf-8"))
        != expected_effective_push_url_sha256
        or not _canonical_branch(target_branch)
        or target_branch != expected_target_branch
    ):
        return {
            "code": "UNKNOWN_PUSH_OUTCOME",
            "vcs_pushed": "unknown",
            "retry_allowed": False,
        }
    query_errors: list[dict[str, str]] = []
    remote_tip = _query_remote_tip(
        Path(project_root).resolve(),
        effective_push_url,
        target_branch,
        query_errors,
    )
    if remote_tip is None or query_errors:
        return {
            "code": "UNKNOWN_PUSH_OUTCOME",
            "vcs_pushed": "unknown",
            "retry_allowed": False,
        }
    if remote_tip == candidate_head:
        return {
            "code": "PUSH_VERIFIED",
            "vcs_pushed": "verified",
            "retry_allowed": False,
        }
    if remote_tip == authorized_old_tip:
        return {
            "code": "PUSH_NOT_APPLIED",
            "vcs_pushed": "not_attempted",
            "retry_allowed": True,
        }
    return {
        "code": "REMOTE_TIP_DIVERGED",
        "vcs_pushed": "unknown",
        "retry_allowed": False,
    }


def exact_push_argv(
    *,
    effective_push_url: str,
    candidate_head: str,
    target_branch: str,
    authorized_old_tip: str,
) -> list[str]:
    """Return the only permitted compare-and-swap push argv."""

    target_ref = f"refs/heads/{target_branch}"
    return [
        "git",
        "push",
        "--porcelain",
        f"--force-with-lease={target_ref}:{authorized_old_tip}",
        effective_push_url,
        f"{candidate_head}:{target_ref}",
    ]


def _git(root: Path, *args: str) -> tuple[bool, str]:
    result = run_bounded(
        ["git", *args],
        cwd=root,
        timeout_seconds=10,
        max_output_bytes=1_000_000,
        mutation_capable=False,
    )
    return result["status"] == "PASS", result["stdout"]


def _single_remote_url(
    root: Path,
    remote_name: str,
    *,
    push: bool,
    errors: list[dict[str, str]],
) -> str | None:
    args = ["remote", "get-url"]
    if push:
        args.append("--push")
    args.extend(("--all", remote_name))
    ok, output = _git(root, *args)
    urls = [line for line in output.splitlines() if line]
    if not ok or len(urls) != 1:
        _error(errors, "REMOTE_ENDPOINT_AMBIGUOUS", "remote endpoint is not unique")
        return None
    url = urls[0]
    supported = url.startswith(("ssh://", "https://", "file://", "/")) or (
        "@" in url and ":" in url
    )
    if not supported:
        _error(errors, "REMOTE_ENDPOINT_UNSUPPORTED", "remote endpoint is unsupported")
        return None
    return url


def _query_remote_tip(
    root: Path,
    effective_url: str,
    target_branch: str,
    errors: list[dict[str, str]],
) -> str | None:
    target_ref = f"refs/heads/{target_branch}"
    result = run_bounded(
        ["git", "ls-remote", "--refs", effective_url, target_ref],
        cwd=root,
        timeout_seconds=30,
        max_output_bytes=4096,
        mutation_capable=False,
    )
    if result["status"] != "PASS":
        _error(errors, "REMOTE_QUERY_FAILED", "remote target could not be queried")
        return None
    lines = [line for line in result["stdout"].splitlines() if line]
    if len(lines) != 1:
        _error(errors, "REMOTE_QUERY_AMBIGUOUS", "remote target result is not exact")
        return None
    fields = lines[0].split("\t")
    if len(fields) != 2 or fields[1] != target_ref or OID.fullmatch(fields[0]) is None:
        _error(errors, "REMOTE_QUERY_AMBIGUOUS", "remote target result is malformed")
        return None
    return fields[0]


def _validate_clean_worktree(
    root: Path,
    *,
    expected_branch: str | None,
    expected_head: str,
    errors: list[dict[str, str]],
    code_prefix: str,
) -> None:
    ok, status = _git(root, "status", "--porcelain=v1", "-z")
    if not ok or status:
        _error(errors, f"{code_prefix}_DIRTY", "worktree is not clean")
    ok, head = _git(root, "rev-parse", "HEAD")
    if not ok or head.strip() != expected_head:
        _error(errors, f"{code_prefix}_HEAD_MISMATCH", "worktree HEAD differs")
    if expected_branch is not None:
        ok, branch = _git(root, "symbolic-ref", "--short", "HEAD")
        if not ok or branch.strip() != expected_branch:
            _error(errors, f"{code_prefix}_BRANCH_MISMATCH", "branch differs")


def _git_common_dir(root: Path, errors: list[dict[str, str]]) -> Path | None:
    ok, output = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not ok or not output.strip():
        _error(errors, "REPOSITORY_IDENTITY_UNAVAILABLE", "Git common directory is unavailable")
        return None
    return Path(output.strip()).resolve()


def _validate_live_remote(
    root: Path,
    *,
    remote_name: str,
    target_branch: str,
    expected_fetch_sha256: str,
    expected_push_sha256: str,
    errors: list[dict[str, str]],
) -> tuple[str | None, str | None]:
    fetch_url = _single_remote_url(root, remote_name, push=False, errors=errors)
    push_url = _single_remote_url(root, remote_name, push=True, errors=errors)
    if fetch_url is None or push_url is None:
        return push_url, None
    endpoint_valid = True
    if fetch_url != push_url:
        endpoint_valid = False
        _error(
            errors,
            "REMOTE_ENDPOINT_MISMATCH",
            "effective fetch and push endpoints differ",
        )
    if _sha256(fetch_url.encode("utf-8")) != expected_fetch_sha256:
        endpoint_valid = False
        _error(
            errors,
            "LIVE_FETCH_ENDPOINT_MISMATCH",
            "effective fetch endpoint fingerprint differs",
        )
    if _sha256(push_url.encode("utf-8")) != expected_push_sha256:
        endpoint_valid = False
        _error(
            errors,
            "LIVE_PUSH_ENDPOINT_MISMATCH",
            "effective push endpoint fingerprint differs",
        )
    if not endpoint_valid:
        return push_url, None
    return push_url, _query_remote_tip(root, push_url, target_branch, errors)


def _name_status_paths(output: str) -> set[str]:
    fields = output.split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(fields):
                break
            paths.add(fields[index])
            paths.add(fields[index + 1])
            index += 2
        elif index < len(fields):
            paths.add(fields[index])
            index += 1
    return paths


def _changed_paths(root: Path, base: str, errors: list[dict[str, str]]) -> set[str]:
    paths: set[str] = set()
    commands = (
        ("diff", "--name-status", "-z", f"{base}..HEAD"),
        ("diff", "--cached", "--name-status", "-z"),
        ("diff", "--name-status", "-z"),
    )
    for command in commands:
        ok, output = _git(root, *command)
        if not ok:
            _error(errors, "GIT_CHANGESET_FAILED", "unable to derive Git change set")
            continue
        paths.update(_name_status_paths(output))
    ok, untracked = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if not ok:
        _error(errors, "GIT_CHANGESET_FAILED", "unable to derive untracked paths")
    else:
        paths.update(path for path in untracked.split("\0") if path)
    ok, ignored = _git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")
    if not ok:
        _error(errors, "GIT_CHANGESET_FAILED", "unable to derive ignored paths")
    else:
        paths.update(
            path
            for path in ignored.split("\0")
            if path and not _is_bounded_transient(path)
        )
    return paths


def _is_bounded_transient(path: str) -> bool:
    """Exclude only deterministic local test/interpreter cache artifacts."""

    parts = PurePosixPath(path).parts
    pytest_cache_files = {
        ".pytest_cache/.gitignore",
        ".pytest_cache/CACHEDIR.TAG",
        ".pytest_cache/README.md",
        ".pytest_cache/v/cache/lastfailed",
        ".pytest_cache/v/cache/nodeids",
        ".pytest_cache/v/cache/stepwise",
    }
    return path in pytest_cache_files or (
        re.fullmatch(r"\.ruff_cache/(?:\.gitignore|CACHEDIR\.TAG)", path) is not None
        or re.fullmatch(r"\.ruff_cache/[0-9]+\.[0-9]+\.[0-9]+/[0-9]+", path)
        is not None
        or (
            "__pycache__" in parts
            and re.fullmatch(r"[^/]+\.py[co]", parts[-1]) is not None
        )
    )


def _gitlink_paths(root: Path, base: str, errors: list[dict[str, str]]) -> set[str]:
    gitlinks: set[str] = set()
    for command in (("ls-files", "--stage", "-z"), ("ls-tree", "-r", "-z", base)):
        ok, output = _git(root, *command)
        if not ok:
            _error(errors, "GIT_MODE_SCAN_FAILED", "unable to inspect Git entry modes")
            continue
        for entry in output.split("\0"):
            if not entry or "\t" not in entry:
                continue
            metadata, path = entry.split("\t", 1)
            if metadata.split(" ", 1)[0] == "160000":
                gitlinks.add(path)
    return gitlinks


def _review_metadata_paths(stage_id: str) -> list[str]:
    return sorted(
        [
            f".harness/reviews/{stage_id}/implementation/reviewed-change-manifest.json",
            f".harness/reviews/{stage_id}/implementation/reviewed-change.diff",
            f".harness/reviews/{stage_id}/implementation/review-set.json",
            f".harness/authority/{stage_id}/delivery-binding.json",
        ]
    )


def _regular_file_mode(path: Path) -> str:
    return "100755" if path.stat().st_mode & 0o111 else "100644"


def _validate_commit_index_projection(
    *,
    root: Path,
    planning_base: str,
    stage: str,
    manifest: Mapping[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """Bind the read-only Git index to the reviewed worktree packet exactly."""

    changes = manifest.get("changes")
    if not isinstance(changes, list):
        _error(errors, "CANDIDATE_INDEX_MANIFEST_INVALID", "review manifest changes are invalid")
        return
    subjects: dict[str, Mapping[str, Any]] = {}
    for item in changes:
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("kind"), str)
            or item.get("kind") not in {"file", "deleted"}
        ):
            _error(errors, "CANDIDATE_INDEX_MANIFEST_INVALID", "review manifest subject is invalid")
            return
        subjects[item["path"]] = item
    metadata_paths = _review_metadata_paths(stage)
    expected_paths = set(subjects) | set(metadata_paths)

    ok, output = _git(root, "diff", "--cached", "--name-status", "-z", planning_base)
    if not ok:
        _error(errors, "CANDIDATE_INDEX_UNAVAILABLE", "staged candidate path set is unavailable")
        return
    staged_paths = _name_status_paths(output)
    if staged_paths != expected_paths:
        _error(errors, "CANDIDATE_INDEX_PATH_SET_MISMATCH", "staged candidate path set differs from the reviewed projection")

    ok, output = _git(root, "ls-files", "--stage", "-z")
    if not ok:
        _error(errors, "CANDIDATE_INDEX_UNAVAILABLE", "staged candidate entries are unavailable")
        return
    entries: dict[str, list[tuple[str, str, str]]] = {}
    malformed = False
    for raw in output.split("\0"):
        if not raw:
            continue
        if "\t" not in raw:
            malformed = True
            continue
        metadata, path = raw.split("\t", 1)
        parts = metadata.split()
        if len(parts) != 3:
            malformed = True
            continue
        mode, oid, index_stage = parts
        entries.setdefault(path, []).append((mode, oid, index_stage))
    if malformed:
        _error(errors, "CANDIDATE_INDEX_ENTRY_INVALID", "staged candidate entry metadata is invalid")

    expected_files = {
        **{
            path: item
            for path, item in subjects.items()
            if item.get("kind") == "file"
        },
        **{path: {"path": path, "kind": "file"} for path in metadata_paths},
    }
    expected_deletions = {
        path for path, item in subjects.items() if item.get("kind") == "deleted"
    }
    for path in expected_deletions:
        if path in entries:
            _error(errors, "CANDIDATE_INDEX_STATE_MISMATCH", "reviewed deletion remains present in the index")
    for path, item in expected_files.items():
        indexed = entries.get(path, [])
        if len(indexed) != 1 or indexed[0][2] != "0":
            _error(errors, "CANDIDATE_INDEX_STATE_MISMATCH", "reviewed file lacks one stage-zero index entry")
            continue
        mode, oid, _ = indexed[0]
        if mode not in {"100644", "100755"} or OID.fullmatch(oid) is None:
            _error(errors, "CANDIDATE_INDEX_MODE_INVALID", "reviewed file is not a regular staged blob")
            continue
        worktree_path = root / path
        if (
            _path_traverses_symlink(root, path)
            or not worktree_path.is_file()
            or worktree_path.is_symlink()
        ):
            _error(errors, "CANDIDATE_INDEX_WORKTREE_INVALID", "reviewed worktree file is unavailable or unsafe")
            continue
        current_mode = _regular_file_mode(worktree_path)
        expected_mode = "100644" if path in metadata_paths else current_mode
        if mode != expected_mode or current_mode != expected_mode:
            _error(errors, "CANDIDATE_INDEX_MODE_MISMATCH", "candidate file mode differs from the required mode")
        if path in subjects:
            reviewed_mode = item.get("mode")
            if (
                not isinstance(reviewed_mode, str)
                or reviewed_mode not in {"100644", "100755"}
            ):
                _error(errors, "CANDIDATE_INDEX_REVIEW_MODE_INVALID", "reviewed file mode is invalid")
            elif mode != reviewed_mode or current_mode != reviewed_mode:
                _error(errors, "CANDIDATE_INDEX_REVIEW_MODE_MISMATCH", "staged or current mode differs from the reviewed mode")
        ok, worktree_oid = _git(root, "hash-object", "--no-filters", "--", path)
        if not ok or OID.fullmatch(worktree_oid.strip()) is None:
            _error(errors, "CANDIDATE_INDEX_BLOB_UNAVAILABLE", "reviewed worktree blob identity is unavailable")
        elif oid != worktree_oid.strip():
            _error(errors, "CANDIDATE_INDEX_BLOB_MISMATCH", "staged blob bytes differ from the reviewed worktree")
        declared_sha256 = item.get("sha256")
        if (
            path in subjects
            and (
                not isinstance(declared_sha256, str)
                or SHA256.fullmatch(declared_sha256) is None
                or _sha256(worktree_path.read_bytes()) != declared_sha256
            )
        ):
            _error(errors, "CANDIDATE_INDEX_REVIEW_HASH_MISMATCH", "reviewed subject hash differs from current bytes")


def build_review_subject_manifest(
    *,
    project_root: str | Path,
    stage_id: str,
    planning_base: str,
) -> dict[str, Any]:
    """Build the exhaustive review subject with exactly four exclusions."""

    errors: list[dict[str, str]] = []
    root = Path(project_root).resolve()
    if SAFE_STAGE.fullmatch(stage_id) is None:
        _error(errors, "STAGE_INVALID", "stage_id is not canonical")
    if OID.fullmatch(planning_base) is None:
        _error(errors, "BASE_OID_INVALID", "planning base must be a Git OID")
    changed = _changed_paths(root, planning_base, errors)
    gitlinks = _gitlink_paths(root, planning_base, errors)
    excluded = _review_metadata_paths(stage_id)
    excluded_set = set(excluded)
    changes: list[dict[str, Any]] = []
    for relative in sorted(changed - excluded_set):
        if not _canonical_path(relative):
            _error(errors, "MANIFEST_PATH_INVALID", "manifest path is not canonical")
            continue
        if relative in gitlinks:
            _error(errors, "MANIFEST_GITLINK_FORBIDDEN", "manifest path is a gitlink")
            continue
        path = root / relative
        if _path_traverses_symlink(root, relative):
            _error(errors, "MANIFEST_SYMLINK_FORBIDDEN", "manifest path is a symlink")
            continue
        if not path.exists():
            changes.append({"path": relative, "kind": "deleted"})
        elif path.is_file():
            changes.append(
                {
                    "path": relative,
                    "kind": "file",
                    "mode": _regular_file_mode(path),
                    "sha256": _sha256(path.read_bytes()),
                }
            )
        else:
            _error(
                errors,
                "MANIFEST_SPECIAL_PATH_FORBIDDEN",
                "manifest path is not a regular file",
            )
    manifest = {
        "schema_version": "repopilot.reviewed_change_manifest/v2",
        "stage_id": stage_id,
        "planning_base": planning_base,
        "excluded_metadata_paths": excluded,
        "changes": changes,
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "manifest": manifest,
        "manifest_sha256": _canonical_sha256(manifest),
        "errors": errors,
    }


def build_reviewed_inventory_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Render the only accepted byte-stable reviewed-change inventory."""

    if not _review_manifest_shape_valid(manifest):
        raise TypeError("invalid review manifest")
    planning_base = manifest.get("planning_base")
    changes = manifest.get("changes")
    if not isinstance(planning_base, str) or not isinstance(changes, list):
        raise TypeError("invalid review manifest")
    lines = [
        "# RepoPilot reviewed-change inventory v2",
        f"# planning-base {planning_base}",
        "# Every line binds the current file bytes; deletions use DELETE without a hash.",
    ]
    for item in changes:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise TypeError("invalid review manifest change")
        if (
            item.get("kind") == "file"
            and set(item) == {"path", "kind", "mode", "sha256"}
            and isinstance(item.get("sha256"), str)
            and isinstance(item.get("mode"), str)
            and item.get("mode") in {"100644", "100755"}
        ):
            lines.append(
                f"FILE\t{item['mode']}\t{item['sha256']}\t{item['path']}"
            )
        elif item.get("kind") == "deleted" and set(item) == {"path", "kind"}:
            lines.append(f"DELETE\t{item['path']}")
        else:
            raise TypeError("invalid review manifest change")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _review_manifest_shape_valid(manifest: object) -> bool:
    if (
        not isinstance(manifest, Mapping)
        or not all(isinstance(key, str) for key in manifest)
        or set(manifest)
        != {
            "schema_version", "stage_id", "planning_base",
            "excluded_metadata_paths", "changes",
        }
        or manifest.get("schema_version") != "repopilot.reviewed_change_manifest/v2"
        or not isinstance(manifest.get("stage_id"), str)
        or SAFE_STAGE.fullmatch(manifest.get("stage_id", "")) is None
        or not isinstance(manifest.get("planning_base"), str)
        or OID.fullmatch(manifest.get("planning_base", "")) is None
        or not isinstance(manifest.get("changes"), list)
    ):
        return False
    excluded = manifest.get("excluded_metadata_paths")
    if excluded != _review_metadata_paths(manifest["stage_id"]):
        return False
    paths: list[str] = []
    for item in manifest["changes"]:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not _canonical_path(item["path"])
            or item["path"] in excluded
        ):
            return False
        paths.append(item["path"])
        if item.get("kind") == "file":
            if (
                set(item) != {"path", "kind", "mode", "sha256"}
                or not isinstance(item.get("mode"), str)
                or item.get("mode") not in {"100644", "100755"}
                or not isinstance(item.get("sha256"), str)
                or SHA256.fullmatch(item.get("sha256", "")) is None
            ):
                return False
        elif item.get("kind") == "deleted":
            if set(item) != {"path", "kind"}:
                return False
        else:
            return False
    return paths == sorted(set(paths))


def _validate_bound_artifact(
    value: object,
    *,
    root: Path,
    fields: set[str],
    errors: list[dict[str, str]],
    location: str,
) -> dict[str, Any]:
    artifact = _strict_fields(value, fields, errors, location)
    relative = artifact.get("path")
    declared_hash = artifact.get("sha256")
    if not _canonical_path(relative):
        _error(errors, "DELIVERY_PATH_INVALID", f"{location} path is not canonical")
        return artifact
    if not isinstance(declared_hash, str) or SHA256.fullmatch(declared_hash) is None:
        _error(errors, "DELIVERY_HASH_INVALID", f"{location} hash is invalid")
        return artifact
    path = root / relative
    if _path_traverses_symlink(root, relative) or not path.is_file():
        _error(errors, "DELIVERY_ARTIFACT_MISSING", f"{location} file is unavailable")
    elif _sha256(path.read_bytes()) != declared_hash:
        _error(errors, "DELIVERY_ARTIFACT_DRIFT", f"{location} file hash changed")
    return artifact


def validate_delivery_binding(
    binding: object,
    *,
    project_root: str | Path,
    expected_stage: str,
    expected_epoch: int,
    expected_authority_record_sha256: str,
    expected_review_packet_sha256: str,
) -> dict[str, Any]:
    """Validate the finite, non-self-hashing post-review evidence tail."""

    errors: list[dict[str, str]] = []
    root = Path(project_root).resolve()
    document = _strict_fields(binding, DELIVERY_FIELDS, errors, "delivery_binding")
    if document.get("schema_version") != "repopilot.stage_delivery_binding/v1":
        _error(errors, "DELIVERY_SCHEMA_INVALID", "delivery schema is invalid")
    comparisons = (
        (document.get("stage_id"), expected_stage, "DELIVERY_STAGE_MISMATCH"),
        (document.get("authority_epoch"), expected_epoch, "DELIVERY_EPOCH_MISMATCH"),
        (
            document.get("authority_record_sha256"),
            expected_authority_record_sha256,
            "DELIVERY_AUTHORITY_MISMATCH",
        ),
    )
    for actual, expected, code in comparisons:
        if actual != expected:
            _error(errors, code, "delivery binding differs from host value")

    manifest_binding = _validate_bound_artifact(
        document.get("reviewed_manifest"),
        root=root,
        fields=ARTIFACT_BINDING_FIELDS,
        errors=errors,
        location="reviewed_manifest",
    )
    diff_binding = _validate_bound_artifact(
        document.get("reviewed_diff"),
        root=root,
        fields=ARTIFACT_BINDING_FIELDS,
        errors=errors,
        location="reviewed_diff",
    )
    review_set_binding = _validate_bound_artifact(
        document.get("implementation_review_set"),
        root=root,
        fields=REVIEW_SET_BINDING_FIELDS,
        errors=errors,
        location="implementation_review_set",
    )
    if review_set_binding.get("packet_sha256") != expected_review_packet_sha256:
        _error(
            errors,
            "DELIVERY_PACKET_MISMATCH",
            "delivery packet differs from host value",
        )
    expected_paths = {
        "manifest": (
            f".harness/reviews/{expected_stage}/implementation/"
            "reviewed-change-manifest.json"
        ),
        "diff": (
            f".harness/reviews/{expected_stage}/implementation/reviewed-change.diff"
        ),
        "review_set": (
            f".harness/reviews/{expected_stage}/implementation/review-set.json"
        ),
    }
    if manifest_binding.get("path") != expected_paths["manifest"]:
        _error(errors, "DELIVERY_PATH_INVALID", "review manifest path is not exact")
    if diff_binding.get("path") != expected_paths["diff"]:
        _error(errors, "DELIVERY_PATH_INVALID", "review diff path is not exact")
    if review_set_binding.get("path") != expected_paths["review_set"]:
        _error(errors, "DELIVERY_PATH_INVALID", "review-set path is not exact")

    harness_files = document.get("final_harness_files")
    if not isinstance(harness_files, list) or len(harness_files) != 2:
        _error(
            errors,
            "FINAL_HARNESS_SET_INVALID",
            "exactly two Harness files are required",
        )
    else:
        validated = [
            _validate_bound_artifact(
                item,
                root=root,
                fields=ARTIFACT_BINDING_FIELDS,
                errors=errors,
                location=f"final_harness_files[{index}]",
            )
            for index, item in enumerate(harness_files)
        ]
        path_values = [item.get("path") for item in validated]
        if any(not isinstance(path, str) for path in path_values):
            _error(errors, "FINAL_HARNESS_SET_INVALID", "Harness file paths must be strings")
        elif set(path_values) != {
            ".harness/allowed_files.md",
            ".harness/review_checklist.md",
        }:
            _error(errors, "FINAL_HARNESS_SET_INVALID", "Harness file set is not exact")
        elif any(not isinstance(item, dict) for item in harness_files):
            _error(errors, "FINAL_HARNESS_SET_INVALID", "Harness file bindings must be objects")
        elif harness_files != sorted(harness_files, key=lambda item: item["path"]):
            _error(
                errors, "FINAL_HARNESS_SET_INVALID", "Harness file set is not sorted"
            )
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _path_allowed(path: str, exact: set[str], prefixes: tuple[str, ...]) -> bool:
    return path in exact or any(path.startswith(prefix) for prefix in prefixes)


def _validate_record_shape(
    record: dict[str, Any], errors: list[dict[str, str]]
) -> None:
    _strict_fields(record, TOP_FIELDS, errors, "record")
    source = _strict_fields(
        record.get("authority_source"), SOURCE_FIELDS, errors, "authority_source"
    )
    scope = _strict_fields(record.get("scope"), SCOPE_FIELDS, errors, "scope")
    rules = _strict_fields(
        scope.get("allowed_path_rules"),
        PATH_RULE_FIELDS,
        errors,
        "scope.allowed_path_rules",
    )
    _strict_fields(
        record.get("planning_baseline"), BASE_FIELDS, errors, "planning_baseline"
    )
    target = _strict_fields(
        record.get("vcs_target"), TARGET_FIELDS, errors, "vcs_target"
    )

    if record.get("schema_version") != SCHEMA_VERSION:
        _error(errors, "SCHEMA_VERSION_INVALID", "unsupported authority schema")
    if not isinstance(record.get("stage_id"), str) or not SAFE_STAGE.fullmatch(
        record["stage_id"]
    ):
        _error(errors, "STAGE_INVALID", "stage_id is not canonical")
    if not isinstance(record.get("authority_epoch"), int) or isinstance(
        record.get("authority_epoch"), bool
    ):
        _error(errors, "EPOCH_INVALID", "authority_epoch must be an integer")
    if source.get("kind") != "host_direct_user_instruction":
        _error(errors, "AUTHORITY_SOURCE_INVALID", "authority source kind is invalid")
    host_reference = source.get("host_reference")
    if (
        not isinstance(host_reference, str)
        or not host_reference.strip()
        or len(host_reference) > 256
        or any(marker in host_reference for marker in ("\n", "\r"))
    ):
        _error(errors, "HOST_REFERENCE_INVALID", "host_reference is required")

    if not isinstance(scope.get("risk"), str) or scope.get("risk") not in {
        "low",
        "medium",
        "high",
    }:
        _error(errors, "RISK_INVALID", "scope risk is invalid")
    if (
        not isinstance(scope.get("summary"), str)
        or not scope.get("summary", "").strip()
        or len(scope.get("summary", "")) > 500
    ):
        _error(errors, "SCOPE_INVALID", "scope summary is required")
    exact = rules.get("exact")
    prefixes = rules.get("prefixes")
    if not isinstance(exact, list) or not all(_canonical_path(item) for item in exact):
        _error(errors, "PATH_RULE_INVALID", "exact path rules are not canonical")
    elif exact != sorted(set(exact)):
        _error(
            errors, "PATH_RULE_INVALID", "exact path rules must be sorted and unique"
        )
    if not isinstance(prefixes, list) or not all(
        _canonical_path(item, prefix=True) for item in prefixes
    ):
        _error(errors, "PATH_RULE_INVALID", "prefix path rules are not canonical")
    elif prefixes != sorted(set(prefixes)):
        _error(
            errors, "PATH_RULE_INVALID", "prefix path rules must be sorted and unique"
        )
    non_goals = scope.get("non_goals")
    if not isinstance(non_goals, list) or not all(
        isinstance(item, str) and item.strip() and len(item) <= 200
        for item in non_goals
    ):
        _error(errors, "NON_GOALS_INVALID", "non_goals must be non-empty strings")
    elif len(non_goals) != len(set(non_goals)):
        _error(errors, "NON_GOALS_INVALID", "non_goals must be unique")
    if not isinstance(
        scope.get("active_allowed_files_sha256"), str
    ) or not SHA256.fullmatch(scope["active_allowed_files_sha256"]):
        _error(errors, "ALLOWED_FILES_HASH_INVALID", "allowed-files hash is invalid")
    if record.get("scope_sha256") != _canonical_sha256(scope):
        _error(errors, "SCOPE_HASH_MISMATCH", "scope digest does not match scope")

    baseline = record.get("planning_baseline", {}).get("commit")
    if not isinstance(baseline, str) or not OID.fullmatch(baseline):
        _error(errors, "BASE_OID_INVALID", "planning baseline must be a Git OID")
    if record.get("action_ceiling") not in ACTIONS:
        _error(errors, "ACTION_CEILING_INVALID", "action ceiling is invalid")
    if not isinstance(target.get("remote_name"), str) or not SAFE_REMOTE.fullmatch(
        target.get("remote_name", "")
    ):
        _error(errors, "REMOTE_INVALID", "remote name is invalid")
    for field in ("effective_fetch_url_sha256", "effective_push_url_sha256"):
        if not isinstance(target.get(field), str) or not SHA256.fullmatch(
            target.get(field, "")
        ):
            _error(errors, "REMOTE_FINGERPRINT_INVALID", f"{field} is invalid")
    branch = target.get("target_branch")
    if not _canonical_branch(branch):
        _error(errors, "BRANCH_INVALID", "target branch is invalid")
    tip = target.get("authorized_remote_tip")
    if not isinstance(tip, str) or not OID.fullmatch(tip):
        _error(errors, "REMOTE_TIP_INVALID", "authorized remote tip is invalid")


def _authority_chain(
    authority_dir: Path,
    errors: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[Path]]:
    if authority_dir.is_symlink() or not authority_dir.is_dir():
        _error(errors, "AUTHORITY_DIRECTORY_INVALID", "authority directory is invalid")
        return [], []
    entries = sorted(authority_dir.iterdir(), key=lambda item: item.name)
    paths: list[Path] = []
    for entry in entries:
        if entry.name == "delivery-binding.json":
            if entry.is_symlink() or not entry.is_file():
                _error(errors, "AUTHORITY_ENTRY_INVALID", "delivery binding is invalid")
            continue
        match = EPOCH_NAME.fullmatch(entry.name)
        if not match or entry.is_symlink() or not entry.is_file():
            _error(errors, "AUTHORITY_ENTRY_INVALID", "unexpected authority entry")
            continue
        paths.append(entry)
    records: list[dict[str, Any]] = []
    for expected_epoch, path in enumerate(paths, start=1):
        match = EPOCH_NAME.fullmatch(path.name)
        assert match is not None
        filename_epoch = int(match.group(1))
        if filename_epoch != expected_epoch:
            _error(errors, "AUTHORITY_LINEAGE_GAP", "authority epochs are not linear")
        record = _read_json(path, errors)
        records.append(record)
        _validate_record_shape(record, errors)
        if record.get("authority_epoch") != filename_epoch:
            _error(
                errors, "EPOCH_FILENAME_MISMATCH", "record epoch differs from filename"
            )
        if expected_epoch == 1:
            if record.get("supersedes_record_sha256") is not None:
                _error(errors, "LINEAGE_INVALID", "epoch 1 must not supersede a record")
        else:
            predecessor_hash = _sha256(paths[expected_epoch - 2].read_bytes())
            if record.get("supersedes_record_sha256") != predecessor_hash:
                _error(errors, "LINEAGE_INVALID", "predecessor hash is invalid")
    return records, paths


def _validate_review_metadata(
    root: Path, stage: str, errors: list[dict[str, str]]
) -> None:
    review_dir = root / ".harness" / "reviews" / stage / "implementation"
    if not review_dir.exists():
        return
    allowed = set(REVIEW_METADATA_NAMES)
    for entry in review_dir.iterdir():
        if entry.name not in allowed or entry.is_symlink() or not entry.is_file():
            _error(
                errors,
                "UNEXPECTED_REVIEW_METADATA",
                "implementation review metadata set is not closed",
            )


def _validate_review_set_input(
    *,
    root: Path,
    stage: str,
    review_set_path: str | Path | None,
    required_review_slots: int | None,
    expected_review_packet_sha256: str | None,
    current_manifest: Mapping[str, Any] | None,
    errors: list[dict[str, str]],
) -> None:
    if review_set_path is None or required_review_slots is None:
        _error(errors, "IMPLEMENTATION_REVIEW_REQUIRED", "review set is required")
        return
    expected_path = (
        root / ".harness" / "reviews" / stage / "implementation" / "review-set.json"
    )
    path = Path(review_set_path)
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        _error(errors, "IMPLEMENTATION_REVIEW_INVALID", "review set is unavailable")
        return
    expected_relative = expected_path.relative_to(root).as_posix()
    if (
        _path_traverses_symlink(root, expected_relative)
        or resolved != expected_path.resolve()
    ):
        _error(errors, "IMPLEMENTATION_REVIEW_INVALID", "review set path is not exact")
        return
    try:
        review_set = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _error(errors, "IMPLEMENTATION_REVIEW_INVALID", "review set is unreadable")
        return
    try:
        report = validate_review_set(
            review_set,
            project_root=root,
            expected_stage=stage,
            expected_phase="implementation",
            required_slots=required_review_slots,
        )
    except (OSError, TypeError, UnicodeError, ValueError):
        _error(
            errors,
            "IMPLEMENTATION_REVIEW_INVALID",
            "review set contains an invalid path or value",
        )
        return
    if report["status"] != "PASS":
        _error(errors, "IMPLEMENTATION_REVIEW_INVALID", "review set did not validate")
    if expected_review_packet_sha256 is None or (
        report.get("packet_sha256") != expected_review_packet_sha256
    ):
        _error(
            errors, "REVIEW_PACKET_MISMATCH", "review packet differs from host value"
        )
    if current_manifest is not None:
        expected_artifacts: list[dict[str, str]] = []
        for item in current_manifest.get("changes", []):
            if item.get("kind") == "file":
                expected_artifacts.append(
                    {"path": item["path"], "sha256": item["sha256"]}
                )
        for name in ("reviewed-change-manifest.json", "reviewed-change.diff"):
            artifact_path = expected_path.with_name(name)
            if not artifact_path.is_file():
                continue
            expected_artifacts.append(
                {
                    "path": artifact_path.relative_to(root).as_posix(),
                    "sha256": _sha256(artifact_path.read_bytes()),
                }
            )
        baseline = review_set.get("baseline")
        declared_artifacts = (
            baseline.get("artifacts") if isinstance(baseline, dict) else None
        )
        artifacts_well_formed = isinstance(declared_artifacts, list) and all(
            isinstance(item, dict)
            and set(item) == {"path", "sha256"}
            and isinstance(item.get("path"), str)
            and isinstance(item.get("sha256"), str)
            for item in declared_artifacts
        )
        if not artifacts_well_formed or sorted(
            declared_artifacts, key=lambda item: item["path"]
        ) != sorted(expected_artifacts, key=lambda item: item["path"]):
            _error(
                errors,
                "REVIEW_SUBJECT_COVERAGE_MISMATCH",
                "review packet does not exactly cover the current subject and metadata tail",
            )


def _validate_current_manifest(
    *,
    root: Path,
    stage: str,
    planning_base: str,
    errors: list[dict[str, str]],
) -> dict[str, Any] | None:
    manifest_path = (
        root
        / ".harness"
        / "reviews"
        / stage
        / "implementation"
        / "reviewed-change-manifest.json"
    )
    diff_path = manifest_path.with_name("reviewed-change.diff")
    manifest_relative = manifest_path.relative_to(root).as_posix()
    diff_relative = diff_path.relative_to(root).as_posix()
    if _path_traverses_symlink(root, manifest_relative) or _path_traverses_symlink(
        root, diff_relative
    ):
        _error(errors, "REVIEW_ARTIFACT_INVALID", "review artifact is a symlink")
        return None
    try:
        declared = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _error(errors, "REVIEW_MANIFEST_INVALID", "review manifest is unreadable")
        return None
    if not isinstance(declared, dict):
        _error(errors, "REVIEW_MANIFEST_INVALID", "review manifest must be an object")
        return None
    if not _review_manifest_shape_valid(declared):
        _error(errors, "REVIEW_MANIFEST_SCHEMA_INVALID", "review manifest schema or file modes are invalid")
        return None
    if not diff_path.is_file():
        _error(errors, "REVIEW_DIFF_MISSING", "reviewed change diff is unavailable")
    else:
        try:
            expected_diff = build_reviewed_inventory_bytes(declared)
        except TypeError:
            _error(errors, "REVIEW_DIFF_INVALID", "reviewed change inventory is invalid")
        else:
            if diff_path.read_bytes() != expected_diff:
                _error(
                    errors,
                    "REVIEW_DIFF_DRIFT",
                    "reviewed change inventory differs from the manifest",
                )
    actual = build_review_subject_manifest(
        project_root=root,
        stage_id=stage,
        planning_base=planning_base,
    )
    if actual["status"] != "PASS":
        _error(
            errors, "REVIEW_MANIFEST_REBUILD_FAILED", "manifest could not be rebuilt"
        )
    elif declared != actual["manifest"]:
        _error(
            errors,
            "REVIEW_MANIFEST_DRIFT",
            "review manifest differs from current files",
        )
    return declared if actual["status"] == "PASS" else None


def validate_authority(
    *,
    project_root: str | Path,
    authority_dir: str | Path,
    required_action: str,
    expected_stage: str,
    expected_epoch: int,
    expected_authority_record_sha256: str,
    expected_risk: str,
    expected_scope_sha256: str,
    expected_planning_base: str,
    expected_action_ceiling: str,
    expected_remote_name: str,
    expected_effective_fetch_url_sha256: str,
    expected_effective_push_url_sha256: str,
    expected_target_branch: str,
    expected_authorized_remote_tip: str,
    implementation_review_set: str | Path | None = None,
    required_review_slots: int | None = None,
    expected_review_packet_sha256: str | None = None,
    delivery_binding: str | Path | None = None,
    expected_candidate_head: str | None = None,
    explicit_source_oid: str | None = None,
    merge_target_worktree: str | Path | None = None,
    expected_target_premerge_head: str | None = None,
    replay_activation_requested: bool = False,
    replay_report: Mapping[str, Any] | None = None,
    stage_cohort: str = "v1",
) -> dict[str, Any]:
    """Validate one action against host-retained expected authority values."""

    errors: list[dict[str, str]] = []
    # Replay/v2 is intentionally dormant. A repository/CLI value cannot prove the
    # external provider-neutral host capability or change an active v1 decision.
    if replay_activation_requested:
        _error(
            errors,
            "HOST_STATE_UNAVAILABLE",
            "external provider-neutral stage state is unavailable",
        )
    if stage_cohort != "v1":
        _error(
            errors,
            "COHORT_SELECTION_FORBIDDEN",
            "active v1 authority cannot be reinterpreted by caller-selected schema",
        )
    del replay_report
    root = Path(project_root).resolve()
    directory = Path(authority_dir)
    if not directory.is_absolute():
        directory = root / directory
    directory_valid = True
    try:
        resolved_directory = directory.resolve()
        resolved_directory.relative_to(root)
    except (OSError, ValueError):
        directory_valid = False
        _error(
            errors, "AUTHORITY_DIRECTORY_INVALID", "authority directory escapes root"
        )
    else:
        try:
            relative_directory = directory.relative_to(root).as_posix()
        except ValueError:
            directory_valid = False
            _error(
                errors,
                "AUTHORITY_DIRECTORY_INVALID",
                "authority directory syntax escapes root",
            )
        else:
            if _path_traverses_symlink(root, relative_directory):
                directory_valid = False
                _error(
                    errors,
                    "AUTHORITY_DIRECTORY_INVALID",
                    "authority directory traverses a symlink",
                )
    expected_directory = root / ".harness" / "authority" / expected_stage
    try:
        expected_resolved_directory = expected_directory.resolve()
    except OSError:
        expected_resolved_directory = expected_directory
    if directory_valid and resolved_directory != expected_resolved_directory:
        directory_valid = False
        _error(
            errors,
            "AUTHORITY_DIRECTORY_PATH_MISMATCH",
            "authority directory is not the canonical stage authority directory",
        )
    if directory_valid:
        records, paths = _authority_chain(directory, errors)
    else:
        records, paths = [], []
    record = records[-1] if records else {}
    record_path = paths[-1] if paths else None

    action_valid = isinstance(required_action, str) and required_action in ACTIONS
    if not action_valid:
        _error(errors, "REQUIRED_ACTION_INVALID", "required action is invalid")
    if record.get("stage_id") != expected_stage:
        _error(errors, "EXPECTED_STAGE_MISMATCH", "stage differs from host value")
    if record.get("authority_epoch") != expected_epoch or expected_epoch != len(
        records
    ):
        _error(errors, "EXPECTED_EPOCH_MISMATCH", "epoch differs from current head")
    if record_path is None or _sha256(record_path.read_bytes()) != (
        expected_authority_record_sha256
    ):
        _error(
            errors,
            "EXPECTED_RECORD_HASH_MISMATCH",
            "record hash differs from host value",
        )

    scope = record.get("scope") if isinstance(record.get("scope"), dict) else {}
    baseline = record.get("planning_baseline")
    baseline = baseline if isinstance(baseline, dict) else {}
    target = record.get("vcs_target")
    target = target if isinstance(target, dict) else {}
    comparisons = (
        (scope.get("risk"), expected_risk, "EXPECTED_RISK_MISMATCH"),
        (
            record.get("scope_sha256"),
            expected_scope_sha256,
            "EXPECTED_SCOPE_MISMATCH",
        ),
        (
            baseline.get("commit"),
            expected_planning_base,
            "EXPECTED_BASE_MISMATCH",
        ),
        (
            record.get("action_ceiling"),
            expected_action_ceiling,
            "EXPECTED_CEILING_MISMATCH",
        ),
        (
            target.get("remote_name"),
            expected_remote_name,
            "EXPECTED_REMOTE_MISMATCH",
        ),
        (
            target.get("effective_fetch_url_sha256"),
            expected_effective_fetch_url_sha256,
            "EXPECTED_FETCH_ENDPOINT_MISMATCH",
        ),
        (
            target.get("effective_push_url_sha256"),
            expected_effective_push_url_sha256,
            "EXPECTED_PUSH_ENDPOINT_MISMATCH",
        ),
        (
            target.get("target_branch"),
            expected_target_branch,
            "EXPECTED_BRANCH_MISMATCH",
        ),
        (
            target.get("authorized_remote_tip"),
            expected_authorized_remote_tip,
            "EXPECTED_REMOTE_TIP_MISMATCH",
        ),
    )
    for actual, expected, code in comparisons:
        if actual != expected:
            _error(errors, code, "record differs from host-retained expected value")

    ceiling = record.get("action_ceiling")
    if (
        action_valid
        and ceiling in ACTIONS
        and ACTIONS.index(required_action) > ACTIONS.index(ceiling)
    ):
        _error(errors, "ACTION_EXCEEDS_CEILING", "action exceeds authority ceiling")

    ok, _ = _git(root, "cat-file", "-e", f"{expected_planning_base}^{{commit}}")
    if not ok:
        _error(errors, "PLANNING_BASE_MISSING", "planning base is unavailable")
    else:
        ok, _ = _git(
            root, "merge-base", "--is-ancestor", expected_planning_base, "HEAD"
        )
        if not ok:
            _error(errors, "BASE_ANCESTRY_INVALID", "planning base is not an ancestor")

    changed_paths = _changed_paths(root, expected_planning_base, errors)
    gitlink_paths = _gitlink_paths(root, expected_planning_base, errors)
    rules = scope.get("allowed_path_rules")
    rules = rules if isinstance(rules, dict) else {}
    exact_values = rules.get("exact")
    prefix_values = rules.get("prefixes")
    exact = (
        {
            item
            for item in exact_values
            if isinstance(item, str) and _canonical_path(item)
        }
        if isinstance(exact_values, list)
        else set()
    )
    prefixes = (
        tuple(
            item
            for item in prefix_values
            if isinstance(item, str) and _canonical_path(item, prefix=True)
        )
        if isinstance(prefix_values, list)
        else ()
    )
    for path in sorted(changed_paths):
        if not _canonical_path(path) or not _path_allowed(path, exact, prefixes):
            _error(
                errors, "SCOPE_PATH_ESCAPE", "a changed path is outside authority scope"
            )
        if path in gitlink_paths:
            _error(errors, "GITLINK_FORBIDDEN", "a changed path is a gitlink")

    if action_valid and required_action in {"plan", "implement", "archive"}:
        allowed_path = root / ".harness" / "allowed_files.md"
        if allowed_path.is_symlink() or not allowed_path.is_file():
            _error(errors, "ALLOWED_FILES_INVALID", "allowed-files control is invalid")
        elif _sha256(allowed_path.read_bytes()) != scope.get(
            "active_allowed_files_sha256"
        ):
            _error(
                errors, "ALLOWED_FILES_DRIFT", "allowed-files changed after approval"
            )

    _validate_review_metadata(root, expected_stage, errors)
    current_manifest: Mapping[str, Any] | None = None
    if action_valid and required_action in {"commit", "archive", "merge", "push"}:
        current_manifest = _validate_current_manifest(
            root=root,
            stage=expected_stage,
            planning_base=expected_planning_base,
            errors=errors,
        )
        _validate_review_set_input(
            root=root,
            stage=expected_stage,
            review_set_path=implementation_review_set,
            required_review_slots=required_review_slots,
            expected_review_packet_sha256=expected_review_packet_sha256,
            current_manifest=current_manifest,
            errors=errors,
        )
    if action_valid and required_action in {"commit", "merge", "push"}:
        if delivery_binding is None:
            _error(errors, "DELIVERY_BINDING_REQUIRED", "delivery binding is required")
        else:
            expected_delivery_path = (
                root
                / ".harness"
                / "authority"
                / expected_stage
                / "delivery-binding.json"
            )
            binding_path = Path(delivery_binding)
            if not binding_path.is_absolute():
                binding_path = root / binding_path
            try:
                binding_resolved = binding_path.resolve(strict=True)
                binding_document = json.loads(
                    binding_resolved.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError, json.JSONDecodeError):
                _error(errors, "DELIVERY_BINDING_INVALID", "binding is unreadable")
            else:
                if (
                    binding_path.is_symlink()
                    or binding_resolved != expected_delivery_path.resolve()
                ):
                    _error(
                        errors, "DELIVERY_BINDING_INVALID", "binding path is not exact"
                    )
                delivery_report = validate_delivery_binding(
                    binding_document,
                    project_root=root,
                    expected_stage=expected_stage,
                    expected_epoch=expected_epoch,
                    expected_authority_record_sha256=(expected_authority_record_sha256),
                    expected_review_packet_sha256=(expected_review_packet_sha256 or ""),
                )
                if delivery_report["status"] != "PASS":
                    _error(
                        errors,
                        "DELIVERY_BINDING_INVALID",
                        "delivery binding did not validate",
                    )
    if required_action == "commit" and current_manifest is not None:
        _validate_commit_index_projection(
            root=root,
            planning_base=expected_planning_base,
            stage=expected_stage,
            manifest=current_manifest,
            errors=errors,
        )
    if action_valid and required_action in {"merge", "push"}:
        if not isinstance(expected_candidate_head, str) or not OID.fullmatch(
            expected_candidate_head or ""
        ):
            _error(errors, "CANDIDATE_HEAD_REQUIRED", "candidate HEAD is required")
        else:
            ok, head = _git(root, "rev-parse", "HEAD")
            if not ok or head.strip() != expected_candidate_head:
                _error(
                    errors,
                    "CANDIDATE_HEAD_DRIFT",
                    "current HEAD differs from candidate",
                )
        if explicit_source_oid != expected_candidate_head:
            _error(
                errors,
                "EXPLICIT_SOURCE_MISMATCH",
                "explicit source differs from candidate",
            )

    if required_action == "merge":
        if (
            merge_target_worktree is None
            or not isinstance(expected_target_premerge_head, str)
            or OID.fullmatch(expected_target_premerge_head or "") is None
        ):
            _error(
                errors,
                "MERGE_TARGET_INPUT_REQUIRED",
                "target worktree and expected pre-merge HEAD are required",
            )
        elif isinstance(expected_candidate_head, str):
            if expected_target_premerge_head != expected_authorized_remote_tip:
                _error(
                    errors,
                    "MERGE_TARGET_TIP_MISMATCH",
                    "target pre-merge HEAD differs from the authorized remote tip",
                )
            _validate_clean_worktree(
                root,
                expected_branch=None,
                expected_head=expected_candidate_head,
                errors=errors,
                code_prefix="FEATURE_WORKTREE",
            )
            target_root = Path(merge_target_worktree).resolve()
            _validate_clean_worktree(
                target_root,
                expected_branch=expected_target_branch,
                expected_head=expected_target_premerge_head,
                errors=errors,
                code_prefix="TARGET_WORKTREE",
            )
            feature_common = _git_common_dir(root, errors)
            target_common = _git_common_dir(target_root, errors)
            if (
                feature_common is not None
                and target_common is not None
                and feature_common != target_common
            ):
                _error(
                    errors,
                    "MERGE_REPOSITORY_MISMATCH",
                    "feature and target worktrees are not from the same repository",
                )
            _, live_tip = _validate_live_remote(
                target_root,
                remote_name=expected_remote_name,
                target_branch=expected_target_branch,
                expected_fetch_sha256=expected_effective_fetch_url_sha256,
                expected_push_sha256=expected_effective_push_url_sha256,
                errors=errors,
            )
            if live_tip is not None and live_tip != expected_authorized_remote_tip:
                _error(errors, "LIVE_REMOTE_TIP_MISMATCH", "remote target moved")
            ok, _ = _git(
                root,
                "merge-base",
                "--is-ancestor",
                expected_authorized_remote_tip,
                expected_candidate_head,
            )
            if not ok:
                _error(errors, "NON_FAST_FORWARD", "authorized tip is not an ancestor")

    if required_action == "push" and isinstance(expected_candidate_head, str):
        _validate_clean_worktree(
            root,
            expected_branch=expected_target_branch,
            expected_head=expected_candidate_head,
            errors=errors,
            code_prefix="PUSH_WORKTREE",
        )
        _, remote_tip = _validate_live_remote(
            root,
            remote_name=expected_remote_name,
            target_branch=expected_target_branch,
            expected_fetch_sha256=expected_effective_fetch_url_sha256,
            expected_push_sha256=expected_effective_push_url_sha256,
            errors=errors,
        )
        if remote_tip is not None and remote_tip != expected_authorized_remote_tip:
            _error(errors, "LIVE_REMOTE_TIP_MISMATCH", "remote target moved")
        ok, _ = _git(
            root,
            "merge-base",
            "--is-ancestor",
            expected_authorized_remote_tip,
            expected_candidate_head,
        )
        if not ok:
            _error(errors, "NON_FAST_FORWARD", "authorized tip is not an ancestor")

    passed = not errors
    return {
        "schema_version": REPORT_SCHEMA,
        "status": "PASS" if passed else "FAIL",
        "claim_level": "mechanical_consistency_only",
        "binding_consistent": passed,
        "technical_ready": "external" if passed else False,
        "human_authorized": "external" if passed else False,
        "vcs_pushed": "not_attempted",
        "stage_id": expected_stage,
        "required_action": required_action if isinstance(required_action, str) else None,
        "current_epoch": record.get("authority_epoch"),
        "changed_paths": sorted(changed_paths),
        "errors": errors,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate stage authority binding")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--authority-dir", required=True)
    parser.add_argument("--required-action", choices=ACTIONS, required=True)
    parser.add_argument("--expected-stage", required=True)
    parser.add_argument("--expected-epoch", type=int, required=True)
    parser.add_argument("--expected-authority-record-sha256", required=True)
    parser.add_argument(
        "--expected-risk", choices=("low", "medium", "high"), required=True
    )
    parser.add_argument("--expected-scope-sha256", required=True)
    parser.add_argument("--expected-planning-base", required=True)
    parser.add_argument("--expected-action-ceiling", choices=ACTIONS, required=True)
    parser.add_argument("--expected-remote-name", required=True)
    parser.add_argument("--expected-effective-fetch-url-sha256", required=True)
    parser.add_argument("--expected-effective-push-url-sha256", required=True)
    parser.add_argument("--expected-target-branch", required=True)
    parser.add_argument("--expected-authorized-remote-tip", required=True)
    parser.add_argument("--implementation-review-set")
    parser.add_argument("--required-review-slots", type=int)
    parser.add_argument("--expected-review-packet-sha256")
    parser.add_argument("--delivery-binding")
    parser.add_argument("--expected-candidate-head")
    parser.add_argument("--explicit-source-oid")
    parser.add_argument("--merge-target-worktree")
    parser.add_argument("--expected-target-premerge-head")
    parser.add_argument("--replay-activation-requested", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = vars(_parser().parse_args(argv))
    report = validate_authority(**args)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
