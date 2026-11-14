"""Update only the four already-authorized controller PWF/handoff documents."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
plan=ROOT/'task_plan.md'
raw=plan.read_bytes().decode('utf-8')
nl='\r\n' if '\r\n' in raw else '\n'
anchor='## Next Step'+nl
assert raw.count(anchor)==1
note='''
**2026-10-10最新外包R1查收（优先于下面的writer历史）：** FACT-CONTENT-01新HEAD d00e2b64/result b227b335及完整handoff已实收，109源文件/106artifact SHA/213锁原件一致；隔离115P、原六机械修复正反例通过。但八新机械漏检、旧版公开只读兼容和三原内容问题仍阻断，维持changes_requested，续卡为本地 docs/implementation/reviews/parallel-packages/2026-10-10/FACT-CONTENT-01-R2.md。EVID仍1597a08/R1未提交且新版handoff不存在，handoff_pending，不复验活writer或拿旧交接冒充新交付。独立审查一次、API/文档下载0；严格清727文件/182目录及一个自建junction，p114r1a不存在，原c15a/real-owner-01保留。此包级查收不关闭F05/G3/其他全局门，原成绩保留。

**唯一下一主线动作：** 回原Phase113/C06步骤4：原ACK后的无凭据引用/撤权实际producer-resume-ack3已1P，活租约实际defer1的该例1P；uncertain另一例被原subject_dispatch_context2_required守卫正确挡在发送前（fixture未冻结真实上下文/原生回执，不是产品缺陷）。补齐原真实context及发送前receipt，只复验该未过用例；不重跑已绿引用/活租约。整组resume-e1的360秒超时不称GREEN，沿原保留fixture接续，不重复新模型调用。再完成原search/candidate_set等全pool操作，整个C06一次集中审查/源发布；不增加小节点审查。checkpoint10仍为最近冻结工程清单，最新接续日志不假称已有checkpoint11。七获准Markdown正常Git可做，新私有验收原件/源码/真实DB/golden不扩为远端导出。

'''
assert '2026-10-10最新外包R1查收' not in raw
raw=raw.replace(anchor,anchor+note.replace('\n',nl),1)
old='Status: concentrated_acceptance_completed_changes_requested; two_independent_remediation_cards_ready'
assert old in raw
raw=raw.replace(old,'Status: R1_concentrated_acceptance_FACT_changes_requested; EVID_new_handoff_pending',1)
oldline='- 最新只读观察：EVID仍原HEAD；FACT有R1未提交改动/RED日志，尚无新完整handoff。原验收保持，避免活writer，修订版齐备后再包级续收；不重跑原验收或自动接管Lab。'
if oldline in raw:
    raw=raw.replace(oldline,'- 最新R1实收：FACT d00e2b64完整交接与115P/原六修复已验证，仍有新阻断，续卡R2；EVID原HEAD/R1未提交且新handoff仍缺。原成果保留，不自动派发或代改源仓。',1)
plan.write_bytes(raw.rstrip('\r\n').encode('utf-8')+nl.encode())

for leaf in ['progress.md','findings.md']:
    p=ROOT/leaf
    entry='''

### 2026-10-10 外包R1集中续验完成
- FACT d00e2b64/result b227b335完整交接真实收到，产品提交是HEAD祖先，无remote；109受控源文件/106artifact原件/213输入锁复核不变。新CodeGraph仅用户明确授权设施，源产品/真实库/名单未写。EVID仍1597a08/R1未提交，新handoff缺失，原成果/活writer保留，不能说两个均已交付签收。
- 实际隔离115P/0F/E/S（JUnit90.061s/controller91.548s/50728exit0）；公开handoff35324exit0仅结构。原六整改反例与正常控制确实通过；新八机械反例仍exit0，旧1.0公开入口exit2，另三原内容问题独立静态复核。均同一次包级验收，FACT changes_requested/R2续卡，不新增helper审查。0收费API/公司文档下载，不关闭金融或全局门。
- 控制器错误更正：FC08首次非法basis=historical导致exit2，不计产品行为；仅改合法trailing后47288真实CLI exit0确认2025证据支持2020目标的缺口。首次junction在沙箱创建拒绝不计缺陷；授权同一自有根实际创建后50816真实CLI exit0确认先resolve绕过。第一次CIM匹配1是查询自身，成功复核单列查询PID并记录其他0，最后五已知测试PID均不存在。失败原件保留，没有覆盖日志或重跑已绿全套。
- R1源/输入最后SHA不变、全部五子进程终态及实际CIM0后，先只rmdir自建junction本身且其目标SHA保持，再strict lstat/单硬链/set-size-SHA逐件清727文件/182目录；p114r1a已不存在。轻量原handoff/原日志/反例结果在intake remediation-01留档；源仓/共享TEMP/原c15a和real-owner-01不动。actual cleanup.json已存在。
- 主线恢复信息：原ACK后的无凭据引用/撤权ack3真实1P；defer1活租约1P，但uncertain fixture在原subject_dispatch_context2_required前置守卫失败，缺真实冻结context/原生dispatch receipt，尚需补齐该用例。resume-e1整组360秒超时不能算GREEN；最近冻结仍checkpoint10，不造11。下一主线先修fixture只跑未过项，再其余原全poolC06操作和整个节点一次集中审查。
- 第一次外仓Git沙箱拒读已由授权只读升级解决；一次PWF空anchor patch拒绝无修改，后按明确追加/已验证marker更新。只正常发布已获准第一方PWF/接手Markdown到既有origin，新增R2/原交接/反例/源码/数据库不扩入远端导出。
'''
    with p.open('a',encoding='utf-8',newline='\n') as f:f.write(entry)

handoff=ROOT/'docs/implementation/handoff-for-new-agent.md'
raw=handoff.read_bytes().decode('utf-8')
nl='\r\n' if '\r\n' in raw else '\n'
head,sep,rest=raw.partition(nl)
assert sep
msg='''

**2026-10-10最新实收，覆盖后面的R1 writer历史：** FACT-CONTENT-01-R1完整handoff已收到，codex/fact-content-01-r1@d00e2b64、result b227b335，109源/106artifact/213锁一致，115P与原六缺陷修复有效；同次独立集中审查/真实CLI仍找到八机械漏检、旧版只读入口缺口和三内容问题，维持changes_requested。本地验收与完整独立续卡在 reviews/parallel-packages/2026-10-10/FACT-CONTENT-01-R1-acceptance.md、FACT-CONTENT-01-R2.md。R2只写FACT唯一根，不自动派发。EVID仍1597a08、未提交R1代码且remediation-01/handoff.json缺失，等待完整新交接，不代改、不重复旧包验收。727文件/182目录和一个自建junction已strict清理，p114r1a不存在；源成果、共享TEMP与原c15a/real-owner-01保留。0API/下载，所有全局门保持。

**下一工程动作仍是原C06，不加门：** 原producer-resume-ack3的无凭据原引用/撤权1P已实际通过；defer1活租约1P，uncertain该例在原subject_dispatch_context2_required守卫失败，因fixture缺真实冻结context/原native发送前receipt。只补该fixture并复验未过项，保留守卫，不能凭测试stub授权；原360秒resume-e1超时不称GREEN，沿保留原fixture继续，不新问模型。最近冻结仍checkpoint10，未生成checkpoint11。随后原search/candidate_set必须覆盖完整owner名单、不可变snapshot分页/原观察引用，不把100批读当全pool上限；整个C06一次集中审查/源发布/严格清理。新验收私有证据/源码/golden/DB没有自动进入远端，四PWF/接手属于原七Markdown许可范围。

'''
handoff.write_bytes((head+sep+msg.replace('\n',nl)+rest).encode('utf-8'))
print('Updated four authorized controller documents; private acceptance evidence not exported.')
