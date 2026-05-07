# Spec: V1 MVP Code Agent

## Project Goal

RepoPilot is an Agentic CodeOps project for repository reading, bug analysis, and repair suggestions. The V1 scope is a runnable FastAPI skeleton that keeps clean extension points for later repository tools, skills, traces, evals, and reflection.

## V1 Goal

Build the smallest working API loop:

- FastAPI app starts successfully.
- `POST /chat` accepts `user_id`, `session_id`, `message`, and `repo_path`.
- The service returns a mock code analysis result.
- Every request receives a `trace_id`.
- The response includes `trace_id`, `answer`, `related_files`, and `tool_calls`.
- Pytest covers the `/chat` endpoint.
- Consecutive requests receive different `trace_id` values.

## Request Contract

`POST /chat`

```json
{
  "user_id": "u001",
  "session_id": "s001",
  "message": "Help me analyze why tests fail",
  "repo_path": "./mock_repo"
}
```

## Response Contract

```json
{
  "trace_id": "trace_xxx",
  "answer": "Mock analysis result: V1 does not read ./mock_repo yet. V2 will add list_files/read_file/search_code tools.",
  "related_files": [],
  "tool_calls": []
}
```

## Architecture Boundary

The V1 flow is:

```text
API -> ChatService -> CodeAgent -> Trace
```

Responsibilities:

- API layer receives HTTP requests and returns schema objects.
- Service layer creates `trace_id` and coordinates the agent call.
- Agent layer returns the mock analysis result.
- Trace layer generates trace identifiers.

## Explicit Non-Goals

V1 does not:

- Connect to a real LLM.
- Read files from `repo_path`.
- Implement `list_files`, `read_file`, or `search_code`.
- Implement Skill Loader.
- Implement Reflection.
- Implement evals.
- Implement a complex Agent Loop.
- Modify repository code automatically.
- Put all logic into `main.py`.

## Acceptance Criteria

- `uvicorn app.main:app --reload` can start the API.
- `POST /chat` accepts the V1 request fields.
- The response includes `trace_id`, `answer`, `related_files`, and `tool_calls`.
- `related_files` and `tool_calls` are empty lists in V1.
- Two consecutive requests return different `trace_id` values.
- The mock answer mentions that V1 does not read `repo_path` and that V2 will add repository tools.
- `pytest` passes.
- `ruff` is available as a quality gate.
- README documents current capability and roadmap.
