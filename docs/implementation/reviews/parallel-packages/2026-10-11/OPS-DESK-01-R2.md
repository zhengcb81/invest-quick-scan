# OPS-DESK-01-R2：原三组边界收口

本卡可独立交给原 harness。唯一 writer 和唯一写根仍为 `C:/Users/郑曾波/Projects/iqs-operations-lab`；不得另开重叠 writer。先读 [R1验收](OPS-DESK-01-R1-acceptance.md)、[独立审查](OPS-DESK-01-R1-independent-review.md)、[原R1卡](OPS-DESK-01-R1.md)，以及 [原包](../../../parallel-lanes/packages/2026-10-11-wave2/OPS-DESK-01.md)/[共同规则](../../../parallel-lanes/packages/2026-10-11-wave2/handoff-rules.md)。不用读聊天。

本次集中验收只续原 R1—R3。R4已关闭，保留其文档准确性，不实现新owner/资格/重试/生产操作。103P/1Windows skip、12原输入、旧1.0/新1.1正常能力和原交接均保留；不是重建十family或另起一轮全项目审计。

## 接手基线与范围

- 分支 `codex/ops-desk-01`，产品 `0867efbfac87563c5b231b4bce1f5ab1618f26a2`，实际验收 HEAD `bab279f261eb23d5bfe8f11687deaa32e5abc008`，状态只有 `?? .codegraph/`。144跟踪文件/82工件核对一致。开工重查当前 HEAD/status，若后续别的 writer 更改，先留差异再接，不回滚/覆盖它。
- 写入仅本 Lab 原范围；重点 `src/iqs_operations_lab/bundle.py`、`paths.py`、`strictjson.py`、`render.py` 和对应原整改测试/`tests/util_cli.py`。可新增同根定向测试、脱敏小 fixture 和 remediation-02 交接。不用改生产仓、输入锁、全局配置、系统权限或其他 Lab。
- 旧1.0 schemas、原fixture/desk-01、初次与remediation-01交接/日志不覆盖。现在具名1.1也是验收冻结参考；这轮应修运行时与它的合同一致，不通过缩小schema来“修复”合法正例。如确需新语义，另列具名版本与读取选择，不能偷偷改默认或旧bytes。
- 总控反例原件在 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/ops-r1-acceptance-2026-10-11-01/retained-cases/`；控制器及 `independent-cases.json`/`extra-cases.json` 保留在其父目录。仅只读，不在总控目录跑脚本或创建资源；在自身独立临时根重建同一小合成场景。原junction已严格清理，不要期待旧alias仍存在。

## 三组固定 RED 与实现要求

### 原R1：稳定类型拒收和合法长度

1. `protocol=[]`、`{}`、null、bool、数字都必须稳定 exit2，无 traceback、无正式render输出。任何membership/get/正则/版本转换前先类型和长度校验。5000位版本主数字必须有界拒收，不能先调用 `int` 再指望后续长度检查。
2. 严格按原 schema 的正例：`CASE-`后60个`A`共65字符，`OS-`/`EV-`后40个`A`共43字符；更新引用以保持闭合。schema验证和两个公开操作都应成功。每类再测上限+1稳定拒收，不能靠改变前缀/随意缩短ID避开。
3. 保留旧非法日历/refs/owner/唯一性/synthetic防线与原中文/正常1.0和1.1partial。不要广义捕获所有异常并返回成功；可安全映射已知输入错误，意外内部错误不包装成“已验证”。

### 原R2：路径链、总量和安全报错

1. 创建两个**实际**同owned根目录junction控制：`alias`指向同case的`real`；其一 evidence=`alias/note.txt`，其二主bundle=`alias/bundle.json`，最终文件均普通、hash/bytes正确。两个公开操作都须拒收、无正式输出。现在只验leaf类型的junction测试不能替代父目录链测试。
2. 明确 bundle/evidence/catalog/inventory 的可信锚点，先保留词法路径检查并逐组件核reparse/symlink/普通文件/硬链接与包含关系，再读。不能先resolve丢弃链的信息；同根别名和越根别名都覆盖。普通目录同根正例须保留。Windows无symlink权限可skip该项，但实际owned硬链接/junction不能全以skip回避；不改系统权限。
3. 总量16MiB按已公布口径先做有界preflight/读取期间预算。固定17个不同ID各声明1MiB、引用同一普通1MiB文件，公开CLI仍exit2，但不能完成17MiB读取后才拒收。计数包装只观察原read函数，不替换它；加正好16MiB和超界/声明与真实bytes不符控制。可缓存同一文件的已核字节，但不能因此让原应拒收的总量合同通过。不要用无限read_bytes、假观测或只测最终exit2证明事前防线。
4. rawJSON包含两个相同的疑似`api_key=<合成哨兵>`键；validate/render exit2但stdout/stderr不得含哨兵或原key。duplicate-key异常只含安全code/结构位置，不能复述原键，审计/日志也同样适用。只用明确假值，不读取实际env/key或传播真实凭据。

### 原R3：真实Markdown语义的纯文本

1. 对原注入文本分别前缀一个反引号、后缀一个反引号，以及首尾空白、换行、不同长度反引号run、code围栏组合。文本仍包含两次换行后伪资格引用、Markdown远程图片和HTML标记。当前动态code span相邻拼接不足以保护。
2. 用实际 CommonMark 解析器检查最终report AST，非可信文本不能生成 image/link/raw HTML、独立伪认证/重试条幅。固定unqualified/synthetic条幅仍清楚；原值保留为非活动文字。手写substring删除/只搜输出字符串不是有效oracle。无需真实浏览器访问远程URL或执行script。
3. 继续接受显式1.1零证据partial和旧合法1.0；不改变评分/owner资格，不要求补假证据。新测试正常中文/无反引号/合法长文本对照也须通过，不能删除展示字段绕过。

## 验证和清理

先把上述反例在原候选测成RED，再最小修复。修复只续跑受影响的三组与旧兼容/R4保留项；同一稳定候选做一次集中unit/integration/实际公开CLI E2E和一次包级独审，不为小helper新增审查。原suite已103P/1skip，不为每个编辑重跑全包；若接口/共同加载路径有大变化，发布前一次完整回归即可。

公开入口示例（cwd本Lab且模块可导入；隔离子环境不含真实key）：

```powershell
python -B -X utf8 -m iqs_operations_lab validate --bundle <owned-case>/bundle.json
python -B -X utf8 -m iqs_operations_lab render --bundle <owned-case>/bundle.json --output <owned-new-output>
```

每个拒收案例核exit2、无traceback、无正式输出、无哨兵；正例核exit0/内容。记录原命令、PID、实际终态、stdout/stderr原bytes与SHA、输入/AST或计数字段，不把自身期望当观测。保留失败日志。无API、收费、公司文档、生产DB或证据执行；Python父子隔离不冒称OS沙箱。临时资源仅自身owned根：绝对目标检查、junction入口不递归移除、封闭硬链接组、文件hash保护、进程终态和清理结果留档。

## 唯一新交接

在本Lab `docs/handoff/OPS-DESK-01/remediation-02/`，沿用公开handoff1.0模板，附README、interfaces、artifacts、原12输入快照、case-map、review、isolation、PWF及原日志。记录真实当前base/product/handoff/terminalHEAD；逐文件scope与raw工作树清单来自实际Git，不拿施工manifest充数。先正常产品commit再交接commit，无remote不用造push。artifacts无自引用且path/bytes/rawSHA闭合，原交接不覆写。

公开总控结构预检使用原wave2 catalog/OPS-DESK-01 package-id；仅形状通过，不得自称G3/F05或生产UI/一键已关闭。最终总控在原包一次接续验收，真实owner/主线接线仍由总控负责。
