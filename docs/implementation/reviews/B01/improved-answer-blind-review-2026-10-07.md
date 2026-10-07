# B01改进实验：164行独立回答盲审

只读匿名包及已有输入审查，未读模型/方法映射、results/blocks/analysis；无API、凭据或外仓写入。五池及164行均逐批读取，每条claim核实际引用窗口。

这是agent辅助审查，支持只表示给定片段支持，不是人类gold或独立事实准确率。没有给精确金标准分数。

## 复算统计

| 项目 | 计数 |
|---|---:|
| 回答行 | 164 |
| claim | 283 |
| claim：部分支持 | 53 |
| claim：支持 | 214 |
| claim：明确冲突 | 11 |
| claim：无支持 | 5 |
| 评分判断：支持不足 | 46 |
| 评分判断：非评分 | 98 |
| 评分判断：有限可辩护 | 11 |
| 评分判断：明确冲突 | 9 |
| 含claim问题的行 | 56 |
| 非评分但含claim问题的行 | 21 |

合法未知多次正确指出实质材料缺口；这些不是已证明的正确答案。部分未知仍有年份、单位或引用错误，已逐条保留。

## 重要反例

- billion换算成亿美元时缩小十倍：营收119.8B、FCF73.3B、现金30.7B应分别为1198/733/307亿美元。
- 将评级表2022-2024数据平移成2023-2025，再与另一期每股净资产混称同期。
- Class C无投票权被改成B/C均超级投票权；合规改善承诺被改成已付和解金。
- 用SEC拦截提示证明财务披露完整；把Cash & Debt截断字段赋成现金。
- 增长/单点份额不能证明复购、难复制、长期无侵蚀；不少8–10分没有题目所需机制事实。
- 同一PDF多个窗口错引用；池中另有事实不代表当前source_id已经支持。
- 半年ROE行缺完整表头不能确定期间/年化；券商CFO负值不能直接推出收入失真或两年需再融资。

## 逐行裁决索引

| 匿名行 | 题号 | 原状态/分 | 评分支持 | claim问题 |
|---|---|---|---|---|
| A_301948de80fd | IQS_06 | scored/7 | 支持不足 | 有 |
| A_c0675ed70c1b | IQS_07 | scored/7 | 支持不足 | 有 |
| A_de4d3906ce74 | IQS_04 | insufficient_evidence/None | 非评分 | 未见 |
| A_9e85e38a0a93 | IQS_02 | insufficient_evidence/None | 非评分 | 未见 |
| A_5d6f8cf4ae50 | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_733565af4fd2 | IQS_02 | insufficient_evidence/None | 非评分 | 有 |
| A_c6ef1db9c7a7 | IQS_13 | insufficient_evidence/None | 非评分 | 有 |
| A_545b0698a054 | IQS_06 | scored/8 | 支持不足 | 未见 |
| A_f0b0540ea0ea | IQS_06 | scored/8 | 支持不足 | 未见 |
| A_d47af140d248 | IQS_04 | scored/7 | 有限可辩护 | 未见 |
| A_14996c239078 | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_b513c65ef56e | IQS_04 | insufficient_evidence/None | 非评分 | 未见 |
| A_ed5c7c72ea52 | IQS_02 | scored/8 | 明确冲突 | 有 |
| A_994c3bb55722 | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_5796a680dde7 | IQS_04 | scored/8 | 支持不足 | 未见 |
| A_1655a6ae5eb7 | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_b953137df131 | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_d1007264445f | IQS_02 | insufficient_evidence/None | 非评分 | 未见 |
| A_76dfa7ca305c | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_031ac9dec4ae | IQS_06 | insufficient_evidence/None | 非评分 | 未见 |
| A_d0e63f798c41 | IQS_05 | scored/7 | 支持不足 | 未见 |
| A_56732f8e4c5a | IQS_10 | insufficient_evidence/None | 非评分 | 未见 |
| A_32034e78ac57 | IQS_16 | insufficient_evidence/None | 非评分 | 未见 |
| A_f34cabb9dbf5 | IQS_05 | scored/9 | 支持不足 | 有 |
| A_72bef6a74984 | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_7b888e4ba128 | IQS_06 | insufficient_evidence/None | 非评分 | 未见 |
| A_929920579629 | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_1e4e5c016fe1 | IQS_12 | scored/8 | 支持不足 | 有 |
| A_d4cfb358a39c | IQS_16 | scored/8 | 支持不足 | 有 |
| A_b5384c0f072d | IQS_01 | scored/6 | 有限可辩护 | 未见 |
| A_ca55f9d4356b | IQS_05 | scored/7 | 明确冲突 | 有 |
| A_bad30135a8a2 | IQS_16 | insufficient_evidence/None | 非评分 | 未见 |
| A_a4bd9b42b026 | IQS_04 | scored/8 | 支持不足 | 有 |
| A_9c1909083abd | IQS_12 | scored/8 | 支持不足 | 有 |
| A_3e02e38a1876 | IQS_02 | insufficient_evidence/None | 非评分 | 未见 |
| A_68c6922297ee | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_9e095688e2ad | IQS_16 | insufficient_evidence/None | 非评分 | 有 |
| A_acd8b89e42b4 | IQS_09 | scored/6 | 支持不足 | 有 |
| A_4cb0b4ffc6d5 | IQS_01 | scored/6 | 有限可辩护 | 未见 |
| A_d8297e3331bd | IQS_13 | scored/7 | 明确冲突 | 有 |
| A_c0fb6c4c0896 | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_128774578979 | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_41b9f0005e7c | IQS_06 | scored/7 | 明确冲突 | 有 |
| A_9605085eefff | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_ca7b3af204de | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_cba2aa410de2 | IQS_05 | scored/7 | 有限可辩护 | 未见 |
| A_e7167484c6c6 | IQS_13 | insufficient_evidence/None | 非评分 | 有 |
| A_96ea89317735 | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_d185c8cd1522 | IQS_14 | scored/5 | 明确冲突 | 有 |
| A_312d47730e51 | IQS_10 | scored/8 | 支持不足 | 有 |
| A_70927b72cd51 | IQS_01 | scored/9 | 支持不足 | 有 |
| A_f1282b7ddc4c | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_9e5cf62c2f65 | IQS_01 | scored/8 | 明确冲突 | 有 |
| A_f4bb8dba6bf1 | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_7f179f97bc62 | IQS_12 | scored/7 | 明确冲突 | 有 |
| A_98235a857251 | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_4d82f803ad11 | IQS_02 | scored/8 | 支持不足 | 有 |
| A_29aa052b4720 | IQS_16 | insufficient_evidence/None | 非评分 | 有 |
| A_d1d3aec6d4ad | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_1698191f729d | IQS_04 | scored/6 | 支持不足 | 未见 |
| A_871a72f94b3f | IQS_05 | scored/8 | 支持不足 | 有 |
| A_255b060d912e | IQS_12 | scored/6 | 支持不足 | 未见 |
| A_e058c0f154c7 | IQS_10 | insufficient_evidence/None | 非评分 | 有 |
| A_cbb4b13b412d | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_3c28039e5266 | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_a7707cffe844 | IQS_12 | scored/7 | 支持不足 | 有 |
| A_9770f6384282 | IQS_10 | insufficient_evidence/None | 非评分 | 未见 |
| A_1648f1a2491c | IQS_01 | scored/8 | 支持不足 | 未见 |
| A_c80daed2f2e8 | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_9f78d0fbd240 | IQS_02 | scored/8 | 支持不足 | 未见 |
| A_677d049f0adc | IQS_16 | insufficient_evidence/None | 非评分 | 有 |
| A_0d1f9ab4eb72 | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_5463736105f0 | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_2765b39addf1 | IQS_02 | insufficient_evidence/None | 非评分 | 未见 |
| A_7459d801a27d | IQS_07 | insufficient_evidence/None | 非评分 | 有 |
| A_0cb9e079eedc | IQS_04 | scored/8 | 支持不足 | 未见 |
| A_d22d6c9595cb | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_8b524956789e | IQS_08 | scored/6 | 支持不足 | 未见 |
| A_e0fa7bdd253f | IQS_12 | insufficient_evidence/None | 非评分 | 有 |
| A_dd855ff84434 | IQS_05 | scored/7 | 有限可辩护 | 有 |
| A_64aa2cc6def4 | IQS_16 | insufficient_evidence/None | 非评分 | 未见 |
| A_ea07af515f80 | IQS_13 | insufficient_evidence/None | 非评分 | 未见 |
| A_5f7b19eaee05 | IQS_10 | scored/8 | 支持不足 | 未见 |
| A_e14395b4da6b | IQS_16 | scored/6 | 明确冲突 | 未见 |
| A_74820001bfb2 | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_30c134a4c6ab | IQS_16 | insufficient_evidence/None | 非评分 | 未见 |
| A_89947721957f | IQS_16 | insufficient_evidence/None | 非评分 | 未见 |
| A_a86dbd162df5 | IQS_10 | insufficient_evidence/None | 非评分 | 未见 |
| A_9fed8078df6e | IQS_16 | insufficient_evidence/None | 非评分 | 有 |
| A_e7275b6f2b15 | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_5c7474e3bd79 | IQS_01 | insufficient_evidence/None | 非评分 | 未见 |
| A_109b4c3e3b4c | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_fe33d1b95164 | IQS_04 | insufficient_evidence/None | 非评分 | 未见 |
| A_5645eca7023e | IQS_12 | scored/7 | 支持不足 | 有 |
| A_5bb641ef0cfe | IQS_01 | scored/9 | 支持不足 | 未见 |
| A_74299c6c0859 | IQS_08 | scored/7 | 支持不足 | 有 |
| A_956dc1b1d667 | IQS_12 | insufficient_evidence/None | 非评分 | 有 |
| A_1e3012640f2b | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_8935258a282b | IQS_05 | scored/8 | 支持不足 | 未见 |
| A_8fd98c46dc8c | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_95c8bb166d72 | IQS_08 | scored/8 | 支持不足 | 未见 |
| A_79c023909062 | IQS_05 | scored/6 | 有限可辩护 | 未见 |
| A_fe0e3b840da7 | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_0c947fa234f3 | IQS_13 | insufficient_evidence/None | 非评分 | 未见 |
| A_ce8f2fd40cc5 | IQS_04 | insufficient_evidence/None | 非评分 | 未见 |
| A_8f506eb26cb1 | IQS_02 | scored/7 | 支持不足 | 有 |
| A_7690441f7e37 | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_ed1377dcbb1f | IQS_01 | scored/7 | 有限可辩护 | 未见 |
| A_5e0c1c2f6616 | IQS_06 | insufficient_evidence/None | 非评分 | 未见 |
| A_05cfc3f8780e | IQS_10 | insufficient_evidence/None | 非评分 | 未见 |
| A_b784458e4ee7 | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_1bd118786b9f | IQS_07 | scored/6 | 支持不足 | 未见 |
| A_6b79c9783bf7 | IQS_06 | scored/8 | 支持不足 | 未见 |
| A_d71af70460b7 | IQS_09 | scored/8 | 支持不足 | 有 |
| A_cace17325a23 | IQS_16 | insufficient_evidence/None | 非评分 | 未见 |
| A_963b0a30d294 | IQS_02 | scored/6 | 支持不足 | 未见 |
| A_e488ee9ace43 | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_573f0c3d297c | IQS_10 | scored/6 | 支持不足 | 有 |
| A_b707f50cbc0b | IQS_06 | scored/8 | 支持不足 | 有 |
| A_2bf578797d6a | IQS_02 | insufficient_evidence/None | 非评分 | 未见 |
| A_b01462e73e6b | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_7e4ea93a844c | IQS_06 | scored/8 | 支持不足 | 未见 |
| A_c18074d9da7e | IQS_01 | scored/8 | 支持不足 | 未见 |
| A_4b8502723e77 | IQS_13 | insufficient_evidence/None | 非评分 | 有 |
| A_993f63bf75db | IQS_16 | insufficient_evidence/None | 非评分 | 有 |
| A_14e2e94af635 | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_1523a0c4b34e | IQS_04 | insufficient_evidence/None | 非评分 | 未见 |
| A_6f0af856a6f9 | IQS_10 | insufficient_evidence/None | 非评分 | 有 |
| A_7f06a4d61fd6 | IQS_13 | insufficient_evidence/None | 非评分 | 有 |
| A_e1980dcdb5f9 | IQS_02 | scored/7 | 支持不足 | 未见 |
| A_88cac4fc1d35 | IQS_16 | insufficient_evidence/None | 非评分 | 有 |
| A_7c61af6a4584 | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_c5f8630df567 | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_58161ca91bfc | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_44fde8e3d700 | IQS_13 | insufficient_evidence/None | 非评分 | 未见 |
| A_ee0713a4f986 | IQS_09 | insufficient_evidence/None | 非评分 | 有 |
| A_f83daa4b76f3 | IQS_10 | insufficient_evidence/None | 非评分 | 有 |
| A_beebf8a5c94d | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_d7c439ae22d0 | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_eb12233d11ea | IQS_12 | insufficient_evidence/None | 非评分 | 有 |
| A_bd6532c5b27d | IQS_06 | scored/9 | 支持不足 | 有 |
| A_f1d095283cf2 | IQS_10 | scored/5 | 支持不足 | 有 |
| A_d6fd1bc716b1 | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_cbad7620d2f3 | IQS_13 | scored/6 | 支持不足 | 有 |
| A_29d7237a3239 | IQS_13 | scored/7 | 有限可辩护 | 有 |
| A_65a1bed1ad81 | IQS_07 | insufficient_evidence/None | 非评分 | 未见 |
| A_ac368c5b7ca2 | IQS_08 | insufficient_evidence/None | 非评分 | 未见 |
| A_d3da8203ab8e | IQS_04 | scored/7 | 支持不足 | 未见 |
| A_581af0a7af2a | IQS_10 | insufficient_evidence/None | 非评分 | 未见 |
| A_a096df05d5dc | IQS_13 | scored/6 | 有限可辩护 | 未见 |
| A_bc4b83b8d4b3 | IQS_13 | scored/7 | 有限可辩护 | 有 |
| A_2cf5d84456e2 | IQS_07 | insufficient_evidence/None | 非评分 | 有 |
| A_2167460b65fd | IQS_01 | scored/10 | 明确冲突 | 有 |
| A_a81492e7573c | IQS_06 | insufficient_evidence/None | 非评分 | 未见 |
| A_953405f6ae54 | IQS_14 | scored/8 | 支持不足 | 有 |
| A_9ab23d0c42bf | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_6af7daa9fcd4 | IQS_10 | insufficient_evidence/None | 非评分 | 有 |
| A_f97e9b194f36 | IQS_09 | insufficient_evidence/None | 非评分 | 未见 |
| A_3edf29276459 | IQS_10 | insufficient_evidence/None | 非评分 | 未见 |
| A_2856f4ca0a12 | IQS_12 | insufficient_evidence/None | 非评分 | 未见 |
| A_f825b9664feb | IQS_01 | scored/7 | 有限可辩护 | 未见 |
| A_8bf81d411be7 | IQS_05 | insufficient_evidence/None | 非评分 | 未见 |
| A_2c27662bb9a2 | IQS_05 | scored/8 | 支持不足 | 未见 |
| A_c64bd6204c07 | IQS_16 | scored/7 | 支持不足 | 有 |

完整逐claim原因、unknown缺口、整段rationale/counter的额外问题与源边界见同名JSON。部分支持不是确定事实错误，明确冲突与缺支持已分开。

本报告不覆盖随后扩展57行，不能合并分母或用于认定某模型/策略准确率。

匿名包SHA-256：3fd059afef075ad7ff503d49171546d3148c1abb78d04f2950b00f2fc89184aa
