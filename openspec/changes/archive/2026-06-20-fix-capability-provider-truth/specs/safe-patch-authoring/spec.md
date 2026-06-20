## MODIFIED Requirements

### Requirement: Patch proposal 由仓库证据约束

系统 SHALL 在明确 patch 请求时基于 repo evidence 生成 patch proposal。Patch proposal MUST 先经过现有 `repo_rag` / Evidence Pack 边界，MUST NOT 只凭模型自由生成。

默认应用装配 MUST 使用离线确定性的 fake Patch Authoring provider，并且 MUST NOT 生成真实 diff。仓库 MAY 提供可通过依赖注入使用的 `ModelPatchAuthoringProvider` 实现边界，但当前默认 `AgentLoop` / `PatchManager` 装配 MUST NOT 被描述为可通过现有 Model Provider 环境变量启用真实 patch proposal。未来若增加该装配，MUST 通过独立 change 定义配置、安全和验证边界。

任何注入的 Patch Authoring provider 返回结构化 JSON unified diff 时，系统 MUST 在创建 pending patch 前校验 schema、citation、路径和 diff。

#### Scenario: 默认 provider 不生成真实 diff

- **WHEN** 用户请求生成 patch proposal 且使用默认应用装配
- **THEN** 系统返回安全 fallback
- **AND** 系统 MUST NOT 创建 pending patch
- **AND** 系统 MUST NOT 修改文件

#### Scenario: Model Provider 环境配置不隐式启用 patch provider

- **WHEN** 应用只配置现有 `REPOPILOT_MODEL_PROVIDER` 等共享 Model Provider 环境变量
- **THEN** 默认 `PatchManager` 仍使用 fake Patch Authoring provider
- **AND** 系统 MUST NOT 声称真实 patch diff generation 已启用

#### Scenario: 注入的合法结构化 diff 创建 pending patch

- **WHEN** 调用方显式依赖注入 Patch Authoring provider 且其返回合法结构化 diff
- **THEN** 系统创建 pending patch
- **AND** 公开回答包含 patch 摘要、目标文件、patch id 和确认方式
- **AND** 公开回答 MUST NOT 暴露完整 diff 文本
