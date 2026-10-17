# QUERY-ENTITY-07 总控独立验收（2026-10-17）

结论：原交付尚有三个输入边界缺陷；隔离修复候选已通过全套回归，待总控将六文件最小补丁按原始字节校验写回、提交并绑定新交接。此记录不授予生产或金融资格。

- 源仓：`C:/Users/郑曾波/Projects/iqs-query-identity-lab`，冻结 HEAD `27dfff9e6f22aa5d7b4313cc6f0050887be45529`；实现 payload `2f3514c46db2e430a6b839f2f281d1c5b3f7a2c8`。
- 输入锁 raw SHA256：`728c93b1fa5383dc95593c9495a02f698f4e7d079487b43a4d4d62b8fc9db5d2`。
- 117 个交接清单/交接自身文件 raw hash 与 HEAD Git blob 全匹配；核心实现、schema、fixture、catalog/content 与实现 payload blob 相符。12 份冻结输入不在 artifacts 清单，但有输入锁哈希，另行冻结核实且 Git ls-files 确认均已跟踪，不是丢失文件。
- 原独审记录有不同 agent 的工具返回标识 `525033d9-8224-4116-ac88-6343ef6a6285`、四轮实际命令日志、11 项关闭、open=[]，review/final 绑定 e426306（后置证据提交）及同一 input lock；实现者 ID 和调用时刻不可得如实为 null。未把元数据提交自引用惯例视为缺陷。此验收并不把保存的调用声明升级为宿主级加密证明。

## 实质发现与已验证的最小修复

1. **QE07-C01 / P2：有限数字溢出导致非标准 CLI 退出。** `identity.extensions={"review/value":1e999}`，Python JSON 默认解成 Infinity，随后 canonical JSON 抛未捕获 ValueError；原 CLI exit1、stderr traceback，违反非法输入 exit2。字面 NaN/Infinity 既有测试不能覆盖指数溢出。修复 strictjson 有限 float 解析；超长整型 ValueError 转输入错误；纯函数 canonical 序列化非有限/循环值转 InputInvalid。原公开 CLI RED 和修后 GREEN 见 independent-probes*.json；新增 unit/E2E 测 `±1e999`、5000 位整数、纯函数 inf/nan，确认不生成输出。
2. **QE07-C02 / P2：显式输入的上级 junction 被跟随。** 原 `_read_bytes` 只检查末段文件是否为链接；将合法 identity.json 放入自有 junction 的目标目录，公开 plan 原 exit0 并产生计划。修复在读取 catalog/identity/questions/order/plan 前调用既有 reject_link_components。完全自有目录实测修后 exit3/input_link_refused，两个 junction 均已删除。见 junction-probe.json、junction-probe-fixed.json。没有读取外部敏感文件或写源仓。
3. **QE07-C03 / P2：extensions:null 破坏 schema/validator 一致性。** 闭合 schema 指定 object，Python helper 原把显式 null 当缺省 {}。独立 jsonschema/validate_identity RED 见 extension-null-red.json。修复只接受缺省或命名空间对象，显式 null 拒绝；缺省 {} 与全部旧合法 fixture 仍通过。

协议、题号、意图含义、原 catalog、版本均保持 1.0.0；没有增加真实身份映射、查询执行或金融结论。补丁仅四个源码文件及两个测试文件，详见 fixed-payload.cas.json、fixes.patch。总控须核原始哈希再写回，不可用本次候选冒充源仓原交付已经修好。

## 实测

- 原交付隔离全套：129 passed、1 skipped；公开 validate exit0，25/25 fixture cases 匹配。
- 修复候选最终全套：**142 passed、1 skipped（12.73s）**；公开 validate exit0，25/25 fixture cases 再通过。实际 argv、cwd、exit、日志 hash 见 commands.json；日志 all-tests-fixed-final2.log。
- 独立公开 CLI：正常链、歧义主体、authority 冲突、挂牌半开时点、OCF/FCF 不合并、未知 major exit4、闭合字段、重复题号/JSON键、NaN/指数溢出、公司名称特殊字符仅作为数据、未证实挂牌阻断。12 项正常语义及非法输入断言通过，overflow 修后 exit2；junction 另以实际自有目录提升权限验证。没有把 synthetic issuer 当真实 StockWiki gold。
- 既有 E2E 覆盖任意 cwd、输入搬迁、plan→validate 重推导稳定、输入/输出冲突与用户显式顺序；仍全部通过。
- 唯一 skip 是宿主无文件 symlink 创建权限；本验收实际 junction 测试覆盖父目录链接拒绝，未伪报文件 symlink 动态测试通过。

## 隔离及失败历史

不执行源仓代码，不读任何 API key；所有测试从只冻结的隔离副本执行，最小环境仅系统路径变量、自己的 HOME/TEMP/PYTHONPATH，PYTHONDONTWRITEBYTECODE=1，关闭插件自动发现。sitecustomize 进程审计拒绝网络 connect/bind/DNS 和外根写；CLI 子进程同样加载 guard。必要 junction 由授权精确 helper 创建/删除，仅在本验收临时树内。0 模型/搜索/抓取 HTTP、0 数据库/名单改动。

保留验收工具自身失败：初期漏拷 input-lock 引用的 12 文件、pytest 默认 NUL 日志被 guard 拒绝、旧 basetemp 的 Windows extended path 被 guard 错判，以及名称特殊字符独立探针未同步其 authority claim 引发合法保守阻断。均修正验收环境/预期后重跑；没有算成产品缺陷或伪报通过。前后 129 项源字节校验一致。

隔离副本和临时树将在冻结补丁与薄证据后删除；实际清理数量、剩余与保留补丁见 cleanup.json。原交付仓保持只读，本验收无 root PWF 或其他 runs 写入。
