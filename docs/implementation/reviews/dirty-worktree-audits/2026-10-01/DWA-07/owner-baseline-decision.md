# DWA-07 owner 基线决议

记录时间：2026-10-01T20:59:49Z。该时间表示记录 owner 决议的时间，不是 harness 重新执行 Git 状态命令的时间；独立审计复跑证据见 [`report.md`](report.md)。

owner 选择采用 StockWiki 仓库在 owner 环境中**生效的全局忽略规则下的空状态**作为 DWA-07 当前基线，状态摘要为 SHA-256 空字节值 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。后续 harness 若不能读取同一全局忽略规则，必须报告状态可见性差异并停止，不能把视图差异解释成仓库新增改动。

初始快照曾记录 `?? .claude/settings.local.json`，其状态摘要为 `3ab8895f206d466e87cc5b9008a83aa4b5f4ba861c536584cfeea7bec0586c82`。owner 已说明该路径是个人 Claude 本地配置；只保留路径与状态元数据，不检查其内容，也不将其作为当前项目改动进行归因。初始快照完整保存在 `snapshot-initial.json`、`snapshot-status-initial.txt` 和 `snapshot-files-initial.jsonl`。

当前基线的 HEAD/分支沿用初始观察：`master@b4f3846bb3e331f5661edee974a7d0b76dbf9664`。这是一项 owner 明确确认的审计口径选择。独立 DWA-07 审计 harness 按状态命令复跑并得到空状态；当前 IQS shell 因无法读取全局忽略文件而看到1条状态，属于已知视图差异。若仓库 HEAD 改变或有效忽略规则发生变化，应另建新快照，不覆盖本记录。
