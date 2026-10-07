# P2-5 真实身份wire兼容批次验收

结论：**verified_for_read_wire_consistency_scope**。独立审查者`/root/identity_wire_review`先只读核查方案，再复核同一实施批次，未发现阻断性问题；本报告由总控依据实际审查消息与日志记档，不冒充审查者写入文件。

## 交付和边界

公共CLI`1.1.0`保留`--schema-version 2.2.0`，默认`stockwiki-g2b/1.0.0`且响应标`wire_profile`，提供显式legacy模式。冻结C01 schema原字节、既有请求envelope和所有原ID不变；内部默认legacy。规则见[兼容说明](../../../../references/identity-wire-compatibility.md)。新profile只在内存副本扩展两个v2.1来源绑定字段为legacy BND或精确BIND UUIDv4；不改历史v2.0格式。

明确拒绝撤销/退役/替代或冲突状态、缺生命周期、非int修订、缺actor、错误所有权/来源/挂牌/属性；official与verified继续HTTPS及全部证券/挂牌精确覆盖。manual null evidence须原字段存在、actor非空和全部来源资格相符，不编造链接。

三份正例是已验收W04历史导出的原字节归档，不是新producer导出。本次未运行StockWiki exporter、访问生产身份库或修复外仓；两provisional不升级，Alphabet四挂牌不合并成单证券。当前CLI不认证caller context、不证明当前as_of资格；work.schema仍有BND词法边界，因此不声称Work/Observation/C05或完整G2b/生产链完成。G3/F05/研究消费者开工门不改变。

## 真实证据与验证

- 原始复现：三份StockQA历史快照经旧IQS公开CLI均exit2/request_schema_invalid。原归档来源/历史子命令/代码观察边界在[manifest](../../contracts/goldens/stockwiki-real-identity-2026-10-07.manifest.json)。
- TDD首次12测试RED：27 failures/1 error；缺兼容是预期失败，1 error为新测试异常类型捕获不全（JsonSchemaValidationError），修正后实现GREEN12通过。保留原日志，不把异常类型失误说成产品缺陷。
- 相关六文件最终回归：**89 passed、139 subtests passed、无skip、102.87s**；含14新测试。不是全产品测试。命令与自有TEMP路径在原始[回归日志](../../contracts/validation-P2-5-wire-regression-2026-10-07.log)。
- 后续只调整新测试的冻结hash断言以容许Git CRLF→LF；两受影响selector复跑**2 passed/0.034s**，[终版检查](../../contracts/validation-P2-5-wire-final-checks-2026-10-07.log)。没有重跑89项批次。
- 独立审查在最终文件上运行`python -B -X utf8 -m unittest discover -s tests -p test_identity_wire_profile.py -v`：**14 tests、40.749s、exit0**。另复核三原档、冻结原schema/blob、派生schema副本、所有关键反例及隔离清理；未重跑完整89项。
- 旧已签收`stockwiki-g2b-72531b5-provisional.json`经当前CLI仍exit0；其他施工包10项冻结输入hash全部不变。新profile Draft7 schema、3 AST、4本地链接、manifest来源及3golden hash、git diff均通过；计划校验仍107 tasks/366 cases/G6，product_tests_executed=false。

回归选择器：`tests/test_identity_wire_profile.py`、`test_identity_contract.py`、`test_identity_contract_cli.py`、`test_identity_bound_work_observation.py`、`test_stockwiki_mapping_contract.py`、`test_exchange_and_query_contract.py`。RED/GREEN日志也在`contracts/validation-P2-5-wire-{red,green}-2026-10-07.log`。

## 隔离与字节口径

测试用本仓唯一临时根，parent恢复tempfile.tempdir，真实子进程以startup audit hook拦截socket和根外写入。guard marker与canary证明hook已加载、拒绝发生在副作用前；输入前后原字节不变；终版独立测试确认残留自有根0。网络/模型/API/下载/生产DB/外仓写入均0，没有凭据读取。

原identity schema工作树CRLF raw SHA=`671292a60bf1656b73009877a59c49c8585935b11d42b7fef5e021fc275fc2e3`，冻结Git LFblob SHA=`4924b5e3bc641dd060f6f748c2fff8a9166d76a7d123c591838fa4c3018282f3`；原request schema SHA=`d63afdf4420d1432fc3cb0be2f6f27c3ff3d1524e17a6fbffd1a3a3c2a51effc`。两原文件没有修改。三golden用精确Git`-text`规则，check-attr均text=unset，避免checkout改字节。

## 被审关键快照

以下为审查时工作树原字节SHA；Git对普通文本的EOL转换口径另行区分。总控之后只追加PWF/交付记录，不改变被审代码/profile/golden。

| 文件 | SHA-256 |
|---|---|
| `.gitattributes` | `7d38860cf71f1b0ad9f7ca45aa7a87e3169ef1db7fb3e92a9042f942e2ea47f1` |
| `scripts/contract_validation.py` | `851156fa76939fc8ad9d1f2dbcf56a4d5c2cee9fed7154ff6486681d3db9edaa` |
| `scripts/identity_contract_cli.py` | `1053239d96e3f692136ae99a043c8daa77e02463f5a1bffb4738890bcd2f8cc8` |
| `schemas/quick_scan/identity-wire-profile.schema.json` | `ca4759c309dcdfc5f91992686add06f73d052760ddbf9664618280b4572789f2` |
| `tests/test_identity_wire_profile.py` | `e9e9907f3bac6f74bcc45e383fa3e0b0e724109426057245fdc450269a5454b3` |
| `references/identity-wire-compatibility.md` | `0fe0e202dae48cd9f9d012007906e62eac07baeffdaa58e5ad2116683d5caea6` |
| `goldens/stockwiki-real-identity-2026-10-07.manifest.json` | `32398dd7b4c4168cd20c8bd8a0d7212d44b6184ced580d729cc548315c1b2dc4` |
| `goldens/stockwiki-real-catl-2026-10-07.json` | `6929f0868243a271ccc35ab7b16005b11fe968f43f18213929d0651c3bf66db7` |
| `goldens/stockwiki-real-cncb_h-2026-10-07.json` | `884855433a431292da3e1dbf7382e757aab9dea41be8f321b464c79303ad908a` |
| `goldens/stockwiki-real-alphabet-2026-10-07.json` | `5ad1a45e287c945680fc4c23db7b4dcf32959a6c0021daea4ba226ebd4365278` |

## 下一动作

精确提交本IQS批次。用户已让QA-NET-01/SW-READY-01开工，两源仓由对应harness独占；总控接收其交付再集中联调，不能代改外仓或用本批关闭上游门。后两研究包暂缓，已设静默只读条件提醒。本批不恢复退役任务回执机制。
