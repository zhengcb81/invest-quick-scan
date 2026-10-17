# 实际不同agent的整包独立审查

实施结束、必要测试完成后，必须实际调用另一个独立agent，对最终payload及本卡/共同规范全面检查。推荐fresh/no-history；不能实施者改名自审或自己写一个reviewed勾选。独审只写本Lab `review-work/`与正式review证据，不改实现；实施者修复全部有效发现，独审复核直到`passed`且`open_findings=[]`。误报只能由审查者给理由撤回，缺上游必要依据则blocked，不造正例或降低范围后仍声称完整。

只设一个整包审查节点，后续修复/受影响测试/复审在同一闭环，不给helper/每条案例加审批。审查所有实现、接口、schema、实质案例、预期与来源，不仅看模板/测试通过；包含完整度、独立测试预期、版本兼容、未知保留、污染/注入/隐私/外写边界、输入真实hash、测试时序、实际清理、可复现交接。审查者须实跑一条合法CLI链及各主要边界类别代表反例，并按包核：SOURCE每个引用和时点预期；QUERY每个issuer/listing/别名歧义关系；AUDIT每个rubric和标注示例是否泄漏/过度确定。

正式review目录必须有：

- `invocation-evidence.json`：真实implementer/reviewer不同agent ID、harness名、调用UTC、实际工具返回标识、保留的最小调用证据位置/raw hash。缺确切时间就null并解释，不补造UUID/隐藏思考/聊天全文。
- `round-01.md`及实际后续round：真实检查范围、命令、观察、finding ID/定位/根因/严重度与限制。审查不足不能标“全面通过”。
- `fixes.json`：逐finding的有效性、修复commit、回归日志/hash、reviewer关闭或有理由撤回；无发现为[]并列实际做过的检查。
- `final.json`：protocol=`iqs.search-lab-review/1.0.0`、package_id、status、两个agent ID、reviewed_payload_commit、input_lock_raw_sha256、round文件raw hash、closed/retracted/open findings、实际复核命令/结果、未覆盖限制、完成UTC。

final必须绑定最终payload，之后改实现/数据/schema/行为文档需同闭环复核新commit；仅后置交接元数据可另commit。独审不得授予金融gold/实时供应商性能/生产权限。缺独审能力或真实调用证据就保留checkpoint并报blocked，不交completed。总控仍会独立接收验收，不要求每小步骤回执。
