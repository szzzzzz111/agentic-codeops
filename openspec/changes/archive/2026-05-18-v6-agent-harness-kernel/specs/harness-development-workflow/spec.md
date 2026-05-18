# harness-development-workflow Delta

## MODIFIED Requirements

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

#### Scenario: 新阶段规划

- **WHEN** 规划 V6 或后续阶段
- **THEN** proposal/design/tasks 明确该阶段的纵向切片
- **AND** 明确默认实现是否为内存、JSON、SQLite 或其它轻量实现
- **AND** 若引入 PostgreSQL、Milvus、Elasticsearch、Kafka 等重依赖，必须在 spec 中说明必要性

#### Scenario: 能力演进

- **WHEN** 新增 RAG、Memory、Skill、Provider 或 Tool 能力
- **THEN** 系统优先定义可替换接口和安全摘要
- **AND** 不把未来 Roadmap 能力写成已实现
