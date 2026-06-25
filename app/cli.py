from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


_PATCH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_SUPPORTED_VERIFY_LABELS = {"pytest", "ruff", "verify"}


class CliUsageError(ValueError):
    pass


class CliArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


def main(
    argv: Sequence[str] | None = None,
    *,
    service_factory: Callable[[], ChatService] = ChatService,
) -> int:
    out = sys.stdout
    err = sys.stderr
    try:
        request = _build_request(argv)
        response = service_factory().handle_chat(request)
        _print_response(response, out)
    except CliUsageError as exc:
        print(f"usage error: {exc}", file=err)
        return 2
    except Exception:
        print("CLI error: request failed", file=err)
        return 1
    return 0


def _build_request(argv: Sequence[str] | None) -> ChatRequest:
    namespace = _build_parser().parse_args(argv)
    _require_non_empty("repo", namespace.repo)
    _require_non_empty("user-id", namespace.user_id)
    _require_non_empty("session-id", namespace.session_id)
    message = _message_from_args(namespace)
    _require_non_empty("message", message)
    return ChatRequest(
        user_id=namespace.user_id,
        session_id=namespace.session_id,
        repo_path=namespace.repo,
        message=message,
    )


def _build_parser() -> CliArgumentParser:
    parser = CliArgumentParser(prog="repopilot")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--user-id", default="cli")
    parser.add_argument("--session-id", default="cli")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ask = subcommands.add_parser("ask")
    ask.add_argument("question")

    patch = subcommands.add_parser("patch")
    patch.add_argument("patch_args", nargs=argparse.REMAINDER)

    verify = subcommands.add_parser("verify")
    verify.add_argument("label_args", nargs=argparse.REMAINDER)

    subcommands.add_parser("status")

    audit = subcommands.add_parser("audit")
    audit.add_argument("audit_args", nargs=argparse.REMAINDER)

    return parser


def _message_from_args(namespace: argparse.Namespace) -> str:
    if namespace.command == "ask":
        return namespace.question
    if namespace.command == "patch":
        return _patch_message(namespace.patch_args)
    if namespace.command == "verify":
        return f"run {_validated_verify_label(namespace.label_args)}"
    if namespace.command == "status":
        return "assistant status"
    if namespace.command == "audit":
        return _audit_message(namespace.audit_args)
    raise CliUsageError("unsupported command")


def _patch_message(args: Sequence[str]) -> str:
    if not args:
        raise CliUsageError("patch requires a request or confirm command")

    if args[0] != "confirm":
        if len(args) != 1:
            raise CliUsageError("patch request must be provided as one argument")
        return args[0]

    if len(args) not in {2, 4}:
        raise CliUsageError("patch confirm requires a patch id and optional --verify label")

    patch_id = _validated_patch_id(args[1])
    if len(args) == 2:
        return f"confirm patch {patch_id}"

    if args[2] != "--verify":
        raise CliUsageError("patch confirm supports only --verify")
    label = _validated_verify_label([args[3]])
    return f"confirm patch {patch_id} and run {label}"


def _audit_message(args: Sequence[str]) -> str:
    if list(args) != ["latest"]:
        raise CliUsageError("audit supports only latest")
    return "audit latest"


def _validated_verify_label(args: Sequence[str]) -> str:
    if len(args) != 1 or args[0] not in _SUPPORTED_VERIFY_LABELS:
        raise CliUsageError("unsupported verification label")
    return args[0]


def _validated_patch_id(patch_id: str) -> str:
    if not _PATCH_ID_RE.fullmatch(patch_id):
        raise CliUsageError("unsupported patch id")
    return patch_id


def _require_non_empty(name: str, value: str) -> None:
    if not value:
        raise CliUsageError(f"{name} must not be empty")


def _print_response(response: ChatResponse, out: TextIO) -> None:
    print(f"trace_id: {response.trace_id}", file=out)
    print("answer:", file=out)
    print(response.answer, file=out)

    if response.related_files:
        print("related_files:", file=out)
        for path in response.related_files:
            print(f"- {path}", file=out)

    if response.tool_calls:
        print("tool_calls:", file=out)
        for call in response.tool_calls:
            summary = " ".join(f"{key}={value}" for key, value in call.items())
            print(f"- {summary}", file=out)


if __name__ == "__main__":
    raise SystemExit(main())
