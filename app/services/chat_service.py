from app.agents.code_agent import CodeAgent
from app.observability.tracing import generate_trace_id
from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    def __init__(self, agent: CodeAgent | None = None) -> None:
        self._agent = agent or CodeAgent()

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        trace_id = generate_trace_id()
        result = self._agent.run(
            message=request.message,
            repo_path=request.repo_path,
            trace_id=trace_id,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        return ChatResponse(
            trace_id=trace_id,
            answer=result.answer,
            related_files=result.related_files,
            tool_calls=result.tool_calls,
        )
