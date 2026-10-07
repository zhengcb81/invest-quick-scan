# Q10 完整观察输入映射与实施边界

状态：IQS producer 侧输入导出已实现、正在定向验证；StockQA v2 consumer、V6耐久存储和封包替代链尚未实现。本文不是 G3/F05 签收或新外仓授权。基线 QA `09f68a69`、SW `04dfc519`，两个源仓只读勘察期间未变。

## 输入来源

| 内容 | 唯一来源及绑定 | 不得补造的内容 |
|---|---|---|
| field/construct/question/template/method/cohort/cutoff | IQS已发布standard-1 manifest，先由`validate_manifest_metric_contract`核验归档题定义、语义、prompt和确定性选题；共用`standard_answers.observation_metadata`，原`build_observations`也调用它 | 不按qid造field，不另算题义/method，不把机器日期当cutoff |
| module package/release、definition/semantic、cycle_sensitive | 同一真实发布包与profile；只支持能发新观察的评分发布，事实模块留F05 | 旧release没有标准观察能力时不能换头升级 |
| run/scan/inputset/task_mode/comparison_group | 调用方明确的五字段执行上下文文件；primary必须group=null，comparison必须group非空 | 不用CLI自动生成的后来run覆盖原批次，缺字段不猜 |
| identity | owner导出文件原字节SHA256；StockQA沿用公开identity loader核验实体及绑定 | IQS只绑定opaque字节，不给synthetic/provisional签verified |
| scope | 发布question + profile提供的真实security/segment ID；未绑定拒绝导出 | 公司名、ticker或scope类别不能代替scope_id |
| 标准答案 | 原LLM完整标准JSON；原外层entity/company/question/score/status绑定保留，description显式携带完整标准body | URL不能自动变title/claim，缺confidence/basis不能填默认值 |
| provider/model/request/attempt/search/prompt/开始完成时间 | 耐久成功HTTP attempt/checkpoint；开始取该attempt.send_intent_at，完成取原response_completed_at | requested model不能冒充actual，封包时刻不能替换执行时刻 |
| observation ID | 完整不可变观察内容的既有IQS canonical digest，含原run/执行/范围/模型/信息日期 | 不能只用entity/qid/scope，也不能靠随机ID规避冲突 |

两份标准schema来自IQS已发布包，其canonical SHA与当前文件一致，实际已核对：Observation `ab547ecdd81ee1b302aaef30941fb20ac1563b9122267f8858bcb91f8f2d34e0`，Answer `cefa301b35235c15f188bfede2706837ea695e10b656a28684eecd0159434fcd`。复制给consumer是发布协议快照，不复制LLM、搜索或题库计算实现；未知schema hash失败关闭。

## v2 authority私有输入

公共C06包仍是既有1.0.0，Observation是已有1.1.0。本批只新增StockQA私有authority **2.0.0**，不改IQS公共schema、旧authority1.0或现有问卷发布锁。IQS已提供`python -B -X utf8 scripts/c06_authority.py --help`。

顶层精确字段：`schema_version`、`contract_versions`、`capabilities`、`producer`、`observation_context`、`observation_context_sha256`。context精确字段：`schema`=`stockqa.quick_scan_observation_context/1.0.0`、`manifest_content_sha256`（canonical）、`manifest_file_sha256`（原文件）、`identity_snapshot_sha256`（原文件）、`observation_schema_sha256`、`answer_schema_sha256`、`metric_registry_sha256`（均canonical）、`questions`。

每题只有`metadata`、`frozen_prompt_sha256`（exact prompt）、`work_prompt_sha256`（strip后实际待办题面）。metadata是既有Observation去掉`observation_id/observed_at/execution/answer`四项；没有虚构执行或答案。导出器先校验真实发布，再用同一归档Observation schema检查metadata；两种manifest hash不混用。StockQA接收后仍须独立比较实际输入manifest/identity字节和逐题原口径；输入hash不是身份或事实审计认证。

CLI需要调用方提供已冻结文件，不隐式读取任何生产config/DB或环境key：

```powershell
python -B -X utf8 scripts/c06_authority.py --manifest <standard-1_manifest.json> --identity <StockWiki_export.json> --run <run-context.json> --versions <contract-versions.json> --producer <producer.json> --output <new-authority.json>
```

run-context精确五字段即上表，versions为既有五个contract_versions键，producer仅component_version/build_id。answer_schema=1.0.0、observation_schema=1.1.0、question_catalog与manifest.template_version一致。输出父目录由调用方准备，目标必须不存在；先写完整临时文件并fsync、再原子exclusive link发布，失败清临时项且不删/覆盖原目标。Windows受限沙箱hardlink可能被拒，本批用相同离线guard沙箱外验证，不改发布保证。**当前StockQA只认识authority1.0，不能将本导出直接当成可开工生产配置。**

## StockQA单一后续实施批次

写前按既有全仓授权报备确切清单；尚未写外仓。预计最小路径：

- `src/utils/quick_scan_c06_authority.py`，新增`src/config/quick_scan_c06_authority.v2.schema.json`；保留原1.0 schema/loader只读能力，v2 loader严格验证。
- 新增`src/utils/quick_scan_observation_context.py`、`src/config/quick_scan_observation.schema.json`、`src/config/quick_scan_answer_content.schema.json`；标准schema原样协议快照，`pyproject.toml`声明jsonschema格式校验依赖，`.gitignore`仅精确例外。
- `src/utils/quick_scan_work_store.py`，V6加不可变context/标准答案侧表及新封包revision/head/事件表；原checkpoint、旧sealed包、旧ACK/费用账本不改payload/hash。明确迁移事务、旧库备份/读兼容与幂等。
- `src/utils/quick_scan_c06_adapter.py`、`src/utils/quick_scan_result_outbox.py`、`src/utils/quick_scan_delivery_seal.py`、`src/utils/quick_scan_question_manifest.py`、`src/runners/llm_runner.py`、必要`src/providers/base_llm_provider.py`：原输入冻结、显式标准JSON外层传输、完整schema+语义验证、补包与ACK接线；不再写一个网络client。
- 对应`tests/unit/test_quick_scan_c06_authority.py`、新`tests/unit/test_quick_scan_observation_context.py`、现有work_store/outbox/seal/manifest测试、公开CLI/transport集成与`docs/handoff/QA-NET-01/`。具体既有测试文件名在写前按当前tree最终报备，不盲改缺失文件。

先在原问题反例上TDD，再做整批集中门/独审；不拆helper审查门。新完整标准答案可以缩为compact checkpoint的summary，同时将完整body原样验证后耐久保存；不能受旧description=5000上限诱导截断/丢字段。旧description里确有完整标准JSON才允许按原prompt/来源绑定恢复侧表；旧极简答案缺字段保持blocked，不自动问LLM补齐。当前v1被seal的残缺包必须历史只读，不重新标为完整标准ready。

旧封包后补只允许有充分原冻结输入/标准答案的情况：保存新revision及supersedes关系、head明确指向当前包；旧ACK按旧包留档，不能落定新head。旧send_uncertain先对账，不偷偷换包；原已delivered不自动重新交付。拒绝旧包不删原答案或解锁重问。最终使用StockQA→StockWiki真实公开CLI验证新包被接受、丢ACK重放单观察同ACK、StockQA公开ACK落定。合成离线正例仍不是实际owner真实数据/G3。
