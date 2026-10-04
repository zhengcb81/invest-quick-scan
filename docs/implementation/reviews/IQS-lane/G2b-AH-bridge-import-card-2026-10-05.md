# G2b A/H Bridge 导入批次施工卡（写前报告，2026-10-05）

## 背景与授权
- A/H 桥草稿表 122 行已由 owner 签收（`docs/implementation/reviews/IQS-lane/G2b-AH-bridge-draft-2026-10-04.json`，`status=SIGNED`，`decision_ref=owner-2026-10-04-g2b-ah-bridge-signoff`）：issuer_id 按现态签（null + `not_found_in_sources`，后补）、30 对 dual_code 未确认项剔除、4 处 H 代码纠偏接受、002142 证伪接受。
- owner 通授覆盖（2026-10-03「全部剩余卡一次性授权」），条件=每批写前报告+独立审查；本卡即写前报告。G2b 最后一项实物：A/H 证据已签、桥表未建。

## 目标（单一 owner：StockWiki 线，总控 IQS 验收）
把 owner 签收的 122 行"同一发行人 A/H 挂牌对证据"导入 StockWiki quick_scan 库的**桥证据表**，可幂等重放、可只读核验；**不**创建 entity/security/member、**不**改变 scan_eligible、**不**做任何身份合并决策。

## 语义与边界
1. 新表 `quick_scan_issuer_bridge`（v4→v5 加法迁移，DDL 全部进 `quick_scan_schema.py`——store 现 922 行，1000 硬门不得突破）：
   - 内容寻址幂等：`content_sha256` 唯一；同 sha 重放=no-op 计数，同对异 sha=conflict 拒绝。
   - 字段直接映射签收行：cn/hk listing_key 与 ticker、双语名、`issuer_id`（恒 NULL 入库）+`issuer_id_status`、evidence_url/kind/verification_source、retrieved_at（UTC）、confidence、notes、import_batch_id、decision_ref。
   - 拒绝项（命名错误码）：文件缺 `status=SIGNED` 或 decision_ref 不匹配、行数≠申报值、任一行缺 evidence_url/content_sha256/retrieved_at、尝试写入非空 entity_id 或 scan_eligible。
2. 导入≠VerifiedIssuerBridge 实体化：schema 合同 `BRG_*/ENT_*/SEC_*` 的完整桥要求 entity_id 与 security_ids——本批只落**对证据**，entity 绑定留待后续 verified issuer 导入时回填（该回填是另一批次，不在本卡）。
3. CLI：`stockwiki issuer-bridge-import --source <signed.json> [--report <path>]`，规范 JSON stdout、命名拒绝 exit 2、零 traceback。
4. 只读核验子命令 `issuer-bridge-report`：行数、sha 清单摘要、按 confidence 分布、与源文件 diff=0 证明。

## 允许改动文件（StockWiki）
- `stockwiki/quick_scan_schema.py`（+v5 DDL）
- `stockwiki/quick_scan_store.py`（仅当必要的数据操作方法；守 <1000 行，否则移新模块）
- 新增 `stockwiki/quick_scan_issuer_bridge.py`（导入/核验逻辑 + CLI handler）
- `stockwiki/cli_parsers/quick_scan.py`（+2 子命令注册）
- 新增 `tests/test_quick_scan_issuer_bridge.py`
- `.planning/sw-ident_handoff_2026-09-30.json`（authorized_paths 追加，引本卡+通授）

## 测试与门（TDD，先红后绿）
- 正例：122 行全量导入 exit0、计数/批量 id/decision_ref 落库；幂等重放 inserted=0。
- 负例：篡改任一行 content_sha256、缺 SIGNED、行数不符、夹带 entity_id、同对异 sha。
- 迁移：v4 真实库升级 v5 保数据（空库与带 216 staging 库两态）。
- 门：ruff / 触及文件 black(100) / `check_all.sh` 全绿；独立审查两轮；5 文件 SHA-256 记档；StockWiki 本地提交（无 remote，决定 7）。

## 证据与记录
- 验证日志 + 本卡 + 审查报告 → `docs/implementation/reviews/IQS-lane/`（IQS 仓）；PWF task_plan 补 Phase 75 节。
