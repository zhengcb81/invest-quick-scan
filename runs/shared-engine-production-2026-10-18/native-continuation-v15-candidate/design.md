# 原通用续行1.5：实施边界（设计，尚未启用）

沿用 ../post-smoke-authority-review/recommendation.md 的实际只读阻断证据。这是原主线的一个完整跨仓能力切片，不另设逐函数审查；先收口批量claim节点，再实施和集中验收。

## 复用与兼容

在原 StockQA quick_scan_owner_budget_continuation 与原 StockWiki 固定namespace权限/quote/委托确认、StockQA admission/SDK 路径加显式新方言。旧1.0–1.4及Task1/2/3全部原正反例保持；不改已有决策、旧cell、旧receipt，不新建费用库/权限服务/调度器。schema24原cell表可继续保存新版本完整control JSON与原work关联，先确认无需新表再改，禁止为已能表达的信息做迁移。

## 通用保留暴露

新快照只读投影原账本全部当前阻断暴露，列表须有界、唯一且不遗漏。逐条派生其budget-only/native single/native pack来源、原policy/row/预约/NULL、物理运输结果、原members/intent/request/receipt哈希及safe-visible是否存在。不能由调用者写not_sent/invalid/disjoint/settled或用缺失字段制造这些结论。本次三笔仅为原数据测试样本，不在新协议硬编码“三笔”或“第三笔”。真正的transport unknown、已收到但无可用输出、现金未知分开。

当前owner明确接受一个未来独立action的保留风险，只例外原reconciliation pause；所有旧累计请求/预约/现金未知/inflight及cost/request/route/group/global硬上限原样计入。旧native members不得被新profile/工单代次/任务名接管重发。快照改变或出现未批准阻断项时，后续新POST拒绝；已经安全落盘的已知回答可在权限仍有效时走原只读恢复，不能为了读取而重发或结清未知费用。

## 已有profile接线

第一交付只接受原 company-scan-task/profile1.0 的一个subject、一个真实native兼容包（1–12原题），显式module_packs、0新搜索、原合格route与思考/输出caps。物理quote按这个真实单包计1，生产Task3不改名。默认不自动推广为全池/搜索/多轮资格。

execution_profile仅含原题绑定/日期/route/资源/pack规则与native group hash，可由原 build_scan_profile 在准入前纯计算；原 group key 实际为entity/company metadata/scope/scope_id/perimeter，不含随机work或批准ID。不能造假owner对象来提前调用受控工厂。请求绑定完整profile哈希；原真实工厂在admission后重算并比较，实际POST再校验原成员和controls，避免审批与profile形成循环。

完整profile hash只防篡改；另列版本化语义投影：subject+原题面/模块绑定+实际cutoff+包策略/成员+route/model+思考输出搜索控制+显式replicate。run/cohort/task/work/generation ID、opaque profile hash不使同一比较自动变新；真实新cutoff和显式replicate必须有新原生owner scope。

## 首个实际小样本

另一个真实canonical身份公司、2个原题、1包，使用同S1原101账/三笔未决和原预算。保持旧Alphabet12不动，不解锁旧工作、不将预约当已付现金。原公开权限→quote→rc2→admission→原SDK；safe response后中断，新进程无key且禁网络恢复0POST。真实模型失败则留原费用/安全诊断，不自动发第二次。金融正确性、原数值/引用支持、结构完整性、费用与纯网络/端到端速度各自报告，不把工程绿当金融合格。

## 充分测试：只在整个节点收口

1. 原101行真实库只读backup隔离夹具，全部旧行/三种暴露保留，同原public软件2题一包与safe后中断/0POST恢复；合成身份或wire必须明确标合成。
2. 漏项/改来源/跨原intent成员/撤销权限等统一0POST，hash或policy JSON不能授权限。
3. 未知费用继续NULL/预约、未知transport原inflight保留，原成本/请求/并发硬cap依旧拒绝超额。
4. 换名换profile/代次不能重发旧比较，真实新cutoff/明确replicate仅经新批准放行。
5. 旧1.0–1.4协议/冻结Task/profile的正反例与hash保持；新能力不得反向放宽1.4。

完工前由真正不同agent整包审查，修尽有效问题后才应用原源；正常各仓测试/hooks、精确路径提交、已有remote推送及PWF/规范同步。授权沿用用户既有全部后续权限，不再次提问。
