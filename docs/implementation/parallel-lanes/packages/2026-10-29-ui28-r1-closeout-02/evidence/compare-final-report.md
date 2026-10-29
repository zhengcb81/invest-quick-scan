# UI-COMPARE-28-R1 独立重验

结论：**原4项产品问题已修复，暂需收口2组工程交付问题**。源业务文件零写入。

源 HEAD `61982a72f35fd3250bc1710bc1a9cc3bf2455424`，payload C `9bb640d30c6a3c64d472bd07cab634d6b819d096`。执行副本为本目录 `isolated-checkout`，独立 Git/index、无网络 clone；本次所有临时文件/profile/log 均在 owned 路径。源前后只有既有两项 `.codegraph` untracked。

## 已实际通过

- 原4个产品有效反例4P；危险 sibling-prefix 清理安全stub1P；dispose/remount生命周期控制1P。
- 原交付测试182项：unit97P，integration82P，perf1P，真实Chrome mock E2E2P（0skip，19.9秒）。完整integration最初81P/1F由验收PATH漏PowerShell引起；补PATH后CLI22P，另60项已在全包通过，去重后82项。
- 浏览器仅连接本人18771/动态loopback mock；验收层追加Chrome proxy/host-resolver隔离，Node远网guard与密钥剥离。没有运行原UI、生产owner、真实库或付费API。

## 仍需收口

1. **启动失败清理**：`tests/browser/cdp.mjs:54` 的 launch 在 `await start()` 失败时不 close；`withBrowser:320` 同样在 try/finally 前 await launch。安全start拒绝stub实际证明 close_calls=0、profile留存（0真实浏览器进程）；不能据此声称已观测真实Chrome进程泄漏。见 `execution/launch-failure.test.mjs`、`execution/launch-failure.log`。最小修：launch异常分支清理部分会话并保留原错误，补失败/正常两条回归。
2. **证据闭合/校验入口**：`tools/iqs_compare_view_tools/validate_delivery.py:430` 新R1仅要求 invocation/final。交付final缺原共同规则要求的4个显式refs；owned副本移除 `tests.json`、`review/fixes.json` 后公开新R1 CLI仍exit0/allsectionsok（`required-refs-negative.json`含完整argv）。总控另以原公共schema CLI实测handoff缺 `scope.out_of_scope_writes` 被拒绝。最小修是补齐新交付元数据和R1入口的实际必需证据/未变schema校验。当前 C/reviewer/lock/文件hash绑定已有真实改善，不再把旧绑定问题重复算缺陷，不作伪造指控。

原C28-05外部重赋config不是已声明更新API，不列缺陷。上述修复保持原范围，不要求新生产接线或金融功能。

## 复验命令与证据

命令均在独占副本、剥离密钥/远网隔离环境运行：

```text
node --test --test-reporter=spec tests/unit/*.test.mjs
node --test --test-reporter=spec tests/integration/*.test.mjs
node --test --test-reporter=spec tests/integration/cli.test.mjs  # corrected PATH
node --test --test-reporter=spec tests/perf/*.test.mjs
node --import <acceptance-browser-network-guard-file-URL> --test --test-reporter=spec tests/browser/e2e.test.mjs
python -B execution/check_evidence_refs.py
node --test --test-reporter=spec execution/launch-failure.test.mjs
```

精确argv、退出码、source SHA、边界和局限见 `final-report.json`、`initial-tests.json`、`integration-and-perf.json`、`remaining-results.json`、各执行log。四个产品counter是总控发布包中的版本，只有冻结源root环境变量指向本副本。

## 清理

浏览器槽已通知总控释放。本人root相关Chrome/Node=0，18771监听=0；临时/profile/CLI输出均经PowerShell严格resolved descendant检查清理为0。正常浏览器profile由原helper清理；反例profile与初次环境失败残留由验收外层清理。保留本次独占源码副本、日志、纯合成截图作为证据，不提交、不推送、不改PWF。
