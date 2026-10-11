# B01：原生 Pro 完整30题首轮不适合直接作为默认配置

2026-10-11，在独占真实Alphabet owner克隆中，用原StockQA公开main、完整30题、实际mimo-v2.6-pro、thinking开启、题包上限3、输出上限8192执行。证券题单独分包；原账本、正式题义/ID/截止日与身份材料保留。没有下载公司文档、保存网页正文或思考内容，也没有修改生产数据库。

本轮结论只适用于这个样本与配置：请求和原生搜索能够运行，但可用评分率为0，不能把该配置作为已验证的默认快扫方案，更不能因此判定公司质量差或排除股票。

| 指标 | 原真实终态 |
| --- | --- |
| 完整题数 / 实际模型HTTP | 30 / 13 |
| 实际原生搜索 | 26（每次HTTP实际2次） |
| HTTP完成状态 | 6 length；7 completed |
| 题级结果 | 15 missing；9 invalid；2检查点拒绝；4合法insufficient_evidence |
| 可用评分 / 已接受检查点 | 0 / 4（均null分） |
| 正式结果库投递 / ACK | 0 / 0；4待投递项blocked |
| 模型输入 / 输出token | 120432 / 81811 |
| 其中思考输出token | 70488（只计数量，不读取内容） |
| 缓存命中 / 写入token | 0 / 0 |
| 项目账本费用 | CNY1.268162：token0.852162＋搜索0.416 |
| 预算状态 | 13全settled；held、inflight均0 |
| 原main时长 / 退出码 | 23分51.80秒 / 1（保存部分结果、26题失败） |

金额来自实际usage与本轮冻结费率的逐包计算，独立公式与原账本一致；未核供应商账户账单。成本以13次物理请求计算，不乘题包成员数；失败和思考费用均计入。四个unknown不能计作四个正确金融结论，无法形成评分准确率的分母。

## 实际发现

输出预算确实不够用：第一包8192输出token中8191为思考，最终答案未完成。MiMo的max_completion_tokens同时约束思考和可见输出；开启思考时增加上限是正式支持的选项，不应通过关闭思考伪造模型能力对照。[官方API说明](https://mimo.mi.com/docs/zh-CN/api/chat/openai-api)

原生搜索执行不等于证据有效。三道已保存unknown对应的检索引用实际来自Microsoft、Morgan Stanley和Lockheed Martin，没有Alphabet官方来源；模型保守不评分是正确行为。另一道只有Alphabet Q1来源，仍未提供足够指标。已有官方primary参考为每题列证据及反证，expected_score均null，尚不是人工金融评分gold。

校验拦住了不合格输出：IQS_21有parser评分5日志，但标准内容一致性校验失败；IQS_22为不可评分状态却带metrics。最终均error/null、无检查点。进度打印可能先显示下一题，不能用该打印把拒绝归错qid；归属由原收执与运行日志时间核对。供应商最终原正文未耐久留存，不能猜IQS_21是哪一个字段冲突，更不能把它记为成功评分。

还有三个执行接续缺口，必须在原B01大节点一次集中处理：

1. 已收到响应、费用已结算但答案不可用的26项仍leased。现行过期恢复会保守归uncertain；需要以原attempt/receipt/physical终态作durable逻辑对账，不能直接重新POST，也不能拿支付记录充当答案。
2. 四个合法unknown无法封存。以原checkpoint/body/schema内存复现，唯一schema错误是execution.request_id实际为None；MiMo未返vendor header request ID。必须保留request_id与真实response_id的区别，通过具名向后兼容接口解决；不填response_id或自造UUID冒充request_id，不改旧冻结结果或伪造ACK。
3. 原refresh quote和旧OwnerState/Preview两schema为USD-only，实际本轮账本是CNY；并且没有durable retry时间/显式对照重问决议。需要新能力兼容旧USD、用原币种和原账本，不能造汇率或用新空账本绕过。

## 下一轮实操顺序

保留这轮30题基线和全部成本；先完成上述已知响应/投递/刷新接续，做受影响TDD与一次集中回归，正常源交付。使用原公开owner preview、已授权operator真实TTY确认、Q13 admission、原main和同一原账本，不另造客户端/预算引擎。

然后固定原IQS_01/02/04、模型、题义、anchors、截止日、prompt及搜索参数：先仅将max输出提高到32768做pack3，再以相同32768做pack1。这是三题对照，不是把首轮30题分母缩成3。原13次之后至少新增4物理请求；原预算支持同policy_id更新policy_version/cap并保留旧累计，按真实owner quote预留足够余量。历史350模型/200搜索与用户超范围继续授权保持，未知成本仍保留预留并暂停。

再独立比较可信SEC/官方IR来源导航和每题检索计划、关键词数2→3、其他已授权模型与可控外部搜索。静态发现三题文本约86%是重复schema，需由原导出器明确semantic text与共享输出合同，保留原题义/版本，不用运行时字符串截断删题。每次只改变明确变量，记录真实模型、搜索、最终结果、期间/来源、缓存、总时间与费用；先看事实正确性与错issuer污染，再看经济性和速度。外部context题包必须每题有proof，不能复制题1证明给整包。

## 软件交付、隔离与边界

StockQA真实BIND兼容两文件已正常提交推送0a0493ecc4bcc01cc7001ea7a47b4c526fff1d07，既有BND也继续支持；原绑定、身份、DDL未改。新增18语义边界在扩展同文件批中通过；原125P/12F保留，旧11fixture故障在原基线复现，修正局部fixture及隔离副本缺旧harness后仅12失败选择器12P，正常hooks通过，不称全仓一次全绿。

原失败启动两次无HTTP，日志不抹。两个已结束测试/发布临时根精确清理2860文件/385目录、留53必要证据；当前live/owner/账本继续保留用于合法接续。生产4DB与旧clone/冻结输入总14保护项raw SHA均未变；外部Labs及他人README不碰。全部真实过程与原件只在本机intake/B01/current-public-chain-2026-10-11/native-live-pro-01留档，不随公文发布密钥、数据库、真实golden、vendor原响应或思考。

MATRIX/LOAD的R1和FACT/EVID/IDENT验收状态见PWF，不因本实验改变。G3/F05、金融准确性、facts、UI、一键启动及全池尚未完成；本轮不是生产上线验收，也不新增helper审查门。
