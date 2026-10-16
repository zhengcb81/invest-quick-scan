# 共同施工契约

以本包卡片指定的一个绝对Lab根为唯一写区。先检查该根有无现成writer或未知文件；冲突即报告，不覆盖、不清理他人文件。可在自己根建Git、自己的PWF及测试目录。IQS、任何外仓/旧Lab/其他新Lab、冻结输入与现有数据库全部只读。不开remote、不push，不代改上游，不向其他harness派任务。主线的原生schema20真实实验正在运行，不能初始化/打开其SQLite或部署schema21候选。

输入锁复用`iqs.real-experiment-parallel-input-lock/1.0.0`和随包`verify_preparation.py`。发布回执给出锁raw SHA；须核全锁结构和本package的全部consumer文件，文件摘要是原始bytes/SHA256，不是JSON canonical hash。完整子集可异机搬迁；不因原source_path不可访问而追源。重复键、NaN/Infinity、未知版本、缺文件/篡改、大小写路径碰撞、根外链接、writer根交叠必须拒绝。source commit是背景记录，冻结实际raw bytes才是本次输入authority。

固定输入布局：`experiment/{questions.json,board.json,answer-schema.json,metrics.json,identity.json}`是本轮明确选定上下文，board为18事实/9来源。`frozen/trial/evidence-board.json`是原依赖携带的旧10事实fixture，仅为兼容桥保留，**不能静默当成选定board**。`frozen/reference/`仅REVIEW消费，10标量/主观无gold的限制保留。导入根按本包consumer实际有的目录显式选择：`driver`、`tools/codec`、`tools/claim`、`tools/session`、`tools/cache`、`judge/src`（schemas与src为兄弟目录）、`frozen/company/src`、`frozen/evaluation/src`、`frozen/iqs/scripts`、`stockqa`。原包需要configure_frozen时明确传`<inputs>/frozen`，不改其实现/默认路径；校验实际module.__file__属于该锁的源，避免宿主同名src或已安装旧包污染。缺依赖诚实停止，不到活动仓补文件。实际live模型/策略/预算登记和任何真实execution不在本轮输入内；冻结源码内的静态schema/示例不是可执行准入配置，不能以原launcher缺注册为由读取活跃T4登记；CHAOS使用自己的synthetic临时配置。

本轮所有任务全程离线。不读取/打印/复制任何真实API key、环境变量值、账户余额、原生预算DB或本轮真实模型execution；不发模型、搜索、网页请求，不下载PDF/财报/全文。不安装联网依赖或使用CDN/telemetry。使用宿主已有Python环境（总控示例为`C:/Miniconda/python.exe`）；缺依赖如实报告，不隐式联网。原SDK只允许在临时测试中mock原HTTP边界，仍走真实解析器/校验器/临时原生账本，明确synthetic。

不得复制实现既有StockQA HTTP/预算、CODEC标准化、SESSION状态机、JUDGE判定或CACHE计量。直接导入锁住的公开API；必要薄适配留在本Lab、注明版本/来源。不能修改冻结源或monkeypatch业务校验使测试通过。发现上游真实缺陷时保留最小反例、精确源hash和预期行为，返回blocked工作检查点给总控；未修复前不能发布completed/ready_for_acceptance的正式交接。总控修上游并另发新锁后才复验，不追latest。

Python包初始1.0.0。CLI支持显式`--inputs`/`--lock`/`--expected-lock-sha256`，不能靠cwd猜根。成功stdout单一JSON，错误stderr；exit 0完成、2输入不合格、3输出/路径冲突、4不支持版本。已有输出拒绝覆盖；错误不得留下看似成功bundle。所有输入只读，输出目录和原件/源码/锁不能重叠。非有限数/重复JSON键拒绝。对象SHA采用UTF-8排序键紧凑JSON、allow_nan=false；raw-file SHA另列。时间、机器绝对路径与稳定内容hash分开。

测试只写本Lab`.test-work/<run-id>`；子进程明确最小环境，移除真实secret继承，设置自己的cwd/HOME/TEMP、关闭bytecode/cache外写，禁网及外根写入。使用原SDK不等于真实调用，mock必须只在原transport注入点。不得在全局pip/site-packages、用户配置或其他进程上修改网络/环境。需要进程故障时只终止自己登记的PID，不按名字杀进程。清理前验证resolved绝对根，拒绝junction/根外跳；只清本次自有temp/进程/端口，留必需日志。证明文件数/bytes、PID/端口释放、剩余0或明确保留理由，测试前后冻结raw hash一致。

交付目录`docs/handoff/<ID>/`：report.md、handoff.json、tests.json、artifacts.json、cleanup.json，以及review/下全部独立审查证据。复用模板原handoff协议和字段，独审证明作为独立artifact，并在report及tests.single_package_review中明确引用，不重建任务回执系统。tests逐suite列argv数组、cwd、UTC、exit、pass/fail/skip、原stdout/stderr与raw hash；有意注入的预期失败和未解决失败不能混计。artifacts列本根相对path/bytes/raw SHA/role，不hash自身或handoff，排除.git/缓存/密钥。

先提交最终实现/test/docs的payload commit，再让独立agent核该commit及工作树，修复后更新payload commit并复审。最后交接元数据commit引用最终reviewed payload；最终HEAD另列，避免自引用。Git正常hooks不得跳过。`production_ready=false`、`financial_qualification_granted=false`、`rating_gold=false`。只有全部必要测试和独审通过、有效发现清零、清理及输入保持有证据时，handoff.status才可为ready_for_acceptance；这仍只是待总控验收。
