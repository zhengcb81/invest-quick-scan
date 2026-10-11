# VIEW-01 集中验收

2026-10-11。结论：**changes_requested，保留交付，原 writer 续做同包 R1。** 原测试通过，关键消费与展示边界仍有缺口；未签收 U01–U04/O05/X09 的真实接线或生产 UI 门。唯一整改入口：[VIEW-01-R1.md](VIEW-01-R1.md)。

## 实际基线与有效成果

源仓 `C:/Users/郑曾波/Projects/iqs-viewer-lab`，分支 `codex/view-01`，base `67bf77e33a84f3fc33e470df1aa62717ecb23150`，产品 `dcf5305791bc440b1334256fddf7e1abb0c6e5a4`，实际 HEAD `dff410526ef4475845db885994f2eee5c9805cd6`。产品是 HEAD 祖先；无 remote；冻结时干净。124 跟踪文件、122 工件的 bytes/raw SHA 均匹配；18 个 VIEW 输入匹配原锁 `105602ed7f50947cf625da07f25fa07a36bd72611bd6a5cdf973ce32e78c4aba`。

交付保留：原生 HTML/CSS/JS、标准库 loopback 只读 server、静态资源无 CDN、动态文本使用 textContent、恶意 HTML 不执行、不自动抓来源；null 不填 0/5，bool/11 标异常；实际模型与三种时间分列；实体计数去重而 scope 分行；风险/恢复/缺口分区；正常列表筛选与返回；2000 合成行性能用例。旧卡 wire 简写有误，worker 按冻结 schema 将 pool scoped 映射为 2.5.0、review-lead 为 2.3.0，属于正确处理，不要求改回错误版本。

公共 handoff 校验 PID18816 exit0，范围仅 `handoff_shape_and_declared_scope_only`。它不能证明 financial accuracy、owner authentication、比较资格或生产验收。

## 集中运行与独立核查

仅在 IQS 自有 `runs/view-acceptance-2026-10-11-01/source/` 的逐文件冻结副本运行。原 suite PID18048 exit0，42.80秒：**71P/1skip，共72项**，含10项真实 Chromium E2E。跳过是 Windows 无符号链接权限，未从分母删除。Python父子环境只传系统运行变量和自有 TEMP/PYTHONPATH，无 API key；现有 pytest/Playwright/Chromium 复用，未安装依赖。运行命令：

```powershell
python -B -X utf8 -m pytest tests -q -s -p acceptance_browser_guard --log-file=<自有日志> -p no:cacheprovider --basetemp=<自有临时根>
```

`acceptance_browser_guard` 是验收目录内的隔离插件，不修改产品/断言；Python audit 限自有写入与 loopback。独立浏览器另在创建 context 后立即配置外部请求 abort，实际请求清单全部本机。此约束针对测试请求，不声称 Python hook 是 OS 级浏览器网络防火墙。

另有 **15组公开 validate CLI 控制**，全部是带重算 artifact bytes/SHA 的合成软件输入；有3项以 traceback/exit1崩溃。不是15题金融测试，不计算“回答准确率”。独立浏览器 PID11976 exit0，6场景，四类语义错误实际渲染，另外两类导航/焦点缺口实际记录。所有原 stdout/stderr、PID、argv、原始 SHA、case bundle、截图和 trace 留在私有验收目录。一个独立 agent 静态审查与本次结果合并，见[独立审查记录](VIEW-01-independent-review.md)。

| 根因 | 实际证据 | 影响 |
| --- | --- | --- |
| 展示声明越过可信边界 | `banner-none` exit0，浏览器醒目提示为空；labels 将 unknown 显示成“已评分”；unknown/score5 显示“未知（未评分）”同时“5 分”；recovery.contributes_score=true 被输出 | 不能让文案覆盖演示等级或把非评分状态变成有效分；恢复字段尚未实际参与加法，但接口与“不加分”说明矛盾 |
| 外壳 supported 不等于真实 wire 支持 | raw schema9.0/operation other 仍 supported 并提取7题；未来 wire 的 watermark=null 与 response=[1] 各 exit1；data_kind=[] exit1；bundle schema 自身重复 additionalProperties | 真实 owner 不可按路径/hash便声称兼容；未知报文也会使查看器崩溃；规范与手写校验不一致 |
| 比较/事实未绑定 owner 证据 | `self-comparison-only` 的 source=self，浏览器显示“owner 判定：可比”；同题最后一条声明覆盖全组；事实能力仅信顶层 capabilities，不消费真实 capabilities exchange | 并排阅读可保留，具名比较资格未实现；冻结2.0 ObservationProjection无比较字段，不能冒充已支持的 owner 入口 |
| 快照/范围/分页丢失 | 旧列表名称华星，详情变 NEW_SNAPSHOT_ONLY；请求只有 sid，不带快照/revision；partial owner rows100/matched150/next_cursor场景被称total100，cursor丢失 | 同公司跨时点会混读，不能把已加载一页误称完整股票池；该partial控制含重复行，仅用于字段消费反例，不是合法真实owner golden |
| 详情/交互未完整交付 | 原池两挂牌，正式详情无挂牌；scope_as_of未提供；键盘进详情焦点落BODY，返回未恢复行；浏览器返回#/pool仍显示“华星”筛选和3行 | 需要准确缺失态及供数映射；桌面能读但字段很密，窄屏把六列挤到逐字换行，单纯无页面溢出不等于可用 |

“self-comparable”早期控制改的是第一条，同题后条覆盖了它；该记录保留用于证明覆盖行为，不把它算成自述可比的独立成功复现。后续 `self-comparison-only` 与真实浏览器才是有效复现。原 demo 也有“coverage undefined”“field_id null”可见缺口，应在同一详情/契约整改中处理。

## 隔离与收尾

用户授权 CodeGraph 实际 init 成功：23文件/431节点/408边，仅新增未跟踪 `.codegraph/`。124 源业务文件与124冻结副本均再次校验不变，HEAD不变；未修改 Lab 产品或他人仓库。收尾实际值见私有 `closeout.json`：所有自有服务退出、独立浏览器5个端口释放、匹配本次根的 Python/Node/Chrome 活动进程0；按路径、文件ID、单链接、bytes/SHA精确清理自有临时/profile/性能生成物。保留原件/案例/日志/截图，不清理来源 Lab 的 runs。

无模型/收费搜索、生产DB/名单写入或公司文档下载。网页来源没有访问。本次只交 Markdown 验收与整改/PWF，不发布私有原件或源 Lab。金融、G3/F05、UI生产接线、一键和全池门继续开放；B01 checkpoint30主线不由此替代。
