# 当前 Review 清单

当前无 active OpenSpec change。最近归档 change：`polish-demo-cli-capability-surface`。

## Planning gate

- [x] 当前分支已切到 `codex/polish-demo-cli-capability-surface`。
- [x] 起始 `main` 工作树干净，最近提交为 `b7fcbcd Add demo-ready RepoPilot CLI`。
- [x] 起始 `openspec list` 为 No active changes found。
- [x] 风险级别判定为 `medium`：用户可见 CLI surface 和流程 skill 变更，但不改 public API、
  provider、CI、Patch wiring、promotion 或核心 runtime。
- [x] 已创建 OpenSpec artifacts 和 spec deltas。
- [x] 已同步 `.harness/allowed_files.md`，实现前只开放 CLI、tests、workflow skills、
  OpenCode review entry、相关 docs/specs/harness。
- [x] 完成内部 plan review：proposal、design、tasks、spec deltas、test plan、Harness 边界互相一致。
- [x] 完成 Codex independent plan review，并 triage findings。
- [x] 完成 OpenCode independent plan review；终端超时后已从 OpenCode session final text 取证，
  并 triage findings。
- [x] `openspec validate polish-demo-cli-capability-surface --strict` 通过。
- [x] `openspec validate --all` 通过：21 passed，0 failed。

## CLI implementation review target

- [x] `repopilot` console entrypoint 仍只调用现有 `ChatService.handle_chat()`，不重写 AgentLoop。
- [x] `repopilot patch "<request>"` 精确映射为 `create patch: <request>`，稳定触发现有 patch proposal intent。
- [x] `patch confirm` 和 `patch confirm --verify` 仍只映射到现有明确确认语义。
- [x] patch id validator 为 `^patch_[A-Za-z0-9_]{1,122}$`，与 runtime confirmation parser 兼容且保留总长上限。
- [x] `verify` label 只允许 `verify`、`pytest`、`ruff`。
- [x] empty required values、unsafe patch id、shell-like syntax、管道、重定向、环境变量赋值、extra args 在调用 `ChatService` 前拒绝。
- [x] CLI 输出只使用公开 `trace_id`、`answer`、`related_files`、`tool_calls`，不读取内部 Evidence Pack 或新增 citation/schema。
- [x] CLI 不新增网络依赖，不读取 provider key，不修改 live eval、default Patch wiring、默认 CI 或 `/chat` contract。
- [x] CLI 不实现 Verified Patch Promotion、commit、merge、push、branch management、PR creation、runtime subagents 或 connectors。

## Workflow skill review target

- [x] `openspec-stage-planner` 明确 medium/high stage 实现前需要 internal、Codex independent、OpenCode independent plan review。
- [x] `repo-stage-workflow` / `workflow-contract` 区分 plan-level review 和 final implementation review。
- [x] `repo-stage-review-loop` 支持 review plan contract，不只 review final implementation。
- [x] `external-review-triage` 明确 external plan findings 也按 `fix`、`clarify`、`reject`、`defer` 分类。
- [x] OpenCode workflow entry 记录优先复用已有 review session：先 `opencode session list`，再
  `opencode run --session <session_id> ...`。
- [x] OpenCode terminal timeout 后必须检查 session final assistant review text；没有 final text 时默认 blocker，
  除非用户明确降级授权。
- [x] Skill/process wording 不把 OpenSpec、Superpowers、MCP、plugin、Codex/OpenCode skills 写成 RepoPilot runtime。

## Docs truthfulness target

- [x] README CLI walkthrough 可在默认 deterministic 配置下解释清楚。
- [x] README/ARCHITECTURE/PROGRESS/HANDOFF/specs 明确 V24 为 CLI Capability Surface，原 Verified Patch
  Promotion 顺延为 V25/backlog。
- [x] 文档不声称默认真实 model patch authoring、promotion、commit/push、runtime subagents 或 connectors 已实现。

## Verification evidence

- [x] Focused CLI tests pass：`pytest tests/test_cli.py -q` -> 41 passed。
- [x] Adjacent regressions pass：CLI/API/AgentLoop/patch parser/verification focused tests -> 133 passed。
- [x] Workflow/skill wording checks pass：`scripts/check_skill_evals.ps1` passed；CLI wording tests included in `tests/test_cli.py`。
- [x] `openspec validate polish-demo-cli-capability-surface --strict` pass。
- [x] `openspec validate --all` pass：21 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` pass：441 passed，1 skipped；ruff and stage scans pass。
- [x] `git diff --check` pass；仅有 CRLF normalization warnings。

## Final review evidence

- [x] Internal final implementation review completed after latest runtime/test/doc/skill changes：发现并修正
  `docs/PROGRESS.md` 路线图旧口径和长期 spec 中 `V24 promotion` 短语；re-scan 后仅保留
  未实现/顺延/未来候选语义。
- [x] Focused external final review completed via reused OpenCode session
  `ses_1018bd2aeffeKLTCcQhhuQ1jFZ` after terminal timeout final-text inspection；no P0/P1。
  P2.1 `FEATURE_LIST passes:true` vs unchecked checklist classified `fix` and closed by this checklist update。
  P3.1 output style classified `defer`；P3.2 parser-coupled CLI test classified `clarify` as intentional
  integration coverage；P3.3 skill wording tests classified `clarify` as deterministic workflow contract tests；
  P3.4 error wording classified `defer` as non-blocking UX polish.
- [x] Stage Debt Sweep completed for changed CLI paths, parser/ChatService adjacent paths, workflow skills,
  OpenCode review entry, roadmap docs, specs, and Harness files.
- [x] OpenSpec archive completed：`polish-demo-cli-capability-surface` archived as
  `openspec/changes/archive/2026-06-25-polish-demo-cli-capability-surface/`。Long-term specs had
  already been synchronized before archive, so archive used `--skip-specs` to avoid duplicate spec application.
