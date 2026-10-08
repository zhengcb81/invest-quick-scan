# QA-C06-02 集中验收（2026-10-08）

结论：**partial_verified / changes_requested**。完整正文、正常封包、真实进程恢复、旧库迁移已有有效成果；四组新输入/持久化绑定缺口及交接清理证据仍需原writer同批修。总控未修改StockQA，不关闭整Q10/G3/F05，也不启动TH/IN/L03。

## 精确版本与范围

- 基线 `09f68a69bbdbf76e3a4fff63043cdd4815572e5b`，代码结果 `7e71b2cd8bbb042a72b282e83cb361a1ddcbb8b7`，实际交接HEAD `a12bc29bf20f5fc48df69236f2e07c3c2472bacd`，master。结果后仅两交接JSON与全门日志变动。
- 交接目录 `C:/Users/郑曾波/Projects/StockQAbyLLM/docs/handoff/QA-C06-02`；36工件交接前后size/SHA一致，5项仅Git LF/工作树CRLF。131个原快照文件按接收工作树字节执行，补两SQL后133项；与结果Git blob EOL等价，所有测试后SHA未变。`.secrets.baseline`仅做不输出内容的opaque hash，不复制/分析。
- authority1.0保留、2.0新增，Observation1.1 / Answer1.0 / Exchange1.0不改；work store5→6。API事实准确性、人类gold、真实StockWiki owner identity golden不在本离线验收范围。
- 7个原未跟踪项保持原样；交接after dirty14是另一个时间快照，当前实际7，不混用。worker review=approved明确是自审，新增独审见[独审记录](independent-review-2026-10-08.md)。

## 实际集中验证

原始证据均在[本轮intake](../../intake/QA-C06-02/2026-10-08/verification/)。不重复worker的1037全套；该日志仅接收。

| 验证 | 本轮实际结果 | 边界 |
|---|---|---|
| 5个unit文件+原CLI/new C06 integration，201 methods | 首批197 passed /4 failed /25.23s；3个SQL相关补齐后3 passed /0.68s，**200个唯一方法已验证** | 初3失败是controller漏复制fixture，非产品RED；1个async因controller拦Windows socketpair未确认 |
| async+3 SQL纠正批次 | 180秒controller超时，subprocess.run终止并wait自身child | 不算产品失败，不再同配置重试；异常输出未由execute保存，事实记入final-verification，不编造原stdout |
| 真实CLI进程cold→另进程warm→另进程seal | exit0/0/0；7.335s/1.780s/2.384s；cold31次HTTP边界stub；warm/seal新增0 | 第二、第三进程撤掉stub，外部网络守卫仍在；31个ready包不是31个已delivered/真实ACK |
| 新集中边界 | **7 failed /2 passed /1.27s** | 三个metadata参数例+run/scan+两个重复键+完整head=四代码组；两GREEN为真实v5迁移和途中失败回滚 |
| 正常观察IQS校验 | 31/31 public validate API通过；selected观察真实`standard_answers.py compare` exit0 | store读取的内容ID用于校验；合成输入，不能当真实身份/事实真值 |
| 错metadata真实CLI | template_version=99.0.0并重签context后CLI仍exit0、发送31题、产生31 ready包/6.420s | 30观察结构有效，1个被IQS以catalog version mismatch拒；真实IQS compare exit2 |
| run/scan DB对照 | 正常31/31以及错metadata31/31观察的fixture-run/fixture-scan不在实际work_run_ref | 真实run-* /scan-l02来源可复核；不是仅根据fixture静态猜测 |
| worker golden | 结构/发布校验通过 | self-contained合成golden，不证明owner认证、实际run绑定或真实StockWiki接收 |
| 原handoff public CLI | 正确manifest catalog时exit2 `temporary_root_not_cleaned` | changed_paths为空；实际Git范围诊断补齐并去说明文字后仍exit2，未代改worker正式交接 |

## 收敛问题

1. **P1 题义与发布版本未绑定**：loader校prompt/hash与题集合，却没校逐题definition/semantic/template metadata与实际manifest。三个重签反例全部接受；真实CLI已证错误版本在HTTP前未被拒，最终下游拒收。
2. **P1 run/scan未绑定**：任意FOREIGN_RUN/FOREIGN_SCAN可附到当前checkpoint并封存；正常真实CLI产物也携带不同于实际work_run_ref的标签。若定义两类run，必须有明确可核映射；目前无映射证据。不能让任意标签冒充实际扫描。
3. **P2 两个新JSON入口静默取后值**：authority重复schema_version（1.0→2.0）、完整正文重复score（1→8）被接受。既有外层JSON测试没有覆盖这两个入口。
4. **P1 full head可脱离不可变侧表**：通过公开`supersede_result_delivery`改claim与原started_at，重签全层哈希可落新head，原standard/context仍不变。hash自洽不等于绑定原答案和真实attempt。正常seal路径从侧表构建的已有成果保留。
5. **交接**：changed_paths为空、authorized_paths带说明、shared TEMP未清与规则冲突、缺真实进程E2E记录和Git/工作树还原口径。worker如实披露未清不等于恢复环境。只要求其处理能够证明归属的自有产物，不按pytest编号代删。

具体修复与一次集中验收范围见[同批整改卡](remediation-2026-10-08.md)。这些结果不否定已通过的正文保存、旧包/旧ACK兼容、事务迁移、正常seal恢复。

## 隔离收尾

本轮唯一根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/qa-c06-02-2026-10-08-01`。环境无真实key，HTTP均synthetic stub；原guard禁止外部socket/任意非Python child/根外写。纠正guard仅尝试放行Windows asyncio精确ephemeral socketpair，不放行任意loopback服务或模型HTTP；此async重试超时已记。Python audit不是全OS读取隔离。

518文件/229目录经lstat单硬链、无reparse、严格CIM无匹配进程、精确set/size/SHA，dry-run→Apply逐叶清除。回执在intake的cleanup-baseline/lstat/dry-run/receipt，root已不存在。外仓写、生产DB复制/访问、收费/搜索/下载均0；旧Phase92根、共享TEMP、opencode.json未碰。

controller错误保留：首次漏SQL、过严网络guard；猜测catalog.json导致catalog_unreadable，改实际manifest.json；早期读取尚未写完日志报路径不存在；cleanup适配一条内联Python的PowerShell解析错误在执行前终止，随后改明确Python文件。不会用这些错误凑产品RED或伪称所有201方法均GREEN。

## 交给谁与下一步

原QA唯一writer按同批整改卡修四组代码和交接；总控只读源仓。原SW五组、Lab六残余仍由各原writer处理，不能用本包结构有效替代它们。收到QA新commit/handoff后只重验受影响范围和本组反例，一次集中签收；QA↔SW真实CLI导入/ACK/恢复/UI联合节点及F05真实gold仍开放。
