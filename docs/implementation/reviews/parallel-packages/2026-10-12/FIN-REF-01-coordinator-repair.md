# FIN 总控直接修复交付

授权：用户 FIN R4最新消息要求“验收发现问题就直接修复，不用再发整改施工卡”。不发R5，不重做已绿历史读取和冻结输入，不代改别的writer仓库。

唯一源根 C:/Users/郑曾波/Projects/iqs-financial-reference-lab；codex/fin-ref-01；原HEAD f4dffda0b15607b497af818474e46ae01a681703。

| 交付 | 实际结果 |
| --- | --- |
| 产品17路径 | 正常commit 6ff65e89dd662c36a313c1d2177bac29fdbc69aa |
| 当前R4交接22路径 | 正常commit/HEAD 1e7d61717661e1dbf9f24801df3afa6500ea941c |
| 源一致性 | 167跟踪与候选全SHA一致，90工件bytes/raw SHA匹配，98历史/schema1.0/fixture路径原字节保持 |
| 测试 | 原85P，最终103P/0skip；PID56876/exit0；公开角色与期间反例2/2，合法零NOPAT0/0 |
| 版本 | pack1.1.0 optional经济角色 / ledger1.0.0 / CLI声明1.4.1；旧读入口保持 |
| 当前研究 | partial：9completed/9gap/72not_started，原90范围未完成 |
| 源Git状态 | 仅原.codegraph/未跟踪，无remote，不能造push |

产品涉及cli/validate、economic_roles/strict_json、schema1.1可选字段及其生成器、明确角色的原测试正例与新增18项、pack/ledger和CSC来源生成器、显式target清单工具。当前交接只刷新remediation-04，实际changed_paths含产品与metadata且等于Git差异；原85/前轮原日志和旧交接不覆盖。清单命令 `python -B -X utf8 tools/build_current_manifest.py --target remediation-04 --overwrite`，排除自身和历史交接树，不遍历个人设施/runtime。

可复跑：去key环境/PYTHONPATH=src，`python -B -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp=<owned-temp>`；公开validate使用content/reference-pack.json、content/calculation-ledger.json与fixtures/inputs.lock.json；export必须新owned目录。角色是curated标签且已知SECconcept不能覆盖，不由标签或103测试授事实准确性。

原47对的一项所谓零OCF/capex→FCF正例不合法，当前正确拒；留原日志，新增合法零NOPAT ROIC对，不降低规范。已知参数arity、期间、当前账/换序/legacy和累计预算控制保持。精确控制/sha/process收据在IQS自有runs/fin-r4-acceptance-2026-10-11-01；源当前handoff/coordinator-receipt.json和logs可供后续harness读取。

清理257文件247目录（root/file ID/单链接/raw SHA），owned Python0，超限合成输入/复制锁/输出删，小控制/原日志/冻结source/candidate留；源.venv/.codegraph/B01/其他writer保护。模型、付费搜索、公司文档下载、生产DB/名单写入0。

后续沿原B01主线，不补造subject/vendorID/golden、不retroactive登记、不重跑已结算原运行。72题研究与独立事实→评分继续属于原计划未完项；软件签收不关闭金融/G3/F05/UI/全池。IQS本轮9文档本地正常commit，远端此前自动审批范围拒绝仍pending。
