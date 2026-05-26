from app.rag.evidence import DEFAULT_MAX_CONTEXT_CHARS, build_evidence_pack
from app.tools.tool_executor import ToolExecutionResult


def test_evidence_pack_builds_stable_items_without_absolute_paths() -> None:
    results = [
        {
            "file_path": "app/service.py",
            "start_line": 3,
            "end_line": 5,
            "score": 900,
            "line_text": "class PaymentService:\n    pass",
        },
        {
            "file_path": "C:/outside/secret.py",
            "start_line": 1,
            "end_line": 1,
            "score": 1000,
            "line_text": "SECRET = True",
        },
    ]

    first = build_evidence_pack(
        results,
        original_query="PaymentService 在哪里?",
        question_type="code_location",
        retrieval_mode="hybrid",
    )
    second = build_evidence_pack(
        results,
        original_query="PaymentService 在哪里?",
        question_type="code_location",
        retrieval_mode="hybrid",
    )

    assert first.original_query == "PaymentService 在哪里?"
    assert first.question_type == "code_location"
    assert first.retrieval_mode == "hybrid"
    assert len(first.items) == 1
    item = first.items[0]
    assert item.evidence_id == second.items[0].evidence_id
    assert item.file_path == "app/service.py"
    assert item.start_line == 3
    assert item.end_line == 5
    assert item.score == 900
    assert item.snippet == "class PaymentService:\n    pass"
    assert item.source_summary == "repo_rag:hybrid"
    assert item.included is True
    assert item.truncated is False


def test_context_budget_includes_omits_and_truncates_items() -> None:
    results = [
        {
            "file_path": "a.py",
            "start_line": 1,
            "end_line": 1,
            "score": 900,
            "line_text": "abc",
        },
        {
            "file_path": "b.py",
            "start_line": 1,
            "end_line": 1,
            "score": 800,
            "line_text": "defgh",
        },
        {
            "file_path": "c.py",
            "start_line": 1,
            "end_line": 1,
            "score": 700,
            "line_text": "ijk",
        },
    ]

    pack = build_evidence_pack(
        results,
        original_query="budget",
        question_type="unknown",
        retrieval_mode="hybrid",
        max_context_chars=5,
    )

    assert [item.file_path for item in pack.items] == ["a.py", "b.py", "c.py"]
    assert pack.items[0].snippet == "abc"
    assert pack.items[0].included is True
    assert pack.items[0].truncated is False
    assert pack.items[1].snippet == "de"
    assert pack.items[1].included is True
    assert pack.items[1].truncated is True
    assert pack.items[2].snippet == ""
    assert pack.items[2].included is False
    assert pack.items[2].truncated is False
    assert pack.budget.max_context_chars == 5
    assert pack.budget.budget_used_chars == 5
    assert pack.budget.budget_remaining_chars == 0
    assert pack.budget.included_count == 2
    assert pack.budget.omitted_count == 1
    assert pack.budget.truncated_count == 1


def test_evidence_pack_audit_summary_uses_fixed_keys() -> None:
    pack = build_evidence_pack(
        [
            {
                "file_path": "app.py",
                "start_line": 1,
                "end_line": 1,
                "score": 10,
                "line_text": "hello",
            }
        ],
        original_query="hello",
        question_type="unknown",
        retrieval_mode="hybrid",
    )

    assert pack.audit_summary() == {
        "evidence_items": 1,
        "included_count": 1,
        "omitted_count": 0,
        "truncated_count": 0,
        "budget_used_chars": 5,
        "max_context_chars": DEFAULT_MAX_CONTEXT_CHARS,
    }


def test_tool_execution_result_keeps_evidence_pack_out_of_call_summary() -> None:
    pack = build_evidence_pack(
        [],
        original_query="missing",
        question_type="unknown",
        retrieval_mode="hybrid",
    )
    result = ToolExecutionResult(
        tool_name="repo_rag",
        parameters={"keyword": "missing"},
        evidence_pack=pack,
    )

    assert "evidence_pack" not in result.call_summary()
