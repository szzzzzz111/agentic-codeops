from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .contracts import AgentClaim, ClaimState, canonical_sha256

_READY = "READY_FOR_REVIEW"
_KNOWN_EVENT_TYPES = {
    "thread.started",
    "turn.started",
    "item.started",
    "item.completed",
    "turn.completed",
    "turn.failed",
}


def adapt_codex_events(
    *,
    run_id: str,
    events: Sequence[dict[str, Any]],
    stream_closed: bool,
    completion_snapshot_sha256: str | None = None,
) -> AgentClaim:
    event_list = list(events)
    try:
        digest = canonical_sha256(event_list)
    except (TypeError, ValueError):
        digest = canonical_sha256({"invalid_event_stream": True})
    thread_ids = [
        event.get("thread_id")
        for event in event_list
        if isinstance(event, dict) and event.get("type") == "thread.started"
    ]
    usable_thread_ids = [
        value
        for value in thread_ids
        if isinstance(value, str) and value and value == value.strip()
    ]
    thread_id = usable_thread_ids[0] if usable_thread_ids else "NOT_OBSERVED"

    def result(state: ClaimState, reason: str) -> AgentClaim:
        ready = state is ClaimState.READY_FOR_REVIEW
        return AgentClaim(
            provider="codex",
            run_id=run_id,
            thread_id=thread_id,
            stream_closed=stream_closed if isinstance(stream_closed, bool) else False,
            state=state,
            event_stream_sha256=digest,
            claim_text=_READY if ready else None,
            bound_snapshot_sha256=completion_snapshot_sha256 if ready else None,
            reason_codes=(reason,),
        )

    if not isinstance(stream_closed, bool) or not event_list:
        return result(ClaimState.INVALID, "EVENT_STREAM_INVALID")
    if any(
        not isinstance(event, dict)
        or not isinstance(event.get("type"), str)
        or event.get("type") not in _KNOWN_EVENT_TYPES
        for event in event_list
    ):
        return result(ClaimState.INVALID, "EVENT_STREAM_INVALID")
    if len(thread_ids) != 1 or len(usable_thread_ids) != 1:
        return result(ClaimState.INVALID, "THREAD_IDENTITY_AMBIGUOUS")

    thread_indexes = [i for i, event in enumerate(event_list) if event["type"] == "thread.started"]
    turn_indexes = [i for i, event in enumerate(event_list) if event["type"] == "turn.started"]
    terminal_indexes = [
        i
        for i, event in enumerate(event_list)
        if event["type"] in {"turn.completed", "turn.failed"}
    ]
    ready_indexes = [
        i
        for i, event in enumerate(event_list)
        if event["type"] == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
        and event["item"].get("text") == _READY
    ]
    agent_message_indexes = [
        i
        for i, event in enumerate(event_list)
        if event["type"] == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
    ]
    if (
        len(turn_indexes) != 1
        or thread_indexes[0] != 0
        or turn_indexes[0] != 1
    ):
        return result(ClaimState.INVALID, "EVENT_CHRONOLOGY_AMBIGUOUS")
    if len(ready_indexes) > 1:
        return result(ClaimState.INVALID, "COMPLETION_CLAIM_AMBIGUOUS")

    if not stream_closed:
        if terminal_indexes:
            return result(ClaimState.INVALID, "TERMINAL_ON_OPEN_STREAM")
        return result(ClaimState.PENDING, "AGENT_STREAM_PENDING")

    if not terminal_indexes:
        return result(ClaimState.NOT_OBSERVED, "TERMINAL_NOT_OBSERVED")
    if len(terminal_indexes) != 1 or terminal_indexes[0] != len(event_list) - 1:
        return result(ClaimState.INVALID, "EVENT_CHRONOLOGY_AMBIGUOUS")
    terminal_index = terminal_indexes[0]
    terminal_type = event_list[terminal_index]["type"]
    if terminal_type == "turn.failed":
        if ready_indexes:
            return result(ClaimState.INVALID, "READY_CLAIM_FOLLOWED_BY_FAILURE")
        return result(ClaimState.FAILED, "AGENT_TURN_FAILED")
    if not ready_indexes:
        return result(ClaimState.NOT_OBSERVED, "COMPLETION_CLAIM_NOT_OBSERVED")
    if not agent_message_indexes or agent_message_indexes[-1] != ready_indexes[0]:
        return result(ClaimState.INVALID, "COMPLETION_CLAIM_NOT_FINAL_AGENT_MESSAGE")
    if ready_indexes[0] <= turn_indexes[0] or ready_indexes[0] >= terminal_index:
        return result(ClaimState.INVALID, "EVENT_CHRONOLOGY_AMBIGUOUS")
    if completion_snapshot_sha256 is None:
        return result(ClaimState.INVALID, "COMPLETION_SNAPSHOT_NOT_OBSERVED")
    try:
        return result(ClaimState.READY_FOR_REVIEW, "READY_FOR_REVIEW")
    except ValueError:
        return result(ClaimState.INVALID, "COMPLETION_SNAPSHOT_INVALID")
