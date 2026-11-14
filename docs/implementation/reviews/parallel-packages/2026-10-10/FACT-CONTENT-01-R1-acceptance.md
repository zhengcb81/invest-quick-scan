# FACT-CONTENT-01-R1 集中续验

结论：**changes_requested**。原六项机械整改已通过本轮独立控制与反例；新增的证据、主体、期间和包含关系闭合缺口仍会让错误资料成为严格正例。保留交付，不作为 F05 生产语义金标准。

## 实际输入与执行

- 唯一源仓 `C:/Users/郑曾波/Projects/iqs-fact-content-lab`，分支 `codex/fact-content-01-r1`，HEAD `d00e2b64c09ff0ff9a563fe6cc3cc11ec26b7555`；产品结果 `b227b3356efe549a2a47904f2000036d4e0e1f64` 确为 HEAD 祖先。没有 remote。
- 109 受控文件固定到总控独占 `runs/p114r1a/fact`；106 交付工件 bytes/raw SHA 全匹配，213 锁内输入无漂移。源仓不运行测试、不代改；用户另行同意的 CodeGraph 初始化 exit0，29 文件/472 节点/443 边，索引不属于产品提交。
- 实际整包回归 **115 passed / 0 failed / 0 error / 0 skipped**，JUnit 90.061s、controller 91.548s，PID50728/exit0。公开 handoff CLI PID35324/exit0，只检形状和自述范围。
- 同次包级复验的公开原 CLI 原件在 `docs/implementation/intake/parallel-packages/2026-10-10/remediation-01/logs/`。反例控制器自身 exit0 是执行成功，**不是**产品全部符合安全断言。未修改生产数据库、名单或原 C06 活根；没有收费 API 或公司文档下载。
- 一次独立只读审查，另由主控实际执行反例；没有新增逐 helper 审查门。

## 已修复并保留

原六类问题已独立复验：错 question/file SHA 会以目标原因拒绝；陈旧 view 不再掩盖 source SHA；explicitly_absent 与 true 冲突拒绝；非法日历日期拒绝；验证后替换磁盘 cases 仍只导出原 46 case、哨兵字节不变；schema override 不能扩大输出根。旧 45 case ID 全保留，新增认证候选后 46 个。FC07/FC10/FC12 的部分修正及周期与恢复允许组合方向有效。

## 实际 CLI 仍放行的八项

下表都使用合法 schema、同步重封原 hash、正常控制例和自有变异输入。绝不读取真实秘密。

| ID | 本轮实际行为 | 应有行为 / 位置 |
|---|---|---|
| FC07 | assertion 与 target 的 valid_from 改2027-01-01，as_of仍2026-06-30，exit0 | 未来尚未生效不能支持当前关系；`case_rules.py:331` |
| FC08 | 合法 trailing 历史目标为2020全年，来源有效期为2025全年，exit0 | 历史目标须有对应区间的证据；`case_rules.py:316` |
| FC09 | 合法 cases 放在自有假 `api_key.json`，嵌套读取exit0 | 原路径在读前拒秘密名称；`guards.py:23` |
| FC10 | 原 nested case_file 经真实 Windows junction，exit0 | 检查原路径全链后才规范化；`validate.py:55` |
| FC11 | 伪根加合法锁内文件后缀、合法SHA、任意lock字符串，可成 real_source_excerpt，exit0 | 绑定该真实锁及完整原件定位；`case_rules.py:445` |
| FC13 | source 与 target 同改 unsourced，supported/strict仍true，exit0 | 无证据保持 unknown；`case_rules.py:264` |
| FC14 | scope.entity换另一家公司，source subject不变，exit0 | 来源与被判定主体必须一致；`case_rules.py:250` |
| FC15 | member_of_refs指向不存在的ct.undefined，exit0 | 独立包含关系引用/自环/循环闭合；`closure.py:220` |

**控制器错误均保留和更正：** FC08 首次用了 schema 不支持的 `basis=historical`，exit2 是 fixture 错误，不能计产品通过或漏检。仅改为原已使用的 `trailing` 后，PID47288 的真实 CLI exit0 才确认该缺口。真实 junction 首次沙箱创建被拒，未进入产品；升级同一自有根创建成功后 PID50816 的原 CLI exit0 才作为证据。第一次 CIM 的匹配1是查询 shell 自身，不是活测试；第二次成功查询单独记录查询 PID，其余自有进程0。

## 兼容与原内容阻断

1. **旧版读取不闭合。** 当前公共 validator 固定1.1.0，实际旧1.0.0输入exit2；归档schema和字节有保留，但没有公开只读解释结果或 needs_review 路径。不能把拒绝全部旧版称兼容；提供明确的旧版只读模式，不补造 target 或升级资格，未来未知版本仍拒绝。见 `schema_io.py:21`、`cli.py:35` 及新版 interfaces 版本表。
2. **FC11-refs-closed：软件闭合当业务证明。** 原 source（`semantic-cases.json:3753`）只证明设备/材料引用在词表中，target（:3772）却声称公司使用设备，supported（:3710）为true。应另有业务证据或保持业务unknown。
3. **FC01-coverage-combo-hardware：选配当业务语境。** source（:345）只有供产销和未披露预售，target（:364）却把 hardware/internet 同时判真（:298/302），缺互联网依据。保持模块可组合，但组合本身不证明公司业务。
4. **FC05-group-subsidiary-ok：母子公司主体位置错。** source subject为集团Synthetic-Q（:1601），事实是其控股另一项目公司70%（:1589），target却将该集团放到 controlled_by 被控制端（:1621），仍true（:1546）。明确两个主体和方向后再判。

后三项属于对原交付的独立内容审查，不混成已执行的测试数量。

## 接续

按 [FACT-CONTENT-01-R2](FACT-CONTENT-01-R2.md) 继续本次包级验收。EVID 本次仍缺新版完整交接、原HEAD未前进且有未提交R1 writer，状态为 `handoff_pending`；不拿旧 handoff 再验或替它提交。F05/G3/C06/W15/真实金融准确性/TH-IN/全池门均不由本包关闭。

严格自有清理的结果以同批 intake `cleanup.json` 为准；只有该实际终态记录存在才称清理完成。原源仓、共享 TEMP、c15a/real-owner-01及其他 writer 文件保留。
