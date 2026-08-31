# 测试命令

## 单元测试和 API 测试

```bash
python -I -m pytest
```

## 一键验证

```bash
python -I scripts/verify.py
```

PowerShell host 等价入口：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。

## 阶段文档漂移扫描

```bash
python -I scripts/check_stage_docs.py
```

PowerShell host 等价入口：`powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1`。

## Skill eval 结构扫描

```bash
python -I scripts/check_skill_evals.py
```

PowerShell host 等价入口：`powershell -ExecutionPolicy Bypass -File scripts/check_skill_evals.ps1`。

## 阶段归档收口检查

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1
```

## Stage authority focused tests

```bash
pytest -q tests/test_stage_authority_validation.py
```

## Dormant stage change replay focused tests

```bash
pytest -q tests/test_stage_change_replay_validation.py tests/test_stage_authority_validation.py
```

Replay validator 的 PASS 只表示 `mechanical_consistency_only`，当前不能授权或阻断任何 v1 mutation。
本 introducing stage 和所有已在 flight 的 v1 stage 保持 pre-change 流程到 terminal。Future blocking v2
必须由后续独立 stage 提供真实 `provider_neutral.stage_state_cas/v1` capability/restart/CAS/dispatch/activation
evidence；repository fixture、CLI flag、activation hash 或 v2 template 均不能代替。调用接口时必须显式传入
immutable workspace binding、terminal state、gate snapshot 与 host-retained event/receipt prior/current
counts/heads；exact CLI flags 以 `python scripts/validate_stage_change_replay.py --help` 和 focused tests 为准。

Activated-v2 governed actions 固定映射为 `implement -> implementation`、`archive -> archive`、
`commit -> candidate`、`merge -> merge`、`push -> push`，且必须等于 current frontier；不存在
`unaffected action` bypass。当前 v1 authority 命令与 active v1 templates 保持原样。

Stage authority 的 action preflight 需要宿主保留的完整 expected envelope，不能从 authority record
自动回填。按当前 stage 的真实值运行：

```text
python scripts/validate_stage_authority.py \
  --project-root . \
  --authority-dir .harness/authority/<stage-id> \
  --required-action <implement|commit|archive|merge|push> \
  --expected-stage <stage-id> \
  --expected-epoch <epoch> \
  --expected-authority-record-sha256 <record-sha256> \
  --expected-risk <low|medium|high> \
  --expected-scope-sha256 <scope-sha256> \
  --expected-planning-base <commit-oid> \
  --expected-action-ceiling <plan|implement|commit|archive|merge|push> \
  --expected-remote-name <remote> \
  --expected-effective-fetch-url-sha256 <fetch-url-sha256> \
  --expected-effective-push-url-sha256 <push-url-sha256> \
  --expected-target-branch <branch> \
  --expected-authorized-remote-tip <remote-tip-oid>
```

当 authority scope 含 `review_slot_requirements` 时，`implement` preflight 还必须传入宿主保留的
plan-review inputs：

```text
  --plan-review-set .harness/reviews/<stage-id>/plan/review-set.json \
  --required-plan-review-slots <bound-plan-slot-count> \
  --expected-plan-review-packet-sha256 <host-retained-plan-packet-sha256>
```

这三个参数缺失或不匹配必须 fail closed。没有该 binding 的 legacy record 保持既有兼容路径，但不得
声称 authority-bound slot count。

Finite candidate `commit`、merge、push 还必须传入实际 implementation review set、required slot count、
host-retained packet hash 与 delivery binding；archive 需要前三项 review inputs。Merge/push 另外需要
exact candidate HEAD。对应 flags 为
`--implementation-review-set`、`--required-review-slots`、`--expected-review-packet-sha256`、
`--delivery-binding`、`--expected-candidate-head`、`--explicit-source-oid`。Merge 还必须传
`--merge-target-worktree` 与 `--expected-target-premerge-head`；其中 target worktree 必须来自同一 Git
common directory，pre-merge HEAD 必须等于 authority 绑定的旧 remote tip。Merge/push 都会现场解析并查询
同一个 effective endpoint。命令成功仍只证明 mechanical consistency，不证明 live human authority 或
push 成功。

运行 `--required-action commit` 前，controller 必须先把 reviewed manifest 的全部 subjects 与精确四个
metadata/tail paths 暂存到 index，并运行 `git diff --cached --check`。Commit preflight 会只读检查 staged
path set、stage-0 regular mode、file/deletion state 与 blob bytes/hash；任何 `CANDIDATE_INDEX_*` 错误都阻断
candidate，不得靠后续 `git add` 改变已验证的 index。
Current reviewed manifest/inventory 使用 v2：每个普通文件 subject/FILE 行都显式绑定 `100644` 或
`100755`；删除项仍只包含 path/kind。缺失或非法 mode、以及 review 后 worktree/index 同步 chmod 都必须
结构化 fail closed。
四个被 manifest 排除的 metadata/tail paths 使用 code-owned canonical mode `100644`；它们的 worktree
与 index mode 即使同步改成 `100755`，commit preflight 也必须返回 `CANDIDATE_INDEX_MODE_MISMATCH`。

## 静态检查

```bash
ruff check .
```

## 本地 API 服务

```bash
uvicorn app.main:app --reload
```

## 手动聊天请求

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u001",
    "session_id": "s001",
    "message": "帮我分析为什么测试失败",
    "repo_path": "./mock_repo"
  }'
```
