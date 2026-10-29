# COMPARE-R1补交02

唯一写根 `C:/Users/郑曾波/Projects/iqs-comparison-view-lab`，分支 `codex/ui-compare-28`。本轮实核HEAD `61982a72f35fd3250bc1710bc1a9cc3bf2455424`，当前C `9bb640d30c6a3c64d472bd07cab634d6b819d096`。正式ID继续 `UI-COMPARE-28-R1`、交回 `docs/handoff/UI-COMPARE-28/remediation-01/handoff.json`。读 [共同约定](handoff-rules.md)、[锁](inputs.lock.json)、[实测报告](evidence/compare-final-report.md)。原四个产品问题、兄弟前缀清理和正确dispose控制已通过，不重做这些功能。

## C-CLOSE-01 启动失败必须在返回会话前清理

- 基线 `tests/browser/cdp.mjs:54–59` 的 `BrowserSession.launch` 先mkdtemp再await start，无失败清理；withBrowser约320行也在try/finally前await launch，失败时拿不到session。
- [有效反例](evidence/compare-startup.test.mjs)：stub start为reject（0真实Chrome），close为真实方法的计数spy；当前close_calls=0、本人profile留存。断言后finally清理测试自己创建的根，不遗留垃圾。
- 最小改动：原launch/start会话拥有边界加失败finally/catch，异常时关闭仅本次部分启动的session并释放profile；保留原错误并如实记录清理失败，不能kill所有Chrome或递归删通用TEMP。
- 回归：spawn/start/DevTools初始化失败、正常退出、超时、重复close，原resolved-owned清理负例与正常browser2仍通过。失败模拟不需要故意启动一个无法控制的真实Chrome。这里只证明profile/startup cleanup缺口，**未观测真实失败Chrome进程泄漏**。

## C-CLOSE-02 标准交接与校验器必须查真实必需证据

- 当前 `handoff.scope` 缺原1.0.0要求的 `out_of_scope_writes`，IQS原公开CLI实际exit2/schema_invalid；不是上游schema新增字段。
- 当前final缺 `invocation_ref/round_refs/fixes_ref/test_refs`。在owned副本移走tests.json与review/fixes.json后，R1 validate-delivery仍exit0/all sections ok，见 [实际命令与输出](evidence/compare-required-refs-negative.json)。这是校验器漏证据，不仅是写法差异。
- 源最小范围：现 `tools/iqs_compare_view_tools/validate_delivery.py`（约430/440/574）及对应CLI负例；新交接生成逻辑/metadata补齐。先用被冻结的公共handoff schema验证自身，再验证final/实际invocation/最终round、tests/fixes及各hash引用，不接受约定文件名存在就代替明确引用。
- 本轮outer C/reviewer/manifest/evidence SHA与有效round已对齐，reviewed文件SHA也实际匹配；不要反过来改造旧审查或声称全部仍是旧C。只修遗漏的必需字段/引用/校验，并在代码工具冻结后做真正最终独审。
- 负例：移除必需scope字段；删除tests或fixes；final缺任一必需ref/指向不存在或错文件；错C/reviewer/hash；旧目录冒新R1。应退出2（路径越界按3），不能valid。

## 交接与测试范围

总控实际独立覆盖交付182P=97unit+82integration+1perf+2正常Chrome mock，另6项总控控制通过。integration首个环境漏PowerShell PATH失败已定向22CLI补跑纠正，不是源产品缺陷、不可双加分母。

本轮仅新增启动失败/必需证据的有效红→绿、受影响CLI/helper及已有功能回归，一次本包正常browsermock和失败边界控制，最终集中独审。原产品API、qid/模型/日期/原件保真和金融资格规则保持；不加新生产接口、不改别人目录。使用本轮新锁rawSHA和新C，同一正式R1路径新增真实复核记录，旧C/M/round原件保留；新代码要真正审过再交。
