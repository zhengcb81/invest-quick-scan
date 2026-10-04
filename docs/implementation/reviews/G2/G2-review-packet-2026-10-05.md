# G2 审查包 — 评分闭环与校准门槛（2026-10-05）

任务：IQS tasks.json **G2**（stage M2, owner iqs, kind review）。本包为审查者输入；allowed_changes 仅 `docs/implementation/reviews/G2/`。审查须逐项产出 case 证据与问题结论（test_binding：不得只复述实现者摘要）。

## 1. 审查范围与不在范围
- **在范围**：G2 三步——①复算固定样本的规则边界/覆盖分母、抽查模型与类型比较 ②大池维护不依赖高分、低谷观察独立、未知不伪装中等 ③校准门槛及全部阻塞问题关闭，给出"允许进入 200 家运行验证"的裁决。
- **不在范围**：B01 方法对照（M3，前置 Q09/Q10/PAR-04 未满足）、L03 本体（另有 Q08/Q09/W10/W11/W12/W15 前置）、A/H bridge 导入批次（等 owner 裁决签收表数据缺陷）、W06 F1/F2/F3 跟进批次（已完成待里程碑合并审查）、Q06/Q07/Q10 partial 收尾链。
- 本包不授予任何外仓写入；审查为只读复算 + 报告写入 `reviews/G2/`。

## 2. 依赖证据（G2 deps 全绿）
| 依赖 | 状态 | 证据锚点 |
|---|---|---|
| **L02** | 报告链闭环 | `reviews/L02/L02-calibration-report-2026-10-05.md`（r1 needs_revision→修订→**r2 approved**）+ `reviews/L02/independent-review-2026-10-05.md` + 证据 `L02-summary-6mimo-2026-10-05.json` |
| W03 | verified | StockWiki 本地 `4fbda21`（Phase 55，六 case、独立审查 approved、基线登记经确认） |
| W04 | verified | StockWiki `5f2739a`（Phase 59，分层候选 60/25/15、两轮审查 approved） |
| W09 | verified | StockWiki `ac5a653`（Phase 65，冻结快照导出、两轮审查 approved） |
| W13 | verified | StockWiki `d007a68`（Phase 62，原子准入、低分不退池、两轮审查 approved） |
| 支撑：W08 | verified | StockWiki `9fa8a7e`（恢复观察、9646 例跨仓差分） |
| 支撑：C03 | verified | SC-07 契约测试（N/A 分母 7/9 vs 7/10） |

## 3. L02 校准核心材料（r2 approved）
- 报告：`docs/implementation/reviews/L02/L02-calibration-report-2026-10-05.md`（修订版，§6=r1 findings 处置表）
- 审查：`docs/implementation/reviews/L02/independent-review-2026-10-05.md`（r1 复算 + r2 五核查点 approved）
- 冻结与修正案链：`docs/implementation/reviews/L02-freeze-2026-10-04.json`（amendment-3 切 MiMo / amendment-4 缩样 6 家冻结于 21:26:31Z 早于派发 21:31:46Z / amendment-5 探针门解释补录）
- 原始产出（只读）：`StockQAbyLLM/pilot_runs/l02_2026-10-04/`（out/primary 11 份、run-log、rejected_* 隔离区含 27 份废产出与探针）
- 复现命令：`python -X utf8 summarize.py <out.json> mimo`（r2 已实跑逐字段复现）

**终态数字（r1/r2 双重独立复算）**：6 家 182 题 = scored 111 (61.0%) / insufficient 60 (33.0%) / unknown 11 (6.0%) / **error 0**（182−111−60−11 推得，证据 JSON 无零值键——r2 INFO）；搜索执行 161/182 (88.5%)；attempts 239（182+57 修复，57/182=31.3%，预算=1 全未触顶）；来源 1,096；均延迟 46.9s / max 178.9s。

## 4. 逐 case 证据图与复算要求
| case | 证据 | 审查动作 |
|---|---|---|
| REV-01 | r1/r2 报告（reviewer 自有代码复算逐格一致、命令、输出路径、结论链） | 核对 r1→修订→r2 的可重现链，确认最终裁决绑定当前文件字节 |
| REV-02 | r1 needs_revision 不被自报通过放行；修订全部落文件后才 r2 | 确认无"旧审查放行新实现"；核 amendment-5 补录如实（retroactive 标注、无虚构 owner 签认） |
| REV-03 | 本批未改任何固定预期/负例；summarize 为只读聚合 | 抽查 diff：报告/证据文件之外无产品代码改动（L02 批次） |
| LIVE-04 | r1 专项：分母完整（71 非 scored 全留、unknown 11/11 有 response_id、15/15 未搜索→fail-closed）、缩减批前冻结、无择优 | 独立重算分母恒等式与冻结/派发时序 |
| UNI-05 | W13 测试（低分不退池 MAINT-06/UNI-05）+ W08（永不按质量删成员）+ 本批 probe:* 零池写入（r1 实证 6 份+探针 entity_id） | 抽跑/核对既有测试证据即可，本批不重测 |
| SC-07 | C03 契约测试（已审核 N/A 7/9、未审核 7/10） | 引用核验，本批不重测 |
| **REV-06**（核心） | §2.2 分层表（每格 n≤2 仅方向性——G2-F4）、成本/失败全留痕（000738 缺口披露）、恢复观察（300327 declining 含恢复题）、零池写入实证 | 复算分母/分层/费用账（run-log budget 940=out 403+rejected 537）；判定"用户排除维度零操作未单列"是否可接受 |

## 5. 可用比较组清单（deliverable 草案；2026-10-05 00:36 事故后修正）
1. **MiMo mimo-v2.6-flash × 顺序逐题 × 6 家 182 题**（L02 批，CN51/US7/HK2 冻结样缩样）——唯一完整校准组；分层 5 格 n≤2（G2-F4），仅方向性；B01 臂①的 MiMo 基线区组。**不受事故影响**（6 份文件 sha256 已记档）。
2. **MiniMax-M3 × 顺序逐题 × 4 家 120 题可复算**（原 5 家 151 题；**000672 上峰水泥的 1.3MB 原始产出于 2026-10-05 00:36:54 被审查方误覆盖为汇总 JSON，不可逆**——仅剩 run-log 级聚合：q=31、statuses={scored 29, unknown 1, not_applicable 1}、attempts=33、search=executed、response_id 在册，复算日志 E7E535D6… 于覆盖前 13 秒留存）——组内管线自检用途不变，**不与组1 跨比**；事故入档见 progress.md。
3. **同公司方法内波动参照**：002122 探针（12 scored）vs 批内（11 scored）——LLM 非确定性量级参考。
4. **不可用组**（B01 前置未满足）：跨模型、打包 3/5/10、单批 30、并发逐题、检索器对照（Brave/Tavily）——一律不得宣称。

## 6. r2 残余 INFO（本包补注，供 G2 口径）
- 墙钟：分段运行 40+18.5=58.5 分钟 ≤1h；**端到端含 4 分钟批间间隔为 62.8 分钟**——两种口径并列，G2 采用其一须写明。
- error=0 为推得值（182−111−60−11）。
- summarize provider 过滤对无 attempt provider 的文件纳入而非跳过（本数据不触发）。
- 000738 账本缺口"≈29"为单次失败口径；含修复硬上界 ≈58（当前表述可接受）。
- 未知不伪装中等的量级补充：11 unknown 全为 null 分不入均分；6 题"搜索已调用但回执不可核验"归 unknown（r1-F9）。

## 7. 诚实边界（G2 裁决须引用）
单模型单批次（MiMo）、6 家缩样（owner ≤1h 指令，批前冻结）、repeat 稳定性顺延、每 cohort n≤2（G2-F4）、样本文件 21:22:23Z 早于 amendment-4 记录写入（21:26:31Z，先冻结文件后记录修正案，freeze sha 绑定不变——G2-F5 旁注）、000738 根因未定位（单次失败+复跑即成）、MiniMax/MiMo 控制台对账 pending（owner，不阻塞）、B01/L03 未开始。
