from pathlib import Path
import sqlite3

from app.assistant.control_surface import (
    AssistantControlSurface,
    is_assistant_status_request,
)
from app.longtask.manager import LongTaskManager
from app.memory.manager import MemoryManager


def test_status_trigger_accepts_explicit_chinese_and_english_requests() -> None:
    assert is_assistant_status_request("助手状态") is True
    assert is_assistant_status_request("RepoPilot 状态") is True
    assert is_assistant_status_request("你能做什么") is True
    assert is_assistant_status_request("assistant status") is True
    assert is_assistant_status_request("what can you do") is True


def test_status_trigger_rejects_capability_and_repo_search_questions() -> None:
    assert is_assistant_status_request("memory 实现了吗?") is False
    assert is_assistant_status_request("MemoryStore 在哪里实现?") is False
    assert is_assistant_status_request("创建长任务：查看助手状态") is False
    assert is_assistant_status_request("你现在能不能介绍一下项目?") is False


def test_status_answer_does_not_create_repo_local_state(tmp_path: Path) -> None:
    surface = AssistantControlSurface(
        memory_manager=MemoryManager(),
        long_task_manager=LongTaskManager(),
    )

    answer = surface.answer_status(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
    )

    assert "当前能力" in answer
    assert "当前状态" in answer
    assert "下一步" in answer
    assert "PREF=0" in answer
    assert "LTM=0" in answer
    assert "STM=0" in answer
    assert "未归档长任务=0" in answer
    assert not (tmp_path / ".repopilot").exists()


def test_status_answer_summarizes_memory_counts_without_values(tmp_path: Path) -> None:
    memory = MemoryManager()
    memory.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住：pref:language=中文",
    )
    memory.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住：project:secret_token=SHOULD_NOT_LEAK",
    )
    memory.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住：stm:topic=V15",
    )
    surface = AssistantControlSurface(
        memory_manager=memory,
        long_task_manager=LongTaskManager(),
    )

    answer = surface.answer_status(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
    )

    assert "PREF=1" in answer
    assert "LTM=1" in answer
    assert "STM=1" in answer
    assert "SHOULD_NOT_LEAK" not in answer
    assert str(tmp_path) not in answer
    assert "memory.sqlite3" not in answer


def test_status_answer_summarizes_recent_long_tasks_without_scratch(tmp_path: Path) -> None:
    long_tasks = LongTaskManager()
    created = long_tasks.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="创建长任务：分析 AgentLoop",
    )
    task_id = created.answer.split("task_id=")[1].split("，")[0]
    long_tasks.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message=f"补充信息到任务 {task_id}：SCRATCH_SHOULD_NOT_LEAK",
    )
    surface = AssistantControlSurface(
        memory_manager=MemoryManager(),
        long_task_manager=long_tasks,
    )

    answer = surface.answer_status(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
    )

    assert "未归档长任务=1" in answer
    assert task_id in answer
    assert "paused" in answer
    assert "分析 AgentLoop" in answer
    assert "SCRATCH_SHOULD_NOT_LEAK" not in answer
    assert str(tmp_path) not in answer
    assert "tasks.sqlite3" not in answer


def test_status_answer_redacts_absolute_paths_from_recent_long_tasks(
    tmp_path: Path,
) -> None:
    long_tasks = LongTaskManager()
    secret_path = r"C:\Users\50805\secret\repo\app.py"
    created = long_tasks.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message=f"创建长任务：分析 {secret_path}",
    )
    task_id = created.answer.split("task_id=")[1].split("，")[0]
    with sqlite3.connect(tmp_path / ".repopilot" / "tasks.sqlite3") as conn:
        conn.execute(
            "UPDATE long_task_steps SET title = ? WHERE task_id = ? AND position = 0",
            (f"检查 {secret_path}", task_id),
        )
    surface = AssistantControlSurface(
        memory_manager=MemoryManager(),
        long_task_manager=long_tasks,
    )

    answer = surface.answer_status(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
    )

    assert "[redacted_path]" in answer
    assert "C:\\Users" not in answer
    assert "secret" not in answer
    assert "app.py" not in answer


def test_status_answer_marks_missing_repo_unavailable(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    surface = AssistantControlSurface(
        memory_manager=MemoryManager(),
        long_task_manager=LongTaskManager(),
    )

    answer = surface.answer_status(
        user_id="u001",
        session_id="s001",
        repo_path=missing,
    )

    assert "状态不可用" in answer
    assert str(missing) not in answer
