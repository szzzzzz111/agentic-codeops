## Context

上一阶段只证明了一次真实 `codex exec --json --ephemeral` 运行可以提供可观察终态、精确
`READY_FOR_REVIEW` 声明，以及绑定同一 Git snapshot 的验证回执。该资格结果仍是开发期证据，不能直接当作
runtime supervisor。RepoPilot 当前的 verification runner 已提供固定 label、argv list 与 `shell=False`，但尚无
统一数据合同把任务边界、Agent 声明、仓库状态和验证结果组合成有界监督决策。

本阶段是 high / L3：在实现前冻结完整设计、规格和任务，并由两个相互隔离的空上下文 Codex reviewer 对同一
packet 复核。当前 authority 只到 `implement`；archive、commit、merge、push 不在本阶段授权内。

## Goals / Non-Goals

**Goals:**

- 为单 Agent、单 repository、单 baseline HEAD 建立不可变的 `RunContract`。
- 从真实 Codex JSONL 事件流机械提取 pending、failed、not-observed、invalid 或精确
  `READY_FOR_REVIEW` claim，并保存事件流 digest。
- 用受控只读 Git 命令和双稳定采样生成可重算 `GitSnapshot`，显式列出 tracked changed paths 与包括 ignored
  文件在内的 all-untracked paths。
- 把 `RunContract + GitSnapshot + AgentClaim + VerificationReceipt` 纯函数求值为
  `continue / intervene / needs_human / ready_for_review`。
- 对缺失、歧义、越界和 snapshot drift 全部 fail closed，并让每个决策保持 `task_complete=false`。

**Non-Goals:**

- 不公开 API/CLI，不接入 `/chat`、ToolRegistry、provider 默认路径或持久化存储。
- 不由 RepoPilot 启动或控制 Agent，不实现 daemon、后台轮询、多 Agent、通知或自动纠偏。
- 不新增任意 verification argv；只引用现有 verification runner 的固定 command label。
- 不 apply、repair、rollback、commit、merge、push、创建 branch/PR 或修改 Agent worktree/index/refs。
- 不证明语义正确、人工审批、产品验收、发布就绪或任务完成。

## Decisions

### 1. 使用小型不可变 Python 合同，不引入 orchestration service

新增 `app/supervision/`，包含 frozen dataclass、受控 factory 与枚举：

- `RunContract`：controller 生成的非空唯一 `run_id`、baseline repository/HEAD/snapshot digest、规范化 exact
  `allowed_tracked_paths`、固定 `verification_label` 与当时解析出的 argv digest。
- `GitSnapshot`：repository id、HEAD、status/tracked-diff digest、排序后的 tracked changed paths、排序后的
  all-untracked paths、完整 stage-0 index path/mode/object identity、全部 tracked worktree regular files 的 raw content SHA-256/实际 mode、`clean` 与
  `stability_samples=2`，并可计算 canonical snapshot digest。
- `AgentClaim`：provider、run id、唯一 Codex thread id、stream-closed 标志、claim state、事件流 digest、可选 claim
  text 与 bound snapshot digest。
- `VerificationReceipt`：run/thread/claim/event identity、固定 command label 与 argv digest、现有 runner result 的
  canonical audit-summary digest、runner status/exit code、bound snapshot digest 与完整 post-verification snapshot。
- `GovernanceDecision`：outcome、稳定 reason codes、恒为 false 的 `task_complete`、`product_acceptance=false`、
  `git_delivery_authorized=false`、`source_provenance=unverified` 与
  `snapshot_continuity=stable_endpoint_samples_only`。

所有 dataclass 在 `__post_init__`/factory 中验证状态与字段组合；evaluator 仍防御性重验，不信任对象必然由正确
factory 创建。`dataclasses.replace`、直接 constructor 或同 snapshot 的旧对象不得绕过 run/thread/claim binding。
这些类型不写数据库、不执行 Agent、不修改 repository。

### 2. Codex adapter 明确区分开放事件前缀和已关闭事件流

adapter 接收 controller-issued `run_id`、已解码 JSON objects、`stream_closed` 和可选 completion snapshot digest：

- 开放流中，唯一 `thread.started -> turn.started` 前缀且尚无 terminal，产生 `pending`。
- `thread.started.thread_id` 必须是非空字符串并在该流中唯一；claim 保存 observed thread id 和 controller run id。
- 已关闭流要求唯一 thread/turn start、唯一 terminal、terminal 为最后事件；`turn.completed` 前必须恰有一个精确
  `READY_FOR_REVIEW` Agent message，且它是 terminal 前最后一个 Agent message。
- `turn.failed` 产生 `failed`；已关闭但缺 terminal 或缺精确 claim 产生 `not_observed`；重复/乱序/terminal 后事件、
  多个精确 claim、ready claim 后 `turn.failed` 或 completed/failed 冲突产生 `invalid`。
- 只有精确完成 claim 才携带 completion snapshot digest；adapter 不把 terminal 本身解释为完成。

选择显式 `stream_closed`，是因为“当前还没看到 terminal”和“进程结束后仍没有 terminal”必须产生不同决策。adapter
不接受手写 source attestation 作为“真实”证明；`run_id` 只提供 execution correlation，不提供不可伪造 provenance。
真实来源仍由调用它的 controller/测试 fixture 提供，本阶段只消费已捕获事件。

### 3. Git snapshot collector 只执行固定、只读 argv

collector 要求调用路径是无 symlink traversal 的现存 repository root，并现场核对
`git rev-parse --show-toplevel`。Git executable 只从 code-owned `os.defpath` 解析为 repository 外的 canonical
absolute regular executable，不消费 inherited `PATH`、相对 path 或 target-repository-local executable。子进程环境从
allowlist 构造，不继承任意 `GIT_*` 注入；`PATH` 固定为 code-owned default，并固定
`LC_ALL/LANG=C`、`GIT_OPTIONAL_LOCKS=0`、`GIT_TERMINAL_PROMPT=0`、pager off、system/global
config off。每个 Git argv 都固定加入 `-c core.fsmonitor=false -c core.untrackedCache=false -c diff.external=`；diff
额外使用 `--no-ext-diff --no-textconv`，不允许 repository-controlled fsmonitor、external diff 或 textconv helper。

在任何 status、working-tree diff 或其他内容读取前，sample 先运行固定 plumbing preflight：读取
repository/common-dir identity 与起始 HEAD，以 `git ls-files --stage -z` 检查 mode，并用固定
`git config --includes --null --get-regexp '^filter\..*\.(clean|process)$'` 检查全部 effective repository scopes
（exit 1 表示无匹配）。该命令运行于已禁用 system/global config、清除继承 `GIT_*` 的同一受控环境，因此覆盖 local
config 及启用 `extensions.worktreeConfig` 后的 worktree config，而不会重新开放外部 scopes。tracked symlink
(`120000`)、gitlink/submodule (`160000`) 或任意 effective clean/process filter 配置都立即 fail closed；因此不会先
进入 submodule，也不会让 status/diff 触发 repository-controlled conversion helper。

preflight 保留并规范化完整 stage-0 `(path, mode, object id)` inventory，使 masked staged blob 仍进入 snapshot identity；
evaluator 将 baseline/current index delta path 并入 exact scope。随后以 POSIX `openat`/`O_NOFOLLOW` 逐层拒绝 worktree symlink traversal，并在总计 128 MiB/
10 秒观察边界内流式绑定全部 tracked regular files 的 raw bytes SHA-256 和实际 mode；由 evaluator 把 baseline/current
raw state 差异并入 exact tracked-path scope。随后才读取 porcelain-v1 NUL status、`--no-ext-diff --no-textconv`
binary diff、`--no-renames` tracked path inventory、`git ls-files --others -z` 的 all-untracked inventory和结束 HEAD。`--others` 刻意不使用 exclude
规则，因此 ignored 文件也必须可见；任一 all-untracked path 使 evaluator 介入。

每条命令使用 `shell=False`、closed stdin、硬 timeout、输出 byte cap 和独立 POSIX process group；超时/超限时终止
并 wait，不返回 partial snapshot。当前 kernel 在无法证明 `openat/O_NOFOLLOW` 与 whole-tree process-group cleanup 的
非 POSIX/不支持平台于 spawn 前返回 `PROCESS_ISOLATION_UNAVAILABLE`，不提供半安全降级。collector 连续完成两个完整
sample，要求起止 HEAD 一致且两份 canonical 内容（包括 index 与 raw file state）完全相同，
否则返回 `REPOSITORY_CHANGED_DURING_COLLECTION`。NUL path 必须是 UTF-8、repository-relative、规范化 POSIX path，
禁止绝对路径、`.`/`..` 段、空项和重复项。

该协议拒绝能被起止 HEAD 或两份 canonical sample 差异观察到的跨命令 torn snapshot，但不声称检测外部 writer 的
完美 ABA。receipt 只证明 completion 和
post-verification 两个“双稳定采样端点”相等；不证明验证全过程无瞬时变化。持续单写者锁/隔离验证属于后续阶段。

### 4. evaluator 使用固定优先级，证据冲突优先于进度状态

求值顺序固定，避免同一输入因检查顺序不同得到不同结论：

1. contract/baseline 无效、repository/HEAD 漂移、all-untracked path、Git diff/raw worktree/stage-0 index 任一 evidenced tracked path 越界、事件歧义、
   ready claim 但零 tracked change、claim snapshot mismatch、跨 run/thread/claim replay、verification command
   mismatch、receipt/post-verification snapshot drift -> `intervene`。
2. 非 ready claim 却携带 receipt -> `intervene`（`PREMATURE_VERIFICATION_RECEIPT`）。
3. 合法开放流的 `pending` 且无 receipt -> `continue`，无论尚无 change 或只有合法 tracked change。
4. `failed/not_observed` 且无 receipt -> `needs_human`。
5. 精确 ready claim、有至少一个合法 tracked change，但 receipt 缺失、不可用、超时、失败/non-zero ->
   `needs_human`。
6. 精确 ready claim、有至少一个合法 tracked change、receipt run/thread/claim/event/command identity 全部匹配、
   verification 成功，且 receipt bound/post-verification stable endpoint snapshot 都等于 completion snapshot ->
   `ready_for_review`。

`ready_for_review` 只表示证据足以让人开始 review。所有 outcome 均输出 `task_complete=false`；没有 outcome 能触发
Git delivery。

### 5. verification receipt 绑定现有白名单 label 和验证后的完整 snapshot

`RunContract.verification_label` 必须来自现有 `app.verification.runner.ALLOWED_COMMANDS`，并在建约时保存
`command_argv(label)` 的 canonical digest。内部 receipt factory 只接收 `VerificationRunResult`、ready claim 和
post-verification snapshot；它保存 `audit_summary()`（已脱敏/可能截断 excerpt）的 canonical digest，而不谎称拥有
完整 raw stdout/stderr。evaluator 重算当前 label argv、claim digest 和 post snapshot digest，并要求 receipt 的
run id、thread id、event digest、claim digest、label/argv digest 与合同和 claim 全部一致。

这能阻止 accidental cross-run/old-receipt replay 与 label remap，但 caller 仍可伪造对象；因此 provenance 固定为
`unverified`，receipt 只证明所提供 runner result 与两个稳定端点在机械上相关。

### 6. 本阶段只提供内部 kernel 和确定性 seam

不新增 manager、endpoint 或后台 loop。测试通过公开 Python 函数构造 contract、解析真实格式事件、捕获临时 Git
fixture snapshot 并调用 evaluator。上一阶段 validator、既有 qualification tests 和长期 spec 保持只读；新测试仅
消费已归档 real observation 的事件形状做回归。fake provider、归档 observation 或合成 JSON 都只能覆盖规则，当前
decision 始终输出 `source_provenance=unverified`，不能声明本次 run 的真实 provenance。

## Risks / Trade-offs

- **[事件格式随 Codex CLI 漂移]** -> adapter 对未知/缺失关键字段 fail closed；后续格式升级必须新增 fixture 与明确版本策略。
- **[路径解析或 Git 配置影响 snapshot]** -> code-owned Git resolution、child-env allowlist、fixed config overrides、NUL 输出、无 helper、raw bytes/mode binding、timeout/output cap、双采样，并拒绝 malformed/symlink/gitlink/outside root。
- **[Windows 无 whole-tree containment]** -> 当前 collector 在 spawn 前 fail closed；Windows Job Object 支持必须另起阶段并取得真实 Windows runner 证据。
- **[并发 writer/ABA]** -> 两次完整稳定采样拒绝普通 torn state；claim 明确降为 endpoint equality，不声称验证全过程隔离。
- **[receipt/caller 仍可伪造]** -> run/thread/claim/command correlation 减少意外 replay；claim ceiling 固定为机械一致性与 unverified provenance，不声称不可抵赖。
- **[所有新文件都被拒绝]** -> MVP 的 allowlist 只允许 tracked paths；新文件只有先由外部 Agent stage 后才成为 tracked change，unstaged/ignored new file 一律介入。
- **[clean baseline 限制真实场景]** -> 首个合同刻意只支持 clean fixture/worktree；dirty baseline 支持留到真实任务 cohort 后评估。
- **[没有持久化与进程恢复]** -> 本阶段只资格化 kernel；崩溃恢复、operator authority 和 lifecycle 属于后续独立阶段。
- **[四态决策过于粗粒度]** -> reason codes 保留机械原因；在 5-10 个真实任务前不增加更多状态。

## Migration Plan

这是新增、未接线的内部模块，无数据迁移和兼容切换。实现按 RED -> GREEN：先落负例与 happy path，再实现合同、adapter、
collector 和 evaluator；focused/full 验证与两席实现复核通过后仍保持 change 未归档、代码未提交。若需要 public API、
持久化、Agent launcher、动态 argv 或任何 mutation，立即停止并拆分新阶段。

## Open Questions

- 本阶段没有阻塞实现的开放决策。真实任务 cohort 应记录哪些 reason codes、是否需要 lifecycle persistence、何时介入，
  但这些问题明确推迟到 kernel 通过并完成 5-10 个个人真实任务之后。
