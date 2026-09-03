"""One-shot Codex App host-task bridge for the governed-run kernel.

The bridge never creates a Codex task and never starts a Codex/provider
process. A host controller creates one fresh task, proves its linked worktree
baseline, and supplies one bounded terminal observation. Repository output
therefore remains source-unverified even when the mechanical chain is ready
for human review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.supervision import (
    AgentClaim,
    ClaimState,
    DecisionOutcome,
    GitSnapshot,
    build_run_contract,
    build_verification_receipt,
    canonical_sha256,
    claim_sha256,
    collect_git_snapshot,
    evaluate_governed_run,
    snapshot_sha256,
)
from app.supervision.git_snapshot import GitSnapshotCollectionError
from app.verification.runner import (
    VerificationRunResult,
    run_whitelisted_verification,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_BASE_HEAD = "b7a8439fac9013f5ad59c308c4b16d333d466ddb"
BASE_README_SHA256 = (
    "70e242e898295dffaeb9a9723c5536edb96b5b6429e94fea274925a4a8b4e64e"
)
EXPECTED_README_SHA256 = (
    "d7844da1d65cabe3307959c6ac9a510e483bcdb99ad5070b280bdea0c33d575c"
)
BASE_README_FIRST_LINE = b"# RepoPilot\n"
EXPECTED_README_FIRST_LINE = b"# RepoPilot Agent Probe\n"
TARGET_PATH = "README.md"
ALLOWED_TRACKED_PATHS = (TARGET_PATH,)
VERIFICATION_LABEL = "ruff"
RUN_ID = "codex-app-one-shot-v1"
PROVIDER = "codex_app"
STATIC_PROMPT = (
    "Modify only README.md in this task worktree. Replace its first line "
    "exactly from '# RepoPilot' to '# RepoPilot Agent Probe'. Do not change "
    "any other bytes or path. Do not commit. When finished, reply with "
    "exactly READY_FOR_REVIEW and nothing else."
)
STATIC_PROMPT_SHA256 = canonical_sha256(STATIC_PROMPT)
OBSERVATION_SCHEMA = "repopilot.codex_app_task_observation/v1"
READY_SCHEMA = "repopilot.codex_app_bridge_ready/v1"
SUMMARY_SCHEMA = "repopilot.codex_app_one_shot_summary/v1"
MAX_OBSERVATION_BYTES = 4096
OBSERVATION_WAIT_TIMEOUT_SECONDS = 900.0
MAX_GIT_OUTPUT_BYTES = 64 * 1024
MAX_THREAD_ID_CHARS = 256


class ObservationFailure(RuntimeError):
    """Stable fail-closed reason from the host-task bridge."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ExperimentStatus(str, Enum):
    FAILED = "failed"
    NOT_OBSERVED = "not_observed"


@dataclass(frozen=True)
class HostTaskObservation:
    schema_version: str
    thread_id: str
    terminal_status: str
    final_text: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentSummary:
    status: ExperimentStatus
    deterministic_chain_passed: bool
    reason_codes: tuple[str, ...]
    decision_outcome: str
    decision_reason: str
    verification_status: str
    observation_sha256: str
    claim_sha256: str
    completion_snapshot_sha256: str
    post_snapshot_sha256: str
    receipt_sha256: str
    verification_result_sha256: str
    static_prompt_sha256: str = STATIC_PROMPT_SHA256
    source_provenance: str = "host_observed_unverified"
    host_task_observed: bool = False
    real_observation: bool = False
    task_complete: bool = False
    semantic_completion: bool = False
    human_review: str = "NOT_OBSERVED"
    product_acceptance: bool = False
    runtime_integration: bool = False
    git_delivery_authorized: bool = False
    snapshot_continuity: str = "stable_endpoint_samples_only"

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        if self.status is not ExperimentStatus.NOT_OBSERVED:
            raise ValueError("repository output cannot prove a real host experiment")
        if self.deterministic_chain_passed != (
            self.decision_outcome == DecisionOutcome.READY_FOR_REVIEW.value
            and self.decision_reason == "VERIFICATION_PASSED"
        ):
            raise ValueError("mechanical chain status does not match decision")
        if self.source_provenance != "host_observed_unverified":
            raise ValueError("host task source must remain unverified")
        if self.host_task_observed or self.real_observation:
            raise ValueError("repository input cannot self-prove a real host task")
        if any(
            (
                self.task_complete,
                self.semantic_completion,
                self.product_acceptance,
                self.runtime_integration,
                self.git_delivery_authorized,
            )
        ):
            raise ValueError("summary exceeds the experiment claim ceiling")
        if self.human_review != "NOT_OBSERVED":
            raise ValueError("human review was not observed")
        if self.snapshot_continuity != "stable_endpoint_samples_only":
            raise ValueError("snapshot continuity claim is too strong")

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["schema_version"] = SUMMARY_SCHEMA
        payload["status"] = self.status.value
        payload["reason_codes"] = list(self.reason_codes)
        return payload


@dataclass
class HostTaskBridge:
    repo: Path
    thread_id: str
    baseline_snapshot: GitSnapshot
    baseline_readme: bytes
    consumed: bool = False

    def ready_summary(self) -> dict[str, object]:
        return {
            "schema_version": READY_SCHEMA,
            "status": "BASELINE_READY",
            "thread_id_sha256": canonical_sha256(self.thread_id),
            "baseline_snapshot_sha256": snapshot_sha256(self.baseline_snapshot),
            "base_head": self.baseline_snapshot.head,
            "target_path": TARGET_PATH,
            "raw_path_persisted": False,
        }

    def consume(
        self,
        raw_observation: bytes,
        *,
        snapshot_collector: Callable[[str | Path], GitSnapshot] | None = None,
        verification_runner: (
            Callable[[str | Path, str], VerificationRunResult] | None
        ) = None,
    ) -> ExperimentSummary:
        if self.consumed:
            raise ObservationFailure("OBSERVATION_DUPLICATE")
        self.consumed = True
        observation = parse_host_task_observation(
            raw_observation,
            expected_thread_id=self.thread_id,
        )
        collector = snapshot_collector or collect_git_snapshot
        runner = verification_runner or run_whitelisted_verification
        completion = _collect_snapshot(collector, self.repo)
        _validate_completion(
            repo=self.repo,
            baseline=self.baseline_snapshot,
            completion=completion,
            baseline_readme=self.baseline_readme,
        )

        contract = build_run_contract(
            run_id=RUN_ID,
            baseline_snapshot=self.baseline_snapshot,
            allowed_tracked_paths=ALLOWED_TRACKED_PATHS,
            verification_label=VERIFICATION_LABEL,
        )
        observation_sha = canonical_sha256(observation.as_dict())
        completion_sha = snapshot_sha256(completion)
        claim = AgentClaim(
            provider=PROVIDER,
            run_id=RUN_ID,
            thread_id=self.thread_id,
            stream_closed=True,
            state=ClaimState.READY_FOR_REVIEW,
            event_stream_sha256=observation_sha,
            claim_text="READY_FOR_REVIEW",
            bound_snapshot_sha256=completion_sha,
            reason_codes=("HOST_TASK_TERMINAL_OBSERVED_UNVERIFIED",),
        )
        pre_receipt = evaluate_governed_run(
            contract,
            self.baseline_snapshot,
            completion,
            claim,
        )
        if (
            pre_receipt.outcome is not DecisionOutcome.NEEDS_HUMAN
            or pre_receipt.reason_codes != ("VERIFICATION_RECEIPT_MISSING",)
        ):
            raise ObservationFailure("PRE_RECEIPT_DECISION_INVALID")

        runner_before = _collect_snapshot(collector, self.repo)
        if snapshot_sha256(runner_before) != completion_sha:
            raise ObservationFailure("RUNNER_BEFORE_SNAPSHOT_DRIFT")
        with _forced_environment("RUFF_NO_CACHE", "true"):
            verification_result = runner(self.repo, VERIFICATION_LABEL)
        if (self.repo / ".ruff_cache").exists():
            raise ObservationFailure("VERIFIER_CACHE_WRITE")
        post_snapshot = _collect_snapshot(collector, self.repo)
        post_sha = snapshot_sha256(post_snapshot)
        if post_sha != completion_sha:
            raise ObservationFailure("POST_VERIFICATION_SNAPSHOT_DRIFT")

        receipt = build_verification_receipt(
            verification_result=verification_result,
            claim=claim,
            post_verification_snapshot=post_snapshot,
        )
        decision = evaluate_governed_run(
            contract,
            self.baseline_snapshot,
            completion,
            claim,
            receipt,
        )
        if (
            decision.outcome is not DecisionOutcome.READY_FOR_REVIEW
            or decision.reason_codes != ("VERIFICATION_PASSED",)
        ):
            raise ObservationFailure("VERIFICATION_CHAIN_NOT_READY")

        return ExperimentSummary(
            status=ExperimentStatus.NOT_OBSERVED,
            deterministic_chain_passed=True,
            reason_codes=("MECHANICAL_CHAIN_READY_HOST_SOURCE_UNVERIFIED",),
            decision_outcome=decision.outcome.value,
            decision_reason=decision.reason_codes[0],
            verification_status=verification_result.status,
            observation_sha256=observation_sha,
            claim_sha256=claim_sha256(claim),
            completion_snapshot_sha256=completion_sha,
            post_snapshot_sha256=post_sha,
            receipt_sha256=canonical_sha256(asdict(receipt)),
            verification_result_sha256=canonical_sha256(
                verification_result.audit_summary()
            ),
        )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def parse_host_task_observation(
    raw: bytes,
    *,
    expected_thread_id: str,
    max_bytes: int = MAX_OBSERVATION_BYTES,
) -> HostTaskObservation:
    if not isinstance(raw, bytes):
        raise ObservationFailure("OBSERVATION_TYPE_INVALID")
    if not raw:
        raise ObservationFailure("OBSERVATION_EMPTY")
    if max_bytes <= 0 or len(raw) > max_bytes:
        raise ObservationFailure("OBSERVATION_OUTPUT_LIMIT_EXCEEDED")
    if (
        not isinstance(expected_thread_id, str)
        or not expected_thread_id
        or len(expected_thread_id) > MAX_THREAD_ID_CHARS
        or any(marker in expected_thread_id for marker in ("\n", "\r"))
    ):
        raise ObservationFailure("EXPECTED_THREAD_ID_INVALID")
    body = raw[:-1] if raw.endswith(b"\n") else raw
    if not body or b"\n" in body or b"\r" in body or body.strip() != body:
        raise ObservationFailure("OBSERVATION_TRAILING_DATA")
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ObservationFailure("OBSERVATION_UTF8_INVALID") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant: {value}")
            ),
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ObservationFailure("OBSERVATION_JSON_INVALID") from exc
    expected_fields = {
        "schema_version",
        "thread_id",
        "terminal_status",
        "final_text",
    }
    if not isinstance(value, Mapping) or set(value) != expected_fields:
        raise ObservationFailure("OBSERVATION_SCHEMA_INVALID")
    if any(not isinstance(value[field], str) for field in expected_fields):
        raise ObservationFailure("OBSERVATION_FIELD_TYPE_INVALID")
    observation = HostTaskObservation(**dict(value))
    if observation.schema_version != OBSERVATION_SCHEMA:
        raise ObservationFailure("OBSERVATION_SCHEMA_INVALID")
    if observation.thread_id != expected_thread_id:
        raise ObservationFailure("OBSERVATION_THREAD_MISMATCH")
    if observation.terminal_status != "completed":
        raise ObservationFailure("OBSERVATION_TERMINAL_NOT_COMPLETED")
    if observation.final_text != "READY_FOR_REVIEW":
        raise ObservationFailure("OBSERVATION_FINAL_TEXT_MISMATCH")
    return observation


def assert_stage_readme_unchanged(stage_root: str | Path = PROJECT_ROOT) -> None:
    try:
        root = Path(stage_root).resolve(strict=True)
        readme = (root / TARGET_PATH).read_bytes()
    except OSError as exc:
        raise ObservationFailure("STAGE_README_UNAVAILABLE") from exc
    if _sha256_bytes(readme) != BASE_README_SHA256:
        raise ObservationFailure("STAGE_README_MUTATED")


def _registered_worktree_paths(repo: Path) -> tuple[Path, ...]:
    env = os.environ.copy()
    env.update(
        {
            "LC_ALL": "C",
            "LANG": "C",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
        }
    )
    try:
        completed = subprocess.run(
            ["git", "-C", os.fspath(repo), "worktree", "list", "--porcelain"],
            capture_output=True,
            timeout=10,
            check=False,
            shell=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ObservationFailure("WORKTREE_REGISTRATION_UNAVAILABLE") from exc
    if (
        completed.returncode != 0
        or len(completed.stdout) + len(completed.stderr) > MAX_GIT_OUTPUT_BYTES
    ):
        raise ObservationFailure("WORKTREE_REGISTRATION_UNAVAILABLE")
    paths: list[Path] = []
    for raw_record in completed.stdout.split(b"\n\n"):
        lines = raw_record.splitlines()
        if not lines:
            continue
        worktree_lines = [
            line for line in lines if line.startswith(b"worktree ")
        ]
        if len(worktree_lines) != 1:
            raise ObservationFailure("WORKTREE_REGISTRATION_INVALID")
        if any(
            line == b"prunable" or line.startswith(b"prunable ")
            for line in lines
        ):
            continue
        try:
            path = Path(
                worktree_lines[0][len(b"worktree ") :].decode(
                    "utf-8",
                    errors="strict",
                )
            ).resolve(strict=True)
        except (OSError, UnicodeDecodeError) as exc:
            raise ObservationFailure("WORKTREE_REGISTRATION_INVALID") from exc
        paths.append(path)
    if not paths or len(set(paths)) != len(paths):
        raise ObservationFailure("WORKTREE_REGISTRATION_INVALID")
    return tuple(paths)


def _collect_snapshot(
    collector: Callable[[str | Path], GitSnapshot],
    repo: Path,
) -> GitSnapshot:
    try:
        snapshot = collector(repo)
        snapshot.__post_init__()
    except (AttributeError, GitSnapshotCollectionError, OSError, TypeError, ValueError) as exc:
        raise ObservationFailure("SNAPSHOT_COLLECTION_FAILED") from exc
    return snapshot


def prepare_host_task(
    repo: str | Path,
    thread_id: str,
    *,
    expected_head: str = FROZEN_BASE_HEAD,
    stage_root: str | Path = PROJECT_ROOT,
    snapshot_collector: Callable[[str | Path], GitSnapshot] | None = None,
) -> HostTaskBridge:
    raw_repo = Path(repo)
    if not raw_repo.is_absolute():
        raise ObservationFailure("TASK_WORKTREE_PATH_NOT_ABSOLUTE")
    try:
        resolved_repo = raw_repo.resolve(strict=True)
        resolved_stage = Path(stage_root).resolve(strict=True)
    except OSError as exc:
        raise ObservationFailure("TASK_WORKTREE_UNAVAILABLE") from exc
    if not resolved_repo.is_dir() or raw_repo != resolved_repo:
        raise ObservationFailure("TASK_WORKTREE_PATH_NOT_CANONICAL")
    if resolved_repo == resolved_stage:
        raise ObservationFailure("TASK_WORKTREE_ROLE_COLLISION")
    if (
        not isinstance(thread_id, str)
        or not thread_id
        or len(thread_id) > MAX_THREAD_ID_CHARS
        or any(marker in thread_id for marker in ("\n", "\r"))
    ):
        raise ObservationFailure("EXPECTED_THREAD_ID_INVALID")
    if (
        not isinstance(expected_head, str)
        or len(expected_head) not in {40, 64}
        or any(character not in "0123456789abcdef" for character in expected_head)
    ):
        raise ObservationFailure("EXPECTED_HEAD_INVALID")

    assert_stage_readme_unchanged(resolved_stage)
    registered = _registered_worktree_paths(resolved_repo)
    if resolved_repo not in registered or resolved_repo == registered[0]:
        raise ObservationFailure("TASK_WORKTREE_ROLE_INVALID")
    if resolved_stage not in registered:
        raise ObservationFailure("BASELINE_REPOSITORY_MISMATCH")

    collector = snapshot_collector or collect_git_snapshot
    baseline = _collect_snapshot(collector, resolved_repo)
    if baseline.head != expected_head:
        raise ObservationFailure("BASELINE_HEAD_MISMATCH")
    if not baseline.clean:
        raise ObservationFailure("BASELINE_NOT_CLEAN")
    try:
        baseline_readme = (resolved_repo / TARGET_PATH).read_bytes()
    except OSError as exc:
        raise ObservationFailure("BASELINE_README_UNAVAILABLE") from exc
    if _sha256_bytes(baseline_readme) != BASE_README_SHA256:
        raise ObservationFailure("BASELINE_README_MISMATCH")
    return HostTaskBridge(
        repo=resolved_repo,
        thread_id=thread_id,
        baseline_snapshot=baseline,
        baseline_readme=baseline_readme,
    )


def _expected_readme_bytes(baseline: bytes) -> bytes:
    if not baseline.startswith(BASE_README_FIRST_LINE):
        raise ObservationFailure("BASELINE_README_MISMATCH")
    return EXPECTED_README_FIRST_LINE + baseline[len(BASE_README_FIRST_LINE) :]


def _validate_completion(
    *,
    repo: Path,
    baseline: GitSnapshot,
    completion: GitSnapshot,
    baseline_readme: bytes,
) -> None:
    if completion.repository_id != baseline.repository_id:
        raise ObservationFailure("COMPLETION_REPOSITORY_MISMATCH")
    if completion.head != baseline.head:
        raise ObservationFailure("COMPLETION_HEAD_MISMATCH")
    if completion.all_untracked_paths:
        raise ObservationFailure("COMPLETION_UNTRACKED_PATH")
    if completion.tracked_index_entries != baseline.tracked_index_entries:
        raise ObservationFailure("COMPLETION_INDEX_DRIFT")
    if completion.tracked_changed_paths != ALLOWED_TRACKED_PATHS:
        raise ObservationFailure("COMPLETION_SCOPE_MISMATCH")
    baseline_files = {
        item.path: item for item in baseline.tracked_worktree_files
    }
    completion_files = {
        item.path: item for item in completion.tracked_worktree_files
    }
    changed_raw = {
        path
        for path in baseline_files.keys() | completion_files.keys()
        if baseline_files.get(path) != completion_files.get(path)
    }
    if changed_raw != {TARGET_PATH}:
        raise ObservationFailure("COMPLETION_SCOPE_MISMATCH")
    try:
        current = (repo / TARGET_PATH).read_bytes()
    except OSError as exc:
        raise ObservationFailure("COMPLETION_README_UNAVAILABLE") from exc
    expected = _expected_readme_bytes(baseline_readme)
    if current != expected or _sha256_bytes(current) != EXPECTED_README_SHA256:
        raise ObservationFailure("COMPLETION_README_MISMATCH")


@contextmanager
def _forced_environment(name: str, value: str) -> Any:
    previous = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def _failure_payload(code: str) -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA,
        "status": ExperimentStatus.NOT_OBSERVED.value,
        "deterministic_chain_passed": False,
        "reason_codes": [code],
        "source_provenance": "host_observed_unverified",
        "host_task_observed": False,
        "real_observation": False,
        "task_complete": False,
        "semantic_completion": False,
        "human_review": "NOT_OBSERVED",
        "product_acceptance": False,
        "runtime_integration": False,
        "git_delivery_authorized": False,
        "snapshot_continuity": "stable_endpoint_samples_only",
    }


def _read_single_observation(
    *,
    timeout_seconds: float = OBSERVATION_WAIT_TIMEOUT_SECONDS,
) -> bytes:
    try:
        file_descriptor = sys.stdin.fileno()
        deadline = time.monotonic() + timeout_seconds
        chunks: list[bytes] = []
        size = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ObservationFailure("OBSERVATION_CHANNEL_TIMEOUT")
            readable, _, _ = select.select(
                [file_descriptor],
                [],
                [],
                remaining,
            )
            if not readable:
                raise ObservationFailure("OBSERVATION_CHANNEL_TIMEOUT")
            chunk = os.read(
                file_descriptor,
                min(4096, MAX_OBSERVATION_BYTES - size + 1),
            )
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_OBSERVATION_BYTES:
                raise ObservationFailure("OBSERVATION_OUTPUT_LIMIT_EXCEEDED")
    except ObservationFailure:
        raise
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        raise ObservationFailure("OBSERVATION_CHANNEL_INVALID") from exc
    raw = b"".join(chunks)
    if not raw:
        raise ObservationFailure("OBSERVATION_EMPTY")
    body = raw[:-1] if raw.endswith(b"\n") else raw
    if b"\n" in body or b"\r" in body:
        raise ObservationFailure("OBSERVATION_TRAILING_DATA")
    return raw


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-worktree", required=True)
    parser.add_argument("--thread-id", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        bridge = prepare_host_task(args.task_worktree, args.thread_id)
        print(
            json.dumps(
                bridge.ready_summary(),
                sort_keys=True,
                separators=(",", ":"),
            ),
            flush=True,
        )
        raw_observation = _read_single_observation()
        summary = bridge.consume(raw_observation)
    except ObservationFailure as exc:
        print(
            json.dumps(
                _failure_payload(exc.code),
                sort_keys=True,
                separators=(",", ":"),
            ),
            flush=True,
        )
        return 2
    print(
        json.dumps(summary.as_dict(), sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
