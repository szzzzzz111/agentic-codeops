# Evaluated Failure Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and execute each task with review checkpoints.

**Goal:** 在不降低任何 live hard gate 或退出码的前提下，为完整可信但 conformance FAIL 的最终真实评测生成固定 allowlist tracked record，并允许 Change 2 以 evaluator readiness 语义归档。

**Architecture:** `core.py` 负责 gate 分类、failure record 构造、schema 校验与写入；`runner.py`
只在本地报告成功写入后，根据完整 run 的 gate 分类选择 PASS attestation、FAIL record 或无 tracked
evidence。历史报告不回填，最终证据必须来自实现提交后的 clean live run。

**Tech Stack:** Python 3.11、dataclasses、JSON、SHA-256、pytest、OpenSpec。

---

### Task 1: Failure Record Schema And Gate Classification

**Files:**
- Modify: `evals/live_model_provider/core.py`
- Test: `tests/test_live_model_provider_eval.py`

- [ ] 新增 RED tests：
  - `build_evaluated_failure_record()` 只返回以下 key：
    `schema_version`、`record_type`、`evaluation_status`、`conformance_status`、
    `evaluator_commit`、`evaluated_at`、`profile`、`rubric_version`、`failed_gates`、
    `local_report_sha256`。
  - `profile` 只包含 `provider`、`model`。
  - `failed_gates` 去重并按字典序排序。
  - API key、URL、prompt、answer、EvidencePack、diff、reasoning、fingerprint 均不出现。
  - 空 gate、未知 gate、PASS report、非 UTC 时间和非 64 位十六进制 hash 均 fail closed。

- [ ] 运行：

```powershell
pytest tests/test_live_model_provider_eval.py -q -k "evaluated_failure_record"
```

预期：因函数/常量尚不存在而 FAIL。

- [ ] 在 `core.py` 增加：

```python
CONFORMANCE_FAILURE_GATES = frozenset({
    "chat_citation_invalid",
    "chat_contract_invalid",
    "chat_status_invalid",
    "finish_reason_not_stop",
    "grounded_answer_invalid_citation",
    "grounded_answer_missing_citation",
    "grounded_answer_no_evidence",
    "grounded_answer_provider_error",
    "grounded_answer_unknown",
    "metrics_missing",
    "no_answer_called_provider",
    "no_answer_fallback_mismatch",
    "patch_pending_store_missing",
    "patch_proposal_invalid",
    "patch_was_applied",
    "planner_action_type_invalid",
    "planner_fallback",
    "planner_step_count_invalid",
    "planner_step_order_invalid",
    "prompt_injection_executed",
    "prompt_token_split_mismatch",
    "requested_model_mismatch",
    "returned_model_mismatch",
    "safe_control_missing_from_evidence_pack",
    "safe_control_missing_from_http_payload",
    "safe_control_missing_from_retrieval",
    "secret_in_evidence_pack",
    "secret_in_http_payload",
    "secret_in_retrieval",
    "total_token_count_mismatch",
    "usage_incomplete",
    "usage_negative",
})

INTEGRITY_FAILURE_GATES = frozenset({
    "api_subprocess_error",
    "api_subprocess_invalid_output",
    "api_subprocess_timeout",
    "call_count_invalid",
    "chat_call_count_invalid",
    "git_state_changed_during_live_run",
    "live_call_count_invalid",
    "patch_call_count_invalid",
    "planner_call_count_invalid",
    "run_timeout",
})

def build_evaluated_failure_record(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
) -> dict[str, object]:
    if report.status != "fail":
        raise ValueError("FAIL report required")
    if len(local_report_sha256) != 64 or any(
        char not in "0123456789abcdef"
        for char in local_report_sha256.casefold()
    ):
        raise ValueError("valid report SHA-256 required")
    if not report.completed_at.endswith("Z"):
        raise ValueError("UTC completion time required")
    failed_gates = conformance_failures_for_record(report.cases)
    return {
        "schema_version": "1",
        "record_type": "evaluated_failure",
        "evaluation_status": "complete",
        "conformance_status": "fail",
        "evaluator_commit": report.tested_commit,
        "evaluated_at": report.completed_at,
        "profile": {
            "provider": report.profile.provider,
            "model": report.profile.model,
        },
        "rubric_version": report.rubric_version,
        "failed_gates": failed_gates,
        "local_report_sha256": local_report_sha256.casefold(),
    }
```

构造结果固定为：

```python
{
    "schema_version": "1",
    "record_type": "evaluated_failure",
    "evaluation_status": "complete",
    "conformance_status": "fail",
    "evaluator_commit": report.tested_commit,
    "evaluated_at": report.completed_at,
    "profile": {
        "provider": report.profile.provider,
        "model": report.profile.model,
    },
    "rubric_version": report.rubric_version,
    "failed_gates": failed_gates,
    "local_report_sha256": local_report_sha256,
}
```

- [ ] GREEN 后运行完整 evaluator tests。

### Task 2: Integrity Classification And Writer

**Files:**
- Modify: `evals/live_model_provider/core.py`
- Test: `tests/test_live_model_provider_eval.py`

- [ ] 新增 RED tests：
  - Prompt Injection、citation、Planner/Patch schema、secret、finish reason、usage failure 可被分类为
    complete conformance FAIL。
  - `api_subprocess_error`、`api_subprocess_timeout`、`api_subprocess_invalid_output`、
    `run_timeout`、`call_count_invalid`、`chat_call_count_invalid`、`planner_call_count_invalid`、
    `patch_call_count_invalid`、`live_call_count_invalid`、`git_state_changed_during_live_run`
    和未知 gate 均为 integrity blocker。
  - 每一种单 case/整轮调用计数 gate 与任意 conformance gate 同时出现时，均不得构造
    evaluated-failure record。
  - Writer 路径为 `docs/evals/live-model-provider/failures/<UTC timestamp>.json`。
  - Writer 拒绝覆盖同名文件。
  - 现有 `write_local_report()` 与 `write_attestation()` 同样拒绝覆盖同名文件。

- [ ] 实现：

```python
def conformance_failures_for_record(cases: list[CaseResult]) -> list[str]:
    failures = {
        failure
        for case in cases
        for failure in case.hard_gate_failures
    }
    if not failures:
        raise ValueError("at least one conformance failure required")
    unknown = failures - CONFORMANCE_FAILURE_GATES - INTEGRITY_FAILURE_GATES
    if unknown:
        raise ValueError("unknown failure gate")
    if failures & INTEGRITY_FAILURE_GATES:
        raise ValueError("evaluation integrity failure")
    return sorted(failures)

def write_evaluated_failure_record(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
    docs_root: Path,
) -> Path:
    payload = build_evaluated_failure_record(
        report,
        local_report_sha256=local_report_sha256,
    )
    failure_root = docs_root / "failures"
    failure_root.mkdir(parents=True, exist_ok=True)
    file_name = report.completed_at.replace(":", "").replace("-", "")
    file_name = file_name.replace("T", "-").replace("Z", "")
    path = failure_root / f"{file_name}.json"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )
    return path
```

未知或 integrity gate 必须抛出 `ValueError`，不得静默忽略。

- [ ] 把 `write_local_report()` 与 `write_attestation()` 从覆盖式 `write_bytes/write_text` 改为
  `path.open("x", ...)`；任何 collision 作为 evaluator internal/integrity failure，不生成其他
  tracked evidence。

### Task 3: Runner Evidence Selection

**Files:**
- Modify: `evals/live_model_provider/runner.py`
- Test: `tests/test_live_model_provider_eval.py`

- [ ] 扩展 `LiveEvaluationOutcome`：

```python
failure_record_path: Path | None = None
```

- [ ] 新增 RED orchestration tests：
  - simulated PASS：退出 0，只写 attestation。
  - trustworthy Prompt Injection FAIL：退出 1，不写 attestation，写 failure record。
  - API subprocess failure、timeout、任一单 case/整轮 call-count gate 或 Git state failure：
    退出 1，不写任一 tracked evidence。
  - SKIP：退出 0，无 tracked evidence。
  - internal exception：退出 2，无 tracked evidence。
  - PASS branch 明确断言 `failure_record_path is None`；FAIL branch 明确断言
    `attestation_path is None`。

- [ ] 修改 runner：
  1. 始终先写本地脱敏报告并获得 hash。
  2. PASS 调用 `write_attestation()`。
  3. FAIL 调用 gate classifier；只有完整 conformance FAIL 才调用
     `write_evaluated_failure_record()`。
  4. CLI 对可信 FAIL 额外打印 `failure_record=<path>`，仍返回 1。

### Task 4: Deterministic Verification And Formal Review

**Files:**
- Modify: `.harness/review_checklist.md`
- Modify: `docs/PROGRESS.md`
- Modify: `HANDOFF_TO_NEXT_CHAT.md`

- [ ] 运行：

```powershell
pytest tests/test_live_model_provider_eval.py -q
pytest tests/test_live_model_provider_eval.py tests/test_model_provider.py tests/test_grounded_answer.py tests/test_long_task.py tests/test_patch_authoring.py tests/test_chat_api.py tests/test_repo_rag.py tests/test_evidence_pack.py -q
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
openspec validate add-live-model-provider-eval --strict
openspec validate --all
git diff --check
```

- [ ] Internal review、independent adversarial external review 与 Stage Debt Sweep 必须覆盖：
  gate misclassification、未知 gate fail-closed、schema 泄漏、PASS/FAIL evidence 互斥、历史证据回填、
  文件覆盖和 archive/certification 文案。

### Task 5: Final Live Evidence And Archive

**Files:**
- Create on trustworthy FAIL: `docs/evals/live-model-provider/failures/<timestamp>.json`
- Or create on PASS: `docs/evals/live-model-provider/<timestamp>.json`

- [ ] 先提交最终 evaluator，确认 tracked tree clean，再运行完整 live gate。
- [ ] 不使用第六次或更早的本地报告回填 tracked evidence。
- [ ] 若 PASS：提交 attestation 并复核 hash/commit/profile/rubric/metrics。
- [ ] 若可信 FAIL：提交 failure record，复核 exact schema、hash、commit、UTC、provider/model、
  rubric 和失败 gate；文档明确 `deepseek-v4-flash` 未通过对应 conformance gate。
- [ ] 若 SKIP 或 integrity failure：保持 active，不归档。
- [ ] 归档、合并、推送只代表 evaluator readiness；不得写成 provider certification。
