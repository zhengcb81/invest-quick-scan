"""Unreviewed C06 progress checkpoint; never publish a half-built public API."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/'runs/c15a'
OUT=ROOT/'docs/implementation/intake/W15/c06-query-2026-10-09'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    result=json.loads((OUT/'contract-green-01.process.json').read_bytes())
    assert result['returncode']==0 and result['terminal_confirmed'] and result['source_unchanged']
    executed=json.loads((OUT/'contract-green-01.sources.json').read_bytes())
    snapshot=OUT/'private-source-01'
    assert not snapshot.exists() and not (OUT/'checkpoint-01.json').exists()
    rows=[]
    for name in ('scripts/query_contract.py','schemas/quick_scan/query-v2.schema.json','tests/test_query_contract_v2.py'):
        raw=(OWN/'iqs'/name).read_bytes()
        assert sha(raw)==executed[str(Path(name))]
        target=snapshot/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
        rows.append(dict(path=name,bytes=len(raw),execution_sha256=sha(raw)))
    guard=(OWN/'guard/sitecustomize.py').read_bytes()
    assert sha(guard)==result['actual_guard_raw_sha256']
    (snapshot/'isolation-guard.py').write_bytes(guard)
    (OUT/'checkpoint-01.json').write_text(json.dumps(dict(state='private_in_progress_not_reviewed_not_published',
            snapshot=rows,guard_raw_sha256=sha(guard),pytest_passed=21,pytest_wall_s=0.38,
            actual_pid=result['pid'],process_sha256=sha((OUT/'contract-green-01.process.json').read_bytes()),
            original_public_IQS_inputs_unchanged=True,source_written=False,API_requests=0,
            real_company_golden=False,nonempty_observation_projection=False,full_C06_validated=False,
            whole_W15_complete=False,owned_runtime_keep=str(OWN)),indent=2)+'\n','utf-8')
    next_clause=('当前原步骤4在新独占runs/c15a连续实施，64原IQS输入不变；私有query v2首批21P只覆盖get_profiles空覆盖/主体绑定/严格JSON，'
        '未审未发布且非空Observation故意拒绝。唯一下一动作补原Observation/模型时间/范围/水位及legacy读取反例，再公共只读producer/受控刷新/真实serializer golden，'
        '同一完整查询节点结束集中审查。不能把private-source-01发布或把C06标通过；根仍在使用，不能清理。')
    progress=ROOT/'progress.md'
    with progress.open('a',encoding='utf-8') as handle:
        handle.write('\n\n## 2026-10-09 原W15步骤4接续：私有query v2首组TDD（当前）\n\n'
            '- 基础源与555件IQS归档929d762已推送，随后仅15件PWF/实际Git日志补记bc9ab49已推送，远端同HEAD、原opencode保留；'
            '源SWa5a97d6/QAc6aafc32不变。新prepare只读核三仓实际基线，固定64件IQS非秘密scripts/schema到runs/c15a，0外仓产品写/真实数据读取/API。\n'
            '- 先冻结query-v2-interface实施约定，EntityId与法律issuer保持分层、明确SubjectRef/expected request/owner绑定，原legacy v1文件不改。'
            '首次控制器在pytest前因Windows guard字符串LF摘要与raw CRLF不符拒绝，0测试执行；保留inputs01，以guard-byte-domains01明确内容/执行两域，守卫内容不变。\n'
            '- 实际RED contract-red-02原70668/pytest2，1 collection error为新query_contract模块缺失，不能称21个产品漏洞。'
            '私有实施后GREEN contract-green-01原67912/pytest0，21P/0.38s/controller0.835s，67文件执行SHA前后不变；只验证合成空覆盖/主体/范围/重复键/非有限JSON。'
            'snapshot三候选＋原guard字节留档，未独审未发布；非空Observation仍maxItems0/具名拒绝，不冒充支持真实评分或完整query。\n'
            '- '+next_clause+' legacy query/W09/UI/三仓生产源未变；金融准确性、F05/G3/L03/THIN/200家live原门仍开放。'
            '本私有进度checkpoint只归档/提交，实际Git以工具回执为准，不新设小节点审查。\n')
    task=ROOT/'task_plan.md'
    text=task.read_text('utf-8')
    needle='下一步接续原W15步骤4：'
    start=text.index(needle,text.index('## Next Step'))
    end=text.index('基础软件不关闭整个W15',start)
    task.write_text(text[:start]+next_clause+text[end:],'utf-8')
    handoff=ROOT/'docs/implementation/handoff-for-new-agent.md'
    text=handoff.read_text('utf-8')
    needle='唯一下一动作按[c06-next.md]'
    start=text.index(needle)
    end=text.index('当前c06_envelope_validated=false',start)
    handoff.write_text((text[:start]+next_clause+'读[具体接口](reviews/W15/module-readiness-2026-10-09/query-v2-interface.md)和[c06-next](reviews/W15/module-readiness-2026-10-09/c06-next.md)。'+text[end:]).rstrip()+'\n','utf-8')
    findings=ROOT/'findings.md'
    with findings.open('a',encoding='utf-8') as handle:
        handle.write('\n- C06私有query v2首21项通过仅证明空覆盖结构/精确主体和范围/原request与独立owner地址绑定；法律issuer与快扫entity可不同，不能互相猜填。'
          '原Observation、模型/时间/水位与分页尚待同批TDD，maxItems0故意拒非空输出，不声称正式C06已实现。'
          '新runs/c15a保持独占，原64公开输入不变；Windows guard两域摘要明确，未修改guard安全内容，当前外仓源不写/0API。\n')
    print(json.dumps(dict(private_checkpoint=True,published=False,passed=21,owned_runtime_keep=str(OWN))))


if __name__=='__main__':
    main()
