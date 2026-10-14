# 三个独立包 — 2026-10-14

已编制并冻结输入；尚未启动harness。三个新根准备时不存在，各包没有彼此前置，可同时交给不同harness。共享PWF/旧Lab/源仓/真实库只读，只有总控最终接线。准备校验通过只说明卡/锁/模板有效，不是工人产品验收。

|施工包|独占工作目录|主要交付|
|---|---|---|
|[BLIND-INPUT-04](BLIND-INPUT-04.md)|C:/Users/郑曾波/Projects/iqs-blind-input-lab|真实Observation/答案及公开候选参考资料到盲评的显式适配，错误槽位与旧格式完整保持|
|[FIN-PROVENANCE-03](FIN-PROVENANCE-03.md)|C:/Users/郑曾波/Projects/iqs-fin-provenance-lab|定位旧冻结副本9个错误，金融90题原件/锁/依赖闭合的便携bundle|
|[CHAIN-VERIFY-04](CHAIN-VERIFY-04.md)|C:/Users/郑曾波/Projects/iqs-chain-verify-lab|三公司36槽位/59claim/52gap完整处置，优先具名关系的官方HTML独立核证|

把各卡绝对路径发给harness即可；卡自带实现/测试/交接，并链接[共同规则](common-rules.md)、[接口](integration-contract.md)、[目录权限](manifest.json)、[原字节锁](inputs.lock.json)、独立targets与handoff模板。输入快照 C:/Users/郑曾波/Projects/invest-quick-scan/runs/parallel-ready-2026-10-14-01/inputs/；换机器携带同字节快照，显式指定新root。前两包禁网，第三包仅人工读公开官方HTML，三包均不读key/不调用收费API/不下载财报/不写生产数据。

总控保留B01真实上下文/owner/原26与4恢复、收费模型搜索实验、真正双人金融核证、生产发布/UI/一键。BLIND不等待FIN的新bundle；FIN不使用新BLIND格式；CHAIN不借另外两包新事实。按冻结原件独立完成，后来源变动只由总控处理，不最后写入者覆盖。

准备检查：`C:/Miniconda/python.exe -B -X utf8 verify_preparation.py`。工人交回后每包一次大节点审查，失败只复跑受影响范围，不增加小节点门。现真实work仍18、source19、0正式评分/ACK0；本批不关闭Financial/G3/F05/生产UI/一键/全池。
