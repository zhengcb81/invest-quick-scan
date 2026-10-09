# Phase111：真正子进程 CLI 与自动恢复

本段优先于旧接口的“OS 子进程尚未验证”叙述。产品仍仅位于 IQS 独占 `runs/n111a/qa`，生产 StockQA 为 `42a517c` / schema8；私有 schema13、公开输出1.1和原 C06 契约保持。最终集中静态/受影响回归/独立审查、源发布和严格清理仍未执行，不能宣布 Phase111 或任何全局门完成。

## 入口与边界

测试实际以另一个 Python OS 进程运行 `main_with_llm.py`。runner、协调器、配置/身份/manifest 校验、SQLite、费用解析、provider、答案校验、公共 JSON 和封包均使用实际组件。只替换 `requests.Session.request/post` 的 HTTP 边界，使用明确合成的身份、供应商用量和本地价格卡；store 时钟通过其原有可注入 `clock` 依赖控制，未改 SQLite 租约/现金行来制造恢复。

继承原子进程 guard，禁真实网络和自有根外 Python 写入，撤去真实凭据环境，禁止非 Python 子进程。Windows asyncio 只允许其确切内部 socketpair。guard 不是完整 OS 安全认证；这些测试不是厂商真实互通、真实计价、公司事实或 StockWiki owner golden。

## 已实施的两个公开入口缺口

1. 默认 `load_search_policy(path)` 与旧1.0继续要求凭据；CLI显式 `allow_cached_recovery=True` 只对1.1延迟凭据检查。仍校验启用状态、完整schema、身份/题库绑定、价格与保存权限。既有协调器先核真实 owner 缓存；真正的新请求仍经 `ExternalSearchProvider` 的原凭据准入，在健康/预留/HTTP前拒绝。公共准入回执无可用密钥时显示 `external_dispatch_enabled=false` / `credentials_unavailable_cache_only`，不把缓存可读当作发包授权。
2. 生命周期 `before_question` 在 `create_or_attach` 成功绑定确切实体、身份、问题、代次、作用域与路由后，对 leased 行调用原 `recover_expired`，再尝试 claim。store原事务保持活租约；过期但有模型发送意图成为 uncertain；没有模型发送意图才能重新 pending。外部搜索/控制操作是否有未知发送继续由原不可变 journal/Q09判断，不能因重新 claim、撤钥或重开进程消除未知账。

## 验证含义

- REST/MCP、external-only/hybrid及开启思考的 DeepSeek 文本：真实冷进程分别2/5个synthetic HTTP（MCP三控制+搜索+模型），上下文确实进入实际模型input，原生工具仅hybrid有；第二进程撤去HTTP替身和搜索凭据，原回执及费用不变、零新HTTP。
- 五个实际付费结果提交后的断点：父进程在明确barrier处真的终止子进程并记录PID/退出码。新CLI自己恢复过期租约，已结算控制/搜索各执行一次，继续剩余HTTP，最终总支出不重复。不是人工先改work状态再叫CLI。
- 六个实际发送、回执尚未保存的断点：保留可用合成密钥及HTTP替身后重开CLI，仍不能再次发包，原预留和已知支出保持。可输出无分数的失败结果文件；不能制造成功checkpoint或把未知成本填零。
- 缺搜索密钥的全新冷运行：无HTTP、无搜索/控制意图、无费用预留。已缓存答案也不能绕过后来停用线路、撤销保存权限或错误manifest。
- 三个完整标准答案入口：从既有合成C06 fixture派生单题，18条证据和完整body进入真实耐久标准答案及公开合法封包；新进程warm与seal均零HTTP，原包不变，思考/私有MCP session不进入公开输出。未造StockWiki ACK，跨owner链仍待联合验收。

## 原始批次，禁止加总冒充一次 GREEN

- `os-public-cold-first-01`：5F；REST两项因loader提前拒绝撤钥缓存，MCP三项另有新fixture把工具结果数组误包成对象。
- `os-public-cold-red-02`：仅修MCP fixture后5F，均准确定位同一CLI撤钥恢复缺口。
- `os-public-cold-green-01`：5P，18.489s controller。
- `os-public-interruption-first-01`：5P/6F；已付费恢复当时通过测试端显式owner恢复API，未知六项实际没有重发，但错误要求失败输出文件不能存在。
- `os-public-recovery-affected-green-01`：四文件263P，pytest90.59s/controller91.35s。其已付费强杀用例当时仍先显式调用恢复API，不能据此认证CLI自动恢复。
- `os-public-complete-seal-first-01`、`green-01`：各3F；分别是测试错读`observation.score`、错序列化getter的bytes。实际冷运行及封包成功，不是产品故障。
- `os-public-complete-seal-green-02`：3P，controller11.757s；标准body/18证据、独立warm/seal通过。
- `os-public-automatic-recovery-red-01`：撤掉测试端恢复调用后6F/5P，准确暴露五个已付费断点不能由CLI恢复、模型未知仍leased的入口缺口。实际自动恢复最终批次结果以新process/JUnit及PWF为准，不能提前标通过。
- `os-public-automatic-recovery-affected-green-01`实际终态exit0：五文件313P、0失败错误跳过，pytest102.41s/controller103.027s、37执行源SHA不变。35集成实例含24新OS场景，11强杀现不由测试端恢复；其余47MCP与配置/协调/transport回归保持。这是本段有限验证，不是完整Phase111集中签收或金融/厂商真实验证。

`archive_os_cli.py`与追加脚本只复制白名单内的实际子进程stdout/stderr、HTTP轨迹、PID/强杀回执、合成轻量输出与执行guard。短编号目录避免Windows长路径；原目录名、原字节hash和process hash在每批subprocess/index.json。部分原集成案例仅有轻量结果日志，不能把case_logs总数当OS进程测试数量。配置、密钥、数据库、网页正文和任意临时文件不进入此归档；旧日志与索引保持不变。
