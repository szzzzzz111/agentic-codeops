# Context

RepoPilot 已有 fake/local provider、审计与验证基础，但本阶段不把真实 provider 接进 runtime。Controller 只在临时
fixture 中显式调用已安装的 `codex exec --json --ephemeral`；仓库内新增的 validator 接收冻结 JSON observation，
机械核对事件序列、Git snapshot 与 verification receipt。这样可以先验证最小数据链，避免在观测资格未知时开发
UI、daemon、多 Agent 或自动纠偏。

# Frozen Data Chain

1. **Real event entry**：实际 Codex CLI JSONL；要求唯一 `thread.started`、`turn.started`、最终
   `item.completed(type=agent_message,text=READY_FOR_REVIEW)` 与唯一、末尾的 `turn.completed`。
2. **Clean fixture**：临时 Git repository 在 Agent 运行前必须 `clean=true`，并记录 repository id、HEAD、
   status digest、tracked binary diff digest 与 untracked inventory digest；qualification 全程禁止 untracked path。
3. **Completion claim**：只把精确 `READY_FOR_REVIEW` 解释为可观察 claim；它启动人工/独立验证，不代表完成。
4. **Git snapshot**：Agent 终态后记录 canonical snapshot；必须与 baseline 属于同一 repository/HEAD，且代码状态
   实际发生变化。`status_sha256` 来自 `git status --porcelain=v1 -z --untracked-files=all`，
   `tracked_diff_sha256` 来自 `git diff --binary --no-ext-diff HEAD`，`untracked_paths_sha256` 来自
   `git ls-files --others --exclude-standard -z`；最后一项必须等于空字节 SHA256。
5. **Verification receipt**：controller 在 completion snapshot 上运行确定性 verifier，记录命令、exit code、
   bound snapshot SHA256 和完整的验证后 snapshot；validator 必须重算后者，不能只信任回执自报哈希。
6. **Decision**：所有约束成立才输出 `QUALIFIED_OBSERVABILITY`；任一缺失或歧义输出 `NOT_OBSERVED`。

# Six Deterministic Failure Scenarios

1. `turn.completed` 缺失：终态不可观察。
2. 终态前没有精确 `READY_FOR_REVIEW` Agent completion claim：完成声明不可观察。
3. 多个终态、终态后仍有事件或 claim/终态顺序歧义：事件归属不可唯一确定。
4. baseline `clean=false`：Agent 变化无法与预存 dirty 状态区分。
5. verification receipt `exit_code != 0`：同快照验证失败。
6. receipt 绑定的 snapshot 与 completion snapshot 不同，或重算出的 verification 后 snapshot 漂移：回执不是
   同快照证据。

# Risk And Authority

- Change class：mechanical qualification tooling；risk `low`。
- Plan/implementation independent review slots：`0/0`，由 authority 显式绑定；仍执行一次内部计划复核和完整
  packet/activation/authority preflight。
- Action ceiling：`implement`。archive、commit、merge、push 均未授权。
- 若实现需要 `app/**`、通用 Agent subprocess supervisor、权限/网络/持久化/default provider 变化，立即停止并
  重新定级，不在本阶段扩 scope。

# Claim Ceiling

真实事件只能证明指定 Codex CLI run 的 event shape 被观察；snapshot/receipt validator 只能证明提供的冻结字段在
机械上同快照、一致且 exit 0。它不证明 provider 内部状态、命令执行来源不可伪造、语义正确性、人工审批、产品
验收或可长期运行的 supervisor。真实命令输出、controller Git/verification 命令和仓库 report 共同构成本次证据；
单元测试只证明 fail-closed 规则，不得替代真实接入。

# Verification

- Focused RED/GREEN tests 覆盖一条正样本和上述六类故障。
- 真实临时 fixture probe + 独立 verification + 同快照 report validation。
- Changed-file Ruff、OpenSpec validation、authority/allowlist preflight、`git diff --check`。
- 由于新增 Python/test，最终运行 canonical repository verification；失败只报告真实状态，不降低 gate。
