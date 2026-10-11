# MATRIX-CASE-01 验收：需要集中整改

验收的是当前工作树冻结字节。实际分支`codex/matrix-case-01`、HEAD`4629e2a79a1d514f99f8db42394e39203dae06f0`，工作树102项且前后相同；无remote。交接仍为partial、result_commit=null，不能称已完成产品提交。166源文件、27锁内快照和artifacts实际字节匹配；原共同锁不改。

正常32例的原公开validate与两次export通过，全部案例无损、两份导出字节相同。已有输出拒覆盖、未来artifact版本、重复ID、错声明SHA、scope混用、缺实际模型及显式unknown带数字的保护有效。真实自有Windows junction反例由公开export拒绝且目标无损。这些成果保留。

独立12个坏输入却返回exit0，归为四组：实际nested冻结文件被添加LF、未来锁2.0和双方相同假定义hash未拦；不同期间/单位/币种/题义或评分尺仍宣称same_basis并授予数值派生；保留指令仍unknown而值改成5、unknown仍允许数值比；无效日期与score=11.5未拒。pack_id均按反例真实内容重算，不能将这些exit0记为通过。不同module release本身不一刀判不可比，需要真实兼容依据或明确未核实。

原测试使用自定义runner。最终43P/1F，唯一安装检查试图去掉强制隔离环境，被guard在创建前拒绝，属于not_run而非完整全绿；未安装到全局Python。初次pytest的37P/2setup error/1deselected及原sandbox硬链接权限错误均保留，分别属于驱动/环境限制，不能计入产品阻断。某早期Windows audit字符串argv控制遗漏也如实记录，后续改为对子进程环境全面检查。

结论changes_requested，全部缺口只归入[同包R1施工卡](MATRIX-CASE-01-R1.md)，不加helper审查，不重做已绿内容。源Lab只读、费用API0、生产库/名单0，不推进比较器、UI、金融准确性或全局门。实际命令、PID/终态、输入和日志留在`docs/implementation/intake/parallel-acceptance-2026-10-11/matrix-case/`；隔离清理以该目录最终cleanup为准，历史失败不改。
