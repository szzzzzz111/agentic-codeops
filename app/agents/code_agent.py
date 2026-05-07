from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentResult:
    answer: str
    related_files: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, str]] = field(default_factory=list)


class CodeAgent:
    def run(self, message: str, repo_path: str, trace_id: str) -> AgentResult:
        return AgentResult(
            answer=(
                "Mock 分析结果：V1 已收到请求，但不会读取 "
                f"{repo_path}。V2 会加入 list_files/read_file/search_code 工具，"
                "用于安全的仓库分析。"
            ),
            related_files=[],
            tool_calls=[],
        )
