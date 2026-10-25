# 真实检索后 prepared 失败与观察库升级复核

确认本轮检索实际成功（HTTP 200、5 条、原预算 750 micros），模型只到 prepared，send_intent 为空，无模型预算、safe response 或 checkpoint。原 public subject-dispatch register 明确拒绝 schema2；原发送路径顺序是 prepared / external-use intent → subject registration → model send intent / budget，因此状态与本地准入失败一致。持久化 SDK 外层只有 generic native_persistence_uncertain；不能将它说成模型服务商拒绝或已经拿到回答。

独立核真实备份 observation schema2、当前 schema4；五旧表内容 SHA、application_id 以及四个 identity DB 字节全部相同。备份六文件均与原 manifest 吻合，manifest 内部 SHA f9665…匹配升级记录（manifest 文件自身 SHA 是不同口径）。当前原 public capabilities 显示 observations schema4/available，并且不授予金融资格。

本复核只读，数据库前后 SHA 相同，无 API、无迁移。共享引擎真实节点仍 pending，待新前置 guard 独审和实际 safe model response、正式封存、断网恢复证据。

## 前置 guard 独立复审

新增 guard 在 OwnerResearchServices 构造末尾、任何 generation/claim/付费检索之前自动调用原 public capabilities1.1 CLI，复用原 schema 且空 Registry 禁止远程 $ref；必须唯一 available observations3/4、自洽 store id、原 subject-register 接口和 0 API/write/dispatch 标志。原 owner 检查前后执行，原物理注册、权限、lease 与预算检查保留，无关闭开关或权限缓存。

独立运行 23 项方向单测全部通过（3.93 秒），测试进程删除 API key 环境且 socket 禁网；只有 public CLI 边界被 mock，不能作为真实 owner 正例。独立临时根已清理、源文件前后 SHA 相同，证据见 subject-readiness-independent.xml 与 cleanup。原失败/升级审查原字节保留 before-readiness.json。真实节点仍待实际结果。
