# Plan: V1 MVP Code Agent

## Files To Add

- `app/main.py`: create the FastAPI app and register routers.
- `app/__init__.py`: mark the app directory as a package.
- `app/api/chat.py`: expose the `POST /chat` endpoint.
- `app/api/__init__.py`: mark the API directory as a package.
- `app/schemas/chat.py`: define request and response models.
- `app/schemas/__init__.py`: mark the schemas directory as a package.
- `app/services/chat_service.py`: orchestrate trace creation and agent execution.
- `app/services/__init__.py`: mark the services directory as a package.
- `app/agents/code_agent.py`: return a mock analysis result.
- `app/agents/__init__.py`: mark the agents directory as a package.
- `app/observability/tracing.py`: generate request trace IDs.
- `app/observability/__init__.py`: mark the observability directory as a package.
- `tests/test_chat_api.py`: test the `/chat` endpoint.
- `pyproject.toml`: define project metadata, dependencies, pytest, and ruff configuration.
- `README.md`: document usage and roadmap.
- `.harness/*`: document lightweight coding and review rules.

## Core Functions And Classes

- `create_app()`: builds the FastAPI application.
- `chat()`: endpoint handler for `POST /chat`.
- `ChatRequest`: request payload schema.
- `ChatResponse`: response payload schema.
- `ChatService.handle_chat()`: coordinates one chat request.
- `CodeAgent.run()`: returns a mock agent result without reading the repo.
- `generate_trace_id()`: returns a unique trace identifier.

## Development Order

1. Create project directories.
2. Write specs and harness rules.
3. Define Pydantic schemas.
4. Implement trace ID generation.
5. Implement mock `CodeAgent`.
6. Implement `ChatService`.
7. Register `/chat` router in FastAPI.
8. Add pytest coverage.
9. Update README.
10. Run tests and ruff.

## Test Strategy

- Use FastAPI `TestClient`.
- Assert `/chat` returns HTTP 200 for a valid payload.
- Assert the response has a `trace_id` with the expected prefix.
- Assert two consecutive requests return different `trace_id` values.
- Assert the response preserves V1 fields: `answer`, `related_files`, `tool_calls`.
- Assert V1 does not return real tool calls or related files.
- Assert the mock answer mentions that V1 does not read `repo_path` yet.

## Future Extension Points

- V2 can add repository tools below `app/tools/` without changing the API contract.
- V3 can replace the mock `CodeAgent.run()` internals with a simple agent loop.
- V4 can add `app/skills/skill_loader.py` while keeping the service boundary stable.
- V5 can expand trace data while keeping `trace_id` in the response.
