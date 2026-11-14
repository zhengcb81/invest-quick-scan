# FACT-CONTENT-01-R2：证据、主体与期间的闭合收口

这是原 FACT-CONTENT-01 同一次集中验收的续改卡，不是新门。唯一写根 `C:/Users/郑曾波/Projects/iqs-fact-content-lab`；其他仓只读。用户总体后续授权保持，先确认本根唯一writer，再正常施工。不得替 EVID 提交或改 IQS 根 PWF。

## 必读与实际基线

- [原R1卡](FACT-CONTENT-01-R1.md)、[本次实质复验](FACT-CONTENT-01-R1-acceptance.md)、[原交接规范](../../../parallel-lanes/packages/2026-10-10/handoff-rules.md)、[原输入锁](../../../parallel-lanes/packages/2026-10-10/inputs.lock.json)。
- 真实 `codex/fact-content-01-r1@d00e2b64c09ff0ff9a563fe6cc3cc11ec26b7555`，产品 `b227b3356efe549a2a47904f2000036d4e0e1f64`；无remote，正常保留原提交。CodeGraph已经由用户授权初始化，不重复询问/重建。不 reset/clean/stash。
- 只读反例规格：[r1_counterexamples.py](r1_counterexamples.py)、[followup](r1_followup_counterexamples.py)、[合法历史fixture](r1_temporal_case.py)。不得盲运行主控脚本，它们绑定 IQS 自有根；在本仓独占测试根构造同类正常/错误输入，运行本仓实际公开CLI。
- 白名单仍是原本仓 README/.gitignore/pyproject、src/schemas/content/tests/fixtures/tools，新增交接只写 `docs/handoff/FACT-CONTENT-01/remediation-02/`。R0/R1交接原件不覆盖。PWF明确pin此新交接下的planning目录，不竞争总控root计划。

## 按顺序实施

1. **一次集中RED，目标错误可辨。** 重封pack/input/case hash并同步或省略可选view；先让无变异同fixture exit0，再断言变异具体拒绝原因。不要用非法schema/旧view错误代替目标负例。合法historical target用既有 `basis=trailing`，不是非法historical枚举。记录首次失败/fixture失败/最终GREEN，旧115P不重复冒充新结果。
2. **证据与主体。** unsourced 不能给同target supported/strict=true，unknown不改成false或零。声明的 scope.entity 与 source_facts.subject 必须对应同一主体；有母子公司转换时显式给双方和角色，不能名称或group关系自动继承资格。正常同主体有源正例保留。
3. **时间支持。** 当前关系须已生效且未过期；定义有效区间边界并统一文档/实现/测试。历史目标区间必须有对应的有效关系证据，不能把2025事实当2020证明；未来目标不能装成当前成立。保留真正历史正例、终止关系的历史资料及未知时间，不删难例。
4. **输入与provenance。** 对每条嵌套原始路径先拒secret/reparse，再规范化并核定位。真实junction正例（应拒）只建在自有临时根，不能因平台创建失败计测试GREEN。`api_key.json` 等假秘密名用自有合法JSON，不读真实key。真实来源绑定实际锁身份、原件完整定位与raw SHA；后缀/非空lock字符串不授予真实来源资格。synthetic照旧不冒充real。
5. **新包含关系闭合。** member_of_refs独立核不存在的引用、自包含和包含循环；禁止通过parent_refs的is-a继承来“解决”集团成员关系。保留有向、合法非循环包含正例；group/subsidiary身份仍不合并。
6. **旧版明确只读消费。** 提供具名只读入口或公开模式，保留1.0字节/schema/原未知标签及版本标记，缺target标needs_review/unknown且不导出已认证1.1业务正例；新写入仍只用当前具名版本。未来版本拒绝。字段意义变化必须新版本，纯拒绝缺口修补不要机械升级无关题目/ID；interfaces写出实际命令和迁移限制。
7. **整体内容修正。** FC11引用闭合与设备使用分开；FC01有hardware证据不能顺带证明internet；FC05明示集团控项目公司与项目公司受集团控制的两个主体/方向。通读全部46case，不删原ID去逃避失败。保持候选模块组合与“当期差/优势仍存/修复待证/不可逆风险”可组合；不能用expected_labels自证正确。相同不足若在别的case出现一起按规则修，不只改三个字符串。

## 测试、版本与交回

开发跑受影响测试，交付一次相关完整回归＋真实公开 validate/export/旧版只读CLI＋本表独立正反例；在同一包级复验收口，不新增helper审查或重跑UI/备份。保留原六类修复的保护测试，重点新八机械反例、旧版消费、三内容问题；精确JUnit分母和selector/raw SHA，不拼重叠批次。

每次全新独占短临时根，TEMP/TMP/TMPDIR、pytest和子进程都归此根；无API/key/网络，源锁只读。终态后只清自己的复制品/假秘密/真实junction，先删除链接本身且不递归目标，再核集合bytes/SHA。保留轻量日志，不留公司文档；共享TEMP、IQS活根、其他writer不碰。

交到本仓 `docs/handoff/FACT-CONTENT-01/remediation-02/`：标准handoff1.0.0（package_id仍FACT-CONTENT-01，lane=iqs，task_ids沿原manifest）、summary/artifacts/interfaces/case-map/isolation/三PWF、逐缺陷映射与内容处置。正常精确git add、先产品/测试commit再记录完整result_commit和交接commit；无remote不用push。实际源码HEAD与handoff齐全才通知总控收件，不把临时文件当完成。

46 case仍synthetic、production_mapping=not_mapped、production_case_status=not_run；本卡不关闭F05、正式题库/词表发布、G3/C06/L03/B01/TH-IN/真实公司准确性/全池门。不自动派发其他harness。
