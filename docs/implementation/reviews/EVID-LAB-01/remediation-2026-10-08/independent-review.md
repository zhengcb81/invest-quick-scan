# EVID-LAB-01整改集中独审记录

2026-10-08，agent `/root/evid_lab_remediation_review` 对结果62fe8b2、交接HEAD380cb49完成**一次只读独审**；未写文件、运行测试、联网、读取key或初始化CodeGraph。动态结果由总控在新的IQS私有Git副本执行，agent只复核所收到日志与源码，不冒称亲跑。

结论：原固定错误修复，离线重放器可部分签；EL03来源完整绑定与有限值入口、EL06完整来源类别不能按全修好签。提案接收为未签核、非执行草案；生成上限与费用上界需纠正。L02/G3/F05不自关。

| 发现 | 源码位置（结果对应代码） | 总控追加实证 |
|---|---|---|
| 历史单答案绑定可省略 | fixtures.py约87按answer_sha256存在才比对，fixture schema约47缺按case形态要求 | FX032删hash并改答案公开exit0/historical发布 |
| 数字指数溢出 | hashing.py约57仅parse_constant；semantic.py约360把inf判positive | 1e400 synthetic方向公共replay=0/semantic.direction pass，无答案使canonical指纹防线不触发 |
| 混合未知source窗口误判 | semantic.py约500排除不可解析窗口；约544只统计usable全冲突 | 2026 claim+A2025+B未知实际fail，而非abstain |
| synthetic来源标签遗漏 | diagnostics.py约204 duplicate-json硬编码historical | 公共FX021已存在的真实诊断输出一条错标 |
| 草案上限/费用不一致 | proposal config约322 output_limit10000，公式约332/341按5000 | Decimal复算0.82296 >0.48276/0.49 |

总控另在本集中批发现custom日期范围被normalize_period约104–118丢弃：同年不重叠日期实际public period=pass；不强求新增日期分析能力，暂不支持时abstain即可。该发现与agent五项合为六残余组。

原81方法、9固定反例、34fixture/350diagnostics、三归档两新根、34单fixture公开replay都已成功。总控新首5case=2fail3pass/2.68s，集中follow-up六case=6fail/0.64s；后批有重复公共证明，不叫11独立漏洞。final rename失败/同路径重试、Windows目标碰撞及改chunk selfhash仍被原归档拒绝三项通过，不能把静态担忧列作已失败。

双字节104工件/84EOL声明、依赖和fixture hash/定位已有实质改进。isolation的225项及“未读取他仓”是旧文案，改为实际224校验/128独立文件及锁定IQS只读。只读的CodeGraph未初始化沿用之前待授权，不为验收写外仓。

此记录把源码推断和总控亲跑分开：[执行计数](../../../intake/EVID-LAB-01/2026-10-08-remediation/verification/result.json)、[最小故障输入/输出](../../../intake/EVID-LAB-01/2026-10-08-remediation/counterexamples/)。不需要再为这次报告收尾触发第二轮审查；原writer同批修后一次受影响复验即可。
