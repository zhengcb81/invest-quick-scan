# W15基础软件交付（2026-10-09）

本交付完成原W15步骤1–3的基础软件范围；步骤4正式query/refresh envelope与真实owner golden继续实施，整个W15仍in_progress。全部后续必要授权有效，root唯一writer，不增加逐helper审查门。

## 实际源交付

| 仓库 | 分支/实际commit | 发布范围 | 远端 |
|---|---|---|---|
| StockWiki | master / a5a97d6efbf5f0ee79122a1ec375def388700690 | 15精确路径，路由存储/CLI/增量刷新/备份及测试 | 既有owner决定7无remote，本地交付 |
| StockQAbyLLM | master / 6aafc32eae5339668e893b8a2b246d0655075584 | 16精确路径，Q13动作与原费用/派发事务接线、schema及测试 | origin/master已核与commit相同 |
| invest-quick-scan | master / 929d76226dc2efa8b02e094312baa51fe71076c8 | 555精确路径，含5公共代码/schema、PWF和原字节证据 | origin/master已核与commit相同 |

源交付原件：[source-publication](../../../intake/W15/module-readiness-2026-10-09/source-publication/)。原未知opencode和QA11未知路径不读、不暂存、不清理；保护源码SHA核验通过。StockWiki正常static hook通过，StockQA原正常格式/类型/密钥等钩子均通过，未跳过检查。

首QA提交控制器600秒超时，CIM核实原PID/父子链/UTC创建时间后仅结束自有遗留进程；原失败不改为通过。接续复用本机已安装的相同版本正常pre-commit缓存，五组公共hook安装状态/manifest摘要前后相同，未删除/还原共享缓存。首接续只因正常mixed-line-ending hook将`.gitignore`换行转LF而失败；仅该非运行文件的raw内容变化，原受审字节、规范化字节及Git域摘要分别保留，文本规则不变。第二接续正常提交和推送终态0。测试环境和TEMP仍独占。

## 实际测试与一次集中审查

- IQS公开handoff最终批18P/103.01s。
- StockWiki基础受影响包91P/59.41s；profiles/观察导入批90P/16.73s。范围重叠不相加。
- StockQA主批307P/1F/72.30s，唯一失败是维护后的Q07合成fixture请求模型默认不一致；只改fixture后完整Q07独立8P/3.44s，产品SHA不再变化。不得拼成“一次308项全绿”。
- 静态Black/isort/mypy63源/Bandit四步终态0；保留原阈值和既有诊断。提交正常hook另有真实终态。
- 同一个集中独审最终[concentrated-recheck-02](review/concentrated-recheck-02.json)：candidate02的36路径匹配，软件开放发现0。F1实际双SQLite重核1P，容量等待中owner current漂移被具名拒绝、0新增费用预留/0 send-intent/0 HTTP；不宣称两个数据库分布式原子锁。
- 首完整SW诊断仍为1063P/64F/18skip/21error，原件及同次分类保留，不称全仓通过。不因本交付重复未改代码的全仓/UI测试。

## 能力与边界

StockWiki scan schema6采用加法迁移能力，路由/问卷原文不可变、主体/报表范围绑定、current CAS及历史保真；StockQA原任务库schema14追加绑定，不新增费用账本。复用已锁定逐题语义、原Observation/model/time与已核N/A；新增/过期题经原Q13租约和账本派发，未知计费及跨代未决优先接续。事实answered和关系投影仍未接线。

本批评分软件测试使用合成公司/真实公开OS CLI；只读真实metadata克隆不是金融或查询golden。真实厂商API、公司文档下载、生产名单写入、生产数据库迁移均0。Python守卫不等于全OS隔离。C06 query仍未验证，L03/G3/B01准确性、facts/F05、TH/IN及200家live各按原前置开放。

自有根`runs/w15a`的实际清理状态以intake的cleanup-receipt.json为准；归档只保留源码锁、合成producer原文和过程证据，不保留真实SQLite/公司metadata克隆/配置。下一步见[c06-next.md](c06-next.md)，新独占根接续，不盲跑已清理的一次性控制器。
