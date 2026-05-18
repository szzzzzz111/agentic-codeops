from dataclasses import dataclass, field

from app.harness.kernel import AgentLoop, AgentLoopRequest
from app.tools.tool_executor import ToolExecutor


@dataclass(frozen=True)
class AgentResult:
    answer: str
    related_files: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, str]] = field(default_factory=list)


class CodeAgent:
    def __init__(
        self,
        tool_executor: ToolExecutor | None = None,
        agent_loop: AgentLoop | None = None,
    ) -> None:
        self._agent_loop = agent_loop or AgentLoop(tool_executor=tool_executor)

    def run(self, message: str, repo_path: str, trace_id: str) -> AgentResult:
        result = self._agent_loop.run(
            AgentLoopRequest(
                message=message,
                repo_path=repo_path,
                trace_id=trace_id,
            )
        )
        agent_result = result.to_agent_result()
        return AgentResult(**agent_result)
