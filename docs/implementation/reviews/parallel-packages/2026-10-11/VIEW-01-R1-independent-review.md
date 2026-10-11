# VIEW-01 R1 独立审查合并记录

2026-10-11，审查对象：VIEW Lab remediation-01，产品7069420、HEAD4d7662b；只读源码/原五组卡/交接。先用CodeGraph context，返回旧结构后读取已定位实际源码，不重复初始化索引。agent不运行suite、不写Lab、不联网或访问真实owner；Git sandbox读取限制由主控提权只读完成。源码行号以该快照为准。

结论：G1核心关闭；G2/G3事实/G4仍有实质缺口；G5主体改善但尚有接口/缺失态。以下与主控同候选集中验收合并，不能沿用交接自述“五组全关”。

| 优先级/原组 | 定位 | 可失败的反例与后果 |
| --- | --- | --- |
| P1/G2 | adapter.py:387、__main__.py::cmd_validate | 匹配所有内层头，只把result.profiles改null，仍supported，随后遍历None；validate构建在异常处理外，真实exit1/traceback。整数数组、URL和comparison理由等也有同类错误 |
| P1/G2 | adapter.py:409 | 两端删除request_id，None==None通过；必要字段存在性、类型、实际result/projection形状未闭合 |
| P1/G3 | adapter.py:676、843、853 | 顶层fact_relations available/source exchange:caps-11；raw caps事实生产ready=false，仍输出available关系。实现只看exchange ID集合，不读实际能力结果；owner_reported字符串不能自证 |
| P1/G4 | adapter.py:466 | request snapshot S1、response watermark S2，优先S1并挂载观察，不核响应快照一致性 |
| P1/G4 | adapter.py:344、904 | subject key只有snapshot/ASJ/revision；同键异store/perimeter/full subject_ref仍能拼接池身份/挂牌与异范围观察。范围不能降作显示小项 |
| P1/G4 | adapter.py:527、836 | 页按bundle顺序拼接，忽略实际request cursor；族只store/universe/snapshot，不含operation/query。真实合成100+50断链仍称完整；同universe不同query水位也会比较 |
| P2/G2 | bundle.py:238、Limits | banner.text未按schema string落实；单文件/文件数已限，尚缺独立总量限制 |
| P2/G5 | app.js:457、278、187 | missing_detail_note未展示，仍泛称新公司暂无结果；接口清单漏page_size_limit及snapshot wire_version |

保留：强制标记、固定状态、未知/不足证据不作有效分、恢复不加分、文本注入防护、禁用写入口、原报文片段与截断、正常两快照/不同revision、双挂牌、卡片和键盘。比较明确demo_claim并按观察ID合并多声明已实质修复；缺真实owner比较供数本身不算失败。

小显示项（null文案、listings/facts若干卡片data-label、补充banner重复）可同批处理，不额外建门。主控20公开CLI/5真实浏览器场景与130原suite的实际结果、隔离和清理见[集中报告](VIEW-01-R1-acceptance.md)。只续[原G2—G5 R2](VIEW-01-R2.md)，不回炉G1或已绿界面，不修改StockWiki或发明owner能力。
