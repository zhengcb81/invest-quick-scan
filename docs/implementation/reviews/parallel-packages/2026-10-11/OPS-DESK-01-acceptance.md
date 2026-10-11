# OPS-DESK-01：集中接收完成，需四组整改

结论：`changes_requested`，保留有效交付，不签收完成。2026-10-11实际收到源仓 `C:/Users/郑曾波/Projects/iqs-operations-lab`，分支 `codex/ops-desk-01`，HEAD `dec3942fbdfe984e024713cb332ca76c8d890f6c`；产品提交 `79b4217d9f9e841bdc59215331ed2485074508c3`、交接提交 `0d210ca`、基础 `24c2484be8b9ef11c3eb77d6fa2d3b80faa8058c`，产品是HEAD祖先。无remote，未替作者提交或推送。

## 保留的有效部分

- 98跟踪文件冻结；96声明工件实际bytes/raw SHA全部匹配，12锁输入冻结副本全部匹配；handoff公开CLI exit0仅证明形状/声明范围。
- 十个故障family、26 incident、17命令条目；独立静态审查核47来源引用全部唯一命中原锁路径/hash。
- 固定unqualified、原币种、费用按物理请求、uncertain先对账、检查点与ACK不同、拟定命令不直接执行的总体设计有效。
- 原基础CLI/中文路径/确定性渲染/拒覆盖、十四个原坏fixture和不执行证据脚本的测试有效。不要求重做整个手册、目录或另写owner引擎。

## 实际复跑和独立反例

验收在IQS独占 `runs/ops-acceptance-2026-10-11-01/source` 副本进行，未在Lab执行代码或修改产品。父/CLI子Python加载只写自有根、拒外部读取/网络/非Python子进程的guard，环境不继承API key。

原57项批次PID4544实际exit1：46P/9E/2skip。九E均为验收guard未适配Windows subprocess audit的 `executable=None`，不是产品失败；保留原日志，修guard02后仅原CLI九项PID60232 exit0/9P。Windows硬链接需沙箱外自有根权限，仅原两链接项PID18008 exit0：1P/1symlink特权skip。累计覆盖56P/1skip，不声称一次57全绿。原harness同样报告56P/1skip。

14个新独立公开CLI控制只有两个正常/合法部分控制符合；十二坏输入错误放行或崩溃。另补两个语义控制：完全没有证据的诚实partial被拒；不可信Markdown/HTML原样进入报告。过程是写本地报告，不存在实际远程图片请求或脚本执行。固定case/期望/实测如下：

| case | 预期 | 实际 |
| --- | --- | --- |
| normal-control / legal-partial-control | validate/render 0 | 两个均0，保留 |
| impossible-utc-date | 拒不存在的日期/时刻 | validate/render 0 |
| refs-as-string / refs-null | closed结构拒收，exit2无输出 | validate0，render1崩溃 |
| unhashable-owner / unhashable-ref | 稳定exit2 | exit1未捕获TypeError |
| excessive-protocol-text / duplicate-state-ref | 按已交schema拒收 | validate/render 0 |
| synthetic-disguised-as-record | 不能把合成件标实录 | validate/render0，状态显示实录摘录 |
| oversized-evidence / oversized-secret-note | 读前有界拒收 | 1,048,577+ bytes真实匹配仍0；超限反而跳过凭据检测 |
| binary-document | 短文本角色不能收公司文档/非UTF8二进制 | 含合成PDF标头/坏编码的证据仍0 |
| hardlinked-bundle | 主输入与证据同等拒链接 | bundle nlink=2仍0 |
| no-evidence-partial | 明确缺口的未认证诊断可读，不造证据 | evidence=[]被exit2拒，未输出 |
| markdown-injection | 非可信字段显示为纯文本 | report包含原伪造资格blockquote、远程image与script标记 |

## 同一次审查的四组根因

1. P1：closed schema与CLI分叉。未执行全部类型/长度/重复引用/日期约束，validate成功不保证render可用；合成类别/标记不一致。统一验证、稳定exit2和无正式输出。
2. P1：读取与轻资产边界。主bundle不拒链接，证据没有实际1MiB拒收，解码失败/超限绕过敏感检查，显示字段检查不完整。读前有界、普通文件/链接闭合，短文本编码/内容明确受控。
3. P1：报告信任边界和partial。用户摘录/缺口/限制作为活Markdown输出，可伪装资格/含远程媒体；真正零证据partial误伤。输出应安全纯文本且保留缺口，无认证/无依据是合法诊断状态。
4. P2：能力声明和协议范围。既有Web UI/CLI存在不等于已提供快扫配置；W16新派发不得以旧preview路径替代耐久permit消费；provisional须按owner明确资格区分，不能全部等同未解析。见独立只读审查与锁内freshness协议。

唯一续做卡：[OPS-DESK-01-R1](OPS-DESK-01-R1.md)。同一稳定候选集中续验，不新增helper审查门。旧有效数据/测试/原失败/1.0字节保留；兼容新增能力具名，不伪造真实owner正例。

## 授权、隔离和证据边界

用户本轮明确授权CodeGraph，实际init exit0、14文件/282节点/268边；源因此仅新增未跟踪 `.codegraph/`，产品跟踪字节保持。不得把总控索引设施当harness越界或代提交/删除它。

私有原过程/反例/guard/source快照在本机自有验收根，最终源保护复核和严格清理见 `closeout.json`。无收费API、外仓产品写入、生产库/名单、网页文档下载或真实owner操作。独立review只读，不重复跑产品测试。

本次仅验收OPS支撑范围，不关闭O02/X02—X09、G3/F05/G5/G6、金融准确性、UI、一键或全池门。B01执行接续主线保持。
