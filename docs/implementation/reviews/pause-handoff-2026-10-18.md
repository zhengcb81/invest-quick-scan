# 2026-10-18 用户要求暂停：续接交接

状态：按用户“手头做好了先暂停吧”收尾。已完成节点保持交付；下一节点保留隔离候选，不要求为了暂停而赶做生产激活，也不以候选测试冒称整包验收通过。

## 已完成并保留的交付

- IQS `master`：`a05dc8b7e56520ff071a951363d11dcce1dcb3bd`，暂停收尾前与 `origin/master` 一致。真实 CATL 缓存恢复、独立审查、金融一致性限制和薄证据已交付。
- StockQA `master`：`c910ed9676fcc6121bad8658d1c630e5668066f6`，与 `origin/master` 一致，tracked 工作树干净。
- Runtime Lab：`f8e251f`，本地提交，原仓没有 remote，不新建远端。
- StockWiki：`809b501`，本地提交，原仓没有 remote，tracked 工作树干净。
- 原真实两题经新进程恢复为 Company 研究槽 2/2 completed，恢复 75.0352 秒、新增模型 HTTP 0、原 native 响应重放一次。原冷请求 305.8697 秒，公开价估算 US$0.014537，不是现金账单。
- 两答仍为 `insufficient_evidence / partial / score=null`。4 项唯一事实受参考来源支持，主观分数与完整评分构念 gold 均为 0/2；`CATL-FIN-01` 措辞限制保留。不得据此宣布整体准确率、评分准入、缓存经济性或策略胜出。
- 工程最终审查 `actual-recovery-final.json`、金融最终记录 `content-verdict.final.json` 和原失败/partial 历史均保留；不重跑已完成付费样本。

## 当前未交付节点

目标是沿原 StockQA work-decision / checkpoint / C06 / outbox 和 StockWiki observation-import / ACK 发布已保存研究结果。显式默认关闭的 `publish_saved_research` 与 research-only checkpoint 候选，不产生 verified-search 证明，不续旧 lease、不改原答案、不清未决费用。

候选仅在：

- `runs/shared-engine-production-2026-10-18/saved-research-publication-candidate/`：跨仓产品 overlay、设计、公开接口、隔离测试及暂停交接。
- `runs/shared-engine-production-2026-10-18/saved-research-publication-controller-candidate/`：`publication_delivery.py`、13 项工程元数据测试、准备说明。真实发布 driver 尚未实现，完整 controller CAS / runtime inventory / 整包 final / delivery 也尚未冻结。
- `runs/shared-engine-production-2026-10-18/saved-research-publication-independent-review/preparation-notes.md`：架构预审，仅 preparation，不是产品最终签收。

这些目录属于本机续接现场，未把原始答案、完整上下文、库副本、配置授权或密钥归档到 Git。暂停清单只记录候选源文件和说明的相对路径及 SHA256，不能当生产部署证明。

作者已写 `handoff-pause.md` 和 18 文件的 `wip-files.json` 并停止，状态 `paused_incomplete_not_ready_for_review_or_application`。最后一组隔离测试 `pause01.xml` 为 5 passed / 7.244 秒，包括原 schema24 只读派生且字节不变；root 工程元数据另为 13 passed，二者不相加作为整节点通过率。公开 E2E 两次失败仍保留，正常格式/类型与旧行为回归、最终 CAS、整包独审、真实发布尚未完成。

## 已知缺口与应保留的拒绝

1. schema 24 升 25 后，只读 reader 不能因 `SCHEMA_VERSION` 常量变化而漏掉 24。候选显式保留 24；恢复时核对只读 derive 在未迁移的 24 副本上成功且字节不变。不能先写真库绕开只读准入，也不能全局放松付费 refresh 的 writer schema 限制。
2. 当前公开链 `public01/public02` 没有通过：原 StockWiki store-ID 与数据库路径绑定，复制真实 namespace 到另一路径后，原 source receipt 应被拒绝。保留拒绝；禁止改 receipt / store-ID 伪造正例。下次公开正例须由原 native 软件在独立隔离 namespace 新建 synthetic pack；真实 102 行副本仅用于迁移、原内容与原行保留测试。
3. 原标准答案校验禁止非评分答案携带指标，但这两份原答包含部分已知财务数字。候选已为显式研究类型局部实现原数字、原单位、原理由与空分共存，并经聚焦测试覆盖；仍待完整公开链与整包验收，旧评分和来源/日期规则不能放松。下次先核已有实现，不重复施工。
4. 真实 StockQA 两条 CATL work 仍为 `uncertain`、无有效 lease。Company 2/2 不等于 native checkpoint、正式入库、ACK 或 delivered。真实 schema 尚未迁移到 25，也未安装/激活新的 saved-research publisher capability。
5. 总 budget 102（99 settled、2 response_unpriced、1 outcome_uncertain），原 101 行及原 12 work / 12 attempt 的保持证据已完成；下一节点不得清旧三笔未决、重新发模型、凭消费者提供的字典授予权限或绕过原 owner。

## 下次唯一续接顺序

1. 先读本文件、PWF 最新暂停段和作者 `handoff-pause.md`；检查原仓新 HEAD / 工作树与候选 base SHA，避免覆盖其他进程。
2. 完成同一出版节点的源候选和公开隔离正反例；实现真实 driver，复用原 fixed owner 的 fresh preview / confirm / inspect / apply，再经原 outbox、公开 import、ACK。不得另建任务回执、权限服务或账本。
3. 一个大节点集中做 unit / integration / public CLI / 隔离 E2E 与真正不同 agent 的整包审查；发现问题修根因，不增加逐 helper 审查门。未通过前不应用生产源和真库。
4. 审查通过后精确应用，正常 hooks、交付闭包核对，再做原真实 safe 的零 HTTP 非评分出版与幂等重放。答案逐对象与原答一致，financial sidecar 保留，StockWiki 仅 `review_pending / screening`；评分/verified-search 资格保持未授予。
5. 保存实际前后账本和原行比较、时间与来源，更新 PWF / 规范 / 实验记录，提交推送精确安全文件。不得把代码准备、进程 exit0 或合成正例当真实链已完成。

## 并行与文件所有权

用户已发出 `RELEASE-DIFF-10`、`SUMMARY-LOSS-10`、`RELATION-DELTA-10`，对应三个 Lab 继续按外部活动 writer 对待；不接管、不索引、不修改，等待正式交接。此次暂停不宣称这些包完成。

IQS `docs/implementation/parallel-lanes/packages/2026-10-10/README.md` 的他人 4 行 tracked 改动保持，未加入总控提交。其他大量 pre-existing untracked 文件不批量暂存、删除或清理。

测试没有下载公司文档。先前精确删除自有隔离测试目录被自动审批在执行前拒绝，原因 `blocked by policy`；现场保留，未换方法绕过。额外测试目录也仍隔离保留，不能写成环境完全清空。
