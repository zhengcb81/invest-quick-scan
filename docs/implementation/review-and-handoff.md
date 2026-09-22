# 审查、完成回执与任务交接

2026-09-22。每张任务卡经历`planned → in_progress → implementation_complete → review_pending → verified`。测试失败或审查发现问题进入`needs_revision`；依赖/环境/必要配置缺失为`blocked`。纯审查卡和在线卡使用相同证据原则，完成状态记录在实际回执中，不在多个表里重复维护。

## 实现者自查

提交审查前用实际diff或文件hash逐项回答：改动是否只属于owner；是否复用已核实接口；契约/题义/作用层是否改变；是否影响旧strict或历史观察；是否出现公司正文/密钥持久化；失败/unknown/过期有没有被吞掉；测试是否调用真实实现；是否处理空、错、重复、过期和中断；其他已存在改动是否被误覆盖。

若项目没有Git，记录任务前后允许修改文件的SHA-256、创建/修改清单和必要的局部差异。不得假装有commit或PR，也不把个人目录中的其他文件纳入大范围快照。

## 独立审查回合

审查可以由另一个模型、另一个明确分开的审查上下文或人工进行，不要求每张卡都打断用户确认。没有独立审查资源时实现者可以继续自查，但状态保留review_pending；不得将同一实现叙述称为独立审查。

审查者读取任务卡、固定约束、关联cases、实际diff/目标快照、测试代码与原始输出。先复述预期行为，再试图找一个会产生错误实体、错误分数、额外费用、丢失任务或错误研究结论的反例。每个发现写清触发条件、位置、影响和期望修复，不只给“建议提高鲁棒性”。

| 审查轮次 | 核心问题 | 不能放行的例子 |
|---|---|---|
| 设计/范围 | 为什么放在这个仓库，是否改变已冻结经济含义？ | 在skill建客户端、证券和实体混用、改变关键风险门槛 |
| 测试/实现 | 测试会在错误实现下失败吗？真实调用链是否走到新增功能？ | mock被测函数、仅测helper却CLI没接入、仍容许5/8 |
| 数据/运行 | 失败、中断、重复和历史回看是否可解释？ | 重导入续期、同键异hash覆盖、未知费用归零、先标delivered再入库 |
| 研究/证据 | 分数、事实、推断、来源资格是否分开？ | 从低分切模型、反转抹掉断粮、使用者被当供应商、自我引用增加置信度 |

G0—G6是跨任务阶段审查；单任务审查不能替代阶段端到端验收。O05/G5若事实能力尚未G4，必须明确评分范围，不能发布完整事实能力。整个计划完成还需G6同时覆盖G4、G5、实际配套安装/技能加载与同一入口的真实全链；最终review绑定release_set，不能只审查其中一仓。

## 问题闭环

问题记录字段：`finding_id / severity / task_id / snapshot / location / trigger / expected / observed / impact / fix_reference / verification / status`。

- 阻塞：错误公司/证券、不可恢复丢数据、无限或越预算收费、伪造来源/搜索/分数、绕过关键风险或越界写入。修复并验证前不能verified。
- 重要：合法场景失效、结果不完整、不可重现历史、错误状态/计数或消费者错误用数。修复或有明确的范围收缩及审查认可，不能默默忽略。
- 一般：不影响上述语义的文案/局部实现改进。记录取舍，不为关闭全部一般意见扩大任务。

修复后将问题逐项关联到变更和测试。审查绑定代码/数据schema/题库/测试场景的精确快照；任何受审查内容再变化，需要重新审查受影响部分。通过文本不是永久通行证。

## 完成回执的最小结构

以下为字段模板，省略项需要明确not_applicable及原因。不要把模板值复制成“已验证”。回执留在owner的任务记录目录；中央计划可保存其路径及hash，不复制公司文档或维护另一份运行数据库。

```json
{
  "task_id": "TASK_ID",
  "status": "review_pending",
  "owner": "OWNER_ID",
  "plan_version": "1.4.0",
  "plan_sha256": "ACTUAL_HASH",
  "case_catalog_sha256": "ACTUAL_HASH",
  "implementation_snapshot": {"commit": null, "file_hashes": {}},
  "dependency_receipts": [],
  "changed_files": [],
  "contract_changes": [],
  "checks": [
    {
      "case_id": "CASE_ID",
      "kind": "automated_or_review_or_live",
      "selector": "ACTUAL_TEST_OR_CHECK",
      "command": "ACTUAL_COMMAND_IF_ANY",
      "cwd": "ACTUAL_OWNER_DIRECTORY",
      "result": "not_run",
      "exit_code": null,
      "executed_count": null,
      "skipped_count": null,
      "output_path": null,
      "output_sha256": null,
      "explanation": "NOT_EXECUTED_YET"
    }
  ],
  "review": {"reviewer": null, "snapshot": null, "result": "pending", "findings": []},
  "rollback_evidence": null,
  "open_issues": [],
  "next_task": null,
  "resume_from": null
}
```

合同/文档审查没有退出码时可以为null，但必须有具体结论、位置与审查记录。自动测试必须保留实际退出码、执行/skip数量和可读取输出；真实调用另附请求/搜索/费用回执。hash证明文件版本一致，不证明测试真实发生或结论正确；审查者仍需复现关键检查。

## 中途交接

上下文用尽或本次无法继续时，写明：当前任务、已完成步骤、允许改动与实际改动、最后一次通过/失败的检查、未解决问题、正在运行请求/结果不明项、费用已用/预留、准确的下一步。记录原始文件/回执位置，不让下个模型靠重新调用LLM寻找进度。

不得标verified来让下一任务开始；依赖只做到implementation_complete时，下游可做兼容性探索，但不能以未验收接口完成发布。只有契约已G0的独立分支才可自行推进；本包不自动创建并行任务或授予外部写入权限。

## 审查提示模板

> 审查任务<TASK_ID>，不要以实现者的完成声明作为结论。先读取任务卡、关联case和固定约束，再检查实际快照、diff、测试代码与输出。重点寻找错误实体、null→5、重复收费、旧数据续期、关键风险绕过、正文落盘或消费者误用的反例。区分未运行、失败、skip和通过。输出具体发现及是否阻塞，核实修复后才给verified；未实际执行的检查保持未执行。
