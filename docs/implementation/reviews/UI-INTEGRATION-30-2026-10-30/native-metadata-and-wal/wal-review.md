# WAL readers: final independent review

**Passed; open findings []**. Independent reviewer `/root/accept_compare28`; source repair author `/root`.

Base StockQA HEAD `052f3f0548b90aa3f2df2c7ea871ce0d3516b9f8` plus the exact final three worktree pins in `final-review.json` is reviewed. No source or real database writes were made by the reviewer.

**36 unique cases passed:** 6 permanent real-SQLite WAL/lock/schema tests, 25 original inspection/admission unit cases, and 5 independent cases (2 sidecar directories, 2 actual Windows junction ancestors, 1 full synthetic business-table fingerprint under legitimate WAL). Main run: 34P plus 2 environment errors because sandbox New-Item Junction returned AccessDenied. That diagnostic was retained; only those same 2 tests were repeated elevated inside the owned root and both passed. No product change was needed for that rerun and no repeated case is counted twice.

The normal commit hook subsequently formatted inspection source and the permanent test. Runtime ASTs are unchanged; the test AST is unchanged after normalizing the same-module imported class alias order changed by isort. Original bytes remain under `original-overlay`. Final published bytes were independently retested: **6 permanent cases pass**, 11:45:37–11:46:01 UTC. These six repeats do not expand the 36-case total.

Both readers use native mode=ro, query_only and transactions, preserve schema/path/reparse/type checks, and refuse real exclusive rollback locking. Legitimate committed WAL reads work; uncommitted and later-commit data do not cross the active reader snapshot. No immutable=1, stale main-file clone, deleted sidecar or weakened admission is introduced. Sidecar directories and actual junction ancestors remain rejected. All synthetic business rows remain unchanged after the two readers; no paid API or reservation occurs.

SQLite readonly WAL coordination can touch/create SHM under its filesystem rules, so do not claim whole-directory byte immutability or delete another writer's sidecars.

Isolation: frozen Git archive + byte overlays; stripped credentials, network-denial guard, isolated cwd/cache/TEMP and synthetic SQLite only. All subprocesses exited and runtime DB/junction/temp roots were resolved beneath the owned review root and removed with native PowerShell. No server/browser/profile was started. Frozen sources/tests/archive and exact UTC/argv/exit/log SHA evidence remain. `cleanup.json` records initial cleanup; `cleanup-final.json` records final-six cleanup.

Evidence files: `execution.json`, `junction-execution.json`, `junction-elevated-execution.json`, `formatter-delta.json`, `final6-execution.json`, and associated hash-pinned logs. Real UI/owner preflight is separate and was not initiated by this reviewer.
