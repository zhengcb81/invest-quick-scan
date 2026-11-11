# MC-IQS：IQS领域边界、公开工作台入口与总控整合

本卡留给总控；若用户交给另一harness，总控停止IQS源码并发写入。先读同目录 [总路线](README.md)、[调查](architecture-audit.md)、[契约/TDD](contracts-and-tdd.md)、[交接](integration-and-handoff.md)。无需此前聊天上下文。

## 工作范围和输入

- 唯一源仓：`C:/Users/郑曾波/Projects/invest-quick-scan`。规划时HEAD `fbe5b39`，包含本地`bb20529`；有共享引擎、语义、题库等WIP，不能从HEAD开始丢弃它们。
- 建议实现工作树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-IQS`，分支`codex/modularity-iqs-20261111`。本轮尚未创建。
- 写入：IQS scripts、相关schemas/tests、tests/suites.json、架构/使用文档及根PWF；不新增行业/问题内容，不修改原回答/运行配置/正式库。其余八仓只读。
- 外包作者只能交自己的子交接，根PWF仍由总控更新；总控自己施工则直接用根PWF。

## 目标结构

四域：题库/路由、答案语义、扫描编排、工作台应用。题库与语义不导入UI/SDK/owner实现；编排只用CA/RT/QA公开API；工作台通过owner adapters读写，组合根选择配置。不要把16个dashboard文件都各自升级成版本化owner。

已有`answer_validation.py`、`shared_company_ports.py`、task facade迁移和历史恢复修复保留。删除实现路径假设而非改名隐藏问题。跨仓身份/模型/存储决定不落回IQS副本。

## 实施顺序

1. 归拢当前WIP，按四域列实际import/数据写入与composition位置；先跑相关短组找旧失败，区分代码与环境问题。
2. 先写T1/T3/T4：最小公开owner替身、不安装兄弟源码的能力发现、非法反向依赖mutation。已有私有扫描收敛为域级规则，不继续解释Python任意执行。
3. 按C1–C3对接owner真实公开操作，操作所需最低版本与QA已实现1.8对齐。浏览能力声明不导入owner；执行时才核所需操作。禁止unknown→legacy重问回退。
4. **优先提供MC-UI输入：**按C5a复用open_dashboard，由IQS自己装配监听器及内部export，snapshot写IQS state_root/workbench；按C5b提供单次`/generated/snapshot.json`（旧五文件保留兼容投影）、snapshot CLI及有效fixture。普通启动不调用UI build_data/serve、不写UI仓；no-refresh只读旧快照。原UI旧serve shim由MC-UI实现。
5. 把UI当前读取的题库/版本/历史适配放到IQS内部单一export层，复用现有库，不复制评分/身份引擎。正式名单来自公开SW；草稿未绑定保持未绑定。
6. 运行域级短组并独审；收集其它owner自包含提交后按I1–I7一次组合。具体失败直接回相应owner修，不重开全部包。

## 本包TDD

|场景|期望|
|---|---|
|仅题库/语义运行，无QA/CA/RT/UI安装|能编译题集/验证历史语义，不加载外部provider|
|1题、36题、增加基础/行业模块、unknown公司类型|按数据构建；不硬编码24/36/12，不改变历史题义|
|shared engine使用只有公开API的fake|执行/恢复/导出可走通，不索取runner/store/模块位置|
|不存在peer安装时capabilities|返回需要的能力；不伪称可执行、不阻止只读页面|
|bank有效、roster或草稿缺失|snapshot局部unavailable；正式任务/结果页面仍可用|
|仅snapshot+UI静态文件，无IQS目录可供UI读|原工作台可启动/展示；UI不反向导入IQS|
|旧paid状态与当前新配置不一致|原资源/答案保存恢复仍沿原合同，API增量0|
|错主体/题义/ACK|明确拒绝真实冲突，不由“解耦”削弱|
|混合恢复/重复调用/慢owner|逐题进展不丢，正常读不被无关执行锁卡住|

现有短组（先选受影响文件，不每步全跑）：

```powershell
python -B -m pytest -q tests/test_shared_public_boundaries.py tests/test_shared_company_task_api.py tests/test_shared_company_engine.py tests/test_shared_answer_semantics.py tests/test_shared_company_engine_finalization.py tests/test_dashboard_module_boundaries.py tests/test_dashboard_http.py tests/test_view_launcher.py -p no:cacheprovider
python -B -m pytest -q tests/test_module_contract.py tests/test_question_manifest.py tests/test_question_sets.py tests/test_routing.py tests/test_read_only_replay_boundaries.py -p no:cacheprovider
python scripts/run_tests.py fast --plan
```

新的公开snapshot/启动测试放本仓正常tests并纳入已有分组。最后一条只列清单，不是测试通过。当前owner真实组合不能仅靠这两个短组或冻结Runtime的7个集成案例证明。

## 交付和结束

公开C5已实现、四域可独立替换、其它owner版本组合真实源码通过I1–I7、独立agent读最终diff并亲测重点、根PWF准确更新。交接位置`docs/handoff/MC-IQS/handoff.md`。本卡不承担新的金融评分、全池扩容或视觉重做；这些不能延长模块化专项。
