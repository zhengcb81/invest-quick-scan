# G2b D 类过渡播种报告（transitional seeding，不关闭 D）

日期：2026-10-04。依据：owner 决定「D 两步走」——第①步=我先做过渡播种（申报散文/docling 日期抽结构化行），第②步=owner 后补交易所官方登记表；**D 卡在官方表到位前保持 open**。执行者：IQS 总控，全程只读零网络。

## 1. 产物

| 文件 | 说明 |
|---|---|
| `G2b-D-seed-extract.py` | 可复跑提取器（stdout JSON）；读 company-wiki `catalog.sqlite3`（mode=ro） |
| `G2b-D-transitional-seeding-2026-10-04.json` | 播种数据：**59 行**（listed 58 + delisted 1）、22 份文档、三重噪音过滤计数、逐行溯源 |

## 2. 方法与三重负门

- 正模式6条：交易所名+上市、上市日期:DATE、DATE+上市、摘牌/终止/退市多种邻接（简繁+无冒号）。
- 负门（命中即剔除该行）：①法律实体噪音 `上市規則/上市實體/上市機制/擬上市…`（7+3+3+2 命中）②**财政/报告噪音** `截至X止年度/年度報告/關鍵審計/公允價值…`（17 命中——这是散文抽日期最大的假阳性源）③窗口内无上市/摘牌动词（0 残留）④`上市文件/招股`（各1）。
- **归属诚实**：只有当匹配窗口**本身包含**文档实体名时才填 `entity_names`（标 `sentence_confirmed`），否则留空并标 `document_level_unverified`——实测57/59 是后者（正文用"本公司"自指，不点名），**绝不把文档主体强挂到日期上**（早先版本把美团年报里"理想汽车上市"挂到美团头上，已修）。
- 每行带：`document_id/span_id/excerpt/document_title/published_date/source=company-wiki.evidence_spans`、`confidence=transitional_pattern_unreviewed`、`review_status=unreviewed`、**`closes_category_D=false`**。

## 3. 抽到什么（人工抽检）

- 真例（listed）：理想汽车 2021-08-12 联交所上市、股份 2018-09-20 香港主板上市、**金山雲「上市日期」指 2022年12月30日**（定义式，最干净）、2022-12-30 主板成功上市、贝壳 2020-05-08 纳斯达克上市（同句还有 2022-12-30 港股第二次上市）。
- 真例（delisted）：**英方股份 2017-12 新三板摘牌**（全库唯一退市命中——公司自己的年报极少自述摘牌，退市语料天然稀缺）。
- 残留轻噪音（如实记录）：个别地址/上市文件句（已尽量过滤）。

## 4. 为什么这**不能**关闭 D（诚实边界）

1. **非权威源**：这些是"申报散文里的说法"，交易所官方登记表（生效日 + `source_sha256`）才是 D 类契约要求的证据；种子只能用于**交叉核对**，不能替代。
2. **覆盖极窄**：59 行来自 22 份文档（本地仅有的申报语料），216 候选里绝大多数没有覆盖；退市几乎为零。
3. **未复核**：`review_status=unreviewed`，无 owner/人工确认；`entity_attribution` 多为文档级未验证。
4. **docling 表格路径**：56 份文件里结构化表格日期仅命中1条（发行期申报非证券主档），不构成规模来源。

**关闭 D 的唯一路径**：owner 提供 HKEX/cninfo/SEC 官方上市/退市登记（字段规格见 `G2b-evidence-hunt-2026-10-03.md` §D：market/exchange_mic/ticker/event_type/effective_from(+to)/reason/source_url/source_sha256/retrieved_at，覆盖至少216），到货后与本种子交叉核对再签收。

## 5. 复现

```
python docs/implementation/reviews/IQS-lane/G2b-D-seed-extract.py \
  > docs/implementation/reviews/IQS-lane/G2b-D-transitional-seeding-2026-10-04.json
```
