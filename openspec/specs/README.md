# OpenSpec Specs

本目录保存 RepoPilot 当前长期 capability specs。Active change 的 spec delta 在归档前位于
`openspec/changes/<change-name>/specs/`，归档时再同步到这里。下面的链接集合必须与直接包含 `spec.md`
的 capability directories 精确一致；`scripts/check_stage_docs.py` 会检查缺项和陈旧入口。

## Runtime Entry And Control

- [agent-loop-tool-execution](agent-loop-tool-execution/)
- [assistant-control-surface](assistant-control-surface/)
- [chat-api](chat-api/)
- [demo-ready-agent-cli](demo-ready-agent-cli/)
- [long-task-agent-execution](long-task-agent-execution/)
- [memory](memory/)

## Retrieval, Answering And Patch

- [grounded-answer-model-provider](grounded-answer-model-provider/)
- [live-model-provider-eval](live-model-provider-eval/)
- [patch-verify-loop](patch-verify-loop/)
- [persistent-audit-recovery](persistent-audit-recovery/)
- [repo-query-understanding-rag](repo-query-understanding-rag/)
- [safe-patch-authoring](safe-patch-authoring/)
- [safe-repository-file-tools](safe-repository-file-tools/)
- [skill-metadata-loader](skill-metadata-loader/)
- [verification-runner](verification-runner/)

## Worktree And Mutation Safety

- [repo-mutation-locking](repo-mutation-locking/)
- [verified-patch-promotion](verified-patch-promotion/)
- [worktree-disposal-reconciliation](worktree-disposal-reconciliation/)
- [worktree-inspection](worktree-inspection/)
- [worktree-isolation](worktree-isolation/)
- [worktree-reverification](worktree-reverification/)

## Repository Development Workflow

- [governed-run-contract](governed-run-contract/)
- [harness-development-workflow](harness-development-workflow/)
- [real-agent-observability-qualification](real-agent-observability-qualification/)
- [stage-authority-binding](stage-authority-binding/)
- [stage-change-replay](stage-change-replay/)
