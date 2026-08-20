# Independent Implementation Review Record

## First Round

- Reviewer：`/root/final_implementation_review`
- Provider/model：OpenAI Codex / GPT-5（宿主未暴露更精确 deployment id）
- Host dispatch：new subagent task，`fork_turns="none"`
- Other implementation first-round conclusions visible：`false`
- Frozen packet：`44d2dbd713a00442785b221bf8ec1a15729fe37f1cbb8204cf8186417184d234`
- Hash gate：22/22 artifacts matched
- Verdict：`FINDINGS`，semantic approval blocked

## Finding Dispositions

| ID | Severity | Disposition | Implemented response |
| --- | --- | --- | --- |
| `IRV-P1-001` | P1 | `fix` | Validator claim ceiling 改为 `mechanical_consistency_only` / `gate_ready=false`；宿主 dispatch provenance 成为 required external check，不再把仓库自填字段描述成 host attestation。 |
| `IRV-P1-002` | P1 | `fix` | Remediation lineage 必须解析并完整校验 content-hashed original first-round receipt 的 schema/reviewer/context/packet/artifacts/conclusion，核对同一 slot/reviewer/implementer，并要求关闭原 finding IDs 的完整集合。 |
| `IRV-P1-003` | P1 | `fix` | Activation timing 明确保留给 pre-change process authority；validator 只绑定 activation record path/hash，并把 activation sequence 列为 required external check。 |
| `IRV-P1-004` | P1 | `fix` | Stage planner 仅在风险合同要求 independent plan review 时生成 receipt；medium/high 为 2，low-risk 使用 checklist 明确数量或 0。 |
| `IRV-P2-005` | P2 | `fix` | Final conclusion 改为 structured findings + disposition/closure + gate verdict；矛盾 no-findings 和 open final findings 均 fail closed。 |
| `IRV-P2-006` | P2 | `fix` | Artifact paths 拒绝 absolute、`.`/`..` alias、symlink 和重复 resolved target；CLI 拒绝 unsafe stage id、非固定 relative receipt path 与 symlink receipt。 |
| `IRV-P2-007` | P2 | `fix` | OpenCode adapter 移除必需 Codex/OpenCode 品牌 gate 的残余文案，改为 risk-contract slots/receipts，同时保留 adapter-specific isolation/recovery。 |

## First Remediation Re-review

- Frozen packet：`53aa7428c4305d71587e8e8ed06f85dc4f7f8a78dd1913eec929476c19e3d17e`
- Hash gate：25/25 artifacts matched
- Closed：`IRV-P1-001`、`IRV-P1-003`、`IRV-P1-004`、`IRV-P2-005`、`IRV-P2-006`、`IRV-P2-007`
- Still open：`IRV-P1-002`。原因：历史 receipt 尚未按完整 receipt schema 检查，且 final remediation 允许只关闭
  原 findings 的非空子集。
- Response：新增完整 history receipt mechanical validation，并把 `closed_finding_ids` 从 subset 改为原 finding
  IDs 的精确集合；新增 3 个 RED→GREEN 反例。

## Second Remediation Re-review

- Frozen packet：`48fac0b0d1247c448eda37d7667a66e18eeb999b3c95584be3a59064d6c814d1`
- Hash gate：26/26 artifacts matched
- Closed：原 `IRV-P1-002` 的 incomplete-history 与 partial-closure fail-open 已关闭；首轮 7 个 findings
  均保持 closed。
- New open：`IRV-R2-P1-001`。原因：exact-set 条件额外强制 `closed_finding_ids` 非空，导致另一席位首轮
  `no_findings` 后无法用空集对空集刷新 remediation final baseline。
- Response：先新增双席位 clean-slot refresh 正样本并确认 RED，再移除非空限制；仍保留 list/type 与原
  finding IDs 的精确集合相等约束。聚焦套件 GREEN：`32 passed`。

## Closure Boundary

本文件只记录 findings、implementer disposition 和中间 re-review 事实，不自行声称最终 findings 已关闭。Closure 以同一
reviewer slot 对修复后新 packet 的 remediation re-review、实际 receipt set 中 content-hashed original
receipt lineage、validator 机械一致性 PASS，以及宿主 dispatch/activation 两项 external checks 为准。
