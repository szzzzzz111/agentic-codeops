# 当前 Harness 写入边界

当前暂无活跃开发阶段。

新阶段开始前，必须先用 OpenSpec 创建 change，并把本文件更新为该阶段允许修改的文件列表。

默认规则：

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 写成 RepoPilot runtime 能力，除非阶段 spec 明确开放。
- 不修改 `app/`、`tests/` 或长期 `openspec/specs/` 行为，除非新阶段 allowed files 明确允许。
