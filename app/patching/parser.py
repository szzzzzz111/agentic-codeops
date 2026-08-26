import re
from dataclasses import dataclass

from app.verification.runner import parse_verification_label

_PATCH_CONFIRM_RE = re.compile(
    r"^\s*(?:应用|确认|apply|confirm)\s+patch\s+"
    r"(patch_[A-Za-z0-9_]+)\s*$",
    re.IGNORECASE,
)
_PATCH_INTENT_TERMS = (
    "生成 patch",
    "生成补丁",
    "修改建议",
    "patch proposal",
    "make a patch",
    "create patch",
)
_PATCH_VERIFY_CONFIRM_PATTERNS = (
    re.compile(
        r"^\s*(?:应用|确认)\s+patch\s+"
        r"(?P<patch_id>patch_[A-Za-z0-9_]+)\s+"
        r"(?:并|并且|然后)?\s*(?:运行|执行|跑)\s*(?P<label>.*)\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:apply|confirm)\s+patch\s+"
        r"(?P<patch_id>patch_[A-Za-z0-9_]+)\s+"
        r"and\s+run\s*(?P<label>.*)\s*$",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class PatchVerifyConfirmation:
    handled: bool
    patch_id: str = ""
    command_label: str = ""
    rejected: bool = False
    reason: str = ""


def parse_patch_confirmation(message: str) -> str | None:
    match = _PATCH_CONFIRM_RE.match(message)
    if match is None:
        return None
    return match.group(1)


def parse_patch_verify_confirmation(message: str) -> PatchVerifyConfirmation:
    for pattern in _PATCH_VERIFY_CONFIRM_PATTERNS:
        match = pattern.match(message)
        if match is None:
            continue
        parsed_label = parse_verification_label(match.group("label"))
        if parsed_label.rejected or not parsed_label.command_label:
            return PatchVerifyConfirmation(
                handled=True,
                patch_id=match.group("patch_id"),
                rejected=True,
                reason=parsed_label.reason,
            )
        return PatchVerifyConfirmation(
            handled=True,
            patch_id=match.group("patch_id"),
            command_label=parsed_label.command_label,
        )
    return PatchVerifyConfirmation(handled=False)


def is_patch_proposal_request(message: str) -> bool:
    lower = message.lower()
    return any(term in lower or term in message for term in _PATCH_INTENT_TERMS)
