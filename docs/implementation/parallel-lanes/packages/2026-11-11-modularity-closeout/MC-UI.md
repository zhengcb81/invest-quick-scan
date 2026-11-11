# MC-UI：原8766工作台成为纯公开接口消费者

可独立交harness。先读 [总路线](README.md)、[契约/TDD的C5](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。C5是本次双方约定，真实IQS实现由MC-IQS提供；本包可先写fake测试，不代改IQS。

## 目录与范围

- 正确源仓：`C:/Users/郑曾波/Projects/iqs-question-bank-ui-lab`，HEAD `47d5354`；**不是iqs-viewer-lab**。开工核实dirty状态，不能假设干净。
- 实现树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-UI`；`codex/modularity-ui-20261111`，尚未创建。
- 允许：scripts/serve.py、build_data.py、adapters/paths及快照适配、src/app/product_api.js/store.js及必要显示层、对应tests/README/本包PWF。
- 保留比较/名单/TIME/RESULT现有组件，不做视觉重设计；不写IQS/StockWiki/QA/Dashboard，原答案/历史名册只读。

## 根因和目标

旧链为IQS启动UI脚本，UI再把IQS/scripts加入sys.path并构造服务；build还认识IQS questions/runs/docs和固定历史日期。目标改为IQS公开启动装配server，UI只提供静态文件；题库/版本/草稿只读C5公开snapshot，正式结果/任务仍走现有HTTP。UI不得自己按名称/ticker裁决公司身份。

## 实施步骤

1. 先锁住当前用户行为和输出形状，保留五个generated对象的消费；明确历史草稿与正式结果来源区别。
2. 用无IQS源码树的snapshot fixture做RED；生产store一次读取C5的/generated/snapshot.json，从同一响应投影五段并处理availability/warnings；不拆成多次读或新增状态核查票据。IQS在自己的state_root生成快照，UI不需要知道物理位置。有效fixture由IQS提供；先按协议造明确标合成的fake，不冒称真实golden。
3. `serve.py`保留兼容命令参数，但调用IQS公开启动，不再import其服务实现；静态开发/预览可独立，不新建第二API服务器。最终启动兼容由IQS与本包一起测。
4. 解除paths.py中的owner内部路径和2026-10-18默认依赖。build_data仅作显式离线snapshot工具，普通启动不调用它；旧verify只核可用段。historical reader由IQS提供，不能复制进UI另一个helper继续耦合。
5. 草稿身份没有owner唯一绑定则unbound/provisional；synthetic差异只从UI自有fixture显式显示。正式结果不得因此缺失或降级。
6. 原HTTP client保留超时、同源、CSRF与不自动重发写操作；schema/optional字段只按公共兼容约定处理。
7. 相关行为测试和独立agent审查；真实C5尚未完成时只报消费者ready，不报正式接线通过。

## TDD

|场景|结果|
|---|---|
|只有UI静态资源+snapshot，无IQS questions/runs/docs|题库/版本/草稿可展示；原/#/dashboard加载src/app/index.html及其资源|
|UI代码反向import IQS或加入其scripts路径|边界mutation失败|
|题库扩张、roster/草稿不可用|无硬编码题数；局部说明，不拖垮任务/设置/正式结果|
|bank available、roster unavailable、answers partial；no-refresh快照缺失|null/未知计数不伪装0；部分草稿与原因可见，正式结果正常；不回读旧UI generated混代|
|同名公司、跨市场重复ticker、无唯一绑定|不自动verified，不最后写入覆盖|
|写请求超时/页面重载/服务重启|查询原命令状态，保持同幂等键，不重发收费|
|兼容optional字段、错误major/错scope|按公共协议接受/报错，不全局白屏|
|生成快照/浏览|不写owner、不联网模型、不延长原TTL|

已有针对性入口：

```powershell
python -m unittest discover -s tests -p "test_serve_runtime_origin.py"
python -m unittest discover -s tests -p "test_serve_snapshot_isolation.py"
python -m unittest discover -s tests -p "test_product_ui.py"
python -m unittest discover -s tests -p "test_optional_draft_boot.py"
python -m unittest discover -s tests -p "test_company_result_ui.py"
```

新的快照/边界用例进入现有测试入口。只启动隔离端口，不占用户8766、不杀现有服务。UI走查使用真实本包资源+fake API一次，最终总控I6用当前IQS服务再验。

## 交付

自己的命名PWF、`docs/handoff/MC-UI/handoff.md`：C5消费者版本、保留的用户入口、删除的内部路径依赖、测试/独审、commit。没有必要新建权限、快照签发或下载流程。
