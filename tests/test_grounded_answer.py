from app.answering.grounded_answer import (
    FALLBACK_NO_EVIDENCE,
    GroundedAnswerGenerator,
    validate_answer_citations,
)
from app.providers.model_provider import ModelProviderResponse
from app.rag.evidence import build_evidence_pack


class StaticProvider:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.called = False

    def generate(self, request):
        self.called = True
        return ModelProviderResponse(
            answer=self.answer,
            audit_summary={
                "provider": "static",
                "model": "test",
                "status": "success",
            },
        )


class LeakyAuditProvider:
    def generate(self, request):
        return ModelProviderResponse(
            answer="PaymentService 实现了 capture_invoice。 app/service.py:10-12",
            audit_summary={
                "provider": "leaky",
                "model": "test",
                "status": "success",
                "prompt": "SECRET_PROMPT",
                "api_key": "SECRET_KEY",
                "raw_output": "SECRET_OUTPUT",
                "fallback_reason": "unused",
            },
        )


def evidence_pack():
    return build_evidence_pack(
        [
            {
                "file_path": "app/service.py",
                "start_line": 10,
                "end_line": 12,
                "line_text": "class PaymentService:\n    def capture_invoice(self):\n",
                "score": 9,
            }
        ],
        original_query="PaymentService 如何 capture_invoice?",
        question_type="implementation_explanation",
        retrieval_mode="hybrid",
    )


def empty_evidence_pack():
    return build_evidence_pack(
        [],
        original_query="MissingToken 是什么?",
        question_type="implementation_explanation",
        retrieval_mode="hybrid",
    )


def test_validate_answer_citations_accepts_provided_citations_with_punctuation() -> None:
    pack = evidence_pack()

    result = validate_answer_citations(
        "答案来自 app/service.py:10-12。",
        pack,
    )

    assert result.valid
    assert result.citations == ["app/service.py:10-12"]


def test_validate_answer_citations_rejects_absolute_or_unprovided_paths() -> None:
    pack = evidence_pack()

    absolute_result = validate_answer_citations(
        "答案来自 C:/repo/app/service.py:10-12",
        pack,
    )
    wrong_line_result = validate_answer_citations(
        "答案来自 app/service.py:10-99",
        pack,
    )

    assert not absolute_result.valid
    assert absolute_result.reason == "invalid_citation"
    assert not wrong_line_result.valid
    assert wrong_line_result.reason == "invalid_citation"


def test_validate_answer_citations_rejects_included_item_without_provider_snippet() -> None:
    pack = build_evidence_pack(
        [
            {
                "file_path": "app/empty.py",
                "start_line": 1,
                "end_line": 1,
                "line_text": "",
                "score": 1,
            }
        ],
        original_query="empty evidence?",
        question_type="implementation_explanation",
        retrieval_mode="hybrid",
    )

    result = validate_answer_citations("答案来自 app/empty.py:1-1", pack)

    assert not result.valid
    assert result.reason == "invalid_citation"


def test_grounded_answer_uses_provider_output_when_citations_are_valid() -> None:
    provider = StaticProvider("PaymentService 实现了 capture_invoice。 app/service.py:10-12")
    generator = GroundedAnswerGenerator(provider=provider)

    result = generator.generate(evidence_pack())

    assert provider.called
    assert result.answer == "PaymentService 实现了 capture_invoice。 app/service.py:10-12"
    assert result.audit_summary["provider"] == "static"
    assert result.audit_summary["status"] == "success"


def test_grounded_answer_redacts_unapproved_provider_audit_fields() -> None:
    generator = GroundedAnswerGenerator(provider=LeakyAuditProvider())

    result = generator.generate(evidence_pack())

    assert result.answer == "PaymentService 实现了 capture_invoice。 app/service.py:10-12"
    assert result.audit_summary == {
        "provider": "leaky",
        "model": "test",
        "status": "success",
    }
    assert "SECRET" not in str(result.audit_summary)


def test_grounded_answer_accepts_valid_citation_followed_by_punctuation() -> None:
    provider = StaticProvider("PaymentService 实现了 capture_invoice，见 app/service.py:10-12。")
    generator = GroundedAnswerGenerator(provider=provider)

    result = generator.generate(evidence_pack())

    assert result.answer == provider.answer
    assert result.audit_summary["status"] == "success"


def test_grounded_answer_does_not_call_provider_without_included_evidence() -> None:
    provider = StaticProvider("不应该调用 app/service.py:10-12")
    generator = GroundedAnswerGenerator(provider=provider)

    result = generator.generate(empty_evidence_pack())

    assert not provider.called
    assert result.answer == FALLBACK_NO_EVIDENCE
    assert result.audit_summary["fallback_reason"] == "no_evidence"


def test_grounded_answer_falls_back_when_provider_returns_no_citation() -> None:
    provider = StaticProvider("PaymentService 实现了 capture_invoice。")
    generator = GroundedAnswerGenerator(provider=provider)

    result = generator.generate(evidence_pack())

    assert result.answer != provider.answer
    assert result.audit_summary["fallback_reason"] == "missing_citation"


def test_grounded_answer_falls_back_when_provider_returns_invalid_citation() -> None:
    provider = StaticProvider("PaymentService 实现了 capture_invoice。 app/service.py:1-1")
    generator = GroundedAnswerGenerator(provider=provider)

    result = generator.generate(evidence_pack())

    assert result.answer != provider.answer
    assert result.audit_summary["fallback_reason"] == "invalid_citation"
