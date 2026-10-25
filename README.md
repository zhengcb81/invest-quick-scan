# invest-quick-scan

用联网LLM问答快速了解上市公司，保存带时间、模型与来源的结构化评分和事实。题库支持公司类型、行业、生命周期及恢复观察的组合；不下载或保存公司财报、公告、网页全文。

## 启动界面

在本项目根目录运行：

```powershell
python -m pip install -r requirements.txt
python scripts/open_dashboard.py
```

终端打印本机地址，默认 `http://127.0.0.1:8765/`。端口被占用时使用其他空闲端口，以终端输出为准。浏览器打开后进入工作台，可维护名单、查看原结果、按分数条件筛选、比较时间/模型，并预览和运行已登记扫描包。Ctrl+C停止服务。

界面源码默认位于同级目录 `iqs-question-bank-ui-lab`；运行环境需要Python。代码与数据目录分开时：

```powershell
python scripts/open_dashboard.py --ui-root "C:/path/to/iqs-question-bank-ui-lab" --data-root "C:/path/to/invest-quick-scan"
```

`--no-refresh`只查看已有展示快照；`--port 8766`指定首选端口；`--plan`只显示启动配置。正常打开页面和筛选不调用模型，不运行测试，不会补造缺失评分。

## 题库与公司结果

- 当前基础必做集合为通用核心24题、杜邦7题和波特五力5题，共36题。数量从题库派生，允许扩展；quick/full及分类未知时均保留。
- 公司类型、行业、阶段与属性题按真实适用性追加。杜邦/五力诊断单列，不重复计入核心质量均分；不适用须说明依据，缺证据留空。
- 当前评分题库48模块、222题，另有61道不评分的信息题。信息题面存在不代表公司事实已采集。
- 已导入名单214家公司；已有12份旧草稿关联11家公司。尚无结果的公司明确显示待补，不将未知当0分或5分。历史缺少模型或题库版本时保持“未记录/未绑定”。

完整操作与配置见[工作台使用说明](docs/implementation/company-and-bank-ui.md)。生产结果直接读StockWiki；题库矩阵、旧草稿与旧选股器仍是明确分开的展示快照。当前已将CATL真实已有一题导入原工作区并用原ACK对账为delivered；这验证工程闭环，不代表金融准确性已通过或全名单已有结果。

首次连接时，复制[连接配置模板](examples/dashboard.config.template.json)到本机忽略文件 `config/dashboard.local.json`，填写原工作区与原运行目录；也可在界面的“设置”保存。扫描输入和导入包必须登记到模板对应列表；详细字段、原预算约束及回执步骤见[产品接口与部署](docs/implementation/dashboard-product-contract.md)。未配置时会显示具体缺项，不从公司名临时制造身份、准入或预算。

当前支持固定注册包的预览、执行、任务状态、安全暂停/恢复及入库对账；**为任意公司自动准备扫描包、连续扫描整个名单仍在开发**。本机现有真实工作区为隔离研究库，标签会显示这一点。

## 生成问题与验证输出

```powershell
# 导出完整基础题（StockQA兼容格式）
python scripts/question_sets.py basic --output runs/basic-questions.json

# 按公司profile组合专属模块，不调用模型
python scripts/question_sets.py compose --profile examples/profile.json --mode quick --out-dir runs/example

# 验证默认基础出题，不调用搜索或模型
python scripts/thin_scan.py --company "宁德时代" --out runs/basic-dry-run --dry-run --as-of 2026-10-25
```

`examples/profile.json`是演示配置，需要替换为经核实的公司分类与时间。`main_questions.json`和旧24题清单仅作历史兼容；新完整基础模板是 `basic_questions.json`。冻结路由、新旧版本兼容和标准答案命令见[SKILL.md](SKILL.md)。薄草稿不等于StockWiki正式观察或金融准确性验收。

## 项目分工与配置

| 项目 | 职责 |
|---|---|
| invest-quick-scan | 题库、路由、评分/事实契约、组合和产品薄接线 |
| StockQAbyLLM | 模型与搜索、原任务/预算账本、配额切换、重试及缓存恢复 |
| StockWiki | 公司身份、挂牌与名单、不可变观察、导入ACK及查询 |
| company-wiki | 复用已有身份与共享引擎基础能力；快扫不要求下载公司文档 |

API密钥只放环境变量，不填README、JSON、Excel或浏览器日志。模型顺序与共享额度模板见[模型配置](examples/model-policy.template.json)；检索失败、结果不明和fallback规范见[搜索与LLM实操](references/search-and-llm-playbook.md)。

## 开发与测试

```powershell
# 日常快速层；完整验收按改动边界选择
python scripts/run_tests.py fast --temp-root C:/Temp
python scripts/run_tests.py all --plan
```

不要每次小改运行小时级全套。集成、端到端和原生跨仓层的前置、隔离与命令见[测试说明](docs/implementation/testing.md)。项目当前进度和接续步骤见[task_plan.md](task_plan.md)、[progress.md](progress.md)及[交接文档](docs/implementation/handoff-for-new-agent.md)。
