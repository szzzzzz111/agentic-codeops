import os
from pathlib import Path

from app.memory.manager import MemoryManager
from app.memory.store import (
    InMemorySessionMemoryStore,
    SQLiteMemoryStore,
    compute_repo_key,
    normalize_repo_path_for_key,
)


def test_sqlite_memory_store_upserts_lists_and_deletes_ltm(tmp_path: Path) -> None:
    store = SQLiteMemoryStore.for_repo(tmp_path)
    repo_key = compute_repo_key(tmp_path)

    first = store.upsert(
        kind="LTM",
        user_id="u001",
        repo_key=repo_key,
        session_id=None,
        key="architecture",
        value="RepoPilot uses AgentLoop",
    )
    second = store.upsert(
        kind="LTM",
        user_id="u001",
        repo_key=repo_key,
        session_id=None,
        key="architecture",
        value="RepoPilot uses AgentLoop with Memory",
    )

    memories = store.list(
        kind="LTM",
        user_id="u001",
        repo_key=repo_key,
        session_id=None,
    )
    assert first.replaced is False
    assert second.replaced is True
    assert [(item.key, item.value) for item in memories] == [
        ("architecture", "RepoPilot uses AgentLoop with Memory")
    ]

    assert store.delete(
        kind="LTM",
        user_id="u001",
        repo_key=repo_key,
        session_id=None,
        query="architecture",
    ) == 1
    assert (
        store.list(kind="LTM", user_id="u001", repo_key=repo_key, session_id=None)
        == []
    )


def test_memory_scope_isolates_user_repo_and_session(tmp_path: Path) -> None:
    repo_a_path = tmp_path / "repo_a"
    repo_b_path = tmp_path / "repo_b"
    repo_a_path.mkdir()
    repo_b_path.mkdir()
    store = SQLiteMemoryStore.for_repo(repo_a_path)
    repo_a = compute_repo_key(repo_a_path)
    repo_b = compute_repo_key(repo_b_path)

    store.upsert(
        kind="LTM",
        user_id="u001",
        repo_key=repo_a,
        session_id=None,
        key="stack",
        value="FastAPI",
    )
    store.upsert(
        kind="LTM",
        user_id="u001",
        repo_key=repo_b,
        session_id=None,
        key="stack",
        value="Django",
    )
    store.upsert(
        kind="LTM",
        user_id="u002",
        repo_key=repo_a,
        session_id=None,
        key="stack",
        value="Flask",
    )

    assert [
        item.value
        for item in store.list(
            kind="LTM",
            user_id="u001",
            repo_key=repo_a,
            session_id=None,
        )
    ] == ["FastAPI"]

    sessions = InMemorySessionMemoryStore()
    sessions.upsert(user_id="u001", session_id="s001", key="topic", value="memory")
    sessions.upsert(user_id="u001", session_id="s002", key="topic", value="rag")

    assert [item.value for item in sessions.list(user_id="u001", session_id="s001")] == [
        "memory"
    ]


def test_repo_key_normalizes_resolved_paths_and_redacts_absolute_path(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "Repo"
    repo.mkdir()

    normalized = normalize_repo_path_for_key(repo)
    assert "\\" not in normalized
    if os.name == "nt":
        assert normalized == normalized.lower()

    manager = MemoryManager()
    result = manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=repo,
        message="记住：project:stack=FastAPI",
    )

    assert result.handled is True
    assert str(repo.resolve()) not in result.audit_summary
    assert "memory.sqlite3" not in result.audit_summary
    assert "repo_key_present=true" in result.audit_summary


def test_memory_parser_supports_colons_languages_and_classification(
    tmp_path: Path,
) -> None:
    manager = MemoryManager()

    pref = manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住：pref:language=中文",
    )
    project = manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="remember: project:framework=FastAPI",
    )
    note = manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="请记住以后默认用中文回答",
    )
    polite_pref = manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="请记住：pref:tone=简洁",
    )
    stm = manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住：stm:topic=V13 Memory review",
    )

    assert pref.handled is True
    assert pref.answer == "已记住偏好：language。"
    assert "kind=PREF" in pref.audit_summary
    assert project.answer == "已记住项目记忆：framework。"
    assert "kind=LTM" in project.audit_summary
    assert note.handled is True
    assert "kind=PREF" in note.audit_summary
    assert polite_pref.answer == "已记住偏好：tone。"
    assert stm.answer == "已记住会话记忆：topic。"
    assert "kind=STM" in stm.audit_summary
    assert "V13 Memory review" not in stm.audit_summary


def test_stm_memory_is_written_and_summarized_by_session(tmp_path: Path) -> None:
    manager = MemoryManager()

    manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住：stm:topic=memory review",
    )

    same_session = manager.summarize_for_request(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
    )
    other_session = manager.summarize_for_request(
        user_id="u001",
        session_id="s002",
        repo_path=tmp_path,
    )

    assert "stm_count=1" in same_session
    assert "stm_count=0" in other_session


def test_memory_delete_prefers_key_then_content_match(tmp_path: Path) -> None:
    manager = MemoryManager()
    manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住: pref:language=中文",
    )
    manager.remember(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="记住: project:framework=FastAPI",
    )

    deleted_key = manager.forget(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="forget: language",
    )
    deleted_content = manager.forget(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="忘记：FastAPI",
    )
    deleted_polite = manager.forget(
        user_id="u001",
        session_id="s001",
        repo_path=tmp_path,
        message="请忘记：missing",
    )

    assert deleted_key.answer == "已删除 1 条记忆。"
    assert deleted_content.answer == "已删除 1 条记忆。"
    assert deleted_polite.answer == "已删除 0 条记忆。"
    assert "deleted_count=1" in deleted_key.audit_summary
    assert "FastAPI" not in deleted_content.audit_summary
