## Context

`add-live-model-provider-eval` 已归档，最终证据是一份可信 evaluated-failure record：当时 8 个真实
provider 调用均为 `availability=unavailable`。归档后使用同一 `.env.live` 做了两次最小脱敏诊断：
DeepSeek endpoint 返回 HTTP 200、`deepseek-v4-flash`、完整 usage；RepoPilot
`OpenAICompatibleModelProvider` 返回 `status=success`、`finish_reason=stop`。

当前没有可复现 runtime 缺陷，也没有 PASS attestation。需要把“evaluator readiness 已归档”和
“provider 后续重新认证”分离，避免修改或重开历史 change。

本阶段风险级别为 high：它会访问真实网络、使用 API key、产生最多 8 次计费调用并可能生成可跟踪
的 provider conformance attestation。风险来自外部状态和证据语义，不来自代码改动规模。

## Goals / Non-Goals

**Goals:**

- 在独立 change 与 clean tracked commit 上复用既有 runner 完成完整 8-call DeepSeek gate。
- PASS 时生成并复核既有 schema 的 attestation；PASS attestation 是唯一 provider certification
  evidence。
- 有效 conformance FAIL 时允许保留 runner exclusive-create 的 tracked failure record 作为当前
  revalidation 分支的暂停现场证据，但它不代表认证完成。
- 保留历史 evaluated-failure record，不覆盖、不删除、不追溯改写。
- 保持默认验证离线 deterministic。
- 在归档前完成 internal review、independent evidence review 和最终证据复核。

**Non-Goals:**

- 不修改 `app/**` runtime、`evals/**` evaluator、fixtures、rubric、profile 或 tests。
- 不诊断或修复不可复现的 provider/runtime 缺陷。
- 不通过降低 hard gate、retry、模型切换或删除历史 FAIL 来制造 PASS。
- 不把 FAIL record 用作 provider certification，不通过 FAIL baseline 完成本 revalidation change。
- 不修改默认 Patch wiring、`/chat` contract、CI、`scripts/verify.ps1`。
- 不创建 V24。

## Decisions

### 1. 独立 revalidation change，不重开 Change 2

历史 archive 表示 evaluator contract 和 readiness 已完成；新的 provider conformance 结果属于新的
外部状态。独立 change 保证历史评测证据不可变，也避免把后续认证错误描述为原 Change 2 的 PASS。

### 2. 只复用已归档 runner，不修改 evaluator

在 live run 前执行 deterministic verification 和 clean-tree preflight。计划中不开放
`app/**`、`evals/**`、tests、fixtures、rubric 或 profile。若 live run 暴露可复现缺陷，本 change
停止并另开 remediation，而不是现场修复后继续认证。

### 3. 只有 PASS attestation 才能完成本 change

本阶段目标是 provider conformance revalidation，不是再次证明 evaluator readiness：

- PASS：退出码 0，生成本地脱敏报告与 tracked attestation，可进入证据复核和归档。
- FAIL：退出码 1，按既有 runner 生成 evaluated-failure record；该 failure record 仅可提交到当前
  revalidation 分支作为暂停现场证据，不归档本 change，不 merge 到 `main`，不 push 为完成态，
  除非后续正式 reshape 契约。
- SKIP/ERROR/integrity failure：不生成有效认证证据，保持 active。

退出码不能单独证明 evidence 类型：PASS 与 SKIP 都返回 0；普通 conformance FAIL 与部分
integrity-blocked FAIL 都可能返回 1。Closeout MUST 同时检查 stdout 状态行与
`attestation=<path>` / `failure_record=<path>`，且验证对应文件实际存在。没有 tracked evidence
路径的 FAIL 不得被称为可信 provider evidence。有效 FAIL record 只能证明本次重新认证失败，
不能证明 provider conformance。

### 4. Live 前允许一次无计费配置检查，不允许额外模型探测

Runner 自己负责 profile/clean-tree preflight。执行阶段不得再发送手工模型/API 诊断请求、不得
retry，完整 live gate 最多 8 次真实调用。Runner 的本地 `git rev-parse` / `git status` 属于
clean-tree integrity 检查，不计为 provider 诊断或模型调用。

Live 执行必须使用同一个 PowerShell 进程读取 `.env.live`，忽略空行和注释，把 key/value 写入当前
process environment，只校验五个 required key 是否存在，不打印任何 value，然后调用
`scripts/run_live_model_eval.ps1`。该 wrapper 不得发送任何 provider/model 请求。

### 5. Attestation 复核使用固定 allowlist

复核内容包括：

- tested commit 与 live 前 clean commit 一致；
- stdout 明确包含 `PASS live model provider eval` 与 `attestation=<path>`，不能只依赖退出码 0；
- report SHA-256 与 attestation 一致；
- UTC、provider/model、profile/rubric version；
- call count 为 8，10 个计划 case 完整；
- hard gates 全部 PASS；
- latency/token/cost 聚合存在且 usage 完整；
- 不包含 API key、完整 URL、prompt、EvidencePack、原始回答/diff/reasoning/fingerprint。

## Risks / Trade-offs

- [外部服务再次瞬时失败] → 不 retry；保留脱敏 FAIL evidence 并暂停，避免把偶发重试挑选成认证。
- [FAIL evidence 被误读为完成态] → failure record 只允许当前分支作为暂停现场证据；不得 archive、
  merge 到 `main` 或 push 为完成态，除非正式 reshape 契约。
- [Live 期间 tracked tree 变化] → runner integrity gate fail closed，不生成 attestation。
- [历史 FAIL 与新 PASS 被误读为冲突] → 两份 evidence 均保留；文档按 commit 和 UTC 描述不同运行。
- [API key 泄漏] → `.env.live` 保持 ignored；命令和报告不打印或持久化 key。
- [认证后 evaluator/profile 改变] → attestation 只认证记录的 commit/profile/rubric，不作泛化声明。
- [Attestation 文件提交身份依赖 Git 历史] → final evidence review 验证 attestation commit 基于
  tested commit；当前 schema 不新增 `attestation_commit` 字段。

## Migration Plan

1. 提交本 change 的 planning/Harness baseline。
2. 在 clean commit 上执行 deterministic verification。
3. 用户确认后执行一次完整 live gate。
4. PASS 时提交 attestation、完成 evidence review、archive、merge、push。
5. FAIL 时可提交当前分支的暂停现场 failure record，但不得 archive、merge 到 `main` 或 push 为完成态；
   ERROR/SKIP/integrity failure 不提交认证证据。任何非 PASS 结果都停止 closeout，不修改 runtime。
6. Archive sync 后验证长期 spec 的全部 6 个 requirement 标题仍存在，且 revalidation scenario
   已合并；delta 只修改同名 requirement，不替换其他 requirement。

## Open Questions

无。任何 live failure 的 remediation 设计必须进入新的 change。
