# QA-C06-02 一批整改卡

唯一写根：`C:/Users/郑曾波/Projects/StockQAbyLLM`，原QA writer续接。总控验收产物只在IQS，不意味着交接完成或夺取写权。本卡不派第二writer，不改StockWiki/company-wiki/Lab/IQS公共题义和schema，不调用收费接口。

读[集中验收](acceptance-2026-10-08.md)、[独审](independent-review-2026-10-08.md)、原[完整施工卡](../../parallel-lanes/packages/2026-10-07-wave2/QA-C06-02.md)。保留代码结果7e71b2c、交接a12bc29上的正常能力，不重做QA-NET/Q13。实际开工先读Git HEAD/dirty；如新代码有变，核hunk而非整文件覆盖。7个原未跟踪、生产SQLite与key不碰。

## 四组代码同批完成

| 组 | 已实际复现 | 修复约束 | 同批关键断言 |
|---|---|---|---|
| 1 题义/发布绑定 P1 | 重签definition/semantic/template三例loader接受；错误template的真实CLI发送31后被IQS拒 | 在key/HTTP/费用预约前，把逐题field/construct、scope、definition/semantic/rubric/template/module/method/cohort/cutoff等与实际冻结manifest核一致；复用现有`bind_question_context`或同一共享规则，不维护第二套遗漏校验 | 正常v2/v1原路径通过；每个错定义例和至少一条真实子进程CLI HTTP0、key读取0、无费用预约/成功checkpoint；原prompt/hash/identity负例继续有效 |
| 2 run/scan绑定 P1 | FOREIGN_RUN/SCAN可封；正常31观察均不在work_run_ref | IQS冻结run/scan和实际work/attempt形成明确不可变关系；若是不同命名空间则持久记录/校核mapping，不静默替换。恢复必须原执行，warm复用不借当前时间生成新的完成执行 | foreign context拒绝；正常DB/Observation一致或有可核映射；独立run/attempt ID区分；另进程warm/seal HTTP0。不要仅改fixture标签掩盖缺校验 |
| 3 严格JSON P2 | authority重复版本、body重复score取最后值 | loader/body入口（含嵌套）拒重复键及非有限JSON；别把正文损坏退为legacy compact并提交成功。复用已有严格JSON能力 | 两个原例RED→GREEN、嵌套重复1例；valid v1/v2/body不变；真实CLI拒绝重复authority在key/HTTP前；invalid body明确拒绝/阻断，不补5分/不自动重问 |
| 4 持久full head绑定 P1 | 公开supersede改claim+started_at，重签后接受 | 凡完整Observation的prepare/supersede入口，除envelope/checkpoint外还核不可变完整body/context与原成功attempt；只有校验后追加revision与head，失败事务不留半修订。legacy compact兼容独立保留 | 当前案例禁止修改；分别单改claim、typed metric、metadata、started_at也拒；无新revision/head不变。合法compact→完整升级、旧ACK拒/同ACK幂等、send_uncertain先对账、delivered只读继续通过 |

源码优先沿原卡：`quick_scan_c06_authority.py`、`quick_scan_observation_context.py`、`quick_scan_work_store.py`、`quick_scan_c06_adapter.py`、`quick_scan_delivery_seal.py`、必要`llm_runner.py`；如共享outbox需要局部增强沿原卡`quick_scan_result_outbox.py`。测试放原允许unit/integration范围，先报备本批精确文件。不要改核心public Observation字段/问题语义来让错误观察合法。

## 交接与环境一并收尾

1. `handoff.scope.changed_paths`填真实base→result清单，不得空；authorized_paths只放路径，说明放authorization_scope_ref/findings。`.secrets.baseline`的额外授权保持可核，不扩展或泄漏其内容。
2. future测试用显式独占`--basetemp`、TEMP/TMP、日志/DB/API fake配置，全生命周期清理并留manifest/CIM/hash回执。旧共享pytest TEMP如无法证归属，明确列残余与原因，**不要按编号/mtime/宽glob删除**；不能填false后仍宣布clean。先核具体inventory，是否达交付规则由总控判断。
3. 为原冻结CRLF文件说明working-tree SHA vs Git blob SHA和可复现还原命令；不要偷偷换行或重签IQS冻结输入。方案若要求新增卡外文件，先协调实际授权；不改全局Git配置。
4. 新CLI E2E至少实际子进程cold/warm/seal，stub仅HTTP边界，另进程撤stub也应恢复成功。模拟ACK测试仍标synthetic，不冒充真实StockWiki。保留本次1037历史日志；改后按仓既定相关门一批，不每helper审查。
5. 真实旧v5源码（09f68a6）造有旧包/ACK库→v6原字段/费用/hash不变，migration中途异常全部rollback已GREEN，作为回归保留，不降库删除数据。

## 固定反例与重现

IQS只读测试源：[acceptance_cases.py](acceptance_cases.py)，实际执行原字节：[controller-cases-executed.py](../../intake/QA-C06-02/2026-10-08/verification/controller-cases-executed.py)。共9例（含三参数例）：7RED、2GREEN。输入全synthetic，当前fixture/原v5源在交接与intake；不复制生产库。

源仓路径不要直接运行会落库的pytest。在独占副本中给`QA100_QA_ROOT`=副本根、`E97_OWNED_ROOT`=独占父根并安装本轮guard到PYTHONPATH，再用公开pytest执行上述文件：

```powershell
python -B -X utf8 -m pytest <owned>/controller-cases-executed.py -q -o addopts= -p no:cacheprovider --basetemp <owned>/tmp/boundaries
```

迁移两例需要`<owned>/legacy_work_store.py`等于09f68a6的`src/utils/quick_scan_work_store.py`，原字节与Git commit已归档。fixed root的prepare/extend/run/focused等是本次验收过程脚本，**不是生产命令**；`focused.py`原async纠正超时，不原样反复执行。200方法GREEN与1未确认async要分别报告；如果用既有StockQA离线checks守卫解决Windows asyncio，给精确新结果，不把本轮controller错误归产品。

## 完成与验收只设一个大节点

四组与交接同批实现、相关单元/集成/真实CLI/旧迁移和替代链一批验证、一个集中审查后提交源仓实际commit/handoff。报告每个旧RED→GREEN，保留原始失败证据和原通过能力；公开C06生成命令/golden标synthetic_only。交总控复验后才能签本包；整Q10/StockWiki导入ACK恢复UI/G3/F05另有联合大节点。无需逐函数/逐helper新审查或重跑已结束收费实验。
