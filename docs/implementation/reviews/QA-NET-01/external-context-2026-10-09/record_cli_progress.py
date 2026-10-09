"""Append actual OS CLI progress once, without retiring or closing global gates."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

IQS = Path(__file__).resolve().parents[5]
CONTROL = Path(__file__).resolve().parent
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
MARK = "Phase111 OS子进程CLI与自动恢复：2026-10-09"
batch = OUT / "verification/os-public-automatic-recovery-affected-green-01"
process = json.loads((batch / "process.json").read_text("utf-8"))
assert process["returncode"] == 0 and not process["timeout"] and process["executed_source_unchanged"]
suite = ET.parse(batch / "junit.xml").getroot().find("testsuite")
assert {k: int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")} == dict(tests=313, failures=0, errors=0, skipped=0)
for name, digest in process["executed_source_hashes"].items():
    assert hashlib.sha256((IQS / "runs/n111a/qa" / name).read_bytes()).hexdigest() == digest
next_step = "完整Phase111同一大节点最终静态/全受影响回归/一次集中独审，满足标准后精确源Git发布并严格自有清理。五文件313P/pytest102.41s/controller103.027s，37执行SHA不变，38已报备路径。真正OS CLI冷暖、24新OS场景含11强杀断点现由CLI自己恢复，MCP→LLM→公共结果/完整标准C06已验证；读[CLI恢复接口](docs/implementation/reviews/QA-NET-01/external-context-2026-10-09/cli-recovery-interface.md)。仍仅private schema13，生产StockQA42a517c/schema8未发布；StockWiki四路径许可/联合ACK/G3/L03/F05/真实gold/TH-IN原门保持，不刷新退役回执或启动200家live。IQS归档提交以progress实际回执为准。"
entry = """
- checkpoint09正常Git提交推送eb2fb493a1b0014f6113cde23b4e1421262c6ed4，439变化/432原工件staged与committed原字节核对通过，仅原opencode保留；StockQA未发布。
- cold-first-01为5F：两REST准确暴露撤钥后loader拒缓存，三MCP另有新fixture把数组误包成对象。只修fixture后的cold-red-02仍5F，同一缓存准入缺口；config/runner显式1.1延迟密钥校验已修，默认/旧1.0保持、provider在预留/HTTP前仍检查。cold-green-01实际5P/18.489s。
- interruption-first-01为5P/6F/28.036s，五已付费当时用测试端公开恢复API接续；未知六实际无重发，失败是测试错误要求不能保存无分数失败JSON。更正后保留可用synthetic key/HTTP替身证明unknown本身阻断；四文件263P/pytest90.59s/controller91.35s，当时仍不能证明CLI自动恢复。
- 完整标准C06三场景由原synthetic31题fixture派生单题：18证据/完整大body/合法封包，独立warm与seal原包及账不变。两次3F分别误读observation.score、误JSON序列化getter bytes，产品不改；complete-seal-green-02为3P/controller11.757s。不伪造StockWiki ACK/golden。
- 加强11强杀断点移除测试端recover调用，原row确实仍leased；automatic-recovery-red-01为6F/5P/controller25.12s，五已付费不能由CLI接续、模型unknown未转uncertain。runner只在精确create_or_attach后接原owner恢复事务，活租约不动，模型发送意图uncertain；外部unknown仍原journal/Q09阻断。
- 最终原session25656实际exit0，五文件313P/0失败错误跳过，pytest102.41s/controller103.027s，37执行SHA不变。含47MCP与35集成实例、其中24新OS场景；不与263/3/776重叠相加。所有测试handle终态，收费API/真实key/下载/外仓写/生产迁移0。
- 十原批次及实际子进程stdout/stderr/PID/强杀退出/HTTP轨迹/合成轻量结果/guard按白名单短编号原字节归档。部分原集成案例只有结果日志，case_logs数不等于OS用例数；配置/密钥/数据库/任意temp不入档。根handoff定位错误已改读docs路径；外仓默认沙箱只读拒绝后按既有授权提升只读Git核QA42a517c七项/SWc40de21clean，未写。一次PWF整批补丁findings锚点误猜，工具整批拒绝零写，现由本脚本先验证全输入再更新，不报产品失败。
- 下一实际动作完整Phase111一次集中静态/全受影响回归/独审/精确源Git/严格清理；新checkpoint10只私有证据归档，Git等实际回执。原01–09/index/日志保持，不放行全局门。
"""
paths = [IQS / "task_plan.md", IQS / "progress.md", IQS / "findings.md",
    IQS / "docs/implementation/handoff-for-new-agent.md", CONTROL / "plan.md"]
texts = {path: path.read_text("utf-8") for path in paths}
assert all(MARK not in value for value in texts.values())
old = "- [ ] 独占隔离环境TDD实现生产路径，完成受影响单元/集成/公开CLI批次。"
assert texts[paths[0]].count(old) == 1 and "## Next Step\n" in texts[paths[0]]
texts[paths[0]] = texts[paths[0]].replace("## Next Step\n", "## Next Step\n\n**最新唯一下一动作（OS CLI自动恢复后，优先于以下历史）：** " + next_step + "\n", 1).replace(old,
    "- [x] 独占隔离环境TDD实现并完成本段受影响单元/集成/真正OS公开CLI；仍仅私有副本，完整集中验收/发布待下项。")
texts[paths[0]] += "\n\n## " + MARK + "\nStatus: private_implementation_verified_for_os_cli_scope_not_source_published\n\n- [x] 五文件313P与实际OS冷暖/11强杀/完整标准封包，原失败及子进程轨迹留档。\n- [ ] 最终整个Phase111集中静态/回归/独审、源发布及严格清理。\n"
texts[paths[1]] += "\n\n## " + MARK + "\n" + entry
texts[paths[2]] += "\n\n## " + MARK + "\n\n- 新进程必须区分验证已有缓存与获得新发送许可。只对明确1.1的CLI恢复延迟凭据检查，保留完整schema/身份/价格/存储准入；实际provider在Q09预留和HTTP前仍检查密钥。\n- 强杀E2E不能靠测试端先恢复work再声称CLI自动恢复；撤掉该调用后真实6F/5P已驱动入口修复。活lease与未知发送不得被自动过期当作重发许可。\n- 未知失败可生成无分数失败JSON，不等于成功checkpoint。标准Observation分数在answer内，getter原包bytes不可强行JSON化；相应fixture错误与产品漏洞分列。\n"
texts[paths[3]] = "**" + MARK + "（优先于下文历史）：** " + next_step + "\n\n以下旧时点保留，不覆盖本段。\n\n" + texts[paths[3]]
texts[paths[4]] += "\n\n## " + MARK + "\n\n" + next_step + "\n"
for path, value in texts.items():
    path.write_text(value, encoding="utf-8")
print(json.dumps({"updated": len(texts), "actual_passed": 313, "production_published": False}))
