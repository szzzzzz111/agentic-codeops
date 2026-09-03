# 当前 Harness 写入边界

Active OpenSpec change：none。`evaluate-governed-run-cohort` 已归档到
`openspec/changes/archive/2026-09-03-evaluate-governed-run-cohort/`（authority epoch 8）。

Planning base 与 authorized remote tip：
`b7a8439fac9013f5ad59c308c4b16d333d466ddb`（`origin/main`，本轮已同 endpoint 只读核对）。

Risk：high / L3。最终结论仍是一个 source-unverified、snapshot-bound 的 `ready_for_review` 实验；它不证明
Agent 语义完成、人工批准、产品验收、runtime integration 或 Git delivery capability。

Action ceiling：push。用户的条件式交付授权已生效，且实现、真实实验、archive 与归档后验证均已完成。
后续只允许在最终两席复审、delivery binding 和精确 staged-index preflight 通过后执行 finite candidate、
ff-only merge 与 exact-old-tip lease push。

## Stage worktree 允许路径

下列清单只约束当前开发 stage worktree。`README.md` 不在其中，stage implementer 不得修改它。

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0001.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0002.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0003.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0004.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0005.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0006.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0007.json`
- `.harness/authority/evaluate-governed-run-cohort/epoch-0008.json`
- `.harness/authority/evaluate-governed-run-cohort/delivery-binding.json`
- `.harness/reviews/evaluate-governed-run-cohort/plan/review-set.json`
- `.harness/reviews/evaluate-governed-run-cohort/implementation/review-set.json`
- `.harness/reviews/evaluate-governed-run-cohort/implementation/reviewed-change-manifest.json`
- `.harness/reviews/evaluate-governed-run-cohort/implementation/reviewed-change.diff`
- `openspec/changes/evaluate-governed-run-cohort/.openspec.yaml`
- `openspec/changes/evaluate-governed-run-cohort/proposal.md`
- `openspec/changes/evaluate-governed-run-cohort/design.md`
- `openspec/changes/evaluate-governed-run-cohort/tasks.md`
- `openspec/changes/evaluate-governed-run-cohort/plan-review.md`
- `openspec/changes/evaluate-governed-run-cohort/specs/governed-run-cohort-evaluation/spec.md`
- `openspec/changes/archive/2026-09-03-evaluate-governed-run-cohort/**`
- `openspec/specs/governed-run-cohort-evaluation/spec.md`
- `openspec/specs/README.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `scripts/evaluate_single_governed_run.py`
- `tests/test_single_governed_run_evaluation.py`
- `tests/fixtures/single_governed_run/pytest.ini`
- `tests/fixtures/single_governed_run/result.txt`
- `tests/fixtures/single_governed_run/test_result.py`

## Host-managed 实验边界

- 只创建一个全新 Codex App task，并由 App 从 exact base 创建独立 worktree；不 fork 当前实现对话。
- handshake turn 只回复 `READY_FOR_TASK` 且不得改文件；baseline clean 后只发送一个固定 coding turn。
- task worktree 是与 stage worktree 分离的唯一实验角色；其唯一 mutation authority 是把 base `README.md` 的完整 bytes
  `sha256:70e242e898295dffaeb9a9723c5536edb96b5b6429e94fea274925a4a8b4e64e` 精确变为
  `sha256:d7844da1d65cabe3307959c6ac9a510e483bcdb99ad5070b280bdea0c33d575c`，即只替换第一行；禁止 commit。
- stage worktree 若修改 `README.md`，或 task worktree 修改任何其他 path/bytes，均 fail closed。
- stage/task 必须同属一次 `git worktree list --porcelain` 的 live non-prunable 集合；无关 prunable 历史记录只排除自身，
  不得替代 stage/task 的 live registration，也不能让有效 pair 误失败。
- 候选脚本只消费一次 bounded、EOF-delimited host observation；controller 写入唯一记录后关闭 stdin，未封口或超时均
  fail closed；脚本不调用 Codex App tools、不启动本地 Codex/provider process。
- verification 固定使用现有 `ruff` label；bridge 在调用 runner 前强制 `RUFF_NO_CACHE=true`，且真实 runner 测试必须证明
  不创建 `.ruff_cache`；completion/runner-before/post snapshot 必须完全相同。
- native task/create/wait/read metadata 由外部 controller 保留，仓库只给 mechanical binding；provenance 保持 unverified。

## 明确禁止

- 不写原脏 worktree `/Users/chelaile/agentic-codeops`，不让 target task 写该 worktree。
- 除本 change 的 archive sync 外，不修改 `app/**`、其他长期 specs/archives、公开 API/CLI/ToolRegistry/provider/persistence。
- 不运行本地 `codex --version`/`codex exec`，不安装或 chmod Codex，不搭 VM/container/credential proxy。
- 不实现 runtime subagent、Codex App plugin/API、daemon、后台 supervisor、重试/resume、cohort rate、多 Agent或自动纠偏。
- 不持久化 raw task output、tool response、prompt、diff、绝对 worktree path 或 credential material。
- 不把 `ready_for_review`、task terminal、verification PASS 或 AI review写成语义完成、真人批准、产品验收或 Git 授权。
- Git 交付只属于本阶段 controller 的 finite closeout，不成为 RepoPilot runtime 自动 commit/merge/push 能力。
- 不删除、清理或自动 archive 用户 task/worktree。
- 不创建下一产品阶段，不采用非 ff-only 合并，不向 `origin/main` 以外 push，不削弱 exact-old-tip lease。

## Stop conditions

- remote tip、target branch、base、allowed paths、risk、task/turn count 或 action ceiling 漂移。
- fresh task/worktree 无法创建或关联，handshake 修改文件，baseline 不 clean，或 task 请求额外权限/用户输入。
- second task、second coding turn、retry/resume、非固定 prompt 或 local CLI fallback。
- terminal/final claim 不精确，observation channel 未 EOF 封口或超时，thread/worktree correlation 缺失，非目标路径/bytes
  变化，verification/receipt/snapshot 失败。
- 需要修改 `app/**`、建设 runtime adapter/隔离平台，或升级 source/security/product/Git claim。
