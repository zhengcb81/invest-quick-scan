# 新一批可独立开工的施工包

编制日期：2026-10-11。状态：文档已准备，未由总控创建工作仓、派发或实施。主线仍在 B01 首轮真实扫描后的修复与联调；本批不改变金融准确性、G3/F05、UI/一键上线门状态。

后续实际状态：OPS、FIN与VIEW均已收到并集中验收为changes_requested；OPS remediation-01现已续验，R4关闭，原writer只续同包三组R2；FIN四组/VIEW五组仍续原R1。见[实时交接状态](dispatch-status.md)。以下目录不存在/未派发是原编制快照，不代表当前OPS/FIN仓不存在；原manifest/输入锁/模板不回写。

| 施工包 | 完成后交付 | 唯一工作目录 | 现在可以做什么 |
| --- | --- | --- | --- |
| [VIEW-01](VIEW-01.md) | 可操作的只读企业结果界面、版本化输入适配、浏览器测试 | `C:/Users/郑曾波/Projects/iqs-viewer-lab` | 用冻结契约和明确合成样例开发；真实 StockWiki 接线留总控 |
| [FIN-REF-01](FIN-REF-01.md) | 三公司正式题集的官方事实核对基准、计算工作表、盲评规范 | `C:/Users/郑曾波/Projects/iqs-financial-reference-lab` | 公开官方网页人工查证；不调用模型、不下载公司文档、不授予 owner 资格 |
| [OPS-DESK-01](OPS-DESK-01.md) | 运维实操手册、故障决策表、脱敏诊断样例及离线浏览工具 | `C:/Users/郑曾波/Projects/iqs-operations-lab` | 从冻结设计和已公开故障记录开发；不运行生产诊断/恢复/模型调用 |

三根编制时实际不存在，彼此不包含；不占 IQS、StockQA、StockWiki、company-wiki、Theme/Industry，也不占现有 EVID/FACT/MATRIX/LOAD/IDENT Lab。开工必须重查目录和 writer。三包无互相依赖，不要求另两包先交付；同一包仅交一个 harness。

## 直接交给 harness

把所选施工卡的完整绝对路径发给 harness。每卡连同 [共同规则](handoff-rules.md)、[冻结输入](inputs.lock.json)、[范围清单](manifest.json)、同名 handoff 模板即可独立恢复上下文。不需要读聊天，不要自动创建线程或代用户派发。

接口冻结的是本包开发基线，主线继续演进不阻止已冻结开发。新能力未发布时显式 `unsupported/not_run`，不得拿私有候选或合成样例宣称生产就绪。

## 接线责任与验收

- VIEW：总控将组件接入 StockWiki 既有 Web/query 服务；页面不持有第二份公司库、评分规则或刷新权限。
- FIN：总控把参考行接 B01 的逐题盲评，并复核主观评分区间；参考资料不等于模型准确率或正式金融 golden。
- OPS：总控在发布后核实实际 CLI/help/版本，接入唯一启动入口；手册不能让尚不存在的拟定命令变成可执行命令。

每包在稳定候选做一次集中 unit/integration/E2E 与包级审查，修复只续跑受影响项。不为小节点增加新审查门。

交回路径为自身仓 `docs/handoff/<package-id>/handoff.json`。沿用 IQS 公开 handoff 1.0.0；总控结构预检：

```powershell
python -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11-wave2/manifest.json --package-id VIEW-01 --input C:/Users/郑曾波/Projects/iqs-viewer-lab/docs/handoff/VIEW-01/handoff.json
```

另两包替换 package-id 和自身路径。结构通过只证明形状和声明范围，实际验收仍核原始输入、Git、测试和产品行为。本批 `validation.json` 仅为文档编制验证。
