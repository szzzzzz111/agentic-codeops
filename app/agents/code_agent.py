from dataclasses import dataclass, field
import re

from app.tools.tool_executor import ToolExecutor


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*")


@dataclass(frozen=True)
class AgentResult:
    answer: str
    related_files: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, str]] = field(default_factory=list)


class CodeAgent:
    def __init__(self, tool_executor: ToolExecutor | None = None) -> None:
        self._tool_executor = tool_executor or ToolExecutor()

    def run(self, message: str, repo_path: str, trace_id: str) -> AgentResult:
        keyword = _extract_keyword(message)
        if not keyword:
            return AgentResult(
                answer="未提取到可搜索关键词，因此没有调用仓库工具。",
            )

        tool_result = self._tool_executor.search_code(
            repo_path=repo_path,
            keyword=keyword,
        )
        related_files = _unique_related_files(tool_result.results)

        if tool_result.error:
            answer = f"已尝试使用只读仓库工具搜索 `{keyword}`，但工具调用失败。"
        elif related_files:
            answer = f"已使用只读仓库工具搜索 `{keyword}`，找到相关文件。"
        else:
            answer = f"已使用只读仓库工具搜索 `{keyword}`，没有找到相关文件。"

        return AgentResult(
            answer=answer,
            related_files=related_files,
            tool_calls=[tool_result.call_summary()],
        )


def _extract_keyword(message: str) -> str:
    tokens = TOKEN_PATTERN.findall(message)
    if not tokens:
        return message.strip()

    for token in tokens:
        if "_" in token or "." in token or token.endswith("Error"):
            return token

    return tokens[0]


def _unique_related_files(results: list[dict[str, str | int]]) -> list[str]:
    related_files: list[str] = []
    seen: set[str] = set()

    for result in results:
        file_path = result.get("file_path")
        if not isinstance(file_path, str):
            continue
        if file_path in seen:
            continue
        related_files.append(file_path)
        seen.add(file_path)

    return related_files
