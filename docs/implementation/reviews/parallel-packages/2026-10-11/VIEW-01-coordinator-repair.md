# VIEW 总控直接修复交付记录

授权：用户“如果验收还不通过你就直接修复吧，不要再给整改施工卡了”。本记录是已完成修复，不是新的施工卡。

| 项目 | 实际值 |
| --- | --- |
| 唯一写仓 | C:/Users/郑曾波/Projects/iqs-viewer-lab |
| branch/base | codex/view-01 / ec62e13a3c2eb1cedbeb9d281455e3a99a7f83a2 |
| 产品commit | cd7bf1a6545c2b51f65ac6b02d10c90e77cdcb50 |
| 交接/终态HEAD | cfdfd705cb66859a3d2f123bae6ac0a7954795c9 |
| 版本 | owner原wire/冻结schema不改；Lab display API增量2.1（view_key/snapshot_key） |
| 最终测试 | 173项172P/1skip，unit128/integration21/真实Chromium24 |
| 清单 | 226跟踪，223工件bytes/raw SHA匹配；18原锁保持 |
| Git状态/remote | 仅既有?? .codegraph/；无remote，无push |

产品10文件：adapter.py、server.py、web/app.js、tests/unit/test_owner_scope_closure.py、tests/unit/test_r2_boundaries.py、tests/helpers.py、tests/integration/test_server_api.py、tests/e2e/test_viewer_e2e.py、tools/build_remediation_manifest.py，以及精确恢复docs/handoff/VIEW-01/remediation-01/artifacts.json。没有修改StockWiki/StockQA/其他Lab/生产库。

交接20文件限于docs/handoff/VIEW-01/remediation-02：纠正README/git-baseline/interfaces/integration-map/case-map/review/PWF/handoff，追加coordinator收据/状态/commit说明、原RED与最终process/stdout/stderr/JUnit/选择器截图、实际artifacts。原158轮JUnit/旧日志保持历史，173最终JUnit另命名；Git真状态明确记有一个已存在CodeGraph设施，不假写全仓空状态。

复跑从该仓去key的测试环境设置PYTHONPATH=src、复用已安装浏览器：`python -B -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp=<owned-temp>`。清单生成必须显式目标：`python -B -X utf8 tools/build_remediation_manifest.py --remediation remediation-02 --overwrite`，只刷新当轮；不能覆盖旧轮。验清单时核实际bytes/raw SHA、排除设施/缓存；原owner integration仍not_run。

自有证据根runs/view-r2-acceptance-2026-10-11-01：release-product.json/product-release-result.json、metadata-paths.json/metadata-release-result.json、最终handoff-check、原与修复cleanup清单、原日志及冻结source/候选。源发布前逐文件SHA和HEAD确认无并行漂移；发布后候选/源一致。总控PWF继续原B01工程动作，未把VIEW软件签收写成全项目完成。
