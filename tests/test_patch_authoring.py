from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.patching.apply import apply_unified_diff
from app.patching.manager import PatchManager
from app.patching.parser import parse_patch_confirmation, parse_patch_verify_confirmation
from app.patching.provider import (
    ModelPatchAuthoringProvider,
    PatchAuthoringProviderRequest,
    PatchAuthoringProviderResponse,
)
from app.patching.store import SQLitePatchStore
from app.providers.model_provider import ModelProviderResponse


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class StaticPatchProvider:
    def __init__(self, response: PatchAuthoringProviderResponse) -> None:
        self.response = response

    def generate_patch(self, request):
        return self.response


class RecordingModelProvider:
    def __init__(self, response: ModelProviderResponse) -> None:
        self.response = response
        self.request = None

    def generate(self, request):
        self.request = request
        return self.response


def test_parse_patch_confirmation_accepts_only_explicit_syntax() -> None:
    assert parse_patch_confirmation("应用 patch patch_20260531_abcdef") == (
        "patch_20260531_abcdef"
    )
    assert parse_patch_confirmation("confirm patch patch_20260531_abcdef") == (
        "patch_20260531_abcdef"
    )
    assert parse_patch_confirmation("可以") is None
    assert parse_patch_confirmation("继续 patch_20260531_abcdef") is None


def test_model_patch_provider_uses_single_source_structured_instruction() -> None:
    model_provider = RecordingModelProvider(
        ModelProviderResponse(
            answer=(
                '{"summary":"update app","target_files":["app.py"],'
                '"diff":"--- a/app.py\\n+++ b/app.py\\n",'
                '"citations":["app.py:1-1"]}'
            ),
            audit_summary={"provider": "recording", "status": "success"},
        )
    )
    provider = ModelPatchAuthoringProvider(model_provider)

    response = provider.generate_patch(
        PatchAuthoringProviderRequest(
            original_query="请修改 app.py",
            question_type="implementation_explanation",
            evidence=[
                {
                    "file_path": "app.py",
                    "start_line": 1,
                    "end_line": 1,
                    "snippet": "old",
                }
            ],
        )
    )

    request = model_provider.request
    assert request is not None
    assert request.output_mode == "json_object"
    assert request.structured_output is not None
    assert request.structured_output.name == "patch_proposal"
    assert request.structured_output.max_output_tokens == 8000
    assert '"target_files"' in request.structured_output.json_example
    assert request.original_query == "请修改 app.py"
    assert "请只返回 JSON" not in request.original_query
    assert response.summary == "update app"


def test_parse_patch_verify_confirmation_requires_patch_id_and_label() -> None:
    parsed = parse_patch_verify_confirmation("确认 patch patch_20260531_abcdef 并运行验证")

    assert parsed.handled is True
    assert parsed.patch_id == "patch_20260531_abcdef"
    assert parsed.command_label == "verify"
    assert parsed.rejected is False

    parsed_pytest = parse_patch_verify_confirmation(
        "apply patch patch_20260531_abcdef and run pytest"
    )
    assert parsed_pytest.handled is True
    assert parsed_pytest.patch_id == "patch_20260531_abcdef"
    assert parsed_pytest.command_label == "pytest"


def test_parse_patch_verify_confirmation_rejects_half_parse_without_apply() -> None:
    missing_label = parse_patch_verify_confirmation(
        "确认 patch patch_20260531_abcdef 并运行"
    )
    unsafe_label = parse_patch_verify_confirmation(
        "确认 patch patch_20260531_abcdef 并运行 pytest tests/test_chat_api.py"
    )
    shell_syntax = parse_patch_verify_confirmation(
        "confirm patch patch_20260531_abcdef and run verify | more"
    )

    assert missing_label.handled is True
    assert missing_label.rejected is True
    assert missing_label.reason == "missing_verification_label"
    assert unsafe_label.handled is True
    assert unsafe_label.rejected is True
    assert unsafe_label.reason == "not_whitelisted"
    assert shell_syntax.handled is True
    assert shell_syntax.rejected is True
    assert shell_syntax.reason == "unsafe_syntax"
    assert parse_patch_confirmation("确认 patch patch_20260531_abcdef") == (
        "patch_20260531_abcdef"
    )


def test_pending_patch_store_scopes_by_user_repo_and_expires(tmp_path: Path) -> None:
    store = SQLitePatchStore.for_repo(tmp_path)
    patch = store.create_pending_patch(
        user_id="u001",
        repo_key="repo_a",
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n",
        summary="update app",
    )

    assert store.get_patch(
        patch.patch_id,
        user_id="u002",
        repo_key="repo_a",
    ) is None
    assert store.get_patch(
        patch.patch_id,
        user_id="u001",
        repo_key="repo_a",
    ) == patch
    assert patch.expires_at > datetime.now(tz=UTC)


def test_apply_unified_diff_rejects_path_traversal_and_sensitive_files(
    tmp_path: Path,
) -> None:
    traversal = "--- a/../outside.py\n+++ b/../outside.py\n@@ -1 +1 @@\n-old\n+new\n"
    sensitive = "--- a/.env\n+++ b/.env\n@@ -1 +1 @@\n-old\n+new\n"

    traversal_result = apply_unified_diff(tmp_path, traversal)
    sensitive_result = apply_unified_diff(tmp_path, sensitive)

    assert traversal_result.applied is False
    assert traversal_result.error == "unsafe_path"
    assert sensitive_result.applied is False
    assert sensitive_result.error == "unsafe_path"


def test_apply_unified_diff_preflight_failure_does_not_write_any_file(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "a.py", "old a\n")
    write_text(tmp_path / "b.py", "old b\n")
    diff = (
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1 +1 @@\n"
        "-old a\n"
        "+new a\n"
        "--- a/b.py\n"
        "+++ b/b.py\n"
        "@@ -1 +1 @@\n"
        "-missing b\n"
        "+new b\n"
    )

    result = apply_unified_diff(tmp_path, diff)

    assert result.applied is False
    assert result.error == "context_mismatch"
    assert (tmp_path / "a.py").read_text(encoding="utf-8") == "old a\n"
    assert (tmp_path / "b.py").read_text(encoding="utf-8") == "old b\n"


def test_patch_manager_creates_pending_patch_from_valid_provider_response(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "old\n")
    provider = StaticPatchProvider(
        PatchAuthoringProviderResponse(
            summary="update app",
            target_files=["app.py"],
            diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
            citations=["app.py:1-1"],
            audit_summary={"provider": "static", "status": "success"},
        )
    )
    manager = PatchManager(provider=provider)

    result = manager.propose_patch(
        user_id="u001",
        repo_path=str(tmp_path),
        message="请生成 patch 修改 app.py",
        evidence_pack=_fake_evidence_pack(),
    )

    assert result.handled is True
    assert result.patch_id.startswith("patch_")
    assert "确认 patch" in result.answer
    assert "--- a/app.py" not in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "old\n"


def test_patch_manager_redacts_absolute_paths_from_provider_summary(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "old\n")
    provider = StaticPatchProvider(
        PatchAuthoringProviderResponse(
            summary=r"update C:\Users\50805\secret.py",
            target_files=["app.py"],
            diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
            citations=["app.py:1-1"],
            audit_summary={"provider": "static", "status": "success"},
        )
    )
    manager = PatchManager(provider=provider)

    result = manager.propose_patch(
        user_id="u001",
        repo_path=str(tmp_path),
        message="请生成 patch 修改 app.py",
        evidence_pack=_fake_evidence_pack(),
    )

    assert result.handled is True
    assert r"C:\Users\50805\secret.py" not in result.answer
    assert "[redacted-path]" in result.answer
    assert "--- a/app.py" not in result.answer


def test_patch_manager_rejects_unsafe_diff_before_creating_pending_patch(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "old\n")
    provider = StaticPatchProvider(
        PatchAuthoringProviderResponse(
            summary="update env",
            target_files=[".env"],
            diff_text="--- a/.env\n+++ b/.env\n@@ -1 +1 @@\n-old\n+new\n",
            citations=["app.py:1-1"],
            audit_summary={"provider": "static", "status": "success"},
        )
    )
    manager = PatchManager(provider=provider)

    result = manager.propose_patch(
        user_id="u001",
        repo_path=str(tmp_path),
        message="请生成 patch 修改 app.py",
        evidence_pack=_fake_evidence_pack(),
    )

    assert result.handled is True
    assert result.patch_id is None
    assert "provider 输出未通过校验" in result.answer
    assert not (tmp_path / ".repopilot" / "patches.sqlite3").exists()


def test_patch_manager_rejects_expired_patch_before_apply(tmp_path: Path) -> None:
    write_text(tmp_path / "app.py", "old\n")
    store = SQLitePatchStore.for_repo(tmp_path)
    patch = store.create_pending_patch(
        user_id="u001",
        repo_key=_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
        expires_at=datetime.now(tz=UTC) - timedelta(seconds=1),
    )
    manager = PatchManager()

    command = manager.prepare_apply(
        user_id="u001",
        repo_path=str(tmp_path),
        message=f"确认 patch {patch.patch_id}",
    )

    assert command.handled is True
    assert command.context is not None
    assert command.context.expires_at_valid is False
    assert "已过期" in command.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "old\n"


def _repo_key(path: Path) -> str:
    from app.memory.store import compute_repo_key

    return compute_repo_key(path)


def _fake_evidence_pack():
    from app.rag.evidence import build_evidence_pack

    return build_evidence_pack(
        [
            {
                "file_path": "app.py",
                "start_line": 1,
                "end_line": 1,
                "line_text": "old",
            }
        ],
        original_query="请生成 patch 修改 app.py",
        question_type="implementation_explanation",
        retrieval_mode="hybrid",
    )
