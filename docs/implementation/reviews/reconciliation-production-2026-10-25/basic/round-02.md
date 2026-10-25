# BASIC-BANK-EXPANSION-21 独立复审：Round 02

- 审查日期：2026-10-25；独立审查者 `/root/review_bank21`；根因修复实施者 `/root/fix_bank21`，总控 `/root`。
- 对象：基线 `046df087b4b3503aa4f765a076c469e4cb4de7c7` 后的明确5文件候选补丁；按逐文件SHA256绑定，不冒充尚未提交的新commit。最终提交绑定由总控在提交后补记。
- 当前状态：**PASSED（本卡工程独立复审）**，未关闭发现0项。初轮 `round-01.md` 的 CHANGES_REQUIRED 历史保持不动。

## 逐项闭合复查

| 发现 | 独立复审结果 | 证据 |
|---|---|---|
| R01 合法 common 诊断题被整库校验拒绝 | 已修；core与诊断的construct期望按role区分，真实隔离publish→compose→历史读取新增集成用例覆盖，独立最小反例通过 | `final-probe-results.json`；主仓新增 `ExpandedLibraryIntegrationTests` |
| R02 diagnostic+critical干扰质量门/跨仓不一致 | 已修；定义入口及两种summary策略均拒绝矛盾组合，generic diagnostic与common扩展都覆盖；真正核心/非诊断context关键风险继续gate | `final-probe-results.json`；主仓新增诊断/真实risk回归 |
| R03 删除诊断扩展patch被接受 | 已修；删除扩展须至少minor且墓碑仍精确累积，patch拒绝 | 独立探针R03通过 |
| R04 核心major变化+诊断删除组合被错误拒绝 | 已修；区分removed_extensions和breaking_removals，仅非诊断删除需后继映射；纯诊断删除仍保留原minor约定 | 独立探针R04；新增核心增添/核心后继组合测试 |
| R05 UI生成器固定总题数222阻断扩张 | 已修；目录注册身份、声明题数、唯一module/global questionID校验，期望总量由源catalog与真实数据派生，缺期望/篡改计数拒绝。完整build写出+--check在223题真实数据副本通过 | `final-ui-tests.txt`；`final-ui-result.json` |
| R06（复审新增）type替代关键核心时可丢critical标记 | 已修；common派生critical_core_ids，registry和archived-release两条正式入口均传给type校验。独立探针构造两个模块的sealed release，明确匹配critical core错误；standalone类型模块校验仍要求调用方提供集合，保留既有局部校验接口边界 | `final-probe-results.json`；动态IQS_99关键构念继承回归 |

## 已完成的独立验证

1. 独立反例复查 **8/8通过**：`python -B .../round_02_probe.py --final`。既检查无效定义/错误summary/patch删除拒绝，也检查合法诊断不动质量分、组合major通过、registry/真实archive两入口critical继承。
2. UI **134 tests OK，6项既有skip，9.936秒**。在标准短系统TemporaryDirectory内复制明确代码/测试/fixture目录，实际源数据根只读；catalog/common与外仓被改的2文件字节前后SHA相同，临时副本已自动删除。新6用例含真实完整main写出、--check、合法扩展223题，以及重复module/重复question/catalog声明漂移/名册漂移/缺期望反例。
3. 主仓6文件最终离线套件完成：**200 passed、245 subtests passed、3项环境失败**，1009.64秒（`final-main-tests.txt`）。三项全是本审查深Temp的Windows路径问题：归档copytree WinError3、两个router迁移测试清理WinError145；产品断言未失败。仅将这三项改到短系统TemporaryDirectory重跑，**3 passed、2 subtests passed，33.21秒**（`final-main-recheck3.txt`）；其余200项不重复。因此203个独立测试项全部得到通过覆盖，不能描述为单次“203 passed”。该次原始runner在自动清理深长路径时也遇到WinError145，未生成其预期result；此事实保留，综合结果独立记录 `final.json`。确切自有根 `final-main-k_7h40fu` 已按绝对路径核验后用Windows长路径方式清理；三项短Temp复验前后源码SHA相同、临时根自动清理。
4. AC-01重新独立取证完成：`compat_probe.py`从真实Git基线 `d5ce8e7fc03f760704e4468904191f1899f30efb`（`f606fa9^`）读取四个重构脚本，与最终代码使用同一现有发布数据，example/bank/cyclical × quick/full 共 **6/6组合**的manifest字节SHA、questions字节SHA、method_id、题数和summary摘要全相同；库报告共享字段相同，最终代码仅增加core_constructs/common_questions两个统计字段（均24）。证据 `compat-baseline.json`、`compat-final.json`、`compat-result.json`，探针只存摘要，临时目录自动清理。

## 源码输入锁

| 仓/文件 | SHA256 |
|---|---|
| 主仓 scripts/module_contract.py | d43c2b469f940cbf8453d61c86e34c90e6ffd7873fdbbec78ca0a81cefc36da6 |
| 主仓 scripts/question_sets.py | f515e2771722818ae223676d2a3461886000aaa7830b4bab2d8cbd40105328b7 |
| 主仓 tests/test_bank_expansion_21.py | bedfe8173ad3575f4a1c8ac39a467211cd85f1308b03a6d0bd8a3d08afc1f8e3 |
| UI scripts/build_data.py | f322bf94494d0adbb1ad6568dcf46edbd8d1b9ba9fff0d61903adabddcabbaef |
| UI tests/test_bank_expansion_build.py | 7fae354d4509294f86bfe2fc0d19fad890438bf6b8ab24b755ea8a2d1ec0b3cc |

## 如实限制

- 此次是新进行的独立审查，不能倒推以前施工时已经完成G4。G5 owner签收仍不代签，整个项目production_ready仍不由本卡决定。
- 未运行全仓78分钟套件，也没有把本轮工程通过解释成金融准确性、实际模型效果或生产owner准入。
- 原报告所引旧AC-01探针没有随旧证据交接；本轮已重新制作并运行独立探针，6个明确profile/模式组合字节相同，且新增真实发布/历史读取精确相等测试。范围不扩大为全历史所有profile/所有输出已逐字节复核。
- 首次深路径UI隔离副本因Windows CopyFile2长路径失败，日志保留在 `round-02-ui-tests.txt`；改为短系统Temp后最终全套通过。主仓两次沙箱环境失败和两次预冻结中断日志均保留并明确标注，不改写为GREEN。
