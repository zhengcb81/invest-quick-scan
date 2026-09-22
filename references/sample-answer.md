# 样板回答与比较视图（全部虚构）

以下只展示统一输出，不是实际公司研究或实际模型测评。机器可重放输入与完整结果见[standard-output.json](../examples/standard-output.json)。模型、公司、请求、搜索回执与数值全部为离线fixture，来源尚未核验。

| 必需字段 | 示例 |
|---|---|
| 公司/作用层 | EXAMPLE_ENTITY_A；entity |
| 扫描批次 | EXAMPLE_SCAN_A |
| 问题/字段 | IQS_01 / score.iqs_01 |
| 截止日 / 信息日期 | 2026-09-22 / 2026-09-01 |
| 开始 / 回答时间 | 2026-09-22 09:00:00 UTC / 09:01:00 UTC |
| 提供商 / 请求模型 / 实际模型 | EXAMPLE_PROVIDER / EXAMPLE_MODEL_A / EXAMPLE_MODEL_A |
| 版本 / 方法 | rubric 1.0.0；固定核心方法及题面指纹 |
| 状态 / 原始分数 / 置信度 | scored / 8 / medium；证据仍unreviewed |
| 结论 | 核心客户持续采购，但客户集中仍需关注。 |
| 标准指标 | operating.repeat_purchase_share=82 percent；2026H1；不是收入留存率 |
| 反证/缺口 | 尚缺分客户采购历史和客户收入占比。 |
| 下次观察 | 跟踪复购及供货状态。 |
| 来源 | e1，虚构example.invalid链接，claim逐项绑定 |

非评分客户题使用同一外层身份/时间/模型字段，但`response_kind=fact`、`status=answered`、`score=null`。客户行固定包含名称、关系`sells_to`、角色`customer`、分部、商业化阶段、有效期和来源e1；未披露收入占比列missing_fields，coverage=partial。设备供应方改用`buys_equipment_from`，使用设备用`uses_equipment`，两种关系不可混同。

| 比较方式 | 左侧 | 右侧 | 示例结果 |
|---|---|---|---|
| 横向公司 | 甲，模型A，8分 | 乙，模型A，8分 | 同字段/口径对照；差0 |
| 同公司时间 | 9月20日扫描，模型A，7分 | 9月22日扫描，模型A，8分 | 保留两个观察和原时间；差+1不自动证明经营改善 |
| 同公司模型 | 模型A，8分 | 模型B，6分 | 显式对照组，差-2；不平均成7分或只取高分 |

这些差值仅说明结构满足比较条件，不能替代来源审核。模型/题义/期间不匹配时仍并排展示原答，但差值留空并说明原因。只有新观察才能产生新回答时间；新扫描复用旧回答时引用旧ID，不给旧分数换新时间戳。
