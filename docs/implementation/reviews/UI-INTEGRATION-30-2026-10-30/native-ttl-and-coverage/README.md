# 三市场UI收尾：coverage显示与TTL-A/B、历史恢复

本目录只归档已核验的薄元数据和独审，不含模型答案正文、context全文、数据库、密钥或委托文件。

- StockWiki正常提交8527bc7：原coverage字段一行投影；新增4+legacy7=11P。独审另跑4，不累加；subject-binding集成模块因环境未配置跳过。第一次提交钩子发现unused Path import，删除该导入后11P、ruff/static原hook通过；after-lint报告绑定最终test SHA。原值/null/缺失不编造，原主体、分数、日期不改。
- 总控两次pytest临时目录3399/3400已按实际时间和测试名识别后清理。首清理命令Split-Path参数集不兼容，后用GetFullPath/GetDirectoryName显式绝对边界重新核验，两目标均不存在；错误不影响生产。其他临时目录/真实库未碰。
- TTL-A原cutoff25腾讯IQS24：正常v8政策下原query/preview/新委托/确认/准入→原UI run5b62→原交付job71ce→真实ACK1/1。新gen2、旧gen1含ACK SHA不变、五份完整36题文件不变。
- 费用沿真实pack_member→pack_send→budget精确归因，新增1HTTP/$0.017088，累计80HTTP/$1.882481、0在途。不是按空的budget.work_attempt_id直连；独审首个直连测量误得0的旧报告只留私有runs，最终报告保留纠正说明。
- 实际info_as_of为2026-08-12，按现有24h规则过期，**只证明正常刷新及真实入库，不证明今日fresh或金融正确性**。总控最初旧元数据比较形状漏stored_ack_sha256，r2真实读取同形比较；首版私有保留，不覆盖生产。

新cutoff30实验B已完成真实准入/运行/原ACK1/1：原UI新preview9ef7...→原route record/activate CAS→原builders完整36题冻结→只1项gen3准入WORK_cd2e...→run3d4016...→deliveryjob8784...。独审重算5份文件及admission config/budget SHA，对齐原SDK registered execution_inputs_sha256，而非只信summary自报。B新增1HTTP/$0.020838，累计81settled/$1.903319、0在途。

实际B信息日2026-04-09，比A08-12更旧，不证明金融结论错误或正确；只读审查未读答案正文，不作内容准确性判断。原fresh query/owner preview规划gen4/无reuse，本轮不确认、不准入、不派发gen4，费用不变。新鲜复用真实正例仍pending。保守24h策略实现正确，但未来需分清指标期间/披露日/实际核查/结论有效时点，见语义讨论；当前未改TTL或补today。

B原UI readonly恢复实测：同run第2进程pid17644于16:53:55–16:54:51真实执行并exit0，返回original_references_and_recovery、API0、历史delivered/deferred，requested_scope_completed=false、whole_manifest_scanned=false、未reseal。前后CP/standard/context/outbox/ACK及总费用完全相同。仅签历史安全恢复0新增费用，**不能签fresh缓存命中或已完成新研究**。此前普通start只是attached原引用，未Popen，不能替代这次resume。

UI另正常commit2f1f450（无remote）修正启动展示：严格status+process_started区分attached与started，未知/矛盾保持未知、显示原回执；不改请求/权限/重试。原完整handler8场景回归有效RED→GREEN，root新8+原身份10由2个pytest wrapper通过，不重复累加；独审实际8通过。初次harness选中前batch handler语法失败只属于harness，不冒称产品红。三市场108有效槽和冷重启独审见相邻native-three-market-recovery目录；105原成功+真实替代3，不是原108全部ACK。

发布哈希见publication-manifest.json；JSON为可读LF归档，source_raw_sha256为原文件字节哈希，二者不得混用。
