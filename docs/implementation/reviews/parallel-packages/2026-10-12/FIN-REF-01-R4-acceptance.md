# FIN-REF-01-R4 集中验收与直接修复

**结论：软件和来源说明的剩余问题已由总控直接修复并签收；参考研究保留partial，金融准确性未签收。** 用户明确“验收发现问题直接修复，不用再发整改施工卡”；本轮不生成R5。原90题研究范围保持，72not_started不能由软件绿自动关闭。

## 实际基线与提交

源 C:/Users/郑曾波/Projects/iqs-financial-reference-lab，branch codex/fin-ref-01，原HEAD f4dffda0b15607b497af818474e46ae01a681703，原产品58b4e13/交接bb89392。初始152跟踪、34工件、20冻结输入raw SHA匹配，仅既有.codegraph/未跟踪。

总控产品17精确文件正常commit **6ff65e89dd662c36a313c1d2177bac29fdbc69aa**；当前R4交接22文件正常commit/HEAD **1e7d61717661e1dbf9f24801df3afa6500ea941c**。最终167跟踪文件与候选全部raw SHA一致；90当前工件bytes/raw SHA匹配；98历史交接/schema1.0/fixture保护路径字节保持，源仍仅.codegraph/，没有remote。实际changed_paths与基线至HEAD精确相等。包1.1.0（可选economic_role）、ledger1.0.0、CLI修复声明1.4.1；旧1.0/早期1.1只读入口不升级或授资格。

## 实际问题与修复证据

原完整测试85P，但独立实际数字派生控制证明：OCF/capex写成ratio并标ROIC，公开validate/export都0并发布；正确ROIC把期初输入重复绑定期末facts，也都0并发布。保留原PID/stdout和小输入。

| 控制 | 原实际 | 修复后公开CLI | 依据 |
| --- | --- | --- | --- |
| OCF/capex冒充ROIC | 0/0且发布 | 2/2，不发布 | ledger_operand_role_mismatch；PID21380/67036 |
| 期末重复作期初 | 0/0且发布 | 2/2，不发布 | ledger_role_period_mismatch；PID26836/79120 |
| 合法零NOPAT ROIC | 新明确正例 | 0/0，可导出 | PID60296/11224；未知分不填 |

补齐注册方法的经济角色，已知SEC companyconcept约束curated标签；不据symbol/description猜角色。NOPAT/平均投入资本覆盖声明期间，nopat_avg_ic的期初为start前一天/期末为end当天，流量覆盖声明期。参数缺失/重复/多余拒绝；输入数组重排不改变公式symbol角色。现有零分母/题义/币种/单位/日期/facts绑定保护保留。角色元数据和源URL不是独立核源证明，不授金融准确性。

共享strict_json用于pack/ledger/lock/manifest，重复键和NaN/Infinity/1e999拒绝；每文件5MiB和公开路径累计32MiB、读取前扣额及去重维持，累计预算测试通过。CSC六个deep attempt的入口未定位06066与TLS失败统一到当前pack/attempts/生成器；不再推出所有材料PDF-only。SEC Item1A截断、债务XBRL口径、72未研究说明先前修复保留。

## 完整测试与一次包级复核

最终**103P，0失败/错误/跳过**：PID56876/exit0，进程19.82785秒，pytest19.12秒。原85+新增18；覆盖计算角色/期间、合法ratio与零分子、参数arity、公开CLI拒发布、strict JSON、lock重复键读取前拒、CSC说明。初始定向59P/5F（4测试env未显式+1正例缺标签）、随后完整101P/2正例缺标签均留原记录；补正例经济含义而不降期望，最终103P。

47旧独立validate/export对中46保留原退出码；原“零OCF/capex ratio却标FCF”的所谓正例本身经济含义非法，当前2/2正确拒绝，未改写原期望或日志。新增合法零NOPAT ROIC0/0证明零分子不误拒。这一旧控制更新明确记录，不能称47旧预期全部相同。另两修复反例2/2命中指定语义码，无internal_error。旧1.0/1.1正反读取/导出、20锁和超限读取控制保持。

同一独立agent只读审查认可经济角色/起终期间/CSC/共享JSON与历史入口的修复范围，未写文件/跑测试/收费调用；不是另一逐helper门，也不是金融事实/评分认证。最终公开handoff PID17448/exit0仅shape_and_declared_scope_only。

## 研究、隔离与下一步

90行/三公司各30、18深核题位、26facts、19writer访问摘要；9completed、9gap、72not_started保持，所有分数/区间null。原90研究未缩减；有效partial材料保留，独立事实→评分校准、F05/G3/金融准确性/真实owner与生产发布仍开放。

自有隔离runs/fin-r4-acceptance-2026-10-11-01保存source/candidate、snapshot、guards、原日志/JUnit、控制与部署/清理收据。按绝对范围/file ID/单链接/raw SHA清理257文件247目录，临时输出/复制锁/超限合成输入已删；CIM owned Python0，后续handoff仅重建空TEMP。未下载公司文档、未调用模型/收费搜索、未写生产库或名单；只写获准FIN Lab，保留源.venv/.codegraph和他人README。

回主线[唯一Next Step](../../../../../task_plan.md)：接续已存在的B01隔离工程候选完整耐久回执/登记/Observation到owner ACK；不重放原13HTTP/26搜索/CNY1.268162的30题运行、不补造ID或retroactive登记。之后继续原研究与盲评，不加小审查门。详见[同包独立记录](FIN-REF-01-R4-independent-review.md)、[源仓交付](FIN-REF-01-coordinator-repair.md)。本批9份IQS Markdown正常本地提交；远端仍因此前自动审批范围拒绝而pending，不绕过或称全同步。
