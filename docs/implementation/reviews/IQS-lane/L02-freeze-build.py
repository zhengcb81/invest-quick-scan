"""L02 freeze builder: stratified sample + per-company question sets + cost model.

Deterministic and offline. Reads the OWNER-SIGNED B2a classification
(`StockQAbyLLM/pilot_runs/b2a_2026-10-03/stratification-final.{json,md}`), the
216 candidate list, and the signed H-share nominations; emits:

1. IQS  `docs/implementation/reviews/L02-freeze-2026-10-04.json`
2. StockQA run dir `pilot_runs/l02_2026-10-04/`:
   companies.json (60 with profile keys), repeat_subset.json (20),
   questions_<key>.json (one frozen question config per unique profile)

Stratification rules (frozen here, gaps reported honestly — never invented):
- Market: use ALL available US (7) and ALL signed HK nominations (3) to force
  three-market coverage; the remaining 50 slots come from CN via round-robin
  over lifecycle x profitability x industry strata.
- The name-overlap pair (中信建投 002168 + 601066) is forced into the sample
  as the multi-listing stratum (they stay two entities — no merge).
- Repeat subset (20): the overlap pair + every 3rd company of the sorted
  remaining sample (deterministic).
- Industry unknowns stay in a dedicated stratum (reported as a gap, never
  force-classified).

Run: python L02-freeze-build.py  (cwd = IQS repo root)
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
from collections import Counter

import sys

IQS = pathlib.Path("C:/Users/郑曾波/Projects/invest-quick-scan")
STOCKQA_RUN = pathlib.Path(
    "C:/Users/郑曾波/Projects/StockQAbyLLM/pilot_runs/b2a_2026-10-03"
)
L02_RUN = pathlib.Path(
    "C:/Users/郑曾波/Projects/StockQAbyLLM/pilot_runs/l02_2026-10-04"
)

# --- deterministic crosswalks (frozen; coarse mappings are reported as such) ---
SW_L1_TO_MODULE = {
    "农林牧渔": "agriculture",
    "基础化工": "materials",
    "钢铁": "materials",
    "有色金属": "resources",
    "电子": "hardware",
    "汽车": "auto",
    "家用电器": "consumer",
    "食品饮料": "consumer",
    "纺织服饰": "consumer",
    "轻工制造": "materials",
    "医药生物": "healthcare",
    "公用事业": "utilities",
    "交通运输": "transport",
    "房地产": "other",
    "商贸零售": "retail",
    "社会服务": "professional_services",
    "建筑材料": "construction",
    "建筑装饰": "construction",
    "电力设备": "energy_transition",
    "国防军工": "industrial",
    "计算机": "software",
    "传媒": "leisure_media",
    "通信": "telecom",
    "银行": "other",
    "非银金融": "other",
    "综合金融": "other",
    "煤炭": "resources",
    "石油石化": "resources",
    "环保": "other",
    "机械设备": "industrial",
    "美容护理": "consumer",
    "综合": "other",
}
OP_TYPE_TO_COMPANY_TYPE = {
    "manufacturing": "operating",
    "service": "operating",
    "platform": "operating",
    "resource": "operating",
    "finance": "bank",
    "holding": "holding",
    "unknown": "operating",
}
LIFE_TO_STAGE = {
    "growth": "scaling",
    "mature": "mature",
    "cyclical": "mature",  # profile.stage may never be "cyclical" (validate_profile)
    "turnaround": "turnaround",
    "declining": "declining",
}
TARGET_TOTAL = 60
REPEAT_TOTAL = 20
CAPS = {
    "primary_request_cap": 2600,
    "http_attempt_ceiling_including_retries": 5200,
    "web_search_call_ceiling": 5200,
}
WINDOW_MAX = 325
WINDOWS = 8


def sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(
            obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def load_iqs_test_case():
    spec = importlib.util.spec_from_file_location(
        "iqs_qsets", IQS / "tests/test_question_sets.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tc = mod.QuestionSetTests
    tc.setUpClass()
    return tc


def profile_for(row: dict, cycle_position: str) -> dict:
    industry_sw = row.get("industry")
    op_type = row.get("operating_type") or "unknown"
    life = row.get("lifecycle_stage") or "mature"
    company_type = OP_TYPE_TO_COMPANY_TYPE.get(op_type, "operating")
    stage = LIFE_TO_STAGE.get(life, "mature")
    industry_module = (
        SW_L1_TO_MODULE.get(industry_sw, "other") if industry_sw else "other"
    )
    cyclical = life == "cyclical"  # stage stays a real lifecycle; cycle flag is separate
    return {
        "company_type": company_type,
        "stage": stage,
        "industry_modules": [industry_module],
        "cycle_sensitive": cyclical,
        **({"cycle_position": cycle_position} if cyclical else {}),
        "recovery_review": life in {"turnaround", "declining"} or op_type == "unknown",
        "recovery_rationale": "L02 calibration stratum",
    }


IND = [
    "农林牧渔", "基础化工", "钢铁", "有色金属", "电子", "汽车", "家用电器", "食品饮料",
    "纺织服饰", "轻工制造", "医药生物", "公用事业", "交通运输", "房地产", "商贸零售",
    "社会服务", "建筑材料", "建筑装饰", "电力设备", "国防军工", "计算机", "传媒", "通信",
    "银行", "非银金融", "综合金融", "煤炭", "石油石化", "环保", "机械设备", "美容护理", "综合",
]


def _extract_classified_rows() -> list:
    """Re-extract per-company rows from the signed B2a raw outputs (JSON or labelled prose)."""
    import re

    rows = []
    for f in sorted((STOCKQA_RUN / "out").glob("classify/*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        entity = data.get("entity") or {}
        answers = data.get("answers") or {}
        ans = answers.get("B2A_CLASSIFY") or {}
        desc = (ans.get("description") or "").strip()
        rec = {
            "entity_id": entity.get("entity_id") or "",
            "name": entity.get("company_name"),
            "industry": None,
            "operating_type": None,
            "lifecycle_stage": None,
            "profitability": None,
        }
        if desc.startswith("{"):
            try:
                inner = json.loads(desc[desc.find("{"):desc.rfind("}") + 1])
                rec.update(
                    industry=inner.get("industry"),
                    operating_type=inner.get("operating_type"),
                    lifecycle_stage=inner.get("lifecycle_stage"),
                    profitability=inner.get("profitability"),
                )
            except Exception:
                pass
        else:
            def lab(key, text=desc):
                m = re.search( re.escape(key) + "[ ]*[:：][ ]*([^" + chr(10) + ";,;]+)", text, re.I)
                return m.group(1).strip() if m else None

            ind = lab("industry")
            rec["industry"] = next((i for i in IND if ind and i in ind), None)
            rec["operating_type"] = lab("operating_type")
            rec["lifecycle_stage"] = lab("lifecycle_stage")
            rec["profitability"] = lab("profitability")
        rows.append(rec)
    return rows


def main() -> int:
    classified = _extract_classified_rows()
    assert len(classified) == 216, len(classified)
    candidates = json.loads(
        (STOCKQA_RUN / "candidates.json").read_text(encoding="utf-8")
    )
    hk_noms = json.loads(
        (STOCKQA_RUN / "hk-discovery-results.json").read_text(encoding="utf-8")
    )
    by_probe = {r["entity_id"]: r for r in classified}
    by_listing = {c["listing_key"]: c for c in candidates}
    assert len(by_listing) == 216, len(by_listing)

    def row_for(listing_key: str) -> dict | None:
        probe = "probe:" + listing_key
        r = by_probe.get(probe)
        if r is None:
            return None
        c = by_listing.get(listing_key, {})
        return {**r, "listing_key": listing_key, "name": c.get("name")}

    cn_pool = [k for k in sorted(by_listing) if k.startswith("CN-A:")]
    us_pool = [k for k in sorted(by_listing) if k.startswith("US:")]
    hk_confirmed = [
        n
        for n in hk_noms
        if isinstance(n.get("result"), dict)
        and str(n["result"].get("has_hk_listing")).lower() == "true"
        and n["result"].get("hk_ticker")
    ]

    hk_keys = list(dict.fromkeys(f"HK:{n['result']['hk_ticker']}" for n in hk_confirmed))
    overlap = ("CN-A:002168", "CN-A:601066")
    selected: list[str] = list(overlap)
    # all US + all signed HK (three-market coverage from what exists)
    for key in us_pool:
        if row_for(key) is not None:
            selected.append(key)
    # CN round-robin over (lifecycle, profitability) strata to fill50 CN slots
    selected = selected + hk_keys
    cn_rows = [(k, row_for(k)) for k in cn_pool if k not in overlap and row_for(k)]
    strata_order: dict[tuple, list] = {}
    for key, row in cn_rows:
        stratum = (
            row.get("lifecycle_stage") or "unknown",
            row.get("profitability") or "unknown",
            row.get("industry") or "unknown",
        )
        strata_order.setdefault(stratum, []).append(key)
    strata_keys = sorted(strata_order)
    buckets = {k: list(strata_order[k]) for k in strata_keys}
    cn_need = TARGET_TOTAL - len(selected)
    picked_cn = 0
    round_i = 0
    while picked_cn < cn_need:
        progressed = False
        for sk in strata_keys:
            if buckets[sk]:
                selected.append(buckets[sk].pop(0))
                picked_cn += 1
                progressed = True
                if picked_cn >= cn_need:
                    break
        if not progressed:
            break
        round_i += 1
    shortfall = cn_need - picked_cn

    selected_final = list(selected)
    assert len(selected_final) == TARGET_TOTAL, len(selected_final)
    

    sample = []
    for key in selected_final:
        if key.startswith("HK:"):
            hk = next(
                n for n in hk_confirmed if f"HK:{n['result']['hk_ticker']}" == key
            )
            sample.append(
                {
                    "listing_key": key,
                    "name": hk.get("name")
                    or {"HK:02202": "万科企业", "HK:06066": "中信建投证券"}.get(key, key),
                    "market": "HK",
                    "source": "signed_hk_nomination",
                    "probe_entity_id": "probe:" + key,
                    "industry": None,
                    "operating_type": None,
                    "lifecycle_stage": None,
                    "profitability": None,
                }
            )
            continue
        row = row_for(key)
        sample.append(
            {
                "listing_key": key,
                "name": row.get("name"),
                "market": "HK"
                if key.startswith("HK:")
                else ("US" if key.startswith("US:") else "CN-A"),
                "source": "b2a_signed_classification",
                "probe_entity_id": "probe:" + key,
                "industry": row.get("industry"),
                "operating_type": row.get("operating_type"),
                "lifecycle_stage": row.get("lifecycle_stage"),
                "profitability": row.get("profitability"),
            }
        )
    assert len(sample) == len(selected_final)
    sample.sort(key=lambda s: s["listing_key"])

    # repeat subset: overlap pair + every 3rd of the sorted remainder
    remainder = [s["listing_key"] for s in sample if s["listing_key"] not in overlap]
    repeat = list(overlap) + remainder[::3]
    repeat = repeat[:REPEAT_TOTAL]
    while len(repeat) < REPEAT_TOTAL:
        for k in remainder:
            if k not in repeat:
                repeat.append(k)
            if len(repeat) >= REPEAT_TOTAL:
                break
    repeat = repeat[:REPEAT_TOTAL]

    # ---- per-company profile + frozen question sets ----
    tc = load_iqs_test_case()
    cycle_position = "trough"
    try:
        mod = tc.modules["cyclical"]
        cycle_position = (mod.get("evidence_context") or {}).get(
            "cycle_position", "trough"
        )
    except Exception:
        pass
    profile_cache: dict[str, dict] = {}
    questions_cache: dict[str, dict] = {}
    company_profiles = []
    for entry in sample:
        if entry["market"] == "HK":
            # signed HK nomination: reuse the CN profile of its listing twin when known
            twin = {"HK:02318": "CN-A:601318", "HK:06066": "CN-A:601066"}.get(
                entry["listing_key"]
            )
            src = next((s for s in sample if s["listing_key"] == twin), None)
            basis = src if src else entry
        else:
            basis = entry
        profile = profile_for(basis, cycle_position)
        key_parts = (
            profile["company_type"],
            profile["stage"],
            profile["industry_modules"][0],
            str(profile.get("cycle_sensitive")),
            str(profile.get("recovery_review")),
        )
        pkey = "|".join(key_parts)
        if pkey not in questions_cache:
            prof = dict(tc.profile)
            prof.update(profile)
            manifest = tc().make_manifest(profile=prof)
            qlist = [
                {"question_id": q["id"], "text": q["question"]}
                for q in manifest["questions"]
            ]
            questions_cache[pkey] = {
                "profile": profile,
                "question_ids": [q["question_id"] for q in qlist],
                "questions": qlist,
                "question_count": len(qlist),
                "questions_sha256": sha(qlist),
                "replacements": manifest["replacements"],
            }
            profile_cache[pkey] = profile
        company_profiles.append(
            {
                "listing_key": entry["listing_key"],
                "probe_entity_id": entry["probe_entity_id"],
                "name": entry["name"],
                "market": entry["market"],
                "profile_key": pkey,
            }
        )

    total_questions = sum(
        questions_cache[c["profile_key"]]["question_count"] for c in company_profiles
    )
    repeat_questions = sum(
        next(c["profile_key"] for c in company_profiles if c["listing_key"] == k)
        and questions_cache[
            next(c["profile_key"] for c in company_profiles if c["listing_key"] == k)
        ]["question_count"]
        for k in repeat
    )
    first_pass = total_questions + repeat_questions
    # dispatch policy: exactly ONE attempt per question plus format_repair_budget=1
    # (observed activation ~5% in B2a/7a); failures are REPORTED, never hidden (LIVE-04)
    # and never silently re-dispatched (no retry headroom fiction).
    repair_rate = 0.05
    with_retry_headroom = int(first_pass * (1 + repair_rate))
    search_estimate = int(first_pass * 2.0)
    search_with_headroom = int(search_estimate * (1 + repair_rate))

    gaps = []
    unknown_ind = [s for s in sample if s["market"] != "HK" and not s.get("industry")]
    if unknown_ind:
        gaps.append(
            {
                "kind": "industry_unknown_stratum",
                "count": len(unknown_ind),
                "listing_keys": [s["listing_key"] for s in unknown_ind],
            }
        )
    if shortfall > 0:
        gaps.append({"kind": "cn_stratum_shortfall", "short": shortfall})
    hk_gap = TARGET_TOTAL - len([s for s in sample if s["market"] == "HK"])
    gaps.append(
        {
            "kind": "hk_stratum_thin",
            "signed_hk_available": len(hk_keys),
            "note": "pool has zero HK candidates; HK stratum = signed nominations only",
        }
    )

    freeze = {
        "schema": "l02_freeze/1",
        "frozen_at": "2026-10-04T00:00:00Z",
        "task": "L02 execute 60-company scoring calibration + rule stability",
        "owner_authorizations": [
            "2026-10-04: L02 live budget agreed in principle; run directly when within 2600/5200 (决定 2, direct-run)",
            "B2a classification signed 2026-10-04 (决定 B2a签收)",
            "H-share nominations signed with B2a (probe-based, zero pool writes)",
        ],
        "inputs": {
            "b2a_classification_reextracted_from": str(STOCKQA_RUN / "out" / "classify"),
            "b2a_classification_files": 216,
            "b2a_summary_report": str(STOCKQA_RUN / "stratification-final.json"),
            "candidates": str(STOCKQA_RUN / "candidates.json"),
            "candidate_count": 216,
        },
        "sample": {
            "total": len(sample),
            "by_market": dict(Counter(s["market"] for s in sample)),
            "by_industry": dict(
                Counter(s.get("industry") or "unknown" for s in sample)
            ),
            "by_lifecycle": dict(
                Counter(s.get("lifecycle_stage") or "unknown" for s in sample)
            ),
            "by_profitability": dict(
                Counter(s.get("profitability") or "unknown" for s in sample)
            ),
            "multi_listing_stratum": {
                "listing_keys": list(overlap),
                "rule": "both forced in, never merged",
            },
            "entities": sample,
            "sample_sha256": sha(sample),
        },
        "repeat_subset": {
            "total": len(repeat),
            "rule": "overlap pair + every 3rd of sorted remainder",
            "listing_keys": repeat,
            "sha256": sha(repeat),
        },
        "question_sets": {
            "mechanism": "IQS select_questions(make_manifest) per frozen profile; per-company file keyed by profile_key",
            "crosswalks": {
                "sw_l1_to_industry_module": SW_L1_TO_MODULE,
                "operating_type_to_company_type": OP_TYPE_TO_COMPANY_TYPE,
                "lifecycle_to_stage": LIFE_TO_STAGE,
            },
            "cycle_position": cycle_position,
            "sets": [
                {
                    "profile_key": k,
                    "question_count": v["question_count"],
                    "questions_sha256": v["questions_sha256"],
                    "question_ids": v["question_ids"],
                    "profile": v["profile"],
                }
                for k, v in sorted(questions_cache.items())
            ],
        },
        "rules": {
            "whitelist_rule_reference": "schemas/quick_scan/rule.schema.json + WL example from results-ui/acceptance",
            "scoring_anchors_reference": "scripts/scoring_rubrics.py (frozen C03 rubrics)",
            "recovery_policy": "recovery-watch-1 (frozen, see L01/W08 records)",
            "boundary_reask": "7/8/9 boundaries re-asked within the 20-company repeat subset",
        },
        "model": {
            "provider": "minimax",
            "model": "MiniMax-M3",
            "config_source": "run-dir frozen llm_apis.json copy (L01 precedent)",
            "search_required": True,
            "entity_id_policy": "probe:<listing_key> (zero pool writes)",
        },
        "budget": {
            "first_pass_questions": first_pass,
            "dispatch_policy": "one attempt per question + format_repair_budget=1; failures reported (LIVE-04), no silent re-dispatch",
            "repair_rate_used_for_estimate": repair_rate,
            "estimated_primary_with_headroom": with_retry_headroom,
            "estimated_searches": search_estimate,
            "estimated_searches_with_headroom": search_with_headroom,
            "caps": CAPS,
            "within_owner_caps": with_retry_headroom <= CAPS["primary_request_cap"]
            and search_with_headroom <= CAPS["web_search_call_ceiling"],
            "owner_cap_envelope": "primary<=2600 / searches<=5200 (owner: 直接跑)",
        },
        "windows": {
            "count": WINDOWS,
            "max_questions_per_window": WINDOW_MAX,
            "rule": "sequential, stop on cap/limit, resume, never delete records",
        },
        "stop_loss": "any provider limit hit / search-unavailable streak -> stop dispatch, persist tasks+receipts+costs, report; no delete-and-rerun",
        "entry_conditions": {
            "g1_f1_information_dates": "satisfied by 7a (StockQA 5fdcc2c)",
            "g1_f2_source_metadata": "satisfied by 7a (StockQA 5fdcc2c)",
            "w07_w08_w09": "verified",
            "b2a_strata": "signed",
        },
        "gaps": gaps,
        "zero_pool_writes": True,
    }
    # write outputs
    out_json = IQS / "docs/implementation/reviews/L02-freeze-2026-10-04.json"
    out_json.write_text(
        json.dumps(freeze, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    L02_RUN.mkdir(parents=True, exist_ok=True)
    (L02_RUN / "companies.json").write_text(
        json.dumps(company_profiles, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (L02_RUN / "repeat_subset.json").write_text(
        json.dumps(repeat, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for pkey, qset in questions_cache.items():
        safe = pkey.replace("|", "__")
        config = {
            "categories": [
                {
                    "category": "calibration",
                    "questions": qset["questions"],  # real catalog question text (L01 precedent)
                }
            ]
        }
        (L02_RUN / f"questions_{safe}.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print("FROZEN sample:", len(sample), dict(Counter(s["market"] for s in sample)))
    print("repeat:", len(repeat))
    print("profiles:", len(questions_cache))
    for k, v in sorted(questions_cache.items()):
        print("  ", k, "->", v["question_count"], "questions")
    print(
        "first_pass questions:",
        first_pass,
        "| with 15% headroom:",
        with_retry_headroom,
        "| within2600:",
        with_retry_headroom <= 2600,
    )
    print(
        "searches:",
        search_estimate,
        "| with headroom:",
        search_with_headroom,
        "| within5200:",
        search_with_headroom <= 5200,
    )
    print("gaps:", json.dumps(gaps, ensure_ascii=False)[:400])
    print("wrote:", out_json)
    return 0



if __name__ == "__main__":
    sys.exit(main())
