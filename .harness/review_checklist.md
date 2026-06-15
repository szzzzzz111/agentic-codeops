# 褰撳墠 Review 娓呭崟

褰撳墠 active stage 涓?V23 Worktree Disposal / Reconciliation closeout銆傚疄鐜扮‘璁ゅ凡鑾峰緱锛屼互涓?gate 鐢ㄤ簬 archive / merge 鍓嶅鏍搞€?
## V23 Planning Gate

- [x] 鍩虹嚎涓哄共鍑€鐨?`main@27a754a`锛屽苟鍒涘缓 `feature/v23-worktree-disposal-reconciliation`銆?- [x] 鍒涘缓 V23 stage planning銆乸roposal銆乨esign銆乼asks 涓?spec deltas銆?- [x] 鍚屾 `.harness/allowed_files.md` 涓庢湰娓呭崟銆?- [x] V23 feature list 鏉＄洰淇濇寔 `passes: true`銆?- [x] 鍐呴儴 plan review 宸插畬鎴愪笖 findings 宸插鐞嗐€?- [x] `openspec validate v23-worktree-disposal-reconciliation --strict` 涓?`openspec validate --all` 閫氳繃銆?- [x] `scripts/check_stage_docs.ps1` 涓?`git diff --check` 閫氳繃銆?- [x] 宸插湪瀹炵幇纭闂ㄨ幏寰楁槑纭‘璁ゅ悗淇敼 runtime/tests銆?
## Command And Routing

- [x] 浠呮帴鍙楀洓绉嶅畬鏁?confirmed 鍛戒护锛涚己灏?confirm銆侀澶栨枃鏈?鍙傛暟鍜?unsafe syntax 鏁翠綋鎷掔粷銆?- [x] `how to discard changes` 绛夎璁烘枃鏈笉瑙﹀彂 V23 intent銆?- [x] V23 route 浣嶄簬 inventory/inspection 鍚庛€乂22 re-verification 鍓嶏紝骞惰褰曠粓姝㈡€?destructive lifecycle 鐨勭悊鐢便€?- [x] malformed disposal-like 璇锋眰涓嶈惤鍏?V22銆乸atch銆乿erification銆乤udit recovery 鎴?repo RAG銆?
## Preflight And Deletion Safety

- [x] normal discard 鍙帴鍙?`patch_applied`銆乣verification_failed`銆乣verification_succeeded`銆?- [x] scoped metadata銆乤ssociated scoped patch銆乪xpected path銆乺egistry/path銆乴ock銆乴inked-worktree `.git`/common-dir/admin-back-reference ownership 涓?HEAD/base 鍧?fail closed銆?- [x] 鎷掔粷 unknown/cross-scope銆乸ath mismatch銆丠EAD mismatch銆乵etadata 鎹熷潖銆佷富宸ヤ綔鍖恒€乵anaged root銆乷utside path銆乻ymlink/reparse point 鍜?unknown ownership銆?- [x] reconciliation 鍙鐞?design 涓殑瀹夊叏娈嬬己闆嗭紝涓嶉殣寮忎慨澶嶃€佷笉鑷姩閲嶈瘯銆?- [x] 绂佹 `git worktree prune`锛屼笉寰楀奖鍝嶅叾浠栫敤鎴枫€佸叾浠?repo 鎴栧叾浠?worktree銆?
## Blocking Hardening And Store APIs

- [x] shared Git metadata runner 鏄?blocking 宸ヤ綔锛氬浐瀹?argv銆乣shell=False`銆佺嫭绔?timeout銆佽鍙栧墠纭笂闄愩€佹棤鑷姩閲嶈瘯銆?- [x] V21 inspection 涓?V22 re-verification 杩佺Щ鍒?shared runner 涓斾繚鎸?contract銆?- [x] patch store 鏂板 true no-create existing lookup銆?- [x] patch store 鏂板 `mark_status_scoped(patch_id, user_id, repo_key, status)`锛沄23 鍙敤 scoped API锛屾棫 `mark_status` 淇濈暀銆?
## Order, Lifecycle, And Failures

- [x] 姝ｅ父椤哄簭涓ユ牸涓?preflight銆乷ptional unlock銆乪xact remove銆乤bsence post-check銆亀orktree `discarded`銆乸atch `discarded`銆乤udit銆?- [x] 浠讳竴姝ュけ璐ョ珛鍗冲仠姝紝涓嶉噸璇曘€佷笉鍥炴粴宸插畬鎴?destructive step銆佷笉鎵ц鍚庣画姝ラ銆?- [x] lifecycle transition table 鐨勬瘡涓€琛岄兘鏈夋祴璇曪紱patch update 澶辫触鍚?worktree `discarded` 涓嶅洖閫€銆?- [x] 瀹屾暣澶勭疆鍚庣殑閲嶅璇锋眰骞傜瓑涓旀墽琛岄浂 destructive operation銆?- [x] patch 鍙湪 worktree 宸茬‘璁ゆ竻闄ゅ苟鎴愬姛鍐欎负 `discarded` 鍚庢洿鏂般€?
## Audit, Contract, And Non-Goals

- [x] 姣忎釜 recognized attempt 灏濊瘯鍐欏叆涓€涓?scoped related `worktree_disposal` persistent audit event銆?- [x] answer銆乼race銆乼ool calls銆乤udit 涓嶆硠闇茬粷瀵硅矾寰勩€乺aw Git output銆丏B 璺緞銆佺幆澧冨彉閲忋€乻ecret銆乨iff銆乸atch body 鎴?unknown directory name銆?- [x] `/chat` 椤跺眰 contract 涓嶅彉锛宍related_files=[]`锛屽け璐?骞傜瓑缁撴灉鏃?execution tool call銆?- [x] 涓嶈皟鐢?repo RAG銆乸atch apply/reapply銆乿erification銆乸romotion銆乧ommit銆乵erge銆乸ush 鎴栧叾浠栬秺鐣屽伐鍏枫€?- [x] V23 涓嶆柊澧炰换鎰?shell銆佸悗鍙颁换鍔°€乻ubagents銆乧onnectors 鎴栧墠绔€?
