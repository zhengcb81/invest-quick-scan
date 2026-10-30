# 三市场UI收尾：coverage显示与真实TTL-A

本目录只归档已核验的薄元数据和独审，不含模型答案正文、context全文、数据库、密钥或委托文件。

- StockWiki正常提交8527bc7：原coverage字段一行投影；新增4+legacy7=11P。独审另跑4，不累加；subject-binding集成模块因环境未配置跳过。第一次提交钩子发现unused Path import，删除该导入后11P、ruff/static原hook通过；after-lint报告绑定最终test SHA。原值/null/缺失不编造，原主体、分数、日期不改。
- 总控两次pytest临时目录3399/3400已按实际时间和测试名识别后清理。首清理命令Split-Path参数集不兼容，后用GetFullPath/GetDirectoryName显式绝对边界重新核验，两目标均不存在；错误不影响生产。其他临时目录/真实库未碰。
- TTL-A原cutoff25腾讯IQS24：正常v8政策下原query/preview/新委托/确认/准入→原UI run5b62→原交付job71ce→真实ACK1/1。新gen2、旧gen1含ACK SHA不变、五份完整36题文件不变。
- 费用沿真实pack_member→pack_send→budget精确归因，新增1HTTP/$0.017088，累计80HTTP/$1.882481、0在途。不是按空的budget.work_attempt_id直连；独审首个直连测量误得0的旧报告只留私有runs，最终报告保留纠正说明。
- 实际info_as_of为2026-08-12，按现有24h规则过期，**只证明正常刷新及真实入库，不证明今日fresh或金融正确性**。总控最初旧元数据比较形状漏stored_ack_sha256，r2真实读取同形比较；首版私有保留，不覆盖生产。

新cutoff30实验仍进行中，不能由这些文件推定其完成。三市场108有效槽和冷重启独审见相邻native-three-market-recovery目录；105原成功+真实替代3，不是原108全部ACK。

发布哈希见publication-manifest.json；JSON为可读LF归档，source_raw_sha256为原文件字节哈希，二者不得混用。
