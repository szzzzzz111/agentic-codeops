import copy
import hashlib
import json
from pathlib import Path

from scripts.validate_real_agent_observability import (
    NOT_OBSERVED,
    QUALIFIED_OBSERVABILITY,
    main,
    snapshot_sha256,
    validate_observation,
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot(*, clean: bool, content: str) -> dict[str, object]:
    return {
        "schema_version": "repopilot.git_snapshot/v1",
        "repository_id": _sha256("fixture-repository"),
        "head": "1" * 40,
        "status_sha256": _sha256("" if clean else " M result.txt\0"),
        "tracked_diff_sha256": _sha256("" if clean else content),
        "untracked_paths_sha256": _sha256(""),
        "clean": clean,
    }


def _valid_observation() -> dict[str, object]:
    completion = _snapshot(clean=False, content="OBSERVED\n")
    completion_sha256 = snapshot_sha256(completion)
    return {
        "schema_version": "repopilot.real_agent_observation/v1",
        "source": {
            "kind": "real_codex_cli",
            "provider": "codex",
            "provider_version": "codex-cli test",
            "invocation": ["codex", "exec", "--json", "--ephemeral"],
            "fixture_is_temporary": True,
        },
        "event_stream": [
            {"type": "thread.started", "thread_id": "thread-test"},
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "agent_message",
                    "text": "READY_FOR_REVIEW",
                },
            },
            {"type": "turn.completed", "usage": {"output_tokens": 4}},
        ],
        "baseline_snapshot": _snapshot(clean=True, content="PENDING\n"),
        "completion_snapshot": completion,
        "verification_receipt": {
            "schema_version": "repopilot.snapshot_verification_receipt/v1",
            "verification_command": [
                "python",
                "-I",
                "-m",
                "unittest",
                "-q",
            ],
            "exit_code": 0,
            "stdout_sha256": _sha256("OK\n"),
            "stderr_sha256": _sha256(""),
            "bound_snapshot_sha256": completion_sha256,
            "post_verification_snapshot": copy.deepcopy(completion),
        },
    }


def _error_codes(report: dict[str, object]) -> set[str]:
    return {error["code"] for error in report["errors"]}  # type: ignore[index]


def test_same_snapshot_real_observation_is_mechanically_qualified() -> None:
    observation = _valid_observation()
    report = validate_observation(observation)

    assert report["status"] == QUALIFIED_OBSERVABILITY
    assert report["errors"] == []
    assert report["completion_claim"] == "READY_FOR_REVIEW"
    assert report["post_verification_snapshot_sha256"] == snapshot_sha256(
        observation["completion_snapshot"]  # type: ignore[arg-type]
    )
    assert report["claim_level"] == "mechanical_observability_only"
    assert report["semantic_completion"] is False
    assert report["product_acceptance"] is False


def test_missing_terminal_event_fails_closed() -> None:
    observation = _valid_observation()
    observation["event_stream"] = observation["event_stream"][:-1]  # type: ignore[index]

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "TERMINAL_NOT_OBSERVED" in _error_codes(report)


def test_missing_completion_claim_fails_closed() -> None:
    observation = _valid_observation()
    observation["event_stream"][2]["item"]["text"] = "I changed the file"  # type: ignore[index]

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "COMPLETION_CLAIM_NOT_OBSERVED" in _error_codes(report)


def test_event_after_terminal_is_ambiguous_and_fails_closed() -> None:
    observation = _valid_observation()
    observation["event_stream"].append(  # type: ignore[union-attr]
        {"type": "item.completed", "item": {"type": "agent_message", "text": "late"}}
    )

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "EVENT_CHRONOLOGY_AMBIGUOUS" in _error_codes(report)


def test_dirty_fixture_baseline_fails_closed() -> None:
    observation = _valid_observation()
    observation["baseline_snapshot"] = _snapshot(
        clean=False,
        content="pre-existing change\n",
    )

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "BASELINE_NOT_CLEAN" in _error_codes(report)


def test_clean_flag_cannot_hide_a_nonempty_baseline_diff() -> None:
    observation = _valid_observation()
    observation["baseline_snapshot"]["tracked_diff_sha256"] = _sha256(  # type: ignore[index]
        "pre-existing diff"
    )

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "BASELINE_NOT_CLEAN" in _error_codes(report)


def test_untracked_inventory_is_rejected() -> None:
    observation = _valid_observation()
    observation["completion_snapshot"]["untracked_paths_sha256"] = _sha256(  # type: ignore[index]
        "new-file.txt\0"
    )

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "UNTRACKED_PATHS_NOT_ALLOWED" in _error_codes(report)


def test_nonzero_verification_fails_closed() -> None:
    observation = _valid_observation()
    observation["verification_receipt"]["exit_code"] = 7  # type: ignore[index]

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "VERIFICATION_FAILED" in _error_codes(report)


def test_receipt_bound_to_different_snapshot_fails_closed() -> None:
    observation = _valid_observation()
    observation["verification_receipt"]["post_verification_snapshot"][  # type: ignore[index]
        "tracked_diff_sha256"
    ] = "f" * 64

    report = validate_observation(observation)

    assert report["status"] == NOT_OBSERVED
    assert "SNAPSHOT_BINDING_MISMATCH" in _error_codes(report)


def test_cli_prints_report_and_returns_nonzero_for_not_observed(
    tmp_path: Path,
    capsys: object,
) -> None:
    observation = copy.deepcopy(_valid_observation())
    observation["event_stream"] = observation["event_stream"][:-1]  # type: ignore[index]
    input_path = tmp_path / "observation.json"
    input_path.write_text(json.dumps(observation), encoding="utf-8")

    assert main(["--input", str(input_path)]) == 1
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert json.loads(output)["status"] == NOT_OBSERVED
