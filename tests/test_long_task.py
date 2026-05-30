from pathlib import Path

from app.longtask.manager import LongTaskManager
from app.longtask.planner import LongTaskPlanner
from app.longtask.store import SQLiteLongTaskStore
from app.memory.store import compute_repo_key
from app.providers.model_provider import ModelProviderResponse


class InvalidPlanProvider:
    def generate(self, request):
        return ModelProviderResponse(
            answer="{not-json",
            audit_summary={"provider": "invalid", "status": "success"},
        )


class SchemaAwarePlanProvider:
    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, request):
        self.prompt = request.evidence[0]["snippet"]
        if "Return JSON only" not in self.prompt or "title" not in self.prompt:
            return ModelProviderResponse(
                answer="{not-json",
                audit_summary={"provider": "schema_aware", "status": "success"},
            )
        return ModelProviderResponse(
            answer=(
                '{"steps": ['
                '{"title": "增强定位", "query_hint": "增强 query", '
                '"expected_outcome": "增强结果", "acceptance_hint": "增强验收"},'
                '{"title": "增强检索", "query_hint": "增强 query 2", '
                '"expected_outcome": "增强结果 2", "acceptance_hint": "增强验收 2"},'
                '{"title": "增强汇总", "query_hint": "增强 query 3", '
                '"expected_outcome": "增强结果 3", "acceptance_hint": "增强验收 3"}'
                "]}"
            ),
            audit_summary={"provider": "schema_aware", "status": "success"},
        )


def test_long_task_store_uses_v13_repo_key_and_user_repo_scope(
    tmp_path: Path,
) -> None:
    store = SQLiteLongTaskStore.for_repo(tmp_path)
    repo_key = compute_repo_key(tmp_path)

    task = store.create_task(
        user_id="u001",
        repo_key=repo_key,
        title="分析 AgentLoop",
        goal="分析 AgentLoop",
        task_type="implementation_explanation",
        plan_source="deterministic_template",
        steps=[
            {
                "step_id": "step_1",
                "title": "检索入口",
                "action_type": "repo_rag",
                "query_hint": "AgentLoop",
            }
        ],
    )

    assert task.repo_key == repo_key
    assert task.status == "paused"
    assert (tmp_path / ".repopilot" / "tasks.sqlite3").exists()
    assert [item.task_id for item in store.list_tasks(user_id="u001", repo_key=repo_key)] == [
        task.task_id
    ]
    assert store.list_tasks(user_id="u002", repo_key=repo_key) == []


def test_long_task_store_enforces_quota_and_archives_terminal_tasks(
    tmp_path: Path,
) -> None:
    store = SQLiteLongTaskStore.for_repo(tmp_path)
    repo_key = compute_repo_key(tmp_path)
    steps = [
        {
            "step_id": "step_1",
            "title": "检索入口",
            "action_type": "repo_rag",
            "query_hint": "AgentLoop",
        }
    ]

    created = [
        store.create_task(
            user_id="u001",
            repo_key=repo_key,
            title=f"任务 {index}",
            goal=f"任务 {index}",
            task_type="unknown",
            plan_source="deterministic_template",
            steps=steps,
        )
        for index in range(20)
    ]

    assert store.count_open_tasks(user_id="u001", repo_key=repo_key) == 20
    assert store.can_create_task(user_id="u001", repo_key=repo_key) is False

    store.update_task_status(created[0].task_id, "completed")
    assert store.archive_task(created[0].task_id) is True

    assert store.count_open_tasks(user_id="u001", repo_key=repo_key) == 19
    assert store.can_create_task(user_id="u001", repo_key=repo_key) is True
    assert created[0].task_id not in [
        task.task_id for task in store.list_tasks(user_id="u001", repo_key=repo_key)
    ]


def test_planner_uses_task_type_templates_and_provider_fallback() -> None:
    planner = LongTaskPlanner(provider=InvalidPlanProvider(), provider_enabled=True)

    plan = planner.plan("规划 V14 OpenSpec 阶段", memory_summary="")

    assert plan.task_type == "stage_planning"
    assert plan.plan_source == "deterministic_fallback"
    assert 3 <= len(plan.steps) <= 5
    assert {step.action_type for step in plan.steps} == {"repo_rag"}
    assert all(step.expected_outcome for step in plan.steps)


def test_planner_sends_json_schema_prompt_for_provider_enhancement() -> None:
    provider = SchemaAwarePlanProvider()
    planner = LongTaskPlanner(provider=provider, provider_enabled=True)

    plan = planner.plan("定位 MissingSymbol", memory_summary="偏好中文")

    assert plan.plan_source == "provider_assisted"
    assert plan.steps[0].title == "增强定位"
    assert plan.steps[0].action_type == "repo_rag"
    assert "Return JSON only" in provider.prompt
    assert "Do not change step count, order, step_id, or action_type" in provider.prompt


def test_manager_create_supplement_reopen_and_redaction(tmp_path: Path) -> None:
    manager = LongTaskManager()
    created = manager.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="创建长任务：分析 AgentLoop task_xxx 路由",
    )

    assert created.handled is True
    assert "task_" in created.answer
    assert "恢复任务" in created.answer
    assert created.tool_action is None
    assert str(tmp_path) not in created.answer

    task_id = created.task_id
    assert task_id is not None

    store = SQLiteLongTaskStore.for_repo(tmp_path)
    store.update_task_status(task_id, "blocked")
    supplemented = manager.handle_command(
        user_id="u001",
        session_id="s999",
        repo_path=tmp_path,
        message=f"补充信息到任务 {task_id}：重点看 app/harness/kernel.py",
    )

    assert supplemented.handled is True
    assert "已补充任务" in supplemented.answer
    assert store.get_task(task_id).status == "paused"

    store.update_task_status(task_id, "failed")
    reopened = manager.handle_command(
        user_id="u001",
        session_id="s999",
        repo_path=tmp_path,
        message=f"重新打开任务 {task_id}",
    )

    assert reopened.handled is True
    assert "已重新打开任务" in reopened.answer
    task = store.get_task(task_id)
    assert task.status == "paused"
    assert task.retry_round == 1


def test_manager_rejects_cross_user_task_id_access(tmp_path: Path) -> None:
    manager = LongTaskManager()
    created = manager.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="创建长任务：分析 AgentLoop",
    )
    task_id = created.task_id
    assert task_id is not None

    status = manager.handle_command(
        user_id="u002",
        session_id="s002",
        repo_path=tmp_path,
        message=f"查看任务 {task_id}",
    )

    assert status.handled is True
    assert status.answer == f"未找到任务 {task_id}。"


def test_manager_rejects_cross_user_tool_completion(tmp_path: Path) -> None:
    manager = LongTaskManager()
    created = manager.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="创建长任务：分析 AgentLoop",
    )
    task_id = created.task_id
    assert task_id is not None

    result = manager.complete_tool_action(
        user_id="u002",
        repo_path=tmp_path,
        task_id=task_id,
        results=[
            {
                "file_path": "app/harness/kernel.py",
                "line_number": 1,
                "line_text": "class AgentLoop:",
            }
        ],
    )

    assert result.handled is True
    assert result.answer == f"未找到任务 {task_id}。"
    assert SQLiteLongTaskStore.for_repo(tmp_path).get_task(task_id).status == "paused"


def test_manager_tool_completion_summary_redacts_absolute_paths(tmp_path: Path) -> None:
    manager = LongTaskManager()
    created = manager.handle_command(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="创建长任务：分析 AgentLoop",
    )
    task_id = created.task_id
    assert task_id is not None

    result = manager.complete_tool_action(
        user_id="u001",
        repo_path=tmp_path,
        task_id=task_id,
        results=[
            {
                "file_path": str(tmp_path / "secret.py"),
                "line_number": 1,
                "line_text": "SECRET = True",
            },
            {
                "file_path": "app/harness/kernel.py",
                "line_number": 1,
                "line_text": "class AgentLoop:",
            },
        ],
    )

    assert str(tmp_path) not in result.answer
    assert "secret.py" not in result.answer
    assert "app/harness/kernel.py" in result.answer
