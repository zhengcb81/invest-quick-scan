# THREE-MARKET-COVERAGE-20261121 交回报告

对应 [施工卡](C:/Users/郑曾波/Projects/investment-dashboard/handoffs/owner-requests/invest-quick-scan/THREE-MARKET-COVERAGE-20261121.md)（五卡验收第 4 项，B-04 / E07）。IQS 主责结果登记及回跳协议，StockWiki 主责公开身份凭据。

**发布 SHA：** IQS `master@296ab84`（8766 现役 release，本轮零代码改动，receipt 见 `.runtime/iqs-e20-296ab84/listen-8766.receipt.json`）；StockWiki `master@7ab8778`（公开身份接口 `dashboard_identity_bridge_cli.py`、onboarding facade、issuer proof）。

## 覆盖总表

| 公司 | 业务工作区原实体/挂牌 | IQS r25 身份凭据 | 正式结果 | 草稿 | 历史 | 跨 ID 解析与回跳 |
|---|---|---|---|---|---|---|
| 药明 603259 | `ENT_2a41e04d` / `LST_f26e4cea` | r25 `ENT_3ac097b9` / `LST_80ed7414`（verified rev2 · XSHG/603259/CNY · active · bridge resolve `resolved`） | 无 —— `company_result_not_registered` | 仅旧版草稿（见具名状态） | 0 | 两端凭据齐备；r25 路由 `partial`（无结果可定位，G-IQS-01 具名保留） |
| 阿里 09988 | `ENT_e4d964f0` / `LST_591474dd` | **本轮补齐**：r25 `ENT_e4d964f0` / `LST_591474dd`（verified rev2 · XHKG/09988/HKD · active · bridge resolve `resolved` · `owner_evidence` 现行） | 无 —— `company_result_not_registered` | 无 | 0 | **真实 007787a 组合栈验证通过**：`workspace_listing_unresolved` 消除，公司视图保留原实体/挂牌；坐标 (HK,XHKG,09988) 唯一匹配 + 名称 NFKC 一致 |
| MongoDB MDB | `ENT_41250504` / `LST_2d86780f` | r25 `ENT_b47ecd1e` / `LST_50d01c61`（verified rev2 · XNAS/MDB/USD · active · bridge resolve `resolved`） | 无 —— `company_result_not_registered` | 无 | 0 | 两端凭据齐备；r25 路由 `partial`（同药明） |
| 中微（对照） | `ENT_a74f8604` / `LST_c1e34bdb` | r25 `ENT_99deceb6` / `LST_4b1d9b36` | `cas_6cab1b94d8f45d42c750` formal（适用 36 · 缺证据 29 · 期间 2026-11-08） | — | 1 | 浏览器同 ID 往返复跑通过（见下） |

公开复读（2026-11-21，现役 8766，`GET /api/product/company/result?id=…` + `GET /api/product/company/history?id=…`）：三家目标均 200 + `company_result_not_registered`、history total 0；中微 200 + `cas_6cab1b94d8f45d42c750`、history 1，与登记时一致（`no_refresh`）。逐项回执：[iqs-public-reads.json](evidence/iqs-public-reads.json)。

## StockWiki 公开身份凭据（施工卡第 1 项）

公开接口 = StockWiki `dashboard_identity_bridge_cli.py`（`search` / `resolve`，`--root` 指定工作区）。前后两次全量取证在 [identity-bridge-receipts.json](evidence/identity-bridge-receipts.json)：

- 药明 / MongoDB：业务端与 r25 端 `resolve` 均 `resolved`（explicit_listing_selected，各自挂牌 active）。映射凭据即两端 receipt 对（canonical_name 一致、坐标一致、identity_state verified）。CWP 侧发行人证明（`cn-primary-uscc/1`、`sec-primary-dei/1`）沿用 2026-11-21 上午验收实物（`.test-runs/five21/candidate.json` 的 `*_proof`，binding 均 `verified`）。
- 阿里：施工前业务端 `resolved`、r25 端 `no_match`（缺口证实）；本轮补齐后 r25 端 `resolved`，凭据与业务端同一实体/挂牌 ID（挂牌 ID 由 security 坐标确定性推导，`listing_id_for_security`）。

### 阿里 r25 身份补齐过程（onboarding facade 全链留痕）

全部经 StockWiki 公开 `dashboard_onboarding_cli.py`（`--root` = r25 owner workspace），无任何手写库：

1. `submit` → `ONB_f8bd7c06-9a7f-416c-89c0-940f6a1fcdab`（idempotency key `THREE-MARKET-COVERAGE-20261121-alibaba-09988-r25`，receipt sha `bffd234e…788cc`），初始 `needs_input / no_owner_listing_match`（缺口具名）。
2. 第一次 `stage-import`+`bind-proof`（payload 携带 `formal_stockwiki_profile="09988.HK"`，`EVI_d88098a8…`）：拒 `owner_store_refused: research profile configuration unavailable` —— r25 工作区无研究 profile 配置，该字段是跨域研究绑定声明，超出本卡身份范围，改为不携带（置 null），未把业务配置复制进现役工作区。
3. 第二次（r25 当前 rev3 回执 `IVR_45ad14e0…`，`EVI_dffd41ae…`）：实体已保存、回执阶段拒 `receipt_reanchor_requires_atomic_record` —— 该回执是 research-profile-binding 流程产生的 re-anchor 回执（supersede reason：`research_profile_binding dashboard-f2-owner-bind-…`），其 transplant 需要 re-anchor 通道且先录 base，公开通道不可达。已按 facade 恢复指引处理：**将 `scan.sqlite` 恢复为本卡开工前字节备份**（SHA `e4e4e031…ffc4` 逐位一致，实体行移除；onboarding journal 保留原样不删），改用 rev2 直录回执。
4. 第三次（rev2 实体 + 直录回执 `IVR_20261115_HKEX_FY2025`，`EVI_9792abec…`）：`bind-proof` 返回 **`completed`**（receipt sha `00660cbe…60d3`），owner verdict：`resolved` + `ENT_e4d964f0` + `LST_591474dd`。

回执与证据内容说明：rev2 与 rev3 回执的实质凭据完全一致（canonical_name、entity、evidence_ref、incorporation_country、listing_attributes、security_attributes、same_legal_issuer 逐字段相同；diff 仅 receipt_id/revision/reanchored_from/decision_ref 四个回执自身字段），evidence_ref 均为 HKEX FY2025 年报 `https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0626/2025062601065_c.pdf`（decision_ref `owner-2026-11-15-alibaba-hkex-fy2025-annual-report-8ab12348`）。r25 记录因此持有与业务端当前证据相同的发行人凭据；差异仅是业务端其后的 research-binding re-anchor 未（也无法）移植，已如实记录。

写盘范围（`backups/three-market-20261121/` 留开工前全量字节备份 + SHA）：

| 库 | 开工前 | 当前 | 说明 |
|---|---|---|---|
| `scan.sqlite` | `e4e4e031…ffc4` | `4c5e1abb…a109` | 阿里实体+证券+来源绑定（rev2，来源绑定/证券与业务端逐字段同值） |
| `identity_receipts.sqlite` | `11302b1e…4026` | `66eb7347…fb58` | 阿里 `IVR_20261115_HKEX_FY2025`（active） |
| 其余四库（观测/正式/主体/市场注册） | — | — | 逐位未变 |

universe 未动：`UNI_IQS_APPROVED_214_20261025` 仍 215 名成员，阿里为 identity-only 记录、非成员；筛选页与指标快照不受影响。

## IQS 盘点与登记（施工卡第 2 项）

盘点范围与证据：[coverage-inventory.json](evidence/coverage-inventory.json)。

- **正式**：`company_assessment_registry` 仅 1 行（中微 formal）。三家目标均无正式结果。
- **草稿**：唯一相关草稿是 `runs/thin-scan-wuxi-2026-10-18/answers.json`（2026-10-18 旧工作台导出，`draft:true / verified:false`，24 检索、IQS_01–24 旧格式答案，无原生观测 payload/来源绑定）。**具名状态：不可经原生 owner 登记链发布**——现行登记要求冻结 release + 原生观测绑定（publish-release → import → record-authority → register），旧格式无对应绑定；其现有读回方式为同目录静态导出（`index.html`）。dashboard-runtime / u25-live / r25-live 各作业目录经全文检索，三家均无准备包、扫描或交付工件。
- **历史**：r25 观测库 156 条，分属中微 37、宁德 44、腾讯 38、微软 37；三家目标 0 条。
- **登记**：无可发布结果，owner 登记流程本轮未触发（中微原登记不动）。三家进入正式覆盖需先有 r25 原生扫描；按施工卡该路径走现有 owner 预算与恢复流程，**本轮未发起任何模型/付费调用（0 模型、0 网络）**，待操作者确认预算后沿现行 admission/恢复链执行。
- **阿里**：identity 补齐后与其他两家同态（`company_result_not_registered` 具名可见），`workspace_listing_unresolved` 不再由 IQS 数据侧产生。

## 跨 ID 回跳（施工卡第 3 项）

- IQS 侧 r25 路由投影（`iqs_link`，`iqs.dashboard.owner/1.0.0`）在 result/history 读面按实体发布，`return_to` 仅接受白名单本地 Dashboard 路由；三家目标在无结果状态下路由为 `partial`（G-IQS-01 具名），中微 `available`——"回跳暂不可用时保留结果与历史、导航单独显示具名状态"的现状行为与卡一致，无需改码。
- 对应关系表（业务挂牌 ↔ r25 挂牌 ↔ 深链）即覆盖总表。**真实 007787a 组合栈验证**（Dashboard main 检出即 `007787a`，backend/contracts 无脏文件，`build_ports(mode="owner")` + TestClient，只读）：四家 `GET /api/v1/companies/{原实体}/quick-scan?listing_id=…` 全部 200 且 `company_preserved=true`——阿里 reasons 只剩 `G-IQS-02_company_result_not_registered` + `G-IQS-01_navigation_unavailable`（**`G-IQS-02_workspace_listing_unresolved` 消除**，即跨 ID 解析经真实 adapter/DTO 栈成功）；药明/MongoDB 与上午验收读数逐项一致（listing resolved + result not registered）；中微对照 formal `cas_6cab1b94d8f45d42c750`、history 1、link available、return available 不变。回执：[combo-probe-quickscan.json](evidence/combo-probe-quickscan.json)，探针：[combo-probe.py](evidence/combo-probe.py)（临时数据目录用后已删，Dashboard 仓无残留）。
- **中微同 ID 对照（浏览器）**：现役 48766 公司粗筛页显示正式结果 `cas_6cab1b94d8f45d42c750`（适用 36/缺证据 29/期间 2026-11-08）与深链（`link_status=available`，return_to 确认）；进入 8766 深链后定位原观测 `obs_a8b901ee…`（published，DUPONT_01）并列 36 条记录；返回链接回到原公司页（原实体 `ENT_99deceb6`、原挂牌 `LST_4b1d9b36`、IQS 粗筛 tab）。回执：[amec-browser-roundtrip.json](evidence/amec-browser-roundtrip.json)，截图 [amec-return-roundtrip-20261121.png](evidence/amec-return-roundtrip-20261121.png)。方法说明：Dashboard SPA 点击被轮询重渲染拦截（locator 超时两次），两跳按快照证实 href 直接导航（用户结果等价，返回链接 count=1 已验证）。

## 证据索引

| 文件 | 内容 |
|---|---|
| [evidence/identity-bridge-receipts.json](evidence/identity-bridge-receipts.json) | 施工前/后两端公开身份 receipt 全文（search+resolve ×3 家） |
| [evidence/alibaba-r25-import-payload*.json](evidence/alibaba-r25-import-payload-noprofile.json) | 三次 stage payload 原件（含 profile / rev3 / rev2 定稿） |
| [evidence/iqs-public-reads.json](evidence/iqs-public-reads.json) | 四实体公开 result/history 读回 |
| [evidence/coverage-inventory.json](evidence/coverage-inventory.json) | 正式/草稿/历史盘点 + 写盘 SHA + universe 状态 |
| [evidence/amec-browser-roundtrip.json](evidence/amec-browser-roundtrip.json) | 中微同 ID 浏览器往返回执 |
| [evidence/combo-probe-quickscan.json](evidence/combo-probe-quickscan.json) | 真实 007787a 组合栈四家 quick-scan 读回（阿里 unresolved 消除） |
| [evidence/combo-probe.py](evidence/combo-probe.py) | 组合栈探针脚本（只读，可复跑） |
| [evidence/amec-return-roundtrip-20261121.png](evidence/amec-return-roundtrip-20261121.png) | 返回原公司页截图 |
| `runs/r25-live/owner-workspace/backups/three-market-20261121/` | 开工前六库字节备份 |

## 剩余开口

1. 三家的正式结果与历史读回需 r25 原生扫描（owner 预算与恢复流程；未发起——按卡新增评估走现有预算与恢复流程，本轮零模型/付费调用）。
2. 阿里如需进入筛选/名单，需另走 membership request 权威流程（本卡未含，未动 universe）。
3. D00 验收可按其关卡复跑正式组合；本报告已交付真实 007787a 组合栈只读验证（见跨 ID 回跳节）。逐家身份与覆盖状态按卡可独立验收。
