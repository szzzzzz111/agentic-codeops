from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path, PureWindowsPath
from typing import Any

import pytest

from scripts.validate_independent_review import ACTIVATION_REF

STAGE_ID = "bind-stage-authority-and-invalidation"
CONFIRMED_RECORD_SHA256 = (
    "6f87a32790f302b8924919aa30f42ab5d97d41cf2824129054858f80411f38de"
)
CONFIRMED_PLANNING_BASE = "88ee2d52bb6edddf52a2a1012580fcf0b693c066"
ZERO_SHA256 = "0" * 64
ONE_SHA256 = "1" * 64


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def _git(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _record_path(project_root: Path, epoch: int = 1) -> Path:
    return (
        project_root / ".harness" / "authority" / STAGE_ID / f"epoch-{epoch:04d}.json"
    )


def _write_record(project_root: Path, record: dict[str, Any], epoch: int = 1) -> Path:
    path = _record_path(project_root, epoch)
    _write_json(path, record)
    return path


def _load_validator_module() -> Any:
    try:
        return importlib.import_module("scripts.validate_stage_authority")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "RED: scripts.validate_stage_authority does not exist yet",
            pytrace=False,
        )
        raise AssertionError from exc


def _valid_record(project_root: Path, baseline: str) -> dict[str, Any]:
    allowed_files = project_root / ".harness" / "allowed_files.md"
    scope: dict[str, Any] = {
        "risk": "high",
        "summary": "Exercise the deterministic stage-authority contract.",
        "allowed_path_rules": {
            "exact": [
                ".harness/allowed_files.md",
                ".harness/review_checklist.md",
                "tests/test_stage_authority_validation.py",
            ],
            "prefixes": [
                f".harness/authority/{STAGE_ID}/",
                f".harness/reviews/{STAGE_ID}/",
                "src/",
            ],
        },
        "non_goals": [
            "credential handling",
            "RepoPilot runtime Git automation or public API changes",
        ],
        "active_allowed_files_sha256": _sha256(allowed_files.read_bytes()),
    }
    return {
        "schema_version": "repopilot.stage_authority/v1",
        "stage_id": STAGE_ID,
        "authority_epoch": 1,
        "supersedes_record_sha256": None,
        "authority_source": {
            "kind": "host_direct_user_instruction",
            "host_reference": "host:test-thread;confirmation:1",
        },
        "scope": scope,
        "scope_sha256": _canonical_sha256(scope),
        "planning_baseline": {"commit": baseline},
        "action_ceiling": "push",
        "vcs_target": {
            "remote_name": "origin",
            "effective_fetch_url_sha256": ZERO_SHA256,
            "effective_push_url_sha256": ZERO_SHA256,
            "target_branch": "main",
            "authorized_remote_tip": baseline,
        },
    }


@pytest.fixture
def authority_repo(tmp_path: Path) -> dict[str, Any]:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Stage Authority Tests")
    _git(tmp_path, "config", "user.email", "stage-authority@example.invalid")

    (tmp_path / ".harness").mkdir()
    (tmp_path / ".harness" / "allowed_files.md").write_text(
        "# allowed\n- `src/**`\n",
        encoding="utf-8",
    )
    (tmp_path / ".harness" / "review_checklist.md").write_text(
        "# review\n",
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "outside.md").write_text("baseline\n", encoding="utf-8")
    activation_path = tmp_path / ACTIVATION_REF
    activation_path.parent.mkdir(parents=True, exist_ok=True)
    activation_path.write_text(
        "pre-change authority activated the review validator\n",
        encoding="utf-8",
    )
    _git(
        tmp_path,
        "add",
        ".harness/allowed_files.md",
        ".harness/review_checklist.md",
        "src/app.py",
        "docs/outside.md",
        ACTIVATION_REF,
    )
    _git(tmp_path, "commit", "-m", "planning baseline")
    baseline = _git(tmp_path, "rev-parse", "HEAD")

    record = _valid_record(tmp_path, baseline)
    record_path = _write_record(tmp_path, record)
    return {
        "root": tmp_path,
        "baseline": baseline,
        "record": record,
        "record_path": record_path,
    }


def _expected(repo: dict[str, Any]) -> dict[str, Any]:
    record = repo["record"]
    record_path = repo["record_path"]
    return {
        "expected_stage": STAGE_ID,
        "expected_epoch": record["authority_epoch"],
        "expected_authority_record_sha256": _sha256(record_path.read_bytes()),
        "expected_risk": record["scope"]["risk"],
        "expected_scope_sha256": record["scope_sha256"],
        "expected_planning_base": record["planning_baseline"]["commit"],
        "expected_action_ceiling": record["action_ceiling"],
        "expected_remote_name": record["vcs_target"]["remote_name"],
        "expected_effective_fetch_url_sha256": record["vcs_target"][
            "effective_fetch_url_sha256"
        ],
        "expected_effective_push_url_sha256": record["vcs_target"][
            "effective_push_url_sha256"
        ],
        "expected_target_branch": record["vcs_target"]["target_branch"],
        "expected_authorized_remote_tip": record["vcs_target"]["authorized_remote_tip"],
    }


def _validate(
    repo: dict[str, Any],
    *,
    required_action: str = "implement",
    expected_overrides: dict[str, Any] | None = None,
    **action_inputs: Any,
) -> dict[str, Any]:
    module = _load_validator_module()
    expected = _expected(repo)
    if expected_overrides:
        expected.update(expected_overrides)
    return module.validate_authority(
        project_root=repo["root"],
        authority_dir=repo["record_path"].parent,
        required_action=required_action,
        **expected,
        **action_inputs,
    )


def _assert_fails_closed(report: dict[str, Any]) -> None:
    assert report["status"] == "FAIL"
    assert report["binding_consistent"] is False
    assert report["human_authorized"] in {False, "external", "unknown"}
    assert report["errors"]


def _write_implementation_review(
    repo: dict[str, Any],
    *,
    inventory_bytes: bytes | None = None,
    omit_subject_files: bool = False,
    required_slots: int = 1,
) -> dict[str, Any]:
    module = _load_validator_module()
    root = repo["root"]
    implementation = root / ".harness" / "reviews" / STAGE_ID / "implementation"
    implementation.mkdir(parents=True, exist_ok=True)
    manifest_path = implementation / "reviewed-change-manifest.json"
    diff_path = implementation / "reviewed-change.diff"
    review_set_path = implementation / "review-set.json"
    built = module.build_review_subject_manifest(
        project_root=root,
        stage_id=STAGE_ID,
        planning_base=repo["baseline"],
    )
    assert built["status"] == "PASS", built["errors"]
    _write_json(manifest_path, built["manifest"])
    diff_path.write_bytes(
        inventory_bytes or module.build_reviewed_inventory_bytes(built["manifest"])
    )
    artifacts = []
    if not omit_subject_files:
        artifacts.extend(
            {"path": item["path"], "sha256": item["sha256"]}
            for item in built["manifest"]["changes"]
            if item["kind"] == "file"
        )
    artifacts.extend(
        [
            {
                "path": manifest_path.relative_to(root).as_posix(),
                "sha256": _sha256(manifest_path.read_bytes()),
            },
            {
                "path": diff_path.relative_to(root).as_posix(),
                "sha256": _sha256(diff_path.read_bytes()),
            },
        ]
    )
    artifacts = sorted(artifacts, key=lambda item: item["path"])
    packet_sha256 = _canonical_sha256(artifacts)
    receipts = [
        {
            "schema_version": "repopilot.independent_review_receipt/v1",
            "stage_id": STAGE_ID,
            "phase": "implementation",
            "slot_id": f"implementation-review-slot-{index + 1}",
            "implementer_instance_id": "/root",
            "reviewer": {
                "provider": "test-provider",
                "model": "test-model",
                "instance_id": f"/root/reviewer-{index + 1}",
            },
            "context_evidence": {
                "evidence_source": "host_tool_metadata",
                "parent_context_inheritance": "none",
                "other_first_round_conclusions_visible": False,
            },
            "review_round": "first_round",
            "reviewed_packet_sha256": packet_sha256,
            "reviewed_artifacts": artifacts,
            "conclusion": {
                "status": "no_findings",
                "findings": [],
                "gate_verdict": "ready",
                "residual_uncertainty": "Host provenance remains external.",
            },
            "lineage": None,
        }
        for index in range(required_slots)
    ]
    activation_ref = ACTIVATION_REF
    activation_path = root / activation_ref
    activation_path.parent.mkdir(parents=True, exist_ok=True)
    activation_path.write_text(
        "pre-change authority activated the review validator\n",
        encoding="utf-8",
    )
    review_set = {
        "schema_version": "repopilot.independent_review_set/v1",
        "stage_id": STAGE_ID,
        "phase": "implementation",
        "activation": {
            "status": "active",
            "activated_after_change": "generalize-independent-review-provider",
            "authority": "pre_change_process_contract",
            "activation_ref": activation_ref,
            "activation_ref_sha256": _sha256(activation_path.read_bytes()),
            "retroactive_plan_validation": False,
        },
        "external_gate_checks": {},
        "implementer": {"instance_id": "/root"},
        "baseline": {
            "kind": "packet_manifest",
            "immutable_ref": f"sha256:{packet_sha256}",
            "artifacts": artifacts,
            "packet_sha256": packet_sha256,
        },
        "review_history": [],
        "receipts": receipts,
    }
    _write_json(review_set_path, review_set)
    return {
        "manifest": built["manifest"],
        "manifest_path": manifest_path,
        "diff_path": diff_path,
        "review_set_path": review_set_path,
        "packet_sha256": packet_sha256,
        "required_slots": required_slots,
    }


def _review_inputs(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "implementation_review_set": review["review_set_path"],
        "required_review_slots": review["required_slots"],
        "expected_review_packet_sha256": review["packet_sha256"],
    }


def _write_plan_review(
    repo: dict[str, Any],
    *,
    required_slots: int,
) -> dict[str, Any]:
    review = _write_implementation_review(repo, required_slots=required_slots)
    document = json.loads(review["review_set_path"].read_text(encoding="utf-8"))
    document["phase"] = "plan"
    for receipt in document["receipts"]:
        receipt["phase"] = "plan"
    path = (
        repo["root"]
        / ".harness"
        / "reviews"
        / STAGE_ID
        / "plan"
        / "review-set.json"
    )
    _write_json(path, document)
    return {
        "review_set_path": path,
        "packet_sha256": review["packet_sha256"],
        "required_slots": required_slots,
    }


def _plan_review_inputs(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_review_set": review["review_set_path"],
        "required_plan_review_slots": review["required_slots"],
        "expected_plan_review_packet_sha256": review["packet_sha256"],
    }


def _bind_review_slots(
    repo: dict[str, Any],
    *,
    plan: object,
    implementation: object,
    risk: str | None = None,
) -> None:
    scope = repo["record"]["scope"]
    scope["review_slot_requirements"] = {
        "plan": plan,
        "implementation": implementation,
    }
    if risk is not None:
        scope["risk"] = risk
    repo["record"]["scope_sha256"] = _canonical_sha256(scope)
    repo["record_path"] = _write_record(repo["root"], repo["record"])


def _write_delivery_binding(
    repo: dict[str, Any], review: dict[str, Any]
) -> Path:
    root = repo["root"]
    binding_path = (
        root / ".harness" / "authority" / STAGE_ID / "delivery-binding.json"
    )
    binding = {
        "schema_version": "repopilot.stage_delivery_binding/v1",
        "stage_id": STAGE_ID,
        "authority_epoch": 1,
        "authority_record_sha256": _sha256(repo["record_path"].read_bytes()),
        "reviewed_manifest": {
            "path": review["manifest_path"].relative_to(root).as_posix(),
            "sha256": _sha256(review["manifest_path"].read_bytes()),
        },
        "reviewed_diff": {
            "path": review["diff_path"].relative_to(root).as_posix(),
            "sha256": _sha256(review["diff_path"].read_bytes()),
        },
        "implementation_review_set": {
            "path": review["review_set_path"].relative_to(root).as_posix(),
            "sha256": _sha256(review["review_set_path"].read_bytes()),
            "packet_sha256": review["packet_sha256"],
        },
        "final_harness_files": [
            {
                "path": ".harness/allowed_files.md",
                "sha256": _sha256(
                    (root / ".harness" / "allowed_files.md").read_bytes()
                ),
            },
            {
                "path": ".harness/review_checklist.md",
                "sha256": _sha256(
                    (root / ".harness" / "review_checklist.md").read_bytes()
                ),
            },
        ],
    }
    _write_json(binding_path, binding)
    return binding_path


def test_frozen_epoch_one_bytes_match_confirmed_host_hash() -> None:
    project_root = Path(__file__).resolve().parents[1]
    record_path = _record_path(project_root)

    assert _sha256(record_path.read_bytes()) == CONFIRMED_RECORD_SHA256
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["planning_baseline"]["commit"] == CONFIRMED_PLANNING_BASE
    assert record["scope_sha256"] == _canonical_sha256(record["scope"])


def test_canonical_authority_record_is_mechanical_only(
    authority_repo: dict[str, Any],
) -> None:
    report = _validate(authority_repo)

    assert report["status"] == "PASS"
    assert report["binding_consistent"] is True
    assert report["claim_level"] == "mechanical_consistency_only"
    assert report["human_authorized"] in {False, "external"}
    assert report["technical_ready"] in {False, "external"}
    assert report["vcs_pushed"] == "not_attempted"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda record: record.update(unexpected=True),
        lambda record: record["authority_source"].update(user_message="secret"),
        lambda record: record["vcs_target"].update(credential="secret"),
    ],
    ids=["unknown-top-level", "message-content", "credential-field"],
)
def test_unknown_or_sensitive_fields_fail_closed(
    authority_repo: dict[str, Any],
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    mutation(authority_repo["record"])
    _write_record(authority_repo["root"], authority_repo["record"])

    _assert_fails_closed(_validate(authority_repo))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda record: record.update(authority_epoch="1"),
        lambda record: record.update(action_ceiling="deploy"),
        lambda record: record["authority_source"].update(host_reference=""),
        lambda record: record["scope"]["allowed_path_rules"].update(
            prefixes=["../outside/"]
        ),
        lambda record: record["scope"]["allowed_path_rules"].update(
            prefixes=["src//"]
        ),
        lambda record: record["planning_baseline"].update(commit="not-an-oid"),
        lambda record: record["vcs_target"].update(target_branch="main.lock"),
    ],
    ids=[
        "epoch-type",
        "invalid-action",
        "missing-host-ref",
        "bad-path",
        "aliased-prefix",
        "bad-oid",
        "bad-branch",
    ],
)
def test_malformed_required_values_fail_closed(
    authority_repo: dict[str, Any],
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    mutation(authority_repo["record"])
    _write_record(authority_repo["root"], authority_repo["record"])

    _assert_fails_closed(_validate(authority_repo))


@pytest.mark.parametrize("field", ["exact", "prefixes"])
@pytest.mark.parametrize(
    "bad_value",
    [[{}], [[]], [1], [None], ["src/", {}]],
    ids=["dictionary", "list", "integer", "null", "mixed"],
)
def test_malformed_path_rule_members_return_structured_failure(
    authority_repo: dict[str, Any], field: str, bad_value: list[object]
) -> None:
    record = authority_repo["record"]
    record["scope"]["allowed_path_rules"][field] = bad_value
    record["scope_sha256"] = _canonical_sha256(record["scope"])
    _write_record(authority_repo["root"], record)

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert any(error["code"] == "PATH_RULE_INVALID" for error in report["errors"])
    assert "Traceback" not in json.dumps(report)


def test_malformed_json_returns_a_redacted_failure(
    authority_repo: dict[str, Any],
) -> None:
    authority_repo["record_path"].write_text('{"schema_version":', encoding="utf-8")

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert "Traceback" not in json.dumps(report)


def test_record_internal_scope_rewrite_cannot_inherit_expected_envelope(
    authority_repo: dict[str, Any],
) -> None:
    authority_repo["record"]["scope"]["summary"] = "rewritten scope"
    authority_repo["record"]["scope_sha256"] = _canonical_sha256(
        authority_repo["record"]["scope"]
    )
    _write_record(authority_repo["root"], authority_repo["record"])

    report = _validate(
        authority_repo,
        expected_overrides={
            "expected_scope_sha256": _valid_record(
                authority_repo["root"], authority_repo["baseline"]
            )["scope_sha256"]
        },
    )

    _assert_fails_closed(report)


def test_wrong_host_expected_record_hash_fails_closed(
    authority_repo: dict[str, Any],
) -> None:
    report = _validate(
        authority_repo,
        expected_overrides={"expected_authority_record_sha256": ONE_SHA256},
    )

    _assert_fails_closed(report)


@pytest.mark.parametrize(
    ("expected_key", "wrong_value"),
    [
        ("expected_stage", "other-stage"),
        ("expected_epoch", 2),
        ("expected_risk", "medium"),
        ("expected_scope_sha256", ONE_SHA256),
        ("expected_planning_base", "1" * 40),
        ("expected_action_ceiling", "archive"),
        ("expected_remote_name", "upstream"),
        ("expected_effective_fetch_url_sha256", ONE_SHA256),
        ("expected_effective_push_url_sha256", ONE_SHA256),
        ("expected_target_branch", "release"),
        ("expected_authorized_remote_tip", "1" * 40),
    ],
)
def test_every_host_retained_expected_value_is_independent(
    authority_repo: dict[str, Any],
    expected_key: str,
    wrong_value: object,
) -> None:
    report = _validate(
        authority_repo,
        expected_overrides={expected_key: wrong_value},
    )

    _assert_fails_closed(report)


def test_action_above_confirmed_ceiling_fails_closed(
    authority_repo: dict[str, Any],
) -> None:
    authority_repo["record"]["action_ceiling"] = "implement"
    _write_record(authority_repo["root"], authority_repo["record"])

    report = _validate(authority_repo, required_action="archive")

    _assert_fails_closed(report)


def test_stale_epoch_is_not_accepted_when_a_later_linear_head_exists(
    authority_repo: dict[str, Any],
) -> None:
    epoch_one_hash = _sha256(authority_repo["record_path"].read_bytes())
    epoch_two = copy.deepcopy(authority_repo["record"])
    epoch_two["authority_epoch"] = 2
    epoch_two["supersedes_record_sha256"] = epoch_one_hash
    _write_record(authority_repo["root"], epoch_two, epoch=2)

    _assert_fails_closed(_validate(authority_repo))


def test_gap_or_missing_predecessor_fails_lineage_validation(
    authority_repo: dict[str, Any],
) -> None:
    epoch_three = copy.deepcopy(authority_repo["record"])
    epoch_three["authority_epoch"] = 3
    epoch_three["supersedes_record_sha256"] = ONE_SHA256
    epoch_three_path = _write_record(authority_repo["root"], epoch_three, epoch=3)
    authority_repo.update(record=epoch_three, record_path=epoch_three_path)

    _assert_fails_closed(_validate(authority_repo))


@pytest.mark.parametrize(
    "unexpected_name",
    ["epoch-1.json", "epoch-0001-copy.json", "fork.json", "epoch-0002.json.bak"],
)
def test_fork_like_or_unexpected_authority_entries_fail_closed(
    authority_repo: dict[str, Any],
    unexpected_name: str,
) -> None:
    unexpected = authority_repo["record_path"].parent / unexpected_name
    unexpected.write_text("{}\n", encoding="utf-8")

    _assert_fails_closed(_validate(authority_repo))


def test_symlinked_authority_directory_fails_closed(
    authority_repo: dict[str, Any],
) -> None:
    authority_dir = authority_repo["record_path"].parent
    real_dir = authority_repo["root"] / ".harness" / "real-authority"
    authority_dir.rename(real_dir)
    authority_dir.symlink_to(real_dir, target_is_directory=True)

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert any(
        error["code"] == "AUTHORITY_DIRECTORY_INVALID" for error in report["errors"]
    )


def test_nested_stale_authority_snapshot_cannot_replace_canonical_chain(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    canonical_dir = authority_repo["record_path"].parent
    snapshot_dir = canonical_dir / "snapshot"
    snapshot_dir.mkdir()
    (snapshot_dir / "epoch-0001.json").write_bytes(
        authority_repo["record_path"].read_bytes()
    )
    second = copy.deepcopy(authority_repo["record"])
    second["authority_epoch"] = 2
    second["supersedes_record_sha256"] = _sha256(
        authority_repo["record_path"].read_bytes()
    )
    _write_record(root, second, epoch=2)
    module = _load_validator_module()

    report = module.validate_authority(
        project_root=root,
        authority_dir=snapshot_dir,
        required_action="implement",
        **_expected(authority_repo),
    )

    _assert_fails_closed(report)
    assert any(
        error["code"] == "AUTHORITY_DIRECTORY_PATH_MISMATCH"
        for error in report["errors"]
    )


@pytest.mark.parametrize(
    "change_kind",
    ["committed", "staged", "unstaged", "untracked", "rename", "delete"],
)
def test_every_git_change_category_detects_scope_escape(
    authority_repo: dict[str, Any],
    change_kind: str,
) -> None:
    root = authority_repo["root"]
    outside = root / "docs" / "outside.md"
    if change_kind == "committed":
        outside.write_text("committed escape\n", encoding="utf-8")
        _git(root, "add", "docs/outside.md")
        _git(root, "commit", "-m", "outside scope")
    elif change_kind == "staged":
        outside.write_text("staged escape\n", encoding="utf-8")
        _git(root, "add", "docs/outside.md")
    elif change_kind == "unstaged":
        outside.write_text("unstaged escape\n", encoding="utf-8")
    elif change_kind == "untracked":
        (root / "outside.txt").write_text("untracked escape\n", encoding="utf-8")
    elif change_kind == "rename":
        _git(root, "mv", "src/app.py", "outside.py")
    elif change_kind == "delete":
        outside.unlink()
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(change_kind)

    _assert_fails_closed(_validate(authority_repo))


def test_ignored_untracked_scope_escape_is_not_hidden(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    exclude = Path(_git(root, "rev-parse", "--git-path", "info/exclude"))
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.write_text("ignored-outside.txt\n", encoding="utf-8")
    (root / "ignored-outside.txt").write_text("hidden escape\n", encoding="utf-8")

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert "ignored-outside.txt" in report["changed_paths"]


def test_cache_directory_does_not_hide_arbitrary_ignored_source(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    exclude = Path(_git(root, "rev-parse", "--git-path", "info/exclude"))
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.write_text(".pytest_cache/\n", encoding="utf-8")
    hidden = root / ".pytest_cache" / "evil.py"
    hidden.parent.mkdir()
    hidden.write_text("MUTATE = True\n", encoding="utf-8")

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert ".pytest_cache/evil.py" in report["changed_paths"]


def test_control_characters_cannot_inject_review_inventory_rows(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    injected = "src/actual.py\nDELETE\tdecoy.py"
    (root / injected).write_text("VALUE = 2\n", encoding="utf-8")

    report = _validate(authority_repo)
    manifest = _load_validator_module().build_review_subject_manifest(
        project_root=root,
        stage_id=STAGE_ID,
        planning_base=authority_repo["baseline"],
    )

    _assert_fails_closed(report)
    assert manifest["status"] == "FAIL"
    assert injected in report["changed_paths"]


@pytest.mark.skipif(os.name != "posix", reason="raw Git path bytes are POSIX-only")
def test_non_utf8_git_path_fails_review_manifest_closed(
    authority_repo: dict[str, Any],
) -> None:
    module = _load_validator_module()
    root_bytes = os.fsencode(authority_repo["root"])
    blob = subprocess.run(
        [b"git", b"hash-object", b"-w", b"--stdin"],
        cwd=root_bytes,
        input=b"VALUE = 2\n",
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    raw_path = b"src/bad\xff.py"
    subprocess.run(
        [
            b"git",
            b"update-index",
            b"--add",
            b"--cacheinfo",
            b"100644," + blob + b"," + raw_path,
        ],
        cwd=root_bytes,
        capture_output=True,
        check=True,
        timeout=10,
    )

    report = module.build_review_subject_manifest(
        project_root=authority_repo["root"],
        stage_id=STAGE_ID,
        planning_base=authority_repo["baseline"],
    )

    assert report["status"] == "FAIL"
    assert any(
        error["code"] in {"GIT_CHANGESET_FAILED", "GIT_MODE_SCAN_FAILED"}
        for error in report["errors"]
    )
    assert "\ufffd" not in json.dumps(report, ensure_ascii=False)


def test_changed_gitlink_fails_closed(authority_repo: dict[str, Any]) -> None:
    root = authority_repo["root"]
    _git(root, "update-index", "--add", "--cacheinfo", f"160000,{repo_oid(root)},src/vendor")

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert any(error["code"] == "GITLINK_FORBIDDEN" for error in report["errors"])


def repo_oid(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD")


def test_commit_without_final_review_and_delivery_fails_closed(
    authority_repo: dict[str, Any],
) -> None:
    allowed_files = authority_repo["root"] / ".harness" / "allowed_files.md"
    allowed_files.write_text("# expanded after confirmation\n", encoding="utf-8")

    report = _validate(authority_repo, required_action="commit")
    _assert_fails_closed(report)
    codes = {error["code"] for error in report["errors"]}
    assert "IMPLEMENTATION_REVIEW_REQUIRED" in codes
    assert "DELIVERY_BINDING_REQUIRED" in codes


def test_cr_closeout_p1_009_commit_accepts_reviewed_final_harness_reset(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    (root / ".harness" / "allowed_files.md").write_text(
        "# next stage reset\n- `openspec/changes/next-stage/**`\n",
        encoding="utf-8",
    )
    (root / ".harness" / "review_checklist.md").write_text(
        "# next stage review reset\n",
        encoding="utf-8",
    )
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-f", "-A")

    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    assert report["status"] == "PASS", report["errors"]
    assert not any(
        error["code"] == "ALLOWED_FILES_DRIFT" for error in report["errors"]
    )


def test_cr_closeout_p1_011_commit_rejects_current_packet_with_stale_index(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    reviewed_spec = root / "src" / "stage-spec.md"
    reviewed_spec.write_text("reviewed spec without final EOF marker", encoding="utf-8")
    first_review = _write_implementation_review(authority_repo)
    _write_delivery_binding(authority_repo, first_review)
    _git(root, "add", "-f", "-A")

    reviewed_spec.write_text(
        "reviewed spec without final EOF marker\n",
        encoding="utf-8",
    )
    current_review = _write_implementation_review(authority_repo)
    current_delivery = _write_delivery_binding(authority_repo, current_review)
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(current_review),
        delivery_binding=current_delivery,
    )

    assert report["status"] == "FAIL"
    assert "CANDIDATE_INDEX_BLOB_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("omission", "CANDIDATE_INDEX_PATH_SET_MISMATCH"),
        ("extra", "CANDIDATE_INDEX_PATH_SET_MISMATCH"),
        ("mode", "CANDIDATE_INDEX_MODE_MISMATCH"),
        ("tail_divergence", "CANDIDATE_INDEX_BLOB_MISMATCH"),
        ("deletion_state", "CANDIDATE_INDEX_STATE_MISMATCH"),
    ],
)
def test_cr_closeout_p1_011_commit_index_projection_is_exact(
    authority_repo: dict[str, Any],
    mutation: str,
    expected_code: str,
) -> None:
    root = authority_repo["root"]
    if mutation == "deletion_state":
        (root / "src" / "app.py").unlink()
    else:
        (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-f", "-A")
    if mutation == "omission":
        _git(
            root,
            "rm",
            "--cached",
            "--",
            delivery.relative_to(root).as_posix(),
        )
    elif mutation == "extra":
        _git(root, "update-index", "--chmod=+x", "docs/outside.md")
    elif mutation == "mode":
        _git(root, "update-index", "--chmod=+x", "src/app.py")
    elif mutation == "tail_divergence":
        delivery.write_text(delivery.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    else:
        _git(root, "restore", "--staged", "--", "src/app.py")
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )
    _assert_fails_closed(report)
    assert expected_code in {error["code"] for error in report["errors"]}


def test_cr_closeout_p1_011_ignored_reviewed_file_must_be_staged(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    (root / ".gitignore").write_text("src/ignored.py\n", encoding="utf-8")
    (root / "src" / "ignored.py").write_text("IGNORED = True\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-A")
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )
    _assert_fails_closed(report)
    assert "CANDIDATE_INDEX_PATH_SET_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_cr_closeout_p1_012_dual_post_review_mode_drift_is_rejected(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    reviewed_file = root / "src" / "app.py"
    reviewed_file.write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-f", "-A")

    reviewed_file.chmod(0o755)
    _git(root, "update-index", "--chmod=+x", "src/app.py")
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    _assert_fails_closed(report)
    assert "CANDIDATE_INDEX_REVIEW_MODE_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_cr_closeout_p1_009_commit_requires_delivery_binding(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(authority_repo)
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
    )
    _assert_fails_closed(report)
    assert "DELIVERY_BINDING_REQUIRED" in {
        error["code"] for error in report["errors"]
    }


def test_cr_closeout_p1_009_commit_rejects_post_binding_harness_drift(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    (root / ".harness" / "allowed_files.md").write_text(
        "# drift after final delivery binding\n",
        encoding="utf-8",
    )
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )
    _assert_fails_closed(report)
    codes = {error["code"] for error in report["errors"]}
    assert "REVIEW_MANIFEST_DRIFT" in codes
    assert "DELIVERY_BINDING_INVALID" in codes


def test_cr_closeout_p1_009_commit_rejects_unbound_final_harness_hash(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    document = json.loads(delivery.read_text(encoding="utf-8"))
    document["final_harness_files"][0]["sha256"] = ONE_SHA256
    _write_json(delivery, document)
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )
    _assert_fails_closed(report)
    assert "DELIVERY_BINDING_INVALID" in {
        error["code"] for error in report["errors"]
    }


def test_active_allowed_files_hash_drift_fails_archive_even_with_fresh_review(
    authority_repo: dict[str, Any],
) -> None:
    allowed_files = authority_repo["root"] / ".harness" / "allowed_files.md"
    allowed_files.write_text("# expanded after confirmation\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert any(error["code"] == "ALLOWED_FILES_DRIFT" for error in report["errors"])


def test_archive_requires_actual_implementation_review_set(
    authority_repo: dict[str, Any],
) -> None:
    report = _validate(authority_repo, required_action="archive")

    _assert_fails_closed(report)


def test_low_risk_bound_zero_archive_consumes_complete_empty_review_packet(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=0, implementation=0, risk="low")
    review = _write_implementation_review(authority_repo, required_slots=0)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    assert report["status"] == "PASS"
    assert report["errors"] == []


def test_unbound_zero_archive_fails_closed(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(authority_repo, required_slots=0)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert "ZERO_REVIEW_SLOTS_UNBOUND" in {
        error["code"] for error in report["errors"]
    }


def test_high_risk_bound_zero_archive_fails_closed(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=2, implementation=0, risk="high")
    review = _write_implementation_review(authority_repo, required_slots=0)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert "ZERO_REVIEW_SLOTS_RISK_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize(
    ("plan_slots", "implementation_slots"),
    [(0, 2), (2, 0)],
)
def test_high_risk_mixed_phase_zero_binding_fails_every_action_closed(
    authority_repo: dict[str, Any],
    plan_slots: int,
    implementation_slots: int,
) -> None:
    _bind_review_slots(
        authority_repo,
        plan=plan_slots,
        implementation=implementation_slots,
        risk="high",
    )

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert "ZERO_REVIEW_SLOTS_RISK_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize("caller_slots", [1, 3])
def test_bound_positive_implementation_count_must_match_caller(
    authority_repo: dict[str, Any], caller_slots: int
) -> None:
    _bind_review_slots(authority_repo, plan=2, implementation=2)
    review = _write_implementation_review(
        authority_repo,
        required_slots=caller_slots,
    )

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert "REVIEW_SLOT_REQUIREMENT_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_bound_future_implement_consumes_canonical_plan_review_set(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=2, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=2)

    report = _validate(authority_repo, **_plan_review_inputs(review))

    assert report["status"] == "PASS"
    assert report["errors"] == []


def test_bound_future_implement_rejects_missing_plan_review_set(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=2, implementation=1)

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert "PLAN_REVIEW_REQUIRED" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize("caller_slots", [1, 3])
def test_bound_positive_plan_count_must_match_caller(
    authority_repo: dict[str, Any], caller_slots: int
) -> None:
    _bind_review_slots(authority_repo, plan=2, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=caller_slots)

    report = _validate(authority_repo, **_plan_review_inputs(review))

    _assert_fails_closed(report)
    assert "REVIEW_SLOT_REQUIREMENT_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_bound_future_implement_rejects_implementation_phase_substitution(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=1, implementation=1)
    review = _write_implementation_review(authority_repo)

    report = _validate(
        authority_repo,
        plan_review_set=review["review_set_path"],
        required_plan_review_slots=1,
        expected_plan_review_packet_sha256=review["packet_sha256"],
    )

    _assert_fails_closed(report)
    assert "PLAN_REVIEW_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize(
    "alias",
    [
        ".harness/reviews/{stage}/plan/../plan/review-set.json",
        ".harness/reviews/{stage}/./plan/review-set.json",
    ],
)
def test_bound_future_implement_rejects_lexical_plan_path_alias(
    authority_repo: dict[str, Any], alias: str
) -> None:
    _bind_review_slots(authority_repo, plan=1, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=1)
    inputs = _plan_review_inputs(review)
    inputs["plan_review_set"] = alias.format(stage=STAGE_ID)

    report = _validate(authority_repo, **inputs)

    _assert_fails_closed(report)
    assert "PLAN_REVIEW_INVALID" in {
        error["code"] for error in report["errors"]
    }


def test_exact_review_path_spellings_support_native_windows_path_objects() -> None:
    module = _load_validator_module()
    root = PureWindowsPath("C:/repo")
    expected = root / ".harness" / "reviews" / STAGE_ID / "plan" / "review-set.json"

    spellings = module._exact_path_spellings(root, expected)

    assert str(expected) in spellings
    assert expected.as_posix() in spellings
    assert str(expected.relative_to(root)) in spellings
    assert expected.relative_to(root).as_posix() in spellings
    assert str(expected.parent / ".." / "plan" / expected.name) not in spellings


def test_bound_future_implement_rejects_wrong_plan_phase_at_canonical_path(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=1, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=1)
    document = json.loads(review["review_set_path"].read_text(encoding="utf-8"))
    document["phase"] = "implementation"
    document["receipts"][0]["phase"] = "implementation"
    _write_json(review["review_set_path"], document)

    report = _validate(authority_repo, **_plan_review_inputs(review))

    _assert_fails_closed(report)
    assert "PLAN_REVIEW_INVALID" in {
        error["code"] for error in report["errors"]
    }


def test_bound_future_implement_rejects_host_plan_packet_mismatch(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=1, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=1)
    inputs = _plan_review_inputs(review)
    inputs["expected_plan_review_packet_sha256"] = ONE_SHA256

    report = _validate(authority_repo, **inputs)

    _assert_fails_closed(report)
    assert "REVIEW_PACKET_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_bound_future_implement_rejects_reduced_plan_manifest_against_host_hash(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=1, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=1)
    document = json.loads(review["review_set_path"].read_text(encoding="utf-8"))
    reduced = document["baseline"]["artifacts"][1:]
    reduced_packet = _canonical_sha256(reduced)
    document["baseline"]["artifacts"] = reduced
    document["baseline"]["packet_sha256"] = reduced_packet
    document["baseline"]["immutable_ref"] = f"sha256:{reduced_packet}"
    document["receipts"][0]["reviewed_artifacts"] = copy.deepcopy(reduced)
    document["receipts"][0]["reviewed_packet_sha256"] = reduced_packet
    _write_json(review["review_set_path"], document)

    report = _validate(authority_repo, **_plan_review_inputs(review))

    _assert_fails_closed(report)
    assert "REVIEW_PACKET_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_bound_future_implement_rejects_incomplete_plan_activation_evidence(
    authority_repo: dict[str, Any],
) -> None:
    _bind_review_slots(authority_repo, plan=1, implementation=1)
    review = _write_plan_review(authority_repo, required_slots=1)
    document = json.loads(review["review_set_path"].read_text(encoding="utf-8"))
    document["activation"].pop("activation_ref_sha256")
    _write_json(review["review_set_path"], document)

    report = _validate(authority_repo, **_plan_review_inputs(review))

    _assert_fails_closed(report)
    assert "PLAN_REVIEW_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize(
    "binding",
    [
        {"plan": True, "implementation": 1},
        {"plan": 1.0, "implementation": 1},
        {"plan": "1", "implementation": 1},
        {"plan": -1, "implementation": 1},
        {"plan": 1},
        {"plan": 1, "implementation": 1, "extra": 0},
    ],
)
def test_review_slot_binding_schema_fails_closed(
    authority_repo: dict[str, Any], binding: dict[str, object]
) -> None:
    authority_repo["record"]["scope"]["review_slot_requirements"] = binding
    authority_repo["record"]["scope_sha256"] = _canonical_sha256(
        authority_repo["record"]["scope"]
    )
    authority_repo["record_path"] = _write_record(
        authority_repo["root"], authority_repo["record"]
    )

    report = _validate(authority_repo)

    _assert_fails_closed(report)
    assert "REVIEW_SLOT_REQUIREMENTS_INVALID" in {
        error["code"] for error in report["errors"]
    }


def test_legacy_positive_implementation_review_remains_compatible(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(authority_repo)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    assert report["status"] == "PASS"
    assert report["errors"] == []


def test_archive_rejects_review_packet_that_omits_subject_files(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(authority_repo, omit_subject_files=True)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert any(
        error["code"] == "REVIEW_SUBJECT_COVERAGE_MISMATCH"
        for error in report["errors"]
    )


def test_archive_rejects_arbitrary_reviewed_change_inventory(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(
        authority_repo,
        inventory_bytes=b"arbitrary review text\n",
    )

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert any(error["code"] == "REVIEW_DIFF_DRIFT" for error in report["errors"])


def test_malformed_review_artifact_returns_structured_failure(
    authority_repo: dict[str, Any],
) -> None:
    review = _write_implementation_review(authority_repo)
    review_set = json.loads(review["review_set_path"].read_text(encoding="utf-8"))
    review_set["baseline"]["artifacts"][0] = "malformed"
    _write_json(review["review_set_path"], review_set)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert any(
        error["code"] == "REVIEW_SUBJECT_COVERAGE_MISMATCH"
        for error in report["errors"]
    )


@pytest.mark.parametrize("bad_path", ["evil\x00.txt", "evil\nrow", "evil\tcell"])
def test_malformed_review_artifact_path_returns_structured_failure(
    authority_repo: dict[str, Any], bad_path: str
) -> None:
    review = _write_implementation_review(authority_repo)
    review_set = json.loads(review["review_set_path"].read_text(encoding="utf-8"))
    review_set["baseline"]["artifacts"][0]["path"] = bad_path
    _write_json(review["review_set_path"], review_set)

    report = _validate(
        authority_repo,
        required_action="archive",
        **_review_inputs(review),
    )

    _assert_fails_closed(report)
    assert any(
        error["code"] == "IMPLEMENTATION_REVIEW_INVALID"
        for error in report["errors"]
    )


def test_merge_requires_delivery_binding_review_packet_and_candidate(
    authority_repo: dict[str, Any],
) -> None:
    report = _validate(authority_repo, required_action="merge")

    _assert_fails_closed(report)


def test_candidate_head_drift_fails_merge_preflight(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    candidate = _git(root, "rev-parse", "HEAD")
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(root, "add", "src/app.py")
    _git(root, "commit", "-m", "later allowed commit")

    report = _validate(
        authority_repo,
        required_action="merge",
        expected_candidate_head=candidate,
    )

    _assert_fails_closed(report)


def test_merge_binds_authorized_endpoint_tip_and_same_repository(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    bare = root.parent / f"{root.name}-remote.git"
    target = root.parent / f"{root.name}-target"
    unrelated = root.parent / f"{root.name}-unrelated"
    bare.mkdir()
    _git(bare, "init", "--bare")
    endpoint = bare.resolve().as_uri()
    _git(root, "remote", "add", "origin", endpoint)
    _git(root, "push", "origin", "main:main")
    endpoint_hash = _sha256(endpoint.encode("utf-8"))
    authority_repo["record"]["vcs_target"].update(
        effective_fetch_url_sha256=endpoint_hash,
        effective_push_url_sha256=endpoint_hash,
    )
    _write_record(root, authority_repo["record"])
    _git(root, "switch", "-c", "feature")
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "candidate")
    candidate = _git(root, "rev-parse", "HEAD")
    _git(root, "worktree", "add", str(target), "main")

    report = _validate(
        authority_repo,
        required_action="merge",
        **_review_inputs(review),
        delivery_binding=delivery,
        expected_candidate_head=candidate,
        explicit_source_oid=candidate,
        merge_target_worktree=target,
        expected_target_premerge_head=authority_repo["baseline"],
    )
    assert report["status"] == "PASS", report["errors"]

    _git(root.parent, "clone", endpoint, str(unrelated))
    report = _validate(
        authority_repo,
        required_action="merge",
        **_review_inputs(review),
        delivery_binding=delivery,
        expected_candidate_head=candidate,
        explicit_source_oid=candidate,
        merge_target_worktree=unrelated,
        expected_target_premerge_head=authority_repo["baseline"],
    )
    _assert_fails_closed(report)
    assert any(
        error["code"] == "MERGE_REPOSITORY_MISMATCH" for error in report["errors"]
    )

    wrong_source = _validate(
        authority_repo,
        required_action="merge",
        **_review_inputs(review),
        delivery_binding=delivery,
        expected_candidate_head=candidate,
        explicit_source_oid=authority_repo["baseline"],
        merge_target_worktree=target,
        expected_target_premerge_head=authority_repo["baseline"],
    )
    _assert_fails_closed(wrong_source)
    assert any(
        error["code"] == "EXPLICIT_SOURCE_MISMATCH"
        for error in wrong_source["errors"]
    )

    (target / "src" / "app.py").write_text("dirty target\n", encoding="utf-8")
    dirty_target = _validate(
        authority_repo,
        required_action="merge",
        **_review_inputs(review),
        delivery_binding=delivery,
        expected_candidate_head=candidate,
        explicit_source_oid=candidate,
        merge_target_worktree=target,
        expected_target_premerge_head=authority_repo["baseline"],
    )
    _assert_fails_closed(dirty_target)
    assert any(error["code"] == "TARGET_WORKTREE_DIRTY" for error in dirty_target["errors"])

    (target / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(root, "config", "--add", "remote.origin.pushurl", endpoint)
    _git(root, "config", "--add", "remote.origin.pushurl", endpoint)
    multiple_destinations = _validate(
        authority_repo,
        required_action="merge",
        **_review_inputs(review),
        delivery_binding=delivery,
        expected_candidate_head=candidate,
        explicit_source_oid=candidate,
        merge_target_worktree=target,
        expected_target_premerge_head=authority_repo["baseline"],
    )
    _assert_fails_closed(multiple_destinations)
    assert any(
        error["code"] == "REMOTE_ENDPOINT_AMBIGUOUS"
        for error in multiple_destinations["errors"]
    )


@pytest.mark.parametrize(
    ("fetch_url", "push_url", "expected_fetch", "expected_push"),
    [
        (
            "ssh://same.example.invalid/repo.git",
            "ssh://same.example.invalid/repo.git",
            ZERO_SHA256,
            ZERO_SHA256,
        ),
        (
            "ssh://fetch.example.invalid/repo.git",
            "ssh://push.example.invalid/repo.git",
            None,
            None,
        ),
    ],
    ids=["fingerprint-mismatch", "fetch-push-inequality"],
)
def test_remote_tip_is_not_queried_before_endpoint_binding_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fetch_url: str,
    push_url: str,
    expected_fetch: str | None,
    expected_push: str | None,
) -> None:
    module = _load_validator_module()
    query_calls: list[tuple[str, str]] = []

    def remote_url(
        root: Path,
        remote_name: str,
        *,
        push: bool,
        errors: list[dict[str, str]],
    ) -> str:
        return push_url if push else fetch_url

    def forbidden_query(
        root: Path,
        effective_url: str,
        target_branch: str,
        errors: list[dict[str, str]],
    ) -> str:
        query_calls.append((effective_url, target_branch))
        return "1" * 40

    monkeypatch.setattr(module, "_single_remote_url", remote_url)
    monkeypatch.setattr(module, "_query_remote_tip", forbidden_query)
    errors: list[dict[str, str]] = []

    _, remote_tip = module._validate_live_remote(
        tmp_path,
        remote_name="origin",
        target_branch="main",
        expected_fetch_sha256=(
            expected_fetch or _sha256(fetch_url.encode("utf-8"))
        ),
        expected_push_sha256=(
            expected_push or _sha256(push_url.encode("utf-8"))
        ),
        errors=errors,
    )

    assert remote_tip is None
    assert errors
    assert query_calls == []


def test_unexpected_fifth_review_metadata_path_invalidates_final_review(
    authority_repo: dict[str, Any],
) -> None:
    metadata_root = (
        authority_repo["root"] / ".harness" / "reviews" / STAGE_ID / "implementation"
    )
    metadata_root.mkdir(parents=True)
    (metadata_root / "extra-metadata.json").write_text("{}\n", encoding="utf-8")

    report = _validate(
        authority_repo,
        required_action="merge",
        expected_candidate_head=authority_repo["baseline"],
    )

    _assert_fails_closed(report)


def test_exposed_reconciliation_keeps_query_failure_unknown(tmp_path: Path) -> None:
    module = _load_validator_module()
    helper = getattr(module, "reconcile_push_outcome", None)
    if helper is None:
        pytest.skip("push reconciliation is not exposed as a helper")

    endpoint = (tmp_path / "missing.git").as_uri()
    report = helper(
        project_root=tmp_path,
        effective_push_url=endpoint,
        expected_effective_push_url_sha256=_sha256(endpoint.encode("utf-8")),
        target_branch="main",
        expected_target_branch="main",
        candidate_head="2" * 40,
        authorized_old_tip="1" * 40,
    )

    assert report["code"] == "UNKNOWN_PUSH_OUTCOME"
    assert report["vcs_pushed"] == "unknown"
    assert report["retry_allowed"] is False


def test_reconciliation_binds_same_endpoint_ref_and_all_tip_states(
    tmp_path: Path,
) -> None:
    module = _load_validator_module()
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    source.mkdir()
    remote.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Reconciliation Tests")
    _git(source, "config", "user.email", "reconcile@example.invalid")
    tracked = source / "tracked.txt"
    commits = []
    for value in ("old", "candidate", "diverged"):
        tracked.write_text(f"{value}\n", encoding="utf-8")
        _git(source, "add", "tracked.txt")
        _git(source, "commit", "-m", value)
        commits.append(_git(source, "rev-parse", "HEAD"))
    old_tip, candidate, diverged = commits
    _git(remote, "init", "--bare")
    endpoint = remote.resolve().as_uri()
    endpoint_hash = _sha256(endpoint.encode("utf-8"))

    for remote_tip, expected_code in (
        (candidate, "PUSH_VERIFIED"),
        (old_tip, "PUSH_NOT_APPLIED"),
        (diverged, "REMOTE_TIP_DIVERGED"),
    ):
        _git(
            source,
            "push",
            "--force",
            endpoint,
            f"{remote_tip}:refs/heads/main",
        )
        report = module.reconcile_push_outcome(
            project_root=source,
            effective_push_url=endpoint,
            expected_effective_push_url_sha256=endpoint_hash,
            target_branch="main",
            expected_target_branch="main",
            candidate_head=candidate,
            authorized_old_tip=old_tip,
        )
        assert report["code"] == expected_code

    endpoint_mismatch = module.reconcile_push_outcome(
        project_root=source,
        effective_push_url=endpoint,
        expected_effective_push_url_sha256=ONE_SHA256,
        target_branch="main",
        expected_target_branch="main",
        candidate_head=candidate,
        authorized_old_tip=old_tip,
    )
    assert endpoint_mismatch["code"] == "UNKNOWN_PUSH_OUTCOME"

    _git(source, "push", endpoint, f"{candidate}:refs/heads/other")
    ref_mismatch = module.reconcile_push_outcome(
        project_root=source,
        effective_push_url=endpoint,
        expected_effective_push_url_sha256=endpoint_hash,
        target_branch="other",
        expected_target_branch="main",
        candidate_head=candidate,
        authorized_old_tip=old_tip,
    )
    assert ref_mismatch["code"] == "UNKNOWN_PUSH_OUTCOME"


def test_exposed_bounded_process_disables_prompts_and_shell(tmp_path: Path) -> None:
    module = _load_validator_module()
    helper = getattr(module, "run_bounded", None)
    if helper is None:
        pytest.skip("bounded process runner is not exposed as a helper")

    script = tmp_path / "print_env.py"
    script.write_text(
        "import os\n"
        "print(os.environ.get('GIT_TERMINAL_PROMPT'))\n"
        "print(os.environ.get('GCM_INTERACTIVE'))\n",
        encoding="utf-8",
    )
    report = helper(
        [sys.executable, str(script)],
        cwd=tmp_path,
        timeout_seconds=2,
        max_output_bytes=1024,
        mutation_capable=False,
        env={**os.environ},
    )

    assert report["status"] == "PASS"
    assert report["stdout"].splitlines() == ["0", "Never"]
    assert report["shell"] is False


def test_review_subject_manifest_is_exhaustive_stable_and_has_exact_exclusions(
    authority_repo: dict[str, Any],
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    metadata = root / ".harness" / "reviews" / STAGE_ID / "implementation"
    metadata.mkdir(parents=True)
    for name in (
        "reviewed-change-manifest.json",
        "reviewed-change.diff",
        "review-set.json",
    ):
        (metadata / name).write_text("tail\n", encoding="utf-8")
    delivery = root / ".harness" / "authority" / STAGE_ID / "delivery-binding.json"
    delivery.write_text("tail\n", encoding="utf-8")

    first = module.build_review_subject_manifest(
        project_root=root,
        stage_id=STAGE_ID,
        planning_base=authority_repo["baseline"],
    )
    second = module.build_review_subject_manifest(
        project_root=root,
        stage_id=STAGE_ID,
        planning_base=authority_repo["baseline"],
    )

    assert first == second
    assert first["status"] == "PASS"
    assert first["manifest"]["excluded_metadata_paths"] == [
        f".harness/authority/{STAGE_ID}/delivery-binding.json",
        f".harness/reviews/{STAGE_ID}/implementation/review-set.json",
        f".harness/reviews/{STAGE_ID}/implementation/reviewed-change-manifest.json",
        f".harness/reviews/{STAGE_ID}/implementation/reviewed-change.diff",
    ]
    paths = {item["path"] for item in first["manifest"]["changes"]}
    assert "src/app.py" in paths
    assert not paths.intersection(first["manifest"]["excluded_metadata_paths"])
    assert first["manifest"]["schema_version"] == "repopilot.reviewed_change_manifest/v2"
    assert all(
        item["mode"] in {"100644", "100755"}
        for item in first["manifest"]["changes"]
        if item["kind"] == "file"
    )


@pytest.mark.parametrize("bad_mode", [None, "100600", True, [], {}])
def test_cr_closeout_p1_012_manifest_modes_are_strict_and_structured(
    authority_repo: dict[str, Any],
    bad_mode: object,
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-f", "-A")
    manifest = json.loads(review["manifest_path"].read_text(encoding="utf-8"))
    file_item = next(
        item for item in manifest["changes"] if item["kind"] == "file"
    )
    if bad_mode is None:
        del file_item["mode"]
    else:
        file_item["mode"] = bad_mode
    with pytest.raises(TypeError):
        module.build_reviewed_inventory_bytes(manifest)
    _write_json(review["manifest_path"], manifest)
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )
    _assert_fails_closed(report)
    assert "REVIEW_MANIFEST_SCHEMA_INVALID" in {
        error["code"] for error in report["errors"]
    }


def test_cr_closeout_p1_012_deleted_manifest_entry_has_no_mode(
    authority_repo: dict[str, Any],
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    (root / "src" / "app.py").unlink()
    built = module.build_review_subject_manifest(
        project_root=root,
        stage_id=STAGE_ID,
        planning_base=authority_repo["baseline"],
    )
    deleted = next(
        item
        for item in built["manifest"]["changes"]
        if item["path"] == "src/app.py"
    )
    assert deleted == {"path": "src/app.py", "kind": "deleted"}
    inventory = module.build_reviewed_inventory_bytes(built["manifest"])
    assert b"DELETE\tsrc/app.py\n" in inventory


def test_cr_closeout_p2_013_non_mapping_manifest_change_is_structured_fail(
    authority_repo: dict[str, Any],
) -> None:
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-f", "-A")
    manifest = json.loads(review["manifest_path"].read_text(encoding="utf-8"))
    manifest["changes"][0] = []
    _write_json(review["manifest_path"], manifest)

    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    _assert_fails_closed(report)
    assert "REVIEW_MANIFEST_SCHEMA_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize("required_action", ["archive", "commit", "merge", "push"])
def test_cr_closeout_p2_013_invalid_manifest_is_safe_for_all_closeout_actions(
    authority_repo: dict[str, Any],
    required_action: str,
) -> None:
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    manifest = json.loads(review["manifest_path"].read_text(encoding="utf-8"))
    manifest["changes"] = [[]]
    _write_json(review["manifest_path"], manifest)

    report = _validate(
        authority_repo,
        required_action=required_action,
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    _assert_fails_closed(report)
    assert "REVIEW_MANIFEST_SCHEMA_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize(
    "bad_changes",
    [
        None,
        {},
        "files",
        True,
        [None],
        [[]],
        [{"path": [], "kind": "deleted"}],
        [{"path": "src/app.py", "kind": []}],
        [
            {
                "path": "src/app.py",
                "kind": "file",
                "mode": [],
                "sha256": ONE_SHA256,
            }
        ],
        [
            {
                "path": "src/app.py",
                "kind": "file",
                "mode": "100644",
                "sha256": [],
            }
        ],
        [
            {
                "path": "../escape.py",
                "kind": "file",
                "mode": "100644",
                "sha256": ONE_SHA256,
            }
        ],
        [
            {
                "path": "src/app.py",
                "kind": "file",
                "mode": "100644",
                "sha256": ONE_SHA256,
                "extra": "field",
            }
        ],
    ],
    ids=[
        "null-container",
        "object-container",
        "scalar-container",
        "bool-container",
        "null-item",
        "list-item",
        "list-path",
        "list-kind",
        "list-mode",
        "list-sha",
        "noncanonical-path",
        "extra-key",
    ],
)
def test_cr_closeout_p2_013_manifest_consumers_reject_malformed_changes(
    authority_repo: dict[str, Any],
    bad_changes: object,
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    manifest = json.loads(review["manifest_path"].read_text(encoding="utf-8"))
    manifest["changes"] = copy.deepcopy(bad_changes)

    with pytest.raises(TypeError):
        module.build_reviewed_inventory_bytes(manifest)
    _write_json(review["manifest_path"], manifest)
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    _assert_fails_closed(report)
    assert "REVIEW_MANIFEST_SCHEMA_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize("bad_manifest", [None, [], "manifest", True])
def test_cr_closeout_p2_013_direct_and_current_manifest_types_are_safe(
    authority_repo: dict[str, Any],
    bad_manifest: object,
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)

    with pytest.raises(TypeError):
        module.build_reviewed_inventory_bytes(bad_manifest)
    _write_json(review["manifest_path"], bad_manifest)
    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    _assert_fails_closed(report)
    assert "REVIEW_MANIFEST_INVALID" in {
        error["code"] for error in report["errors"]
    }


@pytest.mark.parametrize(
    "metadata_name",
    [
        "reviewed-change-manifest.json",
        "reviewed-change.diff",
        "review-set.json",
        "delivery-binding.json",
    ],
)
def test_cr_closeout_p1_014_metadata_mode_is_code_owned(
    authority_repo: dict[str, Any],
    metadata_name: str,
) -> None:
    root = authority_repo["root"]
    (root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    review = _write_implementation_review(authority_repo)
    delivery = _write_delivery_binding(authority_repo, review)
    _git(root, "add", "-f", "-A")
    metadata_path = (
        delivery
        if metadata_name == "delivery-binding.json"
        else review["manifest_path"].with_name(metadata_name)
    )
    relative = metadata_path.relative_to(root).as_posix()
    metadata_path.chmod(0o755)
    _git(root, "update-index", "--chmod=+x", relative)

    report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery,
    )

    _assert_fails_closed(report)
    assert "CANDIDATE_INDEX_MODE_MISMATCH" in {
        error["code"] for error in report["errors"]
    }


def test_review_subject_manifest_rejects_symlinked_subject(
    authority_repo: dict[str, Any],
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    (root / "src" / "linked.py").symlink_to(root / "docs" / "outside.md")

    report = module.build_review_subject_manifest(
        project_root=root,
        stage_id=STAGE_ID,
        planning_base=authority_repo["baseline"],
    )

    assert report["status"] == "FAIL"
    assert any(
        error["code"] == "MANIFEST_SYMLINK_FORBIDDEN"
        for error in report["errors"]
    )


def test_delivery_binding_validates_actual_files_and_rejects_hash_drift(
    authority_repo: dict[str, Any],
) -> None:
    module = _load_validator_module()
    root = authority_repo["root"]
    implementation = root / ".harness" / "reviews" / STAGE_ID / "implementation"
    implementation.mkdir(parents=True)
    manifest_path = implementation / "reviewed-change-manifest.json"
    diff_path = implementation / "reviewed-change.diff"
    review_set_path = implementation / "review-set.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    diff_path.write_text("bounded diff\n", encoding="utf-8")
    review_set_path.write_text("{}\n", encoding="utf-8")
    allowed_path = root / ".harness" / "allowed_files.md"
    checklist_path = root / ".harness" / "review_checklist.md"
    checklist_path.write_text("reviewed\n", encoding="utf-8")
    binding = {
        "schema_version": "repopilot.stage_delivery_binding/v1",
        "stage_id": STAGE_ID,
        "authority_epoch": 1,
        "authority_record_sha256": ONE_SHA256,
        "reviewed_manifest": {
            "path": manifest_path.relative_to(root).as_posix(),
            "sha256": _sha256(manifest_path.read_bytes()),
        },
        "reviewed_diff": {
            "path": diff_path.relative_to(root).as_posix(),
            "sha256": _sha256(diff_path.read_bytes()),
        },
        "implementation_review_set": {
            "path": review_set_path.relative_to(root).as_posix(),
            "sha256": _sha256(review_set_path.read_bytes()),
            "packet_sha256": ZERO_SHA256,
        },
        "final_harness_files": [
            {
                "path": ".harness/allowed_files.md",
                "sha256": _sha256(allowed_path.read_bytes()),
            },
            {
                "path": ".harness/review_checklist.md",
                "sha256": _sha256(checklist_path.read_bytes()),
            },
        ],
    }

    report = module.validate_delivery_binding(
        binding,
        project_root=root,
        expected_stage=STAGE_ID,
        expected_epoch=1,
        expected_authority_record_sha256=ONE_SHA256,
        expected_review_packet_sha256=ZERO_SHA256,
    )
    assert report["status"] == "PASS"

    diff_path.write_text("drift\n", encoding="utf-8")
    report = module.validate_delivery_binding(
        binding,
        project_root=root,
        expected_stage=STAGE_ID,
        expected_epoch=1,
        expected_authority_record_sha256=ONE_SHA256,
        expected_review_packet_sha256=ZERO_SHA256,
    )
    assert report["status"] == "FAIL"


def test_cr_closeout_p2_010_unhashable_final_harness_path_is_structured(
    authority_repo: dict[str, Any],
) -> None:
    module = _load_validator_module()
    review = _write_implementation_review(authority_repo)
    delivery_path = _write_delivery_binding(authority_repo, review)
    binding = json.loads(delivery_path.read_text(encoding="utf-8"))
    binding["final_harness_files"][0]["path"] = ["unhashable"]

    report = module.validate_delivery_binding(
        binding,
        project_root=authority_repo["root"],
        expected_stage=STAGE_ID,
        expected_epoch=1,
        expected_authority_record_sha256=_sha256(
            authority_repo["record_path"].read_bytes()
        ),
        expected_review_packet_sha256=review["packet_sha256"],
    )

    assert report["status"] == "FAIL"
    assert "FINAL_HARNESS_SET_INVALID" in {
        error["code"] for error in report["errors"]
    }
    assert "unhashable" not in json.dumps(report)

    _write_json(delivery_path, binding)
    commit_report = _validate(
        authority_repo,
        required_action="commit",
        **_review_inputs(review),
        delivery_binding=delivery_path,
    )
    _assert_fails_closed(commit_report)
    assert "DELIVERY_BINDING_INVALID" in {
        error["code"] for error in commit_report["errors"]
    }


@pytest.mark.parametrize(
    "binding_name",
    ["reviewed_manifest", "reviewed_diff", "implementation_review_set"],
)
def test_cr_closeout_p2_010_unhashable_delivery_artifact_paths_are_structured(
    authority_repo: dict[str, Any],
    binding_name: str,
) -> None:
    module = _load_validator_module()
    review = _write_implementation_review(authority_repo)
    delivery_path = _write_delivery_binding(authority_repo, review)
    binding = json.loads(delivery_path.read_text(encoding="utf-8"))
    binding[binding_name]["path"] = [["secret-token"]]
    report = module.validate_delivery_binding(
        binding,
        project_root=authority_repo["root"],
        expected_stage=STAGE_ID,
        expected_epoch=1,
        expected_authority_record_sha256=_sha256(
            authority_repo["record_path"].read_bytes()
        ),
        expected_review_packet_sha256=review["packet_sha256"],
    )
    assert report["status"] == "FAIL"
    assert "DELIVERY_PATH_INVALID" in {
        error["code"] for error in report["errors"]
    }
    assert "secret-token" not in json.dumps(report)


@pytest.mark.parametrize("mutation", ["not_list", "bad_elements", "unsorted"])
def test_cr_closeout_p2_010_final_harness_container_remains_exact(
    authority_repo: dict[str, Any],
    mutation: str,
) -> None:
    module = _load_validator_module()
    review = _write_implementation_review(authority_repo)
    delivery_path = _write_delivery_binding(authority_repo, review)
    binding = json.loads(delivery_path.read_text(encoding="utf-8"))
    if mutation == "not_list":
        binding["final_harness_files"] = {"path": ["secret-token"]}
    elif mutation == "bad_elements":
        binding["final_harness_files"] = [[], {}]
    else:
        binding["final_harness_files"].reverse()
    report = module.validate_delivery_binding(
        binding,
        project_root=authority_repo["root"],
        expected_stage=STAGE_ID,
        expected_epoch=1,
        expected_authority_record_sha256=_sha256(
            authority_repo["record_path"].read_bytes()
        ),
        expected_review_packet_sha256=review["packet_sha256"],
    )
    assert report["status"] == "FAIL"
    assert "FINAL_HARNESS_SET_INVALID" in {
        error["code"] for error in report["errors"]
    }
    assert "secret-token" not in json.dumps(report)


def test_exact_push_argv_binds_source_target_and_old_oid() -> None:
    module = _load_validator_module()

    argv = module.exact_push_argv(
        effective_push_url="ssh://example.invalid/repo.git",
        candidate_head="2" * 40,
        target_branch="main",
        authorized_old_tip="1" * 40,
    )

    assert argv == [
        "git",
        "push",
        "--porcelain",
        f"--force-with-lease=refs/heads/main:{'1' * 40}",
        "ssh://example.invalid/repo.git",
        f"{'2' * 40}:refs/heads/main",
    ]


def test_bounded_runner_requires_explicit_intent_and_rejects_unmarked_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_validator_module()
    argv = module.exact_push_argv(
        effective_push_url="ssh://example.invalid/repo.git",
        candidate_head="2" * 40,
        target_branch="main",
        authorized_old_tip="1" * 40,
    )

    with pytest.raises(TypeError):
        module.run_bounded(
            argv,
            cwd=tmp_path,
            timeout_seconds=1,
            max_output_bytes=1024,
        )

    popen_called = False

    def forbidden_popen(*args: object, **kwargs: object) -> None:
        nonlocal popen_called
        popen_called = True
        raise AssertionError("unmarked git push reached Popen")

    monkeypatch.setattr(module.subprocess, "Popen", forbidden_popen)
    report = module.run_bounded(
        argv,
        cwd=tmp_path,
        timeout_seconds=1,
        max_output_bytes=1024,
        mutation_capable=False,
    )

    assert report["status"] == "FAIL"
    assert report["code"] == "PROCESS_INTENT_MISMATCH"
    assert report["returncode"] is None
    assert popen_called is False


def test_bounded_runner_rejects_non_boolean_mutation_intent(tmp_path: Path) -> None:
    module = _load_validator_module()

    report = module.run_bounded(
        [sys.executable, "-c", "print('not launched')"],
        cwd=tmp_path,
        timeout_seconds=1,
        max_output_bytes=1024,
        mutation_capable="false",
    )

    assert report["status"] == "FAIL"
    assert report["code"] == "PROCESS_ARGUMENT_INVALID"


def test_bounded_runner_rejects_non_utf8_output(tmp_path: Path) -> None:
    module = _load_validator_module()

    report = module.run_bounded(
        [sys.executable, "-c", "import os; os.write(1, b'\\xff')"],
        cwd=tmp_path,
        timeout_seconds=1,
        max_output_bytes=1024,
        mutation_capable=False,
    )

    assert report["status"] == "FAIL"
    assert report["code"] == "PROCESS_OUTPUT_ENCODING_INVALID"
    assert report["stdout"] == ""
    assert report["stderr"] == ""


def test_exact_old_oid_lease_rejects_remote_race(tmp_path: Path) -> None:
    module = _load_validator_module()
    source = tmp_path / "source"
    remote = tmp_path / "remote.git"
    source.mkdir()
    remote.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Lease Tests")
    _git(source, "config", "user.email", "lease@example.invalid")
    tracked = source / "tracked.txt"
    commits = []
    for value in ("old", "candidate", "remote-race"):
        tracked.write_text(f"{value}\n", encoding="utf-8")
        _git(source, "add", "tracked.txt")
        _git(source, "commit", "-m", value)
        commits.append(_git(source, "rev-parse", "HEAD"))
    old_tip, candidate, raced_tip = commits
    _git(remote, "init", "--bare")
    endpoint = remote.resolve().as_uri()
    _git(source, "push", endpoint, f"{old_tip}:refs/heads/main")
    push_argv = module.exact_push_argv(
        effective_push_url=endpoint,
        candidate_head=candidate,
        target_branch="main",
        authorized_old_tip=old_tip,
    )
    _git(
        source,
        "push",
        "--force",
        endpoint,
        f"{raced_tip}:refs/heads/main",
    )

    push_report = subprocess.run(
        push_argv,
        cwd=source,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        shell=False,
        timeout=5,
        check=False,
    )
    reconcile = module.reconcile_push_outcome(
        project_root=source,
        effective_push_url=endpoint,
        expected_effective_push_url_sha256=_sha256(endpoint.encode("utf-8")),
        target_branch="main",
        expected_target_branch="main",
        candidate_head=candidate,
        authorized_old_tip=old_tip,
    )

    assert push_report.returncode != 0
    assert reconcile["code"] == "REMOTE_TIP_DIVERGED"


def test_started_bounded_process_failure_is_unknown(tmp_path: Path) -> None:
    module = _load_validator_module()
    script = tmp_path / "large.py"
    script.write_text("print('x' * 5000)\n", encoding="utf-8")

    report = module.run_bounded(
        [sys.executable, str(script)],
        cwd=tmp_path,
        timeout_seconds=2,
        max_output_bytes=128,
        mutation_capable=True,
    )

    if os.name == "nt":
        assert report["status"] == "UNKNOWN"
        assert report["code"] == "UNKNOWN_PUSH_OUTCOME"
    else:
        assert report["status"] == "FAIL"
        assert report["code"] == "PROCESS_ISOLATION_UNAVAILABLE"
        assert report["returncode"] is None


@pytest.mark.parametrize(
    ("script_text", "timeout_seconds", "max_output_bytes", "expected_code"),
    [
        ("import time\ntime.sleep(1)\n", 0.1, 1024, "PROCESS_TIMEOUT"),
        ("print('x' * 5000)\n", 2, 64, "PROCESS_OUTPUT_LIMIT"),
    ],
)
def test_bounded_process_failures_block_before_mutation(
    tmp_path: Path,
    script_text: str,
    timeout_seconds: float,
    max_output_bytes: int,
    expected_code: str,
) -> None:
    module = _load_validator_module()
    script = tmp_path / "bounded.py"
    script.write_text(script_text, encoding="utf-8")

    report = module.run_bounded(
        [sys.executable, str(script)],
        cwd=tmp_path,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
        mutation_capable=False,
    )

    assert report["status"] == "FAIL"
    assert report["code"] == expected_code
    assert report["returncode"] is not None


def test_bounded_process_never_returns_while_child_can_mutate(tmp_path: Path) -> None:
    module = _load_validator_module()
    marker = tmp_path / "late-marker.txt"
    script = tmp_path / "linger.py"
    script.write_text(
        "import os\n"
        "import sys\n"
        "import time\n"
        "os.close(sys.stdout.fileno())\n"
        "os.close(sys.stderr.fileno())\n"
        "time.sleep(1)\n"
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('late')\n",
        encoding="utf-8",
    )

    report = module.run_bounded(
        [sys.executable, str(script)],
        cwd=tmp_path,
        timeout_seconds=0.15,
        max_output_bytes=1024,
        mutation_capable=True,
    )
    time.sleep(0.25)

    if os.name == "nt":
        assert report["status"] == "UNKNOWN"
        assert report["returncode"] is not None
    else:
        assert report["status"] == "FAIL"
        assert report["code"] == "PROCESS_ISOLATION_UNAVAILABLE"
        assert report["returncode"] is None
    assert not marker.exists()


def test_bounded_process_terminates_descendant_tree_before_return(
    tmp_path: Path,
) -> None:
    module = _load_validator_module()
    marker = tmp_path / "descendant-marker.txt"
    child = tmp_path / "child.py"
    parent = tmp_path / "parent.py"
    child.write_text(
        "import time\n"
        "time.sleep(0.8)\n"
        f"open({str(marker)!r}, 'w', encoding='utf-8').write('late')\n",
        encoding="utf-8",
    )
    parent.write_text(
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        f"subprocess.Popen([sys.executable, {str(child)!r}], "
        "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, "
        "stderr=subprocess.DEVNULL)\n"
        "time.sleep(5)\n",
        encoding="utf-8",
    )

    report = module.run_bounded(
        [sys.executable, str(parent)],
        cwd=tmp_path,
        timeout_seconds=0.15,
        max_output_bytes=1024,
        mutation_capable=True,
    )
    time.sleep(1)

    if os.name == "nt":
        assert report["status"] == "UNKNOWN"
        assert report["returncode"] is not None
    else:
        assert report["status"] == "FAIL"
        assert report["code"] == "PROCESS_ISOLATION_UNAVAILABLE"
        assert report["returncode"] is None
    assert not marker.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX containment regression")
def test_mutating_runner_rejects_setsid_escape_before_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_validator_module()
    launched = tmp_path / "launched.txt"
    script = tmp_path / "escape.py"
    script.write_text(
        "import os\n"
        f"open({str(launched)!r}, 'w', encoding='utf-8').write('started')\n"
        "os.setsid()\n",
        encoding="utf-8",
    )
    popen_called = False

    def forbidden_popen(*args: object, **kwargs: object) -> None:
        nonlocal popen_called
        popen_called = True
        raise AssertionError("mutation-capable POSIX command reached Popen")

    monkeypatch.setattr(module.subprocess, "Popen", forbidden_popen)

    report = module.run_bounded(
        [sys.executable, str(script)],
        cwd=tmp_path,
        timeout_seconds=1,
        max_output_bytes=1024,
        mutation_capable=True,
    )

    assert report["status"] == "FAIL"
    assert report["code"] == "PROCESS_ISOLATION_UNAVAILABLE"
    assert report["returncode"] is None
    assert popen_called is False
    assert not launched.exists()


def test_windows_runner_uses_job_object_and_cross_platform_pipe_readers() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "scripts" / "validate_stage_authority.py"
    ).read_text(encoding="utf-8")

    assert "selectors." not in source
    assert "CreateJobObjectW" in source
    assert "AssignProcessToJobObject" in source
    assert "TerminateJobObject" in source
    assert "QueryInformationJobObject" in source
    assert "create_suspended" in source
    assert "_resume_windows_process" in source


def test_windows_pre_resume_isolation_failure_is_not_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_validator_module()

    class SuspendedProcess:
        stdout = object()
        stderr = object()
        pid = 12345
        returncode = -9

    monkeypatch.setattr(module, "_git_subcommand", lambda argv: None)
    monkeypatch.setattr(module.os, "name", "nt")
    monkeypatch.setattr(
        module.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200, raising=False
    )
    monkeypatch.setattr(
        module.subprocess,
        "Popen",
        lambda *args, **kwargs: SuspendedProcess(),
    )
    monkeypatch.setattr(module, "_create_windows_kill_job", lambda process: None)
    monkeypatch.setattr(
        module,
        "_terminate_process_tree",
        lambda process, *, windows_job=None: True,
    )

    report = module.run_bounded(
        ["mutation.exe"],
        cwd=tmp_path,
        timeout_seconds=1,
        max_output_bytes=1024,
        mutation_capable=True,
    )

    assert report["status"] == "FAIL"
    assert report["code"] == "PROCESS_ISOLATION_FAILED"
    assert report["returncode"] == -9


def test_all_apply_and_archive_entrypoints_consume_shared_gate() -> None:
    project_root = Path(__file__).resolve().parents[1]
    expected = {
        ".codex/skills/openspec-apply-change/SKILL.md": "implement",
        ".codex/skills/openspec-archive-change/SKILL.md": "archive",
        ".opencode/commands/opsx-apply.md": "implement",
        ".opencode/commands/opsx-archive.md": "archive",
        ".opencode/skills/openspec-apply-change/SKILL.md": "implement",
        ".opencode/skills/openspec-archive-change/SKILL.md": "archive",
    }

    for relative, action in expected.items():
        text = (project_root / relative).read_text(encoding="utf-8")
        assert "validate_stage_authority.py" in text
        assert f"--required-action {action}" in text
        assert "mechanical" in text.lower()


def test_all_apply_entrypoints_document_bound_plan_review_inputs() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        ".codex/skills/openspec-apply-change/SKILL.md",
        ".opencode/commands/opsx-apply.md",
        ".opencode/skills/openspec-apply-change/SKILL.md",
    )
    required_flags = (
        "--plan-review-set",
        "--required-plan-review-slots",
        "--expected-plan-review-packet-sha256",
    )

    command_contract = (project_root / ".harness/test_commands.md").read_text(
        encoding="utf-8"
    )
    for flag in required_flags:
        assert flag in command_contract, flag
    for relative in paths:
        text = (project_root / relative).read_text(encoding="utf-8")
        for flag in required_flags:
            assert flag in text, (relative, flag)


def test_zero_slot_rules_mark_reviewer_dispatch_not_applicable() -> None:
    project_root = Path(__file__).resolve().parents[1]
    for relative in (".harness/rules.md", "docs/AGENT_RULES.md"):
        text = (project_root / relative).read_text(encoding="utf-8")
        assert "positive-slot" in text, relative
        assert "NOT_APPLICABLE" in text, relative
        assert "activation sequence" in text, relative


def test_archive_entrypoints_gate_before_any_sync_mutation_instruction() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        ".codex/skills/openspec-archive-change/SKILL.md",
        ".opencode/commands/opsx-archive.md",
        ".opencode/skills/openspec-archive-change/SKILL.md",
    )

    for relative in paths:
        text = (project_root / relative).read_text(encoding="utf-8")
        gate = text.index("--required-action archive")
        sync_mutation = text.index("If user chooses sync")
        assert gate < sync_mutation, relative
        assert text.count("--required-action archive") >= 2, relative
        assert "sync mutation invalidates" in text.lower(), relative


def test_replay_activation_request_fails_without_external_host_capability(
    authority_repo: dict[str, Any],
) -> None:
    report = _validate(authority_repo, replay_activation_requested=True)
    assert report["status"] == "FAIL"
    assert "HOST_STATE_UNAVAILABLE" in {item["code"] for item in report["errors"]}


def test_dormant_replay_report_does_not_change_active_v1_authority(
    authority_repo: dict[str, Any],
) -> None:
    baseline = _validate(authority_repo)
    shadow = _validate(
        authority_repo,
        replay_report={
            "status": "PASS",
            "claim_level": "mechanical_consistency_only",
            "requested_action_ready": True,
        },
    )
    assert shadow == baseline


def _dormant_v2_fixture(module: Any) -> dict[str, object]:
    module = _load_validator_module()
    old_scope = {
        "risk": "high",
        "summary": "Superseded v1 envelope.",
        "allowed_path_rules": {"exact": ["docs/a.md"], "prefixes": ["tests/"]},
        "non_goals": ["activation"],
        "active_allowed_files_sha256": ZERO_SHA256,
    }
    v1 = {
        "schema_version": "repopilot.stage_authority/v1",
        "stage_id": "future-stage",
        "authority_epoch": 1,
        "supersedes_record_sha256": None,
        "authority_source": {"kind": "host_direct_user_instruction", "host_reference": "host:v1"},
        "scope": old_scope,
        "scope_sha256": _canonical_sha256(old_scope),
        "planning_baseline": {"commit": "1" * 40},
        "action_ceiling": "push",
        "vcs_target": {
            "remote_name": "origin", "effective_fetch_url_sha256": ZERO_SHA256,
            "effective_push_url_sha256": ZERO_SHA256, "target_branch": "main",
            "authorized_remote_tip": "1" * 40,
        },
    }
    scope = copy.deepcopy(old_scope)
    scope["summary"] = "Prospective dormant v2 mechanical contract."
    old_envelope = {
        key: v1[key]
        for key in ("stage_id", "scope", "planning_baseline", "action_ceiling", "vcs_target")
    }
    event = {
        "schema_version": "repopilot.stage_change_event/v1",
        "stage_id": "future-stage",
        "sequence": 1,
        "previous_event_sha256": None,
        "host_event_id": "host-event-v2-1",
        "event_kind": "direct_user_envelope_change",
        "source_reference": "host:future-stage:envelope-change",
        "authority_before": {"epoch": 1, "record_sha256": _canonical_sha256(v1)},
        "authority_requirement": {"later_epoch_required": True, "required_epoch": 2},
        "changed_fact_ids": ["scope"],
        "before_input_snapshot_sha256": _canonical_sha256(old_envelope),
        "observed_input_snapshot_sha256": "pending",
        "review_phase": None,
        "review_lineage": None,
        "classification_ceiling": "mechanical_consistency_only",
    }
    authority = {
        "schema_version": "repopilot.stage_authority/v2",
        "activation_status": "blocked_on_external_host_capability",
        "stage_id": "future-stage",
        "authority_epoch": 2,
        "supersedes_record_sha256": _canonical_sha256(v1),
        "authority_source": {"kind": "host_direct_user_instruction", "host_reference": "host:future-stage"},
        "trigger_change": {"event_count": 1, "event_head": "pending", "previous_authority_record_sha256": _canonical_sha256(v1), "required_later_epoch": 2},
        "scope": scope,
        "scope_sha256": _canonical_sha256(scope),
        "planning_baseline": {"commit": "1" * 40},
        "action_ceiling": "push",
        "vcs_target": {
            "remote_name": "origin", "effective_fetch_url_sha256": ZERO_SHA256,
            "effective_push_url_sha256": ZERO_SHA256, "target_branch": "main",
            "authorized_remote_tip": "1" * 40,
        },
        "claim_level": "mechanical_consistency_only",
    }
    new_envelope = {
        key: authority[key]
        for key in ("stage_id", "scope", "planning_baseline", "action_ceiling", "vcs_target")
    }
    event["observed_input_snapshot_sha256"] = _canonical_sha256(new_envelope)
    event["payload_sha256"] = _canonical_sha256(event)
    event_head = _canonical_sha256(event)
    authority["trigger_change"]["event_head"] = event_head
    authority_hash = _canonical_sha256(authority)
    receipt = {
        "schema_version": "repopilot.stage_replay_receipt/v1",
        "stage_id": "future-stage",
        "sequence": 1,
        "previous_receipt_sha256": None,
        "event_count": 1,
        "event_head": event_head,
        "graph_version": "repopilot.stage_gate_graph/v1",
        "host_snapshot_generation": 1,
        "authority": {"epoch": 2, "record_sha256": authority_hash},
        "completed_gate_ids": [],
        "gate_evidence": [],
        "invalidated_gate_ids": [
            "plan_contract", "plan_review", "authority", "implementation",
            "verification", "implementation_review", "archive",
            "post_archive_delivery_review", "candidate", "merge", "push",
        ],
        "preserved_gate_ids": [],
        "required_replay_gate_ids": [
            "plan_contract", "plan_review", "authority", "implementation",
            "verification", "implementation_review", "archive",
            "post_archive_delivery_review", "candidate", "merge", "push",
        ],
        "replay_frontier_gate_ids": ["plan_contract"],
        "claim_level": "mechanical_consistency_only",
    }
    receipt_head = _canonical_sha256(receipt)
    delivery = {
        "schema_version": "repopilot.stage_delivery_binding/v2",
        "activation_status": "blocked_on_external_host_capability",
        "stage_id": "future-stage",
        "authority_epoch": 2,
        "authority_record_sha256": authority_hash,
        "replay_state": {"event_count": 1, "event_head": event_head, "receipt_count": 1, "receipt_head": receipt_head},
        "final_review_packet": {"path": "reviews/final.json", "sha256": ZERO_SHA256},
        "pre_candidate": {
            "expected_parent_oid": "1" * 40,
            "review_packet_sha256": ZERO_SHA256,
            "reviewed_manifest_sha256": ZERO_SHA256,
            "reviewed_inventory_sha256": ZERO_SHA256,
            "review_metadata_and_tail_paths": module._review_metadata_paths("future-stage"),
            "construction_policy": "single_parent_exact_subject_plus_metadata/v1",
        },
        "claim_level": "mechanical_consistency_only",
    }
    return {
        "authority_record": authority,
        "delivery_binding": delivery,
        "superseded_v1_authority": v1,
        "trigger_event": event,
        "current_event_state": {
            "prior_count": 1, "prior_head": event_head,
            "current_count": 1, "current_head": event_head,
        },
        "current_receipt_state": {
            "prior_count": 1, "prior_head": receipt_head,
            "current_count": 1, "current_head": receipt_head,
        },
        "current_replay_receipt": receipt,
    }


def test_dormant_v2_interface_has_archive_before_commit_and_never_authorizes() -> None:
    module = _load_validator_module()
    fixture = _dormant_v2_fixture(module)
    report = module.validate_dormant_v2_interface(
        stage_cohort="v2",
        activation_requested=False,
        **fixture,
    )
    assert report["status"] == "PASS"
    assert report["action_order"] == ["plan", "implement", "archive", "commit", "merge", "push"]
    assert report["activation_status"] == "blocked_on_external_host_capability"
    assert report["mutation_authorized"] is False
    extra = copy.deepcopy(fixture["authority_record"])
    extra["unexpected"] = True
    strict_fixture = dict(fixture)
    strict_fixture["authority_record"] = extra
    strict = module.validate_dormant_v2_interface(
        stage_cohort="v2", activation_requested=False,
        **strict_fixture,
    )
    assert "V2_AUTHORITY_SCHEMA_INVALID" in {item["code"] for item in strict["errors"]}
    drifted_delivery = copy.deepcopy(fixture["delivery_binding"])
    drifted_delivery["stage_id"] = "other-stage"
    cross_fixture = dict(fixture)
    cross_fixture["delivery_binding"] = drifted_delivery
    cross = module.validate_dormant_v2_interface(
        stage_cohort="v2", activation_requested=False,
        **cross_fixture,
    )
    assert "V2_CROSS_BINDING_INVALID" in {item["code"] for item in cross["errors"]}


@pytest.mark.parametrize("mutation", ["event", "receipt", "undeclared_delta"])
def test_cr_b_005_dormant_v2_binds_old_new_event_and_receipt_lineage(
    mutation: str,
) -> None:
    module = _load_validator_module()
    fixture = _dormant_v2_fixture(module)
    if mutation == "event":
        fixture["trigger_event"]["source_reference"] = "host:other-event"
        expected = "V2_TRIGGER_EVENT_INVALID"
    elif mutation == "receipt":
        fixture["current_replay_receipt"]["event_head"] = ZERO_SHA256
        expected = "V2_RECEIPT_LINEAGE_INVALID"
    else:
        fixture["authority_record"]["action_ceiling"] = "merge"
        expected = "V2_ENVELOPE_DELTA_INVALID"
    report = module.validate_dormant_v2_interface(
        stage_cohort="v2",
        activation_requested=False,
        **fixture,
    )
    assert expected in {item["code"] for item in report["errors"]}


@pytest.mark.parametrize("cohort", ["v1", "caller-selected-v2", "unknown"])
def test_caller_cannot_select_v2_cohort(cohort: str) -> None:
    report = _load_validator_module().validate_dormant_v2_interface(
        stage_cohort=cohort,
        activation_requested=True,
        authority_record={},
        delivery_binding={},
    )
    assert report["status"] == "FAIL"
    assert report["mutation_authorized"] is False
    assert "HOST_STATE_UNAVAILABLE" in {item["code"] for item in report["errors"]}


def test_all_apply_archive_entrypoints_keep_replay_dormant_for_v1() -> None:
    root = Path(__file__).parents[1]
    paths = (
        ".codex/skills/openspec-apply-change/SKILL.md",
        ".codex/skills/openspec-archive-change/SKILL.md",
        ".opencode/commands/opsx-apply.md",
        ".opencode/commands/opsx-archive.md",
        ".opencode/skills/openspec-apply-change/SKILL.md",
        ".opencode/skills/openspec-archive-change/SKILL.md",
    )
    for relative in paths:
        text = (root / relative).read_text(encoding="utf-8")
        assert "provider_neutral.stage_state_cas/v1" in text, relative
        assert any(marker in text for marker in ("pre-change", "remain v1", "in-flight")), relative
        assert "v1" in text, relative
        assert "validate_stage_authority.py" in text, relative
