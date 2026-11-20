# 版本、状态与质量误拒：架构复核及整改

2026-11-20。范围为 IQS、StockQA、StockWiki、Company Agent、Runtime、原工作台、Dashboard、Theme、Industry 的现行公开边界与实际拒绝记录。复用现有公开接口；没有新增框架、人工审批、任务回执系统或收费调用。

## 结论与设计

确实出现过形式标签压过真实数据的误拒。根因是四种职责混在一个“准入”判断里：接口能否解释、原始数据属于谁、任务是否结束、答案质量如何。现在分别处理：兼容协议按实际字段解释；原始题库及回答引用维持原绑定；已知结束的独立任务可继续；缺题和不足证据留在结果中展示。

保存成功不表示回答正确；formal 表示 owner 发布来源可核，不表示题题可评分。公司总分仍为空，不把诊断题或不同尺度随意混成一个分数。

|位置|实际问题|整改|
|---|---|---|
|StockQA 原语义资源公开端口|相同实现仅把 API 标签改为 1.1.1/1.2.0 就被拒|复用已有协议族、同主版本、最低能力版本判断；实际公开操作与原请求绑定仍检查|
|StockWiki V2 manifest/指标合同|schema 2.0.1/2.1.0 或 metric 1.0.1/1.1.1/1.2.0 数据不变仍被白名单拒绝|兼容小版本按实际字段解释；1.1 才具备的 context 能力按最低能力版本判断|
|StockWiki 结果登记|少题或任一 insufficient_evidence/N/A/search_unavailable 会拒整份快照|保留完整原 release 和实际观察，显式公布缺题与逐题质量，不要求全部 scored/answered|
|Dashboard/IQS 结果显示|已保存题数会掩盖证据不足；原逐题状态依赖可选回执|当前与历史消费可选 answer_coverage；原 public ref 的 answer_status 进入 answer_state；陌生可选元数据回退可读旧含义|
|IQS 多范围编排|实体题组明确失败仍阻止独立挂牌题组；退出状态还可能覆盖原未知发送|同公司保持串行，但等待已知结束而非必须成功；未知发送和活动工作继续等待，避免重复收费|

独审另发现相邻一致性问题：旧 registry 行被篡改后，重复登记可能先答 already_present，读回才失败。已复用原行完整性验证，使成功回执与可读记录一致。

## 历史与保留条件

11-16 的 content_filter 等供应商结束标签曾卡住已付恢复，现有 StockQA 已按原回执/结算事实处理，未知原标签不再天然拒绝。IQS `ac26a3b` 和 Dashboard `5018207` 已修复结果读面的小版本等号；本轮继续修复剩余公开端口与 owner manifest。

身份错配、原题目/原回答字节冲突、活动或未知发送的重复请求、真实新发送的额度不足仍返回准确状态。这些直接防止串公司、篡改和重复收费。原冻结题目定义、业务角色含义与尺度绑定不能靠修改标签强行重命名。新业务角色应由原 owner 如实发布并由读面保留，不能通过不断追加生产白名单演进；本轮未扩大到尚无生产反例的新领域合同。

Company Agent、Runtime、原 UI、Theme、Industry 的本轮检查没有发现另一个阻止正常调用的版本/标签门禁。Theme/Industry 的协商版本用于选定实际 wire，不是任意全局最低版本。静态模块大小等建议保持诊断，不影响正常结果。

## 验证

先跑误拒反例确认失败，再修实现。受影响回归：

- StockWiki 公司评估：116 passed；既有 `scripts/checks.py --static-only` 通过。
- StockQA owner refresh port：24 passed；接上同期新反馈提交 `79b0800` 后再次通过；既有提交钩子通过。
- Dashboard B03/反馈：63 passed。
- IQS 覆盖、公司读面、公开互操作：112 passed（不运行未改动的浏览器用例）。
- IQS 批编排：106 passed。

独立 agent `gate_audit_qa_runtime` 对最终代码复审 ACCEPT，另独立复跑 StockWiki 20 项、批次 13 项，并对 payload/hash/缺行/SQL 状态标签做四个对抗实验。发现的幂等问题已修复并重新审查。没有靠提高测试数量代替有效正反例。

## 真实数据结果

使用原中微公司 36 条 published 观察及原 V2 request：先在六个数据库的一致性备份上通过公开 CLI 登记→read/history→幂等重传；源库 hash 不变，临时 workspace 完全清理。一次隔离测试曾因 SQLite 连接未显式关闭造成清理失败，已关闭句柄、清除该目录并重新验证清理成功。

已随后在原 `runs/r25-live/owner-workspace` 通过 StockWiki 公共 operator CLI 正式登记：

- 实体：`ENT_99deceb6-f58a-48b1-bd6b-437621015d76`。
- 结果：`cas_6cab1b94d8f45d42c750`，registry sequence 1，资料日 2026-11-08。
- 保存覆盖 36/36；8 scored、28 insufficient_evidence；公司总分 null。
- 重复登记 already_present；当前与历史质量投影相同；除追加结果 registry 外，其余五库 hash 不变。

用原部署配置运行真实 StockWiki CLI→临时 IQS HTTP→真实 Dashboard adapter：返回同一结果、36 题、28 缺证据、null 总分；历史一致；所有数据库 hash 不变，临时 HTTP 关闭，0 外部网络/模型调用。原 8766/18792 长驻服务当时未运行，没有宣称已完成新的浏览器用户走查、E07 全部产品验收或金融内容补强。

## 交付

StockWiki `e4d7e85` 已快进 master（该仓没有远端）；Dashboard `faec291` 已快进 main；StockQA `2ec9682` 保留同期反馈提交后接入原运行分支。IQS 本轮提交包含批次和逐题投影修复及回归，不夹带其他仓 WIP。总控与对应 owner 的 PWF 已同步。下一主线仍是事实质量/产业关系 F05/W11、G4 和规模覆盖；28 个不足证据答案是研究内容待补，不再作为已有结果可见性的门禁。
