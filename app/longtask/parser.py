import re

from app.longtask.types import LongTaskCommand


TASK_ID_PATTERN = re.compile(r"\btask_\d{8}_[a-f0-9]{4,12}\b")


def parse_long_task_command(message: str) -> LongTaskCommand | None:
    normalized = _normalize(message)
    lowered = normalized.lower()

    if _starts_with_any(normalized, ("创建长任务", "新建长任务")) or lowered.startswith(
        "create long task"
    ):
        return LongTaskCommand(action="create", goal=_content_after_colon(normalized))
    if _starts_with_any(normalized, ("列出长任务", "任务列表", "列出任务")):
        return LongTaskCommand(action="list")
    if _starts_with_any(normalized, ("查看任务", "任务状态")):
        return LongTaskCommand(action="status", task_id=_extract_task_id(normalized))
    if _starts_with_any(normalized, ("暂停任务",)):
        return LongTaskCommand(action="pause", task_id=_extract_task_id(normalized))
    if _starts_with_any(normalized, ("恢复任务", "继续任务", "运行任务")):
        return LongTaskCommand(action="resume", task_id=_extract_task_id(normalized))
    if _starts_with_any(normalized, ("归档任务",)):
        return LongTaskCommand(action="archive", task_id=_extract_task_id(normalized))
    if _starts_with_any(normalized, ("重新打开任务", "重开任务")):
        return LongTaskCommand(action="reopen", task_id=_extract_task_id(normalized))
    if normalized.startswith("补充信息到任务"):
        task_id = _extract_task_id(normalized)
        note = _content_after_colon(normalized)
        return LongTaskCommand(action="supplement", task_id=task_id, note=note)
    return None


def _normalize(message: str) -> str:
    return message.strip().replace("：", ":")


def _starts_with_any(message: str, prefixes: tuple[str, ...]) -> bool:
    return any(message.startswith(prefix) for prefix in prefixes)


def _content_after_colon(message: str) -> str:
    if ":" not in message:
        return message.split(maxsplit=1)[-1].strip() if " " in message else ""
    return message.split(":", 1)[1].strip()


def _extract_task_id(message: str) -> str:
    match = TASK_ID_PATTERN.search(message)
    if match is None:
        return ""
    return match.group(0)
