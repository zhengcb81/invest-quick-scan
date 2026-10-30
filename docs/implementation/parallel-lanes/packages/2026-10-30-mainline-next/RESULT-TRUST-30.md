# RESULT-TRUST-30｜让用户看懂资料时点、签收和可信度的只读结果组件

唯一工作目录：C:/Users/郑曾波/Projects/iqs-result-trust-ui-lab
分支：codex/result-trust-30。原生ESM，不引入新框架或第二个API客户端。
只读总控入口：C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-30-mainline-next/README.md。
先读handoff-rules.md、interfaces.md、inputs.lock.json及manifest.json本包条目。

## 用户现在的理解障碍

原UI已接比较、名单、真实扫描/入库；不要重做。现在用户容易把“10月30日生成”“资料来自4月/8月”“cutoff30”“已ACK”“checkpoint恢复”“金融已核实”混在一起。原B进程exit0但requested_scope_completed=false、历史deferred，不能标新研究完成。原start附着文案已由2f1f450修复，也不要重复做。

本包增量是在既有结果/展开记录中可嵌入的清晰只读模块：在不篡改原值、不自己评分或判断fresh的前提下，显示这些差异和缺项。TIME候选未发布；本包按当前真实DTO做，不等另包、不使用未落地verified_at。

## 设计与实现

1. 根据冻结StockWiki profiles/observation与原UI presentationRow/answerTable制作owner-field-map，明确每项来自哪条原字段及缺项/冲突行为。原envelope与child身份关系仍按现规则；不能按用户查询的名字补entity或隐藏foreign child。
2. 按interfaces.md实现renderResultTrustPanel与describeResultTrust。主层少而明确：原分数/状态、资料适用时点、研究截止/生成时间、原freshness或未提供、签收与金融资格分开。展开可看模型、scope/证券、题义/版本、原始引用及缺口；不创建新资格汇总。
3. 日期缺失/精度不足不造今天；当前页面时钟不能覆盖原owner freshness。仅观察到ACK不表示可比、已金融审查或整个公司完成。字段矛盾并列说明，不能选较新日期吞掉旧值或默选最新版本。
4. 显示研究状态与历史恢复：prepared/registered≠有答，process_exited≠已评分/已签收，ready≠ACK，accepted/partial≠delivered，原历史deferred不能变新研究completed。只读组件不发任务/授权/导入请求，也不扩大原allowed_actions。
5. 视觉克制、易扫读，键盘/焦点/读屏标签清晰，窄/宽布局可用。提示用大白话，原诊断码可展开，不把内部字段名当主流程。source URL只安全http/https，内容安全DOM，恶意HTML/URL当文本；不读私有思考。
6. 在本Lab的冻结原UI副本或最小原组件host做demo，沿原request依赖注入/只读回调，不另建fetch鉴权/后台服务/生产owner。新样式限定组件class，不能污染原全局样式；不替换比较/名单vendored交付。
7. integration/host-patch-proposal只列总控合到原UI的确切位置、props映射、向后兼容与回滚；补丁在自己Lab产出，不改当前服务或源仓。无需等TIME的新字段，不伪造已接线。

## 输入与测试

全用明确合成fixture、锁定原组件与可在Lab临时合成Wiki生成的原DTO；不得读真实回答或生产库。本批samples.index只有时间/版本元数据，可用于边界启发，不能改名成owner golden。

单元：null分数/0与bool、unknown/insufficient/not_applicable、缺日期、原fresh/stale/unknown、明确/缺失金融资格、混合版本/证券、多条原观察、身份冲突、不安全URL/XSS、旧数据无新字段。分数/日期/来源必须保持原值，输入对象不被改写。

集成：本Lab冻结原presentationRow/原公开profiles形状→组件DOM，验证父envelope作用域、foreign child隔离/缺ID不补，原coverage对象/空/null不变；复用已有比较parent-scope和start-receipt反例，不重做其业务。

E2E：本Lab loopback 127.0.0.1:18794、本人隔离profile和合成服务，走选择记录→主层/展开→原引用回调→键盘/窄宽布局→缺字段/错误数据状态。必须真实渲染/交互和截图，不把字符串存在当浏览器E2E。端口冲突退出，不碰8766/用户浏览器，不联网下载浏览器；缺环境诚实partial。

先有效RED→GREEN，完成后真实不同agent集中从用户与前端角度全面审查：是否会诱导误把旧资料当最新/签收当金融通过，字段是否忠实、无障碍/交互/清理是否可用；修尽问题复审后交接。

## 交接

docs/handoff/RESULT-TRUST-30/handoff.json；src/组件、field-map、合成场景、测试/截图/cleanup、主机patch提案按共同规则。status=complete只表示独立组件完成，production_ready=false；主线接原UI仍由总控完成。
