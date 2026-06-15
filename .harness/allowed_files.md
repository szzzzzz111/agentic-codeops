# 当前 Harness 写入边界

当前无 active development stage。V23 已合并，但 merge 后正式 review 发现未关闭的 P1/P2。
当前只允许进行 review 流程沉淀与后续 V23 debt remediation。

开始下一阶段前，必须先关闭 V23 review findings、通过正式 re-review 与 closeout gate，
然后创建对应 OpenSpec change，并重新同步本文件与 `.harness/review_checklist.md`。

## 当前允许修改

- V23 review 流程沉淀、durable blocker docs 与后续 debt remediation 文件。

## 禁止修改 / 禁止行为

- 未关闭 V23 P1 findings 前，不开始 V24 或其他新 runtime stage。
- 不把连续执行授权解释为跳过正式 review、Stage Debt Sweep、验证或 closeout gate。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段或公开 API。
