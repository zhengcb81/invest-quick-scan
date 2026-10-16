# 三包的互不重叠接口

共同规则：来源输入只读，纯函数不联网/读env/写文件；CLI才管理路径和输出。所有输出带protocol、package_version、source_context、limitations、稳定content_sha256。source_context至少含输入锁raw SHA、原问题/原证据/完整指标registry canonical hash及实际工具版本；hash声明不能靠输出自证，CLI从已核锁派生。所有资格字段保持false。

## CONTEXT-PACK-06

`iqs.prompt-context-plan/1.0.0`：mode、selected_question_ids（保序唯一）、full_question_sha256、selected_question_sha256、evidence_board_sha256、metric_registry_sha256、validation_context_ref（完整题集/证据）、prefix_text、prefix_raw_utf8_sha256/bytes、tool_schema_sha256、preservation_checks、projection_manifest、limitations。不得将裁剪后的题表hash冒充完整验证上下文。

必须实现`baseline_full`与`selected_questions`：前者调用冻结原prefix_text完整题表，字节相同；后者仍调用它但只传明确选中题的原对象，完整board/registry/identity不变。两者各自明确hash；下一版owner必须主动选用新protocol，不可替换活动T4。

`evidence_first`为可选研究变体：只能在精确冻结来源上无损拆分/重排已知组件，证明原布局roundtrip同字节、组件hash及不可信数据边界。遇未知来源格式拒绝，不靠宽泛字符串猜切或改规则/事实来凑缓存。做不到时unsupported+原因，不影响两个必做mode；不能宣称已省钱。第一版**禁止裁剪证据或指标registry**，也不按词频推断无关事实。

`iqs.prompt-pack-schedule/1.0.0`：完整原12题/指定全集、mode、ordered packs及各自context-plan引用、完整/遗漏/重复ID检查、公司累计limits引用、CACHE的prefix分析原输出引用。固定用户顺序/pack_size（1–3）排小包；不推断金融优先级，不给每包重置公司总额。字节公共前缀/理论场景不等于实际token/cache-hit；未计量token和真实价格保持null。

## REVIEW-CAL-06

`iqs.review-calibration-set/1.0.0`：synthetic=true、cases唯一ID、family、原question/完整候选answer或显式缺答、有限public_evidence、expected_judgment、reason、assumptions、origin（counterfactual/transformation/source ref）、难度与成对case ID。expected仅校准synthetic案例，绝不冒充真实金融gold。允许原标准validator故意拒绝的format-negative case，但须单独phase，不能与“格式合法但金融错误”混算。

评审labels沿冻结JUDGE现有semantic_coverage、factual_propositions、scoring_assessment字段，数值atom维度完整，无主观唯一分数。`iqs.review-calibration-report/1.0.0`：原计划/收到/重复/未知/缺失cases、按family confusion/争议列表、机器可核字段一致性、未覆盖语义边界；缺失不算正确，不用单一准确率抹掉严重错误。`score_calibration`只是比较已给标签和独立审查的synthetic expected，不对真实投资答案用关键词自动判真假。

REVIEW的匿名接口固定为：`make_assignment`返回`public_assignment`与`private_map`；公开仅匿名ID及完整实质内容/synthetic标记，不含原ID/family/pair/expected/变换提示。私有map记录casebook/公开assignment的canonical SHA、匿名ID到原ID的一一映射及逐题/答/证据指纹。`score_calibration(..., assignment=..., private_map=..., expected_context=...)`核实际输入及重新计算的内容绑定，不能信自报hash；错map、内容替换仍自报原hash、匿名提示泄漏必须测试。CLI assign写public/assignment.json及private/map.json，compare显式接收两者，评审者不见private。

## RESUME-CHAOS-06

`iqs.resume-chaos-casebook/1.0.0`：synthetic=true、case_id/fault_boundary、输入版本、前置状态、注入点、原公开entrypoint、预期真实HTTP/SDK/commit/预算变化、不应出现副作用、清理资源。无第二状态机或费用实现；expected不是伪造的observed。

`iqs.resume-chaos-report/1.0.0`：计划场景、逐case实际argv/exit/注入证据、原mock HTTP计数/原SDK step计数/合法答案数、原临时store前后投影/row hash、预约及未知状态、恢复实际动作、输入保持、cleanup和unresolved findings。输出不能把人工预期复制成观察结果；不假造发送失败=0费用。源schema20只在本地临时库跑，不升级真实库。检测到上游不符合原合同则block正式完成并交最小反例给总控。
