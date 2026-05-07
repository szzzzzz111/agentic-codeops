# Test Commands

## Unit And API Tests

```bash
pytest
```

## Lint

```bash
ruff check .
```

## Local API Server

```bash
uvicorn app.main:app --reload
```

## Manual Chat Request

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
