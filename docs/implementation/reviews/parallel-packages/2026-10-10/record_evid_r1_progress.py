"""Record the completed R1 acceptance once; only the controller owns PWF."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MARK = "2026-10-11 EVID R1续验收口"
summary = """**2026-10-11 EVID R1续验收口（下方旧未接收描述为历史；C06工程仍checkpoint11）：** EVID完整R1收到70498e4，产品44aa204，258原源/91工件/213输入锁均匹配且结束未变。交接公开CLI结构exit0不等于验收；原样隔离修正回归150P/64F，源根绝对绑定令正常输入先拒绝，不能把无关exit2当反例通过。以213项原字节验证的明确合成重定位锁区分语义缺陷，16案中4正控通过，11缺陷案复现；真实Windows junction单项接续复现，共九类根因，另两内容口径静态，仍changes_requested。R1成果保留，本地EVID-REF-02-R2卡准备好，未自动派发/代改源仓，不增加helper门。520文件/183目录strict自有清理完成，实际CIM0；原C06活根/外仓/共享TEMP不动，socket/API/下载0。FACT d00e2b64活动R2，用户授权的CodeGraph已存在，不重复init/验收半成品。9c2f5fed checkpoint11四份获准PWF文档此前已正常提交并非强推到origin，原回执11证明远端一致；私有源码/本次Lab证据与整改卡不自动导出。

**唯一下一动作仍是Phase113步骤4：** 接原compact pool与有界QueryCaptureStore，完成具名search/candidate_set wire、固定snapshot/分页/完整SubjectRef/规则/字段资格与时效；2.0 get_profiles保持。这里只完成外包续验，不关闭C06/W15/G3/F05/L03/B01/facts/UI/TH-IN/全池门；c15a和real-owner-01继续保留，同一整个C06节点完成后集中审查/源发布/strict清理一次。不要重跑EVID旧包或上述已执行控制器，不以150P或合成CLI声称金融准确；先前214P是交付者源环境自报，本轮实际150P/64F二者分别留档。
"""
detail = """
本轮证据/规则见 `docs/implementation/reviews/parallel-packages/2026-10-10/EVID-REF-02-R1-acceptance.md` 与 `EVID-REF-02-R2.md`。接收档案 `docs/implementation/intake/parallel-packages/2026-10-10/evid-remediation-01/acceptance-result.json`、`cleanup.json` 保留全部RED、衍生锁标记、原始stdout/stderr/退出码及正常控制。

控制器/环境错误均保留并区分产品缺陷：外仓Git status在沙箱首次报not work tree，只读escalated明确核实；EVID没有独立AGENTS.md不重复索引，遵循用户给定规则；首次主控basetemp覆盖与包conftest冲突，修正后150P/64F；反例脚本一处列表闭合语法错误在执行前失败，修复并AST预检后用全新记录名执行；首次junction创建被沙箱拒绝，未当已测，获既有隔离测试授权后沙箱外仅单项真实接续，链接本身移除、目标哨兵不变；没有覆写失败或同代码重复跑全部回归。

九类根因：文字共现冒充语义支持、unknown残留值/分计正确、definition绕资本题义、评分端点来源不闭合、staging祖先junction、答案缩请求分母、旧一致性升级accuracy、passed资格无检查记录、正常原样copy的绝对根锁不支持重定位。财务citation语义和Alphabet护城河4..9端点为同轮静态内容问题，不冒充联网复核或新增金融gold。更新Phase114的当前状态，Phase113步骤4仍in_progress；除四份获准PWF/handoff，本轮新增本地验收/整改档案不进origin发布范围。
"""
for name in ("task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md"):
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    assert MARK not in text
    if name == "task_plan.md":
        assert text.count("## Next Step\n") == 1
        text = text.replace("## Next Step\n", "## Next Step\n\n" + summary + "\n", 1)
    elif name.endswith("handoff-for-new-agent.md"):
        text = summary + "\n\n" + text
    else:
        text += "\n\n## " + MARK + "\n\n" + summary + detail + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
print("four PWF/handoff documents updated; full C06 gate remains open")
