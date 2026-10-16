# 三个05包的正式验收证据

主说明见 [总控验收记录](../../experiments/operating-desk-acceptance-2026-10-16.md)。此目录存最终独立复审、已应用CAS、实际提交与清理记录，保留原字节；不是工人旧handoff的覆盖版。`archive-check.json`逐项绑定本目录文件raw SHA，只有三个独立结果均passed、无未关闭发现、已精确应用并正常提交时，归档工具才生成该清单。

- `catl/`：OPERATING-CATL-05。
- `csc/`：OPERATING-CSC-05。
- `desk/`：EXPERIMENT-DESK-05。

`independent-result.json`绑定的是CAS文件本身的raw SHA，CAS内每个after SHA绑定真实已审文件；`deployment.json`记录原HEAD、最终commit、Git blob逐字节核验及原仓版本CLI冒烟。CATL的另一个`candidate_freeze_sha256`是作者payload清单摘要，与CAS raw SHA属于不同hash域，不应互相替代。旧原件与原始失败日志留在本机`runs/accept-05-2026-10-16/`，此目录不上传真实实验答案、私有盲评映射或数据库。

审查中的前轮needs_revision及RED保留在报告历史段；当前正式状态以报告最上方最终结果及对应JSON为准。测试绿色并不自动签收，独立结构反例也必须关闭。工程签收不授予金融准确率、评分gold或生产资格；源网页真实性、题目覆盖及系统symlink权限限制在各报告中单列。测试临时文件仅清理自有已核实路径，冻结输入、历史交付和他人工作均保留。
