# QA-C06-02 第二轮剩余整改：只补同链边界

总控结论：`partial_verified/changes_requested`。247受影响、原9反例及真实CLI四例已通过，保留现有交付。以下六个失败case收敛为原四组的四个边界，不新增验收门。原StockQA harness继续唯一写入者；本卡不派发任务、不扩大任何外仓授权。

固定基线：StockQA代码 `acb7dbfae0e6a45221924e2d1d5742a4999f4c9d`；收到交接 `361a721df382c468640b27bbafc484e31c8aa321`。开工核最新HEAD/工作树，若并行变化则列实际差异并先协商，不能reset/stash/清理原七未跟踪。路径/授权沿原[施工卡](../../../parallel-lanes/packages/2026-10-07-wave2/QA-C06-02.md)和[四组卡](../remediation-2026-10-08.md)。这次建议只改相同context/outbox/work_store及其测试/交接，不重造另一套规则。

## 同批修复内容

1. **QR1B，P1：具体scope ID要在入口绑定。** `check_context_matches_manifest`共享规则同时核metadata的security_id/segment_id与manifest.profile和预期scope。原fixture IQS_22的security_id改SEC_FOREIGN、仅重签context，loader当前接受；真实CLI当前exit1却已HTTP-stub发送31、打开fixture key文件2次、产生工作/预算库和结果。应在任何key、HTTP、预算、checkpoint前拒绝；正常entity/security/segment保持通过。不要只用退出码判成功拒绝，也不要改冻结fixture标签凑绿。
2. **QR2B，P1：所有新完整write共享run/scan门。** no-context checkpoint attach FOREIGN_RUN/FOREIGN_SCAN后，公开seal已blocked/c06_run_scan_unbound；调用公开prepare仍改为ready、保存foreign观察，而实际refs仅RUN_COMPLETE/SCAN_COMPLETE。prepare与supersede须核同一持久映射，失败不增加revision、不替换blocked/head、不自动重问。合法晚attach与已有映射继续可用。
3. **QR3B，P2：strict JSON入口拒数值溢出。** `parse_standard_answer`当前接受metrics.value=1e400，形成inf。后续canonical拒绝，因此此例未证明错误head；修复共用strict decoder的有限float处理或等效递归检查，嵌套/数组同样拒绝。正常有限数和普通文字仍按旧约定处理。禁止把坏正文退回可计分compact或默认5分。
4. **QR4B，P1：缺持久完整输入的新完整write必须拒绝。** no-side-table checkpoint，从外部context/body构建full包，改claim和original started_at、全层重签。prepare和compact→full supersede当前均落ready，context/answer表仍0。完整write必须具备可验证的不可变context/body/原成功attempt和run映射，不能因缺数据跳过校验。历史已sealed读取、compact v1写入、合法补齐后升级、delivered只读保持兼容；不靠强行插默认side tables或改旧记录补证。

## 输入、测试与交接

- 可直接复制执行的固定反例：[remaining_cases.py](remaining_cases.py)。它只在拥有者独占root用合成fixture；`QA100_QA_ROOT`固定源码、`E97_OWNED_ROOT`唯一拥有根。原[9反例](../acceptance_cases.py)字节保留，不更改断言。
- 预期同批：原9 GREEN；本批7项（1正常＋6反例）全GREEN；本轮247受影响GREEN，包括真实CLI cold/warm/seal、错template/重复JSON早拒、坏body不重问；既有ACK、migration、合法compact升级仍GREEN。有实际改动才定向重验相关组；完成后一次集中审查。已收到1083全套日志，不无故重跑全套/UI/live。
- Windows asyncio需要内部回环socketpair；总控最初沙箱timeout是环境限制。去密钥、禁止外网/外根写入的guard下，沙箱外同Mock case及247已GREEN。不要放行模型HTTP来解决测试环境问题，不输出key内容。
- 五个冻结CRLF文件按原锁工作树SHA复现；Git blob LF与工作树CRLF双口径列明，不重签IQS输入。真实StockWiki owner正例仍由owner提供，不生成假gold。
- 正式交接包含新code/result HEAD、实际变更allowlist、RED→GREEN原输出、输入SHA、一次审查、隔离/清理实际情况。只声明自己证明的范围，旧共享TEMP不能按编号/mtime删或把cleaned=false改true。收到worker清理回执仅有清单聚合hash，不能补写缺失的历史逐文件验证；如原清单尚在可归档，否则明确not_reconstructable即可，不阻止正常代码修复。

真实QA→StockWiki import/ACK/UI、双owner恢复、owner golden、G3/F05/TH/IN/L03仍未签收。本卡完成后总控仅验受影响，再决定已有联合12组执行；不增加中央case或退役任务回执。
