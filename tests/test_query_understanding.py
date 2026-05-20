from app.rag.query_understanding import (
    QUESTION_CODE_LOCATION,
    QUESTION_IMPLEMENTATION_EXPLANATION,
    QUESTION_TEST_OR_VALIDATION,
    QueryUnderstanding,
)


def test_query_understanding_extracts_file_symbol_and_question_type() -> None:
    plan = QueryUnderstanding().build_search_plan(
        "AgentLoop 在 app/harness/kernel.py 里怎么调用 search_code?"
    )

    assert plan.question_type == QUESTION_IMPLEMENTATION_EXPLANATION
    assert "AgentLoop" in plan.symbols
    assert "search_code" in plan.symbols
    assert "app/harness/kernel.py" in plan.path_hints
    assert plan.max_results == 8
    assert plan.retrieval_mode == "lexical"


def test_query_understanding_classifies_location_and_error_questions() -> None:
    location_plan = QueryUnderstanding().build_search_plan(
        "UNIQUE_BUG_TOKEN 在哪个文件?"
    )
    error_plan = QueryUnderstanding().build_search_plan(
        "NotADirectoryError 是哪里处理的?"
    )

    assert location_plan.question_type == QUESTION_CODE_LOCATION
    assert "UNIQUE_BUG_TOKEN" in location_plan.symbols
    assert error_plan.question_type == QUESTION_CODE_LOCATION
    assert "NotADirectoryError" in error_plan.symbols


def test_query_understanding_classifies_test_questions_without_vector_mode() -> None:
    plan = QueryUnderstanding().build_search_plan("怎么验证 PermissionPolicy 的测试?")

    assert plan.question_type == QUESTION_TEST_OR_VALIDATION
    assert "PermissionPolicy" in plan.symbols
    assert plan.retrieval_mode == "lexical"
    assert "embedding" not in plan.keywords
    assert "vector" not in plan.keywords
