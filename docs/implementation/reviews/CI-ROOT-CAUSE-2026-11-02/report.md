# StockQA远端CI连续失败根修（2026-11-02）

当前状态：已完成。最终StockQA0154726的CI与Documentation均completed/success，文档构建与原发布两job均成功，独立审查无开放问题。IQS仓库GitHub Actions共0次运行，本次失败实际来自StockQA。原工程节点通过不代签CI。

## 实际失败与共同根因

GitHub真实证据：[4cffabc CI](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41519233564)、[e5a2781 CI](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41513289638)、[9648aef CI](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41499596533)。三次均依赖安装、black/isort/mypy通过，Bandit B608在以下三处同样失败，pytest尚未运行：

1. `llm_runner.py::assert_question_pack_terminal`：动态构造IN占位符，值原本已绑定。
2. `quick_scan_known_outcome_journal.py::terminal_received_failure`：遍历两个常量表名拼接SELECT。
3. `quick_scan_work_store.py::_company_request_count_tx`：两个动态IN列表，原本也绑定值并COUNT DISTINCT。

并非已证实SQL注入，也不是Node20弃用警告引起失败。修复直接消除动态SQL：两IN改固定 `json_each(?)` 绑定JSON列表，SQLite JSON能力已被原Store触发器/其他查询依赖；表名改固定UNION ALL查询。原工作范围、物理请求去重、费用上限和事务不变，不加nosec/全局skip/吞退出码。

`pre-commit`故意保持轻量，不含Bandit或pytest；本地hooks通过/推送成功不能证明远端绿。此前总控遗漏了对真实Actions结果的收尾。现复用已有 `scripts/checks.py` 默认短CI，不往每个commit加重hook或跑小时full；README补清节点交付与远端状态，新增SQL11例纳入原daily测试包。

## Bandit通过后继续发现的失败

首次完整default：Bandit0，pytest 5F/286P。

- Q07四旧例在完整标准答案后追加同一个score8，却期望error。这与已实现的同值冗余兼容协议冲突；改为真正score7冲突负例，另两authority版本均加同值可保存正例，原答/原CP保留。
- async默认预算绑定拿到成功响应，却因公开正文journal要求请求hash、原捕获函数仅认pack/1.2工作而缺hash。同步默认预算绑定同样存在潜在遗漏。共用 `quick_scan_request_identity_required` 现对任何原work/pack/budget绑定自动启用；实际最终发送body已有统一计算，沿原send_intent/receipt/journal使用，不让调用方补参数或补签。未绑定legacy仍不加hash，真实错误/冲突保护不改。
- 原budget用例扩sync/async，实际post1次、原账本费用/并发正确、body摘要=receipt=原visible journal，并可取回原公开正文。并非只修测试断言或放松数据库校验。

## 测试与独审范围

- 实际远端3份完整日志保存在总控自有 `runs/ci-repair-2026-11-02/<job_id>.log`，jobIDs为125530648409、125510307979、125463339566。只读使用该GitHub仓库原凭据；不打印/落盘密钥，跨域签名日志下载剥离Authorization。
- 新SQL11个实际SQLite行为例：空/未知/重复/引号/Unicode/注入样式字符串/1200个ID、普通+pack同一物理请求去重、已CP/已交付/无关work边界。首定向62P/1skip，跨仓纯合同模块缺失的skip不算通过；非作者后来补原IQS纯合同只读依赖后27P/38.03秒，含真实Store cap/pack计数、终态和SDK接续。
- 非作者Bandit全src0/7.46秒；小尾32P/11.07秒，含sync/async默认journal落盘、冲突重复负例/同值正例、未绑定legacy与默认vendor路径、daily测试目标。非作者`ci_root_review`审最终源码无开放阻断，不代替新远端结果。
- 自有C:/Temp仓库副本，去密钥、阻外网但允许Windows asyncio自用loopback，finally清理；不改真实工作库/名单/原UI配置、无收费API。首guard阻socketpair是环境错误已改wrapper，不当产品RED或改工作流绕过。没有运行小时full。

## 完整默认入口结果

最终隔离副本运行 `python -B scripts/checks.py`：black、isort、101源码mypy、Bandit、pytest、CLI smoke全部通过，pytest **305 passed /54.73秒**，总计105.10秒；副本已自动清理，0新API。新增SQL11例已纳入该次default，未只跑静态或挑选通过的测试。日志 `runs/ci-repair-2026-11-02/default.log`；首次5F/286P保留为 `default-pytest-red.log`。

源码与回归/README共10文件提交StockQA `ee8f49ab8b2ebded2b2a1441612cf43ee2198213`，正常hooks全部通过并推原origin/master，tracked clean、未跟踪其他文件保留。该提交未修改工作流、precommit或依赖版本。新远端[CI 41522697950](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41522697950)和[Documentation 41522697894](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41522697894)结果已核：主CI success，Ubuntu/Python3.10完整入口302P/3个Windows-only平台skip，33.78秒；Documentation build失败，见下节。测试组有重叠，不累加成独立测试总数。


## 同提交文档构建的进一步根修

Documentation 41522697894 / job125542470432在MkDocs渲染 `api/config.md` 时抛 `Highlight.__init__() missing ... md`。远端实际解析为mkdocstrings1.0.6/python-handler2.0.9/pymdown12.3；docs可选依赖原来仅下限，而本机安装1.0.3/2.0.2/11.0.2，说明本机既有环境不能验证新鲜远端解析。

[上游#829](https://github.com/mkdocstrings/mkdocstrings/issues/829)确认1.0.6与pymdown>=12.2构造器不兼容，兼容12.1。官方PyPI/发布记录中最新mkdocstrings1.0.8要求Python>=3.11，而本项目承诺>=3.10，不通过抬高Python底线解决。

只修改现有pyproject docs5项与requirements-lock同步：mkdocs1.6.1、material9.7.7、mkdocstrings[python]1.0.6、mkdocstrings-python2.0.9、pymdown12.1。保留真实API文档生成、实际错误非零以及既有发布逻辑，不skip构建。非作者核官方包Requires-Python/依赖与源码版本同步，兼容3.10且无开放问题；全新TEMPvenv按最终-e.[docs]安装成功、pipcheck无broken、实际Highlighter构造成功，完整离线MkDocs build11.65秒且api/config、api/core HTML存在。wrapper109.56秒，环境及下载/构建文件自动清理、0API；本机为Python3.13，非作者核实际日志与依赖要求无开放问题，该本机结果仅证明3.13；随后最终远端workflow已确认Python3.10也通过。修复0154726正常hooks通过并推原origin，仅2文件，没有改工作流或部署权限。


## 最终真实远端结论与交接

最终StockQA `0154726465a427f7b6b7e5f726bf5833841f73a7`：

- [CI 41523660779](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41523660779)：completed/success，Checks job125545736625成功。
- [Documentation 41523660825](https://github.com/zhengcb81/StockQAbyLLM/actions/runs/41523660825)：completed/success，Build job125545736694与Deploy to GitHub Pages job125546097617均成功；实际Python3.10，不只是本机3.13推断。

GitHub最终结果薄摘要在 `runs/ci-repair-2026-11-02/remote-final-docs-fix.json`。此前ee8f49a主CI成功而Documentation失败及更早红记录均保留，不改签。IQS本轮仅更新根PWF、交接和本报告并推既有origin；其他writer README/未跟踪文件保留。StockQA最终tracked clean，正常hooks/CI未关闭，没有新门禁、审批或审查回执；真实库、名单、模型、预算和原UI配置本轮未变。
