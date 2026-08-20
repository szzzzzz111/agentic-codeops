# 当前 Review 清单

Active OpenSpec change：无。

当前没有 active stage review checklist。启动新阶段前，必须先按最新 RepoPilot 工作流重新创建
或同步 `.harness/allowed_files.md` 与本文件。

最近完成阶段：`generalize-independent-review-provider`。

- OpenSpec archive：`openspec/changes/archive/2026-08-20-generalize-independent-review-provider/`
- Risk：low / process-only
- Result：开发工作流的独立评审从固定 Agent 品牌改为可验证的 reviewer slots；OpenCode 保留为可选 adapter，
  Codex 只有通过 empty-context task 或明确 `fork_turns="none"` 的 subagent 才能计为独立首轮评审。
- Human gate：人工方向、边界、行为语义、风险接受和 push 授权仍是独立门禁，不能由 Agent receipt 或 validator 替代。
- Non-goals：未修改 `app/**`、公开 API、权限、持久化、provider runtime、默认 CI 或 RepoPilot runtime 能力。
- Final review：empty-context Codex 初轮 findings 全部关闭，最终 same-slot re-review 为 `NO_FINDINGS`；实际
  receipt set validator 零退出，宿主 dispatch provenance 与 activation sequence 已另行核对。
- Verification：focused tests 32 passed；changed Python files Ruff PASS；archive 后 OpenSpec validation
  22 passed、0 failed；`git diff --check` PASS。当前主机无 PowerShell；全仓 pytest 的 3 个失败和 Ruff 的
  97 个问题均为未修改路径的既有基线，因此未宣称 full verify PASS。
- Closeout：implementation/archive 已进入 `main` 并推送；原 dirty storage-refactor 工作树保持不变。
