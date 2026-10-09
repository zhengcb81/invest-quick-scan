"""Record actual private-use test evidence, never claim production acceptance."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
CONTROL = Path(__file__).parent
OWN = IQS / "runs/n111a"


def main():
    receipt = json.loads((OUT / "verification/use-affected-green-01/process.json").read_text("utf-8"))
    suite = ET.parse(OUT / "verification/use-affected-green-01/junit.xml").getroot().find("testsuite")
    assert receipt["returncode"] == 0 and not receipt["timeout"] and receipt["executed_source_unchanged"]
    assert suite is not None and int(suite.attrib["tests"]) == 455
    assert all(int(suite.attrib[key]) == 0 for key in ("failures", "errors", "skipped"))
    for name, expected in receipt["executed_source_hashes"].items():
        assert hashlib.sha256((OWN / "qa" / name).read_bytes()).hexdigest() == expected, name
    marker = "## Phase111 实际LLM上下文使用接续：2026-10-09"
    progress_path = IQS / "progress.md"
    assert marker not in progress_path.read_text("utf-8")
    next_step = "**当前下一动作（2026-10-09 Phase111）**：接通真实store验证的上下文使用proof、来源URL与通用结果/检查点/C06投影，再接runner、两阶段/跨租约恢复、MCP和公开CLI。实际LLM同步/异步四接口已绑定外部短context，external-only不发送native工具，explicit hybrid保留独立原生事件。私有schema10；八受影响文件455P/36.24s，0失败错误跳过，执行源码不变；不与历史重叠批次相加。原native回执和实际model/SHA保持，proof仅由实际检索与回答记录派生。原checkpoint1的CHECK/读取/恢复仍只认native，下一段须显式版本/原子迁移并保留历史字节，不能暗改旧解释。读[实际回答接口](docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/answer-use-interface.md)。Phase111保持in_progress，StockQA42a517c/schema8未发布；完整批次集中review/源Git/严格自有根清理待执行。StockWiki四新路径、G3/L03/F05/真实gold/THIN授权原门不变，收费API/200家live/工程回执刷新0。"
    task_path = IQS / "task_plan.md"
    task = task_path.read_text("utf-8")
    old = [line for line in task.splitlines() if line.startswith("**当前下一动作（2026-10-09 Phase111）**")]
    assert len(old) == 1
    task_path.write_text(task.replace(old[0], next_step, 1), encoding="utf-8")
    note = "\n\n" + marker + "\n" + (
        "- 前一heartbeat只读核开工门，三源HEAD及缺前置不变；本goal接续实际实现。仅写IQS隔离副本，没有StockQA或其他源仓写入。\n"
        "- use-red-01实际9F/109deselected/2.50s，新binding缺失；use-green-01实际9F/3.76s，fixture provider_config_ref与真实provider不一致，原Q09拒绝正确。修fixture并保留原日志，use-green-02为9P/0失败，未放宽生产路由。\n"
        "- use-boundary-red-01实际7F/14P/109deselected/4.99s：缺外部proof的hybrid误成功、外来attempt自签、四项检索引用漂移为六真实缺口；另一项为fixture猜错稳定拒绝文字。green-01实际9F/12P/6.18s，实际attempt位于work_transport嵌套字段，错误读取造成回归；修真实嵌套路径后green-02为21P/5.05s。\n"
        "- use-affected-green-01原79500已终态exit0：八文件455P/pytest36.24s/controller37.077s，无失败错误跳过、执行源码SHA不变。覆盖同步/异步OpenAI Responses、MiniMax Responses/Messages、MiMo Chat及explicit hybrid；HTTP替身、真实SQLite/预算。native回执SHA/实际模型不伪改，不保存prompt/reasoning正文，真实API/密钥/下载/外仓写0。\n"
        "- 新私有schema10使用意图不可改写，原实际回答记录派生proof；schema9付费搜索迁移后不变/无假使用。落库失败未发送或发送后未知不重发，原预留守恒。原checkpoint/C06生产投影尚未接，不把客户端GREEN称完整公开CLI或公司答案准确性。\n"
        "- 活跃回归中提前读取OUT stdout路径报不存在：runner capture尚未完成，原79500仍活且只继续poll，没有重启；终态后raw正常归档。该错误是控制器读取时机，不是产品失败。\n"
        "- 已更新计划/发现/接手与实际接口；完整Phase111仍in_progress，集中review留到完整批次。源42a517c/schema8及原七未知项不动，runs/n111a保留；checkpoint04正常IQS Git实际结果随后追加，旧01–03索引/原工件不得覆写。\n"
    )
    progress_path.write_text(progress_path.read_text("utf-8") + note, encoding="utf-8")
    findings = IQS / "findings.md"
    findings.write_text(findings.read_text("utf-8") + "\n\n" + marker + "\n- 实际HTTP和原记录绑定才证明context使用，不能由回答JSON补一个search=true。hybrid原生完成仍必须核外部proof；provider/type/actual模型/实际work_transport attempt及六个检索引用字段都需同源。原receipt_sha256不包含私有proof，保留native历史原字节；最终检查点必须回读owner，而不能仅认自洽hash。\n- 原checkpoint schema1从SQL CHECK到恢复/标准body/C06 adapter都有版本1假设。后续需显式版本化兼容及原子迁移反例，不能绕过native成功条件或把额外键暗塞进旧版。当前455P是软件隔离覆盖，不认证真实issuer gold、事实正确性或真实厂商计价。\n", encoding="utf-8")
    handoff_path = IQS / "docs/implementation/handoff-for-new-agent.md"
    handoff = handoff_path.read_text("utf-8")
    blocks = handoff.split("\n\n", 2)
    assert blocks[0].startswith("**2026-10-09 Phase111") and blocks[1].startswith("**恢复与权限")
    head = "**2026-10-09 Phase111正在实施，优先于下文历史：** 实际LLM context/use-proof客户端接线已私有实现，最新八文件455P/36.24s/0失败错误跳过；原响应、provider/model和native receipt SHA保持。读[连续计划](reviews/QA-NET-01/external-context-2026-10-09/plan.md)、[实际回答接口](reviews/QA-NET-01/external-context-2026-10-09/answer-use-interface.md)和[精确范围](reviews/QA-NET-01/external-context-2026-10-09/scope.json)。唯一下一动作：store验证proof及实际来源URL→通用结果/版本化checkpoint/C06投影→runner/两阶段/跨lease/MCP/公开CLI。StockQA仍42a517c/schema8；runs/n111a/qa私有schema10未发布，完整Phase111未验收，不声称金融答案准确性。"
    authority = "**恢复与权限：** 本批测试79500已终态exit0，其他本批handle均终态；不可poll/restart它们。独占runs/n111a继续保留，禁止盲跑旧checkpoint01–03/publish/cleanup，checkpoint04按实际Git回执判断一次性执行。原opencode/共享TEMP/Phase92/源七未知项不动。测试同guard剥离真实key、禁外网/根外Python写，提升仅避Windows socketpair问题；不是全OS安全认证。实际LLM/use-proof客户端完成不替检查点/公开CLI/MCP；原schema1 SQL CHECK/恢复/C06必须显式版本化，禁止伪native或暗改旧payload。最终完整批次集中一次review，再正常源发布和严格自有清理；不新增helper审查。StockQA全仓授权须先报备，StockWiki四新路径、TH/IN精确写授权、G3/F05/L03/真实gold仍独立缺。"
    handoff_path.write_text(head + "\n\n" + authority + "\n\n" + blocks[2], encoding="utf-8")
    plan_path = CONTROL / "plan.md"
    plan_path.write_text(plan_path.read_text("utf-8") + "\n\n" + marker + "\n实际客户端接线和新schema10 intent已完成私有TDD，八文件455P；见answer-use-interface.md。下一段必须以实际store核proof/来源URL，并明确checkpoint版本/迁移，原schema1 SQL CHECK及消费者假设不可静默放宽。runner/两阶段/跨租约/MCP/公开CLI、整批静态/一次review/源发布/严格清理仍待。只存hash/引用，没有prompt/reasoning正文；源schema8未发布，其他仓0写。\n", encoding="utf-8")
    print(json.dumps({"phase": 111, "private_schema": 10, "passed": 455, "source_published": False}))


if __name__ == "__main__":
    main()
