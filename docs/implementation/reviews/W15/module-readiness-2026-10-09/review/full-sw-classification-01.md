# 同一 W15 集中审查附记：full SW 非绿分类

本附记只读分类原 `full-sw-support-fixed` 的实际终态：PID5808、returncode1，1063P/64F/18skip/21error、225.22s。没有重复 full、没有运行新的基线测试、没有修改任何产品/测试/PWF。覆盖率80%仍是 diagnostic，不作为通过依据。

## 已确定的两个 profiles 原基线 fixture 问题

`tests/test_quick_scan_profiles.py:316` 比较 `observation_id == "obs_p_iqs_leg"`；`tests/test_swr_profiles.py:183` 比较 `observation_id == "OBS_NEWER_FIRST"`。共同调用的已发布 `tests/test_quick_scan_observations.py:179–180` 对非标准短 ID 标签生成 `obs_` 加 SHA256。原 full 的实际失败值正是相应 hash；得分8/4等前置断言均已通过。应比较实际输入 observation 的 ID 或同一合成标签的规范化值，不能为通过而让产品重新接受/输出非法短地址。

只读 Git 对照 `6c46f03b486d215d696d32bee618793bc7fcb410` 已证明两个测试、共享 helper、Observation/import 实现均与候选逐字节相同；profiles/query 实现与已发布源工作树也逐字节相同，Git blob 差别仅既存 CRLF。详见 `published-profile-baseline-01.json` 的11个精确路径、三种 SHA 与比较结果。这是原基线 fixture 内部不一致，不是 W15 改变了原 Observation 地址或逆序选择行为；本附记不伪称另外执行过原基线。后半尚未达到的 source/date/freshness 断言，在修正 fixture 后需要受影响小范围补测。

## issuer 旧版本断言及未执行分支

`tests/test_quick_scan_issuer_bridge.py:361` 的首次 `migrate()==5` 在候选schema6上得到6；原测试文件与已发布基线逐字节相同。`409` 及 `417` 也硬编码5。第一次旧断言失败使真正v4 DB中 staged candidate 保留与桥表添加的后半分支尚未执行。这是 schema 升级后的 fixture 维护，不是已证实迁移丢数据；必须以 `SCHEMA_VERSION`/当前版本核验并补跑完整这一个用例，保留既有 candidate 内容检查与桥表检查，不能只改首断言就宣称两个状态都通过。

## 当前 W15 测试及控制器问题

`tests/test_quick_scan_owner_bridge.py:75` 的 `actual_bundle` fixture 在 full 中未找到。当前文件只 `from test_quick_scan_route_integration import NOW`，没有显式导入/共享 fixture；当前与full执行SHA均 `9b877343cc34e9a40dcfa3fa827d96b9fb1b3124ac77955d1489c14a47932ecd`，先前73P执行SHA为 `c3e17e74134d95dcfcb1b41da46679430c66cd0b2ed04d989cc6fa425dd15668`。这是本包 fixture 变化后的真实 setup 阻断，需显式暴露 fixture并用短、自有basetemp补跑当前桥接用例。不可用旧73P代替当前SHA。

三个 `test_quick_scan_route_integration` 错误的实际 traceback 已取得正确 `IQS_ROUTE_TEST_CODE_ROOT`，停止在 producer 发布工件rename，`WinError3` 的目标位于畸形且过长的basetemp（`sw/Users郑曾波Projectsinvest-quick-scanrunsw15asw-full-test-tmp/...`）。这纠正初次报告“未注入IQS根”的推断；不是产品拒绝了正常route。应使用此前已验证的短绝对自有根补测当前三个用例，不需要再full。

## 其余失败的对应关系

下表按原short summary逐项归组，64F与21error均有归属；这是诊断分类，未变成任何未执行用例的通过声明。

| 范围 | 原数量 | 直接失败原因/归属 |
|---|---:|---|
| 上述profiles | 2F | 已发布基线fixture短ID断言不一致 |
| issuer迁移 | 1F | 旧schema5断言；后半v4/staged尚未执行 |
| W15 owner bridge | 1error | 当前文件丢失fixture暴露，旧73P属于另一SHA |
| W15 route integration | 3error | 实际producer在畸形/过长basetemp发布rename失败 |
| G2b cross-owner CLI | 18F | 旧测试硬编码用户共享TEMP，实际foreign SQLite guard拒绝；不是身份CLI判定失败 |
| UI HTTP及quick_scan HTTP | 11F | Python guard拒绝loopback连接；没有得出W09/C06或业务响应结论 |
| UI Playwright | 11error | asyncio/socketpair的loopback同样被guard拒绝，浏览器断言未执行 |
| `test_check_all_script`及`test_checks`源配置检查 | 5F | 私有导出未含check_all.sh、AGENTS、CI/precommit支持文件 |
| `test_checks` workspace默认根 | 1F | 代码目录名sw，而默认根按StockWiki命名；得到同层真实元数据clone，不是源owner默认根回归 |
| real content conformance | 1F | 本批仅结构化元数据clone，signal/changed_assumptions均0/0；不能复制财报补造原content gate |
| llm_provider旧测试 | 9F | 密钥剥离/未拷贝真实provider配置，旧fixture按真实默认provider读取；未进行实际厂商HTTP |
| industry/news/services_news | 5F | 畸形深basetemp中长文件名实际FileNotFoundError，非W15路由/刷新改动 |
| preflight leak scanner | 3F | 原实现按绝对路径parts排除runs/tests；本批tmp位于runs，因此合成key-shaped fixture也被跳过；不是发生了真实密钥泄漏 |
| SWR backup链接测试 | 6F | os.symlink/Windows junction权限拒绝，恢复/清理断言未达到 |
| SWR UI static与scheduler UI static | 2F | 私有非秘密导出缺ui_static/app.js，静态断言未运行 |
| SWR legacy producer snapshot | 6error | 原legacy fixture/support未带入私有copy，setup未达到 |

保持原64F/21error记录及skip，不修改阈值，不放宽本批网络/foreign SQLite guard来洗绿。full旧测试对共享TEMP的路径行为属于这次全套隔离支持不兼容；本审查没有补跑它们，也没有创建或清理共享TEMP。

## 当前需要补测的实际不确定项

1. F1容量等待：work与budget-only两路径分别在owner-change时拒绝、stable时完成；拒绝必须保留prepared/no新reserve，现修复GREEN终态待主控提供。独立原反例另以新label复核，保留原RED。
2. 当前SHA owner bridge：fixture暴露修复后测试实际first-party CLI与原Observation引用/新题派发/未知work重启，不能沿用旧SHA73P。
3. 当前schema6 issuer fixture：首次空DB与真实v4/staged两个状态完整通过，并检查原candidate数据与新增route表。只需要受影响用例，不需要full。
4. 修复原profiles短ID期望后跑这两个用例及相关已存Observation/projection范围，以实际原payload地址为准。
5. 当前修复候选的IQS/SW/QA受影响终态与正常static接口：精确对执行SHA；Bandit应按原阈值而非降低阈值通过。原full余项保留为环境/支持限制，不能宣称全部软件栈/真实金融/owner query golden已绿。

该附记不给F1或包最终签收提前关闭，不改变真实query/C06 envelope、G3/L03、F05、B01准确性、TH-IN原门。
