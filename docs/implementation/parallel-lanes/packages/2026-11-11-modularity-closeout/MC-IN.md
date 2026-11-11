# MC-IN：行业研究公开查询消费与兼容验证

可独立交harness。先读 [总路线](README.md)、[契约/TDD的C4](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。本包优先验证已有成果，不为凑改动重写行业研究。

## 2026-11-11 入场盘点与并线清单

[实查](intake-audit/store-consumers.md)：`main@7d49ca3` tracked clean，但新增未跟踪`tests/test_quick_scan_module_boundaries.py`；它是待审源码，不是临时测试输出。两条report-generation分支均为main祖先，旧worktree干净，不需要再merge。

先将这份边界测试纳入本卡TDD，审掉重复/过度静态解释规则但保留域级反例；与原五个快扫测试一起验证后提交。没有实际实现缺口则不强行重构。origin/main只在本地ref与main一致，发布前按原流程核远端，不把本次只读盘点说成远端已验证。


## 目录和范围

- 源仓：`C:/Users/郑曾波/Projects/industry-research`，HEAD `7d49ca3`，调查tracked clean；开工复核。
- 实现树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-IN`；`codex/modularity-industry-20261111`，尚未创建。
- 允许：tools/quick_scan_client.py、相关报告/卡片投影、快扫公开schema资源与tests、文档/命名PWF。已有行业框架/研究模型不重构。
- 不写Theme/StockWiki/IQS，不改正式公司记录、既有报告，不下载文档/调用收费API。

## 目标和步骤

1. 保留公开CLI、消费者capture、报告插入；盘点大量手写2.7枚举/必需字段，识别哪些是本域投影，哪些在重复owner语义。
2. 用C4同一公开schema/DTO向量先测兼容：允许optional扩展、真正缺必需字段/错身份/错snapshot；不是先把所有exact检查删除。
3. 普通wire规范保本地有版本的公开schema/规则，不到对方内部源码树找资源，公开CLI路径参数继续兼容。当前2.7来源为StockWiki@12c441e的config/quick_scan_facts_query.schema.json；最终用MC-SW的tests/fixtures/public_contracts/facts-2.7/公共向量，与Theme同义复测。开工可先用本仓fixture。只读对方交付，不修改它的文件；当前closed schema未知字段仍拒，允许的是已声明optional，不自升级2.8。
4. 只用public transport可运行，无StockWiki安装；调用失败在研究输出里显示缺口，不伪装空行业、不自动补扫。报告不重算或升级快扫评分。
5. 若无实质缺陷则保留实现，补确实缺的TDD证明；有失败再最小根修。相关短组和一次独立agent审查后交付。

## TDD用例

|场景|预期|
|---|---|
|public fake transport，无owner源码|研究消费者可运行|
|允许optional字段/同义schema格式|正常投影，不多一套白名单误拒|
|错误major/必要字段/主体/operation|真实错误明确，不吞成空结果|
|query分页、独立export、重放|请求与snapshot对应，owner只读，capture属于消费者|
|quick-scan unavailable/部分事实|行业报告仍生成且标缺口，不自动模型/搜索|
|未知公司或同ticker不同市场|按owner身份，不以名称猜成唯一公司|
|报告重复插入/已有评分|保留原正文与原分数，不生成更高信任标签|
|反向import/外库直读mutation|正常架构测试能捕获|

现有短组：

```powershell
python -B -m pytest -q tests/test_quick_scan_client.py tests/test_quick_scan_report_section.py tests/test_quick_scan_e2e.py tests/test_quick_scan_module_boundaries.py tests/test_quick_scan_card_boundaries.py -p no:cacheprovider
```

用临时capture目录、网络禁止；架构相关测试名有e2e不等于真实owner/模型验收，应明确所用transport。

## 交付

本仓命名PWF与`docs/handoff/MC-IN/handoff.md`：实现commit、仍使用的wire版本、与Theme一致的语义向量、实测命令和独审结论。最后总控I5使用真实StockWiki提交组合；本包不因此声称G4产品使用或G3规模已经完成。
