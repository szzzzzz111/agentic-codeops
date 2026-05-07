# RepoPilot

RepoPilot is an Agentic CodeOps project for repository reading, bug analysis, and repair suggestions. The current V1 implementation is a small FastAPI service with a mock Code Agent, request-level trace IDs, and API tests.

## Current V1 Capability

- FastAPI app with `POST /chat`.
- Request schema with `user_id`, `session_id`, `message`, and `repo_path`.
- Mock `CodeAgent` response.
- Unique `trace_id` per request.
- Empty `related_files` and `tool_calls` placeholders for future tool integration.
- Pytest coverage for the chat endpoint.

## Start The API

```bash
uvicorn app.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u001",
    "session_id": "s001",
    "message": "Help me analyze why tests fail",
    "repo_path": "./mock_repo"
  }'
```

Example response:

```json
{
  "trace_id": "trace_xxx",
  "answer": "Mock analysis result: V1 received your request but does not read ./mock_repo. V2 will add list_files/read_file/search_code tools for safe repository analysis.",
  "related_files": [],
  "tool_calls": []
}
```

## Run Tests

```bash
pytest
```

Optional lint gate:

```bash
ruff check .
```

## V1 Architecture

```text
API -> ChatService -> CodeAgent -> Trace
```

- `app/main.py`: creates the FastAPI app and registers routers.
- `app/api/chat.py`: exposes the chat endpoint.
- `app/schemas/chat.py`: defines request and response schemas.
- `app/services/chat_service.py`: coordinates trace creation and agent execution.
- `app/agents/code_agent.py`: returns the mock analysis result.
- `app/observability/tracing.py`: generates trace IDs.

## Not In V1

- Real LLM integration.
- Real repository reading.
- `list_files`, `read_file`, or `search_code`.
- Skill Loader.
- Reflection.
- Eval.
- Automatic code modification.
- Complex Agent Loop.

## Roadmap

- V2: add safe repository tools: `list_files`, `read_file`, and `search_code`.
- V3: add a simple rule-based Agent Loop.
- V4: add Skill Loader with markdown skills.
- V5: expand trace records with tool calls and retrieved files.
- V6: add mini eval cases for repository debugging.
- V7: add Reflection checks for answer completeness.
- V8: explore RAG for larger repositories.
