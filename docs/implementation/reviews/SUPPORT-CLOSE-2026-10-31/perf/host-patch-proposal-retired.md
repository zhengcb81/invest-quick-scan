# 已撤销：历史缓存预检接线提案

本文件原提案已退役，禁止应用。旧方案把调用方preview/status缓存传入_apply_import，已实证会在包变化后先持久化consumer_binding再拒绝。

当前唯一研究候选为payload C 99c350b8f332e5ea6459919fd692af19bab25100 的 integration/candidate.patch：保持_deliver_scope及_apply_import签名，绑定前新读原preview/status，仅合并worker启动。它未安装生产，也不保证提速；36包实测更慢。完整设计见../../../../integration/performance-design.md。

旧原文仅保存在../controller-close-support31/received-host-patch-proposal.md作历史，不能当当前实施指令。旧写入生成器已写前退役，原公开handoff校验CLI仍可读。
