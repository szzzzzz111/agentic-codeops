# 当前 Harness 写入边界

当前无 active product development stage。process-only workflow maintenance 已完成并本地合并到
`main`。开始下一阶段前，必须创建对应 OpenSpec change，并重新同步本文件与
`.harness/review_checklist.md`。

## 当前允许修改

- 无 active stage 写入范围。
- 下一阶段规划时重新列出明确允许文件。

## 禁止修改 / 禁止行为

- 不把连续执行授权解释为跳过正式 review、Stage Debt Sweep、验证或 closeout gate。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段或公开 API。
- 不修改 `app/**`、`tests/**`、`docs/FEATURE_LIST.json` 或 runtime capability specs。
- 不创建 V24 或其他产品功能 change。
- 不把动态 Git HEAD/remote hash 复制到多份 durable docs。
