from pathlib import Path, PurePosixPath, PureWindowsPath
import sqlite3

from app.longtask.parser import parse_long_task_command
from app.longtask.planner import LongTaskPlanner
from app.longtask.store import SQLiteLongTaskStore, store_for_existing_repo
from app.longtask.types import (
    ACTION_REPO_RAG,
    LongTask,
    LongTaskCommand,
    LongTaskCommandResult,
    TASK_STATUS_BLOCKED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PAUSED,
    TASK_STATUS_RUNNING,
)


LONG_TASK_UNAVAILABLE_ANSWER = "无法处理长任务：当前仓库任务存储不可用。"


class LongTaskManager:
    def __init__(
        self,
        *,
        planner: LongTaskPlanner | None = None,
    ) -> None:
        self.planner = planner or LongTaskPlanner()

    def handle_command(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
        message: str,
        memory_summary: str = "",
    ) -> LongTaskCommandResult:
        command = parse_long_task_command(message)
        if command is None:
            return LongTaskCommandResult(handled=False)
        try:
            store, repo_key = store_for_existing_repo(repo_path)
            return self._handle(
                command=command,
                store=store,
                user_id=user_id,
                repo_key=repo_key,
                memory_summary=memory_summary,
            )
        except (OSError, sqlite3.Error, ValueError):
            return LongTaskCommandResult(
                handled=True,
                answer=LONG_TASK_UNAVAILABLE_ANSWER,
                audit_summary="long_task_status=unavailable",
            )

    def _handle(
        self,
        *,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
        memory_summary: str,
    ) -> LongTaskCommandResult:
        if command.action == "create":
            return self._create(command, store, user_id, repo_key, memory_summary)
        if command.action == "list":
            return self._list(store, user_id, repo_key)
        if command.action == "status":
            return self._status(command, store, user_id, repo_key)
        if command.action == "pause":
            return self._pause(command, store, user_id, repo_key)
        if command.action == "resume":
            return self._resume(command, store, user_id, repo_key)
        if command.action == "supplement":
            return self._supplement(command, store, user_id, repo_key)
        if command.action == "archive":
            return self._archive(command, store, user_id, repo_key)
        if command.action == "reopen":
            return self._reopen(command, store, user_id, repo_key)
        return LongTaskCommandResult(handled=False)

    def _create(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
        memory_summary: str,
    ) -> LongTaskCommandResult:
        goal = command.goal.strip()
        if not goal:
            return LongTaskCommandResult(
                handled=True,
                answer="请提供长任务目标，例如：创建长任务：分析 AgentLoop。",
                audit_summary="long_task_status=blocked; reason=missing_goal",
            )
        if not store.can_create_task(user_id=user_id, repo_key=repo_key):
            return LongTaskCommandResult(
                handled=True,
                answer="未归档长任务已达 20 个，请先归档 completed/failed 任务。",
                audit_summary="long_task_status=quota_exceeded",
            )
        plan = self.planner.plan(goal, memory_summary=memory_summary)
        task = store.create_task(
            user_id=user_id,
            repo_key=repo_key,
            title=_title_from_goal(goal),
            goal=goal,
            task_type=plan.task_type,
            plan_source=plan.plan_source,
            steps=plan.steps,
        )
        first = task.current_step
        fallback_note = (
            "模型规划不可用，已使用默认计划。"
            if plan.plan_source == "deterministic_fallback"
            else ""
        )
        return LongTaskCommandResult(
            handled=True,
            answer=(
                f"已创建长任务：task_id={task.task_id}，状态 {task.status}。"
                f"{fallback_note}"
                f"下一步：{first.title if first else '无'}。"
                f"可说：恢复任务 {task.task_id}。"
            ),
            task_id=task.task_id,
            audit_summary=(
                f"long_task_status=created; task_id={task.task_id}; "
                f"plan_source={plan.plan_source}; task_type={plan.task_type}"
            ),
        )

    def _list(
        self,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        tasks = store.list_tasks(user_id=user_id, repo_key=repo_key)
        if not tasks:
            answer = "当前没有未归档长任务。"
        else:
            lines = [f"{task.task_id}：{task.status}，{task.title}" for task in tasks]
            answer = "当前未归档长任务：\n" + "\n".join(lines)
        return LongTaskCommandResult(
            handled=True,
            answer=answer,
            audit_summary=f"long_task_status=list; count={len(tasks)}",
        )

    def _status(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        task = self._resolve_task(command, store, user_id, repo_key)
        if isinstance(task, LongTaskCommandResult):
            return task
        return LongTaskCommandResult(
            handled=True,
            task_id=task.task_id,
            answer=_format_task_status(task),
            audit_summary=f"long_task_status=status; task_id={task.task_id}",
        )

    def _pause(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        task = self._resolve_task(command, store, user_id, repo_key)
        if isinstance(task, LongTaskCommandResult):
            return task
        if task.status not in {TASK_STATUS_RUNNING, TASK_STATUS_BLOCKED}:
            return LongTaskCommandResult(
                handled=True,
                answer=f"任务 {task.task_id} 当前状态为 {task.status}，不能暂停。",
                task_id=task.task_id,
                audit_summary=f"long_task_status=pause_noop; task_id={task.task_id}",
            )
        store.update_task_status(task.task_id, TASK_STATUS_PAUSED)
        return LongTaskCommandResult(
            handled=True,
            task_id=task.task_id,
            answer=f"已暂停任务 {task.task_id}。",
            audit_summary=f"long_task_status=paused; task_id={task.task_id}",
        )

    def _resume(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        task = self._resolve_task(command, store, user_id, repo_key)
        if isinstance(task, LongTaskCommandResult):
            return task
        if task.archived or task.status in {TASK_STATUS_COMPLETED, TASK_STATUS_FAILED}:
            return LongTaskCommandResult(
                handled=True,
                task_id=task.task_id,
                answer=f"任务 {task.task_id} 当前状态为 {task.status}，不能恢复。",
                audit_summary=f"long_task_status=resume_rejected; task_id={task.task_id}",
            )
        step = task.current_step
        if step is None:
            return LongTaskCommandResult(
                handled=True,
                task_id=task.task_id,
                answer=f"任务 {task.task_id} 没有可执行 step。",
                audit_summary=f"long_task_status=blocked; task_id={task.task_id}",
            )
        store.update_task_status(task.task_id, TASK_STATUS_RUNNING)
        query = _limit(f"{step.query_hint} {task.goal}", 500)
        return LongTaskCommandResult(
            handled=True,
            task_id=task.task_id,
            tool_action=ACTION_REPO_RAG,
            query_text=query,
            answer=f"准备推进任务 {task.task_id} 的步骤：{step.title}。",
            audit_summary=f"long_task_status=resume; task_id={task.task_id}",
        )

    def _supplement(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        task = _task_or_missing(store, command.task_id, user_id, repo_key)
        if isinstance(task, LongTaskCommandResult):
            return task
        if task.archived or task.status in {TASK_STATUS_COMPLETED, TASK_STATUS_FAILED}:
            return LongTaskCommandResult(
                handled=True,
                task_id=task.task_id,
                answer=f"任务 {task.task_id} 当前状态为 {task.status}，不能补充信息。",
            )
        store.append_scratch(task.task_id, command.note)
        if task.status == TASK_STATUS_BLOCKED:
            store.update_task_status(task.task_id, TASK_STATUS_PAUSED)
        return LongTaskCommandResult(
            handled=True,
            task_id=task.task_id,
            answer=f"已补充任务 {task.task_id}，状态 paused。可说：恢复任务 {task.task_id}。",
            audit_summary=f"long_task_status=supplemented; task_id={task.task_id}",
        )

    def _archive(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        if not command.task_id:
            return LongTaskCommandResult(handled=True, answer="请提供 task_id。")
        scoped_task = _task_or_missing(store, command.task_id, user_id, repo_key)
        if isinstance(scoped_task, LongTaskCommandResult):
            return scoped_task
        archived = store.archive_task(command.task_id)
        if not archived:
            return LongTaskCommandResult(
                handled=True,
                answer="只能归档 completed/failed 任务。",
                task_id=command.task_id,
            )
        return LongTaskCommandResult(
            handled=True,
            task_id=command.task_id,
            answer=f"已归档任务 {command.task_id}。",
            audit_summary=f"long_task_status=archived; task_id={command.task_id}",
        )

    def _reopen(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTaskCommandResult:
        if not command.task_id:
            return LongTaskCommandResult(handled=True, answer="请提供 task_id。")
        scoped_task = _task_or_missing(store, command.task_id, user_id, repo_key)
        if isinstance(scoped_task, LongTaskCommandResult):
            return scoped_task
        task = store.reopen_failed_task(command.task_id)
        if task is None:
            return LongTaskCommandResult(
                handled=True,
                task_id=command.task_id,
                answer="只能重新打开 failed 且未归档的任务。",
            )
        return LongTaskCommandResult(
            handled=True,
            task_id=task.task_id,
            answer=f"已重新打开任务 {task.task_id}，状态 paused。",
            audit_summary=f"long_task_status=reopened; task_id={task.task_id}",
        )

    def complete_tool_action(
        self,
        *,
        repo_path: str | Path,
        user_id: str,
        task_id: str,
        results: list[dict[str, str | int]],
        error: str | None = None,
    ) -> LongTaskCommandResult:
        store, repo_key = store_for_existing_repo(repo_path)
        task = _task_or_missing(store, task_id, user_id, repo_key)
        if isinstance(task, LongTaskCommandResult):
            return task
        if error:
            updated = store.mark_step_failure(task, f"tool_error={error}")
            return LongTaskCommandResult(
                handled=True,
                task_id=task_id,
                answer=(
                    f"任务 {task_id} step 执行失败，状态 {updated.status}。"
                    f"可说：恢复任务 {task_id} 重试。"
                ),
                audit_summary=f"long_task_status={updated.status}; task_id={task_id}",
            )
        if not results:
            updated = store.mark_step_blocked(task, "repo_rag 没有返回相关证据")
            return LongTaskCommandResult(
                handled=True,
                task_id=task_id,
                answer=(
                    f"已阻塞任务 {task_id}：当前 step 没有找到相关证据。"
                    f"请补充信息到任务 {task_id}。"
                ),
                audit_summary=f"long_task_status={updated.status}; task_id={task_id}",
            )
        summary = _result_summary(results)
        updated = store.mark_step_success(task, summary)
        next_step = updated.current_step
        if updated.status == TASK_STATUS_COMPLETED:
            answer = f"已完成任务 {task_id}。摘要：{summary}"
        else:
            answer = (
                f"已推进任务 {task_id}，状态 {updated.status}。"
                f"观察摘要：{summary}。"
                f"下一步：{next_step.title if next_step else '无'}。"
                f"可说：恢复任务 {task_id}。"
            )
        return LongTaskCommandResult(
            handled=True,
            task_id=task_id,
            answer=answer,
            audit_summary=f"long_task_status={updated.status}; task_id={task_id}",
        )

    def _resolve_task(
        self,
        command: LongTaskCommand,
        store: SQLiteLongTaskStore,
        user_id: str,
        repo_key: str,
    ) -> LongTask | LongTaskCommandResult:
        if command.task_id:
            return _task_or_missing(store, command.task_id, user_id, repo_key)
        tasks = store.list_tasks(user_id=user_id, repo_key=repo_key)
        if len(tasks) == 1:
            return tasks[0]
        if not tasks:
            return LongTaskCommandResult(handled=True, answer="当前没有未归档长任务。")
        candidates = "\n".join(
            f"{task.task_id}：{task.status}，{task.title}" for task in tasks
        )
        return LongTaskCommandResult(
            handled=True,
            answer=f"请指定 task_id。候选任务：\n{candidates}",
        )


def _task_or_missing(
    store: SQLiteLongTaskStore,
    task_id: str,
    user_id: str | None = None,
    repo_key: str | None = None,
) -> LongTask | LongTaskCommandResult:
    if not task_id:
        return LongTaskCommandResult(handled=True, answer="请提供 task_id。")
    task = store.get_task(task_id)
    if task is None:
        return LongTaskCommandResult(handled=True, answer=f"未找到任务 {task_id}。")
    if user_id is not None and task.user_id != user_id:
        return LongTaskCommandResult(handled=True, answer=f"未找到任务 {task_id}。")
    if repo_key is not None and task.repo_key != repo_key:
        return LongTaskCommandResult(handled=True, answer=f"未找到任务 {task_id}。")
    return task


def _format_task_status(task: LongTask) -> str:
    steps = "\n".join(
        f"{index}. {step.title} - {step.status}"
        for index, step in enumerate(task.steps, start=1)
    )
    current = task.current_step.title if task.current_step else "无"
    return (
        f"{task.task_id}：{task.status}，{task.title}\n"
        f"当前/下一步：{current}\n"
        f"{steps}"
    )


def _title_from_goal(goal: str) -> str:
    return _limit(goal, 120)


def _result_summary(results: list[dict[str, str | int]]) -> str:
    paths: list[str] = []
    for result in results:
        file_path = result.get("file_path")
        if (
            isinstance(file_path, str)
            and not _is_absolute_path(file_path)
            and file_path not in paths
        ):
            paths.append(file_path)
    suffix = f"：{', '.join(paths[:3])}" if paths else ""
    return _limit(f"找到 {len(results)} 条证据{suffix}", 1000)


def _is_absolute_path(file_path: str) -> bool:
    return PureWindowsPath(file_path).is_absolute() or PurePosixPath(
        file_path
    ).is_absolute()


def _limit(value: str, max_chars: int) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"
