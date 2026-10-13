# 三包独立接口与总控接线

## 冻结依赖

inputs.lock protocol=iqs.multi_repo_package_input_lock/1.0.0。条目严格{repository,path,bytes,sha256}，定位snapshot_root/<repository>/<path>；path规范POSIX相对、无绝对路径/..，sha为raw字节。repositories记录完整commit/branch/初始dirty，仅上下文不是授权。inputs-used必须覆盖本包所有依赖条目，不替换为canonical hash。iqs.inputs.lock是给原IQS工具的单仓视图，冻结Lab自身旧fixtures/锁原字节保留。

## 候选输出共同封套

各包主文件为content/<卡指定>.json，严格schema、additionalProperties=false，required={protocol,package_id,artifact_id,created_at_utc,information_cutoff,input_refs,records,limitations,qualification_granted}。qualification_granted恒false，cutoff=2026-10-13。input_refs非空严格{repository,path,bytes,sha256}闭合于本批锁。候选ID=candidate_<包名小写>_<64hex>；canonical域去artifact_id/created_at_utc后JSON UTF8/ensure_ascii=False/sort_keys=True/compact/allow_nan=False，数组顺序保留。这是研究内容ID不是生产semantic hash。

原question_ref严格{path,module_id,question_id,question_object_sha256}，按原题全对象canonical；引用哪个repository、冻结HEAD由input_refs确认，不改原题。各包record ID自有RE03/CS03/BR03前缀，不引用其他新包。后续增加字段/语义另升显式版本并保留旧读取/拒未来版本测试；不往同版封闭schema随意塞字段。

每个records严格含record_id、fixture_class、owner_mapping_status、production_execution以及各卡的payload字段。fixture_class=synthetic|public_source_reference；owner_mapping_status=not_mapped、production_execution=not_run。ROUTE可以native_test_execution=passed|failed|not_run，不能将此字段混成生产执行或资格。

## 薄CLI

每包python -B -X utf8 -m <卡指定module> validate --input <主文件> --inputs-lock <多仓锁>；export同参数另--output <全新目录>。其它依赖显式参数并按实际选择值校验/导出，不校A却导B。exit0候选有效、2非法/未知版本零正式输出、3输出已存在/路径逃逸；validation_scope=candidate_artifact_only。路径根/体积/引用先检查，再做语义验证，再原子输出；不暴露私人traceback。

ROUTE另执行run-cases，使用原routing-v2-request/resolve-route/compose-route而非自己的判定器；失败仍保存真实诊断到本包runs，本包report不得据此改expected。CHAIN没有自动抓取器，validate/export只读已人工核实的结构化增量。BLIND另build-packet/join-reviews，只处理显式输入副本，不调用模型、StockWiki或费用账本。

## 独立消费与最终审查

ROUTE补C01的原v2全案例接线/正式release后验收依据；CHAIN补F03–F06及B01真实产业链核证；BLIND补B01/L02准确性评审工具。三个包现在均可在自己的新根启动，不依赖彼此结果。CHAIN的新事实不会自动进入BLIND，BLIND的模板也不改ROUTE预期。总控收到后按冻结对象/rawSHA CAS并处理实际源漂移，统一发布/接入，不最后写入者覆盖。

真实收费模型矩阵、Brave/Tavily/ZAI请求、原26/4 owner恢复、实际identity/receipt/ACK、正式词表与标尺发布、生产UI和一键仍只由总控实施。源改变允许工人基于冻结版本完成，漂移在接线时处理；未核源/未评审/同名不同主体保留null/冲突，不自动变成正式分数或白名单。
