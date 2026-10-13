# ROUTE-E2E-03：47例接真实v2路由入口与兼容回归

独占C:/Users/郑曾波/Projects/iqs-route-e2e-lab，分支codex/route-e2e-03。先读[共同规则](common-rules.md)、[接口](integration-contract.md)、[manifest](manifest.json)、[锁](inputs.lock.json)、[47例目标](ROUTE-E2E-03.targets.json)、[handoff模板](ROUTE-E2E-03.handoff.template.json)。不等另两包，可开工；不改任何现有仓。

## 现状和目标

ROUTE-COVER-02已修并提交6829cc6：47例只有legacy原CLI全跑（41成功/6拒），native v2只5边界/7subtests。现要把47个固定case都认真转换为原v2证据/请求、实际resolve和compose，识别真实不适配；不重新研究48模块，不重做旧validator，不自造router。

## 按顺序实施

1. 验全部iqs/route冻结字节复制到fixtures。读原tests/test_routing.py RoutingFixture及已修route/tests/test_native_v2_boundaries.py、case-compose audit；只复用原fixture的自有TEMP synthetic identity/release，不激活生产current。记录原公开CLI实际help/版本和所有入口依赖。
2. 将47条的input_profile及明确facts转换成原v2输入，逐条mapping-notes写可用证据、缺失、转换规则和as_of。不能把expected字段喂入分类、编事实使expected成立、用legacy预分类假装v2。
3. 对每case在原公开CLI实际依次routing-v2-request→resolve-route→compose-route，保存命令、PID、退出码、请求/resolve/manifest rawSHA、模块及保留题列表。原物理指针只在TEMP。无法合法建请求也必须保留record、真实失败层和原因；不得删例/skip为passed。
4. 独立比较实际与冻结expected，归类matched/diverged/input_gap/unsupported/product_error。expected确有问题只交proposal，以case_object_sha/原题SHA CAS，不修改冻结目标或用实际输出回填expected。
5. 增补同主体两期/三期序列，重点15%入、10%留/9%两期退、生命周期两期确认、mature+trough诊断、恢复资金/永久损伤差别、unknown只common、金融replacement与经营属性不机械套收入阈值。至少每一类一个真实原v2入口正反序列；原47例与新增序列分母分开。
6. 回归原question ID/内容、module manifest与旧legacy行为，不改生产算法。报告实际产品缺陷及最小复现，写建议patch到本包proposals而非外仓。资料包可partial，软件run-cases必须诚实记录失败。

## 交付接口

主content/v2-case-results.json，protocol=iqs.route_v2_case_result_candidate/1.0.0，47records原case順序不变，payload严格{case_id,baseline_case_sha256,conversion_ref,execution,comparison,limitations}。

- execution严格{native_test_execution,entry_point_runs,request_ref,resolution_ref,manifest_ref,actual_modules,actual_question_refs,terminal_reason}。entry_point_runs每项{command,exit_code,log_ref}；ref={path,bytes,sha256}指本包归档，不指可变TEMP。没跑的ref=null，不造成功输出。
- comparison严格{status,expected_modules,missing_modules,unexpected_modules,retained_questions_missing,proposal_refs}；status取前述5项。不把typed low confidence当低质量分，不把合成身份当真实映射。
- content/sequence-results.json同单独候选协议，content/mapping-notes.md、content/known-product-gaps.json、content/proposals.json。proposals带target_ref/expected_old_sha/reason/candidate_text，不能授发布资格。

module=iqs_route_e2e_lab；validate/export按共同接口，run-cases额外--case-input <冻结目标> --fixture-root <自有fixtures> --output <新目录>，不接受源仓路径作可写fixture。主文件≤8MiB、47基线固定，新序列≤32、每case日志单个≤2MiB且不能截断后假称完整。

## TDD与包级验收

先RED：expected反向注入、legacy冒v2、9%一期即退、unknown被补mature、丢一case、失败记pass、输入锁漂移、归档refs错SHA。集中测原47case执行链/序列/旧题兼容及薄CLI E2E。把软件成功运行、路由匹配率、不可适配率分开；完整47v2全部matched不是硬性造绿要求。

交接报告给case级矩阵和大节点接线建议、实际支持/失败/未跑分母，source/本包commit、输入SHA、清理记录。一次集中包级审查，不逐case设审批门。不关闭C01发布、owner、金融、G3/F05。
