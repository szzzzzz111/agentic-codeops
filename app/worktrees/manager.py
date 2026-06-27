from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import shutil
import sqlite3
import subprocess
from uuid import uuid4

from app.worktrees.inspection import WorktreeInspectionResult, inspect_worktree
from app.worktrees.disposal import (
    WorktreeDisposalPreflight,
    WorktreeDisposalResult,
    dispose_worktree,
    preflight_worktree_disposal,
)
from app.worktrees.reverification import (
    WorktreeReverificationPreflight,
    preflight_worktree_reverification,
)
from app.worktrees.promotion import (
    VerifiedPatchPromotionCompletion,
    VerifiedPatchPromotionPreflight,
    begin_verified_patch_promotion,
    complete_verified_patch_promotion,
    mark_verified_patch_promotion_apply_failed,
    preflight_verified_patch_promotion,
)
from app.worktrees.store import (
    WORKTREE_STATUS_CREATE_FAILED,
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_PATCH_FAILED,
    WORKTREE_STATUS_READY,
    WORKTREE_STATUS_VERIFICATION_FAILED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
    SQLiteWorktreeStore,
    WorktreeRecord,
)


@dataclass(frozen=True)
class WorktreeCreateResult:
    created: bool
    status: str
    reason: str = ""
    worktree_id: str = ""
    execution_repo_path: str = ""
    base_commit: str = ""
    public_summary: str = ""


@dataclass(frozen=True)
class WorktreeInventoryResult:
    store_present: bool
    records: list[WorktreeRecord]


class WorktreeManager:
    def prepare_promotion(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
    ) -> VerifiedPatchPromotionPreflight:
        return preflight_verified_patch_promotion(
            repo_path=repo_path,
            user_id=user_id,
            worktree_id=worktree_id,
        )

    def begin_promotion(self, preflight: VerifiedPatchPromotionPreflight) -> bool:
        return begin_verified_patch_promotion(preflight)

    def complete_promotion(
        self,
        preflight: VerifiedPatchPromotionPreflight,
    ) -> VerifiedPatchPromotionCompletion:
        return complete_verified_patch_promotion(preflight)

    def mark_promotion_apply_failed(
        self,
        preflight: VerifiedPatchPromotionPreflight,
    ) -> None:
        mark_verified_patch_promotion_apply_failed(preflight)

    def prepare_disposal(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
        attempt_kind: str,
    ) -> WorktreeDisposalPreflight:
        return preflight_worktree_disposal(
            repo_path=repo_path,
            user_id=user_id,
            worktree_id=worktree_id,
            attempt_kind=attempt_kind,
        )

    def dispose(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
        attempt_kind: str,
    ) -> WorktreeDisposalResult:
        return dispose_worktree(
            repo_path=repo_path,
            user_id=user_id,
            worktree_id=worktree_id,
            attempt_kind=attempt_kind,
        )

    def create(
        self,
        *,
        repo_path: str,
        user_id: str,
        patch_id: str,
    ) -> WorktreeCreateResult:
        repo_root = Path(repo_path)
        worktree_registered = False
        if not repo_root.exists() or not repo_root.is_dir():
            return WorktreeCreateResult(
                created=False,
                status=WORKTREE_STATUS_CREATE_FAILED,
                reason="repo_unavailable",
                public_summary="worktree 创建失败：仓库不可用。",
            )
        try:
            resolved_repo = repo_root.resolve(strict=True)
            if not _is_git_repo(resolved_repo):
                return _failed("not_git_repo", "worktree 创建失败：当前目录不是 Git 仓库。")
            if _is_bare_repo(resolved_repo):
                return _failed("bare_repo", "worktree 创建失败：不支持 bare 仓库。")
            if not _is_git_work_tree(resolved_repo):
                return _failed("not_git_worktree", "worktree 创建失败：当前目录不是 Git 工作树。")
            try:
                base_commit = _git_stdout("rev-parse", "HEAD", cwd=resolved_repo).strip()
            except subprocess.SubprocessError:
                return _failed("missing_head", "worktree 创建失败：仓库没有有效 HEAD。")
            if not _is_repopilot_ignored(resolved_repo):
                return _failed(
                    "repopilot_not_ignored",
                    "worktree 创建失败：`.repopilot/` 必须先被 Git ignore。",
                )
            if _workspace_status(resolved_repo):
                return _failed(
                    "workspace_not_clean",
                    "worktree 创建失败：主工作区必须干净后才能创建隔离 worktree。",
                )

            worktree_id = _new_worktree_id()
            execution_path = resolved_repo / ".repopilot" / "worktrees" / worktree_id
            execution_path.parent.mkdir(parents=True, exist_ok=True)
            _git(
                "worktree",
                "add",
                "--detach",
                "--lock",
                "--reason",
                "RepoPilot V20 worktree isolation",
                str(execution_path),
                "HEAD",
                cwd=resolved_repo,
            )
            worktree_registered = True
            store, repo_key = SQLiteWorktreeStore.for_repo(resolved_repo)
            store.create_worktree(
                user_id=user_id,
                repo_key=repo_key,
                worktree_id=worktree_id,
                patch_id=patch_id,
                base_commit=base_commit,
                status=WORKTREE_STATUS_READY,
            )
        except (OSError, sqlite3.Error, subprocess.SubprocessError, ValueError):
            if worktree_registered:
                self._rollback_worktree(repo_root, locals().get("execution_path"))
            return _failed(
                "create_failed",
                "worktree 创建失败：未生成可用的隔离工作区。",
            )

        return WorktreeCreateResult(
            created=True,
            status=WORKTREE_STATUS_READY,
            worktree_id=worktree_id,
            execution_repo_path=str(execution_path),
            base_commit=base_commit,
            public_summary=(
                f"已创建隔离 worktree：worktree_id={worktree_id}；"
                f"base_commit={base_commit[:12]}"
            ),
        )

    def get_status(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
    ) -> WorktreeRecord | None:
        try:
            existing = SQLiteWorktreeStore.for_existing_repo(repo_path)
            if existing is None:
                return None
            store, repo_key = existing
            return store.get_worktree(worktree_id, user_id=user_id, repo_key=repo_key)
        except (sqlite3.Error, TypeError, ValueError):
            return None

    def inventory(
        self,
        *,
        repo_path: str,
        user_id: str,
    ) -> WorktreeInventoryResult:
        try:
            existing = SQLiteWorktreeStore.for_existing_repo(repo_path)
            if existing is None:
                return WorktreeInventoryResult(store_present=False, records=[])
            store, repo_key = existing
            return WorktreeInventoryResult(
                store_present=True,
                records=store.list_worktrees(user_id=user_id, repo_key=repo_key),
            )
        except (sqlite3.Error, TypeError, ValueError):
            return WorktreeInventoryResult(store_present=True, records=[])

    def inspect(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
    ) -> WorktreeInspectionResult:
        record = self.get_status(
            repo_path=repo_path,
            user_id=user_id,
            worktree_id=worktree_id,
        )
        if record is None:
            return WorktreeInspectionResult(found=False, changed_files=[])
        try:
            repo_root = Path(repo_path).resolve(strict=True)
        except (OSError, RuntimeError):
            return WorktreeInspectionResult(
                found=True,
                record=record,
                partial=True,
                changed_files=[],
            )
        try:
            return inspect_worktree(repo_root=repo_root, record=record)
        except (OSError, subprocess.SubprocessError, ValueError):
            return WorktreeInspectionResult(
                found=True,
                record=record,
                partial=True,
                changed_files=[],
            )

    def prepare_reverification(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
    ) -> WorktreeReverificationPreflight:
        record = self.get_status(
            repo_path=repo_path,
            user_id=user_id,
            worktree_id=worktree_id,
        )
        if record is None:
            return WorktreeReverificationPreflight(
                accepted=False,
                reason="worktree_not_found",
            )
        try:
            repo_root = Path(repo_path).resolve(strict=True)
            return preflight_worktree_reverification(repo_root=repo_root, record=record)
        except (OSError, RuntimeError, ValueError):
            return WorktreeReverificationPreflight(
                accepted=False,
                reason="preflight_unavailable",
                record=record,
            )

    def record_patch_result(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
        applied: bool,
        changed_files: list[str],
    ) -> None:
        existing = SQLiteWorktreeStore.for_existing_repo(repo_path)
        if existing is None:
            return
        store, repo_key = existing
        store.update_worktree(
            worktree_id,
            user_id=user_id,
            repo_key=repo_key,
            status=WORKTREE_STATUS_PATCH_APPLIED
            if applied
            else WORKTREE_STATUS_PATCH_FAILED,
            changed_files=changed_files,
        )

    def record_verification_result(
        self,
        *,
        repo_path: str,
        user_id: str,
        worktree_id: str,
        command_label: str,
        succeeded: bool,
    ) -> None:
        existing = SQLiteWorktreeStore.for_existing_repo(repo_path)
        if existing is None:
            return
        store, repo_key = existing
        store.update_worktree(
            worktree_id,
            user_id=user_id,
            repo_key=repo_key,
            status=WORKTREE_STATUS_VERIFICATION_SUCCEEDED
            if succeeded
            else WORKTREE_STATUS_VERIFICATION_FAILED,
            verification_label=command_label,
            verification_status="succeeded" if succeeded else "failed",
        )

    def _rollback_worktree(
        self,
        repo_path: str | Path,
        execution_path: Path | None,
    ) -> None:
        if execution_path is None:
            return
        try:
            _git("worktree", "unlock", str(execution_path), cwd=Path(repo_path))
        except (OSError, subprocess.SubprocessError):
            pass
        try:
            _git("worktree", "remove", "--force", str(execution_path), cwd=Path(repo_path))
        except (OSError, subprocess.SubprocessError):
            pass
        shutil.rmtree(execution_path, ignore_errors=True)
        try:
            execution_path.parent.rmdir()
        except OSError:
            pass


def _failed(reason: str, summary: str) -> WorktreeCreateResult:
    return WorktreeCreateResult(
        created=False,
        status=WORKTREE_STATUS_CREATE_FAILED,
        reason=reason,
        public_summary=summary,
    )


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _git_stdout(*args: str, cwd: Path) -> str:
    return _git(*args, cwd=cwd).stdout


def _is_git_work_tree(repo_path: Path) -> bool:
    try:
        return _git_stdout("rev-parse", "--is-inside-work-tree", cwd=repo_path).strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def _is_git_repo(repo_path: Path) -> bool:
    try:
        return bool(_git_stdout("rev-parse", "--git-dir", cwd=repo_path).strip())
    except (OSError, subprocess.SubprocessError):
        return False


def _is_bare_repo(repo_path: Path) -> bool:
    return _git_stdout("rev-parse", "--is-bare-repository", cwd=repo_path).strip() == "true"


def _is_repopilot_ignored(repo_path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", ".repopilot/placeholder"],
        cwd=repo_path,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode == 0


def _workspace_status(repo_path: Path) -> str:
    return _git_stdout("status", "--porcelain", "--untracked-files=all", cwd=repo_path).strip()


def _new_worktree_id() -> str:
    now = datetime.now(tz=UTC).strftime("%Y%m%d")
    return f"wt_{now}_{uuid4().hex[:6]}"
