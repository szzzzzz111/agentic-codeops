import httpx

from app.providers.model_provider import (
    FakeModelProvider,
    ModelProviderRequest,
    OpenAICompatibleModelProvider,
    load_model_provider_from_env,
)


def provider_request() -> ModelProviderRequest:
    return ModelProviderRequest(
        original_query="PaymentService 如何 capture_invoice?",
        question_type="implementation_explanation",
        evidence=[
            {
                "file_path": "app/service.py",
                "start_line": 10,
                "end_line": 12,
                "snippet": "class PaymentService:\n    def capture_invoice(self):\n",
            }
        ],
    )


def test_fake_model_provider_returns_stable_cited_answer() -> None:
    provider = FakeModelProvider()

    first = provider.generate(provider_request())
    second = provider.generate(provider_request())

    assert first.answer == second.answer
    assert "app/service.py:10-12" in first.answer
    assert first.audit_summary == {
        "provider": "fake",
        "model": "deterministic-fake",
        "status": "success",
    }


def test_openai_compatible_provider_sends_minimal_chat_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["json"] = request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "PaymentService 定义了 capture_invoice。"
                                " app/service.py:10-12"
                            )
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleModelProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="mimo-test",
        client=client,
    )

    response = provider.generate(provider_request())

    assert captured["url"] == "https://example.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer secret-key"
    assert "secret-key" not in str(response.audit_summary)
    assert "PaymentService" in response.answer
    assert response.audit_summary["provider"] == "openai_compatible"
    assert response.audit_summary["model"] == "mimo-test"
    assert response.audit_summary["status"] == "success"


def test_openai_compatible_provider_returns_sanitized_error_summary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "quota secret-key"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleModelProvider(
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="mimo-test",
        client=client,
    )

    response = provider.generate(provider_request())

    assert response.answer == ""
    assert response.audit_summary == {
        "provider": "openai_compatible",
        "model": "mimo-test",
        "status": "error",
        "error_class": "HTTPStatusError",
    }
    assert "secret-key" not in str(response.audit_summary)


def test_provider_factory_defaults_to_fake_without_env(monkeypatch) -> None:
    monkeypatch.delenv("REPOPILOT_MODEL_PROVIDER", raising=False)

    provider = load_model_provider_from_env()

    assert isinstance(provider, FakeModelProvider)


def test_provider_factory_requires_openai_compatible_config(monkeypatch) -> None:
    monkeypatch.setenv("REPOPILOT_MODEL_PROVIDER", "openai_compatible")
    monkeypatch.delenv("REPOPILOT_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("REPOPILOT_MODEL_API_KEY", raising=False)
    monkeypatch.delenv("REPOPILOT_MODEL_NAME", raising=False)

    provider = load_model_provider_from_env()
    response = provider.generate(provider_request())

    assert response.answer == ""
    assert response.audit_summary["status"] == "error"
    assert response.audit_summary["error_class"] == "ProviderConfigError"
