## 1. Migration Review

- [ ] 1.1 Review each OpenSpec capability against legacy `specs/001-mvp-code-agent`.
- [ ] 1.2 Review each OpenSpec capability against legacy `specs/002-file-tools`.
- [ ] 1.3 Review each OpenSpec capability against legacy `specs/003-agent-loop`.
- [ ] 1.4 Review each OpenSpec capability against legacy `specs/004-skill-loader`.
- [ ] 1.5 Confirm `docs/FEATURE_LIST.json`, `README.md`, `docs/PROGRESS.md`, and OpenSpec specs do not contradict each other.

## 2. Archive OpenSpec Change

- [ ] 2.1 Run `openspec validate migrate-legacy-specs-to-openspec`.
- [ ] 2.2 Archive the change so accepted requirements populate `openspec/specs/`.
- [ ] 2.3 Confirm `openspec list --specs` shows the migrated capabilities.
- [ ] 2.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.

## 3. Legacy Specs Decision

- [ ] 3.1 Decide whether legacy `specs/00x-*` should be deleted, moved to archive docs, or retained as historical stage documentation.
- [ ] 3.2 If deleting or moving legacy specs, create a separate cleanup change before modifying them.
- [ ] 3.3 Update `AGENTS.md`, `docs/PROGRESS.md`, and `HANDOFF_TO_NEXT_CHAT.md` after the archive/cleanup decision.
