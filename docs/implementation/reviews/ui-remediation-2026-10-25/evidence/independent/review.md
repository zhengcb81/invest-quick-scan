# UI整改整节点独立终审

审查者：独立 agent `/root/review_ui_whole`；2026-10-25。范围为两份原审查的 UX-01–10 / VD-01–12、冻结整改源码和原 owner 边界。本审查不是实现 agent 自述的汇总；已亲自读取具体实现和原服务协议，运行真实 ESM 及原 StockWiki 隔离集成测试。浏览器操作由总控承担，本文不把他人的截图称为本审查亲自浏览。

最终状态：**passed，open_findings=[]**。发现的5项问题（含修复回归）已直接根修，并以最终冻结源码复核。`final.json` 绑定UI 17个文件与总控后端4个文件的真实字节SHA256；这是一轮UI工程节点验收，不授予金融或全池完成资格。

## 独立发现及反例

1. **IR-01 / P2：签收完成后推荐重复开扫。** 原 `dashboard_delivery_jobs.py` 将所选范围全部完成的交付标为 `state=completed`，不是 `delivered`。初次整改的 `operationRecommendation` 没处理该真实终态，原登记仍在时回到“预览后明确开始”。独立 ESM 红灯 `independent-terminal-flow`。应进入结果查看，继续说明所选范围不等于全公司/金融合格；在途、未知、部分交付仍优先处理。
2. **IR-02 / P2：保存中继续编辑会谎报已保存。** 发出保存模型 A 后，等待 HTTP 的期间仍可改为 B。原回调对 A 成功却将 B 编辑状态标为已保存。连接表单同源。独立红灯 `independent-settings-inflight`。应在保存中锁定该区全部编辑控件，或按提交版本与当前草稿区别保存状态；不得删除原 CAS。
3. **IR-03 / P2：清空刚新增的可选路径仍保留隐藏旧值。** `connectionFields` 对原先不存在的字段跳过空串回调，造成用户清空输入后 outgoing JSON 仍保留前值。独立红灯 `independent-clear-new-field`。清除 prepare 可选路径须删除键，因原 schema 不接受存在但空的路径；保留相邻未知字段。
4. **IR-04 / P2：可搜索公司 listbox 被全局36px高度压扁。** 独立源码发现 `<select size=5>` 与固定高度冲突，总控真实浏览器随后实测 height≈36px、scrollHeight≈4018px。须修 `[size]`/实体选择器高度，使真实候选可见；不得靠搜索自动替用户选择唯一实体。
5. **IR-05 / P2：首次修清空逻辑范围过大，根路径被默认重新连接。** 修IR-03后对所有空字段删除键，使清空显式工作区目录时原 `validate_config` 又从 `defaults(root)` 填回默认库。只允许prepare可选字段空值删键；根路径保留明确空串，必填名单ID/标签也交原validator拒绝，不能静默套默认。第二次独立红灯 `independent-clear-root-path` 已保留在 `negative-results-root-clear-before-fix.json`。

初次失败原样保留 `negative-results-before-fix.json`，复核脚本 `review_negative.py` 不调用真实网络或模型。绿灯不能替换红灯历史。

闭合情况：IR-01以真实completed DTO及process_exited/旧launcher running负例通过；IR-02锁定普通字段、增删/顺位按钮和高级JSON，并额外比较提交快照，保留原CAS；IR-03/05仅删除可选prepare空字段，根字段保留明确空值交原validator处理，未知相邻字段保留；IR-04最终CSS给size列表合理高度，总控真实浏览器复测约148px。最终独立6个边界/完整返回场景全部通过。

## 原发现逐项核对

| 原ID | 核查的实质变化与保留边界 |
|---|---|
| UX-01 | 数据说明从同源实际 status 读取原库/执行器，断开不冒称空库；静态构建与显式写 owner 的边界分开，旧全站绝对只读描述已删除。 |
| UX-02 | 后端只按原 entity_id 调 get_entity；缺身份保留名称未知，ID冲突明确拒绝。前端显示原名称/挂牌、搜索50条分页、行选择仍须预览变更。 |
| UX-03 | 连接、模型顺位、原provider引用、额度、预算使用字段表单；高级JSON保留；保存沿用原校验/CAS、不派发。IR-02/03/05已用边界反例闭合。合法原部署仍为真实前置，不能捏造授权。 |
| UX-04 | 三阶段及当前建议、旧单包与手工导入折叠；原allowed_actions仍决定动作。IR-01真实终态反例已闭合。 |
| UX-05 | 名称/代码检索、保持同名多个实体、原ID显式选择、原名单新增项可补入选择器。IR-04实际候选列表高度已复测。 |
| UX-06 | 正式coverage字段保留原field_id，旁边关联题义；旧草稿候选按完整评分题库派生，当前题义只是历史未绑定记录的参考。 |
| UX-07 | 一条历史只展示一条；多条以唯一observation_id选择，重复/缺ID不安全组成对照；无差分或自动可比资格。 |
| UX-08 | 详情携带安全结果返回路由，查询/条件/视图/offset/同一snapshot_token保留；原快照过期不被前端伪造恢复。 |
| UX-09 | 主表仅本次条件及原三态结果；全模块诊断折叠；本次满足数与已评分题数分列；筛选算法没有改写。 |
| UX-10 | 原公开coverage与runtime生成正式记录统计；缺库为未知且不建库；不借草稿12次运行冒称正式已扫或金融合格。 |
| VD-01 | textarea独立auto/min-height，原JSON可展开；普通字段表单及保存提示。IR-02/03/05已闭合。 |
| VD-02 | 单一dialog焦点边界、背景inert、Tab循环、Escape及题号焦点返回；复制有成功/失败反馈。 |
| VD-03 | 模块/题号/矩阵列原生链接，筛选稳定label，原路由保留，不用普通容器tabindex伪造控件。 |
| VD-04 | 收缩grid、末尾断点、局部宽表滚动；真实375/768/1280浏览器接受范围由总控留证，不冒称读屏/200%缩放认证。 |
| VD-05 | 五个主工作区和二级导航涵盖全部旧路由；子路由保持所属栏目，高度收敛，数据源仍显示。 |
| VD-06 | 三阶段、当前推荐、未知不得一键重发；IR-01真实终态反例已通过。 |
| VD-07 | 单一statusDescriptor/statusNotice映射和色彩+文字；未知码原样保留到诊断，不擅自解释为成功。 |
| VD-08 | 研究正文卡片、原文显示截断而非LLM重写；完整理由/来源/原记录仍可读；UTC日期/模型不拆词；资格缺口在主行。 |
| VD-09 | 默认基础三模块，中文列名，说明折叠；逐格原依据保留，48列可切，48px行高与虚拟化匹配，键盘可到末行。 |
| VD-10 | 主栏切换标题焦点/滚动，列表返回保留过滤与滚动，抽屉query不跳背景；skip-to-main为真实焦点动作。 |
| VD-11 | 与UX-07相同，只有一条不生成两次独立支持的错觉。 |
| VD-12 | 拆出纯展示core、组件/forms、dialog/navigation；不迁框架；generation与离页poll清理、同源API及allowed_actions边界保留。 |

## 独立测试和环境

- UI三份定向文件：39 passed，73.52秒；`frontend-tests.xml`。这些原回归通过仍未发现IR-01–03，故另外设计红灯反例，不将自报通过当成终审。
- 后端8个关键反例/原owner隔离集成：8 passed / 32 deselected，11.85秒；`backend-tests.xml`。覆盖精确身份联结、无写入、原记录统计、缺库未知、跨ID拒绝、畸形统计拒绝、provider仅安全元数据。
- 实际临时数据库都在自有短路径 IQS/runs/urv，测试后核绝对路径边界后完整删除；XML保留。没有生产DB、真实设置、名单或预算写入，没有收费API、财报下载或源码副本。
- 最终冻结源码再次运行三份UI定向文件：**43 passed，10.87秒**，`final-frontend-tests.xml`；独立6个边界/返回场景全部通过，`negative-results.json`。后端8项源码未再变化，原结果继续有效。最终21文件SHA256见 `final.json`，闭合缺陷与原红灯仍可核对。
- 读过总控 `browser-notes.md` / `browser-verification.json`：实际正式记录覆盖1/214、同名身份分开、唯一历史只一份、原快照返回、临时原策略保存及CAS拒绝；375/768固定同源iframe仅按真实可观测范围记证，不冒称child scrollWidth/物理手机/读屏/缩放认证。实际付费运行和金融事实不属于这轮UI工程节点的准入结论。
