# 当前 Harness 写入边界

Active OpenSpec change：none。repair-documentation-information-architecture 已归档到
openspec/changes/archive/2026-08-31-repair-documentation-information-architecture/。

Planning base 与 authorized old remote tip：
1d6f45f734124d009fa72cc54cbb080c5caa6c44。

Risk：high。本阶段完成 documentation information architecture 修复，以及 authority-bound review
gate 的窄范围 fail-closed 修补；未修改 app/**、runtime/public contract、依赖、权限、持久化或网络行为。

## 已冻结的 semantic subject

归档后 semantic subject 以
.harness/reviews/repair-documentation-information-architecture/implementation/reviewed-change-manifest.json
中的最终 post-archive changes 为精确清单。清单包含本阶段获授权的文档、OpenSpec、validator、测试、
authority epochs 与 plan review set；其中 4 个 apply 流程文档和 epoch 7 均已纳入。manifest、inventory、
本文件与 review checklist 在 post-archive packet 冻结后也不得再改。

归档目录前缀
openspec/changes/archive/2026-08-31-repair-documentation-information-architecture/
只保存由 OpenSpec archive 生成的当前阶段历史，不得追加改写。

## 唯一 evidence tail

最终 post-archive packet 冻结后，只允许 controller 写入：

- .harness/reviews/repair-documentation-information-architecture/implementation/review-set.json
- .harness/authority/repair-documentation-information-architecture/delivery-binding.json

除此之外一律停止写入。review-set 只记录两位既有 reviewer 对 post-archive packet 的 refresh；
delivery binding 只绑定最终 packet、Harness 文件和 candidate/target facts，不得扩大 scope 或 authority。

## Delivery stop conditions

- post-archive packet、review lineage、candidate index 或 delivery binding 任一不一致。
- local/remote main、endpoint、target branch 或 authorized old tip 漂移。
- 需要修改原脏 worktree、allowlist 外路径、runtime、依赖或外部系统。
- commit 不是 planning base 的单一 fast-forward candidate，或 push 无法使用精确旧 OID lease。
