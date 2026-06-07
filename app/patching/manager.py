from dataclasses import dataclass
from datetime import UTC, datetime
import re

from app.patching.apply import PatchApplyResult, preflight_unified_diff
from app.patching.parser import is_patch_proposal_request, parse_patch_confirmation
from app.patching.provider import (
    FakePatchAuthoringProvider,
    PatchAuthoringProvider,
    PatchAuthoringProviderRequest,
)
from app.patching.store import (
    PATCH_STATUS_APPLIED,
    PATCH_STATUS_APPLIED_IN_WORKTREE,
    PATCH_STATUS_EXPIRED,
    PATCH_STATUS_FAILED,
    PATCH_STATUS_PENDING,
    PendingPatch,
    hash_diff,
    store_for_existing_repo,
)
from app.patching.types import ToolInvocationContext
from app.rag.evidence import EvidencePack


_WINDOWS_ABSOLUTE_PATH_RE = re.compile(
    r"\b[A-Za-z]:[\\/][^\s，。；;]+(?:[\\/][^\s，。；;]+)*"
)
_POSIX_LOCAL_ABSOLUTE_PATH_RE = re.compile(
    r"(?<![\w.])/(?:Users|home|root|tmp|var|etc|opt|mnt|srv)/[^\s，。；;]+"
)


@dataclass(frozen=True)
class PatchCommandResult:
    handled: bool
    answer: str = ""
    patch_id: str | None = None
    diff_text: str = ""
    context: ToolInvocationContext | None = None
    audit_summary: str = ""


class PatchManager:
    def __init__(self, provider: PatchAuthoringProvider | None = None) -> None:
        self.provider = provider or FakePatchAuthoringProvider()

    def is_patch_proposal_request(self, message: str) -> bool:
        return is_patch_proposal_request(message)

    def parse_confirmation(self, message: str) -> str | None:
        return parse_patch_confirmation(message)

    def propose_patch(
        self,
        *,
        user_id: str,
        repo_path: str,
        message: str,
        evidence_pack: EvidencePack | None,
    ) -> PatchCommandResult:
        if evidence_pack is None:
            return PatchCommandResult(
                handled=True,
                answer="无法生成可应用 patch：缺少仓库证据。",
                audit_summary="patch_status=fallback; reason=no_evidence",
            )
        evidence = [
            {
                "file_path": item.file_path,
                "start_line": item.start_line,
                "end_line": item.end_line,
                "snippet": item.snippet,
            }
            for item in evidence_pack.items
            if item.included and item.snippet
        ]
        provider_response = self.provider.generate_patch(
            PatchAuthoringProviderRequest(
                original_query=message,
                question_type=evidence_pack.question_type,
                evidence=evidence,
            )
        )
        if not provider_response.diff_text:
            return PatchCommandResult(
                handled=True,
                answer="无法生成可应用 patch：当前 provider 未返回可校验 diff。",
                audit_summary="patch_status=fallback; reason=no_diff",
            )
        valid, reason = _validate_provider_response(
            provider_response,
            evidence_pack,
            repo_path=repo_path,
        )
        if not valid:
            return PatchCommandResult(
                handled=True,
                answer="无法生成可应用 patch：provider 输出未通过校验。",
                audit_summary=f"patch_status=fallback; reason={reason}",
            )
        try:
            store, repo_key = store_for_existing_repo(repo_path)
            patch = store.create_pending_patch(
                user_id=user_id,
                repo_key=repo_key,
                target_files=provider_response.target_files,
                diff_text=provider_response.diff_text,
                summary=provider_response.summary,
            )
        except (OSError, ValueError):
            return PatchCommandResult(
                handled=True,
                answer="无法生成可应用 patch：patch 存储不可用。",
                audit_summary="patch_status=error; reason=store_unavailable",
            )
        safe_summary = _redact_public_patch_text(patch.summary)
        target_files = ", ".join(patch.target_files)
        return PatchCommandResult(
            handled=True,
            answer=(
                f"已生成 patch proposal：{safe_summary}。"
                f"目标文件：{target_files}。"
                f"patch_id={patch.patch_id}。"
                f"如需应用，请发送：确认 patch {patch.patch_id}"
            ),
            patch_id=patch.patch_id,
            audit_summary="patch_status=pending; target_count="
            f"{len(patch.target_files)}",
        )

    def prepare_apply(
        self,
        *,
        user_id: str,
        repo_path: str,
        message: str,
    ) -> PatchCommandResult:
        patch_id = parse_patch_confirmation(message)
        if patch_id is None:
            return PatchCommandResult(handled=False)
        try:
            store, repo_key = store_for_existing_repo(repo_path)
        except (OSError, ValueError):
            return PatchCommandResult(
                handled=True,
                answer="未找到可应用的 patch。",
                audit_summary="patch_status=missing; reason=store_unavailable",
            )
        patch = store.get_patch(patch_id, user_id=user_id, repo_key=repo_key)
        if patch is None:
            return PatchCommandResult(
                handled=True,
                answer="未找到可应用的 patch。",
                audit_summary="patch_status=missing",
            )
        context = _context_for_patch(user_id=user_id, repo_key=repo_key, patch=patch)
        if not context.expires_at_valid:
            store.mark_status(patch.patch_id, PATCH_STATUS_EXPIRED)
            return PatchCommandResult(
                handled=True,
                answer="该 patch 已过期，未应用任何文件。",
                patch_id=patch.patch_id,
                context=context,
                audit_summary="patch_status=expired",
            )
        if not context.scope_valid or patch.status != PATCH_STATUS_PENDING:
            return PatchCommandResult(
                handled=True,
                answer="该 patch 当前不可应用，未修改任何文件。",
                patch_id=patch.patch_id,
                context=context,
                audit_summary=f"patch_status={patch.status}",
            )
        return PatchCommandResult(
            handled=True,
            answer="",
            patch_id=patch.patch_id,
            diff_text=patch.diff_text,
            context=context,
            audit_summary="patch_status=ready",
        )

    def complete_apply(
        self,
        *,
        repo_path: str,
        user_id: str,
        patch_id: str,
        result: PatchApplyResult,
        worktree_id: str = "",
    ) -> PatchCommandResult:
        try:
            store, repo_key = store_for_existing_repo(repo_path)
            patch = store.get_patch(patch_id, user_id=user_id, repo_key=repo_key)
            if patch is None:
                return PatchCommandResult(
                    handled=True,
                    answer="patch apply 已执行，但状态更新失败。",
                    audit_summary="patch_status=missing_after_apply",
                )
            if result.applied:
                status = (
                    PATCH_STATUS_APPLIED_IN_WORKTREE
                    if worktree_id
                    else PATCH_STATUS_APPLIED
                )
            else:
                status = PATCH_STATUS_FAILED
            store.mark_status(patch.patch_id, status)
        except (OSError, ValueError):
            return PatchCommandResult(
                handled=True,
                answer="patch apply 已执行，但状态存储不可用。",
                audit_summary="patch_status=store_unavailable",
            )

        if result.applied:
            changed_files = ", ".join(result.changed_files)
            if worktree_id:
                return PatchCommandResult(
                    handled=True,
                    answer=(
                        f"已应用 patch {patch_id} 于隔离 worktree。"
                        f"worktree_id={worktree_id}。"
                        f"修改文件：{changed_files}。"
                    ),
                    audit_summary=(
                        "patch_status=applied_in_worktree; "
                        f"patch_id={patch_id}; worktree_id={worktree_id}; "
                        f"changed_files={len(result.changed_files)}"
                    ),
                )
            return PatchCommandResult(
                handled=True,
                answer=(
                    f"已应用 patch {patch_id}。"
                    f"修改文件：{changed_files}。"
                ),
                audit_summary=f"patch_status=applied; changed_files={len(result.changed_files)}",
            )

        return PatchCommandResult(
            handled=True,
            answer=f"patch {patch_id} 应用失败，未静默成功。",
            audit_summary=f"patch_status=failed; error={result.error}",
        )


def _redact_public_patch_text(value: str) -> str:
    redacted = _WINDOWS_ABSOLUTE_PATH_RE.sub("[redacted-path]", value)
    return _POSIX_LOCAL_ABSOLUTE_PATH_RE.sub("[redacted-path]", redacted)


def _context_for_patch(
    *,
    user_id: str,
    repo_key: str,
    patch: PendingPatch,
) -> ToolInvocationContext:
    diff_hash_match = hash_diff(patch.diff_text) == patch.diff_hash
    expires_at_valid = patch.expires_at > datetime.now(tz=UTC)
    scope_valid = patch.user_id == user_id and patch.repo_key == repo_key
    return ToolInvocationContext(
        tool_name="patch_apply",
        user_id=user_id,
        repo_key=repo_key,
        intent="patch_apply",
        patch_id=patch.patch_id,
        confirmed=True,
        patch_status=patch.status,
        diff_hash_match=diff_hash_match,
        expires_at_valid=expires_at_valid,
        scope_valid=scope_valid,
    )


def _validate_provider_response(
    provider_response,
    evidence_pack: EvidencePack,
    *,
    repo_path: str,
) -> tuple[bool, str]:
    if not provider_response.summary:
        return False, "missing_summary"
    if not provider_response.target_files:
        return False, "missing_target_files"
    if not provider_response.diff_text:
        return False, "missing_diff"
    allowed_citations = {
        f"{item.file_path}:{item.start_line}-{item.end_line}"
        for item in evidence_pack.items
        if item.included and item.snippet
    }
    if not provider_response.citations:
        return False, "missing_citation"
    if any(citation not in allowed_citations for citation in provider_response.citations):
        return False, "invalid_citation"
    preflight = preflight_unified_diff(repo_path, provider_response.diff_text)
    if not preflight.applied:
        return False, preflight.error or "invalid_diff"
    if sorted(preflight.changed_files) != sorted(provider_response.target_files):
        return False, "target_files_mismatch"
    return True, "ok"
