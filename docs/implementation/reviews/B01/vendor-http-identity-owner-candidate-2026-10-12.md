# B01具名主体与查询兼容候选（尚未部署）

原同一B01候选在72P真实SQLite封存后推进到显式subject_dispatch_request1.2/execution_profile和observation_subject_binding1.1：before-send不填response ID，after-answer绑定null/nonempty header、physical attempt、response ID和request/response/receipt SHA。旧1.0/1.1协议及旧JSON schema字节保持，原四个blocked检查点不能追认新authority/事前登记。

IQS增query2.6单独dialect，重用原subject/owner/watermark/coverage/答案校验，支持1.2新wire profile与1.1历史，不在旧2.0入口静默接受新协议。query SHA为2.6纳入版本，冻结查询不跨版本混同。新original/binding解析也不能以自报hash取代owner记录或填造header。descriptor从注册schema/实际归档格式计算，StockWiki expected_from_current通过固定IQS CLI和独立frozen manifest取得，不从client profile复制。

软件测试证据分批，不相加为金融准确率：IQS first1F/16P/27subtests是误收集导入TestCase连原10测试，另最初默认pytest log路径guard拒绝未到断言；去掉类导入收集副作用后7新协议＋65旧query共72P。新query wire/profile真实6F/7P随后修正新wire schema/强制profile并贯通OS边界，13新＋65旧共78P，PID32080/exit0/5.566057秒。

StockWiki临时真实SQLite与固定IQS OS CLI回归69P，PID396/exit0/33.470576秒（新3＋旧66）：实际release profile CLI、pre/post不可变记录、原始Observation留存、query2.6与持久capture/replay、owner参数profile不能自报替换。正例身份/expected部分是明确synthetic unit边界，不能冒充生产owner golden或公开路由授权；实际API/模型/金融真值未验证。首次猜错capture测试文件而exit4/no tests ran保留，实际capture纳入新测试。

Capabilities1.2独立schema/explicit CLI选择，暴露execution profile与request/binding版本、2.6 get_profiles；原1.0/1.1默认保持。最初新选择1RED（PID50344）；相关24项为23P/1F（PID8488），新schema旧6条wire上限造成结构拒绝，改新版本7条上限及structured ValueError后仅受影响1项复测P（PID52280/3.0459884秒）。不声称24一次全绿，不重跑已绿旧case；缺owner仍unknown，不初始化源根，financial/full_C06/dispatch与API/数据库写标记保持false/0。

所有修改仍在runs/b01-engineering-2026-10-11-01/iqs、qa、sw隔离候选，未回写源；原live13HTTP/26搜索/CNY1.268162/4不足证据/0评分/ACK0保持。最新candidate字节清单在attestations/checkpoint44.json；不清仍活动候选/旧账本，必要测试scratch按最后整节点清理。无下载或收费API/生产数据库/名单写。

下一步在同节点完成subject-context2/authority3的Observation1.2实际QA发送前登记、完整临时SQLite封存到owner公开导入与原生inspection；同时检查qualified/pool消费者新profile读取，不把未支持行隐藏成空coverage。再接已收到但无有效答案的逻辑终态/原retry决议/CNY refresh与旧USD兼容。完整候选后一次集中审查、核源writer/HEAD/文件SHA、精确提交部署，再从原公开preview/TTY/admission/main做固定三题pack3→pack1真实实验。不追加小helper门，不关闭金融/G3/F05/facts/生产UI/一键/全池。
