"""Validate a frozen real-Agent observation without launching or mutating it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

OBSERVATION_SCHEMA = "repopilot.real_agent_observation/v1"
SNAPSHOT_SCHEMA = "repopilot.git_snapshot/v1"
RECEIPT_SCHEMA = "repopilot.snapshot_verification_receipt/v1"
REPORT_SCHEMA = "repopilot.real_agent_observability_qualification/v1"
QUALIFIED_OBSERVABILITY = "QUALIFIED_OBSERVABILITY"
NOT_OBSERVED = "NOT_OBSERVED"
COMPLETION_CLAIM = "READY_FOR_REVIEW"

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_OID_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
TOP_LEVEL_FIELDS = {
    "schema_version",
    "source",
    "event_stream",
    "baseline_snapshot",
    "completion_snapshot",
    "verification_receipt",
}
SOURCE_FIELDS = {
    "kind",
    "provider",
    "provider_version",
    "invocation",
    "fixture_is_temporary",
}
SNAPSHOT_FIELDS = {
    "schema_version",
    "repository_id",
    "head",
    "status_sha256",
    "tracked_diff_sha256",
    "untracked_paths_sha256",
    "clean",
}
RECEIPT_FIELDS = {
    "schema_version",
    "verification_command",
    "exit_code",
    "stdout_sha256",
    "stderr_sha256",
    "bound_snapshot_sha256",
    "post_verification_snapshot",
}


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def snapshot_sha256(snapshot: Mapping[str, object]) -> str:
    """Return the canonical identity of a declared Git snapshot."""

    return _canonical_sha256(dict(snapshot))


def _error(
    errors: list[dict[str, str]],
    code: str,
    message: str,
    location: str,
) -> None:
    errors.append({"code": code, "message": message, "location": location})


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _validate_source(
    source: object,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(source, Mapping) or set(source) != SOURCE_FIELDS:
        _error(
            errors,
            "SOURCE_INVALID",
            "source must contain the exact real Codex CLI attestation fields",
            "$.source",
        )
        return
    invocation = source.get("invocation")
    if (
        source.get("kind") != "real_codex_cli"
        or source.get("provider") != "codex"
        or not isinstance(source.get("provider_version"), str)
        or not source.get("provider_version")
        or not isinstance(invocation, list)
        or not invocation
        or not all(isinstance(part, str) and part for part in invocation)
        or "--json" not in invocation
        or source.get("fixture_is_temporary") is not True
    ):
        _error(
            errors,
            "SOURCE_INVALID",
            "source must attest a temporary real codex exec --json invocation",
            "$.source",
        )


def _validate_event_stream(
    event_stream: object,
    errors: list[dict[str, str]],
) -> tuple[str | None, str | None]:
    if not isinstance(event_stream, list) or not event_stream:
        _error(
            errors,
            "EVENT_STREAM_INVALID",
            "event_stream must be a non-empty JSON event list",
            "$.event_stream",
        )
        return None, None
    if not all(
        isinstance(event, Mapping) and isinstance(event.get("type"), str)
        for event in event_stream
    ):
        _error(
            errors,
            "EVENT_STREAM_INVALID",
            "every event must be an object with a string type",
            "$.event_stream",
        )
        return None, _canonical_sha256(event_stream)

    thread_starts = [
        index
        for index, event in enumerate(event_stream)
        if event.get("type") == "thread.started"
    ]
    turn_starts = [
        index
        for index, event in enumerate(event_stream)
        if event.get("type") == "turn.started"
    ]
    terminals = [
        index
        for index, event in enumerate(event_stream)
        if event.get("type") == "turn.completed"
    ]
    failed_terminals = [
        index
        for index, event in enumerate(event_stream)
        if event.get("type") == "turn.failed"
    ]

    if len(terminals) == 0:
        _error(
            errors,
            "TERMINAL_NOT_OBSERVED",
            "exactly one turn.completed terminal event is required",
            "$.event_stream",
        )
    elif len(terminals) != 1:
        _error(
            errors,
            "EVENT_CHRONOLOGY_AMBIGUOUS",
            "multiple turn.completed events make the terminal state ambiguous",
            "$.event_stream",
        )
    if failed_terminals:
        _error(
            errors,
            "TERMINAL_FAILURE_OBSERVED",
            "turn.failed conflicts with a qualified completion",
            "$.event_stream",
        )
    if len(thread_starts) != 1 or len(turn_starts) != 1:
        _error(
            errors,
            "EVENT_CHRONOLOGY_AMBIGUOUS",
            "exactly one thread.started and one turn.started are required",
            "$.event_stream",
        )

    terminal_index = terminals[0] if len(terminals) == 1 else None
    if terminal_index is not None:
        if terminal_index != len(event_stream) - 1:
            _error(
                errors,
                "EVENT_CHRONOLOGY_AMBIGUOUS",
                "turn.completed must be the final event",
                "$.event_stream",
            )
        if (
            len(thread_starts) == 1
            and len(turn_starts) == 1
            and not (thread_starts[0] < turn_starts[0] < terminal_index)
        ):
            _error(
                errors,
                "EVENT_CHRONOLOGY_AMBIGUOUS",
                "thread, turn, and terminal events are out of order",
                "$.event_stream",
            )

    search_limit = terminal_index if terminal_index is not None else len(event_stream)
    agent_messages: list[str] = []
    for event in event_stream[:search_limit]:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, Mapping) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if isinstance(text, str):
            agent_messages.append(text)
    completion_claim = agent_messages[-1] if agent_messages else None
    if completion_claim != COMPLETION_CLAIM:
        _error(
            errors,
            "COMPLETION_CLAIM_NOT_OBSERVED",
            "the final Agent message before terminal must be READY_FOR_REVIEW",
            "$.event_stream",
        )

    return completion_claim, _canonical_sha256(event_stream)


def _validate_snapshot(
    snapshot: object,
    *,
    location: str,
    errors: list[dict[str, str]],
) -> Mapping[str, object] | None:
    if not isinstance(snapshot, Mapping) or set(snapshot) != SNAPSHOT_FIELDS:
        _error(
            errors,
            "SNAPSHOT_INVALID",
            "snapshot must contain the exact canonical Git snapshot fields",
            location,
        )
        return None
    valid = True
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA:
        valid = False
    if not _valid_sha256(snapshot.get("repository_id")):
        valid = False
    head = snapshot.get("head")
    if not isinstance(head, str) or GIT_OID_PATTERN.fullmatch(head) is None:
        valid = False
    if not _valid_sha256(snapshot.get("status_sha256")):
        valid = False
    if not _valid_sha256(snapshot.get("tracked_diff_sha256")):
        valid = False
    if not _valid_sha256(snapshot.get("untracked_paths_sha256")):
        valid = False
    if type(snapshot.get("clean")) is not bool:
        valid = False
    if not valid:
        _error(
            errors,
            "SNAPSHOT_INVALID",
            "snapshot contains invalid schema, identity, digest, HEAD, or clean fields",
            location,
        )
        return None
    if snapshot.get("untracked_paths_sha256") != EMPTY_SHA256:
        _error(
            errors,
            "UNTRACKED_PATHS_NOT_ALLOWED",
            "qualification snapshots must not contain untracked paths",
            location,
        )
    return snapshot


def _validate_receipt(
    receipt: object,
    *,
    completion_sha256: str | None,
    errors: list[dict[str, str]],
) -> str | None:
    if not isinstance(receipt, Mapping) or set(receipt) != RECEIPT_FIELDS:
        _error(
            errors,
            "VERIFICATION_RECEIPT_INVALID",
            "verification_receipt must contain the exact receipt fields",
            "$.verification_receipt",
        )
        return None
    command = receipt.get("verification_command")
    shape_valid = (
        receipt.get("schema_version") == RECEIPT_SCHEMA
        and isinstance(command, list)
        and bool(command)
        and all(isinstance(part, str) and part for part in command)
        and type(receipt.get("exit_code")) is int
        and _valid_sha256(receipt.get("stdout_sha256"))
        and _valid_sha256(receipt.get("stderr_sha256"))
        and _valid_sha256(receipt.get("bound_snapshot_sha256"))
    )
    if not shape_valid:
        _error(
            errors,
            "VERIFICATION_RECEIPT_INVALID",
            "verification receipt schema, command, exit code, or hashes are invalid",
            "$.verification_receipt",
        )
        return None
    post_snapshot = _validate_snapshot(
        receipt.get("post_verification_snapshot"),
        location="$.verification_receipt.post_verification_snapshot",
        errors=errors,
    )
    post_snapshot_sha256 = (
        snapshot_sha256(post_snapshot) if post_snapshot is not None else None
    )
    if receipt.get("exit_code") != 0:
        _error(
            errors,
            "VERIFICATION_FAILED",
            "verification command did not exit zero",
            "$.verification_receipt.exit_code",
        )
    if completion_sha256 is not None and (
        receipt.get("bound_snapshot_sha256") != completion_sha256
        or post_snapshot_sha256 != completion_sha256
    ):
        _error(
            errors,
            "SNAPSHOT_BINDING_MISMATCH",
            "receipt and post-verification state must bind the completion snapshot",
            "$.verification_receipt",
        )
    return post_snapshot_sha256


def validate_observation(observation: object) -> dict[str, Any]:
    """Return a fail-closed qualification report for one frozen observation."""

    errors: list[dict[str, str]] = []
    completion_claim: str | None = None
    event_stream_sha256: str | None = None
    completion_snapshot_sha256: str | None = None
    post_verification_snapshot_sha256: str | None = None

    if not isinstance(observation, Mapping) or set(observation) != TOP_LEVEL_FIELDS:
        _error(
            errors,
            "OBSERVATION_INVALID",
            "observation must contain the exact v1 top-level fields",
            "$",
        )
    elif observation.get("schema_version") != OBSERVATION_SCHEMA:
        _error(
            errors,
            "OBSERVATION_INVALID",
            "observation schema_version is unsupported",
            "$.schema_version",
        )
    else:
        _validate_source(observation.get("source"), errors)
        completion_claim, event_stream_sha256 = _validate_event_stream(
            observation.get("event_stream"),
            errors,
        )
        baseline = _validate_snapshot(
            observation.get("baseline_snapshot"),
            location="$.baseline_snapshot",
            errors=errors,
        )
        completion = _validate_snapshot(
            observation.get("completion_snapshot"),
            location="$.completion_snapshot",
            errors=errors,
        )
        if baseline is not None and (
            baseline.get("clean") is not True
            or baseline.get("status_sha256") != EMPTY_SHA256
            or baseline.get("tracked_diff_sha256") != EMPTY_SHA256
        ):
            _error(
                errors,
                "BASELINE_NOT_CLEAN",
                "fixture baseline must be consistently clean before the Agent runs",
                "$.baseline_snapshot",
            )
        if baseline is not None and completion is not None:
            completion_snapshot_sha256 = snapshot_sha256(completion)
            if (
                baseline.get("repository_id") != completion.get("repository_id")
                or baseline.get("head") != completion.get("head")
            ):
                _error(
                    errors,
                    "SNAPSHOT_LINEAGE_MISMATCH",
                    "baseline and completion snapshots must share repository and HEAD",
                    "$.completion_snapshot",
                )
            if (
                completion.get("clean") is not False
                or completion.get("status_sha256") == EMPTY_SHA256
                or completion.get("tracked_diff_sha256") == EMPTY_SHA256
                or snapshot_sha256(baseline) == completion_snapshot_sha256
            ):
                _error(
                    errors,
                    "AGENT_CHANGE_NOT_OBSERVED",
                    "completion snapshot must contain an Agent-produced change",
                    "$.completion_snapshot",
                )
        post_verification_snapshot_sha256 = _validate_receipt(
            observation.get("verification_receipt"),
            completion_sha256=completion_snapshot_sha256,
            errors=errors,
        )

    status = QUALIFIED_OBSERVABILITY if not errors else NOT_OBSERVED
    return {
        "schema_version": REPORT_SCHEMA,
        "status": status,
        "claim_level": "mechanical_observability_only",
        "real_source_attestation": "external_controller_evidence_required",
        "completion_claim": completion_claim,
        "event_stream_sha256": event_stream_sha256,
        "completion_snapshot_sha256": completion_snapshot_sha256,
        "post_verification_snapshot_sha256": (
            post_verification_snapshot_sha256
        ),
        "verification_snapshot_bound": status == QUALIFIED_OBSERVABILITY,
        "semantic_completion": False,
        "product_acceptance": False,
        "supervisor_runtime": False,
        "git_delivery": "not_authorized",
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a frozen real-Agent observability qualification",
    )
    parser.add_argument("--input", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        observation = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report = {
            "schema_version": REPORT_SCHEMA,
            "status": NOT_OBSERVED,
            "claim_level": "mechanical_observability_only",
            "real_source_attestation": "external_controller_evidence_required",
            "completion_claim": None,
            "event_stream_sha256": None,
            "completion_snapshot_sha256": None,
            "post_verification_snapshot_sha256": None,
            "verification_snapshot_bound": False,
            "semantic_completion": False,
            "product_acceptance": False,
            "supervisor_runtime": False,
            "git_delivery": "not_authorized",
            "errors": [
                {
                    "code": "INPUT_INVALID",
                    "message": str(exc),
                    "location": str(args.input),
                }
            ],
        }
    else:
        report = validate_observation(observation)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == QUALIFIED_OBSERVABILITY else 1


if __name__ == "__main__":
    raise SystemExit(main())
