# 交接给下一轮 Chat

## 当前基线

- 当前主线为 `main`，已与 `origin/main` 同步。
- Active OpenSpec change：无；最近完成阶段是 `generalize-independent-review-provider`，已归档到
  `openspec/changes/archive/2026-08-20-generalize-independent-review-provider/`。
- 本阶段是 process-only 开发工作流变更，没有修改 `app/**`、公开 API、权限、持久化、provider runtime
  或 RepoPilot runtime subagent 能力。
- 原 `/Users/chelaile/agentic-codeops` 的 `feature/bootstrap-refactor-harness` 工作树仍保留其既有、未提交的
  storage/Harness 修改；本阶段没有覆盖或带入这些文件。

继续前先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## 最近完成的流程能力

- Medium/high planning 继续要求 internal review 加两个 independent review slots；final implementation review
  的 slot 数量继续由阶段风险合同决定。OpenCode、Codex 或其他受支持工程 Agent 都只是 adapter，不再按品牌设门禁。
- Codex 首轮独立评审必须来自新的 empty-context task，或宿主明确记录 `fork_turns="none"` 的 subagent；
  inherited/unknown context、implementer 自审、先看到其他首轮结论和跨 slot reviewer 复用均 fail closed。
- Remediation re-review 可复用同一 slot 的 reviewer 以保留 finding lineage，但所有 required slots 最终必须绑定
  同一 content-addressed baseline。
- 新增固定 receipt template 和 `scripts/validate_independent_review.py`，校验 canonical artifact hashes、packet、
  identity/context 声明、首轮盲审、结论和 remediation lineage。Validator 的 claim ceiling 固定为
  `mechanical_consistency_only` / `gate_ready=false`；宿主 dispatch provenance、activation sequence 和人工审批仍是
  独立的外部门禁，不能由仓库内自填回执替代。
- OpenCode adapter 保留；上述 development task/subagent/review 机制不是 RepoPilot runtime capability。

## 验证与已知限制

- Focused workflow/validator tests：32 passed；changed Python files Ruff PASS；`git diff --check` PASS。
- Archive 后 OpenSpec validation：22 passed、0 failed；当前没有 active change。
- Empty-context Codex final review 的初轮 findings 已全部修复；同 slot 最终复审为 `NO_FINDINGS`，实际 receipt set
  已通过 validator。宿主另行核对了 `fork_turns="none"` dispatch 与 activation sequence。
- 当前 macOS 环境没有 `powershell` / `pwsh`，因此没有直接运行 `scripts/verify.ps1`。等价全仓 pytest 为
  537 passed、3 failed，失败均在未修改路径；全仓 Ruff 有 97 个既有问题。本阶段只对 changed Python files
  形成 Ruff PASS，不宣称 full verify PASS。

## 下一步

- 下一步由用户决定是否启动新的小阶段；开始前创建或选择 OpenSpec change，并同步
  `.harness/allowed_files.md` 与 `.harness/review_checklist.md`。
- 不要把本次 provider-neutral review workflow 写成 RepoPilot runtime subagent、MCP、plugin 或自动审批能力。
- 若继续 storage refactor，应回到原 `feature/bootstrap-refactor-harness` 工作树，先重新蒸馏其真实状态和写入边界；
  不要从当前已收尾的 process-only 阶段推断 storage 变更已验收。
