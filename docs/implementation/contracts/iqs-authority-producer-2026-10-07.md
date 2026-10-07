# IQS authority v2上游正式交付

范围：IQS上下文生成器及共用metadata公式。私有authority `2.0.0`、context `stockqa.quick_scan_observation_context/1.0.0`，公开Exchange `1.0.0`/Observation `1.1.0`/Answer `1.0.0`不变。CLI源码由实际Git commit和工件SHA绑定，没有另造无实现的CLI版本。支持当前已发布评分standard-1；事实链仍待F05。

用户已确认QA-C06-02、SW-REPAIR-02、EVID-LAB-01三个外包开工；总控只写IQS。此交付不给任何worker扩大写路径或关闭联合门。波次2冻结包/13源快照原字节不改，四个IQS原源保持同一SHA，本次只是把已交接上游正式提交，并增加真实进程验收证据。

## 生成命令和输入

在IQS根，准备真实发布manifest、身份owner文件、精确run/versions/producer文件；输出父目录须已存在、目标须不存在：

```powershell
python -B -X utf8 scripts/c06_authority.py --manifest <manifest.json> --identity <owner-identity.json> --run <run-context.json> --versions <contract-versions.json> --producer <producer.json> --output <new-authority.json>
```

run精确五键`run_id/scan_id/inputset_id/task_mode/comparison_group_id`；primary的group=null，comparison的group须非空。versions五键`identity_schema/answer_schema/observation_schema/question_catalog/model_policy_schema`；answer=1.0.0、observation=1.1.0、catalog与发布manifest一致；identity/model-policy仅声明，接收方独立核版本。producer精确`component_version/build_id`，调用方不能用该声明伪装已认证构建。

exit0 stdout给exported/schema_version/context SHA/network_calls=0/identity_attested=false；exit2仅给错误类型，不输出原文/密钥。identity是opaque文件原字节绑定，允许测试synthetic；不是身份owner校验入口。输出不带答案/执行/观察ID，只带每题metadata和原题面/实际strip题面hash；scope缺security/segment ID拒绝。文件SHA与canonical SHA分别保存，不做EOL归一化。

接收方应核题/口径/schema/metric/manifest/identity/prompt实际绑定；不得将URL补title/claim、封包日期补原attempt时点、低分重问或缺字段猜confidence。v1旧包/ACK/费用历史兼容、v2完整body耐久与replacement/head/ACK接线由QA包完成，不在本批宣称已可运行。

## 可复现验证与证据

在新独占根（命令本身拒绝已存在根）运行真实CLI 11场景：

```powershell
python -B -X utf8 docs/implementation/reviews/G3/iqs_c06_cli_e2e.py --work-root 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/c06-context-producer-<unique>'
```

环境中的key/live只移除可用性不打印值；独立CLI子进程禁止受监控网络/process/registry/根外写，父fixture harness不受同一audit，不夸称全读隔离。实际31题metadata与波次2fixture逐题相等，原文件hash/正例字节稳定；重放、拒覆盖、primary/comparison、duplicate JSON、篡改发布、错版本、缺run、既有目录、缺父目录均通过。没有公司观察/生产DB/真实owner身份或收费API。

35项相关回归和24子测试通过，集中[独立审查](../reviews/G3/iqs-c06-producer-review-2026-10-07.md)无范围内阻断。原日志/正例/输入/hash见[交付索引](../intake/G3/2026-10-07-iqs-producer/artifacts.json)。两个本轮根28文件按manifest、无link、严格argv扫描+已知子进程终态清除；[清理receipt](../intake/G3/2026-10-07-iqs-producer/cleanup-receipt.json)保留逐文件证明。旧Phase92 run、共享TEMP、外仓不动。

新测试自行结束后仍需按其实际manifest清理，不能复用本批两个已清根的cleanup脚本/清单去删除另一次运行。源码/证据回退只禁用该新导出入口，不重写发布题义/旧观察/hash。原mapping文档与原失败日志作为历史保留，当前状态以本交付和根PWF为准；G3/F05和整Q10仍开放。
