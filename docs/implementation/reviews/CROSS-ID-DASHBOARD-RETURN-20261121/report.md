# CROSS-ID-DASHBOARD-RETURN-20261121 交回报告

对应 [施工卡](C:/Users/郑曾波/Projects/investment-dashboard/handoffs/owner-requests/invest-quick-scan/CROSS-ID-DASHBOARD-RETURN-20261121.md)（Dashboard E07/B-04）。IQS 侧接通跨 ID 回到 Dashboard 原挂牌：公开深链按 StockWiki 已核实映射确认原业务返回地址，IQS 原页渲染返回入口，失配与缺证据时单独降级。

**发布 SHA**

| 组件 | 分支 | SHA | 说明 |
|---|---|---|---|
| IQS 服务（8766 现役基线上的候选 release） | `codex/cross-id-dashboard-return-20261121` | `073f82c`（bc388fa → 47c4a7e → 1fd660a → 0fdad97 → 39018f9 → 073f82c） | 服务端映射确认、entity-view 声明、并行预取 |
| IQS 独立 UI（iqs-question-bank-ui-lab） | `codex/cross-id-dashboard-return-20261121` | `cb11311`（3063e38 → 3168c5a → cb11311） | 原页返回入口渲染与 owner 确认采纳 |

UI 仓为本地仓（无远端），验收以其工作树 `src/app`（8766/候选监听静态根）读取该 SHA。

本轮全部证据（回执、浏览器回执、判据）基于 `073f82c` 服务候选 + `cb11311` UI 工作树，隔离候选监听 8769/8768（用后已退出），现役 8766/48766 与另一并行线程的 8767 全程未动。0 模型、0 付费调用（仅公开身份桥只读 resolve）。

## 映射确认协议（施工卡第 1 项）

映射不是静态凭据表，而是**请求时经 StockWiki 公开身份桥的活体核验**（`dashboard_identity_bridge_cli.py resolve`，StockWiki master@7ab8778）：

1. `GET /api/product/entity?id=<r25 实体>&return=<原业务绝对地址>` 收到命名**另一实体**的公司返回时，先按既有 B03 边界校验形态（仅受信回环 authority + 精确 `/company/<ENT>[/<tab>]` + 有界查询键）。
2. 服务用部署配置里的两个工作区根各做一次只读 resolve：r25 owner 工作区（`workspace_root`）解析链接实体；业务工作区（新增配置 `return_bridge_workspace_root`）解析返回地址命中的业务实体及其 `listing_id`。
3. 双方同时满足才确认：两实体 `identity_state=verified`、`resolution_status=resolved`；业务侧显式挂牌必须是 `explicit_listing_selected` 且 `active`；两侧激活挂牌的证券坐标 **(market, exchange_mic, ticker, currency) 完全一致**；canonical_name NFKC 一致。
4. 确认后 `iqs_link.return_to` **逐字节回显**请求的返回地址（Dashboard 候选 b358244 的精确回显校验通过）；任何一步不满足都保持 B03 的 `#/results` 回退，结果、历史与原观测的读面不受影响。
5. `analysis_subject_id` 随返回地址原样保留（Dashboard 自有作用域键，不参与发行人身份核验）。

公开映射凭据（两侧 resolve 回执，含 `lookup_receipt_sha256`）：[bridge-mapping-verdicts.json](evidence/bridge-mapping-verdicts.json)。中微对照：业务 `ENT_a74f8604…`/`LST_c1e34bdb…`（XSHG/688012/CNY，active，verified）↔ r25 `ENT_99deceb6…`/`LST_4b1d9b36…`（同坐标，active，verified），NFKC 名称一致（全角/半角括号折叠），confirmed=true。

**新增公开字段与兼容行为**（施工卡"额外公开字段"项）：

- 配置：`return_bridge_workspace_root`（本机路径，可选）。缺省为空 = 桥未配置 = 跨 ID 返回维持历史 `#/results` 回退，同 ID 与外部拦截行为逐字节不变。`entity`/`entity-view`/`company/result`/`link` 四条路由经同一 `_iqs_link` 确认逻辑。
- `GET /api/product/entity-view` 回包新增**顶层** `iqs_link`（UI 合成返回入口用；投影 `entity` 载荷与 `entity` 路由保持逐字节一致，既有协议校验不受影响）。
- 降级原因具名（仅运维证据，不进冻结 IQSLink）：`return_bridge_not_configured` / `return_bridge_unavailable`（超时、进程不可用、非法回包）/ `r25_identity_unresolved`、`r25_identity_unverified`、`r25_active_listing_missing` / `business_identity_unresolved`（含桥拒绝：无此实体或挂牌）、`business_identity_unverified`、`business_listing_unselected` / `listing_coordinates_mismatch` / `issuer_name_mismatch`。
- 性能：确认在 entity/entity-view 路由并行预取（owner history 读 + 桥双 resolve 与 owner entity 读并发，`_iqs_link` 只 join 同等读数，不改变任何判定）；跨 ID 确认请求现测 0.7–1.6s（暖机），满足 Dashboard 每请求 8s 期限。

## 公开回执（施工卡验收第 1 项）

全部为真实 HTTP GET 回包全文（`captured_at 2026-11-21`，候选监听 8769=已配桥 / 8768=未配桥），汇总：[public-receipt-summary.json](evidence/public-receipt-summary.json)。

| # | 场景 | 请求（摘要） | `iqs_link.return_to` |
|---|---|---|---|
| R1 | **跨 ID 确认** | `entity?id=ENT_99deceb6…&return=http://127.0.0.1:48766/company/ENT_a74f8604…/quickscan?listing_id=LST_c1e34bdb…` | **原地址逐字节确认** [R1](evidence/R1-cross-id-confirmed-8769.json) |
| R2 | 同 ID 回显保留 | `entity?id=ENT_99deceb6…&return=…/company/ENT_99deceb6…/quickscan?listing_id=LST_4b1d9b36…` | 原地址回显（零桥调用） [R2](evidence/R2-same-id-echo-8769.json) |
| R3 | 错挂牌（MongoDB 挂牌挂在原业务返回上） | 同 R1，`listing_id=LST_50d01c61…` | `#/results`，实体回包完整可读（`reason_code=company_result_not_registered` 同前） [R3](evidence/R3-wrong-listing-8769.json) |
| R4 | 映射未核实（`return_bridge_workspace_root` 为空） | 同 R1 @8768 | `#/results` [R4](evidence/R4-unverified-nobridge-8768.json) |
| R5 | 外部地址拦截 | `return=https://evil.example/company/…` | `#/results`，不触碰身份桥 [R5](evidence/R5-external-host-8769.json) |
| R6 | company/result 路由跨 ID 确认 | `company/result?id=ENT_99deceb6…&return=…` | 原地址确认 [R6](evidence/R6-company-result-cross-8769.json) |
| R7 | entity-view 路由（UI 主读面）跨 ID 确认 | `entity-view?id=ENT_99deceb6…&return=…` | 顶层 `iqs_link.return_to` 原地址确认 [R7](evidence/R7-entity-view-cross-8769.json) |

## 真实两跳点击（施工卡验收第 2 项）

隔离组合：Dashboard 候选 `codex/iqs-cross-id-return-20261121@b358244`（backend+已构建前端，`--port 0` 随机端口）、IQS 候选 `073f82c`@8769、StockWiki `master@7ab8778`、`DASHBOARD_E07_CROSS_RETURN=confirmed`。Chromium 真实点击，全部路由守卫（非两个受信源一律 abort，零外泄）：

| 用例 | 实际点击链 |
|---|---|
| **中微跨 ID**（原业务 `ENT_a74f8604…/LST_c1e34bdb…`） | 原业务粗筛页打开 → BFF `quick-scan` 200 且请求带 `return_to=<原页绝对地址>` → Dashboard 回包 `link.return_to==原页地址`、深链带 `id=ENT_99deceb6…&observation=obs_a8b901ee…&result_id=cas_6cab1b94d8f45d42c750&return=…` → 点击"带原始观测上下文进入 IQS"弹出新开 IQS 原页 → 固定结果与"暂定评分题数"渲染可见 → owner history/result 读 200 → **点击"← 返回 Dashboard 公司工作台"回到原业务实体、原挂牌、粗筛页（wait_for_url==company_url，正式公司结果可见）** |
| **同 ID 对照**（r25 `ENT_99deceb6…/LST_4b1d9b36…`） | 同链路实际点击 IQS 返回链接回到原挂牌粗筛页，通过 |

回执：[e07-browser.xml](evidence/e07-browser.xml)（2 passed）、[e07-run.json](evidence/e07-run.json)（`iqs_release=073f82c…`、`pytest_exit=0`、`test_listener_closed=true`）；运行目录与副本在 Dashboard `.test-runs/crossid-e07-20261121/`。

## 测试与回归

- 服务定向：`test_dashboard_return_bridge.py`（12 例：确认/坐标失配/名称失配/挂牌未选中/无激活挂牌/未解析未验证/未配置/传输失败/形态拒绝）、`test_dashboard_entity_iqs_link.py`（含新跨 ID 用例与 entity-view 顶层声明）、entity-view/http/company_result/module_boundaries —— 49+ 通过。
- UI 定向（Node ESM）：`test_cross_id_return_adoption.py`（精确回显采纳、外来回显再校验、形状无效不可采纳）、deep_link/company_return_route/result_pin/company_result_ui/product_ui —— 84+ 通过。
- 服务全量 `-k "dashboard or view_launcher or owner_job"`：763 passed；失败项逐一对照基线 bc388fa 隔离克隆复跑：`test_dashboard_prepare.py` 23 errors、`test_dashboard_owner.py` 2 failed、`prepare_owner_boundary` 1、`iqs_public_integration` 浏览器构建 1 —— **基线同样失败，属环境既有**；delivery 13 failed 在本分支单独复跑全绿（全量并跑的隔离干扰）。本卡改动引入的 module-boundary 违例已消除（公开别名 `owner_environment`/`OWNER_RESPONSE_LIMIT`/`safe_absolute_company_return`）。

## 安全边界保持

- 受信本机路由、原业务实体与挂牌校验（B03 `safe_return_to`/`_safe_absolute_company_return`）逐字未动；外部/不受信地址在形态层即回退（R5），身份桥永不被外部地址触达。
- 桥调用信任面：可执行文件、cwd、两工作区根全部来自部署配置；实体/挂牌 ID 经 `safe_entity_id` 有界校验后以 argv 传入（无 shell）；子进程环境沿用 owner 网关的脱敏 `owner_environment()`；输出 16MiB 上限、超时取 `timeout_seconds`（1–600s 界）。
- 确认不落缓存：每个跨 ID 请求都做当次活体核验（并行化仅改变读取时序，不改变判定与新鲜度）。

## 剩余开口

1. 现役 8766 与 Dashboard 现役仍为旧 release；本卡候选需操作者择机发布升级（发布后在现役上按上表回执复跑即可）。
2. Dashboard 侧 `b358244`（D00 独立工作树）合并与本卡候选同窗发布后，`DASHBOARD_E07_CROSS_RETURN=confirmed` 即为默认行为；合并前现役组合维持 `fallback` 降级显示（原标签页提示），结果与历史照常可读。
3. 药明/MongoDB/阿里尚无 r25 正式结果，跨 ID 返回链路对三家的实际两跳待正式结果登记后按同法复验（协议与中微样本完全一致）。

## 证据索引

| 文件 | 内容 |
|---|---|
| [evidence/public-receipt-summary.json](evidence/public-receipt-summary.json) | 七份公开回执汇总 |
| [evidence/R1–R7-*.json](evidence/) | 各场景请求与完整回包 |
| [evidence/bridge-mapping-verdicts.json](evidence/bridge-mapping-verdicts.json) | 双工作区映射确认/拒绝判据（含 lookup receipt SHA、坐标、NFKC 名称） |
| [evidence/e07-browser.xml](evidence/e07-browser.xml) | Chromium 两跳回归 2 passed（跨 ID + 同 ID 对照） |
| [evidence/e07-run.json](evidence/e07-run.json) | 隔离运行回执（SHA、端口、清理） |
| `runs/crossid-candidate-20261121/` | 候选监听配置与日志（隔离 state，可整体删除） |
