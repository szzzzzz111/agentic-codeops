## 1. Authority And Replan

- [x] 1.1 用户明确授权改为 Codex App 空上下文 task + 独立 worktree，并允许修改计划、实现、复审和一次实验；不含
  archive、commit、merge、push。
- [x] 1.2 authority epoch 5 与 OpenSpec/Harness 绑定 exact base、一个 task、一个 coding turn、candidate paths 和
  `implement` ceiling；旧 CLI packet/review 失效。
- [x] 1.3 internal plan review 已完成；两个 fresh empty-context plan slots 与 validator 结论只写入 subject packet 外的
  `plan/review-set.json` evidence tail，避免勾选回写使已审 packet 自失效。

## 2. Deterministic TDD

- [x] 2.1 RED：strict `HostTaskObservation` 只接受同 thread、completed、精确 `READY_FOR_REVIEW` 和单条有界、EOF-delimited
  输入；buffered duplicate、未封口或超时均 fail closed。
- [x] 2.2 RED：baseline 必须同 repo、live non-prunable 注册 worktree、exact HEAD、clean；无关 prunable 历史记录被排除但
  不得替代 stage/task 自身注册；handshake 后任何变化阻断 coding turn。
- [x] 2.3 RED：completion 只允许 `README.md` 精确第一行替换，无 untracked/index/其他 tracked drift。
- [x] 2.4 RED：claim、completion/runner/post snapshot、verification receipt 与 evaluator 任一不匹配均 fail closed。
- [x] 2.5 RED：脚本不启动 Codex/provider process、不调用 App task API、不把 fake observation 标为 native host evidence，
  claim ceiling 全部保持 false/unverified。
- [x] 2.6 RED：stage worktree 的 `README.md` 不可写；task worktree 只接受冻结的完整 before/after digest。
- [x] 2.7 RED：从无 `.ruff_cache` 的 fixture 调用真实 whitelist `ruff`，bridge 强制 no-cache 且 snapshot 不漂移。

## 3. Minimal Host-Task Adapter

- [x] 3.1 实现一个 in-memory CLI bridge：准备 baseline、输出 bounded ready 摘要、消费一次 EOF-delimited stdin
  observation、输出 bounded final summary；controller 写入唯一记录后关闭 stdin，未封口/超时 fail closed；不持久化 raw
  task/tool material。
- [x] 3.2 复用现有 snapshot/contract/receipt/evaluator 和真实 whitelist `ruff` runner；不修改 `app/**`。
- [x] 3.3 删除或停用旧 executable/HOME/CLI-producer 路线，避免把过期 preflight 写成当前要求。

## 4. Verification And Review

- [x] 4.1 跑 focused tests、changed-file Ruff、OpenSpec strict、`git diff --check` 和 canonical verification；固定版
  `@fission-ai/openspec@1.11.0` strict 已真实 PASS。
- [x] 4.2 冻结新 implementation packet，由两个 fresh slots 复核相同 bytes；P0/P1 未清零前不运行 task。

## 5. One Real Host-Managed Task

- [x] 5.1 创建一个全新 Codex App task；handshake 只回复 `READY_FOR_TASK`，并证明 task worktree baseline clean。
- [x] 5.2 在同一 task 发送唯一 fixed coding prompt，获取 completed terminal 与精确 `READY_FOR_REVIEW`；不重试。
- [x] 5.3 让 reviewed bridge 消费该 observation，完成 completion snapshot、ruff receipt、post snapshot 和 governed decision。
- [x] 5.4 报告 single-run facts、host evidence boundary、claim ceiling 与 task/worktree residual state；不 archive/commit/merge/push。
