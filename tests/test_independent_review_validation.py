import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.validate_independent_review import (
    ACTIVATION_REF,
    main,
    validate_review_set,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _packet_sha256(artifacts: list[dict[str, str]]) -> str:
    canonical = json.dumps(
        sorted(artifacts, key=lambda item: item["path"]),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(canonical)


def _receipt_sha256(receipt: dict[str, object]) -> str:
    canonical = json.dumps(
        receipt,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(canonical)


def _valid_review_set(
    project_root: Path,
    *,
    required_slots: int = 1,
    review_round: str = "first_round",
) -> dict[str, object]:
    artifact_path = project_root / "review-packet.md"
    artifact_path.write_text("frozen review packet\n", encoding="utf-8")
    activation_path = project_root / ACTIVATION_REF
    activation_path.parent.mkdir(parents=True, exist_ok=True)
    activation_path.write_text("pre-change authority activated the final-review gate\n", encoding="utf-8")
    artifacts = [{"path": "review-packet.md", "sha256": _sha256(artifact_path.read_bytes())}]
    packet_sha256 = _packet_sha256(artifacts)
    receipts: list[dict[str, object]] = []
    review_history: list[dict[str, object]] = []

    for index in range(required_slots):
        slot_id = f"slot-{index + 1}"
        reviewer_id = f"reviewer-{index + 1}"
        lineage = None
        if review_round == "remediation_re_review":
            original_receipt: dict[str, object] = {
                "schema_version": "repopilot.independent_review_receipt/v1",
                "stage_id": "stage-a",
                "phase": "implementation",
                "slot_id": slot_id,
                "implementer_instance_id": "implementer-1",
                "reviewer": {
                    "provider": "codex",
                    "model": "gpt-test",
                    "instance_id": reviewer_id,
                },
                "context_evidence": {
                    "evidence_source": "host_tool_metadata",
                    "parent_context_inheritance": "none",
                    "other_first_round_conclusions_visible": False,
                },
                "review_round": "first_round",
                "reviewed_packet_sha256": packet_sha256,
                "reviewed_artifacts": copy.deepcopy(artifacts),
                "conclusion": {
                    "status": "findings",
                    "findings": [
                        {
                            "id": f"F-{index + 1}",
                            "severity": "P1",
                            "disposition": "fix",
                            "closure_status": "open",
                        }
                    ],
                    "gate_verdict": "blocked",
                    "residual_uncertainty": "Same-model correlation remains possible.",
                },
                "lineage": None,
            }
            original_hash = _receipt_sha256(original_receipt)
            review_ref = f"manual-review-{index + 1}"
            review_history.append(
                {
                    "review_ref": review_ref,
                    "receipt_sha256": original_hash,
                    "receipt": original_receipt,
                }
            )
            lineage = {
                "original_slot_id": slot_id,
                "original_reviewer_instance_id": reviewer_id,
                "original_review_ref": review_ref,
                "original_receipt_sha256": original_hash,
                "closed_finding_ids": [f"F-{index + 1}"],
            }
        receipts.append(
            {
                "schema_version": "repopilot.independent_review_receipt/v1",
                "stage_id": "stage-a",
                "phase": "implementation",
                "slot_id": slot_id,
                "implementer_instance_id": "implementer-1",
                "reviewer": {
                    "provider": "codex",
                    "model": "gpt-test",
                    "instance_id": reviewer_id,
                },
                "context_evidence": {
                    "evidence_source": "host_tool_metadata",
                    "parent_context_inheritance": "none",
                    "other_first_round_conclusions_visible": False,
                },
                "review_round": review_round,
                "reviewed_packet_sha256": packet_sha256,
                "reviewed_artifacts": copy.deepcopy(artifacts),
                "conclusion": {
                    "status": "no_findings",
                    "findings": [],
                    "gate_verdict": "ready",
                    "residual_uncertainty": "Same-model correlation remains possible.",
                },
                "lineage": lineage,
            }
        )

    return {
        "schema_version": "repopilot.independent_review_set/v1",
        "stage_id": "stage-a",
        "phase": "implementation",
        "activation": {
            "status": "active",
            "activated_after_change": "generalize-independent-review-provider",
            "authority": "pre_change_process_contract",
            "activation_ref": ACTIVATION_REF,
            "activation_ref_sha256": _sha256(activation_path.read_bytes()),
            "retroactive_plan_validation": False,
        },
        "implementer": {"instance_id": "implementer-1"},
        "baseline": {
            "kind": "packet_manifest",
            "immutable_ref": f"sha256:{packet_sha256}",
            "artifacts": artifacts,
            "packet_sha256": packet_sha256,
        },
        "review_history": review_history,
        "receipts": receipts,
    }


def _error_codes(report: dict[str, object]) -> set[str]:
    return {error["code"] for error in report["errors"]}  # type: ignore[index]


@pytest.mark.parametrize("review_round", ["first_round", "remediation_re_review"])
def test_valid_first_round_and_remediation_review_sets_pass(
    tmp_path: Path,
    review_round: str,
) -> None:
    review_set = _valid_review_set(tmp_path, review_round=review_round)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "PASS"
    assert report["errors"] == []
    assert report["claim_level"] == "mechanical_consistency_only"
    assert report["gate_ready"] is False
    assert {check["code"] for check in report["required_external_checks"]} == {
        "HOST_DISPATCH_PROVENANCE",
        "ACTIVATION_SEQUENCE",
    }


def test_zero_slot_packet_passes_with_empty_receipts_and_history(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path, required_slots=0)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=0,
    )

    assert report["status"] == "PASS"
    assert report["validated_slots"] == 0
    external = {
        check["code"]: check["status"]
        for check in report["required_external_checks"]
    }
    assert external == {
        "HOST_DISPATCH_PROVENANCE": "NOT_APPLICABLE",
        "ACTIVATION_SEQUENCE": "REQUIRED",
    }


def test_zero_slot_packet_rejects_nonempty_review_history(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path, required_slots=0)
    review_set["review_history"] = [{"unexpected": "history"}]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=0,
    )

    assert report["status"] == "FAIL"
    assert "ZERO_SLOT_REVIEW_HISTORY_FORBIDDEN" in _error_codes(report)


def test_zero_slot_packet_rejects_manufactured_receipt(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path, required_slots=1)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=0,
    )

    assert report["status"] == "FAIL"
    assert "REQUIRED_SLOT_COUNT_MISMATCH" in _error_codes(report)


@pytest.mark.parametrize("required_slots", [-1, True, 1.0, "0"])
def test_slot_count_must_be_a_non_negative_true_integer(
    tmp_path: Path,
    required_slots: object,
) -> None:
    review_set = _valid_review_set(tmp_path, required_slots=0)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=required_slots,  # type: ignore[arg-type]
    )

    assert report["status"] == "FAIL"
    assert "REQUIRED_SLOTS_INVALID" in _error_codes(report)


@pytest.mark.parametrize("required_slots", [False, 0.0])
def test_invalid_zero_like_count_keeps_dispatch_provenance_required(
    tmp_path: Path,
    required_slots: object,
) -> None:
    review_set = _valid_review_set(tmp_path, required_slots=0)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=required_slots,  # type: ignore[arg-type]
    )

    assert report["status"] == "FAIL"
    assert report["required_external_checks"][0] == {  # type: ignore[index]
        "code": "HOST_DISPATCH_PROVENANCE",
        "status": "REQUIRED",
    }


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda data: data["receipts"][0]["reviewer"].update(instance_id="implementer-1"),
            "IMPLEMENTER_REVIEWER_COLLISION",
        ),
        (
            lambda data: data["receipts"][1]["reviewer"].update(instance_id="reviewer-1"),
            "DUPLICATE_REVIEWER",
        ),
        (
            lambda data: data["receipts"][0]["context_evidence"].update(
                parent_context_inheritance="all"
            ),
            "CONTEXT_NOT_ISOLATED",
        ),
        (
            lambda data: data["receipts"][0]["context_evidence"].update(
                parent_context_inheritance="unknown"
            ),
            "CONTEXT_NOT_ISOLATED",
        ),
        (
            lambda data: data["receipts"][0]["context_evidence"].update(
                other_first_round_conclusions_visible=True
            ),
            "CROSS_REVIEW_VISIBILITY",
        ),
        (
            lambda data: data["baseline"].update(kind="working_tree"),
            "MUTABLE_BASELINE",
        ),
        (
            lambda data: data["baseline"]["artifacts"][0].update(sha256="0" * 64),
            "ARTIFACT_HASH_MISMATCH",
        ),
        (
            lambda data: data["receipts"][1].update(reviewed_packet_sha256="0" * 64),
            "REVIEW_PACKET_MISMATCH",
        ),
    ],
)
def test_invalid_independence_or_baseline_evidence_fails_closed(
    tmp_path: Path,
    mutation,
    expected_code: str,
) -> None:
    review_set = _valid_review_set(tmp_path, required_slots=2)
    mutation(review_set)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=2,
    )

    assert report["status"] == "FAIL"
    assert expected_code in _error_codes(report)


def test_activation_ref_must_be_the_canonical_validator_activation_record(
    tmp_path: Path,
) -> None:
    review_set = _valid_review_set(tmp_path)
    arbitrary = tmp_path / "docs" / "outside.md"
    arbitrary.parent.mkdir(parents=True)
    arbitrary.write_text("not the activation record\n", encoding="utf-8")
    review_set["activation"]["activation_ref"] = "docs/outside.md"  # type: ignore[index]
    review_set["activation"]["activation_ref_sha256"] = _sha256(  # type: ignore[index]
        arbitrary.read_bytes()
    )

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "ACTIVATION_REF_INVALID" in _error_codes(report)


def test_stale_remediation_receipt_fails_final_baseline_check(tmp_path: Path) -> None:
    review_set = _valid_review_set(
        tmp_path,
        required_slots=2,
        review_round="remediation_re_review",
    )
    review_set["receipts"][0]["reviewed_artifacts"][0]["sha256"] = "1" * 64  # type: ignore[index]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=2,
    )

    assert report["status"] == "FAIL"
    assert "STALE_REMEDIATION_RECEIPT" in _error_codes(report)


@pytest.mark.parametrize(
    ("activation_update", "expected_code"),
    [
        ({"status": "pending"}, "REVIEW_VALIDATOR_NOT_ACTIVE"),
        ({"retroactive_plan_validation": True}, "RETROACTIVE_PLAN_VALIDATION_FORBIDDEN"),
        ({"authority": "self_declared"}, "ACTIVATION_AUTHORITY_INVALID"),
        ({"activation_ref_sha256": "0" * 64}, "ACTIVATION_REF_HASH_MISMATCH"),
    ],
)
def test_new_gate_cannot_self_bootstrap_or_claim_retroactive_plan_pass(
    tmp_path: Path,
    activation_update: dict[str, object],
    expected_code: str,
) -> None:
    review_set = _valid_review_set(tmp_path)
    review_set["activation"].update(activation_update)  # type: ignore[union-attr]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert expected_code in _error_codes(report)


@pytest.mark.parametrize(
    ("lineage_mutation", "expected_code"),
    [
        (
            lambda data: data["receipts"][0]["lineage"].update(
                original_review_ref="missing-review"
            ),
            "REMEDIATION_ORIGINAL_REVIEW_MISSING",
        ),
        (
            lambda data: data["receipts"][0]["lineage"].update(
                closed_finding_ids=["unknown-finding"]
            ),
            "REMEDIATION_FINDING_MISMATCH",
        ),
    ],
)
def test_remediation_lineage_must_resolve_original_receipt_and_findings(
    tmp_path: Path,
    lineage_mutation,
    expected_code: str,
) -> None:
    review_set = _valid_review_set(tmp_path, review_round="remediation_re_review")
    lineage_mutation(review_set)

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert expected_code in _error_codes(report)


def test_remediation_lineage_rejects_original_reviewer_mismatch(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path, review_round="remediation_re_review")
    history_entry = review_set["review_history"][0]  # type: ignore[index]
    history_entry["receipt"]["reviewer"]["instance_id"] = "another-reviewer"  # type: ignore[index]
    revised_hash = _receipt_sha256(history_entry["receipt"])  # type: ignore[arg-type,index]
    history_entry["receipt_sha256"] = revised_hash  # type: ignore[index]
    review_set["receipts"][0]["lineage"]["original_receipt_sha256"] = revised_hash  # type: ignore[index]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "REMEDIATION_REVIEWER_MISMATCH" in _error_codes(report)


@pytest.mark.parametrize("missing_field", ["schema_version", "reviewed_artifacts"])
def test_hashed_but_incomplete_original_receipt_is_rejected(
    tmp_path: Path,
    missing_field: str,
) -> None:
    review_set = _valid_review_set(tmp_path, review_round="remediation_re_review")
    history_entry = review_set["review_history"][0]  # type: ignore[index]
    history_entry["receipt"].pop(missing_field)  # type: ignore[index]
    revised_hash = _receipt_sha256(history_entry["receipt"])  # type: ignore[arg-type,index]
    history_entry["receipt_sha256"] = revised_hash  # type: ignore[index]
    review_set["receipts"][0]["lineage"]["original_receipt_sha256"] = revised_hash  # type: ignore[index]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "REVIEW_HISTORY_RECEIPT_INCOMPLETE" in _error_codes(report)


def test_remediation_must_close_every_original_finding(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path, review_round="remediation_re_review")
    history_entry = review_set["review_history"][0]  # type: ignore[index]
    history_entry["receipt"]["conclusion"]["findings"].append(  # type: ignore[index]
        {
            "id": "F-omitted",
            "severity": "P2",
            "disposition": "fix",
            "closure_status": "open",
        }
    )
    revised_hash = _receipt_sha256(history_entry["receipt"])  # type: ignore[arg-type,index]
    history_entry["receipt_sha256"] = revised_hash  # type: ignore[index]
    review_set["receipts"][0]["lineage"]["original_receipt_sha256"] = revised_hash  # type: ignore[index]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "REMEDIATION_FINDING_MISMATCH" in _error_codes(report)


def test_clean_original_slot_can_refresh_final_remediation_baseline(
    tmp_path: Path,
) -> None:
    review_set = _valid_review_set(
        tmp_path,
        required_slots=2,
        review_round="remediation_re_review",
    )
    clean_history = review_set["review_history"][1]  # type: ignore[index]
    clean_history["receipt"]["conclusion"] = {  # type: ignore[index]
        "status": "no_findings",
        "findings": [],
        "gate_verdict": "ready",
        "residual_uncertainty": "Same-model correlation remains possible.",
    }
    revised_hash = _receipt_sha256(clean_history["receipt"])  # type: ignore[arg-type,index]
    clean_history["receipt_sha256"] = revised_hash  # type: ignore[index]
    clean_lineage = review_set["receipts"][1]["lineage"]  # type: ignore[index]
    clean_lineage["original_receipt_sha256"] = revised_hash
    clean_lineage["closed_finding_ids"] = []

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=2,
    )

    assert report["status"] == "PASS"
    assert report["errors"] == []


def test_no_findings_with_nonempty_findings_is_contradictory(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path)
    review_set["receipts"][0]["conclusion"]["findings"] = [  # type: ignore[index]
        {
            "id": "P1-still-listed",
            "severity": "P1",
            "disposition": "fix",
            "closure_status": "open",
        }
    ]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "CONCLUSION_CONTRADICTORY" in _error_codes(report)


def test_unresolved_findings_cannot_produce_gate_ready_receipt(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path)
    review_set["receipts"][0]["conclusion"] = {  # type: ignore[index]
        "status": "findings",
        "findings": [
            {
                "id": "P1-open",
                "severity": "P1",
                "disposition": "fix",
                "closure_status": "open",
            }
        ],
        "gate_verdict": "blocked",
        "residual_uncertainty": "An unresolved blocker remains.",
    }

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "UNRESOLVED_FINDINGS" in _error_codes(report)


def test_absolute_artifact_path_is_rejected_even_when_inside_project(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path)
    absolute_path = str(tmp_path / "review-packet.md")
    review_set["baseline"]["artifacts"][0]["path"] = absolute_path  # type: ignore[index]
    review_set["receipts"][0]["reviewed_artifacts"][0]["path"] = absolute_path  # type: ignore[index]

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "ARTIFACT_PATH_NOT_RELATIVE" in _error_codes(report)


def test_artifact_alias_path_is_rejected_before_duplicate_resolution(tmp_path: Path) -> None:
    review_set = _valid_review_set(tmp_path)
    alias = "nested/../review-packet.md"
    review_set["baseline"]["artifacts"].append(  # type: ignore[index]
        {
            "path": alias,
            "sha256": review_set["baseline"]["artifacts"][0]["sha256"],  # type: ignore[index]
        }
    )
    review_set["receipts"][0]["reviewed_artifacts"].append(  # type: ignore[index]
        copy.deepcopy(review_set["baseline"]["artifacts"][1])  # type: ignore[index]
    )

    report = validate_review_set(
        review_set,
        project_root=tmp_path,
        expected_stage="stage-a",
        expected_phase="implementation",
        required_slots=1,
    )

    assert report["status"] == "FAIL"
    assert "ARTIFACT_PATH_NOT_CANONICAL" in _error_codes(report)


def test_missing_actual_receipt_set_returns_nonzero_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "--project-root",
            str(tmp_path),
            "--receipt-set",
            ".harness/reviews/missing/implementation/review-set.json",
            "--expected-stage",
            "missing",
            "--expected-phase",
            "implementation",
            "--required-slots",
            "1",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "FAIL"
    assert {error["code"] for error in output["errors"]} == {"RECEIPT_SET_MISSING"}


def test_receipt_set_outside_fixed_stage_phase_path_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wrong_path = tmp_path / "review-set.json"
    wrong_path.write_text(json.dumps(_valid_review_set(tmp_path)), encoding="utf-8")

    exit_code = main(
        [
            "--project-root",
            str(tmp_path),
            "--receipt-set",
            str(wrong_path),
            "--expected-stage",
            "stage-a",
            "--expected-phase",
            "implementation",
            "--required-slots",
            "1",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "RECEIPT_SET_PATH_MISMATCH" in {
        error["code"] for error in output["errors"]
    }


def test_unsafe_stage_id_returns_nonzero_before_path_resolution(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "--project-root",
            str(tmp_path),
            "--receipt-set",
            ".harness/reviews/escape/implementation/review-set.json",
            "--expected-stage",
            "../escape",
            "--expected-phase",
            "implementation",
            "--required-slots",
            "1",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert {error["code"] for error in output["errors"]} == {"STAGE_ID_INVALID"}


def test_symlinked_receipt_path_is_rejected(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_set = _valid_review_set(tmp_path)
    target = tmp_path / "outside-review-set.json"
    target.write_text(json.dumps(review_set), encoding="utf-8")
    receipt_path = (
        tmp_path / ".harness" / "reviews" / "stage-a" / "implementation" / "review-set.json"
    )
    receipt_path.parent.mkdir(parents=True)
    receipt_path.symlink_to(target)

    exit_code = main(
        [
            "--project-root",
            str(tmp_path),
            "--receipt-set",
            ".harness/reviews/stage-a/implementation/review-set.json",
            "--expected-stage",
            "stage-a",
            "--expected-phase",
            "implementation",
            "--required-slots",
            "1",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "RECEIPT_SET_SYMLINK_FORBIDDEN" in {
        error["code"] for error in output["errors"]
    }
