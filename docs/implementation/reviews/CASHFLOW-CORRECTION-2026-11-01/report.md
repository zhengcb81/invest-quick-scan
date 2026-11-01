# 现金流期间错误与原生定向复核接线

本节点继续根PWF答案质量主线，不重做已完成的最近扫描缓存正例，不新增客户端、账本或逐题核查凭证。真实结果完成度以本页更新和原job为准。

## 已核实的问题

原CATL IQS_11把2024粗略FCF写为546.45亿元。官方2025年报合并现金流量表的2024比较列为：经营现金流96,990,345千元，购建长期资产现金31,179,943千元；同式应为658.10402亿元。原2025同式908.75424亿元。维护/增长资本开支未拆分，不能把该代理口径称作完整所有者收益。[公司原披露](https://www.catl.com/uploads/1/file/public/202603/20260310105829_c5p2l3q9ll.pdf)。只在线核对，不下载保存文档。

二手文章的算后结果不能独立证明原始输入正确。新请求提示要求先逐期间列出原始输入、单位、公式和evidence_ids，再算指标；优先核对公司/交易所原披露及同表比较列，缺证据删去对应数字/趋势并列缺项，不凑年度序列。旧题面、renderer fingerprint、旧答案/分数/时点不改。

## 接线修复

- 原native comparison机制已支持保留原答、精确N+1及模型/题包/思考/预算绑定；IQS自动准备此前只接1.2不可用恢复。现在显式1.3加精确原工作决议refs，默认普通准备和1.2恢复不变。
- StockWiki及StockQA的原单动作agent委托目的枚举同步支持comparison；保持完整原request/preview/permission/policy/主体/工作/attempt哈希、期限、撤权和幂等。载体本身不能替代native权限或费用预留。
- 原UI识别既有1.1 subset中的comparison，显示“受控复核子集”，仍单列1题/完整36题，不冒称全公司更新或金融认证。
- 真正准备时又暴露source-bank选择遗漏：源工作已delivered，却有精确比较后继决议，旧代码只找unfinished而新造bank，导致原source metadata自然拒。现仅精确匹配原journal comparison决议的已交付源也选择其原binding/bank；普通completed无ref/错ref不选择，当前StockWiki实质metadata检查不放松。已对真实账本只读验证命中原bank `route_3eeac9ccf8dc5852d48fe1059d3f712a9998dfd79a7705cdbf584f6575afeb01`。

## 验证与独立审查

提示组8通过及8 subtests；IQS定向/原1.2短组最终5通过，含实际reader代码的只读port替身，明确不代真实owner；UI原实际ESM相关3通过。StockWiki原模块22项通过后，新增用例读错install摘要的fixture已修正，新增1项通过，共23个不同用例覆盖；不虚称同次23绿。StockQA有效RED后在独占禁网、去密钥的源码副本13项通过，TEMP全部清除。StockWiki本轮已核实的三个合成pytest目录亦已删除，其他会话与共享目录保留。

非作者`/root/fresh_ui_route`在同一产品节点完成源码、测试实际日志和source-bank尾修复核，passed/open_findings=[]，未重复运行大套或写真实库。它确认逐期规则经原shared engine的prompt_rules实际注入新请求，不是闲置函数；原renderer与历史prompt保持。hooks全部保留：QA正常行尾/Black/isort修正后mypy/其余hooks通过；SW新测试导入排序修正后原static hook通过。

## 当前真实运行

原source工作`WORK_3a5fefcc7c6f4876bc1166c7e0ee49fe`实际generation4，比较目标5。初始原控制已recorded但未派发；原UI准备`prepjob_81fcdad6c4714567a310938957d398db`在scope preview因source-bank遗漏退出，0模型HTTP。已从原UIabandon保留，再经原route activate+精确CAS恢复原bank，保留新旧route历史。旧控制窗口已过，未改旧记录；修复后重新取得当前范围的显式控制，仍同一目标代次，非模型回答择高重问。

截至本页初记，累计仍84HTTP/US$1.974640，0新模型请求；真实新答案、第一方数字对照及原ACK尚未完成，不提前关闭IQS_11。当前临时owner policy10为1.3比较模式，原普通配置备份在本机`runs/cashflow-correction-2026-11-01/`；在未决任务结束前不盲目复位，收尾后须恢复普通策略并移除专用refs，原日期不续期。

## 提交范围

StockQA `c6854fd`已推既有origin/master；StockWiki `1bde9e0`、原UI `0212c5c`已提交，两仓无remote不创建新远端。IQS本节点源码/文档由根正常提交。原服务、原库、原失败事件与已发生费用保留；不提交私有配置、原回答或捕获正文。
