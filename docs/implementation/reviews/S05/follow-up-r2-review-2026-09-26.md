# S05 r2 独立复核

审查者：`/root/question_audit`。结论：**原五项P1已关闭，新发现两项P1、一项P2；S05仍为needs_revision**。独立运行`test_module_registry.py`和`test_standard_answers.py`共38项，0跳过，并经真实公共入口重放原五项反例：跨公司方法一致、篡改manifest在观察前拒绝、旧归档schema可读、3→4→5连续退役可发布、模型不能擅选manual lens。

新发现：

1. **P1，协议变化未入语义指纹**。修改已发布答案schema的`score.description`以改变评分含义，再发布并生成standard-1观察，包和prompt变化而逐题`semantic_sha256`及观察`method_id`不变，跨期比较仍称可比。需把实际嵌入prompt的资源语义计入指纹。
2. **P1，观察语义自报可伪造**。把合法发布观察的`question_semantic_sha256`改成64个`f`、同步method后缀及观察hash，`validate_observation()`仍接受。另把四个发布绑定字段全部删除并重算ID会被识别成legacy；自包含记录在没有外部预期ID/格式时无法证明自己原来是哪一条。应从可信发布包和上下文重算语义，并为新入库设严格发布模式/外部不可变ID，legacy只做明确的只读兼容，不虚称单条记录能抗全面重写。
3. **P2，旧包可发出无法接收的问卷**。真实旧包`pkg_92fc...`仍能经`compose(..., "standard-1", package_id=old)`输出31题，manifest也通过；直到`build_observations()`才发现缺冻结观察schema。须在导出前拒绝新运行，但保留旧包历史读取。

本轮使用唯一TEMP根和`python -B`，禁网络/子进程及TEMP外写入；128个源文件哈希审查前后相同，真实旧包字节未变。关键快照：`module_registry.py` `7B38B7EBA50A723E219CA1449C683C369A565010CFA8E5AE2536AB36E8EE4A3A`，`question_sets.py` `E6FD56AD56C968998CF5A94A88EC2F12EFFD46A58BDFBE72B272988946EFF5EE`，`standard_answers.py` `1796EF5AE8777CC5E92617F44FDC8E64725BEC546C3A4C08B13809FFE8B63576`，`schemas/observation.schema.json` `85A70C39616EF819EE7414EF03D5448A8860A22888519845432AD92F79B270B3`。新修改后须重跑固定反例与独立复审，本报告不能作新版本通过证明。
