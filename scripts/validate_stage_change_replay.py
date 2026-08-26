"""Mechanically validate dormant RepoPilot stage change/replay evidence.

This module deliberately cannot authenticate controller context, reviewer dispatch,
direct-user authority, chronology, or Git delivery. Blocking activation belongs to
the external ``provider_neutral.stage_state_cas/v1`` capability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path, PurePosixPath

GATE_GRAPH = (
    "plan_contract", "plan_review", "authority", "implementation",
    "verification", "implementation_review", "archive",
    "post_archive_delivery_review", "candidate", "merge", "push",
)
GRAPH_VERSION = "repopilot.stage_gate_graph/v1"
FACT_SEEDS = {
    **{name: "plan_contract" for name in ("requirements", "scope", "non_goals", "risk", "allowed_path_rules", "planning_baseline", "plan_subject")},
    **{name: "authority" for name in ("authority_record", "action_ceiling", "vcs_endpoint", "target_branch", "authorized_remote_tip")},
    **{name: "implementation" for name in ("implementation_subject", "workflow_subject", "template_subject", "verification_contract")},
    "verification_evidence": "verification",
    "implementation_review_binding": "implementation_review",
    "archive_output": "archive",
    "final_delivery_packet": "post_archive_delivery_review",
    "candidate_head": "post_archive_delivery_review",
    "merge_target_state": "merge",
    "push_outcome_evidence": "push",
}
GATE_ADAPTERS = {
    "plan_contract": "openspec_plan_contract/v1",
    "plan_review": "independent_review/v1",
    "authority": "stage_authority_core/v1",
    "implementation": "implementation_subject/v1",
    "verification": "verification_bundle/v1",
    "implementation_review": "independent_review/v1",
    "archive": "openspec_archive/v1",
    "post_archive_delivery_review": "post_archive_delivery_review/v1",
    "candidate": "exact_candidate/v1",
    "merge": "ff_only_merge/v1",
    "push": "exact_lease_push/v1",
}
GATE_PRODUCERS = {
    "plan_contract": "validate_openspec_plan_contract",
    "plan_review": "validate_independent_review",
    "authority": "validate_stage_authority_core",
    "implementation": "build_implementation_subject",
    "verification": "validate_verification_bundle",
    "implementation_review": "validate_independent_review",
    "archive": "validate_openspec_archive",
    "post_archive_delivery_review": "validate_post_archive_delivery_review",
    "candidate": "validate_exact_candidate",
    "merge": "validate_ff_only_merge",
    "push": "reconcile_exact_lease_push",
}
GATE_INPUT_FACTS = {
    "plan_contract": {
        "requirements", "scope", "non_goals", "risk", "allowed_path_rules",
        "planning_baseline", "plan_subject",
    },
    "plan_review": {"plan_subject"},
    "authority": {
        "authority_record", "action_ceiling", "vcs_endpoint", "target_branch",
        "authorized_remote_tip",
    },
    "implementation": {
        "implementation_subject", "workflow_subject", "template_subject",
        "verification_contract",
    },
    "verification": {"verification_evidence"},
    "implementation_review": {
        "implementation_subject", "workflow_subject", "template_subject",
        "verification_contract", "verification_evidence",
        "implementation_review_binding",
    },
    "archive": {"archive_output"},
    "post_archive_delivery_review": {"final_delivery_packet", "candidate_head"},
    "candidate": {"candidate_head"},
    "merge": {"merge_target_state"},
    "push": {"push_outcome_evidence"},
}
GATE_EVIDENCE_REQUIRED_FIELDS = {
    "plan_contract": {"packet_sha256", "strict_openspec_pass"},
    "plan_review": {"phase", "packet_sha256", "host_dispatch_verified", "activation_verified"},
    "authority": {"authority_record_sha256", "expected_envelope_sha256"},
    "implementation": {"manifest_sha256", "allowed_paths_sha256"},
    "verification": {"command_ids", "required_command_ids", "commands"},
    "implementation_review": {"phase", "packet_sha256", "host_dispatch_verified", "activation_verified"},
    "archive": {"active_path", "archive_path", "strict_all_pass"},
    "post_archive_delivery_review": {"packet_sha256", "reviewed_manifest_sha256", "reviewed_inventory_sha256"},
    "candidate": {"candidate_oid", "expected_parent_oid", "single_parent", "projection_sha256"},
    "merge": {"candidate_oid", "target_premerge_oid", "target_postmerge_oid", "ff_only"},
    "push": {"candidate_oid", "old_oid", "remote_tip", "same_endpoint", "outcome"},
}
VERIFICATION_COMMAND_CONTRACT = (
    {"command_id": "pytest", "argv": ["python", "-m", "pytest"], "cwd": "."},
    {"command_id": "ruff", "argv": ["ruff", "check", "."], "cwd": "."},
)
PUSH_RECONCILIATION_REQUIRED_BINDINGS = (
    "push_gate",
    "candidate_oid",
    "effective_endpoint_sha256",
    "target_branch",
    "event_head",
)
ACTION_GATES = {"implement": "implementation", "archive": "archive", "commit": "candidate", "merge": "merge", "push": "push"}
EVENT_CEILINGS = {
    "direct_user_envelope_change": {"requirements", "scope", "non_goals", "risk", "allowed_path_rules", "planning_baseline", "authority_record", "action_ceiling", "vcs_endpoint", "target_branch", "authorized_remote_tip", "plan_subject"},
    "agent_technical_correction": {"plan_subject", "implementation_subject", "workflow_subject", "template_subject", "verification_contract", "verification_evidence"},
    "repository_or_git_drift": {"planning_baseline", "vcs_endpoint", "target_branch", "authorized_remote_tip", "archive_output", "final_delivery_packet", "candidate_head", "merge_target_state", "push_outcome_evidence"},
}
REVIEW_CEILINGS = {
    "plan": {"plan_subject"},
    "implementation": {"implementation_subject", "workflow_subject", "template_subject", "verification_contract", "verification_evidence", "implementation_review_binding"},
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OID = re.compile(r"^[0-9a-f]{40}$")


def _error(errors: list[dict[str, str]], code: str, message: str) -> None:
    errors.append({"code": code, "message": message})


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def _safe_text(value: object, limit: int = 256) -> bool:
    return isinstance(value, str) and 0 < len(value) <= limit and all(32 <= ord(char) < 127 for char in value)


def _safe_path(value: object) -> bool:
    if not _safe_text(value) or not isinstance(value, str) or "\\" in value or value.startswith("/"):
        return False
    path = PurePosixPath(value)
    return path.as_posix() == value and all(part not in {"", ".", ".."} for part in path.parts)


def _canonical_archive_path(value: object, expected_stage: object) -> bool:
    if (
        not _safe_path(value)
        or not isinstance(value, str)
        or not isinstance(expected_stage, str)
        or SAFE_ID.fullmatch(expected_stage) is None
    ):
        return False
    prefix = "openspec/changes/archive/"
    suffix = f"-{expected_stage}"
    if not value.startswith(prefix) or not value.endswith(suffix):
        return False
    date_text = value[len(prefix): -len(suffix)]
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_text) is None:
        return False
    try:
        date.fromisoformat(date_text)
    except ValueError:
        return False
    return True


def derive_replay_sets(
    changed_fact_ids: Sequence[str],
    completed_gate_ids: Sequence[str],
    *,
    declared_resume_step: object | None = None,
) -> dict[str, object]:
    if declared_resume_step is not None:
        raise ValueError("numeric or declared resume points are forbidden")
    if isinstance(changed_fact_ids, (str, bytes)) or not isinstance(changed_fact_ids, Sequence):
        raise ValueError("changed facts must be a sequence")  # noqa: TRY004
    facts = list(changed_fact_ids)
    if (
        not facts
        or any(not isinstance(item, str) for item in facts)
        or len(facts) != len(set(facts))
        or any(item not in FACT_SEEDS for item in facts)
    ):
        raise ValueError("changed facts must be known and unique")
    if isinstance(completed_gate_ids, (str, bytes)) or not isinstance(completed_gate_ids, Sequence):
        raise ValueError("completed gates must be a sequence")  # noqa: TRY004
    completed = list(completed_gate_ids)
    if (
        any(not isinstance(item, str) for item in completed)
        or len(completed) != len(set(completed))
        or any(item not in GATE_GRAPH for item in completed)
    ):
        raise ValueError("completed gates must be known and unique")
    seed_index = min(GATE_GRAPH.index(FACT_SEEDS[item]) for item in facts)
    suffix = list(GATE_GRAPH[seed_index:])
    prefix = list(GATE_GRAPH[:seed_index])
    replayed = [gate for gate in suffix if gate in completed]
    if replayed != suffix[: len(replayed)]:
        raise ValueError("completed replay gates are not a monotonic prefix")
    remaining = suffix[len(replayed) :]
    return {
        "invalidated_gate_ids": suffix,
        "preserved_gate_ids": prefix,
        "required_replay_gate_ids": suffix,
        "replay_frontier_gate_ids": remaining[:1],
        "resume_status": "ready" if not remaining else "replay_required",
    }


def validate_event_classification(
    event_kind: object,
    changed_fact_ids: object,
    *,
    review_phase: object = None,
    review_lineage: object = None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if (
        not isinstance(changed_fact_ids, list)
        or not changed_fact_ids
        or any(not isinstance(item, str) for item in changed_fact_ids)
        or len(changed_fact_ids) != len(set(changed_fact_ids))
    ):
        _error(errors, "CHANGED_FACTS_INVALID", "changed facts must be a non-empty unique list")
        return errors
    if any(item not in FACT_SEEDS for item in changed_fact_ids):
        _error(errors, "CHANGED_FACT_UNKNOWN", "event contains an unknown changed fact")
        return errors
    if not isinstance(event_kind, str):
        _error(errors, "EVENT_KIND_INVALID", "event kind is unsupported")
        return errors
    if event_kind == "review_remediation":
        allowed = REVIEW_CEILINGS.get(review_phase) if isinstance(review_phase, str) else None
        if allowed is None or not set(changed_fact_ids) <= allowed:
            _error(errors, "REVIEW_REMEDIATION_CEILING", "review remediation exceeds its phase ceiling")
        required = {"slot_id", "receipt_sha256", "finding_ids", "affected_evidence"}
        if not isinstance(review_lineage, dict) or set(review_lineage) != required:
            _error(errors, "REVIEW_FINDING_LINEAGE_REQUIRED", "exact same-slot finding lineage is required")
        elif (
            not _safe_text(review_lineage["slot_id"])
            or not isinstance(review_lineage["receipt_sha256"], str)
            or SHA256.fullmatch(review_lineage["receipt_sha256"]) is None
            or not isinstance(review_lineage["finding_ids"], list)
            or not review_lineage["finding_ids"]
            or any(not _safe_text(item) for item in review_lineage["finding_ids"])
            or len(review_lineage["finding_ids"]) != len(set(review_lineage["finding_ids"]))
            or not isinstance(review_lineage["affected_evidence"], list)
            or not review_lineage["affected_evidence"]
            or any(
                not isinstance(item, str) or SHA256.fullmatch(item) is None
                for item in review_lineage["affected_evidence"]
            )
        ):
            _error(errors, "REVIEW_FINDING_LINEAGE_INVALID", "review finding lineage is invalid")
    else:
        allowed = EVENT_CEILINGS.get(event_kind)
        if allowed is None:
            _error(errors, "EVENT_KIND_INVALID", "event kind is unsupported")
        elif not set(changed_fact_ids) <= allowed:
            _error(errors, "EVENT_KIND_CEILING_EXCEEDED", "changed facts exceed the event kind ceiling")
        if review_phase is not None or review_lineage is not None:
            _error(errors, "REVIEW_LINEAGE_UNEXPECTED", "review lineage is only valid for review remediation")
    return errors


def validate_gate_evidence(
    gate_id: str,
    evidence: object,
    *,
    generation: int,
    expected_stage: str | None = None,
    expected_subject_sha256: str | None = None,
    expected_event_head: str | None = None,
    expected_archive_path: str | None = None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(gate_id, str):
        _error(errors, "GATE_EVIDENCE_INVALID", "gate id is invalid")
        return errors
    expected = GATE_ADAPTERS.get(gate_id)
    if expected is None or not isinstance(evidence, dict):
        _error(errors, "GATE_EVIDENCE_INVALID", "gate evidence is invalid")
        return errors
    schema = evidence.get("schema_version")
    if schema != f"repopilot.{expected}":
        _error(errors, "GATE_ADAPTER_SCHEMA_INVALID", "evidence schema does not match the code-owned adapter")
    if evidence.get("producer") != GATE_PRODUCERS[gate_id]:
        _error(errors, "GATE_ADAPTER_PRODUCER_INVALID", "evidence producer does not match the code-owned adapter")
    if evidence.get("generation") != generation:
        _error(errors, "GATE_EVIDENCE_GENERATION_STALE", "evidence generation is stale")
    if evidence.get("status") != "PASS":
        _error(errors, "GATE_EVIDENCE_NOT_PASS", "adapter did not pass")
    if expected_stage is not None and evidence.get("stage_id") != expected_stage:
        _error(errors, "GATE_EVIDENCE_STAGE_MISMATCH", "evidence stage does not match")
    if expected_subject_sha256 is not None and evidence.get("subject_sha256") != expected_subject_sha256:
        _error(errors, "GATE_EVIDENCE_SUBJECT_MISMATCH", "evidence subject does not match")
    if evidence.get("event_head") != expected_event_head:
        _error(errors, "GATE_EVIDENCE_EVENT_HEAD_MISMATCH", "evidence event head is stale")
    common = {"schema_version", "producer", "generation", "stage_id", "subject_sha256", "event_head", "status"}
    required_by_gate = GATE_EVIDENCE_REQUIRED_FIELDS[gate_id]
    if set(evidence) != common | required_by_gate:
        _error(errors, "GATE_EVIDENCE_SCHEMA_INVALID", "gate evidence fields are not exact")
    digest_fields = {
        "packet_sha256", "authority_record_sha256", "expected_envelope_sha256",
        "manifest_sha256", "allowed_paths_sha256", "reviewed_manifest_sha256",
        "reviewed_inventory_sha256", "projection_sha256",
    }
    for field in required_by_gate & digest_fields:
        if not isinstance(evidence.get(field), str) or SHA256.fullmatch(evidence.get(field, "")) is None:
            _error(errors, "GATE_EVIDENCE_DIGEST_INVALID", "gate evidence digest is invalid")
    for field in required_by_gate & {"active_path", "archive_path"}:
        if not _safe_path(evidence.get(field)):
            _error(errors, "GATE_EVIDENCE_PATH_INVALID", "gate evidence path is invalid")
    for field in required_by_gate & {"candidate_oid", "expected_parent_oid", "target_premerge_oid", "target_postmerge_oid", "old_oid", "remote_tip"}:
        if not isinstance(evidence.get(field), str) or OID.fullmatch(evidence.get(field, "")) is None:
            _error(errors, "GATE_EVIDENCE_OID_INVALID", "gate evidence Git object is invalid")
    for field in required_by_gate & {"strict_openspec_pass", "host_dispatch_verified", "activation_verified", "strict_all_pass", "single_parent", "ff_only", "same_endpoint"}:
        if evidence.get(field) is not True:
            _error(errors, "GATE_EVIDENCE_ASSERTION_INVALID", "required gate evidence assertion is not true")
    if gate_id in {"plan_review", "implementation_review"}:
        expected_phase = "plan" if gate_id == "plan_review" else "implementation"
        if evidence.get("phase") != expected_phase:
            _error(errors, "REVIEW_PHASE_INVALID", "review evidence phase is invalid")
    subject_bound_digest = {
        "plan_contract": "packet_sha256",
        "plan_review": "packet_sha256",
        "authority": "expected_envelope_sha256",
        "implementation": "manifest_sha256",
        "implementation_review": "packet_sha256",
        "post_archive_delivery_review": "packet_sha256",
        "candidate": "projection_sha256",
    }.get(gate_id)
    if (
        subject_bound_digest is not None
        and expected_subject_sha256 is not None
        and evidence.get(subject_bound_digest) != expected_subject_sha256
    ):
        _error(errors, "GATE_ESSENTIAL_BINDING_INVALID", "gate evidence does not bind its code-owned subject field")
    if gate_id == "archive":
        if not _canonical_archive_path(expected_archive_path, expected_stage):
            _error(errors, "ARCHIVE_EXPECTED_PATH_INVALID", "host expected archive path is absent or non-canonical")
        if (
            evidence.get("active_path") != f"openspec/changes/{expected_stage}"
            or evidence.get("archive_path") != expected_archive_path
        ):
            _error(errors, "ARCHIVE_PATH_BINDING_INVALID", "archive evidence paths do not exactly bind the host mapping")
    if gate_id == "candidate" and evidence.get("candidate_oid") == evidence.get("expected_parent_oid"):
        _error(errors, "GATE_ESSENTIAL_BINDING_INVALID", "candidate must be a new single-parent commit")
    if gate_id == "merge" and (
        evidence.get("target_postmerge_oid") != evidence.get("candidate_oid")
        or evidence.get("target_premerge_oid") == evidence.get("target_postmerge_oid")
    ):
        _error(errors, "GATE_ESSENTIAL_BINDING_INVALID", "merge evidence does not bind an advancing ff-only target")
    if gate_id == "push" and evidence.get("outcome") == "verified" and (
        evidence.get("remote_tip") != evidence.get("candidate_oid")
        or evidence.get("old_oid") == evidence.get("remote_tip")
    ):
        _error(errors, "GATE_ESSENTIAL_BINDING_INVALID", "verified push evidence does not bind the candidate transition")
    if gate_id == "push" and (
        not isinstance(evidence.get("outcome"), str)
        or evidence.get("outcome") not in {"verified", "unknown"}
    ):
        _error(errors, "PUSH_OUTCOME_INVALID", "push reconciliation outcome is invalid")
    if gate_id == "verification":
        command_ids = evidence.get("command_ids")
        required = evidence.get("required_command_ids")
        expected_command_ids = [
            item["command_id"] for item in VERIFICATION_COMMAND_CONTRACT
        ]
        if (
            not isinstance(command_ids, list)
            or not isinstance(required, list)
            or any(not isinstance(item, str) for item in command_ids + required)
            or len(command_ids) != len(set(command_ids))
            or len(required) != len(set(required))
            or command_ids != required
            or command_ids != expected_command_ids
        ):
            _error(errors, "VERIFICATION_COMMAND_SET_INCOMPLETE", "verification command set is incomplete")
            _error(errors, "VERIFICATION_COMMAND_CONTRACT_MISMATCH", "verification commands differ from the code-owned contract")
        commands = evidence.get("commands")
        command_fields = {"command_id", "argv", "cwd", "exit_code", "output_sha256"}
        if not isinstance(commands, list):
            _error(errors, "VERIFICATION_COMMANDS_INVALID", "verification command records are missing")
        else:
            if len(commands) != len(VERIFICATION_COMMAND_CONTRACT):
                _error(errors, "VERIFICATION_COMMANDS_INVALID", "verification command record set is incomplete")
            for index, command in enumerate(commands):
                contract = (
                    VERIFICATION_COMMAND_CONTRACT[index]
                    if index < len(VERIFICATION_COMMAND_CONTRACT)
                    else None
                )
                if (
                    not isinstance(command, dict)
                    or set(command) != command_fields
                    or contract is None
                    or command.get("command_id") != contract["command_id"]
                    or command.get("argv") != contract["argv"]
                    or command.get("cwd") != contract["cwd"]
                    or command.get("exit_code") != 0
                    or not isinstance(command.get("output_sha256"), str)
                    or SHA256.fullmatch(command.get("output_sha256", "")) is None
                ):
                    _error(errors, "VERIFICATION_COMMAND_INVALID", "verification command binding is invalid")
    if gate_id in {"plan_review", "implementation_review"} and evidence.get("host_dispatch_verified") is not True:
        _error(errors, "REVIEW_HOST_DISPATCH_UNVERIFIED", "mechanical review output lacks host dispatch proof")
    if gate_id == "authority" and any(key in evidence for key in ("replay_report", "outer_authority_report")):
        _error(errors, "AUTHORITY_REPLAY_RECURSION", "authority core evidence must precede replay")
    _error(
        errors,
        "EXTERNAL_ADAPTER_ATTESTATION_REQUIRED",
        "caller-supplied adapter evidence cannot prove native producer execution",
    )
    return errors


def _validate_state(value: object, name: str, errors: list[dict[str, str]]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"prior_count", "prior_head", "current_count", "current_head"}:
        _error(errors, f"{name.upper()}_STATE_INVALID", f"{name} state is invalid")
        return {}
    for prefix in ("prior", "current"):
        count = value.get(f"{prefix}_count")
        head = value.get(f"{prefix}_head")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            _error(errors, f"{name.upper()}_COUNT_INVALID", f"{name} count is invalid")
        if (count == 0 and head is not None) or (count > 0 and (not isinstance(head, str) or SHA256.fullmatch(head) is None)):
            _error(errors, f"{name.upper()}_HEAD_INVALID", f"{name} head is invalid")
        current_count = value.get("current_count")
        if (
            isinstance(count, int)
            and not isinstance(count, bool)
            and isinstance(current_count, int)
            and not isinstance(current_count, bool)
            and count >= 0
            and count != 0
            and prefix == "prior"
            and count > current_count
        ):
            _error(errors, f"{name.upper()}_CAS_INVALID", f"{name} prior state exceeds current state")
    return value


def _live_git_identity(root: Path, argument: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", argument], cwd=root, check=True,
            capture_output=True, text=True, timeout=5,
        )
        value = Path(completed.stdout.strip())
        if not value.is_absolute():
            value = root / value
        return _sha256(str(value.resolve(strict=True)).encode())
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _path_has_symlink_component(root: Path, target: Path) -> bool:
    """Reject lexical descendants that traverse a symlink before consumption."""

    try:
        relative = target.absolute().relative_to(root.absolute())
    except ValueError:
        return True
    cursor = root.absolute()
    if cursor.is_symlink():
        return True
    for component in relative.parts:
        cursor /= component
        if cursor.is_symlink():
            return True
    return False


def _read_lineage(
    directory: Path,
    prefix: str,
    errors: list[dict[str, str]],
    *,
    expected_stage: str,
) -> tuple[int, str | None, list[str], list[dict[str, object]]]:
    if not directory.exists():
        return 0, None, [], []
    if directory.is_symlink() or not directory.is_dir():
        _error(errors, "LINEAGE_DIRECTORY_INVALID", "lineage directory is invalid")
        return 0, None, [], []
    previous: str | None = None
    hashes: list[str] = []
    documents: list[dict[str, object]] = []
    entries = sorted(directory.iterdir())
    for sequence, path in enumerate(entries, start=1):
        expected = f"{prefix}-{sequence:06d}.json"
        if path.name != expected or path.is_symlink() or not path.is_file():
            _error(errors, "LINEAGE_PATH_INVALID", "lineage contains an unsafe or non-contiguous entry")
            continue
        try:
            raw = path.read_bytes()
            document = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            _error(errors, "LINEAGE_RECORD_UNREADABLE", "lineage record is invalid UTF-8 JSON")
            continue
        predecessor_key = "previous_event_sha256" if prefix == "event" else "previous_receipt_sha256"
        if (
            not isinstance(document, dict)
            or not isinstance(document.get("sequence"), int)
            or isinstance(document.get("sequence"), bool)
            or document.get("sequence") != sequence
            or document.get(predecessor_key) != previous
        ):
            _error(errors, "LINEAGE_PREDECESSOR_INVALID", "lineage sequence or predecessor is invalid")
        if isinstance(document, dict) and prefix == "event":
            expected_fields = {
                "schema_version", "stage_id", "sequence", "previous_event_sha256",
                "host_event_id", "event_kind", "source_reference", "authority_before",
                "authority_requirement", "changed_fact_ids",
                "before_input_snapshot_sha256", "observed_input_snapshot_sha256",
                "review_phase", "review_lineage", "classification_ceiling",
                "payload_sha256",
            }
            if set(document) != expected_fields or document.get("schema_version") != "repopilot.stage_change_event/v1":
                _error(errors, "EVENT_SCHEMA_INVALID", "event schema is not strict")
            if (
                not isinstance(document.get("stage_id"), str)
                or SAFE_ID.fullmatch(document.get("stage_id", "")) is None
                or document.get("stage_id") != expected_stage
            ):
                _error(errors, "EVENT_STAGE_MISMATCH", "event stage differs from the expected stage")
            errors.extend(validate_event_classification(
                document.get("event_kind"), document.get("changed_fact_ids"),
                review_phase=document.get("review_phase"),
                review_lineage=document.get("review_lineage"),
            ))
            payload = {key: value for key, value in document.items() if key != "payload_sha256"}
            if document.get("payload_sha256") != _canonical_sha256(payload):
                _error(errors, "EVENT_PAYLOAD_HASH_INVALID", "event canonical payload digest is invalid")
            authority_before = document.get("authority_before")
            authority_requirement = document.get("authority_requirement")
            if (
                document.get("classification_ceiling") != "mechanical_consistency_only"
                or document.get("stage_id") is None
                or not _safe_text(document.get("host_event_id"))
                or not _safe_text(document.get("source_reference"))
                or not isinstance(authority_before, dict)
                or set(authority_before) != {"epoch", "record_sha256"}
                or not isinstance(authority_before.get("epoch"), int)
                or isinstance(authority_before.get("epoch"), bool)
                or not isinstance(authority_before.get("record_sha256"), str)
                or SHA256.fullmatch(authority_before.get("record_sha256", "")) is None
                or not isinstance(authority_requirement, dict)
                or set(authority_requirement) != {"later_epoch_required", "required_epoch"}
                or not isinstance(authority_requirement.get("later_epoch_required"), bool)
                or not isinstance(document.get("before_input_snapshot_sha256"), str)
                or SHA256.fullmatch(document.get("before_input_snapshot_sha256", "")) is None
                or not isinstance(document.get("observed_input_snapshot_sha256"), str)
                or SHA256.fullmatch(document.get("observed_input_snapshot_sha256", "")) is None
                or document.get("before_input_snapshot_sha256") == document.get("observed_input_snapshot_sha256")
            ):
                _error(errors, "EVENT_BINDING_INVALID", "event binding fields are invalid")
            if document.get("event_kind") == "direct_user_envelope_change":
                required_epoch = authority_requirement.get("required_epoch") if isinstance(authority_requirement, dict) else None
                before_epoch = authority_before.get("epoch") if isinstance(authority_before, dict) else None
                if (
                    not isinstance(authority_requirement, dict)
                    or authority_requirement.get("later_epoch_required") is not True
                    or not isinstance(required_epoch, int)
                    or isinstance(required_epoch, bool)
                    or not isinstance(before_epoch, int)
                    or required_epoch <= before_epoch
                ):
                    _error(errors, "EVENT_AUTHORITY_DELTA_INVALID", "direct-user event does not require a later authority epoch")
            elif isinstance(authority_requirement, dict) and (
                authority_requirement.get("later_epoch_required") is not False
                or authority_requirement.get("required_epoch") is not None
            ):
                _error(errors, "EVENT_AUTHORITY_DELTA_INVALID", "non-owner event cannot require or adopt later authority")
        elif isinstance(document, dict) and prefix == "receipt":
            expected_fields = {
                "schema_version", "stage_id", "sequence", "previous_receipt_sha256",
                "event_count", "event_head", "graph_version",
                "host_snapshot_generation", "authority", "completed_gate_ids",
                "gate_evidence", "invalidated_gate_ids", "preserved_gate_ids",
                "required_replay_gate_ids", "replay_frontier_gate_ids", "claim_level",
            }
            if set(document) != expected_fields or document.get("schema_version") != "repopilot.stage_replay_receipt/v1":
                _error(errors, "RECEIPT_SCHEMA_INVALID", "receipt schema is not strict")
            if document.get("stage_id") != expected_stage:
                _error(errors, "RECEIPT_STAGE_MISMATCH", "receipt stage differs from the expected stage")
            if document.get("graph_version") != GRAPH_VERSION or document.get("claim_level") != "mechanical_consistency_only":
                _error(errors, "RECEIPT_CONTRACT_INVALID", "receipt graph or claim ceiling is invalid")
            authority = document.get("authority")
            completed_values = document.get("completed_gate_ids")
            gate_evidence_values = document.get("gate_evidence")
            if (
                not isinstance(document.get("stage_id"), str)
                or SAFE_ID.fullmatch(document.get("stage_id", "")) is None
                or not isinstance(document.get("event_count"), int)
                or isinstance(document.get("event_count"), bool)
                or document.get("event_count", 0) < 1
                or not isinstance(document.get("event_head"), str)
                or SHA256.fullmatch(document.get("event_head", "")) is None
                or not isinstance(document.get("host_snapshot_generation"), int)
                or isinstance(document.get("host_snapshot_generation"), bool)
                or document.get("host_snapshot_generation", 0) < 1
                or not isinstance(authority, dict)
                or set(authority) != {"epoch", "record_sha256"}
                or not isinstance(authority.get("epoch"), int)
                or isinstance(authority.get("epoch"), bool)
                or authority.get("epoch", 0) < 1
                or not isinstance(authority.get("record_sha256"), str)
                or SHA256.fullmatch(authority.get("record_sha256", "")) is None
                or not isinstance(completed_values, list)
                or any(not isinstance(item, str) for item in completed_values)
                or len(completed_values) != len(set(completed_values))
                or not isinstance(gate_evidence_values, list)
            ):
                _error(errors, "RECEIPT_BINDING_INVALID", "receipt binding fields are invalid")
            for set_field in (
                "invalidated_gate_ids", "preserved_gate_ids",
                "required_replay_gate_ids", "replay_frontier_gate_ids",
            ):
                values = document.get(set_field)
                if (
                    not isinstance(values, list)
                    or any(not isinstance(item, str) for item in values)
                    or len(values) != len(set(values))
                    or any(item not in GATE_GRAPH for item in values)
                ):
                    _error(errors, "RECEIPT_GATE_SET_INVALID", "receipt gate set is invalid")
        previous = _sha256(raw)
        hashes.append(previous)
        if isinstance(document, dict):
            documents.append(document)
    return len(entries), previous, hashes, documents


def validate_stage_change_replay(
    *,
    project_root: str | Path,
    replay_root: str | Path,
    context: object,
    required_action: str,
    activate: bool = False,
    validate_repository_lineage: bool = True,
    cas_mode: str = "preflight",
) -> dict[str, object]:
    errors: list[dict[str, str]] = []
    supplied_project_root = Path(project_root).absolute()
    root = supplied_project_root.resolve()
    if not isinstance(context, Mapping):
        _error(errors, "CONTEXT_SCHEMA_INVALID", "controller context must be an object")
        context = {}
    stage = context.get("stage_id")
    safe_stage = isinstance(stage, str) and SAFE_ID.fullmatch(stage) is not None
    if context.get("schema_version") != "repopilot.controller_stage_context/v1" or not safe_stage:
        _error(errors, "CONTEXT_SCHEMA_INVALID", "controller context schema or stage is invalid")
    context_fields = {
        "schema_version", "capability", "activation_status", "stage_id",
        "planning_base", "workspace_binding", "terminal_state", "event_state",
        "receipt_state", "gate_snapshots", "authority_core_sha256",
        "current_authority", "expected_archive_path", "requested_transition",
    }
    if set(context) not in (context_fields, context_fields | {"changed_fact_ids"}):
        _error(errors, "CONTEXT_FIELDS_INVALID", "controller context fields are not exact")
    binding = context.get("workspace_binding")
    binding_fields = {
        "workspace_id", "initial_project_root_sha256", "git_common_dir_sha256",
        "worktree_git_dir_sha256", "stage_id", "planning_base",
    }
    if not isinstance(binding, dict) or set(binding) != binding_fields:
        _error(errors, "WORKSPACE_BINDING_INVALID", "immutable workspace binding is invalid")
    else:
        digests = (
            binding.get("initial_project_root_sha256"),
            binding.get("git_common_dir_sha256"),
            binding.get("worktree_git_dir_sha256"),
        )
        common_identity = _live_git_identity(root, "--git-common-dir")
        worktree_identity = _live_git_identity(root, "--git-dir")
        if common_identity is None or worktree_identity is None:
            _error(errors, "WORKSPACE_IDENTITY_UNAVAILABLE", "live Git workspace identity is unavailable")
        if (
            not _safe_text(binding.get("workspace_id"))
            or any(not isinstance(item, str) or SHA256.fullmatch(item) is None for item in digests)
            or binding.get("initial_project_root_sha256") != _sha256(str(root).encode())
            or binding.get("initial_project_root_sha256")
            != _sha256(os.fsencode(supplied_project_root))
            or binding.get("stage_id") != stage
            or binding.get("planning_base") != context.get("planning_base")
            or binding.get("git_common_dir_sha256") != common_identity
            or binding.get("worktree_git_dir_sha256") != worktree_identity
        ):
            _error(errors, "WORKSPACE_BINDING_MISMATCH", "live workspace differs from the host-issued binding")
    planning_base = context.get("planning_base")
    if not isinstance(planning_base, str) or OID.fullmatch(planning_base) is None:
        _error(errors, "PLANNING_BASE_INVALID", "planning base is invalid")
    current_authority = context.get("current_authority")
    if (
        not isinstance(current_authority, dict)
        or set(current_authority) != {"epoch", "record_sha256"}
        or not isinstance(current_authority.get("epoch"), int)
        or isinstance(current_authority.get("epoch"), bool)
        or current_authority.get("epoch", 0) < 1
        or not isinstance(current_authority.get("record_sha256"), str)
        or SHA256.fullmatch(current_authority.get("record_sha256", "")) is None
    ):
        _error(errors, "CURRENT_AUTHORITY_INVALID", "current authority binding is invalid")
    authority_core_sha256 = context.get("authority_core_sha256")
    if (
        not isinstance(authority_core_sha256, str)
        or SHA256.fullmatch(authority_core_sha256) is None
    ):
        _error(errors, "AUTHORITY_CORE_DIGEST_INVALID", "authority core report digest is invalid")
    expected_root = root / ".harness" / "change-replay" / (stage if safe_stage else "invalid-stage")
    supplied = Path(replay_root)
    replay_path_safe = True
    try:
        if supplied.is_symlink() or supplied.resolve() != expected_root.resolve():
            _error(errors, "REPLAY_ROOT_MISMATCH", "replay root is not the host-bound canonical stage path")
            replay_path_safe = False
        if _path_has_symlink_component(supplied_project_root, expected_root):
            _error(errors, "REPLAY_ROOT_SYMLINK_FORBIDDEN", "replay root traverses a symlink component")
            replay_path_safe = False
    except OSError:
        _error(errors, "REPLAY_ROOT_MISMATCH", "replay root cannot be resolved")
        replay_path_safe = False

    expected_archive_path = context.get("expected_archive_path")
    if not _canonical_archive_path(expected_archive_path, stage):
        _error(errors, "ARCHIVE_EXPECTED_PATH_INVALID", "host expected archive path is absent or non-canonical")
    elif _path_has_symlink_component(root, root / expected_archive_path):
        _error(errors, "ARCHIVE_PATH_SYMLINK_FORBIDDEN", "expected archive path traverses a symlink component")

    capability = context.get("capability")
    if (
        not isinstance(capability, dict)
        or set(capability) != {"name", "available", "provenance"}
        or capability.get("name") != "provider_neutral.stage_state_cas/v1"
        or capability.get("available") is not False
        or capability.get("provenance") != "external_unavailable"
    ):
        _error(errors, "CAPABILITY_STATE_INVALID", "repository context must keep external host capability unavailable")
    if activate:
        _error(errors, "HOST_STATE_UNAVAILABLE", "repository validation cannot activate the external host capability")
    if context.get("activation_status") != "blocked_on_external_host_capability":
        _error(errors, "ACTIVATION_STATUS_INVALID", "repository activation status must remain blocked")

    terminal = context.get("terminal_state")
    valid_terminal_pairs = {
        ("open", "not_attempted"),
        ("delivery_unknown", "unknown"),
        ("closed", "verified"),
    }
    terminal_valid = (
        isinstance(terminal, dict)
        and set(terminal) == {"status", "push_outcome"}
        and isinstance(terminal.get("status"), str)
        and isinstance(terminal.get("push_outcome"), str)
        and (terminal.get("status"), terminal.get("push_outcome"))
        in valid_terminal_pairs
    )
    if not terminal_valid:
        _error(errors, "TERMINAL_STATE_INVALID", "terminal state shape or status combination is invalid")
    elif terminal.get("status") == "closed":
        _error(errors, "NEW_STAGE_REQUIRED", "closed stages cannot be reused")
    elif terminal.get("status") == "delivery_unknown" and required_action != "reconcile_push":
        _error(errors, "PUSH_RECONCILIATION_ONLY", "unknown push allows same-endpoint reconciliation only")

    event_state = _validate_state(context.get("event_state"), "event", errors)
    receipt_state = _validate_state(context.get("receipt_state"), "receipt", errors)
    if not isinstance(cas_mode, str) or cas_mode not in {
        "preflight",
        "append_event",
        "append_receipt",
    }:
        _error(errors, "CAS_MODE_INVALID", "CAS mode is unsupported")
    else:
        deltas = {
            "event": (
                event_state.get("current_count", -1)
                - event_state.get("prior_count", -1)
                if isinstance(event_state.get("current_count"), int)
                and isinstance(event_state.get("prior_count"), int)
                else None
            ),
            "receipt": (
                receipt_state.get("current_count", -1)
                - receipt_state.get("prior_count", -1)
                if isinstance(receipt_state.get("current_count"), int)
                and isinstance(receipt_state.get("prior_count"), int)
                else None
            ),
        }
        expected_deltas = {
            "preflight": {"event": 0, "receipt": 0},
            "append_event": {"event": 1, "receipt": 0},
            "append_receipt": {"event": 0, "receipt": 1},
        }[cas_mode]
        if deltas != expected_deltas:
            _error(errors, "CAS_STATE_TRANSITION_INVALID", "prior/current lineage state does not match the requested CAS mode")
    if validate_repository_lineage and safe_stage and replay_path_safe:
        local_event_count, local_event_head, event_hashes, event_documents = _read_lineage(
            expected_root / "events", "event", errors, expected_stage=stage
        )
        local_receipt_count, local_receipt_head, receipt_hashes, receipt_documents = _read_lineage(
            expected_root / "receipts", "receipt", errors, expected_stage=stage
        )
        if (local_event_count, local_event_head) != (event_state.get("current_count"), event_state.get("current_head")):
            _error(errors, "EVENT_HOST_STATE_MISMATCH", "repository event lineage differs from retained host state")
        if (local_receipt_count, local_receipt_head) != (receipt_state.get("current_count"), receipt_state.get("current_head")):
            _error(errors, "RECEIPT_HOST_STATE_MISMATCH", "repository receipt lineage differs from retained host state")
        for name, state, hashes in (
            ("EVENT", event_state, event_hashes),
            ("RECEIPT", receipt_state, receipt_hashes),
        ):
            prior_count = state.get("prior_count")
            current_count = state.get("current_count")
            if isinstance(prior_count, int) and isinstance(current_count, int):
                if current_count - prior_count not in {0, 1}:
                    _error(errors, f"{name}_CAS_APPEND_INVALID", "lineage append is not a single contiguous CAS candidate")
                expected_prior = None if prior_count == 0 else (
                    hashes[prior_count - 1] if prior_count <= len(hashes) else "missing"
                )
                if state.get("prior_head") != expected_prior:
                    _error(errors, f"{name}_PREFIX_REWRITTEN", "retained prior head is not the exact local prefix")
        previous_receipt_document: Mapping[str, object] | None = None
        previous_generation = 0
        for receipt_document in receipt_documents:
            count = receipt_document.get("event_count")
            head = receipt_document.get("event_head")
            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 1
                or count > len(event_hashes)
                or head != event_hashes[count - 1]
            ):
                _error(errors, "RECEIPT_EVENT_BINDING_INVALID", "receipt does not bind an exact event lineage head")
            event_document = (
                event_documents[count - 1]
                if isinstance(count, int)
                and not isinstance(count, bool)
                and 1 <= count <= len(event_documents)
                else None
            )
            completed_values = receipt_document.get("completed_gate_ids")
            if isinstance(event_document, Mapping) and isinstance(completed_values, list):
                try:
                    historical_derived = derive_replay_sets(
                        event_document.get("changed_fact_ids"), completed_values
                    )
                except (TypeError, ValueError):
                    _error(errors, "RECEIPT_COMPLETED_GATES_INVALID", "historical receipt completed gates are invalid")
                else:
                    for field in (
                        "invalidated_gate_ids", "preserved_gate_ids",
                        "required_replay_gate_ids", "replay_frontier_gate_ids",
                    ):
                        if receipt_document.get(field) != historical_derived[field]:
                            _error(errors, "RECEIPT_EXACT_SET_MISMATCH", "historical receipt replay sets differ from code-owned recomputation")
                            break
                historical_authority = receipt_document.get("authority")
                event_authority = event_document.get("authority_before")
                requirement = event_document.get("authority_requirement")
                if event_document.get("event_kind") == "direct_user_envelope_change":
                    if (
                        not isinstance(historical_authority, Mapping)
                        or not isinstance(event_authority, Mapping)
                        or not isinstance(requirement, Mapping)
                        or historical_authority.get("epoch") != requirement.get("required_epoch")
                        or historical_authority.get("record_sha256") == event_authority.get("record_sha256")
                    ):
                        _error(errors, "RECEIPT_AUTHORITY_BINDING_INVALID", "historical receipt does not bind the required later authority")
                elif historical_authority != event_authority:
                    _error(errors, "RECEIPT_AUTHORITY_BINDING_INVALID", "historical receipt authority differs from its event")
            historical_bindings = receipt_document.get("gate_evidence")
            if isinstance(completed_values, list) and isinstance(historical_bindings, list):
                if len(historical_bindings) != len(completed_values):
                    _error(errors, "RECEIPT_GATE_EVIDENCE_INVALID", "historical receipt gate evidence set is incomplete")
                for index, binding_item in enumerate(historical_bindings):
                    gate = completed_values[index] if index < len(completed_values) else None
                    if (
                        not isinstance(gate, str)
                        or gate not in GATE_ADAPTERS
                        or not isinstance(binding_item, dict)
                        or set(binding_item) != {"gate_id", "adapter_id", "report_sha256"}
                        or binding_item.get("gate_id") != gate
                        or binding_item.get("adapter_id") != GATE_ADAPTERS[gate]
                        or not isinstance(binding_item.get("report_sha256"), str)
                        or SHA256.fullmatch(binding_item.get("report_sha256", "")) is None
                    ):
                        _error(errors, "RECEIPT_GATE_EVIDENCE_INVALID", "historical receipt gate evidence binding is invalid")
                        break
            generation = receipt_document.get("host_snapshot_generation")
            if (
                not isinstance(generation, int)
                or isinstance(generation, bool)
                or generation < previous_generation
            ):
                _error(errors, "RECEIPT_GENERATION_NON_MONOTONIC", "historical receipt generation is not monotonic")
            elif generation > 0:
                previous_generation = generation
            if previous_receipt_document is not None and previous_receipt_document.get("event_head") == head:
                before = previous_receipt_document.get("completed_gate_ids")
                after = receipt_document.get("completed_gate_ids")
                if (
                    not isinstance(before, list)
                    or not isinstance(after, list)
                    or after[: len(before)] != before
                    or len(after) < len(before)
                ):
                    _error(errors, "RECEIPT_PROGRESS_NON_MONOTONIC", "receipt progress rewrites or shrinks completed gates")
            previous_receipt_document = receipt_document
    else:
        event_documents = []
        receipt_documents = []

    latest_event = event_documents[-1] if event_documents else None

    snapshots = context.get("gate_snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != len(GATE_GRAPH):
        _error(errors, "GATE_SNAPSHOT_SET_INVALID", "gate snapshot set is not exact")
        snapshots = []
    completed: list[str] = []
    external_prerequisites: list[dict[str, str]] = []
    snapshot_by_gate: dict[str, Mapping[str, object]] = {}
    prior_generation = 0
    snapshot_fields = {
        "gate_id", "state", "generation", "adapter_id", "input_sha256",
        "live_input_sha256", "output_sha256", "dependency_digests", "evidence",
    }
    for index, snapshot in enumerate(snapshots):
        if (
            not isinstance(snapshot, dict)
            or set(snapshot) != snapshot_fields
            or snapshot.get("gate_id") != GATE_GRAPH[index]
            or snapshot.get("adapter_id") != GATE_ADAPTERS[GATE_GRAPH[index]]
        ):
            _error(errors, "GATE_SNAPSHOT_INVALID", "gate snapshot order or adapter is invalid")
            continue
        snapshot_by_gate[GATE_GRAPH[index]] = snapshot
        state = snapshot.get("state")
        generation = snapshot.get("generation")
        state_valid = isinstance(state, str) and state in {
            "open",
            "bound",
            "closed",
        }
        if (
            not state_valid
            or not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation <= prior_generation
        ):
            _error(errors, "GATE_SNAPSHOT_INVALID", "gate snapshot lifecycle is invalid")
        else:
            prior_generation = generation
        for field in ("input_sha256", "live_input_sha256"):
            if not isinstance(snapshot.get(field), str) or SHA256.fullmatch(snapshot.get(field, "")) is None:
                _error(errors, "GATE_SNAPSHOT_DIGEST_INVALID", "gate snapshot digest is invalid")
        output = snapshot.get("output_sha256")
        if output is not None and (not isinstance(output, str) or SHA256.fullmatch(output) is None):
            _error(errors, "GATE_SNAPSHOT_DIGEST_INVALID", "gate output digest is invalid")
        dependencies = snapshot.get("dependency_digests")
        if not isinstance(dependencies, list):
            _error(errors, "GATE_DEPENDENCIES_INVALID", "gate dependency bindings are invalid")
            dependencies = []
        dependency_fields = {"gate_id", "generation", "output_sha256"}
        expected_dependencies = (
            list(GATE_GRAPH[:index])[-1:]
            if index and state_valid and state != "open"
            else []
        )
        seen_dependencies: list[str] = []
        for dependency in dependencies:
            if not isinstance(dependency, dict) or set(dependency) != dependency_fields:
                _error(errors, "GATE_DEPENDENCIES_INVALID", "gate dependency binding is malformed")
                continue
            dependency_gate = dependency.get("gate_id")
            seen_dependencies.append(dependency_gate if isinstance(dependency_gate, str) else "")
            upstream = snapshot_by_gate.get(dependency_gate) if isinstance(dependency_gate, str) else None
            if (
                dependency_gate not in expected_dependencies
                or upstream is None
                or dependency.get("generation") != upstream.get("generation")
                or dependency.get("output_sha256") != upstream.get("output_sha256")
            ):
                _error(errors, "GATE_DEPENDENCY_MISMATCH", "gate dependency generation or output changed")
        if seen_dependencies != expected_dependencies:
            _error(errors, "GATE_DEPENDENCY_SET_INVALID", "gate dependency set is not exact")
        if state_valid and state != "open":
            if snapshot.get("input_sha256") != snapshot.get("live_input_sha256"):
                if event_state.get("current_count") == 0:
                    _error(errors, "MATERIAL_CHANGE_EVENT_REQUIRED", "a closed or bound gate input changed without an event")
                elif (
                    not isinstance(latest_event, Mapping)
                    or not isinstance(latest_event.get("changed_fact_ids"), list)
                    or any(
                        not isinstance(item, str)
                        for item in latest_event.get("changed_fact_ids", [])
                    )
                    or not any(
                        item in GATE_INPUT_FACTS[GATE_GRAPH[index]]
                        for item in latest_event.get("changed_fact_ids", [])
                    )
                    or latest_event.get("before_input_snapshot_sha256")
                    != snapshot.get("input_sha256")
                    or latest_event.get("observed_input_snapshot_sha256")
                    != snapshot.get("live_input_sha256")
                ):
                    _error(errors, "GATE_DRIFT_EVENT_BINDING_INVALID", "gate input drift does not bind the exact related event snapshots")
            evidence = snapshot.get("evidence")
            if evidence is None:
                _error(errors, "GATE_EVIDENCE_MISSING", "closed or bound gate evidence is missing")
            else:
                adapter_findings = validate_gate_evidence(
                    GATE_GRAPH[index], evidence, generation=generation,
                    expected_stage=stage if isinstance(stage, str) else None,
                    expected_subject_sha256=snapshot.get("live_input_sha256") if isinstance(snapshot.get("live_input_sha256"), str) else None,
                    expected_event_head=event_state.get("current_head"),
                    expected_archive_path=(
                        expected_archive_path
                        if isinstance(expected_archive_path, str)
                        else None
                    ),
                )
                adapter_errors = [
                    item
                    for item in adapter_findings
                    if item.get("code") != "EXTERNAL_ADAPTER_ATTESTATION_REQUIRED"
                ]
                if any(
                    item.get("code") == "EXTERNAL_ADAPTER_ATTESTATION_REQUIRED"
                    for item in adapter_findings
                ):
                    external_prerequisites.append({
                        "code": "EXTERNAL_ADAPTER_ATTESTATION_REQUIRED",
                        "gate_id": GATE_GRAPH[index],
                        "message": "native adapter producer attestation is externally required",
                    })
                errors.extend(adapter_errors)
                evidence_digest = _canonical_sha256(evidence)
                if (
                    not adapter_errors
                    and snapshot.get("output_sha256")
                    != evidence_digest
                ):
                    _error(errors, "GATE_OUTPUT_BINDING_MISMATCH", "gate output digest does not bind canonical adapter evidence")
                    adapter_errors = [{"code": "GATE_OUTPUT_BINDING_MISMATCH", "message": "gate output mismatch"}]
                if GATE_GRAPH[index] == "authority":
                    if evidence_digest != authority_core_sha256:
                        _error(errors, "GATE_AUTHORITY_CORE_MISMATCH", "authority gate evidence does not bind the authority core report digest")
                        adapter_errors.append({"code": "GATE_AUTHORITY_CORE_MISMATCH", "message": "authority core mismatch"})
                    if (
                        isinstance(current_authority, Mapping)
                        and evidence.get("authority_record_sha256")
                        != current_authority.get("record_sha256")
                    ):
                        _error(errors, "GATE_AUTHORITY_RECORD_MISMATCH", "authority core evidence binds another authority record")
                        adapter_errors.append({"code": "GATE_AUTHORITY_RECORD_MISMATCH", "message": "authority record mismatch"})
                if not adapter_errors:
                    completed.append(GATE_GRAPH[index])
        elif snapshot.get("evidence") is not None or snapshot.get("output_sha256") is not None:
            _error(errors, "OPEN_GATE_HAS_EVIDENCE", "open gate cannot carry closed evidence")

    changed = context.get("changed_fact_ids")
    replay_completed: list[str] = []
    latest_receipt: Mapping[str, object] | None = None
    if event_documents:
        latest_event = event_documents[-1]
        if latest_event.get("stage_id") != stage:
            _error(errors, "EVENT_STAGE_MISMATCH", "event stage differs from controller stage")
        lineage_changed = latest_event.get("changed_fact_ids")
        if changed != lineage_changed:
            _error(errors, "EVENT_CHANGED_FACTS_MISMATCH", "controller changed facts differ from the current event")
        authority_before = latest_event.get("authority_before")
        authority_requirement = latest_event.get("authority_requirement")
        if latest_event.get("event_kind") == "direct_user_envelope_change":
            if (
                not isinstance(authority_before, dict)
                or not isinstance(authority_requirement, dict)
                or not isinstance(current_authority, dict)
                or current_authority.get("epoch")
                != authority_requirement.get("required_epoch")
                or current_authority.get("record_sha256")
                == authority_before.get("record_sha256")
            ):
                _error(errors, "EVENT_AUTHORITY_MISMATCH", "later authority does not match the direct-user event requirement")
        elif (
            isinstance(authority_before, dict)
            and authority_before != current_authority
        ):
            _error(errors, "EVENT_AUTHORITY_MISMATCH", "event authority differs from the retained current authority")
    if receipt_documents:
        latest_receipt = receipt_documents[-1]
        receipt_completed_value = latest_receipt.get("completed_gate_ids")
        if (
            not isinstance(receipt_completed_value, list)
            or any(not isinstance(item, str) for item in receipt_completed_value)
            or len(receipt_completed_value) != len(set(receipt_completed_value))
            or any(item not in GATE_GRAPH for item in receipt_completed_value)
            or receipt_completed_value != sorted(
                receipt_completed_value, key=GATE_GRAPH.index
            )
        ):
            _error(errors, "RECEIPT_COMPLETED_GATES_INVALID", "receipt completed gates are not a monotonic graph prefix")
        else:
            replay_completed = list(receipt_completed_value)
        if (
            latest_receipt.get("stage_id") != stage
            or latest_receipt.get("event_count") != event_state.get("current_count")
            or latest_receipt.get("event_head") != event_state.get("current_head")
            or latest_receipt.get("authority") != current_authority
            or latest_receipt.get("host_snapshot_generation") != prior_generation
        ):
            _error(errors, "RECEIPT_LIVE_BINDING_MISMATCH", "receipt is stale for the live event, authority, or snapshot")
        gate_bindings = latest_receipt.get("gate_evidence")
        expected_binding_fields = {"gate_id", "adapter_id", "report_sha256"}
        if not isinstance(gate_bindings, list) or len(gate_bindings) != len(replay_completed):
            _error(errors, "RECEIPT_GATE_EVIDENCE_INVALID", "receipt gate evidence set is incomplete")
        else:
            for index, binding_item in enumerate(gate_bindings):
                gate = replay_completed[index]
                snapshot = snapshot_by_gate.get(gate)
                evidence = snapshot.get("evidence") if isinstance(snapshot, Mapping) else None
                if (
                    not isinstance(binding_item, dict)
                    or set(binding_item) != expected_binding_fields
                    or binding_item.get("gate_id") != gate
                    or binding_item.get("adapter_id") != GATE_ADAPTERS[gate]
                    or not isinstance(binding_item.get("report_sha256"), str)
                    or SHA256.fullmatch(binding_item.get("report_sha256", "")) is None
                    or not isinstance(evidence, Mapping)
                    or binding_item.get("report_sha256") != _canonical_sha256(evidence)
                ):
                    _error(errors, "RECEIPT_GATE_EVIDENCE_INVALID", "receipt gate evidence binding is invalid")
    derived: dict[str, object]
    if event_state.get("current_count", 0) == 0:
        if changed not in (None, []):
            _error(errors, "CHANGED_FACTS_WITHOUT_EVENT", "changed facts require an event")
        derived = {"invalidated_gate_ids": [], "preserved_gate_ids": [], "required_replay_gate_ids": [], "replay_frontier_gate_ids": [], "resume_status": "normal_sequence"}
    else:
        if (
            not receipt_documents
            and validate_repository_lineage
            and cas_mode != "append_event"
        ):
            _error(errors, "REPLAY_RECEIPT_REQUIRED", "changed lineage requires a current replay receipt")
        try:
            derived = derive_replay_sets(
                changed if isinstance(changed, list) else [], replay_completed
            )
        except ValueError:
            _error(errors, "REPLAY_SET_INVALID", "replay sets could not be derived")
            derived = {"invalidated_gate_ids": [], "preserved_gate_ids": [], "required_replay_gate_ids": [], "replay_frontier_gate_ids": [], "resume_status": "blocked"}
        preserved_values = derived.get("preserved_gate_ids")
        if (
            isinstance(preserved_values, list)
            and any(gate not in completed for gate in preserved_values)
        ):
            _error(errors, "PRESERVED_GATE_EVIDENCE_REQUIRED", "preserved gate evidence is missing or stale")
        if latest_receipt is not None:
            required_replay = derived["required_replay_gate_ids"]
            if (
                not isinstance(required_replay, list)
                or replay_completed != required_replay[: len(replay_completed)]
            ):
                _error(errors, "RECEIPT_COMPLETED_GATES_INVALID", "receipt completed gates are not the replay suffix prefix")
            for field in (
                "invalidated_gate_ids", "preserved_gate_ids",
                "required_replay_gate_ids", "replay_frontier_gate_ids",
            ):
                if latest_receipt.get(field) != derived[field]:
                    _error(errors, "RECEIPT_EXACT_SET_MISMATCH", "receipt replay sets differ from code-owned recomputation")

    requested_ready = False
    if required_action == "reconcile_push":
        requested_ready = isinstance(terminal, dict) and terminal.get("status") == "delivery_unknown"
    elif not isinstance(required_action, str) or required_action not in ACTION_GATES:
        _error(errors, "REQUIRED_ACTION_INVALID", "required action is unsupported")
    elif event_state.get("current_count", 0) == 0:
        requested_gate = ACTION_GATES[required_action]
        requested_index = GATE_GRAPH.index(requested_gate)
        expected_transition = {
            "implement": "initial_implementation_edit",
            "archive": "openspec_archive",
            "commit": "candidate_commit",
            "merge": "ff_merge",
            "push": "lease_push",
        }[required_action]
        if (
            completed != list(GATE_GRAPH[:requested_index])
            or context.get("requested_transition") != expected_transition
        ):
            _error(errors, "STAGE_SEQUENCE_NOT_READY", "normal stage transition predecessors are not exactly closed")
        else:
            requested_ready = not errors
    else:
        frontier = derived["replay_frontier_gate_ids"]
        requested_gate = ACTION_GATES[required_action]
        if frontier:
            frontier_index = GATE_GRAPH.index(frontier[0])
            requested_index = GATE_GRAPH.index(requested_gate)
            if requested_index < frontier_index:
                _error(errors, "ACTION_BEHIND_REPLAY_FRONTIER", "requested action is earlier than the replay frontier")
            elif requested_index > frontier_index:
                _error(errors, "STAGE_REPLAY_REQUIRED", "requested action is later than the replay frontier")
            else:
                requested_ready = not errors and cas_mode == "preflight"
        else:
            _error(errors, "ACTION_BEHIND_REPLAY_FRONTIER", "replay is complete and earlier mutation needs a new event")

    external_prerequisites.insert(0, {
        "code": "EXTERNAL_HOST_CAPABILITY_REQUIRED",
        "gate_id": "host_stage_state",
        "message": "provider-neutral host state and native producer attestation are required",
    })
    if required_action == "reconcile_push":
        external_prerequisites.append({
            "code": "EXTERNAL_PUSH_RECONCILIATION_ATTESTATION_REQUIRED",
            "gate_id": "push",
            "message": "unknown push reconciliation requires an external host attestation",
            "attestation_schema": "provider_neutral.push_reconciliation_attestation/v1",
            "required_binding": ",".join(PUSH_RECONCILIATION_REQUIRED_BINDINGS),
        })
    external_prerequisites_satisfied = False

    return {
        "schema_version": "repopilot.stage_change_replay_validation/v1",
        "status": "PASS" if not errors else "FAIL",
        "claim_level": "mechanical_consistency_only",
        "activation_status": "blocked_on_external_host_capability",
        "human_authorized": "external",
        "technical_ready": "external",
        "vcs_pushed": "not_proven",
        "stage_id": stage if safe_stage else None,
        "required_action": required_action if isinstance(required_action, str) else None,
        "requested_action_ready": (
            requested_ready
            and cas_mode == "preflight"
            and not errors
            and external_prerequisites_satisfied
        ),
        "external_prerequisites_satisfied": external_prerequisites_satisfied,
        "external_prerequisites": external_prerequisites,
        **derived,
        "errors": errors,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate dormant stage change replay evidence")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--replay-root", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--required-action", required=True)
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--cas-mode", choices=("preflight", "append_event", "append_receipt"), default="preflight")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    errors: list[dict[str, str]] = []
    try:
        context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        context = {}
        _error(errors, "CONTEXT_UNREADABLE", "controller context is not valid UTF-8 JSON")
    report = validate_stage_change_replay(project_root=args.project_root, replay_root=args.replay_root, context=context, required_action=args.required_action, activate=args.activate, cas_mode=args.cas_mode)
    if errors:
        report["errors"] = errors + report["errors"]
        report["status"] = "FAIL"
        report["requested_action_ready"] = False
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
