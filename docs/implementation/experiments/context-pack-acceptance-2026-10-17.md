# CONTEXT-PACK-06总控验收

状态：**工程验收完成，1.0.1已正式签收并正常提交；不授予金融或生产资格**。

| 项目 | 实际依据 |
|---|---|
| 原分支/交接HEAD | main / `169a6735c1ead2d8ece73e1d0776baecdaf398ca` |
| 原受审payload | `54041e324003feecc7f66f915d294305d1df43b1` |
| 原文档修订 | `32e3e70ee24d4af4cc42b1909a7ad1486c47fd80` |
| 原包声明 | 1.0.0，64 passed / 0 failed / 0 skipped，两个独立审查轮次 |
| 总控原件冻结 | 86文件 / 914440 bytes，原件与可修候选分开 |
| 原artifact核对 | 80/81一致；`task_plan.md`声明4299 bytes，实际4810，原hash不一致 |
| 干净输入副本 | 366 consumer文件 / 4359090 bytes，仅锁清单文件，其中14个锁内pyc；0个锁外pyc |
| 锁raw SHA | `968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233` |

本机证据根 `runs/accept-context06-2026-10-17/`，`snapshot.json`绑定交接时真实原件，`original/`不修改，`candidate/`仅放本次修复；原Lab在初始化CodeGraph前Git clean。CodeGraph按既有全Lab授权建立40文件开发索引，不作为验收通过证据。

## 本次检查方式

两路fresh独立agent分别审实现/必要反例/候选修复，以及原交接证据/关键边界/修后独立复审。所有测试使用自有锁内输入副本（含14个锁内pyc）、最小无密钥环境、禁网络与外根写入、明确basetemp；不在原Lab或共享冻结根运行测试。共享输入里的68个锁外pyc来源未明，保留现场，不导入、不删除、不猜归属。`-B`只禁写不禁读旧字节码，不能单靠它宣称执行源来自锁内文件。

此前“无pyc”的测试准备假设已纠正，输入始终按锁复制且未删改；原64题重放不能宣称全程源码执行。修后版本以源码加载器单独关闭字节码执行反例。已有64P与作者passed不能替代总控实测。baseline/selected应真正复用冻结prefix与CODEC，保留全部原题义、证据和公司/期间身份；schedule、plan及analysis的上下文/引用/散列边界以现有契约核查，不另造计量/预算实现。理论前缀布局不是实际缓存命中、价格或金融准确率。

## 交接证据处理

原artifact的过期hash如实保留；原报告标题仍有草稿字样，与终局声明另核。原独审调用身份、实际调用时间和各轮散列也须与留存记录对应，不能由总控猜时间、改agent ID或伪造旧审查。若新代码修复升版，另建本次协调验收记录和当前清单，以真实修复/独立复审及最终文件字节绑定，不冒用旧版本的passed。

已确认交接证据限制：旧调用元数据的round-01返回ID与报告header中的reviewer ID不同，目前没有两者映射的原始证据；这不等于证明未调用，但不能由总控补造映射/时间。旧tests.json指向06:12一轮，源仓同名套件日志已是07:06另一轮，5份stdout不能按旧清单散列绑定。原文件全部保留，当前版本须以本次独立实测及唯一日志路径绑定。

总控独立probe进一步确认：原实现可执行验收自有输入副本中植入的unchecked-hash pyc，即使源`.py`仍匹配输入锁、模块`__file__`表面路径正确。该probe未触碰或导入共享根68个pyc；它证明仅禁写缓存与核源文件散列不足以保证执行来源。此项与schedule/analysis上下文及引用拒绝边界一起按原契约修复，修后必须关闭对应真实RED。

原始冻结第一次因严格artifact检查安全停止，未生成源码副本；改为明确记录needs_revision并冻结实际原件用于复现，没有将失败改作通过。源Git只读受沙箱拒绝后使用已授权提升只读核实，未刷新其索引或改配置。

## 正式签收与复现依据

最终源仓 main/`6054c889aa571a8559227105f04f0a2ed5bd5d66`；29文件CAS写回，受审after raw SHA、实际工作树和最终Git blob全部一致，独立source-commit-binding.json再次核对。源仅`.codegraph/`未跟踪，原仓无remote。包1.0.1；计划/排程DTO protocol仍1.0.0，并继续接收合法旧1.0.0产物，未知版本拒绝。

| 实际验证 | 结果与适用范围 |
|---|---|
| 原实现独立隔离重放 | 64 passed，0 skipped；含14锁内pyc，不声称source-only |
| 修复中候选整组 | 92 passed，0 skipped；早于最后小修 |
| 受影响范围复测 | 27 passed；类型、CLI、排程/CACHE、旧版兼容；早于最后helper pin |
| 最后helper pin后公开CLI | version/help、三个compile模式、schedule、analyze共7条exit0 |
| 另一独立agent | 正常旧七例prefix字节等同、原CACHE输出等同、完整context CODEC展开等同；静读完整防御修复及实际日志 |
| 提交后的源仓版本冒烟 | `iqs_context_pack 1.0.1`，exit0 |

这些测试有重叠，不将92与27相加，也不把最后仅7CLI写成整组重跑。原版新增13/4/3反例及后续3个嵌套类型RED均真实保留。上下文/计划/排程权威、字段形状、路径和冻结源码执行来源按现有契约修复；没有另造CACHE/CODEC/价格/预算实现。

独立复审最终passed/open_findings=[]，绑定CAS raw SHA`85228d45a2798fea0139af28bcb3f2d7b58c184e7dab6a1f0292adf7bc9f5444`、105文件冻结raw SHA`361f57824c34adc0bc08848cf4bb6a0ae8705e5b5fadbea609396dc701c2bc7f`。审查中平台内容检查曾中止，之后不再生成或执行新的字节码/伪模块载荷；候选来源边界由独立静态代码审查、实施者已有测试证据及正常兼容实跑支撑，**没有候选独立对抗执行**，不把这一限制隐去。原版独立E01反例与候选验证分开记录。

原516锁内行、366 consumer、86原件逐项raw bytes保持；共享68锁外pyc raw未变。自有临时清理：实施第一批4178文件/52549622bytes、第二批50文件/1602880bytes，独审558文件/6630498bytes，三处scratch剩余0；原件、输入、唯一日志及复现脚本为必要证据保留。网络/外根写入守卫与最小无密钥环境见记录，0收费API/0下载/0生产库或名单写入。

正常提交前默认Git空白检查将新JSON的CRLF行尾当尾空白，已安全停止；保持相同源码/CAS，仅按命令增加`cr-at-eol`并保留标准blank-at-eol/blank-at-eof/space-before-tab检查后通过，再正常commit hook。未改配置、未跳hook或改受审字节。首次独立source Git只读被沙箱拒后，按已有授权提升只读核对，不写源或索引。

薄归档见[实际日志、独审、CAS和提交](../reviews/context-pack-06-acceptance-2026-10-17/manifest.json)；完整原件与样例保留本机验收根和原Lab，不上传答文或prefix全文。本包没有接入活动T4、生产扫描或正式评分库。理论布局不等于实际缓存命中、价格或准确率。
