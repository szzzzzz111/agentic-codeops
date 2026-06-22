## MODIFIED Requirements

### Requirement: Patch proposal 由仓库证据约束

系统 SHALL 在明确 patch 请求时基于 repo evidence 生成 patch proposal。Patch proposal MUST 先经过
现有 `repo_rag` / Evidence Pack 边界，MUST NOT 只凭模型自由生成。

默认应用装配 MUST 使用离线确定性的 fake Patch Authoring provider，并且 MUST NOT 生成真实 diff。
仓库 MAY 提供可通过依赖注入使用的 `ModelPatchAuthoringProvider` 实现边界，但当前默认
`AgentLoop` / `PatchManager` 装配 MUST NOT 被描述为可通过现有 Model Provider 环境变量启用真实
patch proposal。

`ModelPatchAuthoringProvider` MUST 使用 `json_object` output mode，并显式提供只包含 patch proposal
JSON shape 的 structured output instruction。Patch query MUST 只表达用户修改意图，MUST NOT 重复
拼接 JSON 格式指令。Provider status 非 success 时 MUST 在业务解析前返回安全失败。Provider 只负责
基础 JSON object 校验；ModelPatchAuthoringProvider 继续校验业务字段，PatchManager 继续校验
citation、target files、路径和 unified diff。

#### Scenario: 默认 provider 不生成真实 diff

- **WHEN** 用户请求生成 patch proposal 且未显式配置真实 provider
- **THEN** 系统返回安全 fallback
- **AND** 系统 MUST NOT 创建 pending patch
- **AND** 系统 MUST NOT 修改文件

#### Scenario: Model Provider 环境配置不隐式启用 patch provider

- **WHEN** 应用只配置现有 `REPOPILOT_MODEL_PROVIDER` 等共享 Model Provider 环境变量
- **THEN** 默认 `PatchManager` 仍使用 fake Patch Authoring provider
- **AND** 系统 MUST NOT 声称真实 patch diff generation 已启用

#### Scenario: 注入 provider 使用独立结构化 instruction

- **WHEN** 调用方显式依赖注入 `ModelPatchAuthoringProvider`
- **THEN** provider request MUST 携带 patch proposal structured output instruction
- **AND** query MUST NOT 重复 JSON shape 指令

#### Scenario: 注入的合法结构化 diff 创建 pending patch

- **WHEN** 调用方显式依赖注入 Patch Authoring provider 且其返回合法结构化 diff
- **THEN** 系统创建 pending patch
- **AND** 公开回答包含 patch 摘要、目标文件、patch id 和确认方式
- **AND** 公开回答 MUST NOT 暴露完整 diff 文本
