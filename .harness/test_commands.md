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
