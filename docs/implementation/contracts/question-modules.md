# S04 模块发布与历史问卷契约

2026-09-26。此契约为本仓离线参考实现；不表示StockQA执行器、StockWiki数据库或UI已接入。题库仍以现有`questions/catalog.json`及模块JSON为唯一可编辑源，归档发布包只供历史解析，不得成为第二份手工维护题库。

## 固定对象

- [评分模块schema](../../../schemas/quick_scan/question-module.schema.json)接受现有48个模块的形状，并预留`common_extensions`和用户显式选用的`lenses`。新增模块必须提供activation证据、引入版本、依赖/冲突和对应`scoring-contexts`口径；没有完整注册不生成问卷。事实模块的具体字段schema由F06在保持现有61题字段ID的前提下扩展。
- [发布锁schema](../../../schemas/quick_scan/module-release.schema.json)规定按ID排序且唯一的模块列表、各模块独立版本、不可变归档引用/原始字节SHA-256、逐题定义SHA-256、累计退役题ID，以及catalog/渲染器/路由器版本。`release_id`是除自身外规范JSON的SHA-256；归档引用只能在`questions/releases/`内，不得指向当前可编辑模块路径。真实文件读取还必须拒绝符号链接或解析后越界；S05才负责真正生成首个生产发布包并让旧manifest按锁定版本读取。S04只验证契约和合成归档案例，事实模块发布格式待F06扩展，当前不得将事实伪装成通用评分模块。
- [路由决策schema](../../../schemas/quick_scan/route-decision.schema.json)绑定`entity_id/as_of/decided_at/release_id/router_version`，要求对发布包内每个模块记录selected/rejected/uncertain、依据、置信度与短来源。`decided_at`必须由可信运行时写入UTC时间；手工覆盖有操作者、理由和UTC到期时间，必须晚于实际决策时刻，不能拿较早的资料截止日延长有效期。`decision_id`同样按规范JSON内容寻址。S06才实现候选分类、门槛和人工覆盖的产品决策；当前`ROUTE_01`仍按原机制使用。

## 不可变升级规则

模块新增题必须升minor或major，已发布题ID与内容保持不变。改变题义、锚点、作用层、构念、评分方向、rubric，乃至文案勘误，都不能在同一ID下覆盖；使用新ID并写`supersedes`，旧题留在归档。模块级`applies_when`定义题目的适用范围，不属于可任意patch的展示元数据：只要适用范围改变，就必须在major版本中退役该模块全部旧题ID，并为每个旧ID提供唯一的新ID后继；范围不变时才可保留旧题ID。移除旧题仅在major版本且每个移除题有明确后继映射时允许，旧归档仍可读取；移除ID同时加入`retired_question_ids`墓碑，后续版本与发布锁持续累计。任何模块都不得重新使用全局已退休ID，即使原模块已退出当前选题目录。其他不改变题义和适用范围的模块元数据修订可升patch，但只要实际渲染prompt改变就须在运行manifest记录新hash。版本号不升、同ID静默改题、同模块或跨模块重复题ID均拒绝；已验证的历史`supersedes`边在后续minor升级时保留，不要求反复指向直接前版已退休的问题。`common`必须恰有IQS_01—IQS_24且一题一核心构念；类型题只能一对一替代既有核心构念；额外通用题进入独立扩展层，不改变旧分母。

一题的运行语义指纹来自它自己的定义、实际适用的上下文和渲染规则版本；当前全量`scoring-contexts`文件变动不应重标无关题，共用渲染规则变更却必须被发现。发布锁中的定义hash保护静态题目文件；运行manifest另需保存实际题面hash、适用上下文和指纹，不能把两个层级混同。S05应把校验绑定到`question_sets.py compose/validate_manifest_metric_contract`真实入口，不能只让合成测试通过。

## 历史归档依赖图与legacy兼容

`validate_registry`和`validate_release`必须分别校验依赖图，不能假定归档release一定由本地registry生成。`validate_release`先逐个核实归档路径、原始字节SHA-256、模块身份/版本、题义锁及退役墓碑，再以这些已核实的归档对象构造闭合图：每个`dependencies`/`conflicts`引用都必须指向同一release里的模块；禁止自依赖、自冲突、同一模块同时依赖并冲突于同一目标，以及依赖环。缺少任一归档或任一检查失败时，不得返回部分模块，也不得回退到当前catalog解释历史。

`conflicts`是选择约束，不是发布目录唯一性约束：同一发布目录可以收录互斥的备选模块；实际问卷组合对传递依赖闭包按无向语义检查冲突，若共同选中冲突的一对模块则在派发前阻断。依赖是必需关系，组合必须确定性补入完整传递依赖；缺依赖、未决依赖或依赖闭包冲突都返回`needs_review/blocked`，不能静默删模块或请求模型临时决定。

允许历史模块缺少可选的`dependencies`/`conflicts`字段，只限其`module_id + artifact_sha256`精确命中受信任基线release/legacy allowlist的原始字节；适配器仅在只读解析时把缺失字段解释为空集合，不修改归档、不对未知对象开放。新模块或新的归档字节必须显式提供必需生命周期与依赖元数据；调用方、LLM或自签release不能把新对象声明为legacy。基线、格式版本未知或可信release链断裂时返回`needs_review/blocked`。S05必须从固定基线逐版验证发布链和累计退役题墓碑，单独的自洽hash不构成信任来源。

旧运行必须按其`release_id`找到相同原始归档字节及哈希；找不到或哈希不符时标“不可验证”，不能改用当前catalog重新解释。当前legacy manifest还没有发布锁，S05须定义明确的兼容标识和原样只读策略，不给旧结果补造新的模块版本或执行信息。该契约中的`legacy_ids`和`historical_retired_ids`参数只能来自逐版验证的可信发布链，不能由LLM、profile或用户自由文本提供。单次`validate_upgrade(old,new)`只能检查相邻版本；S05发布时必须从基线逐版校验墓碑与后继关系，不能跳过中间版本后声称全历史ID未复用。

## 分工与验收边界

`scripts/module_contract.py`只实现schema、升级、注册、归档hash/依赖图和路由决策结构的离线参考校验；不会调用搜索、下载财报、生成公司结果或写外仓。MOD-14覆盖两个静态入口及自洽hash循环归档反例；MOD-16/17覆盖S05实际历史reader、精确基线legacy兼容与新模块缺元数据；MOD-18覆盖S06传递依赖闭包和选中冲突。历史包可读、篡改/缺失拒绝不能替代真实发布器、StockQA派发或StockWiki查询接线。Q13/W15/F06/U04各自按拥有者接线并留真实回执。没有这些后续任务和G6全链验收，不宣称模块化产品上线。
