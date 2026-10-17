# CONTEXT-PACK-06 — coordinator acceptance 1.0.1

本候选修复集中工程验收确认的上下文、计划引用、来源加载和路径边界问题。DTO protocol 仍为 1.0.0；新 package 输出版本为 1.0.1，明确兼容已交付的合法 1.0.0 计划与排程。修复列表见 fixes.json，实际测试与日志绑定见 tests.json。

原实现对干净 consumer 投影完整重跑 64 passed。候选先完整重跑 92 passed（原64、独立API反例13、CLI反例4、旧产物兼容8、来源策略3），0 failed、0 skipped；随后3个嵌套类型反例实际RED，补类型与静态缓存来源路径防御后，最终受影响范围实际重跑27 passed（类型3、CLI6、排程/CACHE10、旧产物兼容8）。没有把未实跑的新97项写成整组。原版新拒绝反例分别为13、4、3个预期失败；这些RED不计作未解决候选失败。最终公开模块CLI version/help、三个compile模式、schedule→analyze共7条实际命令均exit0；逐条完整argv/cwd/UTC/原stdout及stderr raw SHA在 code-review/pinned-ok-e2e.record.json。当前 examples/ 直接复制这些实际新输出，baseline仍为40957 UTF-8字节，题义、证据与工具字节复用保持。

干净输入为366文件、4359090 bytes，其中14个pyc在锁内、0个锁外文件；锁raw SHA为968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233。前后逐文件raw SHA完全一致。原64运行不能宣称source-only；1.0.1来源策略忽略全部pyc，传递导入与verifier均从.py源字节编译。共享冻结树的68个锁外pyc没有被本验收导入、删除或修复；不得把该共享树当干净输入。guard-proof实际证明禁网、外根写拒绝、共享输入读取拒绝、无secret环境名及禁写bytecode。

测试只读original/、inputs/，只写验收code-review自有目录。测试fixture路由与Windows长路径等价变换保存在harness-transform.json，未改任何冻结依赖的业务校验。初期harness失败（Windows MAX_PATH、guard的NUL/扩展路径归一化、错误的0pyc前提）日志保留，均不冒充实现失败或成功。final92是既有完整运行；focused27-source-final与source-final-e2e是最后小修后的实际记录。传递模块外根预缓存缺口来自独立静态审查，本次未生成或执行新增注入/伪模块/字节码对抗载荷验证这一分支；合法CLI与现有相关测试已实际运行。

docs/handoff/CONTEXT-PACK-06/完整保留原1.0.0历史。原artifacts.json把task_plan.md列为4299 bytes/ea81a397...，实际为4810 bytes/df6be69e...，由本版新manifest记录正确值；旧报告草稿标题和旧review身份、时间及日志绑定问题保留为历史来源限制，不伪造修补。原review passed不证明本版；本次独立复审真实调用、审查结论、最终source commit和CAS由总控验收根绑定candidate.freeze.json。此报告只提供本候选修复和实测事实，不代替该独立结论。

所有结果是字节投影/理论布局，不是实际缓存率、价格或准确率。没有调用外部API、下载、打开原数据库或真实execution；production_ready=false、financial_qualification_granted=false、rating_gold=false。没有真实模型质量/金融真值验证，也没有跨操作系统实机测试；搬迁检查在同一Windows主机的不同root/cwd完成。临时测试树清理统计见验收code-review/cleanup.json，必要日志、复现脚本、原始反例和本版样例作为证据保留。

最后helper精确路径固定后仅重跑公开CLI7条成功；focused27-source-final先于该精确pin，不冒充pin后的27项运行。helper按冻结原导入优先级固定到frozen/iqs/scripts，driver副本与其raw SHA一致。第一次误固定driver会拒绝合法导入，public-e2e-pinned-final失败日志保留；pinned-ok是校正后的唯一最后合法CLI记录。
