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
                "Mock analysis result: V1 received your request but does not read "
                f"{repo_path}. V2 will add list_files/read_file/search_code tools "
                "for safe repository analysis."
            ),
            related_files=[],
            tool_calls=[],
        )
