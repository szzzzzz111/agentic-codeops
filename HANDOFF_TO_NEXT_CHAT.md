# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：无。
- 最近完成阶段：`bind-stage-authority-and-invalidation`；已归档到
  `openspec/changes/archive/2026-08-20-bind-stage-authority-and-invalidation/`。
- 本文件不保存 controller closeout 的 volatile HEAD、merge 或 push 状态；开始任何 Git mutation 或新阶段前，
  必须重新查询 live branch、worktree、target branch、effective endpoint 和 remote tip。
- `.harness/allowed_files.md` 与 `.harness/review_checklist.md` 已重置为无 active stage 状态。
- 本阶段只改变 repository development workflow，没有修改 `app/**`、公开 API、provider runtime、权限、
  持久化或 RepoPilot runtime Git/subagent 能力。
- 原 `/Users/chelaile/agentic-codeops` 的 `feature/bootstrap-refactor-harness` 工作树仍保留其既有、未提交的
  storage/Harness 修改；不要在当前 closeout 中进入、整理或覆盖该工作树。

继续前先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## 已完成并可依赖的事实

- Stage authority 使用 append-only epoch record、delivery binding 和 deterministic validator 机械绑定 exact
  stage/scope/base/action/Git target；live human authority 仍只能由宿主从 direct-user interaction 独立确认。
- Apply/archive 入口在 gate 激活后 fail closed；final review 绑定穷尽 change manifest、精确四路径 metadata
  exclusion 和有限两文件 evidence tail。Merge/push 仍是 controller-only，不是 RepoPilot runtime capability。
- A/B 两个正式 first-round reviewers 的 blocking P1 均通过原 same-slot remediation re-review 关闭；focused
  Stage Debt Sweep 已完成。
- 验证：focused remediation `92 passed`；combined authority + independent-review + CLI `163 passed`；changed
  Python Ruff PASS；OpenSpec pre-archive strict change PASS / all `24 passed, 0 failed`，post-archive all
  `23 passed, 0 failed`；`git diff --check` PASS。
- Full pytest 为 `645 passed, 3 failed`。3 项 inherited baseline 是 model-provider recursion-depth 1 项，以及当前
  shell 无 `python` 命令导致的 verification-runner 2 项；full Ruff 的 96 项也是既有 baseline。不得把这些结果
  描述成 full repository verification PASS。

## Controller Closeout Protocol

Archived tasks 4.5–4.8 是 controller-only delivery protocol。为避免 final packet/candidate 之后再写仓库造成
self-invalidation，它们的 live 完成状态不回填到本文件或 archived tasks；必须从当前 Git 状态和 controller 的
最终回执核对。本交接本身不证明 finite candidate、merge、push、remote parity 或 `vcs_pushed=verified`。

1. 若尚未完成，先完成 task 4.5 的整个原子步骤：核对 durable docs/Harness reset/activation evidence，生成 post-archive
   delivery manifest/diff，并让所有 required reviewer slots 刷新到同一 final packet。
2. Final packet 后只写 schema-valid implementation `review-set.json` 和 `delivery-binding.json`；验证两者后再
   创建 finite exact candidate commit，并由 host 保留 live candidate HEAD，不把该值写回文档。
3. 只有 current manifest、review packet、authority envelope、exact candidate、target worktree 与 live remote
   preflight 全部一致时，controller 才可 `--ff-only` merge，并在 ancestry proof 后使用 exact-old-OID lease push。
4. Push outcome ambiguous 时保持 `UNKNOWN_PUSH_OUTCOME`，只允许 same-endpoint read-only reconciliation；不得
   自动 retry、rebase、force push、改写历史或切换 target。
5. 只有同一 effective endpoint 的 fresh query 证明 target ref 精确等于 candidate 后，才可报告
   `vcs_pushed=verified`。随后只输出一次 final user handoff，不再写仓库文件。

只有 live controller 状态证明上述 closeout 已完成后，下一会话才可决定是否启动新的小阶段；新阶段必须重新建立
OpenSpec change、allowed files 和 review checklist。
