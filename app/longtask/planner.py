import json

from app.longtask.types import ACTION_REPO_RAG, LongTaskStep, PlanResult
from app.providers.model_provider import (
    ModelProvider,
    ModelProviderRequest,
    StructuredOutputInstruction,
)
from app.rag.query_understanding import (
    QUESTION_CALL_RELATIONSHIP,
    QUESTION_CODE_LOCATION,
    QUESTION_FILE_SUMMARY,
    QUESTION_IMPLEMENTATION_EXPLANATION,
    QUESTION_TEST_OR_VALIDATION,
    QueryUnderstanding,
)


PLAN_SOURCE_TEMPLATE = "deterministic_template"
PLAN_SOURCE_FALLBACK = "deterministic_fallback"
PLAN_SOURCE_PROVIDER = "provider_assisted"
_PLAN_OUTPUT_INSTRUCTION = StructuredOutputInstruction(
    name="long_task_plan",
    json_example=(
        '{"steps":[{"title":"...","query_hint":"...",'
        '"expected_outcome":"...","acceptance_hint":"..."}]}'
    ),
    max_output_tokens=2000,
)


class LongTaskPlanner:
    def __init__(
        self,
        *,
        provider: ModelProvider | None = None,
        provider_enabled: bool = False,
        query_understanding: QueryUnderstanding | None = None,
    ) -> None:
        self.provider = provider
        self.provider_enabled = provider_enabled
        self.query_understanding = query_understanding or QueryUnderstanding()

    def plan(self, goal: str, memory_summary: str = "") -> PlanResult:
        task_type = self._task_type(goal)
        template = _template_for(task_type, goal)
        if not self.provider_enabled or self.provider is None:
            return PlanResult(
                task_type=task_type,
                plan_source=PLAN_SOURCE_TEMPLATE,
                steps=template,
            )

        try:
            response = self.provider.generate(
                ModelProviderRequest(
                    original_query=goal,
                    question_type="long_task_plan",
                    evidence=[
                        {
                            "file_path": "long_task_template",
                            "start_line": 1,
                            "end_line": len(template),
                            "snippet": _provider_template_prompt(
                                task_type,
                                template,
                                memory_summary,
                            ),
                        }
                    ],
                    output_mode="json_object",
                    structured_output=_PLAN_OUTPUT_INSTRUCTION,
                )
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return _fallback_plan(task_type, template)
        if response.audit_summary.get("status") != "success":
            return _fallback_plan(task_type, template)
        try:
            enhanced = _apply_provider_json(template, response.answer)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return _fallback_plan(task_type, template)
        return PlanResult(
            task_type=task_type,
            plan_source=PLAN_SOURCE_PROVIDER,
            steps=enhanced,
            provider_status="success",
        )

    def _task_type(self, goal: str) -> str:
        if any(term in goal for term in ("阶段", "OpenSpec", "规划", "V14", "V15")):
            return "stage_planning"
        return self.query_understanding.build_search_plan(goal).question_type


def _template_for(task_type: str, goal: str) -> list[LongTaskStep]:
    templates = {
        QUESTION_CODE_LOCATION: [
            ("提取定位线索", "提取目标 symbol、路径和错误 token"),
            ("检索候选文件", "定位相关文件和定义位置"),
            ("汇总可能位置", "汇总最相关的文件和行号"),
        ],
        QUESTION_IMPLEMENTATION_EXPLANATION: [
            ("识别相关模块", "识别实现入口和关键模块"),
            ("检索实现证据", "检索实现细节和相关代码"),
            ("汇总行为依赖", "总结行为、依赖和边界"),
            ("准备解释交接", "形成解释和下一步建议"),
        ],
        QUESTION_CALL_RELATIONSHIP: [
            ("识别调用线索", "识别 caller、callee 和依赖线索"),
            ("检索调用点", "检索调用关系和引用位置"),
            ("检索依赖上下文", "检索相关依赖和边界"),
            ("汇总关系", "总结调用关系和风险"),
        ],
        QUESTION_TEST_OR_VALIDATION: [
            ("识别验证目标", "识别测试、验证或脚本目标"),
            ("检索测试脚本", "检索相关测试和验证命令"),
            ("汇总覆盖现状", "总结已有覆盖和缺口"),
            ("提出验证门", "整理后续验证 gate"),
        ],
        QUESTION_FILE_SUMMARY: [
            ("识别目标文件", "识别需要总结的文件"),
            ("检索文件证据", "检索文件结构和职责证据"),
            ("汇总职责", "总结结构、职责和边界"),
        ],
        "stage_planning": [
            ("读取阶段上下文", "读取当前阶段、handoff、harness 和 OpenSpec 上下文"),
            ("定义 scope 和非目标", "整理阶段目标、非目标和边界"),
            ("草拟 OpenSpec 影响", "分析 proposal、design、tasks 和 spec delta 影响"),
            ("定义 review 与验证门", "整理 review checklist 和验证命令"),
            ("准备交接摘要", "形成 handoff、风险和下一步建议"),
        ],
        "unknown": [
            ("澄清目标", "提取用户目标和约束"),
            ("广泛检索证据", "检索相关仓库证据"),
            ("汇总发现", "总结发现和风险"),
            ("准备下一步", "整理下一步建议"),
        ],
    }
    raw_steps = templates.get(task_type, templates["unknown"])
    return [
        LongTaskStep(
            step_id=f"step_{index}",
            title=_limit_text(title, 120),
            action_type=ACTION_REPO_RAG,
            query_hint=_limit_text(f"{hint}: {goal}", 500),
            expected_outcome=_limit_text(hint, 500),
            acceptance_hint=_limit_text("返回仓库证据摘要供人工判断。", 500),
        )
        for index, (title, hint) in enumerate(raw_steps, start=1)
    ]


def _apply_provider_json(
    template: list[LongTaskStep],
    raw_json: str,
) -> list[LongTaskStep]:
    payload = json.loads(raw_json)
    raw_steps = payload["steps"]
    if not isinstance(raw_steps, list) or len(raw_steps) != len(template):
        raise ValueError("provider step count mismatch")
    result: list[LongTaskStep] = []
    for template_step, raw_step in zip(template, raw_steps, strict=True):
        if not isinstance(raw_step, dict):
            raise ValueError("provider step is not object")
        result.append(
            LongTaskStep(
                step_id=template_step.step_id,
                title=_limit_text(str(raw_step.get("title") or template_step.title), 120),
                action_type=template_step.action_type,
                query_hint=_limit_text(
                    str(raw_step.get("query_hint") or template_step.query_hint),
                    500,
                ),
                expected_outcome=_limit_text(
                    str(raw_step.get("expected_outcome") or template_step.expected_outcome),
                    500,
                ),
                acceptance_hint=_limit_text(
                    str(raw_step.get("acceptance_hint") or template_step.acceptance_hint),
                    500,
                ),
            )
        )
    return result


def _provider_template_prompt(
    task_type: str,
    template: list[LongTaskStep],
    memory_summary: str,
) -> str:
    step_rows = "\n".join(
        (
            f"- {step.step_id}: title={step.title}; action_type={step.action_type}; "
            f"query_hint={step.query_hint}; expected_outcome={step.expected_outcome}; "
            f"acceptance_hint={step.acceptance_hint}"
        )
        for step in template
    )
    memory_hint = _limit_text(memory_summary, 500) if memory_summary else "(none)"
    return (
        f"task_type={task_type}\n"
        f"memory_summary={memory_hint}\n"
        f"template_steps:\n{step_rows}"
    )


def _fallback_plan(
    task_type: str,
    template: list[LongTaskStep],
) -> PlanResult:
    return PlanResult(
        task_type=task_type,
        plan_source=PLAN_SOURCE_FALLBACK,
        steps=template,
        provider_status="fallback",
    )


def _limit_text(value: str, max_chars: int) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"
