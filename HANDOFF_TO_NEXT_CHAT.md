# RepoPilot 恢复协议

本文件是稳定的 session 恢复清单，不是 repository state snapshot。它不保存易变的 Git/OpenSpec 状态，
也不证明任何交付结果；每次恢复都必须重新读取 live facts。

## 先查询实时状态

在准备修改前运行：

```text
git status --short --branch
git log -5 --oneline --decorate
git worktree list --porcelain
openspec list
openspec validate --all
```

如果当前 Python 环境提供项目验证工具，再运行：

```text
python -I scripts/verify.py
```

缺少 Python、pytest、Ruff 或 OpenSpec 时明确记录 unavailable；不得把未运行写成 PASS，也不得静默换用
不同验证语义。

## 阅读顺序

1. `README.md`：项目定位、快速开始和文档导航。
2. `docs/ARCHITECTURE.md`：当前 runtime 架构、模块映射和稳定边界。
3. `docs/PROGRESS.md`：durable status、remaining debt、候选顺序和阶段索引。
4. `docs/AGENT_RULES.md` 与 `.harness/rules.md`：长期协作和风险路由。
5. `.harness/allowed_files.md` 与 `.harness/review_checklist.md`：live stage 的写入与 review 边界。
6. `openspec/README.md`、`openspec/specs/` 和 `openspec list`：规格与阶段事实。

## 安全恢复规则

- 只从 live commands 判断 repository/worktree/OpenSpec 状态；不要从聊天摘要或本文反推。
- 发现 dirty worktree 时先识别修改所有者和 scope，不整理、不覆盖、不混入新阶段。
- 新阶段重新冻结 goal、scope、non-goals、change class、risk、implementation lane、delivery actions、
  allowed files、verification 和 stop conditions。
- Low-risk docs/mechanical work使用轻量路径；只有出现行为、权限、持久化、网络、Git/subprocess、
  public contract 或测试削弱时才向上升级。
- `technical_ready`、`human_authorized` 与 `vcs_pushed` 分开判断。Push outcome 不确定时只做同 endpoint
  read-only reconciliation，不自动 retry、rebase 或 force push。
- Final user handoff 报告 live state，但不把易变 delivery facts 回写到这个 tracked file。

## 本文件明确不保存

- active change 名称或状态；
- branch、HEAD、remote-tracking ref 或精确 commit/hash；
- worktree path、stage base reference 或 authorized tip；
- review packet、delivery binding 或 staged-index 状态；
- merge、push、remote parity 或下一阶段已经获批的声明。

这些事实分别由 Git/OpenSpec、当前 Harness artifacts 和 controller output 提供。若它们之间不一致，停止写入并
以 live repository evidence 重新冻结，而不是修改本文去追赶瞬时状态。
