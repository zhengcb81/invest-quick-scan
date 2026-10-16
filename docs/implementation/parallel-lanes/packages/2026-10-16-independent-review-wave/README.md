# 三个可同时施工的新包

三个包均可独立开工，不依赖另两个包或本轮真实模型结果。总控继续真实模型/critic/后续搜索实验；这里不派发任务、不创建Lab、不调用API。开工状态以用户后续确认及独占目录实际状态为准。

| 施工卡 | 唯一可写工作目录 | 工作产物 |
|---|---|---|
| [CONTEXT-PACK-06](CONTEXT-PACK-06.md) | `C:/Users/郑曾波/Projects/iqs-context-pack-lab` | 保持原题/证据的上下文裁剪、前缀布局与小包计划候选 |
| [REVIEW-CAL-06](REVIEW-CAL-06.md) | `C:/Users/郑曾波/Projects/iqs-review-calibration-lab` | 金融口径与证据支持的独立评审校准案例、离线比较工具 |
| [RESUME-CHAOS-06](RESUME-CHAOS-06.md) | `C:/Users/郑曾波/Projects/iqs-resume-chaos-lab` | 原SDK/会话/账本的故障、重启与不重发压力测试包 |

新根编卡时均不存在，互不为祖先/后代。上轮活动writer是`iqs-operating-catl-lab`、`iqs-operating-csc-lab`、`iqs-experiment-desk-lab`；本轮不触碰这些根，也不写CODEC/JUDGE/SESSION等已签Lab、StockQA、StockWiki或IQS。六个外包根互不重叠，所有共享输入只读。

**交接前必须实际调用独立审查agent全面检查，修完所有有效发现，再由独立agent复审通过。** 测试通过、自称reviewer、只换同一agent标题均不能代替独审。每包只设这一个整包审查节点，修复后只重跑受影响检查及该整包复审，不为每个helper增加审批。具体要求见[独立审查与修复闭环](independent-review.md)。没有独立agent能力就报告blocked，不能宣称交付完成。

把任一卡片交给harness即可；卡片会引用本目录[共用契约](integration-contract.md)、[接口规范](interface-spec.md)、[交接模板](handoff.template.json)、[输入校验器](verify_preparation.py)和发布回执。总控冻结输入在`C:/Users/郑曾波/Projects/invest-quick-scan/runs/independent-review-wave-2026-10-16/inputs`；精确锁和校验命令见`preparation-result.json`。只使用已冻结子集，不追活动源latest，不读取本轮execution/账本/答案/费用。

三包全部离线、0模型HTTP、0搜索API、0公司文档下载、0生产写入。新工具只是候选，不改正式题库、用户模型顺位或白名单，不给金融/生产资格。总控收到完成交接后再冻结验收与接入，不承诺原样合并。

## 已完成的发布准备

本轮516文件/6352074bytes，锁raw SHA为`968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233`。全量、三个consumer子集、同一字节锁和输入原样搬迁共5项正例通过；篡改、缺文件、锁SHA错误、writer根交叠、路径外跳、Windows大小写冲突、未知协议和未知consumer共8项拒绝反例通过。测试522文件/7438757bytes已清，剩余0；未创建Lab、未派发。

实际[发布回执](preparation-result.json)提供完整argv；例如CONTEXT包开工先执行（另两包替换package-id）：

```powershell
& 'C:/Miniconda/python.exe' -B -X utf8 'C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-16-independent-review-wave/verify_preparation.py' --inputs 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/independent-review-wave-2026-10-16/inputs' --lock 'C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-16-independent-review-wave/inputs.lock.json' --expected-lock-sha256 968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233 --package-id CONTEXT-PACK-06
```

搬迁时原样复制锁及本consumer全部文件并改路径，不修改锁内容。包设计已由另一个agent做[首轮](publication-review/review.md)及[修复后复审](publication-review/re-review.md)，F01/C01关闭；这只是施工卡发布审查，不代替未来实施者交接前必须完成的独立整包审查。
