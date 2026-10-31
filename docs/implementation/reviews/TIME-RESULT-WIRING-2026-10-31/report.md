# TIME/RESULT原服务接线验收

原IQS代码C：c1ee64fd5a7cd1331e67d7ec7f3a242ff2ffc0b2；原UI代码C：03d6b9aa3d45011f09bc77ef69e62b4a1d21e00e。
精确Git blob清单见installed-code-manifest.json，SHA 7b420282320da7f1b44455d71447201dbf505b0b27876dc4a4cc8bd91fc9fe2a。
最终不同作者审查见independent/final.json，已实核源码、独立反例、实际原接口与浏览器证据。

原8766使用原config/dashboard.local.json启动。新增entity-view显式wrapper，旧entity/refresh DTO、refresh_id、24h规则、原名单/预算/答案/分数保持。TIME纯库固定Git/pins，不引入Lab frozen sys.path；RESULT只读vendor仅有missing_date文字说明补丁。固定222题definition/release绑定，未知事实题/旧release保守不套用。

真实微软/宁德时代/腾讯分别37/38/38条原观察，各36个题目（含杜邦7与五力5）；额外条目为历史变体。新旧DTO只生成时间不同，292原workspace文件hash前后完全一致。112条走纯钟解释、1条旧release保持未绑定。旧观察没有native identity_revision，不从当前身份反填；context_assessed/current_context_verified/reuse_authorized均false，不造verified_at/ACK/金融资格或延长TTL。

后端74关联测试通过，事件失效根修后最终32受影响测试通过；重叠不加总（最终独立用例集合77）。UI53关联通过，最终3受影响复验通过（内含13 Node宿主用例，不再加总）。独立作者另验30temporal、2HTTP、3UI及10对抗探针，不计入总分母。原公开GET的实际代码字节与已提交JS一致。真实CUA三市场均见可信信息/多钟说明、原记录按钮确实展开本条原JSON，数据与模型不重新调用。截图只留本地runs，归档仅metadata/hash，不推回答正文图。

根修：坏旧groups/fields/execution不会拖垮公司读取；外来父/子实体不以当前公司展示分数或C06/质量；缺身份修订仍可解释绑定题目的日期但不假造兼容性；clock-only保留未来/asof>cutoff、来源缺失/撤回及过去/坏/预定事件约束。首次浏览器reload经历加载/selector脱离后读取真实ready状态再行动，不把工具等待上限当页面完成；沙箱Win10013只在受影响读HTTP测试提权重跑，不作产品红。

本次接的是只读解释，不是把TIME候选接成dispatch reuse。原字段TTL/逐观察ACK/核查receipt尚未由该DTO提供时保持未知；金融准确性、fresh真实正例、报表披露日历及当前owner兼容性仍由主线另行完成。启动/使用见[说明](../../time-result-wiring.md)，后续只跑受影响组，不重复小时级上游全套。

## 测试入口收尾（不改变生产runtime）

测试入口C e8f184c47221a97f0eb1f0183b55c38d5f835a01；独审DNS边界补丁C f16da24a5d78eb654a4a3e317e827d7e5cfe7bc0。已把6个遗漏文件登记，当前114文件分层54/57/1/2，各一次。TIME测试显式加载原StockWiki依赖，不再要求额外PYTHONPATH；生产路径不变。自有HTTP夹具只放行字面IP的TCP loopback；UDP与外部connect、getaddrinfo/gethostbyname/gethostbyname_ex/gethostbyaddr/getnameinfo均在pytest进程审计hook拒绝。hook不覆盖所有子孙CLI，不宣传整树网络沙箱。

关联65项通过；最终独立19项通过（重叠不加总），另有真实UDP2和DNS4入口的零数据包/零DNS探针。独审先固定真实RED再验证根修，最终C和逐文件hash见test-entry-independent/final.json。原25项清单仍绑定历史接线C，不用后续测试/元数据字节冒充旧C；生产runtime和原UI字节不变。
