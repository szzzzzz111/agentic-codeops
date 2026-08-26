# 当前 Review 清单

Active OpenSpec change：none。`clear-repository-ruff-baseline` 已归档；semantic subject 已冻结，后续只允许
implementation `review-set.json` 与 `delivery-binding.json` 两个 evidence tail。

Risk：`medium`；behavior-neutral repository lint cleanup。Plan review 要求 internal + 1 个独立 slot；implementation review 要求 internal + 2 个互相隔离的独立 slots。Repo-local receipts 只证明 mechanical consistency。

## Freeze

- [x] Planning base 为 `1743eed4694acd585d2a5ef40d090acf56e2969e`；live origin/main/authorized old tip 为 `2c0d0d4e749e16e43d867931c58c6a82be56cf13`。
- [x] Ruff baseline 为 `92 errors / 53 files`；53-file exact inventory 已进入 allowlist。
- [x] Non-goals：无 unsafe fixes、global/per-file ignore、blanket `noqa`、config/rule 降级、行为重构或 API/权限/依赖/持久化/网络变化；仅允许三处 frozen TRY004 与 14 处既有 fail-closed/fallback BLE001（其中一处同线 S110）精确行级 suppression。

## Plan

- [x] 计划固定 safe autofix、逐规则 manual remediation、回归矩阵、完整门禁和 drift stop。
- [x] 独立 plan reviewer 绑定同一 plan packet，P0/P1 关闭；plan review set mechanical PASS。
- [x] Authority implement preflight 绑定 medium risk、scope、base、origin/main、endpoint 与 old tip。

## Implementation

- [x] Ruff safe fixes 已应用并审阅；未使用 unsafe fixes。
- [x] B023/RUF046/FURB162 等剩余规则以最小等价修改清零；三处 TRY004 与 14 处既有 boundary BLE001（其中一处同线 S110）只用授权的精确行级说明保留行为。
- [x] 未修改 allowlist 外路径，未增加 ignore，未改变功能合同。
- [x] Full pytest `971 passed`、full Ruff、canonical verify、stage-doc/skill-eval scanners、OpenSpec `25/25` 与 diff check 全绿。

## Review And Delivery

- [ ] Internal debt sweep 与两个 independent implementation slots 无 P0/P1，final receipts 绑定同一 post-archive packet。
- [ ] Review-set、delivery-binding 与 exact staged-index preflight PASS；形成第二个 finite candidate commit。
- [ ] 两阶段 commits 可从 old tip fast-forward；merge target 与 remote tip 未漂移。
- [ ] 只使用 explicit refspec + exact-old-OID lease push；fresh same-endpoint query 证明 remote parity。
