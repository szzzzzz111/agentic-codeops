import re


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


def parse_patch_confirmation(message: str) -> str | None:
    match = _PATCH_CONFIRM_RE.match(message)
    if match is None:
        return None
    return match.group(1)


def is_patch_proposal_request(message: str) -> bool:
    lower = message.lower()
    return any(term in lower or term in message for term in _PATCH_INTENT_TERMS)
