from dataclasses import dataclass
from pathlib import Path
import re

from app.longtask.manager import LongTaskManager
from app.memory.manager import MemoryManager


_STATUS_REQUESTS = {
    "助手状态",
    "repopilot 状态",
    "你能做什么",
    "assistant status",
    "what can you do",
}
_LONG_TASK_PREFIXES = (
    "创建长任务",
    "新建长任务",
    "列出长任务",
    "任务列表",
    "列出任务",
    "查看任务",
    "任务状态",
    "暂停任务",
    "恢复任务",
    "继续任务",
    "运行任务",
    "归档任务",
    "重新打开任务",
    "重开任务",
    "补充信息到任务",
)
_MEMORY_PREFIXES = ("记住:", "请记住", "remember:", "忘记:", "请忘记", "forget:")


@dataclass(frozen=True)
class AssistantStatus:
    memory_available: bool
    pref_count: int
    ltm_count: int
    stm_count: int
    long_task_available: bool
    open_task_count: int
    recent_tasks: list[str]


class AssistantControlSurface:
    def __init__(
        self,
        *,
        memory_manager: MemoryManager | None = None,
        long_task_manager: LongTaskManager | None = None,
    ) -> None:
        self.memory_manager = memory_manager or MemoryManager()
        self.long_task_manager = long_task_manager or LongTaskManager()

    def answer_status(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
    ) -> str:
        status = self.collect_status(
            user_id=user_id,
            session_id=session_id,
            repo_path=repo_path,
        )
        unavailable = []
        if not status.memory_available:
            unavailable.append("Memory")
        if not status.long_task_available:
            unavailable.append("Long Task")
        unavailable_note = (
            f"状态不可用：{', '.join(unavailable)}。"
            if unavailable
            else "状态可用。"
        )
        tasks = "；".join(status.recent_tasks) if status.recent_tasks else "无"
        return (
            "当前能力：可以基于仓库证据回答代码问题，管理明确 Memory 指令，"
            "管理 repo-local Long Task，并保持只读权限、审批和审计边界。\n"
            "当前状态："
            f"{unavailable_note} "
            f"Memory PREF={status.pref_count}，LTM={status.ltm_count}，"
            f"STM={status.stm_count}；"
            f"未归档长任务={status.open_task_count}；最近任务：{tasks}。\n"
            "下一步：可以直接问代码问题，发送 `记住：pref:language=中文`，"
            "发送 `创建长任务：...`，或发送 `列出长任务` / `恢复任务 task_xxx`。"
        )

    def collect_status(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
    ) -> AssistantStatus:
        memory = self.memory_manager.control_surface_summary(
            user_id=user_id,
            session_id=session_id,
            repo_path=repo_path,
        )
        tasks = self.long_task_manager.control_surface_summary(
            user_id=user_id,
            repo_path=repo_path,
        )
        return AssistantStatus(
            memory_available=memory["available"] == "true",
            pref_count=int(memory["pref_count"]),
            ltm_count=int(memory["ltm_count"]),
            stm_count=int(memory["stm_count"]),
            long_task_available=tasks["available"] == "true",
            open_task_count=int(tasks["open_task_count"]),
            recent_tasks=list(tasks["recent_tasks"]),
        )


def is_assistant_status_request(message: str) -> bool:
    normalized = _normalize(message)
    if _starts_with_any(normalized, _MEMORY_PREFIXES):
        return False
    if _starts_with_any(normalized, _LONG_TASK_PREFIXES):
        return False
    return normalized.lower() in _STATUS_REQUESTS


def _normalize(message: str) -> str:
    compact = re.sub(r"\s+", " ", message.strip().replace("：", ":"))
    return compact.rstrip("?.？！。")


def _starts_with_any(message: str, prefixes: tuple[str, ...]) -> bool:
    lowered = message.lower()
    return any(lowered.startswith(prefix.lower()) for prefix in prefixes)
