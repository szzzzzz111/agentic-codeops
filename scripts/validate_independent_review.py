"""Deterministically validate independent-review receipt sets.

This validates mechanically observable evidence only. It cannot prove that a
reviewer reasoned independently; the receipt therefore preserves residual
uncertainty for semantic review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

VALIDATION_SCHEMA = "repopilot.independent_review_validation/v1"
ACTIVATION_REF = (
    "openspec/changes/archive/2026-08-20-"
    "generalize-independent-review-provider/activation-record.md"
)
REVIEW_SET_SCHEMA = "repopilot.independent_review_set/v1"
RECEIPT_SCHEMA = "repopilot.independent_review_receipt/v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
STAGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_artifacts(artifacts: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(artifacts, key=lambda item: item["path"])


def _packet_sha256(artifacts: list[dict[str, str]]) -> str:
    canonical = json.dumps(
        _canonical_artifacts(artifacts),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(canonical)


def _object_sha256(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(canonical)


def _add_error(
    errors: list[dict[str, str]],
    code: str,
    message: str,
    location: str = "$",
) -> None:
    errors.append({"code": code, "location": location, "message": message})


def _read_artifacts(
    baseline: dict[str, Any],
    project_root: Path,
    errors: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    declared: list[dict[str, str]] = []
    actual: list[dict[str, str]] = []
    raw_artifacts = baseline.get("artifacts")
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        _add_error(errors, "ARTIFACT_MANIFEST_MISSING", "baseline.artifacts must be a non-empty list", "$.baseline.artifacts")
        return declared, actual

    root = project_root.resolve()
    seen_paths: set[str] = set()
    seen_targets: set[Path] = set()
    for index, item in enumerate(raw_artifacts):
        location = f"$.baseline.artifacts[{index}]"
        if not isinstance(item, dict):
            _add_error(errors, "ARTIFACT_ENTRY_INVALID", "artifact entry must be an object", location)
            continue
        relative_path = item.get("path")
        declared_hash = item.get("sha256")
        if not isinstance(relative_path, str) or not relative_path:
            _add_error(errors, "ARTIFACT_PATH_INVALID", "artifact path must be a non-empty project-relative string", f"{location}.path")
            continue
        path_value = Path(relative_path)
        if path_value.is_absolute():
            _add_error(errors, "ARTIFACT_PATH_NOT_RELATIVE", "artifact path must be project-relative", f"{location}.path")
            continue
        if (
            "\\" in relative_path
            or any(part in {"", ".", ".."} for part in path_value.parts)
            or path_value.as_posix() != relative_path
        ):
            _add_error(errors, "ARTIFACT_PATH_NOT_CANONICAL", "artifact path must be canonical POSIX-relative syntax without aliases", f"{location}.path")
            continue
        if relative_path in seen_paths:
            _add_error(errors, "DUPLICATE_ARTIFACT", f"duplicate artifact path: {relative_path}", f"{location}.path")
            continue
        seen_paths.add(relative_path)
        if not isinstance(declared_hash, str) or SHA256_PATTERN.fullmatch(declared_hash) is None:
            _add_error(errors, "ARTIFACT_HASH_INVALID", "artifact sha256 must be 64 lowercase hex characters", f"{location}.sha256")
            continue

        unresolved_path = root / relative_path
        cursor = root
        symlink_found = False
        for part in path_value.parts:
            cursor /= part
            if cursor.is_symlink():
                symlink_found = True
                break
        if symlink_found:
            _add_error(errors, "ARTIFACT_SYMLINK_FORBIDDEN", f"reviewed artifact path traverses a symlink: {relative_path}", f"{location}.path")
            continue
        artifact_path = unresolved_path.resolve()
        try:
            artifact_path.relative_to(root)
        except ValueError:
            _add_error(errors, "ARTIFACT_PATH_OUTSIDE_ROOT", f"artifact escapes project root: {relative_path}", f"{location}.path")
            continue
        if artifact_path in seen_targets:
            _add_error(errors, "DUPLICATE_RESOLVED_ARTIFACT", f"multiple artifact paths resolve to the same file: {relative_path}", f"{location}.path")
            continue
        seen_targets.add(artifact_path)

        declared.append({"path": relative_path, "sha256": declared_hash})
        if not artifact_path.is_file():
            _add_error(errors, "ARTIFACT_MISSING", f"reviewed artifact does not exist: {relative_path}", location)
            continue
        actual_hash = _sha256(artifact_path.read_bytes())
        actual.append({"path": relative_path, "sha256": actual_hash})
        if actual_hash != declared_hash:
            _add_error(errors, "ARTIFACT_HASH_MISMATCH", f"artifact hash does not match project file: {relative_path}", f"{location}.sha256")

    return _canonical_artifacts(declared), _canonical_artifacts(actual)


def _validate_conclusion(
    conclusion: object,
    errors: list[dict[str, str]],
    location: str,
    *,
    allow_unresolved: bool,
) -> set[str]:
    finding_ids: set[str] = set()
    if not isinstance(conclusion, dict):
        _add_error(errors, "CONCLUSION_INCOMPLETE", "conclusion must be an object", location)
        return finding_ids

    status = conclusion.get("status")
    findings = conclusion.get("findings")
    gate_verdict = conclusion.get("gate_verdict")
    residual = conclusion.get("residual_uncertainty")
    if status not in {"findings", "no_findings"} or not isinstance(findings, list):
        _add_error(errors, "CONCLUSION_INCOMPLETE", "conclusion requires status and a findings list", location)
        return finding_ids
    if not isinstance(residual, str) or not residual.strip():
        _add_error(errors, "RESIDUAL_UNCERTAINTY_MISSING", "residual_uncertainty must be recorded", f"{location}.residual_uncertainty")

    if status == "no_findings":
        if findings:
            _add_error(errors, "CONCLUSION_CONTRADICTORY", "no_findings requires an empty findings list", f"{location}.findings")
        if gate_verdict != "ready":
            _add_error(errors, "CONCLUSION_CONTRADICTORY", "no_findings requires gate_verdict=ready", f"{location}.gate_verdict")
        return finding_ids

    if not findings:
        _add_error(errors, "CONCLUSION_INCOMPLETE", "findings status requires at least one finding", f"{location}.findings")
        return finding_ids

    has_open = False
    for index, finding in enumerate(findings):
        finding_location = f"{location}.findings[{index}]"
        if not isinstance(finding, dict):
            _add_error(errors, "FINDING_INVALID", "finding must be an object", finding_location)
            continue
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not finding_id or finding_id in finding_ids:
            _add_error(errors, "FINDING_ID_INVALID", "finding id must be non-empty and unique", f"{finding_location}.id")
        else:
            finding_ids.add(finding_id)
        if finding.get("severity") not in {"P0", "P1", "P2", "P3"}:
            _add_error(errors, "FINDING_SEVERITY_INVALID", "severity must be P0, P1, P2, or P3", f"{finding_location}.severity")
        if finding.get("disposition") not in {"fix", "clarify", "reject", "defer"}:
            _add_error(errors, "FINDING_DISPOSITION_INVALID", "disposition must be fix, clarify, reject, or defer", f"{finding_location}.disposition")
        closure_status = finding.get("closure_status")
        if closure_status not in {"open", "closed"}:
            _add_error(errors, "FINDING_CLOSURE_INVALID", "closure_status must be open or closed", f"{finding_location}.closure_status")
        elif closure_status == "open":
            has_open = True

    if has_open:
        if not allow_unresolved:
            _add_error(errors, "UNRESOLVED_FINDINGS", "a final receipt cannot contain open findings", f"{location}.findings")
        if gate_verdict != "blocked":
            _add_error(errors, "CONCLUSION_CONTRADICTORY", "open findings require gate_verdict=blocked", f"{location}.gate_verdict")
    elif gate_verdict != "ready":
        _add_error(errors, "CONCLUSION_CONTRADICTORY", "all-closed findings require gate_verdict=ready", f"{location}.gate_verdict")
    return finding_ids


def _validate_embedded_artifacts(
    raw_artifacts: object,
    errors: list[dict[str, str]],
    location: str,
) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history receipt requires reviewed_artifacts", location)
        return artifacts
    seen_paths: set[str] = set()
    for index, item in enumerate(raw_artifacts):
        item_location = f"{location}[{index}]"
        if not isinstance(item, dict):
            _add_error(errors, "REVIEW_HISTORY_ARTIFACT_INVALID", "history artifact must be an object", item_location)
            continue
        relative_path = item.get("path")
        sha256 = item.get("sha256")
        if not isinstance(relative_path, str) or not relative_path:
            _add_error(errors, "REVIEW_HISTORY_ARTIFACT_INVALID", "history artifact path is required", f"{item_location}.path")
            continue
        path_value = Path(relative_path)
        if (
            path_value.is_absolute()
            or "\\" in relative_path
            or any(part in {"", ".", ".."} for part in path_value.parts)
            or path_value.as_posix() != relative_path
            or relative_path in seen_paths
        ):
            _add_error(errors, "REVIEW_HISTORY_ARTIFACT_INVALID", "history artifact path must be unique canonical project-relative syntax", f"{item_location}.path")
            continue
        seen_paths.add(relative_path)
        if not isinstance(sha256, str) or SHA256_PATTERN.fullmatch(sha256) is None:
            _add_error(errors, "REVIEW_HISTORY_ARTIFACT_INVALID", "history artifact sha256 must be 64 lowercase hex characters", f"{item_location}.sha256")
            continue
        artifacts.append({"path": relative_path, "sha256": sha256})
    return _canonical_artifacts(artifacts)


def _validate_history_receipt(
    receipt: dict[str, Any],
    errors: list[dict[str, str]],
    location: str,
    *,
    expected_stage: str,
    expected_phase: str,
    implementer_id: object,
) -> set[str]:
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", f"history receipt schema_version must be {RECEIPT_SCHEMA}", f"{location}.schema_version")
    if receipt.get("stage_id") != expected_stage or receipt.get("phase") != expected_phase:
        _add_error(errors, "REVIEW_HISTORY_SCOPE_MISMATCH", "history receipt stage/phase does not match review set", location)
    if not isinstance(receipt.get("slot_id"), str) or not receipt.get("slot_id"):
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history receipt slot_id is required", f"{location}.slot_id")
    if receipt.get("implementer_instance_id") != implementer_id:
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history receipt implementer must match review set", f"{location}.implementer_instance_id")

    reviewer = receipt.get("reviewer")
    if not isinstance(reviewer, dict) or any(
        not isinstance(reviewer.get(field), str) or not reviewer.get(field)
        for field in ("provider", "model", "instance_id")
    ):
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history receipt requires complete reviewer metadata", f"{location}.reviewer")
    elif reviewer.get("instance_id") == implementer_id:
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history reviewer must differ from implementer", f"{location}.reviewer.instance_id")

    context = receipt.get("context_evidence")
    if not isinstance(context, dict):
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history receipt requires context_evidence", f"{location}.context_evidence")
    elif (
        context.get("evidence_source") != "host_tool_metadata"
        or context.get("parent_context_inheritance") != "none"
        or context.get("other_first_round_conclusions_visible") is not False
    ):
        _add_error(errors, "REVIEW_HISTORY_CONTEXT_INVALID", "history receipt must preserve declared first-round context isolation", f"{location}.context_evidence")

    if receipt.get("review_round") != "first_round" or receipt.get("lineage") is not None:
        _add_error(errors, "REVIEW_HISTORY_NOT_FIRST_ROUND", "remediation history must preserve an original first-round receipt", location)

    artifacts = _validate_embedded_artifacts(
        receipt.get("reviewed_artifacts"),
        errors,
        f"{location}.reviewed_artifacts",
    )
    packet_hash = receipt.get("reviewed_packet_sha256")
    if not isinstance(packet_hash, str) or SHA256_PATTERN.fullmatch(packet_hash) is None:
        _add_error(errors, "REVIEW_HISTORY_RECEIPT_INCOMPLETE", "history receipt requires reviewed_packet_sha256", f"{location}.reviewed_packet_sha256")
    elif artifacts and packet_hash != _packet_sha256(artifacts):
        _add_error(errors, "REVIEW_HISTORY_PACKET_MISMATCH", "history packet hash does not match its artifact manifest", f"{location}.reviewed_packet_sha256")

    return _validate_conclusion(
        receipt.get("conclusion"),
        errors,
        f"{location}.conclusion",
        allow_unresolved=True,
    )


def _validation_report(
    *,
    errors: list[dict[str, str]],
    stage_id: str | None = None,
    phase: str | None = None,
    required_slots: int | None = None,
    validated_slots: int = 0,
    packet_sha256: str | None = None,
) -> dict[str, object]:
    dispatch_status = (
        "NOT_APPLICABLE"
        if type(required_slots) is int and required_slots == 0
        else "REQUIRED"
    )
    return {
        "schema_version": VALIDATION_SCHEMA,
        "status": "PASS" if not errors else "FAIL",
        "claim_level": "mechanical_consistency_only",
        "gate_ready": False,
        "required_external_checks": [
            {"code": "HOST_DISPATCH_PROVENANCE", "status": dispatch_status},
            {"code": "ACTIVATION_SEQUENCE", "status": "REQUIRED"},
        ],
        "stage_id": stage_id,
        "phase": phase,
        "required_slots": required_slots,
        "validated_slots": validated_slots if not errors else 0,
        "packet_sha256": packet_sha256,
        "errors": errors,
    }


def validate_review_set(
    review_set: object,
    *,
    project_root: Path,
    expected_stage: str,
    expected_phase: str,
    required_slots: int,
) -> dict[str, object]:
    """Return a structured PASS/FAIL report for one frozen review set."""

    errors: list[dict[str, str]] = []
    if not isinstance(review_set, dict):
        _add_error(errors, "RECEIPT_SET_INVALID", "review set must be a JSON object")
        return _validation_report(errors=errors)

    if review_set.get("schema_version") != REVIEW_SET_SCHEMA:
        _add_error(errors, "RECEIPT_SET_SCHEMA_INVALID", f"schema_version must be {REVIEW_SET_SCHEMA}", "$.schema_version")
    if review_set.get("stage_id") != expected_stage:
        _add_error(errors, "STAGE_MISMATCH", "stage_id does not match --expected-stage", "$.stage_id")
    if expected_phase not in {"plan", "implementation"} or review_set.get("phase") != expected_phase:
        _add_error(errors, "PHASE_MISMATCH", "phase must match --expected-phase (plan or implementation)", "$.phase")
    slot_count_valid = (
        type(required_slots) is int and required_slots >= 0
    )
    if not slot_count_valid:
        _add_error(
            errors,
            "REQUIRED_SLOTS_INVALID",
            "--required-slots must be a non-negative integer",
        )

    activation = review_set.get("activation")
    if not isinstance(activation, dict) or activation.get("status") != "active":
        _add_error(errors, "REVIEW_VALIDATOR_NOT_ACTIVE", "the receipt set must declare the review gate active", "$.activation.status")
    else:
        if activation.get("activated_after_change") != "generalize-independent-review-provider":
            _add_error(errors, "ACTIVATION_PROVENANCE_MISSING", "activated_after_change must identify the enabling change", "$.activation.activated_after_change")
        if activation.get("authority") != "pre_change_process_contract":
            _add_error(errors, "ACTIVATION_AUTHORITY_INVALID", "activation timing remains owned by the pre-change process authority", "$.activation.authority")
        activation_ref = activation.get("activation_ref")
        activation_hash = activation.get("activation_ref_sha256")
        if activation_ref != ACTIVATION_REF:
            _add_error(errors, "ACTIVATION_REF_INVALID", "activation_ref must identify the canonical validator activation record", "$.activation.activation_ref")
        else:
            activation_path = (project_root.resolve() / activation_ref).resolve()
            cursor = project_root.resolve()
            traverses_symlink = False
            for part in Path(activation_ref).parts:
                cursor /= part
                if cursor.is_symlink():
                    traverses_symlink = True
                    break
            try:
                activation_path.relative_to(project_root.resolve())
            except ValueError:
                _add_error(errors, "ACTIVATION_REF_INVALID", "activation_ref escapes project root", "$.activation.activation_ref")
            else:
                if traverses_symlink:
                    _add_error(errors, "ACTIVATION_REF_INVALID", "activation_ref must not traverse a symlink", "$.activation.activation_ref")
                elif not activation_path.is_file():
                    _add_error(errors, "ACTIVATION_REF_MISSING", "activation authority record does not exist", "$.activation.activation_ref")
                elif not isinstance(activation_hash, str) or activation_hash != _sha256(activation_path.read_bytes()):
                    _add_error(errors, "ACTIVATION_REF_HASH_MISMATCH", "activation authority record hash does not match", "$.activation.activation_ref_sha256")
    if isinstance(activation, dict) and activation.get("retroactive_plan_validation") is not False:
        _add_error(errors, "RETROACTIVE_PLAN_VALIDATION_FORBIDDEN", "a newly introduced gate cannot claim retroactive plan validation", "$.activation.retroactive_plan_validation")

    implementer = review_set.get("implementer")
    implementer_id = implementer.get("instance_id") if isinstance(implementer, dict) else None
    if not isinstance(implementer_id, str) or not implementer_id:
        _add_error(errors, "IMPLEMENTER_ID_MISSING", "implementer.instance_id must be recorded", "$.implementer.instance_id")

    baseline = review_set.get("baseline")
    if not isinstance(baseline, dict):
        _add_error(errors, "BASELINE_MISSING", "baseline must be an object", "$.baseline")
        baseline = {}
    if baseline.get("kind") != "packet_manifest":
        _add_error(errors, "MUTABLE_BASELINE", "baseline.kind must be packet_manifest", "$.baseline.kind")

    declared_artifacts, actual_artifacts = _read_artifacts(baseline, project_root, errors)
    computed_packet_hash = _packet_sha256(actual_artifacts) if actual_artifacts else None
    declared_packet_hash = baseline.get("packet_sha256")
    if not isinstance(declared_packet_hash, str) or SHA256_PATTERN.fullmatch(declared_packet_hash) is None:
        _add_error(errors, "PACKET_HASH_INVALID", "baseline.packet_sha256 must be 64 lowercase hex characters", "$.baseline.packet_sha256")
    elif computed_packet_hash is not None and declared_packet_hash != computed_packet_hash:
        _add_error(errors, "PACKET_HASH_MISMATCH", "baseline packet hash does not match current artifact contents", "$.baseline.packet_sha256")
    if baseline.get("immutable_ref") != f"sha256:{declared_packet_hash}":
        _add_error(errors, "IMMUTABLE_REF_MISMATCH", "immutable_ref must equal sha256:<packet_sha256>", "$.baseline.immutable_ref")

    raw_history = review_set.get("review_history")
    if not isinstance(raw_history, list):
        _add_error(errors, "REVIEW_HISTORY_INVALID", "review_history must be a list", "$.review_history")
        raw_history = []
    if slot_count_valid and required_slots == 0 and raw_history:
        _add_error(
            errors,
            "ZERO_SLOT_REVIEW_HISTORY_FORBIDDEN",
            "zero-slot review sets must have empty review_history",
            "$.review_history",
        )
    history_by_ref: dict[str, dict[str, Any]] = {}
    for index, history_entry in enumerate(raw_history):
        history_location = f"$.review_history[{index}]"
        if not isinstance(history_entry, dict):
            _add_error(errors, "REVIEW_HISTORY_ENTRY_INVALID", "review history entry must be an object", history_location)
            continue
        review_ref = history_entry.get("review_ref")
        original_receipt = history_entry.get("receipt")
        receipt_hash = history_entry.get("receipt_sha256")
        if not isinstance(review_ref, str) or not review_ref or review_ref in history_by_ref:
            _add_error(errors, "REVIEW_HISTORY_REF_INVALID", "review_ref must be non-empty and unique", f"{history_location}.review_ref")
            continue
        if not isinstance(original_receipt, dict):
            _add_error(errors, "REVIEW_HISTORY_RECEIPT_INVALID", "history receipt must be an object", f"{history_location}.receipt")
            continue
        computed_receipt_hash = _object_sha256(original_receipt)
        if receipt_hash != computed_receipt_hash:
            _add_error(errors, "REVIEW_HISTORY_HASH_MISMATCH", "history receipt hash does not match its canonical content", f"{history_location}.receipt_sha256")
        original_findings = _validate_history_receipt(
            original_receipt,
            errors,
            f"{history_location}.receipt",
            expected_stage=expected_stage,
            expected_phase=expected_phase,
            implementer_id=implementer_id,
        )
        history_by_ref[review_ref] = {
            "receipt": original_receipt,
            "receipt_sha256": computed_receipt_hash,
            "finding_ids": original_findings,
        }

    receipts = review_set.get("receipts")
    if not isinstance(receipts, list):
        _add_error(errors, "RECEIPTS_INVALID", "receipts must be a list", "$.receipts")
        receipts = []
    if slot_count_valid and len(receipts) != required_slots:
        _add_error(errors, "REQUIRED_SLOT_COUNT_MISMATCH", f"expected {required_slots} receipts, found {len(receipts)}", "$.receipts")

    seen_slots: set[str] = set()
    seen_reviewers: set[str] = set()
    for index, receipt in enumerate(receipts):
        location = f"$.receipts[{index}]"
        if not isinstance(receipt, dict):
            _add_error(errors, "RECEIPT_INVALID", "receipt must be an object", location)
            continue
        if receipt.get("schema_version") != RECEIPT_SCHEMA:
            _add_error(errors, "RECEIPT_SCHEMA_INVALID", f"receipt schema_version must be {RECEIPT_SCHEMA}", f"{location}.schema_version")
        if receipt.get("stage_id") != expected_stage:
            _add_error(errors, "RECEIPT_STAGE_MISMATCH", "receipt stage_id does not match expected stage", f"{location}.stage_id")
        if receipt.get("phase") != expected_phase:
            _add_error(errors, "RECEIPT_PHASE_MISMATCH", "receipt phase does not match expected phase", f"{location}.phase")

        slot_id = receipt.get("slot_id")
        if not isinstance(slot_id, str) or not slot_id:
            _add_error(errors, "SLOT_ID_MISSING", "slot_id must be recorded", f"{location}.slot_id")
        elif slot_id in seen_slots:
            _add_error(errors, "DUPLICATE_SLOT", f"duplicate slot_id: {slot_id}", f"{location}.slot_id")
        else:
            seen_slots.add(slot_id)

        receipt_implementer_id = receipt.get("implementer_instance_id")
        if receipt_implementer_id != implementer_id:
            _add_error(errors, "IMPLEMENTER_ID_MISMATCH", "receipt implementer identity must match review set", f"{location}.implementer_instance_id")

        reviewer = receipt.get("reviewer")
        reviewer_id = reviewer.get("instance_id") if isinstance(reviewer, dict) else None
        if not isinstance(reviewer_id, str) or not reviewer_id:
            _add_error(errors, "REVIEWER_ID_MISSING", "reviewer.instance_id must be recorded", f"{location}.reviewer.instance_id")
        else:
            if reviewer_id == implementer_id:
                _add_error(errors, "IMPLEMENTER_REVIEWER_COLLISION", "reviewer must be distinct from implementer", f"{location}.reviewer.instance_id")
            if reviewer_id in seen_reviewers:
                _add_error(errors, "DUPLICATE_REVIEWER", f"reviewer instance reused across slots: {reviewer_id}", f"{location}.reviewer.instance_id")
            else:
                seen_reviewers.add(reviewer_id)
        if isinstance(reviewer, dict):
            for field in ("provider", "model"):
                if not isinstance(reviewer.get(field), str) or not reviewer.get(field):
                    _add_error(errors, "REVIEWER_METADATA_MISSING", f"reviewer.{field} must be recorded", f"{location}.reviewer.{field}")

        context = receipt.get("context_evidence")
        if not isinstance(context, dict):
            _add_error(errors, "CONTEXT_EVIDENCE_MISSING", "context_evidence must be an object", f"{location}.context_evidence")
            context = {}
        if context.get("evidence_source") != "host_tool_metadata":
            _add_error(errors, "CONTEXT_EVIDENCE_UNVERIFIED", "context evidence must come from host_tool_metadata", f"{location}.context_evidence.evidence_source")
        if context.get("parent_context_inheritance") != "none":
            _add_error(errors, "CONTEXT_NOT_ISOLATED", "parent context inheritance must be explicitly none", f"{location}.context_evidence.parent_context_inheritance")
        if context.get("other_first_round_conclusions_visible") is not False:
            _add_error(errors, "CROSS_REVIEW_VISIBILITY", "other first-round conclusions must not be visible", f"{location}.context_evidence.other_first_round_conclusions_visible")

        if receipt.get("reviewed_packet_sha256") != declared_packet_hash:
            _add_error(errors, "REVIEW_PACKET_MISMATCH", "receipt does not bind the final packet hash", f"{location}.reviewed_packet_sha256")
        reviewed_artifacts = receipt.get("reviewed_artifacts")
        receipt_artifacts = _canonical_artifacts(reviewed_artifacts) if isinstance(reviewed_artifacts, list) and all(isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str) for item in reviewed_artifacts) else None
        if receipt_artifacts != declared_artifacts:
            code = "STALE_REMEDIATION_RECEIPT" if receipt.get("review_round") == "remediation_re_review" else "REVIEW_ARTIFACT_MISMATCH"
            _add_error(errors, code, "receipt artifact manifest does not match the final baseline", f"{location}.reviewed_artifacts")

        _validate_conclusion(
            receipt.get("conclusion"),
            errors,
            f"{location}.conclusion",
            allow_unresolved=False,
        )

        review_round = receipt.get("review_round")
        lineage = receipt.get("lineage")
        if review_round == "first_round":
            if lineage is not None:
                _add_error(errors, "FIRST_ROUND_LINEAGE_INVALID", "first-round receipt lineage must be null", f"{location}.lineage")
        elif review_round == "remediation_re_review":
            if not isinstance(lineage, dict):
                _add_error(errors, "REMEDIATION_LINEAGE_INVALID", "remediation re-review must preserve original receipt lineage", f"{location}.lineage")
            else:
                original_ref = lineage.get("original_review_ref")
                original = history_by_ref.get(original_ref) if isinstance(original_ref, str) else None
                if original is None:
                    _add_error(errors, "REMEDIATION_ORIGINAL_REVIEW_MISSING", "original_review_ref must resolve review_history", f"{location}.lineage.original_review_ref")
                else:
                    original_receipt = original["receipt"]
                    original_reviewer = original_receipt.get("reviewer")
                    original_reviewer_id = original_reviewer.get("instance_id") if isinstance(original_reviewer, dict) else None
                    if (
                        lineage.get("original_slot_id") != slot_id
                        or original_receipt.get("slot_id") != slot_id
                    ):
                        _add_error(errors, "REMEDIATION_SLOT_MISMATCH", "remediation must remain in the original slot", f"{location}.lineage.original_slot_id")
                    if (
                        lineage.get("original_reviewer_instance_id") != reviewer_id
                        or original_reviewer_id != reviewer_id
                    ):
                        _add_error(errors, "REMEDIATION_REVIEWER_MISMATCH", "remediation must reuse the original reviewer instance", f"{location}.lineage.original_reviewer_instance_id")
                    if original_receipt.get("implementer_instance_id") != implementer_id:
                        _add_error(errors, "REMEDIATION_IMPLEMENTER_MISMATCH", "original receipt implementer must match review set", f"{location}.lineage")
                    if lineage.get("original_receipt_sha256") != original["receipt_sha256"]:
                        _add_error(errors, "REMEDIATION_RECEIPT_HASH_MISMATCH", "lineage must bind the canonical original receipt hash", f"{location}.lineage.original_receipt_sha256")
                    closed_ids = lineage.get("closed_finding_ids")
                    if (
                        not isinstance(closed_ids, list)
                        or not all(isinstance(item, str) for item in closed_ids)
                        or set(closed_ids) != original["finding_ids"]
                    ):
                        _add_error(errors, "REMEDIATION_FINDING_MISMATCH", "closed findings must exist in the original receipt", f"{location}.lineage.closed_finding_ids")
        else:
            _add_error(errors, "REVIEW_ROUND_INVALID", "review_round must be first_round or remediation_re_review", f"{location}.review_round")

    return _validation_report(
        errors=errors,
        stage_id=expected_stage,
        phase=expected_phase,
        required_slots=required_slots,
        validated_slots=len(receipts),
        packet_sha256=computed_packet_hash,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate an independent-review receipt set")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--receipt-set", required=True)
    parser.add_argument("--expected-stage", required=True)
    parser.add_argument("--expected-phase", choices=("plan", "implementation"), required=True)
    parser.add_argument("--required-slots", type=int, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    if STAGE_ID_PATTERN.fullmatch(args.expected_stage) is None:
        errors = [{
            "code": "STAGE_ID_INVALID",
            "location": "--expected-stage",
            "message": "expected stage must use safe identifier characters",
        }]
        report = _validation_report(errors=errors)
    else:
        expected_relative = (
            Path(".harness")
            / "reviews"
            / args.expected_stage
            / args.expected_phase
            / "review-set.json"
        )
        supplied_relative = Path(args.receipt_set)
        receipt_path = project_root / supplied_relative
        if supplied_relative.is_absolute() or supplied_relative != expected_relative:
            errors = [{
                "code": "RECEIPT_SET_PATH_MISMATCH",
                "location": args.receipt_set,
                "message": f"receipt set must use the fixed relative path: {expected_relative}",
            }]
            report = _validation_report(errors=errors)
        else:
            cursor = project_root
            symlink_found = False
            for part in expected_relative.parts:
                cursor /= part
                if cursor.is_symlink():
                    symlink_found = True
                    break
            if symlink_found:
                errors = [{
                    "code": "RECEIPT_SET_SYMLINK_FORBIDDEN",
                    "location": str(receipt_path),
                    "message": "fixed receipt path must not traverse a symlink",
                }]
                report = _validation_report(errors=errors)
            elif not receipt_path.is_file():
                errors = [{
                    "code": "RECEIPT_SET_MISSING",
                    "location": str(receipt_path),
                    "message": "actual review receipt set does not exist",
                }]
                report = _validation_report(errors=errors)
            else:
                try:
                    review_set = json.loads(receipt_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    errors = [{
                        "code": "RECEIPT_SET_UNREADABLE",
                        "location": str(receipt_path),
                        "message": str(exc),
                    }]
                    report = _validation_report(errors=errors)
                else:
                    report = validate_review_set(
                        review_set,
                        project_root=project_root,
                        expected_stage=args.expected_stage,
                        expected_phase=args.expected_phase,
                        required_slots=args.required_slots,
                    )

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
