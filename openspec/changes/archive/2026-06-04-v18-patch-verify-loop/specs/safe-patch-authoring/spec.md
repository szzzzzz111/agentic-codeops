## MODIFIED Requirements

### Requirement: Patch apply 必须明确确认

系统 SHALL 只接受明确确认语法应用 patch：`应用 patch <patch_id>`、`确认 patch <patch_id>`、`apply patch <patch_id>` 和 `confirm patch <patch_id>`。系统 MUST NOT 接受“可以”“继续”“就这样”等含糊表达作为 apply 确认。

V18 MAY 支持明确组合确认语法，将 pending patch apply 与白名单 verification run 串联。组合确认 MUST 同时包含有效 patch id 和有效 verification label；任一缺失或不安全时 MUST 拒绝整个组合请求，并且 MUST NOT apply patch。

#### Scenario: 含糊确认不触发 apply

- **WHEN** 用户发送 `可以`
- **THEN** 系统 MUST NOT 执行 `patch_apply`
- **AND** 系统 MUST NOT 修改文件

#### Scenario: 组合确认缺失验证标签不触发 apply

- **WHEN** 用户发送类似组合确认但只包含 patch id
- **THEN** 系统 MUST 拒绝组合请求
- **AND** 系统 MUST NOT 执行 `patch_apply`
