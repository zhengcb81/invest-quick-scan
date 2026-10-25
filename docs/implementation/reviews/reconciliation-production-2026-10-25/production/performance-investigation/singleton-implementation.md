# 原 SDK singleton 已知无效答案接续：实现交接

实现者：`/root/review_bank21`（总控明确另行指派本修复；本补丁由 `/root/fix_bank21` 独立审查，不以实现者自检代替独审）。本文件不声称真实 IQS_05 已重试、已封存或已通过金融准确性验收。

## 根因与范围

只读核实原账本时，该工作是 generation1/epoch3、最新 attempt 为 `response_available`、原 safe1、checkpoint0；`quick_scan_question_pack_member` 对该 work 的行数为0。原 `_physical` 只认 pack，因而即使原 SDK singleton 的不可变 intent、原 safe、费用与主体发送回执齐全，仍拒绝 `owner_work_frozen_native_pack_required`。等待真实租约到期并不能补出 pack 证据；不能手插 member 或把语义无效答案改成有效分数。

本实现仅修改 StockQA：

- `src/utils/quick_scan_known_outcome_journal.py`：在无 pack member 时委托 `_single_physical`，旧 pack 分支和返回字段不变。
- 新增 `tests/unit/test_known_outcome_singleton.py`：23 条原 SDK + 临时 SQLite 回归。HTTP 和 owner authority 明确是合成夹具，不代表实际公司答案或真实授权 golden。

## singleton 的严格证明

新载体明确声明 `proof_protocol=stockqa.native_singleton_known_response/1.0.0`，包含 research task/intent/绑定 SHA；不含 `pack_id` 或 `pack_manifest_sha256`，不伪装成 pack。既有 work-decision 外层信封保持1.0，因为其 physical 是由原 QA 派生、owner 再独立核验的字典，没有封闭 pack-only 字段合同；新载体在自身协议字段显式版本化。

原同一事务重验：唯一原 native attempt→单一 work 的 intent 关联、原规范编码/绑定 hash、请求 payload SHA、原不可变 receipt 的 intent 锚；费用必须为同 attempt/route/model 的 completed+settled 原预算；原 response 模型身份、receipt/body hash、HTTP/请求回执对应；context2、原 owner binding、实际主体 pre-send receipt 与完整派生 dispatch request 相等；当前 epoch 仍匹配原 attempt。没有原 intent、context/owner proof 或费用未定等情况仍拒绝。

通用 `resolve_known_response` 的原 lease 到期、原 diagnostic/response 绑定、无 checkpoint、两次当前权限核验和幂等守卫不变。记录 logical failed 与 retry 意图不增加 HTTP、不新建 generation、不重置费用；新 generation 仍须原 owner refresh1.2/admission。原表重开校验可能传入 `QuickScanWorkStore` 类，故 intent 纯编码/hash核验在原连接中完成，不另开连接调用实例 getter。

## 实测证据

- 产品 RED：`singleton-product-red.txt/.xml`，原 SDK 单题被 pack-only guard 拒绝。早期 `singleton-red.*` 是测试夹具时钟误用导致的 admission 失败，已纠正，不能算产品 RED。
- 中间失败日志均保留：包含原 MiMo 协议夹具纠正、receipt wrapper 层读取修正、重开时 class 校验修正，以及专用 guard 环境配置失败。它们不被最终成功覆盖。
- 最终五文件在真实原 `tests/fixtures/delegated_guard/sitecustomize.py` 下运行，去除所有 API 环境变量，cwd/log/temp/SQLite 全在自有 runtime：**92 passed，97.18秒，无 skip/deselect**。`singleton-guarded-final.txt/.xml`。
- 两个真实进程 guard attestations 在 `singleton-final-proof.json`；父子网络调用、外部 SQLite、外部文件写均有实际被拒证据。测试使用 mocked SDK wire，无供应商请求。
- 新例包含 derive→inspect 完整对象回读、resolve→retry→原 owner-control 投影 generation2、重开幂等、缺证明/费用/活跃租约/假授权/撤权拒绝、篡改与重新 hash intent 仍被原 receipt 锚拦截。
- 原 pack、work-decision inspect、authority 与 apply 旧回归同时通过。独立审查者 `/root/fix_bank21` 已在 `engine-review/singleton-known-outcome-final.json` 判定 passed：原 pack AST 除无 member 分流外保持不变；下游 shape 兼容；对实际原 CATL 账本的公开 derive/inspect 只读回读成功、request 相同、数据库不变及0 API。该结论未执行原 owner confirmation/resolve，也不证明新 generation 已创建；不由本实现报告代签。

## 冻结与清理

| 文件 | SHA256 |
|---|---|
| StockQA `src/utils/quick_scan_known_outcome_journal.py` | `75b8711b5a8678759c940c6862ad41f52c81a2a79224735ae34bb3b8cd068cd9` |
| StockQA `tests/unit/test_known_outcome_singleton.py` | `2d216c07846a67bbf92149e7a549b3b5d161834fd89463b04f275486e7603a04` |
| 最终 XML | `3da794b2b5785cd1c702ac4ae9c5aea9cfaa8b4c51fd0fd37351a373e0354baf` |

`singleton-cleanup.json` 记录10个本实现明确创建、已核绝对边界且无 reparse point 的临时根全部删除；保留薄日志/XML/哈希/guard证据。早期未加专用 guard 的测试会使用导入模块的相对 `logs/stock_qa_20261025.log`；未取得该共享日志的运行前基线，也可能有其他 writer，因此没有删除或回滚该日志，更不宣称清理了全机/其他进程文件。最终套件的日志完全在已清理的自有 runtime。

实际原 `runs/r25-live/work.sqlite` 未被本实现写入，原 safe/预算/lease 均未修改；没有真实 API、下载、时钟改动或私有 handle 接管。公开下一步草案见 `retry-unusable-answer-plan.py.txt`，须总控核对实际 diagnostic、原 owner 预览和真实 terminal action，再执行。真实 terminal 若由 root 自动操作，应如实记录已授权自动操作，不能假称人类手输。

## 正常提交钩子格式整理后的绑定

总控正常 hooks 首轮仅由 black 整理两文件、isort 整理新测试；mypy/detect-secrets 已通过，首轮没有 commit。等待该进程终态后，我从 `f88b53e` 原 blob 和冻结 helper 重建了格式前产品文件，精确复现上述 `75b8711…`；格式前测试也精确复现 `2d216c0…`。`singleton-after-hook-ast.json` 记录产品全 AST 相同；测试仅 import regrouping，同作用域 import alias 集合与全部非 import AST 相同。这不是对任意 import 顺序改动的抽象语义等价承诺。

格式后仅重跑新增 **23 passed/15.37秒**，使用原 guard、去除 API 环境变量、自有 cwd/log/temp；未重跑92项套件。证据为 `singleton-after-hook.txt/.xml`、`singleton-after-hook-guard.json`；`singleton-after-hook-cleanup.json` 记录精确自有 runtime 已删除。

| 格式后文件 | SHA256 |
|---|---|
| StockQA `src/utils/quick_scan_known_outcome_journal.py` | `48a6257956defcd57fef2f0da18a68689227b5267002db496a7bb3aaa797801a` |
| StockQA `tests/unit/test_known_outcome_singleton.py` | `581ec30c441f81ea3bb3add55a399e32fc9d4f31046f376c0869fbfe2d8340f5` |
| after-hook XML | `3a7491c2c3c94903fb09667e62e06ee40b4ee9238f98c41405f8ffcb4c1884b5` |

格式前独审/测试 SHA 保留为历史，不覆盖；提交后的实际 commit 由总控另行绑定。此阶段仍未执行真实 owner 决策、变更原账本或调用 API。
