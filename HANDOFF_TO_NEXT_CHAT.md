# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：none。`restore-deterministic-verification-baseline` 已归档到
  `openspec/changes/archive/2026-08-26-restore-deterministic-verification-baseline/`。
- 当前只在干净 worktree `/private/tmp/agentic-codeops-restore-verification.01a03bfc`、分支
  `codex/restore-deterministic-verification-baseline` 开发；planning base 为
  `2c0d0d4e749e16e43d867931c58c6a82be56cf13`。
- 当前小阶段修复 deterministic JSON nesting、Verification Runner 的当前解释器/required-tool fail-closed
  语义和 portable canonical verification entry。全仓 Ruff 机械清理由紧随其后的独立小阶段完成。
- 本文件不保存 controller closeout 的 volatile candidate HEAD、merge 或 push 状态；开始任何 Git mutation
  或新阶段前，必须重新查询 live branch、worktree、target branch、effective endpoint 和 remote tip。
- 本阶段不修改公开 API、权限、持久化、依赖、网络默认值或 RepoPilot runtime Git/subagent 能力。
- 原 `/Users/chelaile/agentic-codeops` 的 `feature/bootstrap-refactor-harness` 工作树仍保留其既有、
  未提交的 storage/Harness 修改；不要在当前 closeout 中进入、整理或覆盖该工作树。

继续前先运行：

```bash
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
python -I scripts/verify.py
```

## 已完成并可依赖的事实

- Stage-change replay 的 V1 graph、event/receipt lineage、exact invalidated/preserved/frontier 集合、CAS append、
  workspace/symlink 边界与 dormant v2 old/new authority delta 已形成 repository-local validator/test 合同。
- 该合同固定为 `mechanical_consistency_only`。11 个 gate adapter、host CAS/restart、native producer execution、
  dispatch、activation、terminal tombstone 与 push reconciliation attestation 均保持 external prerequisite；
  当前 validator 对任何 action 都不会给出可变更 readiness。
- Introducing/in-flight stage 继续由 pre-change v1 流程走到 terminal；v2 仍为
  `blocked_on_external_host_capability`，没有被本阶段激活。
- 前序 `add-stage-change-replay` 的最终 review packet 是
  `7eccf12cf3b8793c52a7e5146ffe6698746f69b19d212f0b0d272aebcf636500`，最终 candidate/pushed commit 是
  `2c0d0d4e749e16e43d867931c58c6a82be56cf13`；旧 `bce8…` 只是中间 packet，不再作为最终事实。
- 当前实现的 full pytest 已通过（`971 passed`），changed-file Ruff 已通过；full Ruff residual 为
  92 项 / 55 文件，canonical verification 在 pytest 全绿后于 Ruff 明确非零停止。Pre-archive
  implementation review 的两个独立 slots 已关闭全部 findings，OpenSpec archive/spec sync 已完成；当前仍需
  final post-archive packet refresh，尚未形成 candidate。
- 当前阶段只允许形成 reviewed local candidate；全仓 Ruff 与 canonical verification 全绿后，才可执行已授权的
  fast-forward merge 和 exact-old-OID lease push。

## Controller Closeout Protocol

Archived tasks 5.3–5.5 是 controller-only delivery protocol。为避免 final packet/candidate 后再写仓库造成
self-invalidation，它们的 live 完成状态不回填到本文件或 archived tasks；必须从当前 Git 状态和 controller 的
最终回执核对。本交接本身不证明 finite candidate、merge、push、remote parity 或 `vcs_pushed=verified`。

1. 完成 post-archive delivery manifest/diff，并让所有 required reviewer slots 刷新到同一 final packet。
2. Final packet 后只写 schema-valid implementation `review-set.json` 和 `delivery-binding.json`；验证后创建
   一个 finite exact candidate commit，并由 host 保留 live candidate HEAD，不把它回写到文档。
3. 只有 manifest、review packet、authority envelope、candidate、target worktree 与 live remote preflight
   全部一致时，controller 才可 `--ff-only` merge，并在 ancestry proof 后使用 exact-old-OID lease push。
4. Push outcome ambiguous 时保持 `UNKNOWN_PUSH_OUTCOME`，只允许 same-endpoint read-only reconciliation；
   不得自动 retry、rebase、force push、改写历史或切换 target。
5. 只有同一 effective endpoint 的 fresh query 证明 target ref 精确等于 candidate，才可报告
   `vcs_pushed=verified`。随后只输出一次 final user handoff，不再写仓库文件。

只有 live controller 状态证明 closeout 完成后，下一会话才可决定是否启动新的小阶段；新阶段必须重新建立
OpenSpec change、allowed files 和 review checklist。
