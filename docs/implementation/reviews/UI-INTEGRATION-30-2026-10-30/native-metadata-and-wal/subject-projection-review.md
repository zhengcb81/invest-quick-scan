# 原生保留subject元数据投影：独立验收

**通过，open findings为空。最终21个唯一case全通过**：14个reviewer自有隔离case +7个原profiles case，2026-10-30T11:40:46.396681Z至11:40:53.180768Z，exit0、skip0。源码SHA见final-review.json（绑定当前工作树原字节，不冒充新commit）。

有效r02先得到12P/2F。两处真实根因均由总控修复：原observation.import_sequence与原accepted ACK不一致曾被接受；sbr绑定receipt_id改错并重算外层hash曾被接受。现同一只读snapshot批量加载原ACK，并用原bound _checked_original_ack核对；按既有合同重新核sbr canonical关系。额外静态签名问题已通过原store bound method正确解决，不计为额外行为红。

正例由原SubjectBoundObservationStore.register_dispatch/apply_decisions及真实纯IQS合同生成，绝非手写DTO。entity/security的legacy NULL subject/listing字段不被回写；元数据能准确投影；真实未绑定legacy仍未绑定；已导入后增加当前rev2不改历史rev1。10类元数据矛盾（hash/receipt/obs/payload/scope/sequence/protocol/attempt/pre-send/sbr）全部拒绝。读前后owned原数据库文件哈希不变，qualification/publication未提升。

独立静态审确认 observations/bindings/dispatches/ACK共享原只读事务，未每行调用CLI，未改旧观察或赋予C06/金融资格。支持的vendor1.2请求与binding1.1字段参与原canonical关系；本agent没有读真实vendor正文或执行真实vendor请求，实际部署DTO仍需总控只读验证。

r01遗漏metric-registry静态asset以及第一次final收集缺CLI默认配置均单列为隔离环境错误，未当产品反例。后者仅在owned副本创建providers: []，实际模型配置或API key均未读。原错误日志/JUnit保留；不把重跑叠加到21。

四轮owned临时目录全部清理，网络/模型/搜索实际请求0，真实源仓/DB/名单/预算写0。完整UTC/argv/log SHA、源pin、清理与限制见final-review.json。可复用用例与runner都在本目录；这是元数据读投影验收，不等于三市场全部扫描、金融准确性或全C06正式资格通过。

## 永久用例晋升补记

StockWiki原正常hook提交 `8cd239e346289a5af5b825bdb03c675ba576d2fa` 已只读核实；profiles与永久test的原始工作树字节均等于Git blob（分别73178183…、1fec9fa9…）。新增永久test仅加原integration opt-in skip guard并整理import，14个用例行为未变。以最终永久文件在独享副本重跑14P；清除integration标记及IQS/StockWiki路径后单测模块正确skip1、无error（pytest exit5表示未收集测试函数），证明guard在导入contract之前生效。两轮新temp清理成功。该晋升重跑不累计到原21个唯一业务case。完整命令/UTC/logSHA和最终Git双hash见promotion-delta.json；晋升前报告字节另存before-promotion文件。
