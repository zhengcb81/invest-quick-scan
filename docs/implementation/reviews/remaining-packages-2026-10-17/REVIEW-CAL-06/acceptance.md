# REVIEW-CAL-06 独立接收与隔离整改（2026-10-17）

结论：**原交付不予直接签收；核心安全、绑定和写盘修复候选通过 81 tests，尚有两项共同 carrier 契约欠账，未冒充全包完成。** 总控可先按 CAS 原始字节校验整合十四文件，再统一处理 carrier envelope/稳定业务 hash 及实际 Git/交接绑定。源仓保持只读。

## 来源与原交付

- 源：`C:/Users/郑曾波/Projects/iqs-review-calibration-lab`；intake 记录 HEAD `f697bf3ea0e929fa875a636a6e1d639254ce11d4`、payload `7fccfcc5bfc063a4415a32a9246d895fc5a56d79`。本子任务没有再申请外仓 Git 权限；最终 Git blob/HEAD 核验由总控批量完成，不能把已核工作树 hash 冒充本子任务独立 Git 核验。
- 原锁 raw SHA `968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233`，387 consumer 项全部保持字节一致；源仓原实现/交接/历史独审共 52 文件前后 raw hash 相同。
- 作者记录有独立校准 agent `efdf5ef6-1d3c-4177-9b9e-95c4561454b5`、两名整包 reviewer、两轮记录、修复台账和 final；final 绑定旧 payload 及同一锁。保存的工具返回 ID/记录相互一致，但这不是宿主签名证明，也不覆盖总控修复。
- artifacts 宣称已删除 `.gen_artifacts.py`，确为缺项；没有重造临时文件。候选移除该声明并纳入正式历史 review 文件，明确标为历史而非新补丁通过证明。

## 已修复的实质问题

1. **RC06-C01 / P1：先执行代码、后核锁。** `configure_frozen` 在 expected lock SHA 验证前导入冻结包；正确 expected SHA 下篡改包 `__init__.py` 原仍 exit0，错误 SHA 原也先写 canary 再拒绝。原锁校验只核三份业务数据，未核全部执行 consumer。新增标准库 bootstrap，先核 expected raw SHA、387 consumer 字节、安全相对路径、重复/大小写碰撞、链接和未锁定执行文件，再导入冻结工具；原 frozen 代码不变。
2. **RC06-C02 / P1：缓存模块来源污染。** 原只记录 module.__file__，不拒绝外国 standard_answers。现在 configure 前后核实际来源，拒绝外国/旧根缓存；公开 configure 也先验证 consumer，不靠 CLI 单独保护。
3. **RC06-C03 / P1：哈希自洽不等于内容绑定。** 原可替换实际公开 question/answer/evidence，重绑 slot/private/assignment 声明 hash 后被接受；现在按实际 casebook 重建逐项公开投影核对。
4. **RC06-C04 / P2：private 分类与匿名映射可篡改。** 原 family/phase 可改写统计分组，anon_to_case 可置换导致报告错标；现在核 case_id、family、phase、pair、origin、reason 与实际 casebook，并核 entry 与映射一致。
5. **RC06-C05 / P2：compare 不重新校验 casebook，context 只验长度。** compare 现在先跑原 casebook validator；三个 context SHA 及 cutoff 必须与实际 context 一致。六步公开 CLI 中把所有相关 hash 重新绑定后，作者自标 calibrated_by=author 仍被拒绝。
6. **RC06-C06 / P2：命题重复及分类/争议被忽略。** 重复 claim_key 原静默取最后一个；assertion_kind 原不参与校准，disputed=true 可计 clean match。现在拒绝重复、比较 fact/inference，并把明确争议保留为争议；争议不能掩盖真正严重错误。
7. **RC06-C07 / P2：路径及失败清理。** 输入/输出检查补上 Windows junction 分支；省略 --lock 也保护实际所选锁目录；partial JSON、assign private 写盘失败、compare 写盘失败清理本次新建产物，既有输出/输入保留。
8. **RC06-C08 / P2：交接缺项/历史审查误用。** 移除临时 generator 缺项声明；旧 review 作为历史保留。候选 handoff 为 checkpoint，实际修复提交和新验收绑定由总控完成，不能沿用原 passed 来宣称补丁已受审。

金融 expected、58 个案例、原题/schema/metric、387 输入文件均未改。没有另写金融 scorer、费用账本或身份解析器；不授予生产/金融/rating gold 资格。

## 实测与证据

- 原交付 baseline3：58 passed。
- provenance_red2：4 failed、58 passed，其中重复 lock 原 validate 探针先遇到 context 拒绝，不足以证明该项；改用原源 CLI/bridge 的自有隔离副本 public build 后，原正确 SHA+重复路径确实 exit0 且生成 casebook，见 `original-duplicate-red.json`，修后拒绝。
- `binding_red1`：6 failed、62 passed，三个公开内容替换、family/phase 改写、匿名映射置换均为真实反例。
- `output_red1`：2 failed、70 passed，私有写失败遗留 public bundle、部分写失败遗留 JSON 均为真实反例。
- 最终固定代码 `controller_final3`：**81 passed、0 failed、0 skipped，97.30s**。实际 argv/cwd/exit 见同名 result.json，stdout/stderr 保留。
- 独立 public CLI `controller_cli_chain_v2`：build→validate→assign→compare、已有输出 exit3、完全重绑后的作者自标 casebook exit2，六步均符合预期。58 个 synthetic labels 全匹配只证明工程闭环，真实 reviewer/model accuracy 为 null。
- 逐条审阅 50 个金融语义 case、8 个 format-negative 与 12 对关键含义差异；覆盖 OCF/FCF、维护/全部 capex、净利/营业利润、单位/期间/主体、镜像源、推断越界、低谷与永久损害、多命题与 honest insufficiency。expected 仍是经历史独审校准的 synthetic 标签，不重新认证其所借用的真实公司数据，也不赋予主观分数唯一 gold。

初期 Windows 长路径/guard 环境失败及 controller 探针改正日志全部保留。provenance_green2 等中间运行期间有后续隔离源修改，不用来证明最终 CAS；最终 controller_final3 的代码/测试字节之后未再改动，后续只写行为说明和交接元数据。

## 尚未关闭的共同契约问题

- **RC06-O01 / P2：通用 envelope 不完整。** 旧 public_assignment/private_map/report 等未统一具备 package_version/source_context/limitations/content_sha256/qualification，也没有完整独立机器 JSON Schema。当前函数闭合/部分校验不能等同共同 interface 全面通过。
- **RC06-O02 / P2：跨机器重建稳定业务 hash 未实现。** casebook.expected_context.inputs_root 是实际绝对路径，进入旧完整 casebook fingerprint，再被 assignment 引用；搬迁后能运行不等于重建业务 hash 相同。需要明确兼容设计，不能默改旧 fingerprint 含义或把已知路径伪标 unknown 来凑结果。

两项已报总控；本次候选不擅自扩大旧 1.0 carrier 设计，也不把这些欠账写成 passed。root 可继续设计新稳定 carrier/可选向后兼容字段并另做受影响测试。`fixed-payload.cas.json` 明列 open_contract_findings。

## 隔离、清理与限制

所有执行均来自本 acceptance 根的隔离副本。最小 env 去除真实 secret，自己的 HOME/TEMP/APPDATA、禁止 pyc/cache 外写，进程审计拒绝 connect/bind/DNS 和外根写，子进程只准 Python 并继承 guard。0 付费调用、0 网页抓取、0 API key 读取、0 数据库/名单/源仓写。

本验收未重新动态创建 Windows junction：默认沙箱连自有根的 New-Item Junction 也拒绝，未再请求额外提权。junction 分支静态核验且沿用 is_junction 原生检测，不把其他包的真实 junction 实测冒充本包动态测试。需要物理 junction 复验可由总控在既有有界提权批次补做。

冻结补丁和薄证据后仅删除本 acceptance 自有 isolated 树，具体文件/bytes、剩余、保留项见 cleanup.json。完整源仓和冻结 consumer 保持原样；并行源仓未受影响。
