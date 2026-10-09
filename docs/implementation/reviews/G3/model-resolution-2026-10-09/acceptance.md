# Phase110｜模型来源追溯的有限软件验收

**当前：本批一次[集中独立审查](independent-review.md)及[同批EOL最终附记](independent-review-eol.md)允许有限交付24文件，StockQA已正常commit／push为 `42a517c4bd6bc8219f926957c6c332944da3278a`。** 基线StockQA `86b1e8ab1221e085f08718ed31d18e792e526d34`；IQS `bc6e63a38b59b8faf52c64adeda4dfa7efeaaacf`。用户全仓授权以逐批先报备为条件；本批[24路径](scope.json)已报备，原scope中的not_published仅为报备时快照而不改写。实际[Git回执](../../../intake/G3/2026-10-09-model-resolution/source-git-receipt.json)绑定新的EOL审批／source02，原七未知项保留。实施和测试仅在IQS自有根，生产数据／名单及其它外仓未写；本批清理以实际回执另列。

## 最终行为与版本

- 请求模型在每次HTTP入口捕获，贯穿同步／异步endpoint、预算／发送意图、POST、parser与回执；等待连接期间修改client不会改变此请求。
- 实际模型只取HTTP envelope；默认exact。独立`quick_scan_model_resolution/1.0.0`按provider／protocol／requested／resolved精确注册，非空许可纳入策略指纹并在派发前冻结，不从热配置追认。
- 私有工作SQLite schema8增加不可变派发绑定与响应来源表；保存sanitize receipt及canonical JSON摘要，work和budget-only均有来源。未知实际价格保留unknown／预留，不按requested定价或填0。
- 新checkpoint必须取同work最终attempt，save/read/seal共用来源核对；中间repair／fallback回执不得抢占。历史exact checkpoint可读，旧裸attempt不回填actual；升级添加空表，失败rollback。已有请求无checkpoint在恢复时仍uncertain，不能因后一个repair未发而自动重问。
- C06 Observation的requested／resolved分列及封包重建保留；公共Observation／ExchangePackage／ImportAck、原模型优先policy v2未改。项目元数据仍0.1.0，部署版本以真实source commit辨识。

## 准确冻结证据

最终[source02 manifest](../../../intake/G3/2026-10-09-model-resolution/snapshots/model-release-02/source.json) SHA256：`387dc2442e88a192ce45ec497cb7aba41d40f7a84476777d502055f091b99506`。24改动、117原未改、137原保护文件加4新文件共141，原beforeSHA／normLF均保持。原[source01](../../../intake/G3/2026-10-09-model-resolution/snapshots/model-release-01/source.json)及审批／发布回执仍原字节，SHA `3c38dd7a3ada47f18bc1ac4dc21ca6d37f62c206d0e84dd6537e3556886ba72c`。第一次正常commit被换行钩子拒绝并仅统一11 CRLF→LF，Black/isort/mypy/secrets都Passed；以独立copy-intent及[proof](../../../intake/G3/2026-10-09-model-resolution/eol-source-proof.json)续收，不覆盖旧失败日志、不跳钩子。

钩子统一换行前的`model-affected-final-03`：14受影响文件，**606 passed，failures/errors/skipped均0**；pytest76.31秒、controller76.898秒、exit0、无timeout，全部执行源hash保持。包括三个独立公开CLI进程的alias冷跑／warm／删除当前许可后seal；后两步无新增HTTP且同包bytes。`model-static-04`：24格式／类型命令全0、mypy57源无问题、7.436秒；与static03比产品源码相同，仅恢复fixture变。具体入口与直接／间接覆盖见[测试映射](test-map.md)。

换行后的`model-affected-final-04`实际14文件**606P／0 failure-error-skip**，pytest75.96秒／controller76.591秒，exit0／无timeout／执行字节不变；24份snapshot02 raw与该执行副本／记录逐项一致，117原保护文件仍原字节。`model-static-04`产品文本未变，首轮正常owner hook的静态门也已Passed。最终正常source提交三个命令全0、24文件、origin/master与HEAD相同；[终态核对](../../../intake/G3/2026-10-09-model-resolution/verification/final-verification.json)实比141源／自有副本、117未改／24授权且原七未知项保留。

原日志、JUnit、每轮已实际捕获的源码／guard／runner均按不同label留在`intake/G3/2026-10-09-model-resolution/verification/`；不将重复次数加成独立测试数。最早model-red/config-red两轮没有完整执行源快照，只保留原hash／日志，不能补填后来源码冒充。

## TDD与错误的区别

| 记录 | 实际结果 | 含义 |
|---|---|---|
| model-red-01 | 3F/157 deselected | 未注册替换被认可、裸成功attempt无durable源可checkpoint、新alias接口缺失；动态RED |
| model-config-red-01 | collection error | 当时helper尚不存在，不当配置规则动态测试 |
| model-async-red-01 | 300.027秒timeout，source changed | 沙箱异步窗口及并发改测试导致无效验证，不当产品RED |
| model-async-red-02 | 4F | repair来源与uncertain/persistence传播的真实RED；同命令批准后执行 |
| model-core-check-01 | 512P/4F | 302伪完成body采身份过宽、两429 fixture缺必需错误码 |
| model-regression-check-01 | 55P/19F | 18旧裸receipt夹具／1旧schema期望需要接完整来源；ACK/JR2原断言保留 |
| model-affected-check-01、final-01 | 各590P | 阶段GREEN；不是下方新缺口的证明，不冒充最终验收 |
| model-final-attempt-red-01 | 6F/2P | 旧repair抢占新attempt及重签旧来源可读的真实RED；原unknown/late两保护保持 |
| model-async-model-red-01 | 1F | await后真实POST模型C，而冻结意图／预留仍A；真实RED |
| model-affected-check-02 | 605P/1F | 新fixture错误期待pending；原已发未checkpoint的uncertain恢复正确 |
| model-affected-final-02 | 605P/1F | fixture漏真实预算注册，在mark_send_intent被严格拒绝；没有改产品准入 |
| model-recovery-fixture-check-01 | 1P/103 deselected | 真注册后恢复、来源、预留、旧lease拒和不重问断言通过 |
| model-affected-final-03 | 606P | 钩子前批准字节的完整受影响GREEN，原记录不改 |
| model-affected-final-04 | 606P | 换行后实际发布字节的完整受影响GREEN，独立新label／source02 |

static01曾有5个mypy类型错误，局部保留runtime严格校验修复；后续最终57源无问题。collector首次拒绝唯一额外`qa/logs/stock_qa_20261009.log`，它来自原logger的dated FileHandler。保存initial controller、给该精确输出记SHA/bytes并排除源码发布，任何其它额外文件仍拒；该日志保留在自有根等待严格清理，不清洗原数据或静默放行未知文件。

## 证据边界与后续

native测试是合成payload／HTTP替身，不是真实厂商alias、真实公司搜索或准确性实验。只测受影响14文件，未重复全仓／UI／收费矩阵。迁移直接起点1/2/4/6/7，3/5由共同升级链覆盖；legacy after_question独立alias成功、alias专属late及所有跨响应组合没有声称逐个直接测试。canonical JSON SHA不是raw网络body hash。

guard实际network-attempts=0，移除真实API key环境；原source01记录846次、新source02记录987次累计自有synthetic配置读取，均为各自冻结时点，不把累计读取当独立请求或测试数。这是Python audit范围证明，不能冒称完整OS读隔离。未读取真实公司文档、下载、生产库或发付费请求。

本批批准后只发布24原范围最终字节，正常owner钩子／commit／push；源hash变化先停，不跳钩子或force push。严格CIM／lstat／单硬链／精确set-size-SHA的dry→Apply仅清本批OWN，保留共享TEMP、旧Phase92、未知未跟踪／个人配置。实际Git与清理结果另附，不以意图替结果。

JR1/JR3的StockWiki四路径新增写许可仍待答复。原SW／Lab有限签收保留；真实ACK闭环、双owner恢复、真实身份／事实query golden、G3/F05、TH/IN和L03未因此完成。不刷新退役回执，不自动开展200家live。

## 实际交付与清理收口

StockQA `42a517c4bd6bc8219f926957c6c332944da3278a` 已正常提交并推送origin/master；新source-git-eol三命令均0，24源文件与测试raw相同、原七未知项保留。终态141文件对照及原117未改通过。清理dry-run与Apply分别原78550／48950实际exit0，strict CIM0／lstat单硬链无reparse／精确set-size-SHA，仅本批自有根**5492文件、2530目录**，根已不存在；[清理回执](../../../intake/G3/2026-10-09-model-resolution/cleanup-receipt.json)。没有删除共享TEMP、原Phase92、外仓或未知项。IQS本批工件随后以真实归档index与Git回执交付，不在此提前填结果commit。
