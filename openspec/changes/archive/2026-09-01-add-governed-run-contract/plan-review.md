# Internal Plan Review

## Scope and value

- The stage advances the agreed supervisor mainline by one bounded step: a reusable internal evidence/decision kernel after
  real-Agent observability qualification.
- It does not add a competing code author, public control surface, daemon or Git delivery path.
- The first consumer remains deterministic tests and a future thin controller; no runtime integration is implied by this stage.

## Authority and risk

- Risk is high / L3 because the stage defines runtime supervision semantics and invokes local Git subprocesses, even though
  those subprocesses are read-only.
- Authority is bound to the clean `origin/main` baseline and exact allowlist with action ceiling `implement`.
- Two independent plan slots and two independent implementation slots are required. Archive, commit, merge and push remain
  forbidden until separately authorized.

## Counterexamples checked internally

- A terminal event without the exact Agent claim cannot reach review-ready.
- An open valid prefix can continue, while a closed stream missing terminal/claim needs human attention.
- Duplicate/contradictory chronology, scope breach, untracked paths and snapshot/receipt drift intervene before progress rules.
- A failed or absent verification receipt after a valid claim needs human attention and cannot silently continue.
- A self-reported bound hash is insufficient because the evaluator recomputes the complete post-verification snapshot digest.
- Dynamic argv, shell text, symlink traversal, repository subdirectories and malformed NUL path data remain outside the accepted
  Git/verification boundary.
- Every outcome keeps `task_complete=false`; review-ready cannot authorize apply, commit, merge or push.

## Verification design

- Contract, adapter, collector and evaluator each have focused RED/GREEN tests with negative paths.
- Collector tests spy on argv/environment and compare repository state before/after collection.
- The existing frozen real-Codex observation is retained as a regression input; synthetic fixtures only verify rules.
- Final gates include focused tests, changed-file Ruff, OpenSpec strict, diff check, canonical verification and two-slot final review.

## Internal conclusion

The first frozen packet was sent to two isolated reviewers. Both verified the exact packet and blocked it on substantive P1
counterexamples. The revised plan closes them without adding a public/runtime integration:

- `NO_EVIDENCED_CHANGE` and premature-receipt cases now have explicit conflict-first outcomes, and the decision table is total.
- run id, observed thread id, event/claim digest, resolved command digest and snapshot are correlated across all four contracts;
  constructors and evaluator both enforce invariants.
- Git children now use an environment allowlist, disable repository-controlled helpers, close stdin, cap time/output, clean up
  failed processes and use two identical full samples rather than mixing independent reads.
- all-untracked inventory now includes ignored files; tracked symlink/gitlink state is rejected in the first MVP.
- continuity is explicitly limited to two stable endpoint samples. Perfect ABA and continuous single-writer isolation are not
  claimed and remain future work.
- the receipt digest is defined over the existing runner's audit summary, not unavailable raw streams; source provenance remains
  unverified.
- the previous qualification validator/tests were removed from this stage's writable scope and are consumed read-only.

The remediated packet must return to the same two reviewer slots. Every original P0-P2 finding will be preserved in review
history and explicitly closed or left blocking; only final no-finding receipts on one new frozen packet may open the L3 user
confirmation gate.

The first remediation review closed the original findings but exposed two narrower specification gaps. The second remediation
makes the normative drift rule observable (HEAD/sample differences only, with perfect ABA retained as an explicit claim limit)
and moves symlink/gitlink plus effective clean/process-filter preflight ahead of every status/content-diff command. Tests must
lock down the command order and prove malicious helpers do not execute.

A subsequent counterexample showed that `--local` alone omits `config.worktree`. The final preflight therefore reads all
effective repository scopes inside the already sanitized environment (system/global disabled), so local and worktree-scope
clean/process commands are both rejected before content reads.
