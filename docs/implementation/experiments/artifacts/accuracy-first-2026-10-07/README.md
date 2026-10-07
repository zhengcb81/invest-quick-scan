# Phase96最小归档

主实验、补实验、ZAI诊断、隔离离线验证分别在main/followup/diagnostic/validation。index.json绑定原字节size/SHA，四个archive-manifest.json还保存清理前文件清单。StockQA transport固定commit记录在runtime-manifest.json，不复制外仓源码长期驻留。

保留最终结构答案/短说明、题义、官方事实参照、UTC与模型参数回执、源URL/标题/内容hash、逐项coverage及独审、全部费用预约/异常。未保留搜索片段、网页/财报、原始供应商响应、独立思考、无效答案正文、答案缓存或临时runtime。source-catalog是元数据，coverage是总控审查结论，不能冒充原片段全文；无法从本最小包重建实际prompt或重新解析invalid正文。

公开离线复算（IQS仓根，Windows Python，无API调用）：

```powershell
python -B -X utf8 scripts/accuracy_report.py --main docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/main --followup docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/followup --diagnostic docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/diagnostic --output docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/followup/terminal-report.json --check
```

预期accuracy-report/2: matched；108模型HTTP/56搜索相关HTTP/USD3.871962保守上界/1历史处理未知。unknown-disposition.json保留USD0.03全预约及禁止盲重发，删临时文件不释放该预约。初始浮点评估及首轮数值报告保留，最终十进制/来源补标/说明审查显式分开。

validation/result.json与stdout/stderr.log记录51项相关离线测试，最终summary是Ran 51/OK；source freeze在归档前再次复核。cleanup receipt在reviews/B01/accuracy-first-cleanup-receipt-2026-10-07.json，以applied实际值为准。此包不代表生产验收、评分gold、公司池变更或G3/F05关闭。
