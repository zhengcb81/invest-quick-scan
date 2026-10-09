# W15模块持久化与评分扩容准备

本批接续既有W15任务，不新增逐helper审查门。2026-10-09用户全部后续所需授权已生效，root总控为唯一writer。起点：IQS469d11b已推送、StockWiki6c46f03本地clean且按决定7无remote、StockQA bc41908已发布。未知opencode与其他项目工作保留；现阶段0收费、0正式库/名单迁移。

## 当前接口事实与实现顺序

W06已有逐题语义/作用层/TTL/未知冷却的纯缺口计划；W11实际只处理基础字段缺失。Q13已有manifest/问题集绑定及新增题/未知发送对账，但不能把其存在说成完整StockWiki模块持久化或字段时效送达。IQS的routing.validate_route_snapshot、validate_route_for_execution和question_manifest.validate_manifest_metric_contract已有发布包/策略/选择/逐题定义/精确prompt完整验证；StockWiki不得复制这套题库、路由算法或导入另仓Python模块。

1. 先在IQS增加公开**离线route-bundle validator**，完整调用原验证器，给出有版本、两原文SHA、独立expected ID、发布包/模块锁及原执行上下文的校验DTO。必须要求调用方独立持有expected ID；自报/重算hash不是来源认证。校验history与新execution明确分开，历史不产生新派发许可。CLI仅JSON stdout和具名拒绝，不能执行输入命令或联网。
2. StockWiki从公开适配器取得DTO后，在既有scan.sqlite追加不可变路由/问卷原文与当前锚点，schema加法迁移及备份支持一起完成。CAS只更新当前指针，旧快照/分类置信度/实际ROUTE_02模型时间保持原样；旧router缺字段保持缺失。新派发从持久行独立读expected ID，不能从传入待执行快照自取。
3. 基于锁定模块/逐题语义、作用层/期间/模型和W06计划做模块增量刷新；新增题不改变24核心分，退出模块留历史不计当前覆盖，规则变化标不可比。未知费用/部分ACK经StockQA原Q08/Q09/Q10/Q13对账而非新账本；发现TTL新generation交接缺口在同批明确补接，不能静默旧题复用。
4. 接通公开store/query/refresh入口以及原C06 envelope投影，出当前实际serializer golden和生成命令。身份真实性与真实公司金融准确性另按原门；合成测试输出不得冒充真实owner正例。

## 本批路径与边界

IQS当前先写scripts/route_store_handoff.py、schemas/quick_scan/route-store-validation.schema.json、tests/test_route_store_handoff.py及本目录计划/证据/PWF。后续StockWiki拟写quick_scan_routes、schema/store迁移、refresh、CLI及备份manifest和对应测试；Q13如需TTL代际接续，按实际缺口报备最小范围。全授权无需再次按文件请求，但每次写前重核HEAD、现有dirty归属、实际接口和唯一writer。安装镜像、company-wiki、真实公司文档不在本批。

## 接口规则

validator输入为独立route原文、与其相同的嵌入式manifest、调用方独立expected_decision_id、模式，以及execution模式的可信UTC时间；以原IQS发布包存储为根。绑定单一实体/作用层/分部、module_package/release、原manifest routing_execution、完整module locks，拒绝重复JSON键、非有限数、截断、篡改、重封另一ID或丢失归档。raw SHA与canonical decision_id分别记录，不能称为同一种摘要。

DTO只证明该原文在指定根的结构/归档/锚点校验，不签名认证供应商回答、真实身份或金融结论。StockWiki接收方必须绑定实际来自可信IQS校验入口的DTO及独立请求上下文，不能接收任意用户JSON并自称已认证。验证器不派发LLM、不创建任务、不补历史字段、不选择公司。

存储键还须冻结实际analysis_subject_id/revision及perimeter hash，而非仅issuer/ticker；同发行人的不同报表范围不能共享current指针或覆盖。从StockWiki现行AnalysisSubjectStore读取subject与perimeter receipt，匹配primary issuer及作用层；原entity/挂牌仍分别保留。schema6事务追加route_snapshot与route_current、CAS指针和备份上界一起验证，真实库不迁移。当前validator第一段只支持发布manifest3.1+route schema2（含router2.0–2.3历史），不把legacy route schema1意外缺scope的读取路径称为支持。

## TDD和集中验收

先保存公开producer实际生成route/manifest的合成测试RED，再实现GREEN。重点覆盖重新封印的route锚点冲突、manifest与route差异、篡改逐题prompt/归档、当前可编辑catalog升级不重释旧manifest、原字节SHA和CLI错误退出；接续覆盖router2.2置信度保真/2.0–2.1缺失、模块新增/退出、边界TTL、作用层/期间/模型不可比、竞争CAS/迁移回滚、部分ACK与零重复收费。

所有测试使用全新独占runs/w15a及其临时发布/SQLite，凭据环境剥离、禁Python网络/非自有DB；mock只用外部边界，公开CLI另由真实OS子进程执行。归档日志及执行SHA后，终态检查、真实lstat/链接/文件SHA/绝对边界清理本批自有根，不清共享TEMP或其他进程状态。

开发只测受影响范围；整个评分扩容准备包结束做一次集中独审和正常提交。任何小入口GREEN都不关闭W15整包、L03/G3、B01准确性、F05、TH/IN。W15后先固定用户已同意216挂牌中的真实200公司运行输入及B01准确性门，未通过就保持开放；不自造2000名单。
