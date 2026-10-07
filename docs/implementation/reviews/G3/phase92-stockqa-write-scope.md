# Phase92 StockQA 写前报备

用户已授权总控修改StockQA全仓并要求逐批报备；当前唯一writer是总控。只改以下路径，按当前工作树最小hunk；不写StockWiki/Theme/Industry/company-wiki，不读取或修改生产配置/名单/数据库或原七项untracked。

首段TDD先新增下列6件源码/测试/合成输入及schema快照：

1. `StockQAbyLLM/src/utils/quick_scan_observation_context.py`
2. `StockQAbyLLM/src/config/quick_scan_observation.schema.json`（IQS已发布schema原字节副本）
3. `StockQAbyLLM/src/config/quick_scan_answer_content.schema.json`（同上）
4. `StockQAbyLLM/tests/unit/test_quick_scan_observation_context.py`
5. `StockQAbyLLM/tests/fixtures/quick_scan_c06_authority_v2_fixture.json`（真实IQS编译器生成的**合成身份**输入，不是真实StockWiki golden）
6. `StockQAbyLLM/tests/fixtures/quick_scan_c06_manifest_v2_fixture.json`（同一评分发布的完整冻结问卷；实际测试只消费其中一题，不冒充全问卷已答）

后续同一整改批次将接线并逐次报备下列既有/新路径：authority loader/v2 schema、work store/outbox/seal/manifest/runner/base provider、pyproject的jsonschema声明、`.gitignore`的精确JSON例外，相关已有unit/CLI/transport测试与本包docs。具体清单和行为见`c06-authority-v2-input-map-2026-10-07.md`；该预计列表不允许盲改尚未核对的测试文件。

首段只是RED脚手架及纯上下文/完整标准答案验证模块，暂不接生产派发，因此不能声明v2已可运行，也不关闭G3/F05或整体Q10。测试在IQS唯一自有root重建公开StockQA源码后执行，环境key/live清除、网络/根外写禁止；不在源仓跑会落库的测试。

首轮34 RED后增补并报备第7个快照路径：`StockQAbyLLM/src/config/quick_scan_metric_registry.json`。标准答案必须校验固定指标单位，不能仅验证JSON shape而接受单位混用；该文件也是IQS已发布资源原样副本。v2 context在尚未发布阶段补`metric_registry_sha256`，冻结此资源，重新生成同一合成fixture；不改任何生产authority文件。

消费模块采用现成jsonschema校验库，接着精确修改第8/9路径：`StockQAbyLLM/pyproject.toml`仅增加运行依赖`jsonschema[format-nongpl]>=4.23.0`，`StockQAbyLLM/.gitignore`仅为本批3个公开协议快照和2个合成fixture加精确例外。原authority1.0 schema与其他JSON忽略均保留。不运行安装或升级命令，不改全局环境。
