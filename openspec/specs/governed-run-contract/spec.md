# governed-run-contract Specification

## Purpose

定义 RepoPilot 内部单 Agent governed-run kernel 的机械证据合同：把 clean baseline、Codex completion claim、
只读 Git snapshot 与白名单 verification receipt 绑定到同一 run/thread/snapshot，并仅产生有界人工 review 决策。
该合同不证明语义完成、产品验收、真实来源、持续隔离或任何 Git 交付授权，也不接入公开 runtime route。

## Requirements
### Requirement: Immutable single-run contract
系统 SHALL 为一个 Agent run 建立不可变合同，绑定 controller-issued run id、clean baseline snapshot identity、
repository id、HEAD、exact allowed tracked paths、现有白名单 verification label 和解析后的 argv digest。所有 contract、
claim、receipt 类型 MUST 在构造时验证字段组合，evaluator MUST 防御性重验，不得仅依赖 `frozen=True`。

#### Scenario: Valid clean-baseline contract
- **WHEN** 调用者提供非空 run id、clean baseline、唯一规范化 repository-relative allowed tracked paths 和现有白名单
  verification label
- **THEN** 系统创建不可变 `RunContract`，且 baseline digest 与当前白名单 argv digest 均可重算

#### Scenario: Dirty baseline is rejected
- **WHEN** baseline snapshot 包含 tracked 或 untracked change，或其 `clean` 标志与 digest/path inventory 不一致
- **THEN** 系统拒绝合同，不得把预存变化归因于 Agent

#### Scenario: Unsafe path or verification command is rejected
- **WHEN** allowed path 为绝对路径、包含 `.`/`..` 段、重复，或 verification label 不在现有固定白名单
- **THEN** 系统拒绝合同，且不接受动态 argv 或 shell text

#### Scenario: Invalid direct construction is rejected
- **WHEN** 调用者通过直接 constructor 或 `dataclasses.replace` 创建状态与字段不一致的 contract、claim 或 receipt
- **THEN** 类型验证或 evaluator 拒绝该对象，不得因对象不可变而默认其可信

### Requirement: Fail-closed Codex completion claim adapter
系统 SHALL 从捕获的 Codex JSON event objects 中区分开放事件前缀、失败终态、未观察、歧义和精确
`READY_FOR_REVIEW` claim，并把 controller run id、唯一非空 `thread.started.thread_id` 与 canonical event digest 保存到
claim。只有唯一、有序、以 terminal 结尾的 closed stream 可产生终态 claim；terminal 自身 MUST NOT 被解释为任务完成。

#### Scenario: Open valid prefix continues
- **WHEN** event stream 含唯一有序的 `thread.started` 和 `turn.started`、尚无 terminal，且 `stream_closed=false`
- **THEN** adapter 产生 `pending` claim state，并保存 run id、唯一 thread id 和 canonical event-stream digest

#### Scenario: Exact review claim is observed
- **WHEN** closed stream 只有一个有序 terminal，terminal 是最后事件，且 terminal 前恰有一个精确
  `READY_FOR_REVIEW` Agent message 并且它是最后一个 Agent message
- **THEN** adapter 产生 `ready_for_review` claim，并绑定 run/thread/event identity 与调用者提供的 completion snapshot digest

#### Scenario: Missing closed-stream evidence is not observed
- **WHEN** stream 已关闭但 terminal 缺失，或 `turn.completed` 前没有精确 review claim
- **THEN** adapter 产生 `not_observed`，不得伪造或推断 completion claim

#### Scenario: Ambiguous chronology is invalid
- **WHEN** thread id 缺失/为空、start/terminal 重复或乱序、completed 与 failed 冲突、terminal 后仍有事件，或出现多个
  精确 review claims
- **THEN** adapter 产生 `invalid` 并保留稳定 reason code

#### Scenario: Agent terminal failure is preserved
- **WHEN** 唯一合法 terminal 为 `turn.failed`
- **THEN** adapter 产生 `failed`，不得改写成 completion 或 review-ready

#### Scenario: Ready message followed by failed terminal is invalid
- **WHEN** 精确 `READY_FOR_REVIEW` message 后的唯一 terminal 为 `turn.failed`
- **THEN** adapter 产生 `invalid`，evaluator 必须按证据冲突介入

### Requirement: Read-only canonical Git snapshot collection
系统 SHALL 使用 code-owned absolute Git executable resolution、child-environment allowlist、禁用 repository-controlled Git helpers、固定 argv、closed stdin、
`shell=False`、`GIT_OPTIONAL_LOCKS=0`、hard timeout 和 output byte cap，对 repository root 连续执行两个完整 sample。
只有两份 sample 的起止 HEAD 和 canonical 内容完全相同，系统才可生成 `GitSnapshot`。snapshot MUST 包含 tracked binary
diff、tracked paths、完整 stage-0 index path/mode/object identity、全部 tracked regular files 的 raw content/mode identity
与包括 ignored 文件在内的 all-untracked inventory；系统 MUST NOT 修改 worktree、index、refs 或 remote。无法证明 whole-tree process containment 或 no-follow
raw reads 的平台 MUST 在 spawn/content read 前 fail closed。

#### Scenario: Tracked change snapshot is captured
- **WHEN** 无 symlink traversal 的 repository root 具有固定 HEAD 和 tracked working-tree change
- **THEN** collector 返回相同 repository identity/HEAD、raw status/diff digests、排序去重的 changed paths、空 untracked
  inventory、`clean=false` 和 `stability_samples=2`

#### Scenario: Ignored and ordinary untracked paths remain visible
- **WHEN** repository 含普通或由 `.gitignore`/exclude 规则忽略的 untracked path
- **THEN** collector 将规范化 path 放入 all-untracked inventory，使 evaluator 能 fail closed，而不是忽略该 path

#### Scenario: Repository-controlled helper is never executed
- **WHEN** inherited environment 或 local config/attributes 尝试注入 alternate Git state、fsmonitor、external diff、
  textconv、local/worktree-scope clean/process conversion filter 或嵌套 submodule helper
- **THEN** collector 在任何 status/content diff 前按固定顺序完成 stage-mode preflight，清除注入并在 system/global
  config 已禁用的环境中检查全部 effective repository scopes；发现 symlink/gitlink 或任意 clean/process command
  立即 fail closed，helper 不得执行或产生副作用

#### Scenario: Git executable cannot be supplied by the target repository
- **WHEN** inherited `PATH` 含空项、相对项、`.` 或 target-repository-local fake Git executable
- **THEN** collector 仍只使用 code-owned default roots 中解析出的 repository 外 canonical executable，或在 spawn 前
  fail closed；fake executable 不得运行

#### Scenario: Git-normalized raw change remains in scope evidence
- **WHEN** `core.filemode=false`、EOL/encoding normalization 或其他 Git normalization 使 tracked worktree raw bytes/mode
  变化未出现在普通 diff path inventory
- **THEN** 两次 sample 仍绑定 raw content/mode；evaluator 将 baseline/current raw delta 并入 exact allowed path 判断，
  或 collector 因 Git evidence 不一致 fail closed

#### Scenario: Masked staged blob remains in snapshot and scope evidence
- **WHEN** out-of-scope path 的 blob 已写入 index，随后该 path 的 worktree bytes 恢复为 HEAD，同时另一个 allowed path
  保留净 worktree change，使普通 HEAD-to-worktree diff 不显示该 staged blob
- **THEN** 两次 sample 仍绑定 stage-0 index path/mode/object identity；evaluator 将 baseline/current index delta 并入
  exact allowed path 判断，且替换 staged blob object 必须改变 snapshot identity

#### Scenario: Unsupported process isolation fails before spawn
- **WHEN** 平台无法提供本阶段所需的 POSIX process-group whole-tree cleanup 与 no-follow raw file traversal
- **THEN** collector 返回 `PROCESS_ISOLATION_UNAVAILABLE`，不得启动 Git、helper 或目标代码

#### Scenario: Torn sample is rejected
- **WHEN** 跨命令变化被起止 HEAD 不一致或两个连续 canonical sample 不同所观察
- **THEN** collector 返回 `REPOSITORY_CHANGED_DURING_COLLECTION`，不得组装 mixed snapshot

#### Scenario: Symlink or gitlink repository state is rejected
- **WHEN** tracked inventory 含 symlink mode 或 gitlink/submodule，可能让验证依赖 snapshot 外内容
- **THEN** collector fail closed，不得返回可供 evaluator 使用的 snapshot

#### Scenario: Unsafe or malformed repository input is rejected
- **WHEN** 输入经 symlink/outside traversal、不是 repository root、HEAD 缺失、Git command 失败/超时/超限，NUL path
  output malformed，或被终止进程无法完成清理
- **THEN** collector 返回有界 collection error，不返回 partial snapshot，且不执行任何 mutation command

### Requirement: Deterministic governed-run decision
系统 SHALL 以固定、互斥且穷尽的优先级对
`RunContract + baseline/current GitSnapshot + AgentClaim + optional VerificationReceipt` 求值，只输出 `continue`、
`intervene`、`needs_human` 或 `ready_for_review` 和稳定 reason codes。

#### Scenario: In-progress valid run continues
- **WHEN** contract/baseline/current snapshot 一致、没有越界或 untracked change，且 claim state 为合法开放流的 `pending`
- **THEN** evaluator 输出 `continue` 和 `task_complete=false`

#### Scenario: Scope, identity, or snapshot conflict intervenes
- **WHEN** repository/HEAD 漂移、all-untracked path、Git diff/raw worktree/stage-0 index 任一 evidenced tracked path 超出 allowlist、ready claim 未绑定 current snapshot，
  或 receipt 的 run/thread/event/claim/label/argv/bound/post-snapshot identity 与合同、claim 或 current snapshot 不一致
- **THEN** evaluator 输出 `intervene` 和对应稳定 reason code，即使其他证据尚未完成

#### Scenario: Invalid event chronology intervenes
- **WHEN** AgentClaim state 为 `invalid`
- **THEN** evaluator 输出 `intervene`，不得降级为 continue 或 review-ready

#### Scenario: Ready claim without tracked change intervenes
- **WHEN** AgentClaim 为精确 ready、current snapshot 与 clean baseline 相同且没有 tracked changed path
- **THEN** evaluator 固定输出 `intervene/NO_EVIDENCED_CHANGE` 和 `task_complete=false`，无论 receipt 缺失、失败或成功

#### Scenario: Premature receipt intervenes
- **WHEN** claim state 不是 ready 但调用者提供 verification receipt
- **THEN** evaluator 固定输出 `intervene/PREMATURE_VERIFICATION_RECEIPT`

#### Scenario: Missing or failed completion evidence needs a human
- **WHEN** closed run 的 claim 为 `failed`/`not_observed`，或精确 ready claim 后 receipt 缺失、不可用、超时、失败或
  exit code 非零
- **THEN** evaluator 输出 `needs_human` 和 `task_complete=false`

#### Scenario: Same-endpoint-snapshot verified claim enters human review
- **WHEN** 精确 ready claim 绑定 current snapshot、至少一个 tracked change 全部在 exact allowlist、没有 all-untracked path、
  receipt 的 run/thread/event/claim/label/argv identity 与合同和 claim 一致、verification 成功且 receipt bound 与完整
  post-verification stable snapshot 都等于 current snapshot
- **THEN** evaluator 输出 `ready_for_review` 和 `task_complete=false`

#### Scenario: Every accepted input has exactly one outcome
- **WHEN** evaluator 接收任意通过类型 shape validation 的 claim state、tracked-change emptiness 和 optional receipt 组合
- **THEN** 固定优先级恰好产生一个 outcome，不抛出未定义状态，也不依赖集合空值的真值推断

### Requirement: Review decision claim ceiling
系统 SHALL 把所有 governed-run outcomes 限制为内部机械监督信号。`ready_for_review` MUST 只表示两个双稳定采样端点
相同且所提供证据机械一致，可以开始人工 review；MUST NOT 表示验证全过程无 ABA、真实来源已证明、任务完成、语义正确、
人工批准、产品验收、发布就绪或任何 Git delivery 授权。

#### Scenario: Every outcome remains incomplete
- **WHEN** evaluator 返回任意合法 outcome
- **THEN** `task_complete`、`product_acceptance`、`git_delivery_authorized` 恒为 `false`，
  `source_provenance=unverified`，且结果不触发 apply、commit、merge、push 或其他 repository mutation

#### Scenario: Real-source qualification is not inferred from synthetic data
- **WHEN** 测试使用 fake provider、手写 JSON 或合成 fixture 验证合同规则
- **THEN** 系统只声称 event shape 和合同规则被确定性测试，不得据此声明当前 run 的真实 Agent provenance 或产品验收

#### Scenario: Stable endpoints do not prove continuous isolation
- **WHEN** completion 和 post-verification 的两次稳定 endpoint snapshots 相同，或外部 writer 发生采样无法观测的完美 ABA
- **THEN** 系统最多声称 `snapshot_continuity=stable_endpoint_samples_only`，不得声称排除了外部 writer 的完美 ABA
