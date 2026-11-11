# MC-TH：主题研究只读消费者与schema误拒

可独立交harness。先读 [总路线](README.md)、[契约/TDD的C4](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。只改Theme，不代改StockWiki/IQS。

## 目录和已有改变

- 源仓：`C:/Users/郑曾波/Projects/analyze-theme-value-chain`，HEAD `3352b58`。client和integration test已有tracked修改，另有`quick_scan_client_test_harness.py`等新文件；开工必须完整识别支持关系，不能只提交两份tracked diff。
- 实现树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-TH`，`codex/modularity-theme-20261111`，尚未创建。
- 允许：scripts/quick_scan_client.py及本域测试harness、tests/fixtures、公开schema本地资源、使用说明及命名PWF；不改主题估值/研究方法，不动已完成研究输出。

## 根因与方案

当前load_validator固定schema原字节SHA，默认进入IQS源码树找schema。与StockWiki公开schema语义完全相同的格式变化仍被拒。按C4使用本地有版本的公开schema/校验器，不进入IQS/SW内部源码找资源；公开CLI的owner_root/iqs_code_root配置仍保留。公开schema复制是合同资源，不是私有实现。

## TDD步骤

1. 先RED：同一schema改变空白/键序/CRLF仍应消费；用StockWiki公开同义schema复现旧误拒。错误major/必要字段/身份要有相反测试。
2. 移除原字节hash的普通准入与源码路径默认，固定本地公开schema版本和来源说明；原来源/回答摘要完整性不删。
3. 客户端只通过OwnerCliTransport调用现有公开命令，保持capture-root本地。用无StockWiki安装的fake executable验证独立运行。
4. 同一组C4 DTO向量覆盖分页、query/export不同snapshot、重放、optional扩展。错误不能被吞成无公司/无事实。
5. quick-scan不可用时主题研究可继续，显式缺口；不自动调用LLM/搜索补全。独立agent审并修完，形成自包含commit。

必测：语义同schema格式变化成功；错误wire与错主体失败；只读不写owner；分页/导出请求哈希与operation不串用；用户输出根以外不落文件；消费者不导入owner模块、不发收费调用。当前2.7只接受已声明optional（如Request.label、Counterparty.text/entity_ids），未知字段按closed schema拒绝，不自行放宽。共同向量最终来自MC-SW的tests/fixtures/public_contracts/facts-2.7/；开工先用本仓fixture。

现有入口：

```powershell
python -B -m pytest -q tests/test_quick_scan_integration.py -p no:cacheprovider
```

新边界/fixture用例纳入此短组或本仓正常发现；没有新的实现缺陷时保留成熟行为。无需等待StockWiki包完成才能用既有2.7协议开工。

## 交付

自己的`.planning/modularity-closeout-20261111/`与`docs/handoff/MC-TH/handoff.md`；最终commit、schema来源/版本、RED/GREEN、独立agent结论。无remote时记录本地发布。真实SW当前提交的I5由总控组合，不用历史golden替代。
