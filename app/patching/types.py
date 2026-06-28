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
    lock_owner_token: str = ""
    lock_operation: str = ""

    def with_lock(self, *, owner_token: str, operation: str) -> "ToolInvocationContext":
        return ToolInvocationContext(
            tool_name=self.tool_name,
            user_id=self.user_id,
            repo_key=self.repo_key,
            intent=self.intent,
            command_label=self.command_label,
            patch_id=self.patch_id,
            worktree_id=self.worktree_id,
            confirmed=self.confirmed,
            patch_status=self.patch_status,
            diff_hash_match=self.diff_hash_match,
            expires_at_valid=self.expires_at_valid,
            scope_valid=self.scope_valid,
            promotion_preflight_valid=self.promotion_preflight_valid,
            lock_owner_token=owner_token,
            lock_operation=operation,
        )
