# 交接给下一轮 Chat

## 当前基线

- 当前隔离分支：`codex/independent-review-provider`；工作目录：
  `/private/tmp/agentic-codeops-independent-review.H3nBHU`。
- Active OpenSpec change：`generalize-independent-review-provider`，当前未 archive。
- 本阶段从稳定 `main` 基线 `17010b6` 建立隔离 worktree；原
  `/Users/chelaile/agentic-codeops` 的 storage/Harness 未提交修改不属于本阶段，禁止覆盖或带入。
- 本阶段没有执行 commit、merge 或 push，也未获得这些动作的授权。

继续前先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## Active OpenSpec change

`generalize-independent-review-provider` 把开发工作流中的独立评审从固定 Agent 品牌改成可验证的 reviewer
slots，同时保持评审强度：

- Medium/high plan review 仍为 internal review 加两个 independent plan-review slots。
- Final implementation review 的 required slot 数量继续由阶段风险合同决定。
- Codex 只有通过新的 empty-context task 或宿主明确记录 `fork_turns="none"` 的 subagent 才能替代任一 slot；
  inherited/unknown context 不计数。
- 首轮 reviewer 彼此盲审同一个冻结 packet；same-slot remediation re-review 可以复用原 reviewer，但所有
  required slots 最终必须绑定同一个 content-addressed baseline。
- OpenCode skill 仍保留为 adapter；首轮必须新建/证明隔离 session，session reuse 只用于同一 slot 的修复复审
  或恢复同一次 timeout。
- 这些 task/subagent 是 development workflow 手段，不是 RepoPilot runtime capability。

## 当前实现状态

- Workflow rules、long-term spec、stage planner/workflow/review-loop skills 和 OpenCode adapter 已同步到同一合同。
- 已新增固定 receipt template 和 `scripts/validate_independent_review.py`；validator 校验固定 receipt-set 路径、
  stage/phase/count、声明的 reviewer/implementer/context/首轮可见性、canonical artifact paths/hashes、packet hash、
  闭合 final conclusion 和 content-hashed original receipt-bound remediation lineage。它只证明机械一致性，
  固定 `gate_ready=false`；宿主 dispatch provenance 和 activation sequence 仍是外部门禁。
- 新 validator 不追溯验证本 change 的 plan review；`plan-review.md` 保留变更前 manual contract 的冻结 hashes、
  8 个已修复 findings 和 same-slot re-review 记录。
- 当前未修改 `app/**`、runtime API、provider runtime、权限、持久化、Git/subprocess 执行或默认 CI。

## 已有验证

- RED：原 workflow/OpenCode 结构断言失败；validator 模块缺失；新增固定路径用例在路径未校验时失败。
- GREEN：聚焦 workflow/validator tests `32 passed`；changed Python files Ruff PASS；`git diff --check` PASS。
- OpenSpec：strict active-change validation PASS；`openspec validate --all` 为 `23 passed, 0 failed`。
- 当前环境没有 `powershell`/`pwsh`，所以 `scripts/verify.ps1`、`check_stage_docs.ps1` 和
  `check_skill_evals.ps1` 未直接运行；翻译后的 stage-doc/skill-eval 结构检查退出 0。
- 全仓 pytest 为 `537 passed, 3 failed`：失败均在本阶段未修改路径，分别是 recursion-depth provider 用例和
  两个依赖 `python` 命令名的 verification-runner 用例。全仓 Ruff 有 97 个既有问题；不要据此宣称 full verify
  PASS，也不要在这个 process-only change 中越界修复。

## Resume / Completion Check

先检查 `.harness/reviews/generalize-independent-review-provider/implementation/review-set.json`：

- 若文件不存在，必须对冻结的 implementation/spec/skill/test/docs packet 运行一个新的 empty-context Codex
  independent review。若有 finding，按 `fix / clarify / reject / defer` 处理；修复后复用同一 slot 做 remediation
  re-review，并重新冻结 baseline，然后创建实际 receipt set。
- 若文件存在，运行下面的 validator；只有零退出、宿主控制器已直接核对 native dispatch metadata、变更前流程
  authority 已核对 activation sequence、active tasks/checklist 已完成且没有后续 implementation/spec/skill/test/docs
  变更，才能把 final independent review 计为完成。Repository receipt 中自填字段不能替代前两项外部核对。

```text
python scripts/validate_independent_review.py \
  --project-root . \
  --receipt-set .harness/reviews/generalize-independent-review-provider/implementation/review-set.json \
  --expected-stage generalize-independent-review-provider \
  --expected-phase implementation \
  --required-slots 1
```

完成后仍保持 change active，停止于未 commit/merge/push 状态；只有用户后续明确授权时才能执行相应 Git closeout。
