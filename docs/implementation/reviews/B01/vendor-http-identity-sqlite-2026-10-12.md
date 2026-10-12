# B01耐久回执真实SQLite封存候选

同一B01隔离候选已推进到真实临时SQLite。新Observation1.2能保留真实缺失header为null、不同response/physical attempt ID及三种SHA；从已持久化的原回执重建Observation，写入完整C06封存修订。重启重放字节一致/只一个修订；缺耐久记录具名阻断后恢复不调用模型；伪造六个执行字段，即使重新计算全部载荷hash或篡改caller getter，也不能写入数据库head。明确缺键不能混同null，旧1.1仍不接受null header。

首次8F（PID23572）是新合成fixture遗漏search_protocol，补真正必填协议后8F（PID31860）复现旧outbox把1.2 header强制非空的产品问题。总控直接仅在显式1.2 + durable-response-v1下允许捕获null并绑定response/receipt SHA，旧分支不改。随后69P/1F（PID38216）是伪造hash误用与原值相同的e重复字节，改为确实不同的9并保留失败。单独缺header键反例1RED（PID68816）后要求键存在；最终受影响4文件套件72P/0skip，PID73900/exit0/26.3779322秒。原87P格式装配与64P上下文是其它批次，不相加为金融准确率或一次全绿。

72项含新10条真实SQLite及原13回执/23封存/26outbox回归，合成公司/receipt仅软件证据，不是实际vendor/StockWiki owner/金融gold。5个精确测试scratch清138文件78目录；路径/无reparse/硬链接闭合集合核验，仅自有temp，下游活动候选/原live台账和生产数据库保持。日志、小案例、原失败和真实子进程回执留在runs/b01-engineering-2026-10-11-01；无收费API或文档下载。

新增QA候选src/utils/quick_scan_result_outbox.py与tests/unit/test_quick_scan_vendor_receipt_sqlite.py；原已改4文件/1测试保留。尚未部署源QA/IQS/SW。下一步继续同节点request1.2、binding1.1、query2.6/capabilities1.2/inspection显式profile接线，再一次集中大节点审查和重核源writer后精确部署。不能追认旧4个blocked检查点的新上下文/事前登记，原13HTTP/26搜索/CNY1.268162/0评分/ACK0保持。
