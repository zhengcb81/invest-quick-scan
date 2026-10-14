# ROUTE-E2E-03 / CHAIN-SOURCE-03 / BLIND-REVIEW-03 总控验收收口

日期：2026-10-14。结论：三个包完成集中独立审查和直接修复，按源 HEAD 与逐文件 raw SHA 做 CAS 回写并正常提交；接收范围是软件/研究候选。路由与产业链资料仍 partial，盲评工具仍有真实输入适配边界。**没有取得金融 gold、真实 owner 映射、生产执行或正式发布资格。**

## 交付与原件

|包|分支|冻结交接 HEAD|总控修复提交|精确发布文件数|
|---|---|---|---|---:|
|ROUTE-E2E-03|codex/route-e2e-03|b426f697146675f063e066c476a10ad052670b10|617171b1d96604325bb264761b723d19b77b0357|533|
|CHAIN-SOURCE-03|codex/chain-source-03|cfb497acc1283e4a16b5e7c24788cd557292038e|5c5dd1404f44f899251143d3f1430b1fcd9a41a0|25|
|BLIND-REVIEW-03|codex/blind-review-03|e7185b68a3ca1e765980b13c5e2dd26b7b137e8b|0b0e0666376f63ee116ca1683b9e26c34d436c15|20|

工作目录分别为 C:/Users/郑曾波/Projects/iqs-route-e2e-lab、iqs-chain-source-lab、iqs-blind-review-lab。修复提交后各 Lab tracked 业务 clean、index 空；CodeGraph 设施不算业务交付。原 worker 的 docs/handoff 不重签，最新总控报告独立放在各 Lab 的 docs/coordinator/acceptance-2026-10-14/。

原 ROUTE 1138 项和 BLIND 1231 项交接 manifest 的 raw SHA 全匹配；CHAIN 37 项只有35项匹配，README/progress两项是旧摘要，且原结果 commit 后有23文件后继变化。接收依据是本轮实际 HEAD、工件冻结和后续修复，不采用旧自报 complete 取代验收。原交接、冻结 fixtures 与所有实际失败记录保留。

## ROUTE：完整链能跑，不代表标签有充分证据

保留原47例固定分母，43例完整 request→resolve→compose 通过，4例缺真正历史 prior decision（C19/C20/C23/C47），只完成 request 后停止。实际133次公开 CLI 均 exit0；4个链失败不是调用报错。比较结果是 **14 matched /32 input_gap /1 diverged**。32个缺口由28个生命周期事实不足和4个 prior 缺失组成，C16为显式诊断请求差异。新增合成序列是独立7类/17步，全部真实三入口与断言通过，不加入47例分母。

删除分类标签扩写出的30条经营生命周期“事实”，不再给 C09补两期、给 C22收入15%补毛利/资本分母，也不把 selected_modules造出来源、日期或历史份额。validator核 actual命令顺序/退出码/PID/引用SHA/原case/实际模块和题号/比较/立即前期决议。现拒绝删除既存 sibling release、写冻结区、伪 passed 和未来版本。便携导出携带432个真实归档引用，中文长路径写入已修。

主与序列结果协议显式升为 **1.1.0**，entry_point_runs闭合六字段；原卡严格三字段与旧交付六字段同版不一致，原1.0 schema/样例保持原字节，旧实际形状仅作 historical_archive_only 读取。兼容读取不授事实质量或新资格。

## CHAIN：错源、日期与关系归属已修，仍未封闭资料缺口

36原槽位原序、18原partial、41原gap ID全部保持。当前59 claims /25 sources /68 attempts /52 gaps /13词条与13查询提案；槽位29partial、6unverified、1not_applicable，claims45partial、10unverified、4corroborated。

修正大众 MOU 与极氪新闻错源、半年度/全年混淆、计划未验证误称 contradicted、发起人历史7%误当现行持股；Google/Apple官方HTML支持合作及未来模型/云计划，仍不支持“首选云供应商”、金额或实际部署。滚动TPU页日期绑定具体公告，实绩与计划分开。中信建投 gap 不再挂 CATL槽位，词条/提案不跨槽借证据。运行时实际复用冻结 CHAIN reader/hash/题目/schema函数；所选主文件/侧车按原字节验证导出，不读浮动源仓。

主协议 **1.1.0** 显式封套 record_id、public_source_reference、not_mapped、not_run、原九字段payload。CS03-R001–036固定顺序；原1.0 schema/历史样例保持，侧车仍1.0。新旧reader先核本版schema再规范化，未知未来版本拒绝。公开HTML人工核源和 keyless离线软件测试分开，未重访来源、抓取timeout及弱证据保留，source-review.md不声称全面重新核证。

## BLIND：不会再把未审或主观评价算成客观准确率

严格六字段主协议 **iqs.blind_review_contract_candidate/1.1.0**，额外适配说明移到独立附录。新review_input/1.1.0核显式答案/题目sidecar真实bytes、raw/objectSHA、主体、期间、cutoff与题义。旧1.0仅synthetic asserted-only，不追认新担保；未来1.2/2.0拒绝。

新私有映射仅保留 reasoning_sha256，不保存思考正文；原输入只读。修复转义文本泄露、同answer_id跨请求碰撞、future citation、失败槽位超限、packet篡改后join不复核、路径/链接越界与双根失败回滚。未评审的 agreement/coverage分母0、rate=null；主观判断不进factual accuracy。所有失败/未审槽仍在ledger。

EVID strict_loads/canonical_fingerprint、FIN validate_pack与SCORE interval实际调用冻结函数并有spy证明。FIN真实校验返回false：3 manifest_sha_mismatch、6 locked_input_missing，90 expected_score仍null，未因运行函数或软件通过获得金融资格。

**真实参考集桥接尚未完成**：现参考集适配仅支持封闭synthetic reference-set；真实公开reference-set和其他模型原始回答布局必须显式适配，不能猜补。1.1 sidecar不是通用vendor导入器；内容hash不认证作者，reviewer不是已认证真人双审。双根回滚不宣称机器断电事务或系统级race防护。

## 测试证据与复查入口

每包一次集中审查；真实RED保留，后续只测受影响集合，不追加逐helper审批门。使用 run_lane.py：600秒时限、keyless、父子禁网、Python子进程限定、单lane自有写入；Windows硬链接/junction需离开沙箱时仍保留这些护栏。形状校验、合成回归、真实内容核证是不同结果，不相加为准确率。

|包|最后集中/受影响验证|实际PID|限制|
|---|---|---:|---|
|ROUTE|适用包级126P/2skip/6deselect；最终版本/CLI46P|55548；51460|2次长重放已单独执行；6历史manifest/Git检查由总控原仓只读核查，未重签|
|CHAIN|最终集中117P|65004|公开来源核证缺口独立保留|
|BLIND|最终受影响45P；原生junction1P；复用3P|40716；20856；30952|154不同用例跨批末次通过，不声称一次154项全绿suite|

本机可复核的原收据目录是 C:/Users/郑曾波/Projects/invest-quick-scan/runs/next-acceptance-2026-10-14-02/。各reviews/<lane>/report.md、repair-manifest.json、测试收据及logs/<lane>/*.process.json、stdout/stderr/XML均保留。closeout-audit.json逐项复核发布bytes、冻结fixtures/handoff、每份实际stdout/stderrSHA和XML统计；source-publication.result.json保存原HEAD、精确文件、正常commit与tracked状态。

需要以后复跑时先新建独占隔离副本/一次性label，不直接重跑旧句柄或旧发布脚本。例如此轮实际CLI集合：

```powershell
# 在新的keyless隔离runner内运行，不在真实源库或旧测试namespace执行
python -B -X utf8 -m pytest tests/test_protocol_versions.py tests/test_independent_acceptance.py tests/test_cli_e2e.py -q -p no:cacheprovider -o addopts=
```

三包CLI均在其src包中公开；具体argv以实际收据为准，避免猜入口或补造历史命令。已通过范围没有新变更时不重复长整链。

## 清理、错误记录与主线接续

三个实际测试PID闭包为0，temp/route、temp/chain、temp/blind为空。路由7个辅助脚本已移至reviews/route/audit-tools并逐字核SHA；CHAIN两轮精准删除198文件/82目录；BLIND移除4份本轮临时输入。原01快照Windows长路径失败副本、失败日志、原件、候选和精确source-before-repair备份保留，不清他人未提交文件。根2026-10-10 README他人4行改动不改不暂存。

如实保留本轮错误：首次快照超260路径，02用扩展路径和排除旧tmp/staging重新冻结；初版publisher不识别repairs/entries，在任何源写入前拒绝，已修；closeout沙箱Git/CIM读取拒绝，离开沙箱进行只读实际核查；沙箱CIM错误不能当成零进程证据；首轮closeout发现temp残留7脚本，归档后再核为空。此前RED、版本/导出Windows错误、错误pytest节点和失败XML均未擦除。

本轮真实模型请求、收费搜索、公司文档下载、生产名单/数据库写均0。原real work.sqlite SHA **236e5aa4c4252a37f76c092100c8012c9abff11ee60914edb839bf424b0864e2** 不变，仍schema18；源能力支持19不表示已迁移。原30题/13HTTP/26native搜索/CNY1.268162/26expired leased/4blocked insufficient/0正式评分/ACK0保持。

下一步回checkpoint55原B01：先只读核真实上下文/owner与26/4恢复边界，备份、参数预览后用原公开入口按真实批准恢复，并接明确的真实答案/参考集盲评adapter，保留FIN锁/来源缺口和null。随后做小规模LLM×搜索×题包准确性对照，准确性优先，费用与速度分别计。候选包不替代真实确认、正式schema发布或双人金融核证；Financial/G3/F05/生产UI/一键/全池均继续开放。三包已接收，不重复派发。
