# verified 身份证据审计 — 2026-10-18

只读审计：对 209 个 verified 实体，逐条重算 IVR、核对法人名、校验归档证据哈希。

## 结果

| 项 | 数量 |
|---|---|
| verified 实体 | 209 |
| 通过 | **207** |
| 失败 | **0** |
| 预先存在、证据在早期 run（Alphabet、CATL） | 2 |

- 200 家 cninfo：归档响应（`cninfo-profiles.jsonl`）重算 sha256 一致、公司全称与实体名一致、IVR = sha256("cninfo:"+entity_id+":"+name) 一致。
- 7 家 SEC：完整 submissions 响应（`sec-submissions/*.json`）sha256 与归档一致、registrant name 与实体名一致、ticker 在列表中、IVR = sha256("sec:"+entity_id+":"+name) 一致。
- 万科A：SZSE 年报 PDF URL + IVR = sha256("verified:"+entity_id+":2:"+name) 一致。
- Alphabet 与 CATL 是更早的 verified，证据在之前的 run，不在本归档范围。

## 边界

- 只审“身份证据”，不判断财务准确性、评分资格或投资结论。
- 归档目录：`docs/implementation/evidence/verified-identity-2026-10-18/`（cninfo 200 条 + SEC 7 条 + SEC 完整 submissions 7 份 + summary）。

## 工具

`scripts/verified_evidence_audit.py`，可重复运行；输出 JSON 在 `runs/existing-list-onboarding-2026-10-18/verified-evidence-audit.json`。
