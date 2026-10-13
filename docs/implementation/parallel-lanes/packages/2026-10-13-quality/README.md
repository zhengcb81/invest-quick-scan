# 三个独立质量施工包

当前状态：2026-10-13用户已确认三个包全部派出，见[动态分派记录](dispatch-status.md)。下面编制时的未派发/目录不存在及manifest/validation仅为历史快照，不重复创建或分派。本批是既有计划的内容与验收支撑，不新增小节点审查门。

| 施工卡 | 交付的实际用途 | 唯一工作目录 |
| --- | --- | --- |
| [ROUTE-COVER-02](ROUTE-COVER-02.md) | 验证公司类型、行业、阶段、周期与困境模块是否选对；给出具体题库/路由改进提案 | C:/Users/郑曾波/Projects/iqs-route-coverage-lab |
| [CHAIN-CONTENT-02](CHAIN-CONTENT-02.md) | 把三家已选公司的产业链信息做成可核验的真实内容基准，支持以后按主题找公司 | C:/Users/郑曾波/Projects/iqs-chain-content-lab |
| [SCORE-ANCHOR-02](SCORE-ANCHOR-02.md) | 补齐通用24题的评分解释与证据要求，检验低谷、成长和不同会计口径能否公平比较 | C:/Users/郑曾波/Projects/iqs-score-anchor-lab |

三个新目录在编制时均不存在；这不是持续独占保证。每个 harness 开工重查目录归属，只有自己的新根可写。旧 MATRIX/FACT/FIN/PRIMARY 交付不返工；本批分别补“组合覆盖”“真实关系内容”“评分插值依据”，不另造路由器、查询器、财务计算器或公司数据库。

必读自身卡、[共同规则](common-rules.md)、[交付接口](integration-contract.md)、[输入锁](inputs.lock.json)、[范围清单](manifest.json)和同名 handoff 模板。只发送卡的绝对路径即可；卡链接了全部规则。输入快照位于本机 IQS 的 runs/parallel-quality-2026-10-13-01/inputs/iqs，跨机器须另行携带锁中原件，不能用浮动最新源替代。

总控继续负责 B01 的批准参数→admission→runner、真实实验、跨仓接入与发布。三包不写总控候选，不等待另两包，不自动关闭 G3/F05/金融准确性、生产 UI、一键启动或全池门。完成交接后总控按一个包级节点验收；候选资料及模板通过不等于上线。

准备验证：`C:/Miniconda/python.exe -B -X utf8 <本目录>/verify_preparation.py`。结果见 validation.json，仅检查文件锁、目录边界、链接及 handoff 模板，不代表三个产品测试通过。
