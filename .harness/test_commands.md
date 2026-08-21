# 测试命令

## 单元测试和 API 测试

```bash
pytest
```

## 一键验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

## 阶段文档漂移扫描

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1
```

## Skill eval 结构扫描

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_skill_evals.ps1
```

## 阶段归档收口检查

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1
```

## Stage authority focused tests

```bash
pytest -q tests/test_stage_authority_validation.py
```

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

Merge/push 还必须传入实际 implementation review set、required slot count、host-retained packet hash 与
delivery binding/exact candidate HEAD；archive 需要前三项 review inputs。对应 flags 为
`--implementation-review-set`、`--required-review-slots`、`--expected-review-packet-sha256`、
`--delivery-binding`、`--expected-candidate-head`、`--explicit-source-oid`。Merge 还必须传
`--merge-target-worktree` 与 `--expected-target-premerge-head`；其中 target worktree 必须来自同一 Git
common directory，pre-merge HEAD 必须等于 authority 绑定的旧 remote tip。Merge/push 都会现场解析并查询
同一个 effective endpoint。命令成功仍只证明 mechanical consistency，不证明 live human authority 或
push 成功。

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
