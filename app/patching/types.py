from dataclasses import dataclass


@dataclass(frozen=True)
class ToolInvocationContext:
    tool_name: str
    user_id: str = ""
    repo_key: str = ""
    intent: str = ""
    command_label: str = ""
    patch_id: str = ""
    worktree_id: str = ""
    confirmed: bool = False
    patch_status: str = ""
    diff_hash_match: bool = False
    expires_at_valid: bool = False
    scope_valid: bool = False
    promotion_preflight_valid: bool = False
