# -*- coding: utf-8 -*-
"""G2 独立复算脚本（审查者自有代码，只读访问 StockQAbyLLM 原始产出）。

用法:  python -X utf8 G2-recompute-2026-10-05.py
覆盖:  步骤① 覆盖分母（逐公司/逐分层）、三值状态分布、unknown/null 与均分关系、
       搜索执行归因、模型/类型比较可比性声明；步骤② 低谷观察题与零池写入实体；
       步骤③ 费用总账、冻结/派发时序。
不调用任何 LLM / 网络，不写 StockQAbyLLM / StockWiki 任何文件。
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

RUN = r"C:\Users\郑曾波\Projects\StockQAbyLLM\pilot_runs\l02_2026-10-04"
IQS = r"C:\Users\郑曾波\Projects\invest-quick-scan"
OUT = os.path.join(RUN, "out", "primary")
REJ_ERR = os.path.join(RUN, "rejected_error_2026-10-05")
REJ_PRB = os.path.join(RUN, "rejected_probe_2026-10-05")


def p(*a):
    print(*a)
    sys.stdout.flush()


def ts(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def analyze(path):
    d = load(path)
    ans = d.get("answers", {}) or {}
    rcpt = d.get("execution_receipts", {}) or {}
    st = Counter()
    score_bad = []          # status!=scored 但有数值分 / status==scored 但分数非法
    nonnull_nonscored = []
    null_scored = []
    scores = []             # status==scored 且合法分
    exec_by_status = Counter()
    nocall_by_status = Counter()
    unknown_meta = []
    attempts = 0
    repairs_attempted = 0
    repairs_delta = 0
    exec_receipts = Counter()
    calls_total = 0
    sources_ans = 0
    sources_rcpt = 0
    with_rid = 0
    lat = []
    prov = set()
    model = set()
    ent = d.get("entity", {})
    for q, a in ans.items():
        s = a.get("status")
        st[s] += 1
        sc = a.get("score")
        sources_ans += len(a.get("source_urls") or [])
        if s == "scored":
            if isinstance(sc, bool) or not isinstance(sc, int) or not (1 <= sc <= 10):
                score_bad.append((q, s, sc))
            else:
                scores.append(sc)
        else:
            if sc is not None:
                nonnull_nonscored.append((q, s, sc))
        if s == "unknown":
            r = rcpt.get(q, {})
            unknown_meta.append(
                dict(q=q, score=sc, rid=bool(r.get("response_id")),
                     search=r.get("search_status"),
                     calls=len(r.get("web_search_calls") or []),
                     repair=(r.get("format_repair") or {}).get("status"),
                     desc=(a.get("description") or "")[:40]))
    for q, r in rcpt.items():
        ex = r.get("search_status")
        exec_receipts[ex] += 1
        calls = len(r.get("web_search_calls") or [])
        calls_total += calls
        sources_rcpt += len(r.get("source_urls") or [])
        if r.get("response_id"):
            with_rid += 1
        status = (ans.get(q) or {}).get("status")
        if ex == "executed":
            exec_by_status[status] += 1
        if calls == 0:
            nocall_by_status[status] += 1
        at = r.get("attempts") or []
        attempts += len(at)
        if len(at) > 1:
            repairs_delta += len(at) - 1
        fr = r.get("format_repair")
        if isinstance(fr, dict) and fr.get("attempted"):
            repairs_attempted += 1
        prov.add(r.get("provider"))
        model.add(r.get("actual_model"))
        for a in at:
            s0, c0 = ts(a.get("started_at")), ts(a.get("completed_at"))
            if s0 and c0:
                lat.append((c0 - s0).total_seconds())
    return dict(
        file=os.path.basename(path),
        entity_id=ent.get("entity_id"), name=ent.get("name"),
        provider=d.get("provider"), prov_set=sorted(x for x in prov if x),
        model_set=sorted(x for x in model if x),
        questions=len(ans), statuses=dict(st), attempts=attempts,
        repairs_attempted=repairs_attempted, repairs_delta=repairs_delta,
        exec_receipts=dict(exec_receipts), calls_total=calls_total,
        sources_ans=sources_ans, sources_rcpt=sources_rcpt,
        with_rid=with_rid, rcpts=len(rcpt),
        exec_by_status=dict(exec_by_status), nocall_by_status=dict(nocall_by_status),
        score_bad=score_bad, nonnull_nonscored=nonnull_nonscored,
        n_scores=len(scores),
        mean_score=(round(sum(scores) / len(scores), 2) if scores else None),
        min_score=min(scores) if scores else None,
        max_score=max(scores) if scores else None,
        score_hist=dict(sorted(Counter(scores).items())),
        unknown_meta=unknown_meta,
        lat_avg=(round(sum(lat) / len(lat), 1) if lat else None),
        lat_max=(round(max(lat), 1) if lat else None),
        lat_n=len(lat),
        observed_at=d.get("observed_at"),
    )


def main():
    files = sorted(os.listdir(OUT))
    p("=" * 100)
    p("STEP 1 — out/primary 全文件清单与 provider 归属")
    p("=" * 100)
    allf = [analyze(os.path.join(OUT, f)) for f in files if f.endswith(".json")]
    for r in allf:
        p(f"{r['file']:24s} provider={r['provider']} model={r['provider'].get('requested_model') if isinstance(r['provider'],dict) else '?'} "
          f"entity={r['entity_id']} q={r['questions']} statuses={r['statuses']}")

    mimo = [r for r in allf if (r["provider"] or {}).get("name") == "mimo"]
    mini = [r for r in allf if (r["provider"] or {}).get("name") != "mimo"]
    p(f"\nMiMo 文件 {len(mimo)} 份 / 非 MiMo 文件 {len(mini)} 份")

    p("\n" + "=" * 100)
    p("STEP 1a — 6 家 MiMo 逐公司复算")
    p("=" * 100)
    hdr = ("company", "q", "scored", "insuff", "unk", "err", "exec", "nocall", "att", "rep", "srcA", "srcR", "rid", "avg", "max")
    p("%-22s %4s %6s %6s %4s %4s %5s %6s %5s %4s %5s %5s %4s %6s %6s" % hdr)
    tot = defaultdict(float)
    exec_status = Counter()
    nocall_status = Counter()
    all_unknown = []
    all_scores = []
    bad = []
    for r in mimo:
        s = r["statuses"]
        p("%-22s %4d %6d %6d %4d %4d %5d %6d %5d %4d %5d %5d %4d %6s %6s" % (
            r["file"].replace(".json", ""), r["questions"], s.get("scored", 0),
            s.get("insufficient_evidence", 0), s.get("unknown", 0), s.get("error", 0),
            r["exec_receipts"].get("executed", 0),
            (r["nocall_by_status"].get("insufficient_evidence", 0) + r["nocall_by_status"].get("unknown", 0)
             + r["nocall_by_status"].get("scored", 0)),
            r["attempts"], r["repairs_attempted"], r["sources_ans"], r["sources_rcpt"],
            r["with_rid"], r["lat_avg"], r["lat_max"]))
        tot["q"] += r["questions"]
        for k in ("scored", "insufficient_evidence", "unknown", "error", "not_applicable"):
            tot[k] += s.get(k, 0)
        tot["exec"] += r["exec_receipts"].get("executed", 0)
        tot["unver"] += r["exec_receipts"].get("unverified", 0)
        tot["att"] += r["attempts"]
        tot["rep"] += r["repairs_attempted"]
        tot["repd"] += r["repairs_delta"]
        tot["srcA"] += r["sources_ans"]
        tot["srcR"] += r["sources_rcpt"]
        tot["rid"] += r["with_rid"]
        tot["calls"] += r["calls_total"]
        exec_status.update(r["exec_by_status"])
        nocall_status.update(r["nocall_by_status"])
        all_unknown.extend(r["unknown_meta"])
        bad.extend(r["score_bad"])
        # 与 evidence JSON 一致的 attempt 级延迟需逐 attempt，此处复算全量
    p("-" * 100)
    p(f"{'TOTAL(6家)':22s} {int(tot['q']):4d} {int(tot['scored']):6d} {int(tot['insufficient_evidence']):6d} "
      f"{int(tot['unknown']):4d} {int(tot['error']):4d} {int(tot['exec']):5d} {'':6s} {int(tot['att']):5d} "
      f"{int(tot['rep']):4d} {int(tot['srcA']):5d} {int(tot['srcR']):5d} {int(tot['rid']):4d}")
    p(f"non-scored = {int(tot['insufficient_evidence']+tot['unknown']+tot['error'])} "
      f"(期望 71); scored%={tot['scored']/tot['q']*100:.1f} insuff%={tot['insufficient_evidence']/tot['q']*100:.1f} "
      f"unk%={tot['unknown']/tot['q']*100:.1f}; exec%={tot['exec']/tot['q']*100:.1f}; repairs_delta={int(tot['repd'])}")
    p(f"calls_total(内建搜索调用)={int(tot['calls'])}  sources(answer层)={int(tot['srcA'])} sources(receipt层)={int(tot['srcR'])}")

    # attempt 级延迟（6 家全量）
    lat = []
    latmax = None
    for r in mimo:
        d = load(os.path.join(OUT, r["file"]))
        for q, rec in (d.get("execution_receipts") or {}).items():
            for a in rec.get("attempts") or []:
                s0, c0 = ts(a.get("started_at")), ts(a.get("completed_at"))
                if s0 and c0:
                    v = (c0 - s0).total_seconds()
                    lat.append(v)
                    if latmax is None or v > latmax[0]:
                        latmax = (v, r["file"], q)
    p(f"attempt 级延迟 n={len(lat)} avg={sum(lat)/len(lat):.1f}s max={latmax[0]:.1f}s ({latmax[1]} {latmax[2]})")

    p("\n" + "=" * 100)
    p("STEP 1b — 搜索执行归因交叉表（receipt.search_status × answer.status）")
    p("=" * 100)
    p(f"search_status=executed  -> {dict(exec_status)}")
    p(f"web_search_calls==0     -> {dict(nocall_status)}")
    # 未 executed 的全表
    nonexec = Counter()
    calls_pos_unver = Counter()
    for r in mimo:
        d = load(os.path.join(OUT, r["file"]))
        for q, rec in (d["execution_receipts"]).items():
            s = rec.get("search_status")
            if s != "executed":
                nonexec[(s, d["answers"][q]["status"])] += 1
                if len(rec.get("web_search_calls") or []) > 0:
                    calls_pos_unver[d["answers"][q]["status"]] += 1
    p(f"search_status!=executed 逐组合 -> {dict(nonexec)}")
    p(f"其中 calls>0 但回执不可核验 -> {dict(calls_pos_unver)}")
    nonexec_scored = sum(v for (s, stt), v in nonexec.items() if stt == "scored")
    p(f"未 executed 却 scored 的题数 = {nonexec_scored} （必须为 0）")
    nocall_scored = nocall_status.get("scored", 0)
    p(f"calls==0 却 scored 的题数 = {nocall_scored} （必须为 0）")

    p("\n" + "=" * 100)
    p("STEP 1c — unknown/null 与均分的关系（未知不伪装中等）")
    p("=" * 100)
    p(f"status!=scored 但 score 非 null 的题: {len(bad)+sum(1 for r in mimo for x in r['nonnull_nonscored'])} -> "
      f"{[x for r in mimo for x in r['nonnull_nonscored']][:10]}")
    p(f"非法分（bool/非1-10整数）: {sum(len(r['score_bad']) for r in mimo)} -> {bad[:10]}")
    p(f"unknown 11 题明细:")
    for u in all_unknown:
        p(f"   {u['q']:18s} score={u['score']} rid={u['rid']} search={u['search']} calls={u['calls']} repair={u['repair']} | {u['desc']}")
    # 均分验证：分别按 status==scored 与 score is not None 计算
    diff = 0
    p("\n逐公司均分（scored 集合 vs 非 null 分集合，二者必须逐字相等）:")
    for r in mimo:
        d = load(os.path.join(OUT, r["file"]))
        a_set = [a["score"] for a in d["answers"].values() if a["status"] == "scored"]
        b_set = [a["score"] for a in d["answers"].values() if a.get("score") is not None]
        same = a_set == b_set
        diff += 0 if same else 1
        p(f"   {r['file']:22s} n(scored)={len(a_set):3d} n(non-null)={len(b_set):3d} mean={sum(a_set)/len(a_set):.2f} equal={same}")
    p(f"不一致公司数 = {diff} （必须为 0）")
    p("注：本批 unknown/insufficient 全为 null，故任何按非 null 分聚合的均分都等价于只按 scored 聚合，"
      "unknown 不可能以 5 分或任何默认分进入均分（I05/SC-02）。")

    p("\n" + "=" * 100)
    p("STEP 1d — 模型/类型比较可比性声明抽查")
    p("=" * 100)
    for r in mimo:
        p(f"   {r['file']:22s} provider.name={r['provider'].get('name')} requested={r['provider'].get('requested_model')} "
          f"receipt providers={r['prov_set']} models={r['model_set']} entity={r['entity_id']}")
    p(f"MiMo 组内 provider 集合是否唯一: {len({tuple(r['prov_set']) for r in mimo}) == 1 and len(mimo[0]['prov_set']) == 1}")
    p(f"MiMo 组内 model 集合是否唯一: {len({tuple(r['model_set']) for r in mimo}) == 1 and len(mimo[0]['model_set']) == 1}")
    p("\n非 MiMo（MiniMax 旧产）文件:")
    tot_q = 0
    for r in mini:
        tot_q += r["questions"]
        p(f"   {r['file']:22s} provider={r['provider']} entity={r['entity_id']} q={r['questions']} statuses={r['statuses']} "
          f"models={r['model_set']}")
    p(f"   MiniMax 组题数合计 = {tot_q}，公司集合 = {sorted(r['file'] for r in mini)}")

    p("\n" + "=" * 100)
    p("STEP 2 — 恢复/低谷观察题、实体策略（零池写入）")
    p("=" * 100)
    for r in mimo:
        d = load(os.path.join(OUT, r["file"]))
        rec = [q for q in d["answers"] if q.startswith("RECOVERY")]
        if rec:
            det = [(q, d["answers"][q]["status"], d["answers"][q]["score"]) for q in sorted(rec)]
            p(f"   {r['file']:22s} RECOVERY 题 {len(rec)} 个 -> {det}")
    p("\n全 6 份 + 探针 entity_id:")
    probe = os.path.join(REJ_PRB, "CN_A_002122_mimo.json")
    ents = [r["entity_id"] for r in mimo]
    if os.path.exists(probe):
        pr = analyze(probe)
        ents.append(pr["entity_id"])
        p(f"   probe: {pr['file']} entity={pr['entity_id']} q={pr['questions']} statuses={pr['statuses']} "
          f"exec={pr['exec_receipts']} att={pr['attempts']} rep={pr['repairs_attempted']} "
          f"avg={pr['lat_avg']} max={pr['lat_max']} srcR={pr['sources_rcpt']}")
        p(f"   probe 未 executed -> {pr['nocall_by_status']} / 全部非exec状态: ", )
        p(f"   probe attempts<=2 全部? 计算于下方")
    p(f"   全部 entity_id = {ents}")
    p(f"   零池写入（全部以 probe: 开头） = {all(e and e.startswith('probe:') for e in ents)}")

    p("\n" + "=" * 100)
    p("STEP 2/3 — attempts 预算与费用总账")
    p("=" * 100)
    out_att = 0
    out_files = 0
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".json"):
            continue
        d = load(os.path.join(OUT, f))
        n = sum(len(r.get("attempts") or []) for r in (d.get("execution_receipts") or {}).values())
        out_att += n
        out_files += 1
    rej_att = 0
    rej_files = 0
    for base in (REJ_ERR, REJ_PRB):
        for f in sorted(os.listdir(base)):
            if not f.endswith(".json") or f.startswith("run-log") or f.startswith("repair-manifest"):
                continue
            d = load(os.path.join(base, f))
            if not isinstance(d, dict) or "execution_receipts" not in d:
                p(f"   [skip non-output] {base}\\{f}")
                continue
            n = sum(len(r.get("attempts") or []) for r in (d.get("execution_receipts") or {}).values())
            rej_att += n
            rej_files += 1
    p(f"out/primary: {out_files} 份 attempts = {out_att}")
    p(f"rejected_* : {rej_files} 份 attempts = {rej_att}")
    p(f"合计 = {out_att + rej_att}")
    rl = load(os.path.join(RUN, "run-log.json"))
    p(f"run-log 顶层键 = {list(rl.keys())}")
    budget = rl.get("budget") or {}
    p(f"run-log budget = {json.dumps(budget, ensure_ascii=False)}")

    # attempts<=2 检查
    over = 0
    for base, dirs in ((OUT, sorted(os.listdir(OUT))),):
        for f in dirs:
            if not f.endswith(".json"):
                continue
            d = load(os.path.join(base, f))
            for q, r in (d.get("execution_receipts") or {}).items():
                if len(r.get("attempts") or []) > 2:
                    over += 1
    p(f"单题 attempts>2 的 receipt 数（预算=1 修复，应为 0）= {over}")

    p("\n" + "=" * 100)
    p("STEP 3 — 冻结/派发时序与探针门")
    p("=" * 100)
    fz = load(os.path.join(IQS, "docs", "implementation", "reviews", "L02-freeze-2026-10-04.json"))
    for a in fz.get("amendments", []):
        p(f"   {a['id']} at={a['at']}")
    p(f"   zero_pool_writes={fz.get('zero_pool_writes')}  sample.total={fz['sample']['total']} "
      f"by_market={fz['sample']['by_market']}")
    # 批窗
    for name in ("run-log.backup-before-000738-repair.json", "run-log.json"):
        path = os.path.join(RUN, name) if name == "run-log.json" else os.path.join(REJ_ERR, name)
        try:
            r2 = load(path)
        except FileNotFoundError:
            continue
        lw = r2.get("last_window") or {}
        p(f"   {name}: last_window={json.dumps(lw, ensure_ascii=False)}")
    # 探针门实测
    pr = analyze(probe)
    p(f"   探针 002122: response_id {pr['with_rid']}/{pr['questions']} error={pr['statuses'].get('error',0)} "
      f"search executed={pr['exec_receipts'].get('executed',0)}/{pr['questions']} "
      f"(amendment-4 门 >=25 executed -> {'未达标' if pr['exec_receipts'].get('executed',0) < 25 else '达标'})")
    # 时间锚点
    p(f"   批内首个 attempt started_at(UTC) / 末个 completed_at(UTC):")
    lo, hi = None, None
    for r in mimo:
        d = load(os.path.join(OUT, r["file"]))
        for q, rec in (d["execution_receipts"]).items():
            for a in rec.get("attempts") or []:
                s0, c0 = ts(a.get("started_at")), ts(a.get("completed_at"))
                if s0 and (lo is None or s0 < lo):
                    lo = s0
                if c0 and (hi is None or c0 > hi):
                    hi = c0
    p(f"      first={lo.isoformat()} last={hi.isoformat()} span={(hi-lo).total_seconds()/60:.1f} min")

    p("\n" + "=" * 100)
    p("STEP 1 补 — 分层（公司维度）表复算（供报告 §2.2 对照）")
    p("=" * 100)
    comp = load(os.path.join(RUN, "companies.json"))
    byfile = {r["file"]: r for r in mimo}
    fname = {"CN-A:002122": "CN_A_002122.json", "CN-A:002156": "CN_A_002156.json",
             "CN-A:300327": "CN_A_300327.json", "CN-A:000738": "CN_A_000738.json",
             "US:NASDAQ:GENB": "US_NASDAQ_GENB.json", "HK:02202": "HK_02202.json"}
    for c in comp:
        f = fname[c["listing_key"]]
        r = byfile[f]
        s = r["statuses"]
        p(f"   {c['name']:12s} {c['listing_key']:16s} {c['market']:6s} {c['profile_key']:44s} "
          f"q={r['questions']:3d} scored={s.get('scored',0):3d} insuff={s.get('insufficient_evidence',0):3d} "
          f"unk={s.get('unknown',0):2d} exec={r['exec_receipts'].get('executed',0):3d} rep={r['repairs_attempted']:3d} "
          f"avg={r['lat_avg']}s mean_score={r['mean_score']} range=[{r['min_score']},{r['max_score']}]")

    p("\n" + "=" * 100)
    p("STEP 4 — 冻结题库 vs 运行题库 vs 产出题面（固定预期未被改动）")
    p("=" * 100)
    import hashlib
    fz = load(os.path.join(IQS, "docs", "implementation", "reviews", "L02-freeze-2026-10-04.json"))
    sets = {s["profile_key"]: s for s in fz["question_sets"]["sets"]}
    p(f"   冻结题库 set 数 = {len(sets)}")
    for c in comp:
        pk = c["profile_key"]
        s = sets.get(pk)
        if s is None:
            p(f"   {c['listing_key']:16s} 无冻结 set! pk={pk}")
            continue
        qpath = os.path.join(RUN, "questions_" + pk.replace("|", "__") + ".json")
        d = load(qpath)
        ids = [q["question_id"] for cat in d["categories"] for q in cat["questions"]]
        qs = [q for cat in d["categories"] for q in cat["questions"]]
        out = load(os.path.join(OUT, fname[c["listing_key"]]))
        out_ids = list(out["answers"].keys())
        variants = {
            "list_sorted": hashlib.sha256(json.dumps(qs, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "list_raw": hashlib.sha256(json.dumps(qs, ensure_ascii=False).encode()).hexdigest(),
            "ids": hashlib.sha256(json.dumps(ids, ensure_ascii=False).encode()).hexdigest(),
        }
        match = [k for k, v in variants.items() if v == s["questions_sha256"]]
        p(f"   {c['listing_key']:16s} 题数 file={len(ids)} freeze={s['question_ids'] and len(s['question_ids'])} "
          f"out={len(out_ids)} | file==freeze={ids == s['question_ids']} out==freeze={out_ids == s['question_ids']} "
          f"sha_match={match}")
    p("   （sha 变体若均未命中，仅说明哈希口径不同；判定以 question_ids 逐一相等为准）")

    p("\nDONE")


if __name__ == "__main__":
    import io

    class _Tee:
        def __init__(self, *streams):
            self.streams = streams

        def write(self, s):
            for st in self.streams:
                st.write(s)
                st.flush()

        def flush(self):
            for st in self.streams:
                st.flush()

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "G2-recompute-output-2026-10-05.txt")
    fh = io.open(log_path, "w", encoding="utf-8", newline="\n")
    sys.stdout = _Tee(sys.__stdout__, fh)
    try:
        main()
    finally:
        fh.close()
        sys.stdout = sys.__stdout__
    print("log written:", log_path)
