# PERF 新增故障测试独立审查：缓存语义仍有有效行为红

审查者 /root/review_time_result_wiring31，原21/25测试作者 /root/review_perf_close31；只修改本审查runs目录，未改源Lab/PWF/原库/服务/预算，未调用外网或收费API。

## 实测

原新增25个参数化执行：17原生双变体集成全部通过；另外8授权/publisher单元首次受沙箱os.link/WinError5限制，在原记录发布处失败、未到业务断言，提权仅重跑这8个后通过。没有重跑旧39或完整性能矩阵。两个测试文件中的variant参数未选择不同代码，25执行不等于25独特变体行为；建议删除无效variant重复，改为17集成+2委托+2publisher=21个有效新增。

原生fault matrix有实质覆盖：真实producer sealed outbox、receiver import生成ACK、producer uncertain→重开→相同ACK幂等；拒绝foreign store/obs/hash及unknown status，checkpoint和budget attempt rows不变。委托单元确实使用原grant/confirmation/revocation与真实OS principal，缓存0/36的上游preview明确synthetic；publisher单元用实际原require_publisher及seal先验位置，调用实际owner.inspect(current_permissions)，不将最小SQLite carrier冒完整native published checkpoint。应把publisher宽ValueError改成permission_denied命名匹配。

## 阻断：候选缓存改变拒绝前的持久化副作用

额外新探针 `test_service_preflight.py` 穿过**真实baseline/candidate DashboardService._apply_import**、原owner._owner_worker以及原producer.bind_result_delivery_consumer。薄execution适配器只转调真实store方法，没有造bind/ACK；唯一fault injection为第一次真实preview后，给合成package文件追加一个空格，未更新其原登记SHA。

- baseline重跑preview，先报bundle_hash_mismatch。原consumer_binding仍None，bind调用0，delivery仍ready。
- candidate采用先前preview/status，先实际bind一次，原immutable quick_scan_delivery_consumer_binding已写入；随后import_apply才报相同bundle_hash_mismatch。delivery仍ready，但原绑定不可重定向，与baseline不等价。
- 实际有效结果：1P/1F，`seam-red.log`；命令/时点/SHA/清理在`seam-red.json`。检查的是SDK真实`consumer_binding`，不是ACK侧`consumer_store_id`；初探曾误看后者而2P，已独立保留`seam-field-probe-before.log`，不把那次当通过证据。
- 所有本次临时库/变体/短临时根已finally清。没有观察成功写入或真实公司错误绑定的指控，这是合成原生测试里的确定性差异。

因此新增21/25组件测试尚不能关闭“可变预检缓存不弱化原service”缺口，候选补丁不可按当前形式生产接线。

## 建议根修

把批读优化移动到 `_apply_import` 最后绑定之前：

1. `_deliver_scope`保留原第一次preview，然后按原接口调用_apply_import，不传先前preview/status跳过检查。
2. `_apply_import`针对mapped bundle，立即通过一个新worker批量执行fresh import_preview + fresh status；unwrap第一条仍按原preview失败处理，status按原不可用规则处理。
3. 比较body.preview_token与**新preview**、核can_apply，再从**新status**确定target，然后bind与原import_apply。
4. 这样保留原最后重验和原拒绝前副作用语义，同时把原第二preview+status两个worker合为一个。不要只恢复preview而继续用缓存status，否则接收目标轮换仍可能先绑定旧store。
5. 新回归至少把package和release两种篡改都在两变体走过该seam，拒后绑定/观察/费用/状态不变；另给receiver status变化场景，确保绑定实际新目标或保守拒绝。不是用stubs成功替代原store。

新candidate patch改变后，旧final4 wall数据只能作为旧候选历史，不能保留为新候选当前性能结论；candidate-source-manifest/hash和当前补丁必须更新，必要只补小批计时/进程数，不凭旧33/36数值声称新实现提速。

如果本探针复制成永久测试，其作者是本审查agent，最终全部payload宜由另一名非作者检查探针；本agent可继续复核root编写的runtime修复及真实新C，不自审自己测试质量。
