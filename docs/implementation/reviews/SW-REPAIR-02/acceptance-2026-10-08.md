# SW-REPAIR-02查收：原六项整改有效，整包仍需整改

总控2026-10-08完成一次集中只读查收。StockWiki分支`master`，基线`04dfc5190589a8bbe224a47e94b045779c884b80`，代码结果`9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`，交接提交`753dfcabd32b03887a3f340d4e5727f04549a94c`，收到及收尾HEAD为`6d1dddbc1289a17a2fb91d40a0d4f57494fa1bfd`，实际工作树clean；结果后的卡内代码/测试未变。后续narrative线提交不属于本包。worker说明尚未push，总控未代推StockWiki。

**结论为changes_requested，保留现有交付。** 原六项修复已有真实通过证据，但新增的12个逻辑边界案例失败；不能签收W12/U01/U02全部完成。原writer按[五组整改卡](remediation-2026-10-08.md)同批处理，再做一次受影响回归和集中复验，不为每个helper增加审查门。

## 已确认的部分

- worker工件53/53原字节size/SHA匹配，收尾仍相符。9项工作树与Git blob差异仅CRLF/LF；这是字节口径差异，没有证据表明内容篡改。
- 从准确代码提交导出296个源码/测试/旧producer文件，运行worker受影响74项加最初冻结7反例，**81 passed / 19.48s / 0 skip**。原冻结反例未改成更宽的断言。
- 真实StockWiki页面在已安装Chromium上完成**11 passed / 79.64s / 0 skip**，覆盖多条件筛选、详情变体及2000行synthetic列表。总控实际loopback143请求/11临时端口，worker自己的142请求另列，不混账；未下载浏览器。
- 原空目标恢复、foreign self-digest删除归属、final rename失败清理、subject分开、UI AND/OR、旧真实producer snapshot兼容等已在上述范围得到通过证据。不能由此推断分部/期间/归一化口径也正确隔离。
- worker全套日志1032 passed/18 skip（结果提交）与1046 passed/18 skip（并行narrative合入后）已接收，**总控没有重跑全套**；它们不是本轮独立执行计数。

## 未通过的边界

| 组 | 优先级 | 实际复现 | 要求 |
|---|---|---|---|
| SR02-1 | P1 | 公开导入均accepted=2；分部A/B、FY2025/2026H1、同2026H1的current/normalized，分别给2与9分，详情只剩9分，`>=8`仍返回公司 | 保存全部不可比变体；默认ambiguous/null并退出筛选，只有明确选择可比较维度才计算 |
| SR02-2 | P1 | 备份根自身及`backups`父目录为真实Windows junction时，create返回成功并在逻辑workspace外写入备份 | 在写入前拒绝根及祖先重解析，不在resolve后把逃逸路径重新当安全根 |
| SR02-3 | P2 | owner registry版本999，或记录owner_module/workspace_root不符，prune仍删除旧backup_a | 未知版本拒绝；错误归属不授予删除权，保留并报告 |
| SR02-4 | P2 | manifest为合法JSON `[]`、`null`、`0`或`{"files":null}`，list/prune发生AttributeError/TypeError | 损坏/未知条目跳过且保留，继续处理合法自有备份 |
| SR02-5 | 交接 | 原公开handoff CLI exit2 changed_path_out_of_scope；只展开已有授权glob的诊断副本又exit2 temporary_root_not_cleaned | 具体路径、临时根归属与清理、接口hash绑定正确，不修改validator或虚填cleaned=true |

SR02-1三个最小输入与真实详情/查询输出在[counterexamples](../../intake/SW-REPAIR-02/2026-10-08/counterexamples/)；全部synthetic，不是假真实identity golden。最终期间案例截止2026-09-30，FY2025和2026H1均已结束；current/normalized比较使用同一个2026H1。初始未来期输入保留为`*-initial.json`，已由这两个定向失败复验替代。

SR02-2仅动态证明**create越过逻辑workspace写入**；两个junction目标仍在总控唯一IQS隔离根，没写任何真实外部目录。尚未用该案例动态证明prune越界删除，不把静态风险写成已经发生。

## 执行、错误适配及清理

[结果与原日志](../../intake/SW-REPAIR-02/2026-10-08/verification/result.json)是执行口径。额外10项首批失败2.16s，修正测试序列化后junction两项失败0.84s；期间/basis两项定向重验失败1.13s，替代初始同名两项。**最终12个逻辑案例失败，不叠加重试算14项。**

首次core缺惯常provider配置而收集失败，补的是`providers: []`惰性配置，不复制真实配置或key。首次junction测试把dataclass当JSON对象导致测试自身错误，修正后重新取得实际失败证据。首次Playwright启动诊断被中断，无浏览器下载；最终guard明确指向已安装浏览器缓存。上述controller适配日志保留，不算产品RED。收尾清理也曾安全拒绝单Target字符串索引及另外四个原测试junction；解除全部六个已知节点后才登记/删除文件，没有递归跟随链接。

总控使用唯一`runs/sw-repair-2026-10-08-01`，TMP/TEMP、所有数据库和截图均在此；白名单进程环境无API key，Python audit限制写根/子进程/外部DNS，浏览器禁外部页面路由和后台联网。此guard不是OS级完整隔离，也不是系统抓包。收费/模型/搜索API和生产库读写均0；源仓未写。296个导出文件测试后size/SHA均不变。

本轮769临时文件，经strict CIM/11端口无监听、lstat单链接、精确set/size/SHA核对后dry-run→Apply已删除；[回执](../../intake/SW-REPAIR-02/2026-10-08/cleanup-receipt.json)为applied=true。两个新增junction和四个原测试junction先仅解除节点，目标保留，再按自身文件清单清理。旧Phase92根、共享TEMP、生产目录及opencode.json未动。**这不代表worker共享TEMP残留也已恢复。**

## 交接与全项目门

原handoff的`tests/test_swr_*.py`在公开CLI按字面prefix校验，故实际四个测试文件失败；[diagnostic](../../intake/SW-REPAIR-02/2026-10-08/shape-diagnostic.json)仅把已有glob展开，不是新授权或正式修复。worker共享TEMP109/110/111明确cleaned=false，浏览器日志还指向105，现有库存不完整；总控不按编号代删。

`quick_scan_variant_projection`声明profiles/1.0.0，但hash `ce206537…`绑定rows.py；实际profiles工作树hash `b73db0d5…`。更新交接须明确接口绑定及Git/工作树字节，保留原提交和证据。

真实身份/事实owner golden、完整QA C06→W05/ACK→UI及双owner恢复仍missing/not_run；查询schema/capabilities的synthetic样例不能替代它们。QA-C06-02尚未正式交付，总控不对其动态工作树运行联合验收。**G3/F05、TH-IMPL-01/IN-IMPL-01、L03仍未放行。**

独立agent完成一次集中源码/日志复核，见[独审记录](independent-review-2026-10-08.md)。整改由原StockWiki writer实施，总控下一次核新commit/handoff后只重验受影响范围及固定反例；不重做已完成功能，不替代writer写外仓。
