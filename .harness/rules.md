# Harness Rules

## V1 Scope

V1 is limited to a runnable FastAPI skeleton with a mock Code Agent. The API accepts `repo_path` for compatibility, but no code may read files from that path in V1.

## Layering

Use this boundary:

```text
API -> Service -> Agent -> Trace
```

- API handles HTTP only.
- Service coordinates request handling.
- Agent owns analysis behavior.
- Trace owns trace ID generation.

## Forbidden In V1

- Real LLM calls.
- Repository file reads.
- `list_files`, `read_file`, or `search_code`.
- Skill Loader.
- Reflection.
- Evals.
- Complex Agent Loop.
- Automatic code modification.
- Hardcoded API keys or secrets.
