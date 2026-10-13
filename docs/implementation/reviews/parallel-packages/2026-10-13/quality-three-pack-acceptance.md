# 三个质量施工包总控验收收口（2026-10-13）

三个原交付均有实质问题，总控在互不重叠的隔离副本中补反例、直接修复并接收。**接收范围是软件和研究候选，未授予金融准确性、生产身份、正式路由或评分尺发布资格。** 原worker handoff保持历史，总控记录另放各Lab的docs/coordinator/acceptance-2026-10-13/。

|包|修后实际用途|验证证据|正常本地提交|
|---|---|---|---|
|ROUTE-COVER-02|48模块、47适用性案例；补锁/日期/10%保留与unknown边界|全集161P、原native v2另5P/7subtests、末次受影响20P；166独立test，后续20不重复累加|6829cc6230c9b63fc9c97bbb932e9ee6ec105271|
|CHAIN-CONTENT-02|三公司36槽位、64claims、35sources；仍partial，17supported/18partial/1N/A均是候选|全集117P；后来发现主体错引后38P受影响回归；旧builder退役7P，批次不累加|4ea357921f606328776c9834254193e4b2624ce2|
|SCORE-ANCHOR-02|24构念、45单题盲例、10单变量配对、16诊断说明|全集132P；最后情景细化后86P受影响回归，不重复累加|993e0a9e4ff525670b8631579057c8f027529086|

三个CodeGraph索引已按用户授权初始化，.codegraph设施未入业务提交。CAS交付分别14/19/12文件（包含独立总控记录），精确原HEAD/rawSHA与候选SHA核对，现各Lab tracked业务clean；未覆盖原handoff。一次性修正工具只在私有reviews保留，不发布成运行工具。

## 主要改进

- ROUTE把材料覆盖与实际路由覆盖分开：47例legacy原CLI实际41成功、6拒绝；C21/C23重大性差异保留。另用原synthetic fixture验证15%入、10%保留/9%连续退出、两期切换、低谷保留诊断、unknown common-only。其余47例完整v2及真实owner全链仍not_run。
- CHAIN撤掉用2008法规支持2025资管规模的错引，纠正采购/托管/股东角色、日期和官方来源标签，清除CATL借Alphabet evidence的词条。Google/CATL主源HTML已抽样读过；CSC官方正文、动态公开日、部分具名关系仍保留缺口，未用摘要或事件年伪造证据。validate/export验证实际选择的依赖，坏输入零输出；旧build_content入口明确退役，不能重建错内容。
- SCORE不再用循环题号假装24构念覆盖，不把多变量/不同主体对照称因果对照，不让9分要求高于原10。保留原题对象、metric、权重、原1/5/10及正式schema；缺信息分数null。卡遗漏的配对metadata由总控明确接受原候选v1 schema的可选字段；没有改生产格式。

## 边界及后续消费

ROUTE供C01原路由/模块回归；CHAIN供F03/F04/F05/F06事实关系/词表；SCORE供C02候选标尺和B01盲评。总控统一根据冻结question_object_sha256做CAS，改题提案另留，不直接覆盖原题。旧作者emit_*/build_gaps/build_handoff/run_checks属于历史过程，不可作为当前签收或覆盖新内容的入口。实际公开薄CLI validate/export与测试可用。

本轮与源码收口没有收费模型HTTP、收费搜索、公司文档下载或生产数据库/名单写。source支持work schema19；原真实work仍18，26expired/4blocked、13HTTP/26搜索/CNY1.268162/30题/0有效评分/ACK0保持。金融90题null与gold0保持。G3/F05、真实owner ACK、生产UI、一键和全池没有因此关闭。

## 清理与留档

ROUTE实际358临时文件、SCORE19文件清理后空根；CHAIN闭包0后逐路径/rawSHA清理953文件/478目录/28,900,782 bytes，空根。B01提交后测试temp另清190文件/474目录/144,309,371 bytes，空根。原件、修复候选、失败/通过日志、SHA清单、备份与原真实账本保留在私有runs；不把这些批量加入Git或远端。

详细报告：

- [ROUTE报告](C:/Users/郑曾波/Projects/iqs-route-coverage-lab/docs/coordinator/acceptance-2026-10-13/report.md)
- [CHAIN报告](C:/Users/郑曾波/Projects/iqs-chain-content-lab/docs/coordinator/acceptance-2026-10-13/report.md)及[source review](C:/Users/郑曾波/Projects/iqs-chain-content-lab/docs/coordinator/acceptance-2026-10-13/source-review.md)
- [SCORE报告](C:/Users/郑曾波/Projects/iqs-score-anchor-lab/docs/coordinator/acceptance-2026-10-13/report.md)

接续：沿原B01公开owner预览与真实原账本恢复，使用本批研究候选及既有FIN/PRIMARY做小规模准确性盲评；不重建已完成Lab、不重跑已绿长合成全链，不新增逐题审查门。
