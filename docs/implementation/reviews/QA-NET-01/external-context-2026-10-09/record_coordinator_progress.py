"""Record executed private coordinator development, without certifying release."""
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
MARKER = "## Phase111 检索调度接续：2026-10-09"


def replace_prefix(path, prefix, replacement):
    text = path.read_text("utf-8")
    lines = text.splitlines()
    matching = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    assert len(matching) == 1, path
    lines[matching[0]] = replacement
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append(path, text):
    previous = path.read_text("utf-8")
    assert MARKER not in previous, path
    path.write_text(previous.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def main():
    replace_prefix(IQS / "task_plan.md", "**当前下一动作（2026-10-09 Phase111）**：",
        "**当前下一动作（2026-10-09 Phase111）**：把已实现的外部检索调度接入既有LLM回答路径，绑定实际prompt/attempt与独立context-use proof，再验证两阶段恢复/MCP/公开CLI。私有六受影响文件最终276P/20.36s；其中检索调度可冷跑、warm零HTTP、已知且已计价失败换下一搜索路由、未知发送/计价停机，同一live lease下未发送意图可原预留续接。收到Retry-After才记已知等待；实际用量超界不可通过新generation绕过。同网页不同查询保留各自短摘要/检索时点/operation，来源数据仍不是事实认证。见本批[接线接口](docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/coordinator-interface.md)。原REST调度未实现的历史已更新，LLM/来源proof/MCP/公开CLI、最终静态/一次集中review/源发布/严格清理仍待执行；Phase111保持in_progress，模型cascade继续只用原模型policy，Q09共享投影只作会计。StockQA旧全仓授权须先报备；StockWiki JR1/JR3四新路径、G3/L03/F05/真实identity/facts golden/THIN授权原门不变，不启动收费API/200家live、不刷新退役工程回执。")
    append(IQS / "task_plan.md", MARKER + """
- 私有检索协调入口已实施，真实SQLite/Q08/Q09＋HTTP边界替身验证；五个现有报备路径变化，无源仓发布。最终coordinator-health-green-01为276P/20.36s（controller21.007s），0失败/错误/跳过。
- 冷跑、缓存/重复恢复、确认且可计价的拒绝/坏JSON/错实体/空结果转下一route、unknown/无usage/保存失败停机、并发一次许可、同查询跨题共享、TTL新轮刷新、两query之间真实持久中断及Retry-After/超价界均覆盖。20项初RED是协调入口尚缺，不冒充20个独立旧漏洞；原中间失败保留。
- 同URL跨查询去重曾丢第二query覆盖，是真实新增反例；复用既有normalizer按query处理、最终URL去重并保留各次短摘要/日期/operation/检索时间，metadata仍受总cap。两处中间fixture错误是未配对pricing basis/usage unit使主route不准入，已修正并断言全部预期route准入，不扩大产品口径。
- 当前无活测试或Git handle：27720和35856均已实际终态exit0。runs/n111a保留供完整Phase111接线，不能清理或重启旧helper。新IQS checkpoint03以实际Git回执为准；这不是集中签收，不发布schema9，也不关闭其他门。
""")
    append(IQS / "progress.md", MARKER + """
- 上一工程goal有配置/计价/数据TDD与checkpoint02实际537a174a及后续PWF67bf570，属于progress；其间heartbeat仅只读查门，无实施/测试/Git写。当前沿同根PWF和28路径范围，五私有源码/测试变化，不写StockQA或其他源仓。
- coordinator-red-01：20F/80deselected/3.28s（controller3.953），协调入口未实现；green-01：19P/1F，Tavily fixture未将basis改per_search导致主route未准入；补断言完整admitted route。green-02：23P/2F，1真实同URL跨query丢coverage、1success-only fixture没配per_search/search_calls。原stdout/JUnit/执行字节均保留，不算成三产品失败。
- green-03：26P/80deselected/4.61s（controller5.529）。受影响六文件coordinator-affected-green-01原27720终态exit0：273P/22.28s（controller22.850），0失败/错误/跳过，不与此前批次相加。
- health-red-01：3F/106deselected/2.18s（controller2.924），实证收到Retry-After但仍用默认cooldown，以及超verified usage换generation又发送。接既有Q08已知等待；同一计价预算版本的超界历史阻断新轮，保留真实6000费用，不称免费。
- coordinator-health-green-01原35856终态exit0：六文件276P/20.36s（controller21.007），0失败/错误/跳过，全部执行源SHA不变。真实私有SQLite/Q09/Q08与HTTP替身；真实API、密钥、下载、生产库和外仓写均0。未创建回答attempt，检索不是LLM回答。
- 仅相同有效lease的无dispatch意图能复用原operation/预留继续；dispatch存在或结果/费用未知不重发/不failover。过期旧lease的未发送意图安全停机，跨owner接续尚待完整两阶段恢复，不称已完成。MCP明确before-reservation block，仍必须实施分阶段计费握手，不把REST通过当MCP通过。
- 已更新PWF/接线接口/接手说明；下一动作原LLM发送边界及context-use proof，最终受影响/静态/公开CLI和一次集中review留到完整批次。不新增小节点审查门，G3/F05/THIN/StockWiki四新路径许可不变；当前自有根不清理。IQS checkpoint03 Git实际结果随后追加。
""")
    append(IQS / "findings.md", MARKER + """
- durable cache查找必须先于credential/health/新预算预留；否则warm依赖key、credential不足或尚未MCP握手会留下孤儿付费意图。lookup只核原SQLite/哈希/身份/计划，不创建新预算owner。实际begin/consume事务仍是唯一发送授权，双worker即使同取未发送意图，只有一次能过consume。
- 原scope下sent unknown即使已知某个HTTP费用也不能当确认拒绝换route；缺usage保留Q09预留并停。已计价401/已知429/坏JSON/错issuer/空数据的原操作保持，恢复只能继续下一个已准入route，不能重复问同一路。
- 公司网页URL可被不同query返回不同短摘要/报告日期；URL去重不是抹掉查询及检索来源。按query复用既有normalizer，context URL单列、retrieval_provenance保留每个实际operation的原摘要与时点；不得给旧摘要加上新retrieved_at，最终上下文及metadata统一cap。
- Retry-After仅解析实际delta秒、无原headers保存；日期/非法header暂按unknown等待，不声称已知quota reset。超verified usage仍按observed units结算，但同计价版本不能凭换generation再跑；修改并获准的计价版本是另一显式配置动作，未扩大额度或重置历史费用。
- 当前实现只解决私有检索调度。真实回答prompt/attempt/use-proof、原生＋external混合来源隔离、publicCLI和MCP/跨lease恢复尚缺，不能把276P扩大成完整Phase111或答案准确性验收。
""")
    path = IQS / "docs/implementation/handoff-for-new-agent.md"
    text = path.read_text("utf-8")
    first, second, rest = text.split("\n\n", 2)
    assert first.startswith("**2026-10-09 Phase111正在实施") and second.startswith("**恢复与权限：**")
    first = "**2026-10-09 Phase111正在实施，优先于下文历史：** 唯一下一动作把已实现的检索协调入口接入既有LLM回答路径，绑定实际prompt/attempt与独立context-use proof，再做两阶段恢复/MCP/公开CLI；读[连续批次计划](reviews/QA-NET-01/external-context-2026-10-09/plan.md)、[接线接口](reviews/QA-NET-01/external-context-2026-10-09/coordinator-interface.md)和[精确范围](reviews/QA-NET-01/external-context-2026-10-09/scope.json)。检索/v1.1配置/计价/来源已在IQS自有runs/n111a/qa实施，最新六文件276P/20.36s/0失败错误跳过；不与历史重叠批次相加。原20RED/夹具诊断/同URL来源丢失及Retry-After/新轮绕价格上界RED都已留档。StockQA仍42a517c/schema8；private schema9/1.1未发布，整Phase111尚未验收。"
    second = "**恢复与权限：** 所有测试handle（含最新27720、35856）均已确认终态，不能poll/restart。runs/n111a仍未完成，禁止盲跑硬编码旧HEAD的checkpoint.py/checkpoint_02.py及旧publish/cleanup；新checkpoint03亦仅当前基线的一次留档，按实际Git回执判断是否已运行。原opencode、共享TEMP、Phase92及源七未知项不动。测试剥离真实key，guard禁外网/根外Python写；async/子进程受影响批用同guard沙箱外避Windows socketpair问题。模型cascade用原模型policy、共享Q09投影仅计费，预算版本不含公司查询。协调函数lookup先于key/health/预留；仅同一live lease、无durable dispatch可原意图续接，sent unknown或无计价停机。MCP before-reservation block是待实现状态，不是成功MCP；实际LLM/use-proof、跨lease/整两阶段、publicCLI、最终静态和一次集中review/源发布/严格清理仍待。无需重新实施已GREEN部分或增helper审查。StockQA全仓授权须先报备，StockWiki四新路径/THIN授权与真实identity/facts golden/G3/F05/L03原门不变。"
    path.write_text(first + "\n\n" + second + "\n\n" + rest, encoding="utf-8")
    append(Path(__file__).parent / "plan.md", MARKER + """
协调入口现已私有实现：lookup→必要时Q08 admission→Q09原预留/intent→单次adapter→原journal计价settle→重建短context；真实保存故障、并发和跨query中断都覆盖。最新276相关测试通过，原失败保留；没有集中review、LLM/公开CLI/MCP或源发布。

下一实际接线点是现有LLMClient/AsyncLLMClient.send_search_request、_search_request_payload、_parse_protocol_search_response及begin_quick_scan_send。不得改走不记账send_request：原生prompt/receipt SHA和Q10实际模型都保留原HTTP来源。external-only真实payload不提供native工具；hybrid按显式计划，同时分别证明外部context和原生工具；BaseLLMProvider不得继续无条件要求模型native搜索。先以实际HTTP payload与SQLite反例RED，再建立版本化私有context-use intent/result（绑定实际work/lease/attempt、context SHA、最终prompt SHA、原retrieval receipt SHA、实际response receipt SHA），调用点前后原子、不可由回答正文回填。不向native receipt插外部搜索事件/搜索route actual_model；公开C06 generic搜索状态只能在独立use-proof通过后投影。格式修复/备用模型是新的实际HTTP收费attempt，但复用原冻结上下文，warm/返回结果未知不得重复请求。MCP每个init/discovery/search单独Q09 operation，尚未完成，不把before-reservation拒绝作为最终交付。
""")


if __name__ == "__main__":
    main()
