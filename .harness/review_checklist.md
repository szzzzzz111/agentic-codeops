# 当前 Review 清单

Active OpenSpec change：无。

最近完成阶段：`consolidate-stage-documentation-sources` 已完成 implementation review、Stage Debt Sweep、验证，并归档到
`openspec/changes/archive/2026-06-27-consolidate-stage-documentation-sources/`。

## Planning Gate

- [x] 已读取 `AGENTS.md`、必读项目文档、`openspec/README.md` 和 workflow 风险规则。
- [x] 已检查 branch、worktree、recent commits 和 active OpenSpec changes。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。
- [x] OpenSpec proposal / design / tasks / spec delta 已创建。
- [x] `openspec validate consolidate-stage-documentation-sources --strict` 通过。
- [x] Internal plan review 完成；findings 已按 `fix / clarify / reject / defer` 分类。
- [x] Codex independent plan review 完成；findings 已按 `fix / clarify / reject / defer` 分类。
- [x] OpenCode independent plan review 完成；先 `opencode session list`，复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；findings 已按 `fix / clarify / reject / defer` 分类。
- [x] 用户明确确认后再进入 documentation implementation。

## Plan Findings Triage

- [x] Internal plan review：发现 proposal/checklist/spec delta 与当前 planning evidence 存在轻微同步风险；按 `fix` 更新 checklist、tasks 与 spec delta 后重跑 strict validation。
- [x] Codex independent P2：checklist 显示 artifacts/strict validation 未完成但事实已完成；按 `fix` 更新 checklist 和 tasks evidence。
- [x] Codex independent P2：proposal 定义 `docs/AGENT_RULES.md` 职责，但 spec delta 未列入职责矩阵；按 `fix` 将 AGENT_RULES 职责加入 spec delta。
- [x] OpenCode P3.1：`single-source-of-truth` 措辞可能被过度解读；按 `fix` 收窄为 volatile repository state 的 single-source policy。
- [x] OpenCode P3.2：proposal 职责列表缺少 `docs/AGENT_RULES.md` 和 `scripts/check_stage_docs.ps1`；按 `fix` 补充职责。
- [x] OpenCode P3.3：tasks 未显式列 `opencode session list`；按 `clarify` 拆出 session list 前置任务。

## Implementation Review Targets

- [x] README 只保留 facade、当前 capability snapshot、quick start 和 doc links，不承载详细阶段历史。
- [x] ARCHITECTURE 只描述稳定 runtime boundary 和 durable relationships，不把 transient stage task 写成当前事实。
- [x] PROGRESS 保留历史、durable decisions、validation evidence 和 unresolved debt；current guidance 不再描述已完成阶段为 future/backlog。
- [x] HANDOFF 只保留下轮安全行动上下文，不复制长期历史或 volatile hash。
- [x] FEATURE_LIST notes 保持 acceptance-oriented，不承载路线图叙述。
- [x] `scripts/check_stage_docs.ps1` 区分 current facts 与 historical records，且保持 Windows/ASCII-safe。
- [x] `tests/test_chat_api.py` docs consistency regression 不再要求 README 承载完整 route map。
- [x] OpenSpec archive 历史内容未被误改。

## Verification Gate

- [x] `openspec validate --all` 通过：22 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过：pytest 469 passed、1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] `git diff --check` 通过，仅 CRLF normalization warnings。
- [x] Stage Debt Sweep 覆盖 changed docs、adjacent responsibility statements、drift script 和 docs consistency regression。

## Final Review

- [x] Internal implementation review：README/ARCHITECTURE/PROGRESS/HANDOFF/AGENT_RULES/spec/script/test changes 与 OpenSpec/Harness 边界一致；未发现 P0/P1/P2。
- [x] OpenCode final implementation review：复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；检查 README route-map 收敛、ARCHITECTURE stable facts、PROGRESS/HANDOFF current facts、drift script、test contract、allowed files 和 runtime scope；无 P0/P1/P2/P3。
- [x] Scope check：未修改 `app/**`、provider runtime、live eval profile、default CI、`/chat` public contract 或 product runtime behavior。

## Archive Gate

- [x] OpenSpec archive：`openspec archive consolidate-stage-documentation-sources --skip-specs --yes`。
- [x] Archive-after `openspec list`：No active changes found。
- [x] Archive-after `openspec validate --all`：21 passed，0 failed。

## 下一阶段 gate

- [ ] 新阶段开始前重新读取 `AGENTS.md` 及必读文档。
- [ ] 新阶段开始前检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [ ] 新阶段必须先同步 `.harness/allowed_files.md` 与本 checklist。
- [ ] Medium/high risk 阶段必须按流程完成 plan review、implementation review、Stage Debt Sweep 和 deterministic verification。
