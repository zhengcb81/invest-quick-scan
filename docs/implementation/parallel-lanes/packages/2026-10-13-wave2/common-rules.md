# 独立harness共同施工与交接规范

当前IQS55c2ef5、QA205b749、SW9d411c7已经交付跨模型源码；source支持19，真实旧work仍18，原13HTTP/26搜索/30题/0评分/ACK0保持。ROUTE6829cc6、CHAIN4ea3579、SCORE993e0a9已接收研究候选，不是金融/owner/发布资格。不要重做旧包，也不要从历史handoff推断当前源。具体实际完整commit/raw bytes以本批inputs.lock为准。

## 唯一写入范围和输入

1. 仅manifest中本包新根及authorized_relative_paths可写。根不存在才新建git仓、codex/<包名小写>分支；已存在但无法证明本harness接续归属时停止写并报告，不重置/清空/强制checkout。所有其他现有仓、Labs、StockWiki数据库、用户名单、共享IQS PWF及快照均只读。不得自动接另包、自动推远端。
2. 校验inputs.lock自身rawSHA并记录；对本包input_repositories的每一条，验证bytes/rawSHA后复制到fixtures/<repo>/，保留原相对路径。也复制实际被复用Lab的冻结fixtures，不能改其旧锁、旧输入或重新指向浮动源。执行代码只在自己复制件内；ROOT按包目录解析，不硬编码现有原仓。主仓后续变化不要求停工；使用已冻结输入。收到不同输入必须另声明迁移而非默默更换。
3. 建自己的task_plan/progress/findings，写明输入commit、source dirty快照、自己Git基线、UTC、本地时间、独占根。不存在CodeGraph时遵守AGENTS先询问建索引，不因此停止可独立读取/设计；不能改共享PWF。
4. 复用原validator/json canonical、router/compose、既有EVID与FIN边界；不写第二路由器、计算器、题库、身份库、调度器或LLM客户端。旧emit/build/handoff作者工具是历史过程，不运行它们覆盖已验收内容。只有ROUTE允许在自有TEMP复用原RoutingFixture产生明确synthetic release；不调用源仓publish/activate/current。

## 研究与资格

ROUTE/BLIND零网络，所有包零收费模型/搜索API、零密钥读取、零生产库/名单写。CHAIN允许用已有浏览搜索工具人工阅读公开官方HTML；不得下载/保存PDF、财报或网页全文，只记录结构事实、URL、定位和必要短摘录，遵守工具版权限制。研究访问与离线测试分离。不得因403/登录/仅PDF而伪造已读来源、公开日期或关系。停止理由有证据就是合法partial，不要求强行全绿。

不改原题ID、题义、anchors、权重、metric、scope、正式schema、FIN90个null。不把候选资料的supported、agent审查、多模型多数意见或合成oracle当世界真值。真实身份not_mapped，金融资格false，production_execution=not_run。原定义变化只交带expected_old_sha的proposal，由总控统一CAS决定。

## TDD、包级测试与恢复

少量关键反例先RED→实现→一个稳定候选集中unit/integration/公开CLI E2E和包级内容审查。失败保留，修改后只复跑受影响范围，不每题设门。期望不能抄实际结果、反向喂入路由，或只断言自己填的标签。

所有执行子进程按白名单构环境，无API_KEY/ACCESS_TOKEN/SECRET/PASSWORD；TEMP/TMP、pytest basetemp、cache/HOME若需均本包runs/test-唯一值，python -B -X utf8，禁pytest cache。离线测试阻止父/子外部网络、外部SQLite与写入；Windows NUL和Python executable应精确兼容，不扩大目录/网络豁免。避免全局安装和持久环境改动。原不可变发布器硬链接在沙箱不支持时报告并申请原生隔离执行，不删除安全逻辑。

CLI至少测中文空格路径、随机cwd、真实子进程、两次确定性导出、坏输入零正式输出、拒覆盖、路径穿越、symlink/junction逃逸、duplicate JSON key、NaN/Infinity/1e400、集合/体积上限。有限数超限拒绝不静默截断；未知版本明确拒或按已声明旧版本读取。

清理前记录实际PID/子进程闭包和精确resolved绝对路径，验证只在自有本轮测试根、无外部链接；结束自己子进程后删除创建清单内临时文件，保留失败/通过日志、候选、锁、SHA及研究记录。不要清共享TEMP、另一harness目录或他人缓存。Windows长路径用原生\\?\接口但仍验证规范绝对路径。cleanup如实列未清项，不能先删除再编数量。

## 固定交接

docs/handoff/<包ID>/：handoff.json、report.md、artifact-manifest.json、tests.json、cleanup.json、inputs-used.json。正常本地提交内容，result_commit指内容commit；handoff随后commit另记避免自引用。artifact-manifest列交付文件相对路径/bytes/rawSHA，排除自身、.git、缓存、真实库、secret和临时副本。

复用本批handoff.template与IQS既有1.0.0 schema：verification.checks字段只name/command/scope/result/passed/failed/skipped，result=passed|failed|not_run；actual PID、退出码、日志path/bytes/SHA、耗时、环境放tests.json，check_id和checks.name一致。只自审时review.status=not_run并说明self_review；独审结论按原enum。partial可交接但目标分母不能少。完成本包不关闭全局G3/F05/UI/一键/全池。

只读形状检查（换自己的ID和目录）：

```powershell
C:/Miniconda/python.exe -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-13-wave2/manifest.json --package-id ROUTE-E2E-03 --input C:/Users/郑曾波/Projects/iqs-route-e2e-lab/docs/handoff/ROUTE-E2E-03/handoff.json
```

工具exit0只证明结构/声明范围。总控还核真实commit/rawSHA、实际产品行为和核源边界，再单writer接入。
