# 当前 Review 清单

当前活跃阶段：无 active implementation stage。

## V19 Planning / OpenSpec Gate

- [x] V19 plan 已明确 runtime scope：持久审计摘要 + 只读恢复视图。
- [x] V19 non-goals 已明确：不做 V20 Worktree Isolation，不做真实 subagents/connectors/notifications/heartbeat/always-on assistant。
- [x] OpenSpec change 包含 `persistent-audit-recovery` 新能力 spec delta。
- [x] OpenSpec change 覆盖所有被修改或约束的能力：`agent-loop-tool-execution`、`chat-api`、`safe-patch-authoring`、`verification-runner`、`long-task-agent-execution`、`harness-development-workflow`。
- [x] Recovery intent 路由优先级固定为 patch/verification 之后、capability/status 与 repo_search 之前。
- [x] `.codex/skills/**` 若修改，只能作为流程文档，不得写成 RepoPilot runtime 能力。

## V19 Runtime Gate

- [x] 所有 `/chat` 请求记录轻量 trace envelope；patch、verification、long task 记录脱敏摘要。
- [x] Audit store 使用 repo-local `.repopilot/audit.sqlite3`，并按 `user_id + repo_key` 隔离。
- [x] Audit record 不保存 full diff、full stdout/stderr、full Evidence Pack、provider prompt/output、secret、DB path、环境变量或本机绝对路径。
- [x] Recovery/status 是只读能力，不执行 patch、verification、task resume、repo mutation、commit、push 或 worktree 操作。
- [x] Missing audit DB 查询不创建 `.repopilot` 或 `audit.sqlite3`。
- [x] Audit persistence failure 不影响主 `/chat` 请求。
- [x] `/chat` 顶层 response schema 不新增字段；recovery 只通过 `answer` 返回。
- [x] Recovery intent 命中后不调用 repo RAG。
- [x] Retention 维持 V19 锁定决策：无限保留，不自动清理；查询默认最近 20 条。

## V19 Test Gate

- [x] `tests/test_persistent_audit.py` 覆盖 schema、scope、ordering、default limit、missing-store no-create、redaction/capping。
- [x] AgentLoop tests 覆盖 trace、patch、verification、long task audit event。
- [x] AgentLoop/API tests 覆盖 recovery routing、no repo RAG、read-only behavior、audit failure non-blocking 和 `/chat` schema unchanged。
- [x] Security tests 证明 SQLite payload 不包含 full diff、full stdout/stderr、Evidence Pack、provider content、secret、DB path 或本机绝对路径。

## V19 Stage Debt Sweep / Closeout Gate

- [x] Stage Debt Sweep 已在 V19 commit/archive 前扫描 current docs、harness docs、active OpenSpec、long-term specs、changed runtime paths 和 adjacent older runtime paths。
- [x] 发现 debt 已修复或记录为 blocker，并沉淀到 `docs/PROGRESS.md` 与 `HANDOFF_TO_NEXT_CHAT.md`，不只留在聊天里。
- [x] `.harness/review_checklist.md` 已记录 Stage Debt Sweep evidence/gate。
- [x] `openspec/specs/**/spec.md` 不保留 `TBD`、`TODO`、`created by archiving change` 这类 Purpose 占位。
- [x] V19 merge/push 后 durable docs 已更新真实 `main`/remote 状态、commit hash、验证结果和下一阶段建议。
- [x] V19 branch cleanup/retention 已作为 closeout checklist 显式项执行并记录。

## V19 Stage Debt Sweep Evidence

- [x] Long-term specs placeholder sweep：`openspec/specs/**/spec.md` 未发现 `TBD`、`TODO`、`created by archiving change` 占位 Purpose。
- [x] Durable docs sweep：`README.md`、`docs/PROGRESS.md`、`docs/ARCHITECTURE.md`、`HANDOFF_TO_NEXT_CHAT.md` 已更新到 V19 active branch/change 状态。
- [x] Harness docs sweep：`.harness/allowed_files.md` 和 `.harness/review_checklist.md` 已同步 V19 allowed files、review gates、post-merge durable docs gate 与 branch retention gate。
- [x] Archived OpenSpec sweep：`openspec/changes/archive/2026-06-05-v19-persistent-audit-recovery/` 包含 proposal/design/tasks/stage planning 与所有受影响能力 spec delta；当前无 active OpenSpec change。
- [x] Changed runtime path sweep：`app/audit/**` 与 `app/harness/kernel.py` 已通过 targeted tests、full verify 和 ruff。
- [x] Adjacent runtime path sweep：patching、verification、longtask、AgentLoop/API tests 已覆盖 V19 audit hook 对既有路径的影响。
- [x] Additional documentation debt fixed：`docs/FEATURE_LIST.json` 已修复为可解析 JSON，并将 V19 acceptance 更新为通过状态。
- [x] Historical V18 doc drift fixed：V18 archive merge hash `3c7a8b3...` 已标注为历史归档记录，并由 V18 closeout debt commit `8b93330` supersede。
- [x] Post-merge evidence：`main`、`agentic-codeops/main` 和本地 `feature/v19-persistent-audit-recovery` 均指向 `add702d62bcf737925b6418d3c9b9fb258e7ff35`；feature branch fully merged，并按审计惯例保留。

## V18 Closeout Baseline

- [x] V18 implementation/archive/merge/push 已完成。
- [x] V18 post-merge/handoff debt remediation 已提交到 `main` commit `8b93330` 并推送到 `agentic-codeops/main`。
- [x] V18 closeout debt remediation 验证通过：`openspec validate --all` 13 passed, `scripts/verify.ps1` 178 passed/1 skipped, `git diff --check` 无 whitespace error。
- [x] V18 feature branch retention 决策：保留近期阶段分支用于审计；不在 V19 中自动删除。
