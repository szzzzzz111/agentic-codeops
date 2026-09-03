## Context

已归档 observability qualification 证明真实 Codex CLI JSONL 可被观察，已归档 governed-run contract 提供内部纯
evaluator。当前阶段只验证：Codex App 管理的一个新任务能否通过外部 controller 的真实 task terminal observation、
独立 Git worktree snapshot 和现有 verification receipt 驱动该 evaluator 一次。

本设计是 development-time host-assisted experiment，不是 RepoPilot runtime subagent、Codex App plugin 或通用 Agent
runner。Codex App task tools 不可由仓库 Python 脚本直接调用，因此“任务真实存在、终态来自 host tool”属于 controller
证据；仓库脚本只验证其消费后的机械链，固定 `source_provenance=unverified`。

## Goals / Non-Goals

**Goals:**

- 创建一个全新空上下文 Codex App task，并让 App 从精确 `origin/main` 创建独立 worktree。
- 在 mutation 前由外部 controller 证明 task worktree baseline clean、HEAD 与 repository identity 正确。
- 只消费一次 completed host observation、精确 `READY_FOR_REVIEW` 和同 worktree completion snapshot。
- 运行现有固定 `ruff` verifier，并证明 verification 前后 snapshot 未变化。
- 用现有 `RunContract`、`AgentClaim`、`VerificationReceipt` 和 evaluator 产生一次有界 decision。

**Non-Goals:**

- RepoPilot runtime 调度任务、调用 Codex App API、plugin/MCP、后台 supervisor 或 durable task service。
- 本地 `codex exec`、二进制完整性、隔离 `CODEX_HOME`、凭据代理、VM/container 或恶意代码安全证明。
- 多 Agent、cohort rate、重试/resume/crash recovery、人工 friction、自动纠偏或长期 observation 存储。
- 修改 `app/**`、公开 API/CLI/ToolRegistry/provider/persistence，或 archive/commit/merge/push。
- 证明 OS 级读取隔离、task source attestation、语义完成、产品验收或 Git delivery authority。

## Decisions

### 1. 一个 fresh task、一个 App worktree、一个 coding turn

外部 controller 先通过 Codex App 创建全新 task；不得 fork 当前开发对话。创建时从 Git 项目的默认分支生成 App
worktree，controller 必须独立核对其 HEAD 为
`b7a8439fac9013f5ad59c308c4b16d333d466ddb`，且与 RepoPilot Git repository identity 一致。

创建 prompt 只允许回复 `READY_FOR_TASK`，明确禁止修改文件、运行任务或 commit。该 turn 完成后，controller 再次确认
worktree clean；任何变化立即停止，不能发送 coding prompt。

唯一 coding prompt 固定为：只把 task worktree 的 `README.md` 第一行从 `# RepoPilot` 改为
`# RepoPilot Agent Probe`，禁止修改其他内容、禁止 commit，完成后只回复 `READY_FOR_REVIEW`。其完整文件 before/after
SHA-256 分别固定为 `70e242e898295dffaeb9a9723c5536edb96b5b6429e94fea274925a4a8b4e64e` 与
`d7844da1d65cabe3307959c6ac9a510e483bcdb99ad5070b280bdea0c33d575c`。这是一条与 stage worktree
allowed-path list 分离、绑定 task-worktree role 的 mutation authority；stage implementer 不得据此修改 stage worktree 的
`README.md`。controller 不发送第三个 turn，不重试、不改 prompt。

### 2. 候选脚本只做 in-memory host bridge

脚本新增一个窄入口，参数只包含由 controller 已解析的 task worktree absolute path 和 thread id。启动后它：

1. 验证 stage 与 target 是同一 `git worktree list --porcelain` 集合中的 live、non-prunable 注册 worktree，HEAD 精确匹配
   planning base、baseline clean；无关的 prunable 历史记录不计入 live 集合，也不能让本轮 target 误失败；
2. 保存 baseline snapshot 与 `README.md` baseline bytes；
3. stdout 输出一个不含绝对路径的 `BASELINE_READY` 摘要并等待恰好一条有界、EOF-delimited JSON observation；controller
   写入唯一记录后必须关闭 stdin，未封口或等待超时均 fail closed；
4. observation 只接受固定 schema、同一 thread id、`terminal_status=completed`、
   `final_text=READY_FOR_REVIEW`，拒绝额外字段、超限、空行、重复输入、尾随数据、未封口或超时；
5. 收集 completion snapshot，要求无 untracked、仅 `README.md` 改变，且 bytes 精确等于冻结的一行替换；
6. 构造 provider=`codex_app` 的 ready claim，event digest 绑定 canonical host observation；
7. 运行现有 whitelist `ruff` verifier，收集 post-verification snapshot，构造 receipt 并调用 evaluator；
8. 只输出 bounded summary/digests，不持久化 prompt、task output、diff、绝对路径或 raw tool response。

脚本不导入或调用 Codex App task tools，不启动 Codex/provider process，也不把 caller JSON 变成来源证明。真实 task 与
terminal status 只能由本轮 controller 的 native create/wait/read tool metadata 支持。

### 3. Host observation adapter 的 claim ceiling

`HostTaskObservation` 是严格 typed、strict-field、bounded object。它能证明 controller 消费的字段之间机械一致，不能证明
caller 没有伪造 JSON。因此：

- live controller 可报告 `host_task_observed=true`；
- repository summary 固定 `source_provenance=host_observed_unverified`；
- `task_complete=false`、`semantic_completion=false`、`human_review=NOT_OBSERVED`、
  `product_acceptance=false`、`runtime_integration=false`、`git_delivery_authorized=false`；
- evaluator 的 `ready_for_review/VERIFICATION_PASSED` 只表示可以进入人工 review。

fake/injected unit tests 只能证明 adapter/kernel rules，不计作真实 Codex App observation。只有 controller 同时持有本轮
task id、native terminal result 和对应 worktree facts时，才可把这一次标为真实 host observation。

### 4. Snapshot 与 verification 绑定

baseline、completion、runner-before 和 post-verification 都由现有 `collect_git_snapshot` 收集。completion 必须满足：

- repository id 与 baseline 相同；
- HEAD 仍为 planning base；
- 无 untracked/index drift；
- 唯一 changed path 为 `README.md`；
- 当前 bytes 是 baseline bytes 的精确第一行替换。

verification 固定为现有 `ruff` label，不允许附加 argv。bridge 必须在调用现有 runner 前强制
`RUFF_NO_CACHE=true`；测试必须从不存在 `.ruff_cache` 的 fixture 调用真实 whitelist runner，并证明运行后仍不存在缓存。
runner-before 与 post snapshot 必须等于 claim-bound completion snapshot。这里只证明离散稳定端点；验证区间内发生并
恢复的完美 ABA、同用户写权限和 OS 级 isolation 仍未证明。

### 5. 六类确定性故障与 stop condition

以下任一情况均 fail closed，且不得创建第二个 task 或发送第二个 coding turn：

1. task 创建/handshake/terminal 不可观察，status 非 completed，observation schema/长度/相关性错误，或 stdin 未以 EOF
   封口/等待超时；
2. baseline 非 clean、HEAD/repository/live non-prunable worktree registration 不匹配，或 handshake 已修改文件；无关
   prunable 历史记录只忽略该记录，不能替代 stage/task 自身的 live registration；
3. claim 缺失、非精确、thread id 不匹配或 final text 不是唯一 `READY_FOR_REVIEW`；
4. stage worktree 出现 `README.md` 修改、task worktree 出现 untracked/index drift、非 `README.md` 变化或目标 bytes/完整
   digest 不是精确替换；
5. completion、runner-before、post-verification snapshot 任一不一致；
6. verifier 创建 `.ruff_cache` 或其他 bytes、receipt/evaluator 非成功，或 kernel 不返回
   `ready_for_review/VERIFICATION_PASSED`。

外部 task tool unavailable、需要用户交互、worktree 无法定位或 task 请求额外权限，也都直接 `NOT_OBSERVED`，不改走本地
CLI、不继承旧 observation、不搭建新平台。

## Risks / Trade-offs

- [Codex App task tools 不是仓库 runtime] -> 明确限定为 development workflow qualification；后续 runtime adapter 需新阶段。
- [host JSON 可由 controller 伪造] -> 固定 unverified provenance；最终结论同时引用 native host task metadata，不让仓库自证。
- [task worktree 与宿主共享用户身份] -> 任务固定、无敏感输入，只声明 scoped write/snapshot observation，不声明安全隔离。
- [单次样本无稳定性] -> 不算比例、不外推，只报告本次事实。
- [task worktree 可能保留] -> 不自动删除或 archive 用户 task；最终精确报告 task/worktree 状态。

## Implementation Plan

1. authority epoch 5 绑定本路线、当前 base、allowed paths、一次 task/coding turn 与 `implement` ceiling；旧 packet 失效。
2. 更新 OpenSpec/Harness 后完成 internal 与两个 fresh empty-context plan review slots。
3. 先写 host observation、baseline/target/snapshot/receipt 六类 RED tests，再最小修改候选脚本；不改 `app/**`。
4. 跑 focused、changed-file Ruff、OpenSpec strict、`git diff --check` 和 canonical verification。
5. 冻结新 implementation packet，交两个 fresh implementation review slots；修改后回原 slots。
6. review 通过后，按 direct-user epoch 5 authority 创建一次 Codex App task，完成 handshake、baseline、唯一 coding turn、
   verification 与 summary；任一失败不重试。
7. 报告 evidence/unknowns，停止在 unarchived/uncommitted/unmerged/unpushed。

## Open Questions

- Codex App create/wait/read 返回是否足以让 controller 精确关联 task id、completed terminal 和 App worktree？若任一字段或
  worktree 定位不可得，本轮保持 `NOT_OBSERVED`，不扩实现。
