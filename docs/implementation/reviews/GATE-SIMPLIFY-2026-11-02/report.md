# 过度门禁清理（2026-11-02）

本节点已完成：相关代码修复、针对性回归、集中非作者审查通过，原8766 UI的真实历史gen7响应已零API恢复、保存、补封并入库，取得原StockWiki ACK。没有新增审批步骤或资格凭证。本报告是阶段说明，不参与运行时授权。

## 确实发生过正常结果被误拒

历史测试曾暴露URL跟踪参数、已付恢复依赖当前配置/有效期等问题。本次再次沿新发送、已付恢复、结果保存、读取导出、UI接续和逐项入库检查，并通过原真实响应找到了更多漏点。

11/01已付gen7原先因未登记指标名称未保存CP；本轮实际UI复验又先后发现单位文字误判及旧singleton绑定编码遗漏。这些都是软件误拒，不能当成模型未回答，也不能因此重发收费请求。原始safe、响应哈希、分数和模型标记保持；该回答仍有分红范围、利润归属口径及日期状态等金融限制，未签全答金融正确。

## 已移除或解耦的限制

| 原限制 | 最终行为 |
|---|---|
| 已付保存重新读取今天的模型/key/价格/预算/研究时效/route anchor | 原公开runner前置只读恢复，用原响应元数据构造无key、无endpoint的原SDK对象；原任务和原响应继续绑定 |
| 整批题必须都有响应 | 保留原完整题数，保存已答部分，列出未问/未知部分，不伪造回执或补问 |
| schema/指标表整体hash静态白名单 | 答案schema/指标表hash作为原资源溯源，保留完整context原hash、真实结构、主体、题义和执行profile验证 |
| 诊断开关关闭或旧scratch清理后不能恢复/导入 | 原捕获文件按原位置读取；临时验证使用系统自清TEMP，不要求旧scratch存在 |
| 补封/导出/任务刷新/本地归档要求新预算和整发送配置相等 | 移除无关发送依赖；任务读取和导出固定原confirmation精确work IDs，不用latest generation替代 |
| 交付绑定解释器或源码路径 | 核真实receiver store_id及原包；旧不透明记录不能证明目标时保留只读和既有明确导入动作 |
| 单条损坏历史引用或混合拒收阻塞其他结果 | 保留损坏记录及错误；其他独立任务可读，StockWiki沿原逐项ACK接收正常项目 |
| 普通analysis/监管Authorization/Bearer shares等业务词被当私有内容 | 按真实结构化私有字段、显式标签和凭据形态检测 |
| 未登记指标、同源多短摘、多期间指标整答拒绝 | 原指标保留并标未映射，不参与标准聚合；逐指标用自身期间，同一文档允许不同摘录 |
| 同值重复、完整JSON围栏、无害解释字段、800/5000字展示限制 | 兼容可见答案并完整保留理由，沿既有总传输安全界限；真实重复冲突仍拒绝 |
| source.unit与metric.unit_detail必须文字相同 | 删除无证文字等值门；thousand/千元人民币及合法派生比率可用，不建单位别名表、转换器或自动摘数 |
| 自审用总览年份核各期指标，或用current/trailing推断GAAP口径 | 自审与原校验按指标自身期间对齐；时间basis不冒充会计口径 |
| 原始未发送任务必须先claim/release才能证明未发 | epoch0且无attempt/intent的pending可只读识别；真正POST仍走原claim和预算 |
| singleton恢复重复手写旧binding哈希，遗漏provided_context | 两读取处共用原research_intent纯codec；旧无context哈希不变，新context完整入hash，物理证明全部保留 |

集中独审修复了两个真实引用漏洞：换alias绕过已知来源冲突，以及同原ID异URL被最后一项覆盖。完全同值重复允许，真实冲突仍拒绝。不同单位详情在比较阶段仍不能未经对齐就横比，不把保存兼容当自动换算正确。

## 保留的实质边界

新POST预算预留、账户访问及委托撤销、原主体/题意/原工作/响应绑定、真正typed unit/币种/期间/分数冲突、未知请求不重发、接收库身份和逐条ACK继续有效。原字段数据不足时不编造分数或金融核实结论。

自动审批拒绝了取消StockWiki当前账户与委托撤销检查，理由是会持续放宽访问控制；该修改未执行。采用保留访问边界、去掉今天预算回读的安全替代，没有向用户增加审批操作。

## 实际验证

不跑小时全套。相关组有重叠，不能累加为总通过数；测试使用自有TEMP并清理，剥离密钥。原组件长E2E额外禁止网络，只替换vendor wire；普通纯函数短测不冒称都装了socket拦截。

- root Store/恢复/语义边界260P；后续部分导出99P；正常长理由保存及模型输出43P。
- 内容最终IQS40P+5subtests、QA295P、Company106P/1平台junction skip；引用与registry尾修54P。
- Dashboard三个最终整文件214P/133.38秒，owner尾测3P，UI完整DOM57P/18.03秒；非作者终审15P/16.42秒。
- StockWiki原确认/预算正反例101P；新公开只读action seam35P，非作者核源通过。
- 冷公开CLI原owner/SDK/Runner/SQLite E2E：1P/298.03秒；paid1/未问1，删当前model/budget后两个全新进程重复恢复，原CP/响应不变、0新增HTTP、未问题仍未完成，隔离副本清理。
- 真实响应暴露的单位/自审尾修118P；非作者89P，确认旧journal/snapshot findings沿原记录回放，不因新规则重算后拒历史。
- singleton共享codec三模块54P/48.25秒；非作者核旧缺列/NULL旧hash固定值、dict/SQLite.Row一致及8类篡改拒绝。保留member、settled budget、receipt anchor、PRE dispatch和fencing。
- StockQA正常提交hooks含全src mypy、格式、密钥扫描均通过，没有skip。

## 原UI真实历史响应闭环

仅操作原`run-5a03133643e34e60b69d6b9b311b46c0`、原gen7/work`WORK_ef7cfb7bd41740ab95e2d31af6c78548`。前两次本轮seal分别暴露单位与旧codec问题，均0API且未保存CP；最后第6次原launch成功exit0，CP `CHECKPOINT_1c5c5d9766b34ddcab8317ac34256b31`，原score8、MiMo Pro及响应时间`2026-11-01T23:44:40.990609Z`保持。

原UI交付job `deliveryjob_03aeb32cc6f07b1525d3a147fb893cc0`完成，原work为delivered，StockWiki于`2026-11-02T11:00:20Z`回accepted ACK `ack_fd86eacd8b792b505a582f13`。新观察`obs_7a62aa609e05f43578b03f4627b4fa0368f1d0250dbd3f91318a7cb78fc0687d`与旧gen6观察均可在原公司详情公开接口找到；结果总览保留多代歧义，不伪合成一个评分。

最终实际对账：87HTTP、2053896micros（US$2.053896）、0在途/0未结，与本轮前相同；原响应行hash及普通dashboard配置字节hash相同。60包保留，普通pack2/thinking/max32768、shared=null及原policy11保持，doctor ready。原safe/旧export保留；没有下载公司文档。私有运行证据位于`runs/qa-public-seams-2026-11-02/`，不随报告发布回答正文或数据库。原真实UI补验还覆盖了带provided context的单题保存；它不能被无短证据的合成例代替。

本机复验冷CLI的既有隔离包装器：`C:/Miniconda/python.exe -B -X utf8 runs/qa-public-seams-2026-11-02/run_paid_cold.py paid-partial-cold-native-current`；它复制五组件到自有TEMP，剥离密钥并装原网络/写入guard，运行公开测试`tests/test_paid_partial_cold_native_e2e.py::test_paid_partial_cold_cli_without_current_sending_configuration`后清理。包装器是本机编排；仓内公开测试保留，普通pytest不冒充已构造隔离runtime。不要把生产目录伪填为`IQS_C06_OWN`。

## 提交与边界

IQS实现`79b94ce`；StockQA `6eecce7`、`e2850bd`已推原origin/master；Company `937454b`、`360c7df`，StockWiki `e5a1be6`，UI `fa7ceb6`本地原分支提交（三仓无远端）。本报告与PWF/交接随本次文档收尾提交，IQS最终origin状态以git为准。

本节点工程目标已完成；金融回答准确性、全池覆盖和事实/研究消费者等剩余主线按根计划推进，不能由本次工程通过代签。
