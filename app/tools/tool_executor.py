from dataclasses import dataclass, field

from app.tools.file_tools import search_code


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    parameters: dict[str, str]
    results: list[dict[str, str | int]] = field(default_factory=list)
    error: str | None = None

    def call_summary(self) -> dict[str, str]:
        summary = {
            "tool_name": self.tool_name,
            **self.parameters,
            "status": "error" if self.error else "success",
            "result_count": str(len(self.results)),
        }
        if self.error:
            summary["error"] = self.error
        return summary


class ToolExecutor:
    def search_code(
        self,
        repo_path: str,
        keyword: str,
        max_results: int = 20,
    ) -> ToolExecutionResult:
        try:
            results = search_code(
                repo_path=repo_path,
                keyword=keyword,
                max_results=max_results,
            )
        except (NotADirectoryError, OSError, ValueError) as exc:
            return ToolExecutionResult(
                tool_name="search_code",
                parameters={"keyword": keyword},
                error=type(exc).__name__,
            )

        return ToolExecutionResult(
            tool_name="search_code",
            parameters={"keyword": keyword},
            results=results,
        )
