# U6 独立整节点审查

结论：**工程审查通过，未关闭问题 0 项**。审查者 `/root/review_product_u6` 与实施者分离；未修改源码、PWF、生产名单或生产数据库，未调用收费 API。最终绑定 33 个源码/测试文件原始 SHA256，详见 `final.json`。

本轮发现的 12 项问题均已修复并复核：非法 subject 被 serializer 接受、原权限同集合乱序误拒、准备回调与跨会话放弃竞争、配置 CAS 丢更新、2000 公司登记提前触发 4000 次原 CLI、批次读取被长任务阻塞、UI 缺少原 run 检查入口、同步交付阻塞 UI、全池引用超出自身读取上限、孤儿准备任务无法恢复、Windows 静态目录越界，以及把答案日期午夜误当作 owner 时间。

最后一项已使用原 import_entity 的“今天刚验证”回执和原 bootstrap preview/apply 验证：服务器冻结完整 UTC 时间并在预览、重查、应用中复用；答案 information_cutoff 保留为用户指定历史日期。测试在原 route 首次写入前明确停止并标为 partial，未伪造 prepared/golden。旧已完成候选保留幂等回放，旧未应用候选必须重新预览；浏览器不能指定 authority 时间。

| 独立最终回归 | 结果 | pytest 耗时 |
|---|---:|---:|
| IQS 产品整节点 8 个测试文件 | 154 通过 | 122.26 秒 |
| UI Node ESM 与真实回环 HTTP 静态边界 | 42 通过，1 OS 权限跳过 | 24.69 秒 |
| 最终格式化 QA 实际请求 scope | 6 通过 | 0.96 秒 |
| 最终 SW 权限置换/重复/缺项/外来项 | 7 通过 | 1.52 秒 |
| 原 SW→QA wire 交叉验证 | 10 通过，无跳过 | 11.17 秒 |
| 最终 UTC / fresh receipt / 历史答案日期 / 旧候选 / 浏览器时间拒绝 | 3 通过 | 36.71 秒 |

此前更广原 QA 130 例、SW 59 例及权限/委托 47 例的独立回归亦保留。上述各轮有重叠，不把重复运行相加当作独立覆盖量。原委托子集曾因仅加载 SW 而跳过的 10 例，最终已加载两边原源码逐一实际通过。最终常规测试期间 31 文件未变，UTC 窄测试期间另 2 文件未变；报告生成时再次核对全部 33 文件。

总控的两个慢原生准入门分别验证已有 subject 与仅有 verified issuer 的完整 36 题路径，按原权限分成 33 个 entity 问题和 3 个 security 问题，0 API；它们是隔离工程身份，不是生产身份或财务正确性 golden。两门运行时的源码 SHA 与最终时间修复不同，`final.json` 明确保留旧 SHA，未宣称最后版本重跑了慢门。最终变化已做增量原 bootstrap/application 边界验证。

已有真实 CATL 的公开完整交付回放独立于新 36 题准备：保留原 24 题 manifest、原 package 精确字节及原 ledger SHA，经过原导出→独立 receiver→绑定→原 import→精确 ACK，0 模型请求。CUA 显示 214 家原名单、48 个评分模块/222 个评分题、61 个信息题及一条真实 CATL 结果，缺失摘要没有用平均分代替。

当前默认生产 prepare/execution 配置仍为空，UI 如实显示不可执行，Microsoft 的 bank preview `can_apply=false`。工程通过不等于默认配置已经能一键扫描全池；不能代造 owner 权限、预算或把高级策略降级。214 家也没有全部完成扫描。本次不授予金融准确性、全池覆盖或新生产身份资格。

QA 正常提交 `7e8bf387c1f8b5b831ec3d9951cab79246d6fd4c`；SW 正常本地提交 `7085ddcc4c27b41f1954496909a44a522addb925`；UI 正常本地提交 `cc382f3ddeab7de3f3f28bfb220078556a14d676`，均由 reviewer 实际只读核实 HEAD。IQS 最终源码以 SHA 绑定，等待总控提交。QA 格式化前后已独立做 AST 等价核对和最终窄回归。

所有 reviewer 自有临时目录、58 个最终回归 SQLite 以及各轮 fixture 均已清理；cleanup JSON 保留具体路径与计数。审查目录不含数据库、回答或上下文副本。唯一最终 skip 是操作系统未授予创建 symlink 权限；其他实际 HTTP、路径别名和 reparse/containment 检查已执行。初轮深临时路径清理失败和 reviewer Windows 路径分隔断言均如实保留历史，源代码未变的短根/窄回归已通过。
