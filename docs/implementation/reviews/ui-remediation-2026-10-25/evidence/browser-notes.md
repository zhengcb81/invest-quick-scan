# 总控实际浏览器检查（进行中）

- 8766正式首页明确214原实体/1有正式记录/213无正式记录/1观察，12历史草稿单列，未冒称全题完成。
- 名单搜索中信建投：原HK06066 provisional及CN601066 verified分别显示，唯一实体保持不同，0业务写。
- 隔离8770初始fixture将configured=false模板预存为有效policy，原StockQA正确拒绝（configured必须为True）；修正测试环境为原policy缺失→未启用模板流程，不改原校验。临时provider禁用、空key/example.invalid，执行包为空、prepare空；不调用模型。

- 临时UI实际连接保存成功；策略通过原StockQA save，文档未知字段保留/provider仍禁用。原校验正确拒0预算，临时专用策略1USD/1请求/0.1上限仅用于保存验收，未创建原费用授权或运行任务；没有改真实r25。并发原文件改动后旧页面409拒绝，原字段未覆盖。冲突中文提示仍需改善，已交product。
- CATL详情主层分数7、短理由、模型、时间、published/review_pending/主体与模型修订缺口可见，完整理由/来源折叠；详情返回保留query=宁德、limit50、offset0、view与原snapshot_token。
- 独审两个实质发现已复现并接修：原delivery job completed推荐误回扫描；select[size=5]被全局36px压缩。独审另检保存期间draft竞态，由product修。

- 真实历史CATL仅1个.answer-record；页面明确“目前只有1条观测，暂无第二份可对照记录”。数据说明原动态连接与历史静态来源已分清。
- 最后CSS实际重载后：准备公司size5列表147.999px（原35.998），1280页宽1265；旧草稿题义select1167.476px、页宽1265（修前selector1313.221/页宽1362）。
- 375/768固定同源iframe真SPA截图：首页/扫描步骤/设置/矩阵；frame实际外宽374.994与767.999CSSpx，设置字段堆叠。矩阵窄屏副导航局部横滚，主导航完整可见。CUA只读DOM facade不暴露child contentWindow/contentDocument，所以未断言子文档精确scrollWidth，未冒称物理手机、外层resize、读屏或缩放。首轮截图短暂未加载/旧CSS缓存，完整reload等实际内容出现后再复测，未把加载空白误当布局缺陷。
- HTTP/交付/准备接口31P/11.54秒，先前sandboxloopback WinError10013原14F/17P记录保留，合法提权同命令通过，没改断言。

- 最终产品源重载后真实表单：模型保存中47个编辑控件禁用，连接保存中21个控件禁用；原搜索路径输入后清空再保存，原配置prepare不含该键。合法策略保存成功后再次并发改文件，旧页面拒绝覆盖，明确提示“配置已被其他进程修改，未覆盖”并提供重新读取按钮。原文件保存的模型仍是engineering-fixture-final-save及所有未知字段，stale模型未写入。
