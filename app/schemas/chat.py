from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    repo_path: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    trace_id: str
    answer: str
    related_files: list[str]
    tool_calls: list[dict[str, str]]
