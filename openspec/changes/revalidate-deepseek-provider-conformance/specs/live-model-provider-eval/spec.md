## MODIFIED Requirements

### Requirement: Change 归档表示 evaluator readiness

Change SHALL 把 evaluator readiness 与 provider conformance 分离。Prompt Injection 等
provider/system conformance gate MUST 保持 hard gate；FAIL run MUST 继续返回退出码 1。已归档的
evaluator capability MAY 通过独立 revalidation change 在新的 clean commit 上重新评测 provider，
但历史 tracked evidence MUST 保持不可变。

#### Scenario: PASS evidence 允许 evaluator closeout

- **WHEN** 最终 clean committed evaluator 的所有 live hard gates PASS
- **AND** PASS-only attestation 与本地报告 hash 复核一致
- **THEN** change MAY 在 deterministic verification、formal review 和 closeout evidence 完整后归档
- **AND** 被测 provider MAY 被描述为通过该 profile/rubric 的 conformance gate

#### Scenario: 可信 FAIL baseline 允许 evaluator closeout

- **WHEN** 最终 clean committed evaluator 产生有效 evaluated-failure record
- **AND** failure record 与本地报告 hash、evaluator commit、provider/model、rubric 和失败 gate 复核一致
- **THEN** change MAY 在 deterministic verification、formal review 和 closeout evidence 完整后归档
- **AND** 文档 MUST 明确归档仅表示 evaluator readiness
- **AND** 被测 provider MUST 明确记录为未通过对应 conformance gate
- **AND** 历史本地 FAIL 报告 MUST NOT 被倒推为 tracked failure record

#### Scenario: 独立 revalidation 生成新的 PASS attestation

- **WHEN** evaluator capability 已归档且历史运行保留 evaluated-failure record
- **AND** 独立 revalidation change 在新的 clean commit 上完整执行相同 profile/rubric 的 live gate
- **AND** 所有 hard gates PASS
- **THEN** runner SHALL 生成绑定该新 commit 与运行时间的 PASS-only attestation
- **AND** 历史 evaluated-failure record MUST NOT 被删除、覆盖或改写
- **AND** provider conformance 声明 MUST 只适用于 attestation 记录的 commit、profile 和 rubric

#### Scenario: 独立 revalidation 的 FAIL record 只允许暂停

- **WHEN** 独立 revalidation change 执行相同 profile/rubric 的 live gate
- **AND** runner 生成有效 evaluated-failure record
- **THEN** failure record MAY 被提交到当前 revalidation 分支作为暂停现场证据
- **AND** change MUST NOT archive、merge 到 `main` 或 push 为完成态
- **AND** failure record MUST NOT 被描述为 provider certification evidence
- **AND** 后续 remediation 或 FAIL-baseline closeout MUST 通过正式 reshape 契约处理
