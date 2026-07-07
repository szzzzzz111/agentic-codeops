from dataclasses import dataclass
from typing import Iterable, Protocol


REPO_RAG_TOOL = "repo_rag"
PATCH_APPLY_TOOL = "patch_apply"
WORKTREE_CREATE_TOOL = "worktree_create"
WORKTREE_DISPOSE_TOOL = "worktree_dispose"
VERIFICATION_RUN_TOOL = "verification_run"

V11_CAPABILITY_STATUS_ANSWER = (
    "V11 提供 Grounded Answer 和 Model Provider Boundary；"
    "默认 fake provider 保持离线可验证，显式配置后可使用 OpenAI-compatible provider；"
    "V12 提供 deterministic query rewrite 和 rerank；"
    "V13 提供 SQLite-backed Memory（PREF/LTM 和进程内 STM）；"
    "当前仍未实现真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、"
    "跨 repo 智能召回或 context compression。"
)
V12_CAPABILITY_STATUS_ANSWER = (
    "V12 提供 deterministic query rewrite 和 rerank；"
    "V13 已实现 Memory；"
    "当前仍未实现真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、"
    "跨 repo 智能召回或 context compression。"
)
V13_CAPABILITY_STATUS_ANSWER = (
    "V13 提供 SQLite-backed PREF/LTM 和进程内 STM；"
    "支持明确 memory 指令和内部 memory audit；"
    "当前未实现向量记忆、自动模型总结、跨 repo 智能召回或 context compression。"
)
VECTOR_CAPABILITY_STATUS_ANSWER = (
    "V9 提供轻量 embedding retrieval 和 hybrid search；"
    "当前未默认接入 Milvus、Elasticsearch、PgVector、Qdrant 或真实外部 embedding 服务。"
)
PATCH_CAPABILITY_STATUS_ANSWER = (
    "V16 提供 Safe Patch Authoring：可基于仓库证据生成 patch proposal，"
    "并在明确确认后受控 apply；V17 提供独立 Verification Runner；"
    "V18 提供明确组合确认下的 Patch + Verify Loop；"
    "V19 提供 Persistent Audit / Recovery；"
    "V20-V23 提供隔离 worktree 生命周期，包括创建、检查、重验证和丢弃/对账；"
    "V25 提供精确确认后的 Verified Patch Promotion；"
    "当前未实现自动 commit/push、branch/PR automation、connector、"
    "background retry 或 runtime subagent，默认不生成真实 diff。"
)


class ToolMetadata(Protocol):
    name: str


@dataclass(frozen=True)
class RuntimeCapabilityFacts:
    registered_tools: frozenset[str]

    @property
    def missing_patch_execution_primitives(self) -> tuple[str, ...]:
        required = (
            PATCH_APPLY_TOOL,
            VERIFICATION_RUN_TOOL,
            WORKTREE_CREATE_TOOL,
            WORKTREE_DISPOSE_TOOL,
        )
        return tuple(name for name in required if name not in self.registered_tools)

    @property
    def patch_execution_available(self) -> bool:
        return not self.missing_patch_execution_primitives

    @property
    def repo_rag_available(self) -> bool:
        return REPO_RAG_TOOL in self.registered_tools


def derive_runtime_capability_facts(
    tool_specs: Iterable[ToolMetadata],
) -> RuntimeCapabilityFacts:
    return RuntimeCapabilityFacts(
        registered_tools=frozenset(spec.name for spec in tool_specs),
    )


def default_runtime_capability_facts() -> RuntimeCapabilityFacts:
    return RuntimeCapabilityFacts(
        registered_tools=frozenset(
            {
                REPO_RAG_TOOL,
                PATCH_APPLY_TOOL,
                WORKTREE_CREATE_TOOL,
                WORKTREE_DISPOSE_TOOL,
                VERIFICATION_RUN_TOOL,
            }
        )
    )


def format_capability_status_answer(
    message: str,
    facts: RuntimeCapabilityFacts,
) -> str:
    lower = message.lower()
    asks_patch = "patch" in lower or "补丁" in message
    asks_memory = "memory" in lower or "记忆" in message
    asks_rewrite_or_rerank = any(term in lower for term in ("query rewrite", "rerank"))
    asks_vector_stack = any(
        term in lower
        for term in ("embedding", "milvus", "elasticsearch", "pgvector", "qdrant", "vector")
    )
    asks_repo_rag_backed_status = asks_vector_stack or _asks_about_v11_stack(message)
    if asks_repo_rag_backed_status and not facts.repo_rag_available:
        answer = (
            "repo RAG backed capability 当前不能宣称当前可用：repo_rag 未注册。"
            "当前未默认接入 Milvus、Elasticsearch、PgVector、Qdrant 或真实外部 embedding 服务；"
            "真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、"
            "跨 repo 智能召回或 context compression 仍未实现。"
        )
        if asks_memory:
            return f"{answer}；{V13_CAPABILITY_STATUS_ANSWER}"
        return answer
    if asks_patch:
        return _format_patch_capability_status(facts)
    if asks_memory and asks_vector_stack:
        return f"{VECTOR_CAPABILITY_STATUS_ANSWER}；{V13_CAPABILITY_STATUS_ANSWER}"
    if asks_memory and asks_rewrite_or_rerank:
        return f"{V12_CAPABILITY_STATUS_ANSWER}；{V13_CAPABILITY_STATUS_ANSWER}"
    if asks_memory:
        return V13_CAPABILITY_STATUS_ANSWER
    if asks_rewrite_or_rerank:
        return V12_CAPABILITY_STATUS_ANSWER
    if _asks_about_v11_stack(message):
        return V11_CAPABILITY_STATUS_ANSWER
    return VECTOR_CAPABILITY_STATUS_ANSWER


def format_control_surface_capability_summary(
    facts: RuntimeCapabilityFacts,
) -> str:
    if facts.repo_rag_available:
        return (
            "当前能力：可以基于仓库证据回答代码问题，管理明确 Memory 指令，"
            "管理 repo-local Long Task，并保持只读权限、审批和审计边界。"
        )
    return (
        "当前能力：仓库证据问答当前不可用（repo_rag 未注册）；"
        "仍可管理明确 Memory 指令和 repo-local Long Task，"
        "并保持只读权限、审批和审计边界。"
    )


def _format_patch_capability_status(facts: RuntimeCapabilityFacts) -> str:
    missing = facts.missing_patch_execution_primitives
    if not missing:
        return PATCH_CAPABILITY_STATUS_ANSWER
    missing_summary = "、".join(f"{name} 未注册" for name in missing)
    return (
        "patch capability status 当前不能宣称执行路径可用："
        f"{missing_summary}。"
        "V19 提供 Persistent Audit / Recovery 等 manager-only 边界；"
        "当前未实现自动 commit/push、branch/PR automation、connector、"
        "background retry 或 runtime subagent，默认不生成真实 diff。"
    )


def _asks_about_v11_stack(message: str) -> bool:
    lower = message.lower()
    return any(
        term in lower
        for term in (
            "grounded answer",
            "model provider",
            "rerank",
            "context compression",
            "query rewrite",
        )
    )
