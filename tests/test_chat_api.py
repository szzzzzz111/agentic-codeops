from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def valid_payload() -> dict[str, str]:
    return {
        "user_id": "u001",
        "session_id": "s001",
        "message": "Help me analyze why tests fail",
        "repo_path": "./mock_repo",
    }


def test_chat_endpoint_returns_mock_analysis() -> None:
    response = client.post("/chat", json=valid_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"].startswith("trace_")
    assert body["answer"].startswith("Mock analysis result")
    assert "does not read ./mock_repo" in body["answer"]
    assert "list_files/read_file/search_code" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []


def test_chat_endpoint_requires_repo_path_for_future_tool_compatibility() -> None:
    payload = valid_payload()
    payload.pop("repo_path")

    response = client.post("/chat", json=payload)

    assert response.status_code == 422


def test_chat_endpoint_generates_unique_trace_ids() -> None:
    first_response = client.post("/chat", json=valid_payload())
    second_response = client.post("/chat", json=valid_payload())

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["trace_id"] != second_response.json()["trace_id"]
