# 公司agent实验包

把 [COMPANY-AGENT-01.md](COMPANY-AGENT-01.md) 的绝对路径交给一个独立harness即可。独占 `C:/Users/郑曾波/Projects/iqs-company-agent-lab`，准备时尚不存在；未自动创建或派发。可以与10-14前一批三个包并行，无共享写入。

目标是交付固定三题包、自由公司agent、证据驱动协调agent的可插拔研究执行器与离线重放。真实模型/搜索/owner/费用由总控复用StockQA接入，不另造客户端；本包不跑收费实验、不改其他仓。详见[设计](../../../experiments/company-agent-design-2026-10-14.md)、[预注册](../../../experiments/company-agent-registration-2026-10-14.md)、[接口](integration-contract.md)、[输入锁](inputs.lock.json)、[范围](manifest.json)。

冻结输入位于 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/company-agent-preparation-2026-10-14/inputs`；换机器携同字节快照并显式传新根。QA片段仅定位接口，非可独立运行的完整runtime；参考答案不放研究agent输入目录。已有盲评桥/金融依赖/产业链核证三个包不重复实现。

准备核验：`python -B -X utf8 verify_preparation.py`；它只检查卡、输入、目标和交接模板，不是产品测试或金融准确性证明。首轮实验最多318模型HTTP，真实执行尚未开始。
