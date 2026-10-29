# UI-UNIVERSE-28 独立验收：需整改

- HEAD `154afd936c7d1ae84f974eb6c0a689225fa883dd`；payload `3fdbba0f4402942c72b5ef22731df96329f039a2`。
- 原业务/测试源码未改；按最新用户指示交还原 harness 改进，主线保持暂停。
- 原145项单元全通过，但独立5项行为反例全部真实失败。稳定版已去固定sleep/错误码捆绑，原实现仍5F。

| ID | 根因 | 具体问题 | 源码 |
|---|---|---|---|
| ACCEPT-U01 | listing_validity | Implicit sole-security selection bypasses the listing validity check | src/iqs-universe-import/machine.js:315-371 |
| ACCEPT-U02 | draft_write_ownership_and_unknown | Different rows dispatch concurrent mutations despite global inFlightRowId | src/iqs-universe-import/machine.js:465-496 |
| ACCEPT-U03 | draft_write_ownership_and_unknown | A new upload replaces the draft while its prior mutation is still pending | src/iqs-universe-import/machine.js:182-237 |
| ACCEPT-U04 | draft_write_ownership_and_unknown | unknown can be reset and re-POSTed without inspecting original state | src/iqs-universe-import/machine.js:239-310,315-379,381-463 |
| ACCEPT-U05 | async_selection_epoch | A delayed preview for candidateA attaches to selected candidateB | src/iqs-universe-import/machine.js:381-436 |

## 复验范围

- 原 unit：145P。Python首次52P/1setupF；修隔离副本独立Git索引后，唯一受影响用例1P，不把它冒称一次重跑53P。
- 浏览器首次6setupF（验收自己的DNS防护误拦loopback）；修127.0.0.1例外后，仅原单E2E复验1P/31.26秒。原5个DOM集成未复跑，不计通过。
- `independent-counterexamples.test.mjs` 是最终5个有效行为红；initial版本和两次日志分别保留。
- 对U02/U03/U05，普通mount按钮有view.busy串行保护；缺口在导出machine/getMachine/host接口，不能宣称普通点击路径全部可触发。U05未证明原owner错误写入。

## 独审与交接证据

- `review/final.json` 指新payload/新reviewer，但其唯一invocation_ref仍指第一轮旧payload/旧reviewer，最终引用未闭合。不得改旧记录造新调用；返修结束调用真实独立agent并绑定最终C/锁/文件pins。
- 无src导入失败不能当产品行为RED；保留历史，新增本轮真实行为红→绿。
- 报告86/204测试数字需统一口径。

## 清理与下一步

- CodeGraph仅本Lab已授权初始化，源业务/测试7文件SHA完全保持，HEAD未变。
- runtime、浏览器profile/临时根已清；外层finally无遗留owned进程，18772可独占绑定；主UI/8766未动，模型/搜索/真实owner调用0。
- 分三根因组一张R1整改：有效挂牌选取；整draft写互斥/unknown保留；异步选择epoch。所有5红应在修复后转绿并补相邻取消/连接切换/removed与名单版本/ACK归属用例。
- 组件仍未接生产，不能关闭金融/生产资格门。
