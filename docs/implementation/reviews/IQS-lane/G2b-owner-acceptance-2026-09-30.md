# G2b owner export: IQS coordinator acceptance slice

Date: 2026-09-30. StockWiki read-only input: `master@72531b5` (`8bee364` W04 owner context). IQS source was `master@5aac63a` before this slice. Scope: identity package 2.2.0 / Entity 2.1.0 **provisional, single Security and Listing** from a deterministic synthetic fixture. This is an Entity producer/consumer compatibility result, not a verified issuer, multi-listing, AnalysisSubject, or full W01–W03 acceptance.

## Reproducible public-path command

From the IQS root, with StockWiki checked out at the commit above:

```powershell
python -B -X utf8 scripts/stockwiki_g2b_acceptance.py --stockwiki-root C:\Users\郑曾波\Projects\StockWiki --golden docs\implementation\contracts\goldens\stockwiki-g2b-72531b5-provisional.json
python -B -X utf8 -m pytest -p no:cacheprovider -q -o addopts= tests/test_stockwiki_g2b_frozen_golden.py tests/test_identity_contract_cli.py --basetemp .tmp-g2b-frozen
```

The coordinator script seeds two independent isolated roots **through StockWiki owner store APIs** using the exact deterministic fixture values in `tests/test_identity_g2b_export.py` and its offline ISO sample CSV. It calls public `python -m stockwiki.cli ... identity-export-g2b` twice, compares canonical bytes, and checks the public owner read projections for Entity/revision, active receipt, Listing/Security/source-binding joins, and registered MIC. It then calls IQS public `scripts/identity_contract_cli.py` with the exported bytes. It does not open StockWiki SQLite directly, use production data, make a network/API call, or write StockWiki.

Frozen [raw owner CLI golden](../../contracts/goldens/stockwiki-g2b-72531b5-provisional.json) is 2,765 UTF-8 bytes, without the CLI terminal newline. SHA-256: `0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f`, matching StockWiki W04 closure. The first local capture attempt produced a different hash because it left Windows stdout `\r` after removing only `\n`; the script now removes the terminal CRLF before hashing, and the owner E2E fixture independently reproduces the exact expected hash. No mismatching golden was saved.

## Results and limits

- Two owner exports: byte identical and expected SHA. IQS CLI positive: exit 0, `status=valid`, no errors.
- Five one-field consumer negatives (Entity ID, missing owner receipt, source record ID, MIC registry membership, identity revision): each exits 2 with `semantic_validation_failed` and no company payload echo. StockWiki's own E2E separately covers 17 mutation cases; this coordinator run does not claim all 17 were independently repeated.
- Producer-side name ambiguity check uses **synthetic** labels “中微公司（合成标签）” and “中微半导体（合成标签）” on two distinct fixture Entities with the same listing key. Public snapshot/mapping APIs return `ambiguous` with two unmerged candidates and no selected Entity; an exact source namespace/record query maps only one Entity. This is a resolver boundary test, not an assertion about those real-world companies.
- IQS frozen-golden and CLI boundary suite: **8 passed**. CLI suite includes duplicate JSON keys, >1 MiB input, unsupported package version, and Entity/AnalysisSubject contract fixtures. All coordinator temporary roots were removed; the pytest temp root was separately removed. StockWiki worktree remained at `72531b5` with only its pre-existing untracked `.claude/`.
- StockWiki's owner DTO mapping version is 1.0.0. IQS has verified its public owner API behavior above but has **not yet added its own four-state mapping DTO consumer validator/golden**. No verified issuer receipt, multi-listing issuer bridge, or public AnalysisSubject golden was supplied. Therefore the complete construction-card step 5/G2b gate remains **partial**; this report signs off only the Entity provisional producer/consumer slice. W01–W03 and scan eligibility remain separately pending.
