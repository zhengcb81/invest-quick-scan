# OPS-DESK-01-R1 集中验收：三组续做，手册组关闭

2026-10-11。结论：`changes_requested`。本次接收 remediation-01，不重复原包实现；原 R4 手册能力/permit/资格说明已关闭，原 R1—R3 仍有边界反例。原 writer 只续 [同包 R2](OPS-DESK-01-R2.md)。这是同一个包的集中验收，不新增 helper 审查门。

## 实际交付与范围

- 唯一源根 `C:/Users/郑曾波/Projects/iqs-operations-lab`，分支 `codex/ops-desk-01`，基线 `dec3942fbdfe984e024713cb332ca76c8d890f6c`，产品 `0867efbfac87563c5b231b4bce1f5ab1618f26a2`，实际终态 HEAD `bab279f261eb23d5bfe8f11687deaa32e5abc008`。交接便笺另记录 handoff commit `b95a0193b3d1e6283cc89d3005c795358fd9b14e`；它不等于实际终态 HEAD。
- `docs/handoff/OPS-DESK-01/remediation-01/` 的 82 项工件、12 项原输入锁、144 个跟踪原件均按 bytes/raw SHA 冻结核对。Git 实际产品差异与声明的 38 路径相等（27 新增、11 修改）；交接文档另外列在真实 Git 差异中。base/result 工作树清单分别核 80/107 条，与旧冻结/本次副本相符；没有清单漂移。
- 原 1.0 schemas、原交接/日志、原 fixture、desk-01 输出和原四个测试文件保持字节不变。当前源状态只有此前获准的未跟踪 `.codegraph/`；验收前后 HEAD/status/144 文件 SHA 相同。没有写 Lab 或代其提交。
- 新具名 `iqs.operations_case_bundle/1.1.0` 与 `iqs.operations_render/1.1.0` 保留旧协议；CLI 同时读 1.0/1.1。bundle schema SHA `7dd44ed54e23aa2f3502ffe7a9100a659da0ffc5a63725b3aabf1892b8d306c1`，render schema SHA `60c89336339db23d3e9d656183b98acf3e57f5cf4272f31ca866bcd61151e0db`。

## 原测试和总控独立控制

实际隔离根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/ops-r1-acceptance-2026-10-11-01`。保留 snapshot/delivery-check、全部真实子进程 PID/终态/stdout/stderr raw SHA、控制器、冻结源副本和小合成反例；未将这些私有样例或日志整体推送。

| 验证 | 实际结果与范围 |
| --- | --- |
| 原 `python -B -X utf8 -m unittest discover -s tests -v` | PID 48012，exit0，10.7286163 秒；104 项中 103P/1 Windows symlink 权限 skip。真实 owned 硬链接和 leaf junction 测试通过 |
| 25 组独立公开 validate/render | 50 次真实 CLI；20/25 组退出码符合预期，5 组不符。此外 2 组虽 exit0 仍激活 Markdown 标记，1 组虽 exit2 仍泄露合成凭据哨兵。退出码符合不等于完整行为通过 |
| 4 项定向补验 | 2 个实际父目录 junction 被接受；超长版本触发异常；总量读界限事后才判断。详见下表 |
| IQS 公开 parallel_handoff_cli | PID 6124，exit0，`handoff_shape_and_declared_scope_only`；不认证 writer 的 complete/approved 声明，不关闭产品验收 |
| 单次独立静态包级审查 | [独立审查记录](OPS-DESK-01-R1-independent-review.md)：R4 关闭，R1—R3 续做；总控以实际 CLI/CommonMark/IO 控制核实 |

原 suite stderr SHA `e9e6c9f7463d5b5b9da5c51293144ec96bec352ca3042b18c5d955301144d677`；stdout 为空。handoff stdout SHA `46028ec7585c63b2c0df5c3c5af8899da3f84cefb9a79fbf0dbbf03c3e842366`；stderr 为空。其他 PID、输入 SHA 与日志 SHA 在 `independent-cases.json`、`extra-cases.json` 和 `logs/*.process.json` 可逐项对照。

## 仍未关闭的原根因

| 原组 / 独立场景 | 预期 | 实际 |
| --- | --- | --- |
| R1 protocol-array / protocol-object | 畸形容器稳定 exit2、无 traceback、无正式输出 | validate PID63776/54732、render77080/69520 均 exit1，未捕获 TypeError |
| R1 huge-protocol-version | 超长版本有界拒收 exit2 | 主版本 5000 位数字；validate21220/render33704 均 exit1、int 转换 traceback |
| R1 三个 legal-*-id-schema-boundary | 旧 schema 合法正例 exit0 | case 前缀后60字符、state/evidence前缀后40字符（全长65/43）均通过原 schema，却 validate/render exit2；validate PID74704/18852/27296 |
| R2 ancestor-evidence-junction | 路径链上的链接按原规则拒收 | 实际 owned `alias` 目录 junction 指向同 case `real`，`alias/note.txt` 叶子为普通文件；validate67188/render12712 均 exit0并产正式输出 |
| R2 ancestor-bundle-junction | 主 bundle 路径链同样检查 | 从 `alias/bundle.json` 读同根目标；validate24896/render57712 均 exit0并产正式输出 |
| R2 aggregate-evidence-read-budget | 16MiB 总量在读取前/读取期间约束 | 17 个不同 evidence ID 引用同一1MiB普通文件；公开 validate64484 exit2，但观测原 CLI 的包装进程80620实际调用17次，先读17,825,792 bytes 后才判总量超限 |
| R2 duplicate-secret-key | 重复 JSON 拒收，不回显任何疑似凭据 | validate46448/render62112 exit2，原 duplicate key 被复述，两个输出都含合成哨兵 |
| R3 backtick-prefix-injection / backtick-suffix-injection | 用户文本保持非活动引用，固定未认证条幅清楚 | validate/render exit0；CommonMark 实际 AST 出现远程图片和/或原始 HTML 标记。原测试的手写 token 清除器误认为它们在 code span 内 |

Markdown 控制使用真实 `MarkdownIt("commonmark")`，仅解析 AST，没有启动浏览器、请求图片或执行 script。它证明渲染文本能够形成活动标记，不能冒称发生了网络泄露或脚本执行。IO 包装仅观察原 `read_bounded` 的路径、返回字节和次数，不替换实现、不更改产品。

已经修好的非法日历/refs类型/owner类型/重复引用/合成混淆、单文件大小/二进制/主硬链接、真正1.1零证据 partial 等保留。R4 对快扫 Web 设置保持未核实，旧 preview 操作只限旧协议，新 permit/dispatch_commit 派发保持 not_available，并保留 eligible_provisional 受限例外；这些说明已合格。

## 隔离与清理

测试父子环境去除所有 key，只保留系统变量和 owned Python 路径；继承 Python audit 限制读写、socket和子进程，真实 junction 命令只允许一个预先确定的 owned 路径对。handoff CLI 额外只读允许原 IQS script/catalog/schema 三个精确文件，核其前后 SHA。没有真实 API、生产数据库、公司文档下载或外仓业务写入。

两个反例目录 junction 核定其绝对路径/目标后，仅移除链接入口、没有递归跟随目标。再逐文件核普通文件、SHA、file ID、封闭硬链接组和144个冻结原件，清理83个自有临时文件/43个目录，保留小合成反例及完整日志/副本。沙箱 CIM 访问被拒的空管道不算进程证据；随后提权只读 CIM 成功，owned Python 进程为0。`closeout.json` 留真实结果。

## 后续

原 writer 续 [R2 三组卡](OPS-DESK-01-R2.md)，保留已绿内容，不重写手册或另开重叠 writer。新交接放 remediation-02，原交接/清单/日志不覆盖。收到后在同一包续验受影响正反例；B01 主线、金融准确性、G3/F05、真实 owner 接线、生产 UI/一键/全池门不因此关闭。
