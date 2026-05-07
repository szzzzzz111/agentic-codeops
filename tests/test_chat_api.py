from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def valid_payload(
    repo_path: Path,
    message: str = "帮我分析 UNIQUE_BUG_TOKEN",
) -> dict[str, str]:
    return {
        "user_id": "u001",
        "session_id": "s001",
        "message": message,
        "repo_path": str(repo_path),
    }


def test_chat_endpoint_returns_tool_results_for_unique_keyword(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")

    response = client.post("/chat", json=valid_payload(tmp_path))

    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"].startswith("trace_")
    assert "UNIQUE_BUG_TOKEN" in body["answer"]
    assert body["related_files"] == ["app/service.py"]
    assert body["tool_calls"] == [
        {
            "tool_name": "search_code",
            "keyword": "UNIQUE_BUG_TOKEN",
            "status": "success",
            "result_count": "1",
        }
    ]


def test_chat_endpoint_returns_empty_related_files_when_keyword_is_missing(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "print('ok')\n")

    response = client.post("/chat", json=valid_payload(tmp_path))

    assert response.status_code == 200
    body = response.json()
    assert body["related_files"] == []
    assert body["tool_calls"] == [
        {
            "tool_name": "search_code",
            "keyword": "UNIQUE_BUG_TOKEN",
            "status": "success",
            "result_count": "0",
        }
    ]


def test_chat_endpoint_does_not_return_sensitive_file_content(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "UNIQUE_BUG_TOKEN = 'placeholder'\n")
    write_text(tmp_path / ".env", "UNIQUE_BUG_TOKEN=real-secret\n")

    response = client.post("/chat", json=valid_payload(tmp_path))

    assert response.status_code == 200
    body_text = response.text
    assert "real-secret" not in body_text
    body = response.json()
    assert ".env" not in body_text
    assert body["related_files"] == ["app.py"]
    assert body["tool_calls"] == [
        {
            "tool_name": "search_code",
            "keyword": "UNIQUE_BUG_TOKEN",
            "status": "success",
            "result_count": "1",
        }
    ]


def test_chat_endpoint_sanitizes_tool_errors(tmp_path: Path) -> None:
    missing_repo = tmp_path / "missing"

    response = client.post("/chat", json=valid_payload(missing_repo))

    assert response.status_code == 200
    body_text = response.text
    assert str(missing_repo) not in body_text
    assert response.json()["tool_calls"] == [
        {
            "tool_name": "search_code",
            "keyword": "UNIQUE_BUG_TOKEN",
            "status": "error",
            "result_count": "0",
            "error": "NotADirectoryError",
        }
    ]


def test_chat_endpoint_requires_repo_path_for_future_tool_compatibility() -> None:
    payload = {
        "user_id": "u001",
        "session_id": "s001",
        "message": "帮我分析 UNIQUE_BUG_TOKEN",
        "repo_path": "./mock_repo",
    }
    payload.pop("repo_path")

    response = client.post("/chat", json=payload)

    assert response.status_code == 422


def test_chat_endpoint_generates_unique_trace_ids(tmp_path: Path) -> None:
    first_response = client.post("/chat", json=valid_payload(tmp_path))
    second_response = client.post("/chat", json=valid_payload(tmp_path))

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["trace_id"] != second_response.json()["trace_id"]
