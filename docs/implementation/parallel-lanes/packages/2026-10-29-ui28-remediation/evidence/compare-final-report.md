# UI-COMPARE-28 总控隔离验收

结论：changes_requested。当前源HEAD `dd99431d3abda7920cb0a6b0377dae01bc7b53ef`；原业务源/测试未修改，只有获授权CodeGraph生成的2个未跟踪本地配置。

实际正例：原unit88P + 安全integration58P + perf1P = 147P/0skip。另4个产品行为反例有效失败，安全清理stub反例1F；原第5项config重赋诊断不是已声明更新API，校准后不计有效产品红，正确dispose/remount控制1P；原CLI21与browser2未执行，不把未跑或改helper副本算原通过。

所有反例为合成数据/公开serializer结构，未读取真实公司答案、库、key或运行模型。

## C28-01 / high

Actual original history rows contain reported_score/answer_status plus nested payload.answer/execution/versions. The delivered flat-only projector drops score8 and known as-of/version/model revision/coverage into null. Synthetic demo already uses flattened rows, masking the real shape.

位置：src/compare_view.js:178-285; src/compare_view.js:323-354; src/compare_client.js:159-172

实证：controller-counterexamples.test.mjs C28-01; observed deepEqual fails on seven original metadata fields

最小范围：src/compare_view.js projection + tests and optionally compare_client seam

整改：Normalize both original public entity/detail and history observation shapes, preserve explicit inner null/missing distinctions and exact scope/date/model, no SQL or authority changes. Add fixture labelled synthetic public serializer shape and actual client-chain regression.

## C28-02 / high

The shipped createComparisonClient returns projected records and removes raw groups. mount tries payload.groups to save original summaries, so even flat valid owner rows lose expandable original reasons through the actual shipped client->mount chain.

位置：src/compare_client.js:146-147; src/compare_view.js:2002-2035; src/compare_view.js:1929-1941

实证：controller-counterexamples.test.mjs C28-02 actual component/client, original summary unique token absent after clicking cell

最小范围：src/compare_client.js + src/compare_view.js raw-detail in-memory plumbing

整改：Keep a bounded in-memory raw-original lookup or explicitly injected original resolver through the client/view seam; use exact source pointers/observation refs, render summary/evidence safely; never place bodies in exportViewState/log/metadata store.

## C28-03 / high

For the same stable qid across old/new module packages, the first package seeds the single row, candidates are reduced to that package before observation_choices. Explicitly choosing new OBS_NEW yields missing/score null although the selected original observation exists.

位置：src/compare_view.js:520-592; src/compare_view.js:1261-1284

实证：controller-counterexamples.test.mjs C28-03 old score3 pkg_old + new score9 pkg_new, select only OBS_NEW; actual state missing/[] vs required single/9/OBS_NEW

最小范围：src/compare_view.js discoverQuestionRows/buildMatrixModel/explicit observation selection

整改：Ensure explicit original observation selection stays reachable across module releases; do not silently first-package-select or recalculate score; retain per-record package/version/perimeter diagnostics and honest original values.

## C28-04 / major

Model-axis grouping keys only entity+model_resolved and uses provider from the first record. Two distinct providers exposing the same model string collapse into one multiple cell, preventing side-by-side model-source comparison.

位置：src/compare_view.js:1221-1240; src/compare_view.js:1283-1284

实证：controller-counterexamples.test.mjs C28-04 providersP1/P2 same-model-name -> actual1 column expected2

最小范围：src/compare_view.js model-axis key/filter + tests

整改：Use complete declared model identity dimensions (provider+model, and known revision as appropriate) for model columns/filter/labels; unknown revision remains unknown; do not change financial qualification.

## C28-06 / high

Cleanup checks only startsWith(tmpdir), allowing sibling-prefix escape, then invokes destructive cmd/rmdir and rmSync. CLI tests similarly invoke cmd/rmdir without strict resolved owner containment. E2E sequential ports18771/18772 also overlap the other package default18772.

位置：tests/browser/cdp.mjs:301-321; tests/integration/cli.test.mjs:82-101; tests/browser/e2e.test.mjs:27-40

实证：cleanup-containment-counterexample.test.mjs C28-06 fully intercepted filesystem/process calls; virtual temp-sibling path reaches both destructive APIs, actual spawn/delete0. Browser not run.

最小范围：tests/browser/cdp.mjs + tests/integration/cli.test.mjs cleanup helpers

整改：Single native Node/PowerShell file mechanism; strict resolved descendant of unique caller-owned root, reject root/sibling/junction escape, verify PID/profile exact ownership. Avoid other package default port and record finally cleanup on success/failure/timeout.

## C28-07 / high

Handoff result/review commit be2ce169 differs from final-review payload ab2f486. Final reviewer is reviewer6, invocation points to reviewer2/01d8af8; evidence_sha256=null. reviewed_file_hashes are prose, not SHA256. This cannot authenticate a final different-agent review bound to the delivered payload.

位置：docs/handoff/UI-COMPARE-28/handoff.json; docs/handoff/UI-COMPARE-28/review/final.json; docs/handoff/UI-COMPARE-28/review/invocation-evidence.json

实证：Read-only field comparison, no assertion of fabrication. Original records preserved.

最小范围：docs/payload-manifest.json + final handoff/review metadata and test evidence

整改：Preserve history; deliver a new exact content payload with real final different-agent invocation/round/final hash evidence, align final commit/inputlock/payload manifest/file pins and handoff pointers; metadata-only commit separate. Never fabricate previous calls or self-sign.

## 可复现命令

先从原源HEAD `git archive` 建独占副本；公开源只读。下列证据测试在总控自己的隔离目录运行。

```powershell
C:/Users/郑曾波/nodejs/node.exe --test --test-reporter=spec C:/Users/郑曾波/Projects/invest-quick-scan/runs/accept-ui28-2026-10-29/compare/controller-counterexamples.test.mjs
C:/Users/郑曾波/nodejs/node.exe --test --test-reporter=spec C:/Users/郑曾波/Projects/invest-quick-scan/runs/accept-ui28-2026-10-29/compare/cleanup-containment-counterexample.test.mjs
```

第二个测试仅调用完整拦截的虚拟filesystem/process接口，无真实删除/外部进程。整改后需将反例移入自己Lab并改相对import为自有src，不能依赖总控私有目录；不得只删断言或固定fixture输出来求绿。

## 清理

execution/tmp实际为空；没有启动Chrome、mock监听服务或真实API；测试子进程已全部正常结束。git archive副本和日志是有意保留的只读审计材料，不是临时残留。源Lab业务无变动。主线/生产UI保持暂停。

## C28-05 校准（非阻断）

调用方直接重新赋值config.connectionIdentity不是本组件已声明的可观察更新API，故原诊断失败不能证明实现缺陷。正确dispose→重新mount的真实组件控制测试1P0.585s，旧pending不发布、旧host为空、新host仅显示9。宿主集成建议宜明确切连接也dispose/remount；本轮不要求魔法观察外部config赋值、不声称真实部署跨连接泄漏。参见connection-lifecycle-control.json与对应测试/日志。
