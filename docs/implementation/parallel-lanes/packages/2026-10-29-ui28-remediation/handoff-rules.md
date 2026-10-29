# 两包 R1 共同边界、复现和交接

## 1. 唯一writer与冻结输入

- 继续自己的原Lab/原codex分支，不新建第二身份库、评分库或业务执行器。原业务源码未被总控修改；输入锁给出实际HEAD、raw SHA/bytes与Git blob。当前仅总控生成 `.codegraph/.gitignore` / `.codegraph/config.json` 未跟踪，别当垃圾删除、别混入旧payload或伪称它们是原交付脏改。可在自己Lab `.gitignore` 精确忽略 `.codegraph/`，但记录该局部变更，不改全局Git/其他目录。
- 开工核实际HEAD和源pin、活动writer。若用户或其他harness又改了原Lab，不reset/stash/覆盖；先列差异与真实当前基线交总控处理。源HEAD前进不等于可以悄悄用latest；旧commit与旧审查保留。
- 必须读本批inputs.lock。原10-28的21个参考文件及原锁SHA `680c4d7de15f2afd140bbe127ceb6cb9b65eabd1a1c5313de81843a9c67189ad` 保留；本批另锁StockWiki的observations/profiles/ui_quick_scan和IQS dashboard_owner，专门证明entity和history公共响应不同。Git commit/blob是40hex，SHA256是64hex，工作树CRLF与blobLF的字节数/hash分别核，不混称。
- 本批锁的deliveries是**可修改目标的开工基线**：开工核旧worktree，原commit/blob始终可读；修复后允许这些目标按卡变更，按最终新C/payload-manifest的新hash验，不要求仍等于旧worktree hash，更不改旧基线锁来求绿。原21参考与additional_read_only_sources仍须只读/保持锁定字节。
- 只读这些原仓参考和本批报告/合成反例；允许修改自己Lab原src、相关tests/tools/demo/schemas/fixtures、局部.gitignore、payload清单及新增R1交接。主IQS/原UI/StockWiki/StockQA及另一Lab禁写，真实答案/库/名单/config/key/env凭据禁读，不能运行原owner/收费模型/搜索/下载。不改变原协议经济含义或新增金融资格。

## 2. 有效红与回归

本批evidence中的测试已把原隔离目录import改为 `IQS_R1_COMPONENT_ROOT` 指定的组件根，业务断言保留；比较测试中无协议依据的config重赋诊断被排除，另附正确dispose/remount控制。Node原生test和既有helpers即可，不装新依赖。

PowerShell例（`$iqsUiR1OldRoot`保留/恢复普通非凭据变量）：

```powershell
$iqsUiR1OldRoot = $env:IQS_R1_COMPONENT_ROOT
try {
  $env:IQS_R1_COMPONENT_ROOT = 'C:/Users/郑曾波/Projects/iqs-comparison-view-lab'
  C:/Users/郑曾波/nodejs/node.exe --test 'C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-29-ui28-remediation/evidence/compare-product.test.mjs'
} finally { $env:IQS_R1_COMPONENT_ROOT = $iqsUiR1OldRoot }
```

名单改为自己的Lab及 `universe-product.test.mjs`。测试先对**锁定的原坏版本**确认目标行为红，再移入自己Lab回归测试，import改向本包src/helpers。可以采用等价的新数据/错误码，但不删掉核心不变量、不用预归一理想API替换真实公共形状，也不能仅返回固定fixture求绿。测试缺src、import失败、浏览器起不来不是有效业务红。

`compare-cleanup.test.mjs` 只对原已锁定helper证明风险，原版可能破坏文件的API在测试内全部拦截，真实删除/spawn=0。**先审清理实现**；如R1改用新的API，先把所有新破坏性接口也做stub，再运行负例，不可让虚拟 `C:\owned\...` 落到真实系统。不得为复现危险helper实际调用cmd/rmdir/删除非本人路径。

保留原基线测试范围，修后运行受影响单元/集成、该包完整功能组和一次安全真实浏览器mock E2E；只跑自己Lab，不跑小时级跨仓全套。必须测试交付的真实client/adapter→view/machine链，stub仅在传输/时钟/外部边界，不能mock被测投影或状态机。计数/退出码/skip/未跑项目按实际记录。未运行不等于通过。

## 3. 测试隔离与清理

本R1在测试隔离和新增交接路径上补充原卡，其余原范围不扩大。测试在自己的独占副本/临时Git工作区，不能让Git-less目录错误读祖先IQS index。允许从自己Lab的本地Git对象作无网络、无hardlink克隆到本人owned临时根，或等价独立Git导出；不clone外部仓、不fetch/push、不共享原活动index、不改全局Git/hook配置。保持最终源C原字节稳定，测试输出写外部owned临时根或后续元数据目录，不在reviewer运行时改变被审payload。

临时cwd/TEMP/TMP/cache/profile、上传样本、日志、子进程仅本人owned根；环境普通变量白名单，不继承/打印凭据。Loopback mock用各自原默认18771/18772或本人动态端口；COMPARE不得占UNIVERSE默认18772。不能碰8765/8766、别人的端口、进程或浏览器会话；冲突退出，不能kill占用方。真实浏览器须拒绝远端请求且允许本人127.0.0.1；错误DNS/proxy保护挡住自己loopback是环境问题，不能伪称产品红。

所有成功/失败/启动失败/超时都finally：核本次PID/命令/profile确为自己创建后关闭；递归删除前将绝对resolved目标与本人唯一创建根/拥有记录精确匹配，拒绝根目录、兄弟前缀、junction/symlink外跳和别人temp。不跨shell拼删除命令，使用一套原生Node fs或PowerShell机制。保留薄日志/合成截图与cleanup记录，删除临时profile/cache/生成夹具；有意保留的冻结输入副本须明确标审计输入，不冒称临时目录已删。

## 4. 一次最终集中独审，所有问题修完再交

完成合并修复、有效红→绿及功能回归后，冻结实际最终payload commit C和 `docs/payload-manifest.json` rawSHA。调用真实不同agent全面检查需求、diff、真实接口兼容、状态/隔离/清理、测试及证据；作者不能自称另一agent。审查发现需修的项全部修复，形成新C并复审受影响部分，最终必须passed/open_findings=[]。不要求每个函数或小修单独审，也不接受把尚未修复的缺陷写成accepted limitation放行。原卡已明确的“需总控接原UI/gateway、无生产/金融资格”继续保留。

最终invocation/round/final都绑定**同一C、同一输入锁、同一payload manifest和精确文件SHA**：

- handoff.snapshot.result_commit = handoff.review.snapshot_commit = review/final.payload_commit = 最终invocation.payload_commit = C；不能一处写content commit、另一处写review-evidence commit。
- final.reviewer_agent_id与它实际引用的最终invocation/round一致、不同于实现作者；invocation必须是实际调用，不把旧调用日期/ID/commit改造成新调用。保存必要平台返回元数据，不保存私有思考。
- evidence_path、evidence_sha256指真实工件且raw SHA256匹配；不能null、占位符、目录或“reviewed”文字。
- reviewed_file_hashes每key是具体最终文件，value是64hex且与C中的字节/声明消费字节对应；不要用文件夹代替所有源/schema/tests/tools。允许工作树与blob两种hash，但须标口径、精确一致。
- 实际实现/schema/回归fixture/测试/工具在C中，独审报告、运行日志和handoff可在后续metadata commit M；M不得改C功能文件。payload-manifest不hash自己/未来metadata，别把尚未产生的C塞进自己文件造成自指。最终聊天给真实C和M。
- 强化自己Lab现有validate-delivery，拒绝旧invocation/错C/错reviewer/null或文字hash/文件缺失/实际hash不符。它只能证明自洽，不鉴定真实独立调用或金融事实；不得因CLI退出0代签。

## 5. 现有工具如何消费两份锁和新交接（必须实际实现并测）

**不能把本批inputs.lock直接塞给原verify-inputs/demo。** 它是 `iqs.ui28_remediation_inputs/1.0.0`，原工具只认识旧21文件的files/repositories结构。这两份锁用途不同：

- 原 `verify-inputs` / `demo` 保持旧命令及原21输入锁、原source_package_id（UI-COMPARE-28或UI-UNIVERSE-28），原工作兼容不变。
- R1 `validate-delivery` 必须实际指向新 `remediation-01/handoff.json`，验证新package_id（原ID后缀-R1）；内部校原21参考时按对应source_package_id筛选，**不能拿R1 ID去旧锁筛成0文件再声称通过**。
- 兼容扩展现CLI的可选参数 `--handoff <新handoff>`、`--package-id <R1 ID>`、`--remediation-lock <本批新锁>`；原 `--lock <原21锁>` 继续显式提供。不要求新增第二工具。旧入口不带新增参数仍保持旧语义；新R1报告必须给出修后 `--help` 支持且真正运行过的完整argv（参数位置以修后parser为准）。UNIVERSE现有旧目录/PACKAGE_ID硬编码需要参数化；COMPARE要分开交接ID与旧锁过滤ID。
- R1校验：本批deliveries验证原Git对象/基线存在，不对修后的目标强求旧worktree hash；additional只读源及旧21参考按锁核；最终功能文件按C/payload清单核；本轮final/invocation的input_lock_sha256绑定**本批R1锁rawSHA**，原21锁SHA另外在report中明确保留，不能混用。
- 负例必须覆盖：指定R1 ID却落回旧handoff目录；旧package ID；任一锁缺失/非法/未知版本/漂移；R1 ID导致旧锁0文件；旧invocation或错C/reviewer/hash。均明确拒绝，不返回“旧交付valid”冒充R1通过。

完整调用语义示意（**以下新增参数须R1实现，旧版当前不支持，不是已验证可运行命令**）：`python -m <自己原工具模块> validate-delivery --lab-root <自己Lab> --lock <原21锁> --handoff <自己remediation-01/handoff.json> --package-id <自己R1-ID> --remediation-lock <本批inputs.lock.json> --out <本人未存在的新输出目录>`。最终必须将实测可执行的参数顺序写入README/tests.json。

## 6. 新交回位置与标准

保留原 `docs/handoff/UI-COMPARE-28/` 或 `UI-UNIVERSE-28/` 的旧原件不覆盖；新增各自 `remediation-01/`。handoff仍用原1.0.0闭字段，不往顶层加新字段。本批catalog登记新package_id；任务task_ids=[]，scope只本Lab，verification.network_calls如浏览器本地HTTP发生即真实bool true，外部/收费均0。

新目录至少：handoff.json、report.md、tests.json、artifacts.json、cleanup.json、review/invocation-evidence.json、round-*.json、fixes.json、final.json。report逐项映射本卡问题ID→修改文件→有效红/绿与邻接回归→真实证据SHA/已知未接线项；tests记argv/cwd/UTC/exit/count/skip/logSHA，cleanup核真实残留。历史环境失败和旧错误计数诚实区分，不伪造旧review/TDD。

总控之后按本批manifest运行原 `scripts/parallel_handoff_cli.py --verify-references`；这是公开形状/引用预检，不替代总控重新验收。两包均不启动生产接线、真实用户文件导入或108题扫描。
