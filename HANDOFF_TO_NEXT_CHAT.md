# 交接给下一轮 Chat

## 当前基线

- 当前分支：`main`
- Active OpenSpec change：无
- `revalidate-deepseek-provider-conformance` 已归档。
- `harden-grounded-prompt-injection-live-behavior` remediation 已归档并合入。
- 默认 pytest、CI 与 `scripts/verify.ps1` 仍保持离线 deterministic。
- 未创建 V24。

## 当前阶段

- 阶段目标：README 顶部“面试官版”门面优化 + Demo-ready Agent CLI 规划。
- README 顶部门面已完成；CLI 仍只做 planning，不直接实现 CLI runtime，不修改 `app/**`、`tests/**`、provider runtime、live eval profile、默认 Patch wiring、默认 CI 或 `/chat` contract。
- 风险级别：low。
- OpenSpec change 已归档：`openspec/changes/archive/2026-06-25-demo-ready-readme-cli-planning/`。
- Long-term specs 已同步：
  - `openspec/specs/demo-ready-agent-cli/spec.md`
  - `openspec/specs/harness-development-workflow/spec.md`
- 已同步：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 当前状态：archive 已完成，等待 commit/push；不创建 V24。

## 当前验证

- `openspec validate demo-ready-readme-cli-planning --strict`：passed。
- `openspec validate --all`：passed。
- `git diff --check`：passed，仅有 CRLF normalization warning。
- Focused regression：`pytest tests/test_chat_api.py::test_docs_keep_stage_route_map_consistent -q`，1 passed。
- Full verify：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` passed；pytest 400 passed、1 skipped；ruff passed；stage docs scan passed；skill eval structure scan passed。

## 上一轮 DeepSeek 结果

- DeepSeek `deepseek-v4-flash` renewed live gate 已 PASS。
- PASS attestation：`docs/evals/live-model-provider/20260624-124206.json`
- Tested commit：`8b018b84ae8c39eff3b18aeda98ac4a106b9d65d`
- Report SHA-256：`bd5010d556061fdb77243da16e4a305790f5416f3bcaa5a3382fe84d2170cdbb`
- Evidence shape：10 cases、8 provider calls、quality baseline 5/5。
- Provider-backed cases 均为 `availability=available`、`finish_reason=stop`、usage complete。
- No-answer 和 secret-filter 为 zero-call PASS。
- 同 run 未生成 failure record。

## 上一轮验证

- Post-remediation preflight：focused evaluator tests 64 passed；full verify 400 passed、1 skipped；OpenSpec all 20 passed。
- Archive 后：full `scripts/verify.ps1` 400 passed、1 skipped；OpenSpec all 19 passed、0 failed；stage docs 与 `git diff --check` 通过。
- Merge 到 `main` 后：full `scripts/verify.ps1` 400 passed、1 skipped；OpenSpec all 19 passed、0 failed；stage docs 与 `git diff --check` 通过。

## 下一步

- 若用户确认 closeout，下一步是 commit/push；当前已在 `main`，无需 merge。
- README 不得声明 `repopilot` CLI 已实现；CLI 只作为未来薄封装规划。
- 不修改 runtime、tests、live eval、provider runtime、默认 Patch wiring、默认 CI、`/chat` contract 或 V24。
- 继续前先检查：

  ```powershell
  git status --short --branch
  git log -5 --oneline --decorate
  openspec list
  ```
