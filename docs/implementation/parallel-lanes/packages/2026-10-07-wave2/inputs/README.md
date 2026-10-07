# 冻结输入说明

本目录只保存明确交接的代码、协议与synthetic fixture，不含生产库、公司文档或密钥。精确路径、SHA-256、来源仓和复制时点见上层`inputs.lock.json`的`working_tree_snapshots`。这些快照由总控创建，本目录对worker只读。

`qa-phase92-overlay/`九文件是尚未提交的StockQA有效首段工作，含已知`embedded_answer`真实RED。`iqs-phase92/`保存同一时点IQS metadata/generator/test原字节及字段映射。它们不是独立安装runtime；导出测试仍使用自己的隔离根和原IQS依赖。IQS私有generator尚未正式提交，其生产接口不能因保存快照而视作签收。

字段映射原件的“尚未写consumer”是较早状态，故完整保留原字节以便追溯；当前首段九文件及未接生产loader/store的准确状态以QA-C06-02卡为准。不能改旧映射原件去伪装历史状态。schema协议快照与合成身份测试不能当StockWiki真实owner golden。

目标源仓若与这些字节不同，报告具体hunk/归属，不能自动覆盖。全新且匹配HEAD的独立worktree才允许导入明确列出的九文件；其他七项未跟踪内容不复制、不读、不删。总控持有IQS修改权，QA worker不得把IQS snapshot回写IQS。
