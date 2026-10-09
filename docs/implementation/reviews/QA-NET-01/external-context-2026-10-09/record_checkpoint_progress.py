"""Record a completed private slice, without closing Phase111 or publishing."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
LABEL = "runtime-checkpoint-affected-green-01"
receipt = json.loads((OUT / "verification" / LABEL / "process.json").read_text("utf-8"))
suite = ET.parse(OUT / "verification" / LABEL / "junit.xml").getroot().find("testsuite")
assert receipt["returncode"] == 0 and not receipt["timeout"] and receipt["executed_source_unchanged"]
assert suite is not None and int(suite.attrib["tests"]) == 672
assert all(int(suite.attrib[key]) == 0 for key in ("failures", "errors", "skipped"))


def replace_line(name, prefix, replacement):
    path = IQS / name
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.decode("utf-8").startswith(prefix)]
    assert len(matches) == 1, name
    newline = b"\r\n" if lines[matches[0]].endswith(b"\r\n") else b"\n"
    lines[matches[0]] = replacement.encode("utf-8") + newline
    path.write_bytes(b"".join(lines))


def append(name, content):
    path = IQS / name
    raw = path.read_bytes()
    assert "## Phase111 检查点与执行器接续：2026-10-09".encode("utf-8") not in raw, name
    newline = "\r\n" if b"\r\n" in raw else "\n"
    path.write_bytes(raw.rstrip(b"\r\n") + ("\n\n" + content.rstrip() + "\n").replace("\n", newline).encode("utf-8"))


replace_line("task_plan.md", "**当前下一动作（2026-10-09 Phase111）**：",
    "**当前下一动作（2026-10-09 Phase111）**：接通公开结果序列化与实际runner/cascade检索调度，再接两阶段/跨租约恢复、逐HTTP计费MCP和公开CLI。私有schema11/checkpoint2已核实际store使用proof，transport-managed runner、同步provider通用metadata、完整标准答案/C06和交付绑定已接线；14受影响文件672P/58.19s，0失败错误跳过，执行源码不变。原native回执、实际model/响应SHA保持，旧checkpoint1原payload/hash迁移保留且迁移故障整笔回滚。读[检查点与执行器接口](docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/checkpoint-interface.md)。公开quick_scan_result/1.0.0与IQS ROUTE_02仍假设原生web_search_calls，不得伪造事件或把内部metadata通过冒充公开链完成；下一段须明确版本与消费者兼容。Phase111保持in_progress，StockQA42a517c/schema8未发布；完整批次集中review/源Git/严格自有根清理待执行。StockWiki四新路径、G3/L03/F05/真实gold/THIN授权原门不变，收费API/200家live/工程回执刷新0。")

replace_line("docs/implementation/handoff-for-new-agent.md", "**2026-10-09 Phase111正在实施，优先于下文历史：**",
    "**2026-10-09 Phase111正在实施，优先于下文历史：** 私有schema11/checkpoint2、实际store来源proof、transport-managed runner、同步provider metadata及完整标准答案/C06已接线，最新14文件672P/58.19s/0失败错误跳过；原native receipt/响应SHA/provider/实际model不改，旧checkpoint1原字节保留。读[连续计划](reviews/QA-NET-01/external-context-2026-10-09/plan.md)、[检查点与执行器接口](reviews/QA-NET-01/external-context-2026-10-09/checkpoint-interface.md)和[31路径范围](reviews/QA-NET-01/external-context-2026-10-09/scope.json)。唯一下一动作：公开结果显式版本/消费者兼容与真实runner/cascade检索调度→两阶段/跨lease/MCP/公开CLI。StockQA仍42a517c/schema8，runs/n111a/qa私有11未发布；本批非完整Phase111验收，不声称金融答案准确性。")

replace_line("docs/implementation/handoff-for-new-agent.md", "**恢复与权限：** 本批测试79500",
    "**恢复与权限：** 本批原测试72663已终态exit0，其他本批测试/Git handle均已终态；不可poll/restart它们。checkpoint04实际IQS提交推送为a6691beb，233精确路径/227工件原字节核对；新checkpoint05以progress实际Git回执为准，禁止盲跑旧01–04 helper。独占runs/n111a继续保留，原opencode/共享TEMP/Phase92/源七未知项不动。guard剥离真实key、禁外网/自有根外Python写，提升仅避Windows socketpair，不是全OS认证。完整公开JSON/dispatch/MCP/跨lease尚缺；public结果1.0与ROUTE_02要求原生事件，必须显式演进并保持旧版兼容，不能制造native web_search_calls。最终完整批次才集中一次review/正常源发布/严格清理，不加小节点门。StockQA授权须写前报备；StockWiki四新路径、THIN精确授权、G3/F05/L03/真实gold仍独立缺。")

append("task_plan.md", """## Phase111 检查点与执行器接续：2026-10-09
- checkpoint04已实际正常提交推送a6691beb4f1b1d87234f076bc8cd659cf3a1ec99：233精确路径/227工件原字节、7原批次/118支持文件不变；这是私有留档，不是StockQA发布。旧01–04索引与源字节不覆写。
- 私有schema11原子重建answer_checkpoint以显式支持1/2，旧payload/hash/已封包和费用保留；故障回滚、旧1.0使用intent读取、不补来源和实际URL越界反例通过。
- 当前31路径均已先报备，仅IQS私有副本；新增三路径为outbox及两份旧C06 fixture测试。实际owner重读使用proof，transport-managed runner/同步provider投影、完整standard body→C06→outbox、来源越界拒绝与重启零HTTP已覆盖。
- 最终runtime-checkpoint-affected-green-01为14文件672P/58.19s（controller58.868s），无失败错误跳过/源码不变；不与491或此前455重叠批次相加。API/下载/外仓写0，原RED与fixture/控制器错误保留。
- 完整Phase111仍in_progress：公开JSON及IQS消费者显式版本兼容、实际runner/cascade检索调度、async provider投影、两阶段/跨lease/MCP/公开CLI、最终静态/一次集中review/源发布/严格清理待执行。StockWiki新授权及G3/F05/THIN原门不动。checkpoint05真实Git待progress回执，不提前标完成。
""")

append("progress.md", """## Phase111 检查点与执行器接续：2026-10-09
- 上一用户进度说明为只读状态说明，无新增工程成果；本goal已重核当前a6691beb及实际源/失败，继续可安全实施的链，不重复小节点审查。checkpoint04实际Git完成：233精确路径/227工件/7批次/118支持不变，HEAD=origin/master；原源码42a517c/schema8未写发布。
- checkpoint-red-01真实9F；green-01为8P/1F（sanitizer按旧契约省略空native URLs，fixture不能硬取键）；green-02为9P。新增迁移故障/旧use1.0/来源重哈希越界等后，affected-green-01为486P/4F，旧schema硬编码及旧metadata未覆盖当前HTTP来源。binding-red-01为2F：实际outbox拒checkpoint2，非adapter假正例。
- 先报备追加outbox、complete-seal/qa-net-seal两个测试，scope31。affected-green-02为485P/5F：新版URL排序错误、旧转换丢协议/requested字段，以及并发fixture未识别原consume边界的具名拒绝。新增metadata-red-01真实1F；补原转换字段、保留native-first URL顺序、并发断言已消费一次；affected-green-03为491P/38.19s（controller38.873）。不放宽原模型/实际响应条件。
- runtime-projection-red-01真实10F：新owner投影接口尚缺、外部runner丢proof。get_external_context_use与实际final_receipt再次同源核验，外来/缺失/重哈希proof不接纳；green-01为11P。实际runner保存checkpoint2并阻断缺authority封包，重启不增HTTP。
- runtime-complete-red-01为4F/2P，其中两正例fixture猜不存在get_checkpoint_context；改为既有get_observation_context/seal_result_delivery后red-02仍4F/2P，确认完整adapter拒2和同步provider未投影外部URL。green-01为4P/2F，原synthetic SQLite时钟晚于电脑HTTP时间，正确触发execution time/cutoff拒绝；仅fixture统一时钟，不改产品时间门。green-02为6P；外来URL无checkpoint/标准body部分写，真实全body保留并封存。
- 最终原72663终态exit0：runtime-checkpoint-affected-green-01十四文件672P/pytest58.19s/controller58.868s，0失败错误跳过/执行源码SHA不变。包含models/provider/runner/integration原回归；真实SQLite/客户端/封包函数，HTTP仅替身，收费/真实密钥/下载/外仓写0。
- 通用公开result1.0和IQS ROUTE_02消费者仍要求原生web_search_calls；当前仅同步provider metadata已投影，不能由672P推断公开JSON/CLI已通。下一段需显式版本/消费者兼容，保留原native回执/源URL与模型，禁止制造工具事件。async投影、真实检索dispatch、两阶段/跨lease、逐HTTP MCP和集中最终验收仍待。
- 更新PWF/findings/新接口/接手；旧04接口与writer不改，source仍42a517c/schema8，runs/n111a保留。checkpoint05正常IQS Git实际结果随后追加，不提前声称发布、完成或严格清理；G3/F05/THIN/StockWiki四新路径仍独立未齐，退役工程回执不刷新。
""")

append("findings.md", """## Phase111 检查点与执行器接续：2026-10-09
- checkpoint2的generic搜索执行仅来自实际已保存外部use1.1；原native状态/事件/URL/receipt SHA保持。read/save均回读实际owner/最后回答attempt，不能认调用方自洽hash。来源URL来自实际eligible检索，不能只检查proof有一个URL字段；use1.0旧历史不补URL，不伪升级。
- schema11显式重建SQLite CHECK且保留旧行全部字节；事务中途失败恢复旧schema/rows/user_version。旧fixture必须真实重建旧DDL后再降PRAGMA，不能靠篡版本号声称覆盖真实迁移。
- 旧execution_receipt_for_checkpoint在非transport分支丢protocol/requested_model/response SHA等当前必需字段，是真实转换缺口；应保留HTTP来源字段，不能把缺字段的回答强标已验证。owner投影和checkpoint入口保留原完整receipt hash，generic源集合按native-first稳定去重。
- 并发begin允许同一有效lease重取尚未发送意图，但consume唯一；race loser的具名WorkConflict正是安全围栏。测试须核dispatch实际只有一行/预算只有一次，不能把围栏拒绝当成第二HTTP或通过重试洗绿。
- 完整body/source/cutoff校验不能仅在compact adapter做。actual runner→standard side tables→完整C06→outbox已覆盖，foreign URL拒绝且不部分落库；缺authority保留blocked，并不制造owner golden。fixture的实际发送/响应时点必须处于同一时钟，不能删时间门满足测试。
- 672P只支持私有当前14文件范围，非付费厂商/金融事实准确性或全CLI验收。StockQA public result1.0与IQS ROUTE_02依赖native calls来源集合；对external必须设计显式公共版本/消费者绑定，不能向web_search_calls添加假的native事件。公开C06 generic字段无需改，但生产caller、外仓ACK及真实gold仍各自验收。
""")

append("docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/plan.md", """## Phase111 检查点与执行器接续：2026-10-09
私有schema11/checkpoint2/use-proof1.1保留原native响应与旧checkpoint1字节；实际runner/同步provider metadata、完整standard body/C06/outbox通过672项相关回归。读checkpoint-interface.md；这不是源发布或完整验收。
下一段先补明确公开result版本和IQS ROUTE_02消费者的external来源规则，再接真实runner/cascade调度、异步provider、两阶段/跨lease/MCP/公开CLI。现有public1.0仅native来源，不能暗改历史解释或造web_search_calls。整个Phase111齐备后一次集中审查/正常源Git/严格清理；当前自有根保持，不另建工程回执或小节点门。
""")
print(json.dumps({"recorded": "private_schema11_checkpoint2_runtime", "tests": 672,
    "source_published": False, "phase111_complete": False}))
