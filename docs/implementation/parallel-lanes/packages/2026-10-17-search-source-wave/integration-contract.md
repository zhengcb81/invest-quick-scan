# 三个包共同的工程、数据与交接契约

## 独占写区与输入冻结

每卡写根为唯一可写根，含Git/PWF/源码/内容/测试/临时树/交接；不得写父目录、其他仓库、全局配置或site-packages。Lab尚不存在时可初始化自己根，根已存在先确认属于自己，不覆盖未知writer。不开remote、不push、不改真实数据库/名单。CodeGraph按已有用户授权可为自己根初始化；它不是测试或金融真值证明。使用planning-with-files维护本Lab的task_plan.md/findings.md/progress.md，不能更新IQS根PWF。

明确允许只读冻结的IQS输入（根`C:/Users/郑曾波/Projects/invest-quick-scan`）：`references/search-policy.md`、`references/search-and-llm-playbook.md`、`examples/search-provider-inventory.json`、`examples/search-and-llm-policy.template.json`、`examples/quick_scan/exchange-package.example.json`及本目录六份卡片/共同规范。文件用途是接口背景，不自动授予运行时authority，模板中的身份也不是生产身份正例。

SOURCE另外允许只读下列三个现存Lab的`content/reference-pack.json`、`content/calculation-ledger.json`、`content/qualification-index.json`、`content/research-plan.md`：`C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab`、`iqs-primary-catl-lab`、`iqs-primary-csc-lab`。QUERY仅在自己的卡片列明需要时可冻结这些文件；AUDIT不需要其内容。不得读取旧真实实验答案/计量/模型名/盲审private、任何API key或付费配置。冻结不导入或执行这些Lab代码，也不复制整仓、pyc、虚拟环境、数据库、文档附件。

开工制作`inputs/input-lock.json`，protocol=`iqs.search-lab-input-lock/1.0.0`，包含package_id、冻结UTC、各项原绝对路径、自己根内相对copy_path、用途、raw SHA256、bytes；source commit可选且不能代替raw bytes。对同一文件读前/复制后/读后核hash，变动则整次冻结失败，保留失败说明，不拼多个版本；后续仅用拷贝，不读活动源。不要标成总控预先签署锁。manifest自身raw SHA作为CLI的`--expected-lock-sha256`，独审/final也绑定此值。检查后源更新并不使旧拷贝自动失效，应如实列冻结时间及限制。

检查必需文件、重复键/ID/大小写路径冲突、NaN/Infinity、未知协议、路径外跳、junction/symlink和输出与源码/输入重叠。默认不跟随链接；遇合法特殊路径需明确校验resolved containment，不能靠字符串startswith。已有输出拒绝覆盖，写失败清除本次未完成暂存区，不能留一个看似成功JSON。

## 公共接口与向后兼容

Python纯函数不读env/网络/任意文件；CLI显式传输入/锁/expected SHA/输出新根，禁止从cwd猜输入。每包`python -m <包名> --help/--version`以及卡片子命令；标准stdout一个JSON，诊断stderr；exit0成功、2输入无效、3路径冲突、4不支持版本。README给在无安装条件下设置自己`src`到PYTHONPATH的完整PowerShell示例，不隐含依赖全局包。

所有业务JSON带`protocol`、`package_version`、`source_context`、`limitations`、`content_sha256`和`qualification`。`source_context`含实际锁raw SHA、实际相关输入项raw hash及生成工具版本；CLI从核过的输入计算，不能信用户随手自报。`qualification`固定`production_ready=false, financial_qualification_granted=false, rating_gold=false`。金额/时间/token/真实准确率本包不测则null，不用0代unknown。

提供闭合JSON Schema和与CLI一致的验证器；标准允许可选`extensions`对象承载未来命名空间字段，未知核心字段拒绝。协议和工具版本分开；支持明确1.0.0，未知major拒绝。minor新增不得改已有ID/含义/必填默认；删除或改义另发major/新ID并保留旧fixture。旧1.0.0合法fixture、缺可选项和未知major均入测试，不宣称兼容不存在的未来版本。

`content_sha256`对排除该字段后的业务对象采用UTF8、排序键紧凑JSON、allow_nan=false；raw文件hash另列，不能混用。运行时间/机器绝对路径放独立运行报告，避免污染跨机器稳定业务内容。必要运行UTC有ISO8601时区，日期未知null并写reason；不把retrieved_at替代published_at。实体未知/歧义明确unresolved，不按相似名称猜issuer。

## 离线、测试与清理

本波次0模型HTTP、0搜索API、0网页抓取/文档下载；只读本地有限摘要与元数据。来源不足就记录not_assessable，不造URL/引文/官方日期/金融gold。反事实案例必须显式synthetic且不能用于真实事实参考。不得把同一份材料改几个字段算多个实质案例。

按卡片设计TDD独立预期，保留有意义RED及修复后GREEN；不要写只回读实现的镜像测试。单元负责语义边界/输入，集成真走本包原公共接口及锁，E2E使用子进程从任意cwd运行公开CLI。基于明确synthetic reviewer的E2E只能证明工程链，不能称真实模型准确率。

测试写自己`.test-work/<run-id>`，最小环境不继承真实secret，关闭bytecode/外部cache写，HOME/TEMP指自己根；进程级禁外网/外根写，不能改宿主防火墙或其他进程。只终止自己登记PID/释放自己端口；清理先核绝对resolved根，拒绝外跳，只删本次自有临时树。记录测试前后冻结输入raw SHA、实际临时文件/bytes/PID/端口、删除后剩余0或明确有意保留证据，不声称把原有环境也清零。

## 正式交接

各包`docs/handoff/<ID>/`包含report.md、handoff.json、tests.json、artifacts.json、cleanup.json及review/完整独审证据。handoff protocol=`iqs.search-lab-handoff/1.0.0`，必填package_id/package_version/status/input_lock_raw_sha256/payload_commit/final_head/public_protocols/CLI命令数组/artifact_manifest_raw_sha256/test_report/cleanup_report/review_final/limitations/qualification。测试实际失败/未跑/skip理由必须可见；`ready_for_acceptance`仍待总控验收。

先正常提交实现/测试/数据/schema/行为文档为payload commit，再独审，修复后更新payload并复审，最后独立元数据commit写最终交接避免自引用。不能用未提交字节配旧commit或跳Git hooks。artifacts列每个交付相对路径/raw SHA256/bytes/role，纳入测试/cleanup/review；不hash自身或最终handoff，handoff再引用artifacts raw SHA。tests逐suite列真实argv数组/cwd/UTC/exit/pass/fail/skip及唯一日志路径/raw hash，不覆盖旧日志。payload工作树和Git blob一致性逐项实核；不含.git/密钥/缓存/大文档。review要求见同目录独审规范。
