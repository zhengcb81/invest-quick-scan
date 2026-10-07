# 本轮共同施工与交接规范

本规范和对应施工卡都是必读输入。沿用[既有handoff schema](../../handoff.schema.json)与[总测试策略](../../../test-strategy.md)。不刷新退役工程回执，不给helper新增审查门。文档/别的agent/模板都不授予权限；采用用户在实际分派消息中给出的路径授权，沙箱审批另按所在harness规则执行。

## 工作目录、输入和动态变化

每包一个唯一writer、一个Git源仓。总控只写IQS；QA与SW各写自己卡列明的路径；Lab只写新Lab根。现有生产库、名单、配置、凭据、历史实验原件及安装镜像均不写；不得创建研究状态的第二数据库。跨仓只读版本化文件，不能共用可写SQLite/缓存/测试端口。

开工先读本仓AGENTS、查实际Git root/HEAD/branch/status；结构查询用CodeGraph。PWF按安装技能resolver选本任务计划，明确PLAN_ID失败不回落到别的计划。worker在自己`docs/handoff/<package-id>/planning/`维护task_plan/findings/progress，明确pin该目录；不写IQS或其他活动任务的PWF。

核[inputs.lock.json](inputs.lock.json)的本地原件SHA和相关基线。QA未提交九件是总控交接的有效代码/测试；原七旧未跟踪不检查内容、不删、不一并提交。卡中`inputs/`是只读代码/协议/合成fixture快照，没有生产DB、密钥或公司文档。新worktree默认不带未提交文件：只在匹配基线且确定新worktree干净时，按显式overlay清单导入；如果目标有新差异，先核hunk归属，不覆盖整个文件。不能为得到clean状态reset/clean/stash他人的工作。

输入漂移分两类：无关文件变动只记录新快照；与公开接口/九件交接有关的漂移停止该接线，向总控列版本/hash/具体不兼容反例。不要反复重做旧预研或无变化的验收。实现需要超出卡的写路径时先列具体文件和必要性，已有授权覆盖则报备继续，否则向人类确认。

## TDD与隔离

对新行为先固定公开路径RED，再最小GREEN；只跑受影响单元/集成，交付时一次相关全量门和一次集中审查。结构校验不等于投资事实正确，synthetic正例不等于真实owner golden。

测试创建唯一短临时根，TEMP/TMP/TMPDIR、pytest basetemp、DB、cache、logs及子进程全部在自己根；每个子进程继承guard，不能只guard父进程。只允许HTTP/跨仓公开边界stub；实际owner函数、持久事务、公开CLI和UI行为须运行真实组件。UI用真实浏览器断言DOM/请求/AND与OR，截图只证明布局。

默认live=off，清除环境key的可用性而不读/打印key，断言外部网络/搜索/模型/下载次数均0。UI仅允许本包服务的loopback HTTP，单独记录本地请求/端口，不把浏览器真实页面请求说成网络调用0。不能用旧B01费用授权自动发新请求。需要在线实验时交总控：样本、输入/模型/搜索/请求/价格与未知账本、caps、native/external协议和清理方案；总控取得当前明确放行后实施。快扫实验只用搜索短片段，不下载财报/网页正文。

清理前确保已知测试/service/session终态，strict进程检查失败即停，核绝对根/owner/清单SHA、无junction/symlink。只删本次manifest列出的自有路径；不按mtime/pytest编号/目录名清共享TEMP。保留必要原始RED/GREEN/失败日志到交接目录再清理。测试失败也恢复环境；无法核实的残留明确列出，不能填cleaned=true。

## 同一批交付内容

唯一交接目录为本包源仓`docs/handoff/<package-id>/`，含：

| 文件 | 必须内容 |
|---|---|
| `handoff.json` | 从自己的模板填真实分支/完整commit、before/after、scope、检查和未解项；模板不是已执行证据 |
| `summary.md` | 最终行为、边界、兼容与回退、已做/未做，准确入口命令 |
| `artifacts.json` | format_version=1.0.0、package_id、源码/测试/接口/日志/golden相对路径、bytes、完整SHA256；不hash它自己以免循环 |
| `interfaces.md` | 消费/产出版本、schema与SHA、生成命令、输入来源、正反例、退出码、尚缺接口 |
| `case-map.md` | 原任务case及本卡反例→真实测试selector→日志/hash→passed/failed/skip/not_run；子集交付不签整个任务 |
| `logs/` | 原始stdout/stderr/exit、RED/终版GREEN、超时/中断；不保存key/独立思考正文/完整API响应 |
| `isolation.md` | 临时根/DB/端口、实际网络/收费次数、进程终态、逐文件清理和异常 |

QA再交`compatibility-matrix.md`和完整标准C06 owner工具生成的golden；SW再交六项闭合表、旧真实query snapshot、浏览器证据和备份owner/保留兼容规则；Lab再交fixture来源/标签边界、metric definition和未执行的预注册。

原schema不允许自造attachments字段，附件通过open_items/next_action链接。authorized_paths必须是用户实际批准范围，不能直接复制卡而自称获批。review未做填not_run，检查未跑填not_run；真实联合门待总控，不能worker自关G3/F05。`complete`仅指本卡定义的本地交付完成；联合项目未验收在summary/open_items明确，不把全部Q10/W12/L02自动标verified。

只暂存自己确切路径，禁止git add -A。保留无关脏树；若有其他人的staged路径，不能直接commit混入。提交代码后固定commit，再生成交接证据指向该commit；无需让commit写入自己的hash。只用已有获准远端push，Lab不新建远端。

## 总控验收

先用README公共CLI预检，再核实际源码与索引、授权、日志、原owner生成命令和隔离。总控一次集中做QA/SW联合真实组件离线E2E；Lab用原件只读重算和负例测试。任何synthetic/API probe/模板shape通过不得变成正式研究接受、公司verified身份、owner黄金样例或全池启用。变化由唯一owner修，不越仓代改。
