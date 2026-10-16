> 当前派发状态：用户于2026-10-16确认三包均已开工；各Lab按独立writer避让。以下冻结/发布描述为准备时事实，原inputs.lock.json及输入原件保持，不回写已分发锁。

# 真实实验期间的三个独立施工包

2026-10-16，状态：已冻结并通过发布验证，可交给独立 harness 开工，尚未派发。这里没有建立外部 Lab，没有运行模型或收费搜索，也没有授予任何金融或生产资格。

| 可直接交给 harness 的卡片 | 独占可写根 | 交付 |
|---|---|---|
| [OPERATING-CATL-05](OPERATING-CATL-05.md) | `C:/Users/郑曾波/Projects/iqs-operating-catl-lab` | CATL 有界经营机制、反证、未知与离线覆盖工具 |
| [OPERATING-CSC-05](OPERATING-CSC-05.md) | `C:/Users/郑曾波/Projects/iqs-operating-csc-lab` | 中信建投对应材料，保留 A/H 同主体和集团/母公司边界 |
| [EXPERIMENT-DESK-05](EXPERIMENT-DESK-05.md) | `C:/Users/郑曾波/Projects/iqs-experiment-desk-lab` | 固定 T0/T1 与六工具产物的离线只读矩阵、时轴和明细 |

以上三个绝对根在本次编卡只读检查时均不存在，互相不是祖先/后代，亦不在 IQS 或既有六工具 Lab 内。工人开工时必须再检查；存在不明文件或 writer 时报告冲突，不覆盖。检查只表示可预留，不能写成已创建或已授权派发。

三个包不依赖另两个包的新产物，不重复已验收财务标量、六工具、预算恢复或主线实验。总控继续原 SDK/累计预算下的真实调用与集成；工人只写自己新根。真实实验下一轮是否成功不影响这三包离线施工。

每张卡片与 [共同契约](integration-contract.md)、[接口字段规范](interface-spec.md)、[交接模板](handoff.template.json)、总控生成的 `inputs.lock.json` 以及其选定输入子集一起交付即可独立运行，无须聊天补充。`source-requests.json` 是明确建议采集清单，**不是**已经冻结的输入锁。总控按清单将原始文件逐个冻结到 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/real-experiment-parallel-2026-10-16/inputs`，发布前实测原 hash、搬迁、篡改、缺文件和路径交叠反例。缺输入必须报告并修正发布清单，不能给工人追活动仓 latest。

发布冻结还应把本目录的实际交付文档纳入 `package/` 输入，记录原始 SHA256；工人仅认随卡片发出的锁与原件。本目录 [发布验收要求](release-checklist.md) 是一个整包节点，不给每个 helper 加审批。主线后续补充 `preparation-result.json` / `preparation-review.md` 时，应明确实际检查与尚未运行，不把本文设计要求当成执行证据。

最新依据为 [六工具工程签收](../../../experiments/six-tools-acceptance-2026-10-16.md)：426 项整组与 7 项跨包通过，但不等于金融准确率或策略赢家。固定样例 T0 为 4/72 合法答案、T1 为 15/72；T1 工具 adapter 只有 36 输入槽，原登记仍是 72。未知费用保留未知；旧测量快照中的 pending 不覆盖后来完成的独立审查。

发布实测：397 个精确输入已冻结，完整集及三个 consumer 子集核 hash 通过；搬迁通过，篡改、缺文件、写根交叠和路径越界均拒绝。测试副本 398 文件 / 8866481 bytes 已清理，剩余 0。见 [发布回执](preparation-result.json) 与 [集中审查](preparation-review.md)。锁文件 raw SHA 由发布回执传递，工人使用 `verify_preparation.py --inputs <输入根> --lock <锁> --package-id <包名> --expected-lock-sha256 <回执中的值>` 核验；这里只验证输入完整性，不代表产品或金融验收。
