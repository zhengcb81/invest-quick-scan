# B01 下游兼容接续（2026-10-13，实施中）

本次继续 checkpoint46 的同一隔离候选 `runs/b01-engineering-2026-10-11-01`，未部署。PRIMARY 三包及 FIN 已验收交付不重做。不新增小节点审查门；以下发现合并到 B01 大节点回归。

## 独立只读审查

`b01_downstream_review` 审查现有候选，未写源仓、未联网或操作数据库：

- StockWiki 的 execution qualification、qualification、subject refresh、pool 四个内部消费者仍固定 query 2.0，遇到 Observation 1.2 会明确拒绝。内部选择新 2.6 方言；旧公共 2.0 仍按原 schema 拒绝新版，不静默丢行。
- StockQA execution inspection 将原件版本固定为 1.1；需支持具名 1.2，同时保留完整 SQL 重建、事前登记和物理请求/响应摘要验证。`durable-response-v1` 是正确来源标记，不需改名。
- IQS field assessment 的 `_bound` 直接使用旧 original validator。需显式新方言入口，复用 `_assess(... bound_original=...)`；不得另造资格判断引擎。pool 公共紧凑 wire 无需为内部原件版本升级。

## 实际整链测试

无密钥/禁网络/自有临时 SQLite 与固定 OS CLI，只有供应商 HTTP 回答被明确合成。不是 StockWiki 真实身份 golden，也不证明金融准确性。

- 四次准备运行分别暴露缺原 bundle producer、sandbox 原子硬链接权限、缺旧 CSV fixture、错误合成 citation 形状；原日志保留，均不计产品 RED。
- 原 fixture 精确补入同源 producer 与 `iso10383_sample.csv`（SHA256 `a4f5d6aa9941d91a7867e74cd98f9e83f47f7f12762c95bea3bcaf4dab4fadc4`）；atomic 发布未改，测试显式使用原生权限且仍受隔离 guard 约束。
- `vendor-full-chain-valid-mimo` PID23260，exit1，18.25秒：实际事前注册与回答 checkpoint 成功，封存明确失败 `invalid request_payload_sha256`。原因是同步/异步 client 仅在提供可选 thinking/token 参数时捕获请求 body 摘要。此次默认调用没有摘要，是有效产品 RED。
- 候选修复为所有搜索调用在 POST 前捕获最终 JSON body；不捏造旧回执，不改变历史 Observation 内容。上述三组下游修复仍在同一集中节点实施/验证。

当前软件测试与源仓部署分开。真实首轮 13 HTTP/26原生搜索/CNY1.268162、30题分母、4blocked、0评分/ACK0全部保持；金融、G3/F05/UI/一键及全池门不关闭。

## checkpoint48：候选集中验证结果

原测试准备和失败日志全部保留，未拼成一次全绿。实际结果：

| 批次 | 实际结果 | 范围/限度 |
|---|---|---|
| 新/旧公开整链首次集中 | PID73324：2P/2F | 两旧格式通过；两新格式负例的内部KeyError与测试预期ValueError不符，仍是拒绝，无坏数据入库 |
| 新版完整负例修正 | PID26600：2P | 实体/挂牌，缺PRE事务回滚、错work/hash、四个vendor sidecar字段伪造均拒绝 |
| 冻结profile选择接线 | PID54064：2P | 默认1.2工作捕获请求摘要，旧无绑定调用保持旧receipt外形；没有开启/关闭思考的隐式变更 |
| 客户端/原件封存/inspection | PID25492：244P/1deselected | 原受影响回归；Windows asyncio精确内部socketpair放行，其余网络仍禁。旧schema16不可变SQL仅复制件正常迁移 |
| 默认同步/异步＋真实junction | PID2676：5P | 四个新默认成功/失败回执单元例；junction用核定临时路径的原生mount-point API并清除，未开放任意shell |
| owner下游/qualification/pool | PID72664：72P/1F，PID16820：原失败选择器1P | 一个60k合成codec例缺既定IQS runtime环境，补环境续测；含新版固定CLI字段评估与原库保持控制 |
| pack与逻辑终态 | PID31104：69P/2F，PID65528：原两个fixture选择器2P | 实际部分成功原件/费用保持；旧schema16 fixture需移除新18 trigger，另原子进程显式env |
| v18 ledger/client扩大回归 | PID79188：372P/12F，PID29528：原12＋错误分类1，共13P | 旧schema3/4/6/7 fixture留18 trigger导致形状错；只在mutable legacy fixture移除，未放宽native schema验证 |
| 最终terminal/engine | PID25224：35P | 写锁等待期间过期会拒绝；真实lifecycle只结束明确解析失败，generic storage/lease问题仍恢复 |
| 实际partial最终状态 | PID35336：2P | 一物理请求：有效题result_ready，缺题failed，原费用/receipt不变，重新运行零发送；无authority的测试封存阻断/日志诊断不当完整成功 |
| CNY显式新方言 | PID58588 RED2F/4P；PID10428 GREEN49P | 原refresh-v1字节不变，只new1.1接受真实CNY及query2.6，拒未知币种/混旧wire |
| CNY公开preview→consent→admission/replay | PID61124：1P，100.46秒 | 合成consent，真实临时native库/OS CLI，API0，零attempt/预算预留，重复无新work；USD文件替换拒绝并恢复原字节 |
| 实际公开main→owner ACK→native执行核验→assessment | PID63468：1P/35deselected，177.41秒 | Observation1.2，原main恢复/引用无重封无新请求，撤owner许可拒绝；只execution_verified，screening/金融准确性false |

CNY公开链另实际复现了Q13 admission借用原store但缺schema17起的thread-local事务上下文（PID74768，exit1），候选只初始化该内存状态，不调用创建/迁移initializer。后续一次fixture路径超长错误（PID62012）保留；runner改成固定长度唯一短临时根，PID61124才作有效正例。

新逻辑终态用原failed状态和原work_event。schema18只为该事件表加禁止UPDATE/DELETE两个trigger，17先严格校验后迁移，不改旧数据；当前仅隔离副本。最新attempt/当前lease/原耐久response及model resolution核对，pack额外核membership/receipt/非uncertain和settled/completed费用。checkpoint/delivery、过期/旧epoch/发送不明或未结算均拒绝。没有把旧真实26条leased自动改成failed，也没有拿absence-of-answer判定崩溃请求无效。

一次大节点独立审查发现的无PRE旧兼容分支、明确member错误reason丢失、锁前now三项已分别直接修复并加入真实负例；不增加helper验收门。

部署仍未完成：同候选需最新源writer/HEAD/逐文件SHA核对、精确应用与源级接线验证。真实旧expired工作仍需原owner对账/重试决议，不自动恢复或换代。真实金融/G3/F05/生产门、原13HTTP/26搜索/CNY1.268162/0评分/ACK0保持。

## 2026-10-13 checkpoint49 — B01源码交付与正常本地提交

此前checkpoint47/48的“未源部署”是历史。本节点68个精确文件已部署：IQS20、StockQA32（含新schema的精确Git忽略例外）、StockWiki16。部署前逐文件及HEAD核对无目标并发漂移；原文件备份和实际交付SHA留在本机，当前68目标再次匹配。其他进程的2026-10-10 README不覆盖、不提交；生产数据库、名单、旧实验账本均未修改。

StockQA正常本地提交`21b2c5f9caa4db8adafb7bc74d69ce75aed4c9fe`；首次正常hook修正四个文件的混合换行而拒绝提交，保留日志后只重暂存同32文件，第二次black/isort/mypy/secret及其它正常hooks全通过。StockWiki正常本地提交`5b11f55909efdbd724fb07e1e7f298631c4200cb`，正常静态hook通过。独立源静态检查QA PID76912/exit0、SW PID34484/exit0；均未跳过检查。换行只改变raw bytes，原schema canonical SHA一致，候选镜像和交付摘要已同步，不把canonical相同声称为raw相同。

公开协议：Observation1.2/profile vendor-http-identity-v1；事前主体request1.2/binding1.1；query2.6/capabilities1.2；refresh显式1.1接受CNY、旧1.0继续USD；work store18。新旧整链、逻辑terminal、原件恢复与CNY admission的集中测试见[本节点报告](docs/implementation/reviews/B01/vendor-profile-downstream-2026-10-13.md)。同节点独审发现的缺PRE、typed reason、锁前clock已直接修复；最后源只读复核未发现这三处遗漏，不新增小审查门。

下一动作：只读核对原真实owner/work账本和当前公开恢复路径，保留13物理HTTP、26原生搜索、已settled CNY1.268162、30题分母、4旧blocked/26旧expired、0评分/ACK0。schema18升级需原账本备份及原生迁移；无答案的旧expired不能用新terminal强改，不补造事前记录或header ID。由原owner生成当前显式1.1 CNY quote/新的批准与admission后，才对固定IQS_01/02/04做pack3/32768→pack1真实小实验；旧approval不扩大、不重放one-shot控制器。

软件接线完成不等于答案准确：本轮API/付费搜索0，金融gold0，Financial/G3/F05/生产UI/一键/全池仍开放。PRIMARY/FIN已交付不重做。源码与本批公文只正常本地提交，尚未推远端；此前自动审批导出范围pending保持，私有日志/数据/golden/密钥不随公文发布。
