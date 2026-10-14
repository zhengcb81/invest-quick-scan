# 跨包接口：无彼此前置，独立可验证，总控统一消费

每包[manifest.json](manifest.json)列自己的输入仓集合和独占新根；三个包没有彼此新交付依赖。BLIND直接消费冻结FIN，若旧副本缺输入则保留boundary错误，不等待FIN-PROVENANCE。FIN-PROVENANCE不采用BLIND新增协议；CHAIN不读取另外两包的产物。禁止后台修改其他卡、共享PWF、真实库或正式release。总控保留真实B01恢复/模型请求/费用/正式发布/生产UI与最终接线单writer职责，本轮不同时自己改这三个候选。

## 输入锁与可搬迁

inputs.lock=iqs.multi_repo_package_input_lock/1.0.0；files条目严格repository/path/bytes/sha256，path为POSIX相对、无绝对/..，rawSHA不是canonical。snapshot_root仅当前机器运输位置；迁移宿主显式传--input-root，仍使用同锁同bytes，不重签原锁。input_refs只能引用自己的依赖仓锁条目；nested fixtures原路径与锁保留。inputs-used须列所有实际依赖与各仓完整commit，并声明原件/副本不同根。

## 新候选公共封套（1.0.0）

各content主文件strict required={protocol,package_id,artifact_id,created_at_utc,information_cutoff,input_refs,records,limitations,qualification_granted}，additionalProperties=false。cutoff=2026-10-13；访问时间可2026-10-14或之后，但截止后的来源不能支撑该截止的事实。qualification_granted=false，记录owner_mapping_status=not_mapped、production_execution=not_run，fixture_class=synthetic|public_source_reference。前三为包ID自有前缀BI04/FP03/CV04 record_id及各卡精确payload，schema不允许未声明字段。

artifact_id=candidate_<包ID小写>_<64hex>；域去artifact_id/created_at_utc后JSON UTF8/ensure_ascii=False/sort_keys=True/compact/allow_nan=False，数组原序。这是候选内容ID，不是生产semantic hash。引用原题全对象canonical与路径/module_id/question_id闭合，不能只比题目名字。声明的query/metric/claim与issuer/period/cutoff边界全部保留；文件hash闭合与金融证据资格分开。

每条records对象恰好五字段：record_id、fixture_class、owner_mapping_status、production_execution、payload。payload恰好该卡“输出与验收”列出的字段；不得再次出现旧包漏封套或超字段问题。实现时交独立strict JSON schema、最小合成样例与拒第六字段/缺marker/未来版测试。最小样例只能标synthetic，不冒真实来源正例。

字段类型基线：ID、protocol、UTC、cutoff、状态均string；qualification_granted为false；input_refs、records、limitations为array（limitations为string列表）。payload中所有*_refs和losses/mapping_rules为array；source_refs/dependency_refs引用冻结四字段file ref，test_refs/diagnostic_refs为本包三字段{path,bytes,sha256}文件ref。参考资格状态、dependency closure与金融状态分开。retained_denominator为闭合对象{input_slots,output_slots,error_slots,replay_slots}非负整数；reference_boundary为闭合对象{validator_status,eligible_fact_count,ineligible_fact_count,errors}，status=passed|failed|not_run，errors保留code/detail而非只布尔。question_ref闭合{path,module_id,question_id,question_object_sha256}，若原金融输入无法定位module不得猜填，module_id=null并保留meaning gap。CHAIN的claim/gap/attempt refs引用自己侧车ID，new_source_refs为新source ID，每个ID须在同批实际验证导出的侧车存在。实现者必须在自己的schema进一步封闭nested rule/source/disposition对象，类型不明时提出明确兼容边界，不自行放宽为任意字典。

来源/文件ref严格{repository,path,bytes,sha256}；新增公开事实source sidecar引用是本包导出相对路径，其schema单独声明url/定位/issuer/事件日期/公开日期/访问UTC/范围/短摘录/support_status，不冒充锁内旧来源。secret、思考正文、整页正文不入公开manifest。

## 薄CLI一致行为

```powershell
python -B -X utf8 -m <本包module> validate --input <content主文件> --inputs-lock <本批锁> --input-root <自己的fixtures>
python -B -X utf8 -m <本包module> export --input <同主文件> --inputs-lock <本批锁> --input-root <自己的fixtures> --output <全新目录>
```

BLIND=iqs_blind_input_lab，FIN=iqs_fin_provenance_lab，CHAIN=iqs_chain_verify_lab。依赖/sidecar原件参数显式传入，核A不能导B；输入锁/数量/路径/引用先验、内容后验，原子导出同一批验证bytes。exit0 candidate有效；2非法/未知版本/超过预算且零正式输出；3输出已存在/路径越界。报告validation_scope=candidate_artifact_only，不暴露私有traceback。确定性物料id与body稳定，时间/宿主路径放独立回执；记录确定性比较域，不靠删除有用字段制造相等。

## 各包向总控的交付

BLIND：content/blind-input-bridge.json、显式格式支持表、可在临时副本运行的真实输入适配器、旧格式回归、错误槽位完整ledger、原盲评build/join公开正反例、schema/compat与base/new SHA补丁提案。不输出实际真人review，不生成费用/任务结果。

FIN：content/reference-bundle.json、90原题/来源/账本一一闭合索引、历史9错误与当前根对照、便携完整冻结bundle、公开FIN validate/export实际收据、缺失资料ledger。可以结构上完整而金融仍partial；不能用新manifest重签原handoff，不能用外包结果补旧工件SHA。

CHAIN：content/verification-delta.json、36槽位/59 claims/52 gaps逐项处置、人工primary核源尝试、结构来源侧车及短摘要、具名关系核验/差异提案。新fact只供总控核证，不直接重写原CHAIN或正式词表/题库。

三个包独立交回后总控各做一次包级审查并处理源漂移。未评审、不支持或输入缺口保留null/unknown；任何包都不能自授gold、owner批准或关闭G3/F05。
