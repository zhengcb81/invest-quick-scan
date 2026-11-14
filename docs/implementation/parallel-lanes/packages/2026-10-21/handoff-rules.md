# APPLIC-RESOLVE-14 交接规则（2026-10-21 批次）

本文件与 `APPLIC-RESOLVE-14.md`、`manifest.json`、`inputs.lock.json` 共同构成完整授权边界。worker 只能写本卡指定的新 Lab；不得修改共同文档、冻结输入、主控 PWF 或任何其他仓库。接口建议写自己根 `docs/interface-proposals.md`。主线输入变更不追 latest，按本锁实施。

## 一、写边界与输入

- 唯一可写根：`C:/Users/郑曾波/Projects/iqs-applic-lab`（新建，唯一 writer；开工前主控确认空或干净，G0）。
- 只读根：`C:/Users/郑曾波/Projects/invest-quick-scan`（数据根）及一切其他仓库（含 UI-BANK-EXPLORER-13 的 iqs-question-bank-ui-lab）。
- 输入唯一字节清单：`inputs.lock.json`（8 文件：catalog、routing-policy.v2、current 指针、roster-status、4 个模块锁）。`path` 为数据根下 POSIX 相对路径，`sha256` 为原文件 raw 字节哈希，`bytes` 为字节数；**加载前逐文件校验，任何不符立即停止并报告，不得绕过**。只加载锁内文件，不扫描任意本机路径；资源加载不得联网。
- 坐标换算：数据根绝对路径由 CLI 参数显式传入（`--data-root`），不硬编码作者机器；不 `pip install -e` 进共享环境，用项目局部依赖或临时 PYTHONPATH；缺库只报告最小依赖，不自动联网安装。

## 二、共同技术约束

- 仅 Python 3.13 stdlib，零第三方运行时依赖。
- UTF-8 严格 JSON：拒绝重复键、NaN/Infinity、超大输入、非法编码；schema 一律 `additionalProperties=false`。
- CLI：`python -B -X utf8 -m <本包 module> ...`，`--help` 可用；成功 stdout 机器可读 JSON，诊断走 stderr；退出码 **0=有效 / 1=仅评估未定 / 2=输入或语义非法 / 3=越界或输出已存在**。不得把未知/未运行填成 false/0/通过。
- 路径防 `..`、绝对外跳、符号链接/junction 逃逸；测试只用自己的临时根；原始输入不可改写。
- 确定性：排序 entity_id 升序；canonical JSON（UTF-8、ensure_ascii=False、sort_keys=True、separators=(',', ':')、allow_nan=False）；时间戳 UTC。
- 零网络（network_scope=none）：模型 API 调用数 0、付费搜索调用数 0、外部写入 0；执行期证据（grep/日志）优先于文档声称。

## 三、红线（全部反例测试锁死，缺一不放行）

1. 属性缺失 → `unknown`，**绝不**判 `not_applicable`；
2. `not_applicable` 必须有肯定性反证（谓词可判假），无证据 = `not_evaluated`（fail-closed）；
3. `verified` 属性必带锁内出处或所有者引用；`assumed` 必带推断依据，不冒充 verified；无源 = `unknown`；
4. 快照是派生物：键含 `(entity_id, module_id, predicate_version, attributes_version)`，可由（属性×谓词）全量重建且两次重建 sha256 一致；快照 append-only，禁止手改与原地更新；
5. override 一等公民：`operator/reason原话/decided_at/ttl` 落盘、优先于 auto、TTL 过期回归 auto；append-only；
6. 谓词复用 S06 冻结语义，不新建第二规则语言；prose 原文与结构化规则并存互引；
7. 不重算分数、不碰答案与选股、不裁决模块依赖闭包（属 S06）。

## 四、门禁顺序（不得跳步或自签）

| 门 | 内容 | 放行条件 |
|---|------|---------|
| G0 | 主控确认卡、写根干净、唯一 writer | 主控确认 |
| G1 | 设计：四资产 Schema 冻结、谓词语法与三值语义、失效/重建策略、UI 对接形状 | 独立 agent A 产出 design/functional-tech.md |
| G2 | **所有者确认**：prose→谓词映射判读口径、属性分级门槛与来源白名单、override 协议 | `design/owner-approval.json`（decision/原话/timestamp/commit）由**所有者**落盘；agent 不得自签 |
| G3 | TDD 实现：红线反例先行，引擎 + 导出器 | 全测试离线通过，日志入 docs/handoff/logs/ |
| G4 | 按 kind 分批生产（industries→stages→types→overlays→diagnostics），逐条 provenance | **独立审查 agent（非作者）全量复核**：provenance 抽查 + 红线复跑，结论落 review/，findings 纯字符串 |
| G5 | 全量快照 + 失效用例 + UI parity + 所有者验收 | `demo/signoff.json`（decision/原话/approved commit）由**所有者**落盘 |
| G6 | 交接套件 + CLI 校验 + worktree clean | 见第五节 |

## 五、交接套件（唯一交接目录 `docs/handoff/APPLIC-RESOLVE-14/`）

按冻结协议 `docs/implementation/parallel-lanes/handoff.schema.json#1.0.0`（Draft202012，逐层 additionalProperties=false）填：

- **handoff.json**：lane_id=iqs、package_id、status、snapshot（repository/base_ref/base_commit(≥7)/result_ref/result_commit/worktree_before/worktree_after 真实脏态）、scope（task_ids 集合相等 ["S06","W15"]、owned_paths/authorized_paths/changed_paths ⊆ 授权路径、out_of_scope_writes=[]）、interfaces[]（name/version/content_hash/direction/result）、verification（checks 真实命令与结果、**external_writes/network_calls/paid_calls 均为 false 布尔标量**、temporary_roots 带 created/cleaned）、review（status/snapshot_commit(string|null)/findings 纯字符串数组）、open_items[]；可选 next_action。
- **artifacts.json**：每项 `{path, bytes, sha256, role}`，路径相对自己根；只列实际接入的源码/schema/data/报告/测试日志；**不给自身或 handoff 做递归 hash**；禁止占位符（如 `_full_not_stated`/`computed_at_packaging`），sha256 必须逐文件实算 40 字符。
- **tests.json**：command（argv 数组）、cwd、started_at/completed_at UTC、exit_code、passed/failed/skipped、stdout/stderr 原件引用及 raw SHA；RED 反例与整包结果各一份。
- **cleanup.json**：临时根绝对路径、运行前存在性、创建的文件/进程/端口、删除数与字节、结束后剩余、未清理理由；递归删除先验证 resolved 路径在自己测试根内；测试失败也 finally 清理。
- **summary.md / report.md**：做了/没做什么、复用的原接口、运行命令、测试真结果与 skip 原因、已知限制、最小调用示例、版本兼容矩阵、测试环境与清理结果；`production_ready=false`、`financial_qualification_granted=false`。
- **logs/**：真实运行日志（.gitignore 需放行 `!docs/handoff/APPLIC-RESOLVE-14/logs/*.log`）。

## 六、主控校验（worker 不自验放行）

交付后主控在数据根运行（强制 --catalog）：

```powershell
python scripts\parallel_handoff_cli.py --input C:\Users\郑曾波\Projects\iqs-applic-lab\docs\handoff\APPLIC-RESOLVE-14\handoff.json --package-id APPLIC-RESOLVE-14 --catalog docs/implementation/parallel-lanes/packages/2026-10-21/manifest.json
```

要求 exit 0 且 `{"status":"valid"}`。失败 = exit 2：修根因，**绝不绕过或改校验器**。之后主控做范围包含性核对（changed_paths ⊆ 授权路径、review 独立性、日志与快照同 commit）并另行派发独立审查；worktree 保持 clean。

## 七、提交与发布

- 只提交自己仓，不自动推送、不配置远端；handoff 元数据单独 commit，记录真实最终 HEAD，不为让 commit 等于含它自身的 commit 而无穷重写；
- 不声明生产资格：`production_ready=false`、`financial_qualification_granted=false`、模型/付费调用 0；
- 三包级门（S06/W15/U04 的主线集成、真实 owner 接口 E2E）不由本包关闭；总控验收才有权更新主线状态。

## 八、消费对接（UI-BANK-EXPLORER-13）

- 导出器输出该卡 `adapters/applicability_resolver.py` 直读形状（四态枚举与 basis 字段同名）；parity 验收（AC-07）以该卡当前 commit 的 resolver 为准；
- **不得**改 UI 仓任何文件；形状如需演进，写 `docs/interface-proposals.md` 由主控走 UI 卡变更流程。
